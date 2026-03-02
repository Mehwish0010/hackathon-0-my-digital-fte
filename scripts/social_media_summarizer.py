"""
Social Media Summarizer for AI Employee.

Generates social media activity summaries by scanning vault folders
for completed social posts and compiling engagement reports.
Output goes to /Briefings/social_summary_{date}.md for the CEO briefing.

Usage:
    uv run python scripts/social_media_summarizer.py --vault ./AI_Employee_Vault
    uv run python scripts/social_media_summarizer.py --days 7
"""

import argparse
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SocialMediaSummarizer")

# Platform prefixes
PLATFORM_PREFIXES = {
    "LINKEDIN_": "LinkedIn",
    "FACEBOOK_": "Facebook",
    "INSTAGRAM_": "Instagram",
    "TWITTER_": "Twitter/X",
}


def scan_completed_posts(vault_path: Path, days: int = 7) -> dict:
    """Scan /Done/ for completed social media posts within the time window."""
    done_dir = vault_path / "Done"
    if not done_dir.exists():
        return {}

    cutoff = datetime.now() - timedelta(days=days)
    results = {}

    for prefix, platform in PLATFORM_PREFIXES.items():
        posts = []
        for f in done_dir.glob(f"{prefix}*.md"):
            # Check file modification time
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                continue

            content = f.read_text(encoding="utf-8", errors="replace")

            # Extract status
            status = "unknown"
            for line in content.split("\n"):
                if line.strip().startswith("status:"):
                    status = line.split(":", 1)[1].strip()
                    break

            # Extract posted timestamp
            posted_at = None
            posted_match = re.search(r"_Posted to .+ at (.+?)_", content)
            if posted_match:
                try:
                    posted_at = posted_match.group(1).strip()
                except Exception:
                    pass

            posts.append({
                "filename": f.name,
                "status": status,
                "posted_at": posted_at or mtime.isoformat(),
                "file_date": mtime,
            })

        results[platform] = posts

    return results


def scan_pending_posts(vault_path: Path) -> dict:
    """Scan /Pending_Approval/ and /Approved/ for queued social posts."""
    pending = {}

    for folder_name in ["Pending_Approval", "Approved"]:
        folder = vault_path / folder_name
        if not folder.exists():
            continue

        for prefix, platform in PLATFORM_PREFIXES.items():
            if platform not in pending:
                pending[platform] = {"pending_approval": 0, "approved": 0}

            count = len(list(folder.glob(f"{prefix}*.md")))
            key = "pending_approval" if folder_name == "Pending_Approval" else "approved"
            pending[platform][key] = count

    return pending


def scan_audit_logs(vault_path: Path, days: int = 7) -> dict:
    """Scan JSON audit logs for social media related entries."""
    import json

    logs_dir = vault_path / "Logs"
    social_events = {"posted": 0, "failed": 0, "drafted": 0}

    now = datetime.now()
    for i in range(days):
        date = now - timedelta(days=i)
        log_file = logs_dir / f"{date.strftime('%Y-%m-%d')}.json"

        if not log_file.exists():
            continue

        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue

                action = entry.get("action_type", "")
                if "posted" in action and any(p.lower() in action for p in ["facebook", "instagram", "twitter", "linkedin"]):
                    social_events["posted"] += 1
                elif "failed" in action and any(p.lower() in action for p in ["facebook", "instagram", "twitter", "linkedin"]):
                    social_events["failed"] += 1
                elif "draft" in action and "social" in action:
                    social_events["drafted"] += 1

    return social_events


def generate_summary(vault_path: Path, days: int = 7) -> str:
    """Generate the social media summary markdown."""
    now = datetime.now()

    completed = scan_completed_posts(vault_path, days)
    pending = scan_pending_posts(vault_path)
    audit_events = scan_audit_logs(vault_path, days)

    total_posted = sum(len(posts) for posts in completed.values())

    summary = f"""---
type: social_media_summary
date: {now.strftime('%Y-%m-%d')}
generated: {now.isoformat()}
period_days: {days}
---

# Social Media Summary — {now.strftime('%A, %B %d, %Y')}

**Period**: Last {days} days

## Overview

- **Total posts published**: {total_posted}
- **Posts failed**: {audit_events.get('failed', 0)}
- **Drafts created**: {audit_events.get('drafted', 0)}

## Posts by Platform

| Platform | Published | Pending Approval | Approved (Queued) |
|----------|-----------|-----------------|-------------------|
"""

    for platform in ["LinkedIn", "Facebook", "Instagram", "Twitter/X"]:
        published = len(completed.get(platform, []))
        pend = pending.get(platform, {})
        pa = pend.get("pending_approval", 0)
        ap = pend.get("approved", 0)
        summary += f"| {platform} | {published} | {pa} | {ap} |\n"

    summary += "\n## Recent Posts\n\n"

    any_posts = False
    for platform, posts in completed.items():
        if not posts:
            continue
        any_posts = True
        summary += f"### {platform}\n\n"
        for post in sorted(posts, key=lambda x: x["posted_at"], reverse=True):
            summary += f"- **{post['filename']}** — {post['status']} ({post['posted_at'][:16]})\n"
        summary += "\n"

    if not any_posts:
        summary += "_No social media posts published in the last {days} days._\n\n"

    # Recommendations
    summary += "## Recommendations\n\n"

    recommendations = []
    for platform in ["LinkedIn", "Facebook", "Instagram", "Twitter/X"]:
        if len(completed.get(platform, [])) == 0:
            recommendations.append(f"- No {platform} posts this week — consider creating content")

    if total_posted < 3:
        recommendations.append("- Low posting frequency — aim for 3-5 posts per week across platforms")

    if audit_events.get("failed", 0) > 0:
        recommendations.append(
            f"- {audit_events['failed']} post(s) failed — check browser sessions and retry"
        )

    if not recommendations:
        recommendations.append("- Social media activity looks healthy. Keep it up!")

    summary += "\n".join(recommendations)

    summary += f"""

---
*Generated by Social Media Summarizer at {now.strftime('%H:%M:%S')}*
"""

    return summary


def main():
    parser = argparse.ArgumentParser(description="AI Employee Social Media Summarizer")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to summarize (default: 7)",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    briefings_dir = vault_path / "Briefings"
    briefings_dir.mkdir(parents=True, exist_ok=True)

    summary = generate_summary(vault_path, days=args.days)

    today = datetime.now().strftime("%Y-%m-%d")
    output_path = briefings_dir / f"social_summary_{today}.md"
    output_path.write_text(summary, encoding="utf-8")

    logger.info(f"Social media summary saved: {output_path.name}")

    # Also log it
    logs_dir = vault_path / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"{today}.md"
    entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **social_summary**: Generated {output_path.name}\n"

    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        content += entry
    else:
        content = f"# Activity Log - {today}\n\n{entry}"

    log_file.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
