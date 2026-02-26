"""
LinkedIn Auto-Poster for AI Employee.

Reads approved LinkedIn post drafts from /Approved/ and posts them
via Playwright browser automation. Saves proof screenshots.

Usage:
    uv run python scripts/linkedin_poster.py --vault ./AI_Employee_Vault
    uv run python scripts/linkedin_poster.py --login   # First-time LinkedIn login
    uv run python scripts/linkedin_poster.py --dry-run
"""

import argparse
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("LinkedInPoster")

# Persistent browser session directory
SESSION_DIR = "linkedin_session"


def extract_post_content(file_path: Path) -> dict | None:
    """Extract post content and hashtags from a LINKEDIN_*.md file."""
    content = file_path.read_text(encoding="utf-8")

    # Extract the post body — between "## LinkedIn Post Draft" and next "##"
    post_match = re.search(
        r"## LinkedIn Post Draft\s*\n(.*?)(?=\n## |\Z)",
        content,
        re.DOTALL,
    )
    if not post_match:
        # Fallback: try "## Proposed Action" (from HITL approval files)
        post_match = re.search(
            r"## Proposed Action\s*\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )

    if not post_match:
        logger.warning(f"Could not extract post content from {file_path.name}")
        return None

    post_body = post_match.group(1).strip()

    # Extract hashtags
    hashtag_match = re.search(r"## Hashtags\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    hashtags = hashtag_match.group(1).strip() if hashtag_match else ""

    # Combine post + hashtags
    full_post = post_body
    if hashtags:
        full_post += "\n\n" + hashtags

    return {
        "content": full_post,
        "filename": file_path.name,
        "path": file_path,
    }


def login_to_linkedin(session_dir: str):
    """Open a headed browser for manual LinkedIn login. Saves session."""
    Path(session_dir).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=session_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://www.linkedin.com/login")

        logger.info("Please log in to LinkedIn in the browser window.")
        logger.info("After logging in, close the browser window to save the session.")

        # Wait for the user to close the browser
        try:
            page.wait_for_event("close", timeout=300000)  # 5 min timeout
        except Exception:
            pass

        browser.close()

    logger.info(f"LinkedIn session saved to {session_dir}/")


def post_to_linkedin(post_content: str, session_dir: str, proof_path: str, dry_run: bool = False) -> bool:
    """Post content to LinkedIn using Playwright."""
    if dry_run:
        logger.info(f"[DRY RUN] Would post: {post_content[:100]}...")
        return True

    Path(session_dir).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=session_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        try:
            # Navigate to LinkedIn feed
            page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=30000)
            time.sleep(2)

            # Check if logged in (look for the post composer button)
            start_post_btn = page.locator("button.share-box-feed-entry__trigger, button[class*='artdeco-button--muted']")

            if start_post_btn.count() == 0:
                logger.error("Not logged in or LinkedIn UI changed. Run with --login first.")
                page.screenshot(path=proof_path)
                browser.close()
                return False

            # Click "Start a post"
            start_post_btn.first.click()
            time.sleep(2)

            # Wait for the post modal/editor
            editor = page.locator("div.ql-editor[contenteditable='true'], div[role='textbox'][contenteditable='true']")
            editor.wait_for(state="visible", timeout=10000)

            # Type the post content
            editor.click()
            editor.fill(post_content)
            time.sleep(1)

            # Click the "Post" button
            post_btn = page.locator("button.share-actions__primary-action, button[class*='share-actions__primary']")
            if post_btn.count() == 0:
                # Fallback selector
                post_btn = page.get_by_role("button", name="Post")

            post_btn.first.click()
            time.sleep(3)

            # Wait for post to be submitted
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)

            # Take proof screenshot
            page.screenshot(path=proof_path)
            logger.info(f"Post submitted. Proof screenshot: {proof_path}")

            browser.close()
            return True

        except PlaywrightTimeout as e:
            logger.error(f"Timeout during posting: {e}")
            page.screenshot(path=proof_path)
            browser.close()
            return False
        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            try:
                page.screenshot(path=proof_path)
            except Exception:
                pass
            browser.close()
            return False


def process_approved_posts(vault_path: Path, session_dir: str, dry_run: bool = False):
    """Find and post all approved LinkedIn drafts."""
    approved_dir = vault_path / "Approved"
    done_dir = vault_path / "Done"
    logs_dir = vault_path / "Logs"

    done_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    if not approved_dir.exists():
        logger.info("No /Approved/ directory found.")
        return

    # Find LinkedIn posts
    linkedin_files = list(approved_dir.glob("LINKEDIN_*.md"))

    if not linkedin_files:
        logger.info("No approved LinkedIn posts to process.")
        return

    logger.info(f"Found {len(linkedin_files)} approved LinkedIn post(s).")

    for file_path in linkedin_files:
        logger.info(f"Processing: {file_path.name}")

        post_data = extract_post_content(file_path)
        if not post_data:
            logger.warning(f"Skipping {file_path.name} — could not extract content.")
            continue

        # Proof screenshot path
        proof_name = file_path.stem + "_proof.png"
        proof_path = str(done_dir / proof_name)

        # Post it
        success = post_to_linkedin(post_data["content"], session_dir, proof_path, dry_run=dry_run)

        if success:
            # Update file status and move to Done
            content = file_path.read_text(encoding="utf-8")
            content = content.replace("status: pending_approval", "status: posted")
            content = content.replace("status: approved", "status: posted")
            content += f"\n\n---\n_Posted to LinkedIn at {datetime.now().isoformat()}_\n"

            done_path = done_dir / file_path.name
            done_path.write_text(content, encoding="utf-8")

            if not dry_run:
                file_path.unlink()  # Remove from /Approved/

            # Log
            log_action(logs_dir, "linkedin_posted", f"Posted: {file_path.name}")
            logger.info(f"Successfully posted: {file_path.name}")
        else:
            log_action(logs_dir, "linkedin_failed", f"Failed to post: {file_path.name}")
            logger.error(f"Failed to post: {file_path.name}")


def log_action(logs_dir: Path, action_type: str, details: str):
    """Append to daily log."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.md"
    entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **{action_type}**: {details}\n"

    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        content += entry
    else:
        content = f"# Activity Log - {today}\n\n{entry}"

    log_file.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="AI Employee LinkedIn Auto-Poster")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Open browser for manual LinkedIn login (first-time setup)",
    )
    parser.add_argument(
        "--session-dir",
        default=SESSION_DIR,
        help=f"Browser session directory (default: {SESSION_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without posting",
    )
    args = parser.parse_args()

    if args.login:
        login_to_linkedin(args.session_dir)
        return

    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    if args.dry_run:
        logger.info("[DRY RUN MODE] No posts will be made.")

    process_approved_posts(vault_path, args.session_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
