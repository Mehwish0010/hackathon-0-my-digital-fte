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

    # Extract image path if present
    image_match = re.search(r"## Image\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    image_path = image_match.group(1).strip() if image_match else None

    return {
        "content": full_post,
        "filename": file_path.name,
        "path": file_path,
        "image_path": image_path,
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


def _wait_for_fb_login(page, timeout=300):
    """Wait until user is logged in to Facebook."""
    logger.info("Waiting for you to log in... (checking for feed page)")
    start = time.time()
    while time.time() - start < timeout:
        url = page.url
        # Facebook redirects to / or /home.php after login
        if "facebook.com" in url and "/login" not in url and "checkpoint" not in url:
            # Dismiss any popups (e.g., "Remember password", notifications)
            for dismiss_text in ["Not now", "Not Now", "Skip", "Close", "OK"]:
                try:
                    dismiss_btn = page.locator(f"[aria-label='{dismiss_text}'], a:has-text('{dismiss_text}'), span:has-text('{dismiss_text}')")
                    if dismiss_btn.count() > 0:
                        dismiss_btn.first.click(timeout=2000)
                        logger.info(f"Dismissed popup: {dismiss_text}")
                        time.sleep(1)
                except Exception:
                    pass
            # Check if we see the composer (means we're on the feed)
            composer = page.locator(
                "[aria-label*=\"What's on your mind\"], "
                "[role='button']:has-text('on your mind'), "
                "div[class*='x1i10hfl']:has-text('on your mind')"
            )
            if composer.count() > 0:
                logger.info("Login detected! Proceeding...")
                time.sleep(2)
                return True
        time.sleep(3)
    logger.error("Login timeout — did not detect logged-in state.")
    return False


def _wait_for_mfb_login(page, timeout=300):
    """Wait until user is logged in on mobile Facebook."""
    logger.info("Waiting for you to log in on mobile Facebook...")
    start = time.time()
    while time.time() - start < timeout:
        url = page.url
        # Check various post-login URLs
        if "facebook.com" in url and "/login" not in url and "checkpoint" not in url and "recover" not in url:
            logger.info(f"Login detected! URL: {url}")
            time.sleep(2)
            return True
        time.sleep(3)
    logger.error("Login timeout.")
    return False


def post_to_facebook(post_content: str, session_dir: str, proof_path: str, dry_run: bool = False, interactive_login: bool = False) -> bool:
    """Post content to Facebook using mobile site (m.facebook.com) for reliability."""
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
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)

            # Check if logged in
            composer = page.locator(
                "[aria-label*=\"What's on your mind\"], "
                "[role='button']:has-text('on your mind')"
            )

            if composer.count() == 0:
                if interactive_login:
                    page.goto("https://www.facebook.com/login", wait_until="domcontentloaded", timeout=15000)
                    logger.info("Please log in to Facebook in the browser window.")
                    if not _wait_for_fb_login(page, timeout=300):
                        page.screenshot(path=proof_path)
                        browser.close()
                        return False
                    page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5)
                    composer = page.locator(
                        "[aria-label*=\"What's on your mind\"], "
                        "[role='button']:has-text('on your mind')"
                    )
                else:
                    logger.error("Not logged in. Run with --login-and-post.")
                    page.screenshot(path=proof_path)
                    browser.close()
                    return False

            # Step 1: Click composer
            composer.first.click()
            time.sleep(3)

            # Step 2: Handle "Review audience" -> Continue -> "Update settings" -> Done
            review = page.locator("text='Review audience'")
            if review.count() > 0:
                logger.info("Review audience popup detected")
                cont = page.locator("div[role='button']:has-text('Continue')")
                if cont.count() > 0:
                    cont.first.click(force=True)
                    logger.info("Clicked Continue")
                    time.sleep(3)

                # Now "Update settings" appears — click Done to accept current settings
                update = page.locator("text='Update settings'")
                if update.count() > 0:
                    logger.info("Update settings popup detected")
                    done_btn = page.locator("div[role='button']:has-text('Done')")
                    if done_btn.count() > 0:
                        done_btn.first.click(force=True)
                        logger.info("Clicked Done")
                        time.sleep(3)
                    else:
                        # Try Save button
                        save_btn = page.locator("div[role='button']:has-text('Save')")
                        if save_btn.count() > 0:
                            save_btn.first.click(force=True)
                            logger.info("Clicked Save")
                            time.sleep(3)

            # Step 3: Composer might have closed, re-open
            editor = page.locator("div[contenteditable='true'][role='textbox']")
            if editor.count() == 0 or not editor.first.is_visible():
                logger.info("Re-opening composer...")
                composer2 = page.locator(
                    "[aria-label*=\"What's on your mind\"], "
                    "[role='button']:has-text('on your mind')"
                )
                if composer2.count() > 0:
                    composer2.first.click(force=True)
                    time.sleep(3)

            # Step 4: Type content
            editor = page.locator("div[contenteditable='true'][role='textbox']")
            editor.wait_for(state="visible", timeout=15000)
            editor.click(force=True)
            time.sleep(1)
            page.keyboard.type(post_content, delay=15)
            logger.info(f"Typed post content ({len(post_content)} chars)")
            time.sleep(2)

            page.screenshot(path=proof_path.replace(".png", "_before.png"))

            # Step 5: Click Post via JavaScript (force click doesn't work on FB)
            posted = page.evaluate("""() => {
                // Find all elements with aria-label="Post" and role="button"
                const btns = document.querySelectorAll('div[aria-label="Post"][role="button"]');
                for (const btn of btns) {
                    // Check if it's visible and inside the create post dialog
                    const rect = btn.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        btn.click();
                        return 'clicked_aria';
                    }
                }
                // Fallback: find the blue Post button by text
                const spans = document.querySelectorAll('span');
                for (const span of spans) {
                    if (span.textContent.trim() === 'Post') {
                        const parent = span.closest('div[role="button"]');
                        if (parent) {
                            parent.click();
                            return 'clicked_span';
                        }
                    }
                }
                return 'not_found';
            }""")
            logger.info(f"Post button click result: {posted}")
            if posted == 'not_found':
                logger.info("Trying Ctrl+Enter as fallback")
                page.keyboard.press("Control+Enter")

            # Step 6: Wait and handle any post-submit dialog
            time.sleep(5)
            update2 = page.locator("text='Update settings'")
            if update2.count() > 0:
                done2 = page.locator("div[role='button']:has-text('Done')")
                if done2.count() > 0:
                    done2.first.click(force=True)
                    logger.info("Clicked Done on post-submit dialog")
                else:
                    save2 = page.locator("div[role='button']:has-text('Save')")
                    if save2.count() > 0:
                        save2.first.click(force=True)
                        logger.info("Clicked Save on post-submit dialog")

            time.sleep(5)

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


