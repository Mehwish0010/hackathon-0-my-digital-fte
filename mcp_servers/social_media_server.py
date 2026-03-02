"""
Social Media MCP Server for AI Employee.

Exposes tools for creating social media post drafts across platforms.
Does NOT post directly — creates draft files in /Pending_Approval/ for HITL.

Usage:
    uv run python mcp_servers/social_media_server.py

Register in .claude/settings.json to make tools available to Claude Code.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SocialMediaMCP")

# Initialize MCP server
mcp = FastMCP("AI Employee Social Media Server")

# Vault path
VAULT_PATH = Path(os.environ.get("VAULT_PATH", "./AI_Employee_Vault")).resolve()

# Platform configs
PLATFORMS = {
    "linkedin": {
        "prefix": "LINKEDIN",
        "char_limit": 3000,
        "header": "LinkedIn Post Draft",
        "type": "linkedin_post",
    },
    "facebook": {
        "prefix": "FACEBOOK",
        "char_limit": 63206,
        "header": "Facebook Post Draft",
        "type": "facebook_post",
    },
    "instagram": {
        "prefix": "INSTAGRAM",
        "char_limit": 2200,
        "header": "Instagram Post Draft",
        "type": "instagram_post",
    },
    "twitter": {
        "prefix": "TWITTER",
        "char_limit": 280,
        "header": "Twitter Post Draft",
        "type": "twitter_post",
    },
}


def _create_draft_file(
    platform: str,
    content: str,
    hashtags: str = "",
    notes: str = "",
    topic: str = "post",
) -> str:
    """Create a draft file in /Pending_Approval/ for a social media post."""
    pending_dir = VAULT_PATH / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    config = PLATFORMS.get(platform)
    if not config:
        raise ValueError(f"Unknown platform: {platform}. Use: {', '.join(PLATFORMS.keys())}")

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    slug = topic.replace(" ", "_")[:30]
    filename = f"{config['prefix']}_{slug}_{timestamp}.md"
    file_path = pending_dir / filename

    # Character count check
    full_content = content + (" " + hashtags if hashtags else "")
    char_count = len(full_content)
    char_warning = ""
    if char_count > config["char_limit"]:
        char_warning = (
            f"\n\n> **WARNING**: Content is {char_count} characters, "
            f"exceeding {platform}'s {config['char_limit']}-character limit. "
            f"Please edit before approving."
        )

    file_content = f"""---
type: {config['type']}
status: pending_approval
created: {now.isoformat()}
platform: {platform}
char_count: {char_count}
char_limit: {config['char_limit']}
---

## {config['header']}

{content}

## Hashtags

{hashtags if hashtags else '(none)'}

## Notes

{notes if notes else f'- Platform: {platform.title()}'}
- Character count: {char_count}/{config['char_limit']}
{char_warning}

## Instructions for Reviewer

