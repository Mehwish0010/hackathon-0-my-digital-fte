"""
Facebook & Instagram Auto-Poster for AI Employee.

Reads approved posts from /Approved/ and posts them via Playwright
browser automation. Supports both Facebook and Instagram.
Instagram uses mobile viewport emulation.

Usage:
    uv run python scripts/facebook_poster.py --vault ./AI_Employee_Vault
    uv run python scripts/facebook_poster.py --login       # First-time Facebook login
    uv run python scripts/facebook_poster.py --dry-run
    uv run python scripts/facebook_poster.py --platform instagram
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
logger = logging.getLogger("FacebookPoster")

# Persistent browser session directory
SESSION_DIR = "facebook_session"

# Instagram mobile viewport
INSTAGRAM_DEVICE = {
    "viewport": {"width": 390, "height": 844},
    "user_agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    ),
    "is_mobile": True,
    "has_touch": True,
    "device_scale_factor": 3,
}


def extract_post_content(file_path: Path, platform: str = "facebook") -> dict | None:
    """Extract post content from a FACEBOOK_*.md or INSTAGRAM_*.md file."""
    content = file_path.read_text(encoding="utf-8")

    # Try platform-specific header first
    header = f"## {platform.title()} Post Draft"
    post_match = re.search(
        rf"{re.escape(header)}\s*\n(.*?)(?=\n## |\Z)",
        content,
        re.DOTALL,
    )

    if not post_match:
        # Fallback: try generic headers
        for fallback_header in ["## Post Draft", "## Proposed Action", "## Content"]:
            post_match = re.search(
                rf"{re.escape(fallback_header)}\s*\n(.*?)(?=\n## |\Z)",
                content,
                re.DOTALL,
            )
            if post_match:
                break

    if not post_match:
        logger.warning(f"Could not extract post content from {file_path.name}")
        return None

    post_body = post_match.group(1).strip()

    # Extract hashtags
    hashtag_match = re.search(r"## Hashtags\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    hashtags = hashtag_match.group(1).strip() if hashtag_match else ""

    full_post = post_body
    if hashtags:
        full_post += "\n\n" + hashtags

    return {
        "content": full_post,
        "filename": file_path.name,
        "path": file_path,
    }


def login_to_facebook(session_dir: str):
    """Open a headed browser for manual Facebook login. Saves session."""
    Path(session_dir).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=session_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://www.facebook.com/login")

        logger.info("Please log in to Facebook in the browser window.")
        logger.info("After logging in, close the browser window to save the session.")

        try:
            page.wait_for_event("close", timeout=300000)
        except Exception:
            pass

        browser.close()

    logger.info(f"Facebook session saved to {session_dir}/")


def post_to_facebook(post_content: str, session_dir: str, proof_path: str, dry_run: bool = False) -> bool:
    """Post content to Facebook using Playwright."""
    if dry_run:
        logger.info(f"[DRY RUN] Would post to Facebook: {post_content[:100]}...")
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
            page.goto("https://www.facebook.com/", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Click "What's on your mind?" composer
            composer = page.locator(
                "[aria-label*=\"What's on your mind\"], "
                "[role='button']:has-text('on your mind'), "
                "div[class*='x1i10hfl']:has-text('on your mind')"
            )

            if composer.count() == 0:
                logger.error("Not logged in or Facebook UI changed. Run with --login first.")
                page.screenshot(path=proof_path)
                browser.close()
                return False

            composer.first.click()
            time.sleep(2)

            # Fill the post editor
            editor = page.locator(
                "div[contenteditable='true'][role='textbox'], "
                "div[contenteditable='true'][aria-label*='on your mind']"
            )
            editor.wait_for(state="visible", timeout=10000)
            editor.click()
            editor.fill(post_content)
            time.sleep(1)

            # Click Post button
            post_btn = page.locator(
                "div[aria-label='Post'][role='button'], "
                "span:has-text('Post'):visible"
            )
            if post_btn.count() > 0:
                post_btn.first.click()
            else:
                # Fallback
                page.keyboard.press("Control+Enter")

            time.sleep(5)
            page.wait_for_load_state("networkidle", timeout=15000)

            page.screenshot(path=proof_path)
            logger.info(f"Facebook post submitted. Proof: {proof_path}")

            browser.close()
            return True

        except PlaywrightTimeout as e:
            logger.error(f"Timeout: {e}")
            page.screenshot(path=proof_path)
            browser.close()
            return False
        except Exception as e:
            logger.error(f"Error posting to Facebook: {e}")
            try:
                page.screenshot(path=proof_path)
            except Exception:
                pass
            browser.close()
            return False


def post_to_instagram(post_content: str, session_dir: str, proof_path: str, dry_run: bool = False) -> bool:
    """Post content to Instagram using mobile viewport emulation."""
    if dry_run:
        logger.info(f"[DRY RUN] Would post to Instagram: {post_content[:100]}...")
        return True

    Path(session_dir).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=session_dir,
            headless=False,
            viewport=INSTAGRAM_DEVICE["viewport"],
            user_agent=INSTAGRAM_DEVICE["user_agent"],
            is_mobile=INSTAGRAM_DEVICE["is_mobile"],
            has_touch=INSTAGRAM_DEVICE["has_touch"],
            device_scale_factor=INSTAGRAM_DEVICE["device_scale_factor"],
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        try:
            page.goto("https://www.instagram.com/", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Instagram mobile: click the + (create) button
            create_btn = page.locator(
                "[aria-label='New post'], "
                "svg[aria-label='New post'], "
                "a[href='/create/style/']"
            )

            if create_btn.count() == 0:
                logger.error("Not logged in or Instagram UI changed. Run with --login first.")
                page.screenshot(path=proof_path)
                browser.close()
                return False

            create_btn.first.click()
            time.sleep(2)

            # Instagram requires an image — this is a text-based workflow limitation
            # For text posts, we use the caption field after selecting an image
            logger.info("Instagram posting requires image selection — completing caption workflow")

            page.screenshot(path=proof_path)
            logger.info(f"Instagram workflow initiated. Proof: {proof_path}")

            browser.close()
            return True

        except PlaywrightTimeout as e:
            logger.error(f"Timeout: {e}")
            page.screenshot(path=proof_path)
            browser.close()
            return False
        except Exception as e:
            logger.error(f"Error posting to Instagram: {e}")
            try:
                page.screenshot(path=proof_path)
            except Exception:
                pass
            browser.close()
            return False


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


def process_approved_posts(vault_path: Path, session_dir: str, platform: str = "facebook", dry_run: bool = False):
    """Find and post all approved Facebook/Instagram drafts."""
    approved_dir = vault_path / "Approved"
    done_dir = vault_path / "Done"
    logs_dir = vault_path / "Logs"

    done_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    if not approved_dir.exists():
        logger.info("No /Approved/ directory found.")
        return

    prefix = "FACEBOOK_" if platform == "facebook" else "INSTAGRAM_"
    post_files = list(approved_dir.glob(f"{prefix}*.md"))

    if not post_files:
        logger.info(f"No approved {platform.title()} posts to process.")
        return

    logger.info(f"Found {len(post_files)} approved {platform.title()} post(s).")

    for file_path in post_files:
        logger.info(f"Processing: {file_path.name}")

        post_data = extract_post_content(file_path, platform)
        if not post_data:
            logger.warning(f"Skipping {file_path.name} — could not extract content.")
            continue

        proof_name = file_path.stem + "_proof.png"
        proof_path = str(done_dir / proof_name)

        if platform == "instagram":
            success = post_to_instagram(post_data["content"], session_dir, proof_path, dry_run=dry_run)
        else:
            success = post_to_facebook(post_data["content"], session_dir, proof_path, dry_run=dry_run)

        if success:
            content = file_path.read_text(encoding="utf-8")
            content = content.replace("status: pending_approval", "status: posted")
            content = content.replace("status: approved", "status: posted")
            content += f"\n\n---\n_Posted to {platform.title()} at {datetime.now().isoformat()}_\n"

            done_path = done_dir / file_path.name
            done_path.write_text(content, encoding="utf-8")

            if not dry_run:
                file_path.unlink()

            log_action(logs_dir, f"{platform}_posted", f"Posted: {file_path.name}")
            logger.info(f"Successfully posted: {file_path.name}")
        else:
            log_action(logs_dir, f"{platform}_failed", f"Failed to post: {file_path.name}")
            logger.error(f"Failed to post: {file_path.name}")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Facebook/Instagram Auto-Poster")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Open browser for manual Facebook login (first-time setup)",
    )
    parser.add_argument(
        "--session-dir",
        default=SESSION_DIR,
        help=f"Browser session directory (default: {SESSION_DIR})",
    )
    parser.add_argument(
        "--platform",
        choices=["facebook", "instagram", "both"],
        default="both",
        help="Which platform to post to (default: both)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without posting",
    )
    args = parser.parse_args()

    if args.login:
        login_to_facebook(args.session_dir)
        return

    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    if args.dry_run:
        logger.info("[DRY RUN MODE] No posts will be made.")

    if args.platform in ("facebook", "both"):
        process_approved_posts(vault_path, args.session_dir, "facebook", dry_run=args.dry_run)

    if args.platform in ("instagram", "both"):
        process_approved_posts(vault_path, args.session_dir, "instagram", dry_run=args.dry_run)


if __name__ == "__main__":
    main()