def post_to_instagram(post_content: str, session_dir: str, proof_path: str, dry_run: bool = False, interactive_login: bool = False, image_path: str = None) -> bool:
    """Post content to Instagram using desktop web with image upload."""
    if dry_run:
        logger.info(f"[DRY RUN] Would post to Instagram: {post_content[:100]}...")
        return True

    if not image_path or not Path(image_path).exists():
        logger.error(f"Instagram requires an image. Path: {image_path}")
        return False

    Path(session_dir).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=session_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        try:
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)

            # Check if logged in — look for create/new post button
            create_btn = page.locator(
                "svg[aria-label='New post'], "
                "[aria-label='New post'], "
                "a[href='/create/style/'], "
                "svg[aria-label='New Post']"
            )

            if create_btn.count() == 0:
                if interactive_login:
                    logger.info("Please log in to Instagram in the browser window.")
                    # Wait for login
                    start = time.time()
                    while time.time() - start < 300:
                        url = page.url
                        if "instagram.com" in url and "/accounts/login" not in url:
                            create_btn = page.locator(
                                "svg[aria-label='New post'], "
                                "[aria-label='New post'], "
                                "svg[aria-label='New Post']"
                            )
                            if create_btn.count() > 0:
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
                    logger.error("Not logged in. Run with --login-and-post.")
                    page.screenshot(path=proof_path)
                    browser.close()
                    return False

            # Dismiss any "Turn on Notifications" popup
            try:
                not_now = page.locator("button:has-text('Not Now'), button:has-text('Not now')")
                if not_now.count() > 0:
                    not_now.first.click()
                    logger.info("Dismissed notifications popup")
                    time.sleep(1)
            except Exception:
                pass

            # Step 1: Click "New post" / "+" button
            create_btn.first.click()
            time.sleep(3)

            # Step 2: Upload image via file input
            # Instagram creates a hidden file input when the create dialog opens
            file_input = page.locator("input[type='file'][accept*='image']")
            if file_input.count() == 0:
                # Sometimes need to wait a bit more
                time.sleep(2)
                file_input = page.locator("input[type='file']")

            if file_input.count() > 0:
                file_input.first.set_input_files(image_path)
                logger.info(f"Uploaded image: {image_path}")
                time.sleep(5)
            else:
                logger.error("Could not find file input for image upload")
                page.screenshot(path=proof_path)
                browser.close()
                return False

            # Step 3: Handle crop/resize screen — click "Next"
            # May need to dismiss "Crop" dialog first
            for _ in range(3):
                next_btn = page.locator(
                    "div[role='button']:has-text('Next'), "
                    "button:has-text('Next')"
                )
                if next_btn.count() > 0:
                    next_btn.first.click()
                    logger.info("Clicked Next")
                    time.sleep(3)
                else:
                    break

            # Step 4: Type caption
            caption_field = page.locator(
                "textarea[aria-label*='Write a caption'], "
                "div[aria-label*='Write a caption'], "
                "textarea[placeholder*='Write a caption']"
            )
            if caption_field.count() > 0:
                caption_field.first.click()
                time.sleep(1)
                page.keyboard.type(post_content, delay=15)
                logger.info(f"Typed caption ({len(post_content)} chars)")
                time.sleep(2)
            else:
                logger.warning("Could not find caption field")

            page.screenshot(path=proof_path.replace(".png", "_before.png"))

            # Step 5: Click "Share"
            share_btn = page.locator(
                "div[role='button']:has-text('Share'), "
                "button:has-text('Share')"
            )
            if share_btn.count() > 0:
                share_btn.first.click()
                logger.info("Clicked Share")
                time.sleep(10)
            else:
                logger.error("Could not find Share button")
                page.screenshot(path=proof_path)
                browser.close()
                return False

            # Wait for "Post shared" confirmation or redirect
            time.sleep(5)

            page.screenshot(path=proof_path)
            logger.info(f"Instagram post submitted. Proof: {proof_path}")

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


def process_approved_posts(vault_path: Path, session_dir: str, platform: str = "facebook", dry_run: bool = False, interactive_login: bool = False):
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
            success = post_to_instagram(post_data["content"], session_dir, proof_path, dry_run=dry_run, interactive_login=interactive_login, image_path=post_data.get("image_path"))
        else:
            success = post_to_facebook(post_data["content"], session_dir, proof_path, dry_run=dry_run, interactive_login=interactive_login)

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
    parser.add_argument(
        "--login-and-post",
        action="store_true",
        help="Login interactively then post in one session (use when session expired)",
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
        process_approved_posts(vault_path, args.session_dir, "facebook", dry_run=args.dry_run, interactive_login=args.login_and_post)

    if args.platform in ("instagram", "both"):
        process_approved_posts(vault_path, args.session_dir, "instagram", dry_run=args.dry_run, interactive_login=args.login_and_post)


if __name__ == "__main__":
    main()