- **To Approve**: Move this file to /Approved/
- **To Reject**: Move this file to /Rejected/
- **To Edit**: Modify the content above before approving
"""

    file_path.write_text(file_content, encoding="utf-8")
    logger.info(f"Created draft: {filename}")
    return filename


def _log_action(action_type: str, details: str):
    """Append to daily markdown log."""
    logs_dir = VAULT_PATH / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.md"
    entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **{action_type}**: {details}\n"

    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        content += entry
    else:
        content = f"# Activity Log - {today}\n\n{entry}"

    log_file.write_text(content, encoding="utf-8")


@mcp.tool()
def create_social_post_draft(
    platform: str,
    content: str,
    hashtags: str = "",
    notes: str = "",
    topic: str = "post",
) -> str:
    """Create a social media post draft for human approval.

    The draft is saved to /Pending_Approval/ — it does NOT post directly.

    Args:
        platform: Target platform — "linkedin", "facebook", "instagram", or "twitter"
        content: The post content/caption text
        hashtags: Hashtags to append (e.g. "#AI #automation")
        notes: Additional notes for the reviewer
        topic: Short topic slug for the filename

    Returns:
        Confirmation with filename and character count.
    """
    platform = platform.lower().strip()
    if platform == "x":
        platform = "twitter"

    if platform not in PLATFORMS:
        return f"Unknown platform '{platform}'. Supported: {', '.join(PLATFORMS.keys())}"

    try:
        filename = _create_draft_file(platform, content, hashtags, notes, topic)
        config = PLATFORMS[platform]
        full_content = content + (" " + hashtags if hashtags else "")
        char_count = len(full_content)

        _log_action("social_draft_created", f"{platform}: {filename}")

        result = (
            f"Draft created: {filename}\n"
            f"- Platform: {platform.title()}\n"
            f"- Characters: {char_count}/{config['char_limit']}\n"
        )

        if char_count > config["char_limit"]:
            result += f"- **WARNING**: Over limit by {char_count - config['char_limit']} characters!\n"

        result += f"\nMove from /Pending_Approval/ to /Approved/ to queue for posting."
        return result

    except Exception as e:
        logger.error(f"Error creating draft: {e}")
        return f"Error creating draft: {e}"


@mcp.tool()
def list_pending_social_posts() -> str:
    """List all pending social media post drafts.

    Returns:
        Formatted list of pending posts across all platforms.
    """
    pending_dir = VAULT_PATH / "Pending_Approval"
    approved_dir = VAULT_PATH / "Approved"

    results = []

    for label, directory in [("Pending Approval", pending_dir), ("Approved (queued)", approved_dir)]:
        if not directory.exists():
            continue

        for prefix_name, config in PLATFORMS.items():
            prefix = config["prefix"]
            files = sorted(directory.glob(f"{prefix}_*.md"))
            for f in files:
                results.append(f"- [{label}] **{f.name}** ({prefix_name.title()})")

    if not results:
        return "No pending social media posts found."

    return f"**Social Media Posts:**\n\n" + "\n".join(results)


@mcp.tool()
def get_social_post_status(filename: str) -> str:
    """Check the status of a specific social media post draft.

    Args:
        filename: The filename to check (e.g. "LINKEDIN_ai_update_20260227.md")

    Returns:
        Current status and location of the post.
    """
    folders = {
        "Pending Approval": VAULT_PATH / "Pending_Approval",
        "Approved": VAULT_PATH / "Approved",
        "Done": VAULT_PATH / "Done",
        "Rejected": VAULT_PATH / "Rejected",
    }

    for status, directory in folders.items():
        file_path = directory / filename
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            # Extract frontmatter status
            for line in content.split("\n"):
                if line.strip().startswith("status:"):
                    fm_status = line.split(":", 1)[1].strip()
                    return (
                        f"**{filename}**\n"
                        f"- Location: /{directory.name}/\n"
                        f"- Status: {fm_status}\n"
                    )
            return f"**{filename}** found in /{directory.name}/ (status: {status.lower()})"

    return f"File '{filename}' not found in any vault folder."


@mcp.tool()
def cross_post(
    content: str,
    platforms: list[str] | None = None,
    hashtags: str = "",
    topic: str = "post",
) -> str:
    """Create adapted drafts for multiple platforms at once.

    Automatically adjusts content per platform:
    - Twitter: Truncated to 280 chars with warning if too long
    - Instagram: Formatted as caption
    - LinkedIn/Facebook: Full content

    Args:
        content: The core message to adapt
        platforms: List of platforms (default: all four)
        hashtags: Hashtags to include
        topic: Short topic for filenames

    Returns:
        Summary of all created drafts.
    """
    if platforms is None:
        platforms = ["linkedin", "facebook", "instagram", "twitter"]

    # Handle comma-separated string input
    if isinstance(platforms, str):
        platforms = [p.strip() for p in platforms.split(",")]

    platforms = [p.lower().strip().replace("x", "twitter") for p in platforms]

    results = []
    for platform in platforms:
        if platform not in PLATFORMS:
            results.append(f"- {platform}: SKIPPED (unknown platform)")
            continue

        config = PLATFORMS[platform]
        adapted_content = content

        # Adapt content for Twitter
        if platform == "twitter":
            full_text = content + (" " + hashtags if hashtags else "")
            if len(full_text) > TWITTER_CHAR_LIMIT:
                # Truncate content, keep hashtags
                max_content_len = TWITTER_CHAR_LIMIT - len(hashtags) - 4  # " " + "..."
                if max_content_len > 20:
                    adapted_content = content[:max_content_len] + "..."
                else:
                    adapted_content = content[:TWITTER_CHAR_LIMIT - 3] + "..."
                    hashtags = ""

        try:
            filename = _create_draft_file(platform, adapted_content, hashtags, "", topic)
            char_count = len(adapted_content + (" " + hashtags if hashtags else ""))
            warning = " **OVER LIMIT**" if char_count > config["char_limit"] else ""
            results.append(
                f"- {platform.title()}: {filename} ({char_count}/{config['char_limit']} chars{warning})"
            )
        except Exception as e:
            results.append(f"- {platform.title()}: ERROR — {e}")

    _log_action("cross_post_created", f"Drafts for: {', '.join(platforms)}")

    return (
        f"**Cross-post drafts created:**\n\n"
        + "\n".join(results)
        + "\n\nReview each in /Pending_Approval/ and move to /Approved/ to queue for posting."
    )


# Twitter char limit constant for cross_post
TWITTER_CHAR_LIMIT = 280


if __name__ == "__main__":
    mcp.run()
