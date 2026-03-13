"""
Twitter/X Auto-Poster for AI Employee.

Reads approved tweet drafts from /Approved/ and posts them
via Playwright browser automation. Enforces 280-character limit.

Usage:
    uv run python scripts/twitter_poster.py --vault ./AI_Employee_Vault
    uv run python scripts/twitter_poster.py --login   # First-time Twitter login
    uv run python scripts/twitter_poster.py --dry-run
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
logger = logging.getLogger("TwitterPoster")

# Persistent browser session directory
SESSION_DIR = "twitter_session"

# Twitter character limit
TWITTER_CHAR_LIMIT = 280


def extract_post_content(file_path: Path) -> dict | None:
    """Extract tweet content from a TWITTER_*.md file."""
    content = file_path.read_text(encoding="utf-8")

    # Try Twitter-specific header first
    post_match = re.search(
        r"## Twitter Post Draft\s*\n(.*?)(?=\n## |\Z)",
        content,
        re.DOTALL,
    )

    if not post_match:
        # Fallback headers
        for header in ["## Tweet Draft", "## Post Draft", "## Proposed Action", "## Content"]:
            post_match = re.search(
                rf"{re.escape(header)}\s*\n(.*?)(?=\n## |\Z)",
                content,
                re.DOTALL,
            )
            if post_match:
                break

    if not post_match:
        logger.warning(f"Could not extract tweet content from {file_path.name}")
        return None

    post_body = post_match.group(1).strip()

    # Extract hashtags
    hashtag_match = re.search(r"## Hashtags\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    hashtags = hashtag_match.group(1).strip() if hashtag_match else ""

    full_tweet = post_body
    if hashtags:
        full_tweet += " " + hashtags

    # Character limit warning
    char_count = len(full_tweet)
    if char_count > TWITTER_CHAR_LIMIT:
        logger.warning(
            f"Tweet exceeds {TWITTER_CHAR_LIMIT} chars ({char_count} chars). "
            f"Content may be truncated by Twitter."
        )

    return {
        "content": full_tweet,
        "char_count": char_count,
        "filename": file_path.name,
        "path": file_path,
    }


def login_to_twitter(session_dir: str):
    """Open a headed browser for manual Twitter login. Saves session."""
    Path(session_dir).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=session_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://x.com/i/flow/login")

        logger.info("Please log in to Twitter/X in the browser window.")
        logger.info("After logging in, close the browser window to save the session.")

        try:
            page.wait_for_event("close", timeout=300000)  # 5 min timeout
        except Exception:
            pass

        browser.close()

    logger.info(f"Twitter session saved to {session_dir}/")


def post_to_twitter(post_content: str, session_dir: str, proof_path: str, dry_run: bool = False, interactive_login: bool = False) -> bool:
    """Post a tweet to Twitter/X using Playwright."""
    if dry_run:
        char_count = len(post_content)
        over = f" (OVER by {char_count - TWITTER_CHAR_LIMIT})" if char_count > TWITTER_CHAR_LIMIT else ""
        logger.info(f"[DRY RUN] Would tweet ({char_count} chars{over}): {post_content[:100]}...")
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
            page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)

            # Click the tweet composer
            composer = page.locator(
                "div[data-testid='tweetTextarea_0'], "
                "div[role='textbox'][data-testid='tweetTextarea_0']"
            )

            if composer.count() == 0:
                if interactive_login:
                    logger.info("Please log in to Twitter/X in the browser window.")
                    start = time.time()
                    while time.time() - start < 300:
                        url = page.url
                        if "x.com/home" in url or ("x.com" in url and "/login" not in url and "/i/flow" not in url):
                            composer = page.locator(
                                "div[data-testid='tweetTextarea_0'], "
                                "div[role='textbox'][data-testid='tweetTextarea_0']"
                            )
                            if composer.count() > 0:
                                logger.info("Login detected!")
                                time.sleep(2)
                                break
                        time.sleep(3)
                    else:
                        logger.error("Login timeout.")
                        page.screenshot(path=proof_path)
                        browser.close()
                        return False
                else:
                    logger.error("Not logged in or Twitter UI changed. Run with --login-and-post first.")
                    page.screenshot(path=proof_path)
                    browser.close()
                    return False

            # Click and type into the composer
            composer.first.click()
            time.sleep(1)
            page.keyboard.type(post_content, delay=15)
            logger.info(f"Typed tweet ({len(post_content)} chars)")
            time.sleep(2)

            # Click the Post/Tweet button
            post_btn = page.locator(
                "button[data-testid='tweetButtonInline'], "
                "button[data-testid='tweetButton']"
            )

            if post_btn.count() == 0:
                logger.error("Post button not found. Twitter UI may have changed.")
                page.screenshot(path=proof_path)
                browser.close()
                return False

            post_btn.first.click()
            logger.info("Clicked Post button")
            time.sleep(5)

            # Take proof screenshot
            page.screenshot(path=proof_path)
            logger.info(f"Tweet submitted. Proof: {proof_path}")

            browser.close()
            return True

        except PlaywrightTimeout as e:
            logger.error(f"Timeout: {e}")
            page.screenshot(path=proof_path)
            browser.close()
            return False
        except Exception as e:
            logger.error(f"Error posting to Twitter: {e}")
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


def process_approved_tweets(vault_path: Path, session_dir: str, dry_run: bool = False, interactive_login: bool = False):
    """Find and post all approved Twitter drafts."""
    approved_dir = vault_path / "Approved"
    done_dir = vault_path / "Done"
    logs_dir = vault_path / "Logs"

    done_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    if not approved_dir.exists():
        logger.info("No /Approved/ directory found.")
        return

    twitter_files = list(approved_dir.glob("TWITTER_*.md"))

    if not twitter_files:
        logger.info("No approved Twitter posts to process.")
        return

    logger.info(f"Found {len(twitter_files)} approved tweet(s).")

    for file_path in twitter_files:
        logger.info(f"Processing: {file_path.name}")

        post_data = extract_post_content(file_path)
        if not post_data:
            logger.warning(f"Skipping {file_path.name} — could not extract content.")
            continue

        proof_name = file_path.stem + "_proof.png"
        proof_path = str(done_dir / proof_name)

        success = post_to_twitter(post_data["content"], session_dir, proof_path, dry_run=dry_run, interactive_login=interactive_login)

        if success:
            content = file_path.read_text(encoding="utf-8")
            content = content.replace("status: pending_approval", "status: posted")
            content = content.replace("status: approved", "status: posted")
            content += f"\n\n---\n_Posted to Twitter/X at {datetime.now().isoformat()} ({post_data['char_count']} chars)_\n"

            done_path = done_dir / file_path.name
            done_path.write_text(content, encoding="utf-8")

            if not dry_run:
                file_path.unlink()

            log_action(logs_dir, "twitter_posted", f"Posted: {file_path.name} ({post_data['char_count']} chars)")
            logger.info(f"Successfully posted: {file_path.name}")
        else:
            log_action(logs_dir, "twitter_failed", f"Failed to post: {file_path.name}")
            logger.error(f"Failed to post: {file_path.name}")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Twitter/X Auto-Poster")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Open browser for manual Twitter login (first-time setup)",
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
    parser.add_argument(
        "--login-and-post",
        action="store_true",
        help="Login interactively then post in one session",
    )
    args = parser.parse_args()

    if args.login:
        login_to_twitter(args.session_dir)
        return

    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    if args.dry_run:
        logger.info("[DRY RUN MODE] No tweets will be posted.")

    process_approved_tweets(vault_path, args.session_dir, dry_run=args.dry_run, interactive_login=args.login_and_post)


if __name__ == "__main__":
    main()
