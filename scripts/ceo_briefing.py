"""
CEO Briefing Generator for AI Employee.

Pulls from ALL sources: vault stats, Odoo financials, social media metrics,
audit logs, and business goals. Generates a comprehensive weekly briefing.

Usage:
    uv run python scripts/ceo_briefing.py --vault ./AI_Employee_Vault
    uv run python scripts/ceo_briefing.py --vault ./AI_Employee_Vault --period 7
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("CEOBriefing")


def get_vault_stats(vault_path: Path) -> dict:
    """Count items in each vault folder."""
    folders = [
        "Inbox", "Needs_Action", "In_Progress", "Done",
        "Pending_Approval", "Approved", "Rejected", "Plans",
    ]
    stats = {}
    for folder in folders:
        path = vault_path / folder
        if path.exists():
            files = [f for f in path.iterdir() if f.is_file() and not f.name.startswith(".")]
            stats[folder] = len(files)
        else:
            stats[folder] = 0
    return stats


def get_done_this_week(vault_path: Path, days: int = 7) -> list[str]:
    """List items completed in the last N days."""
    done_dir = vault_path / "Done"
    if not done_dir.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days)
    completed = []
    for f in done_dir.iterdir():
        if f.is_file() and not f.name.startswith("."):
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime >= cutoff:
                completed.append(f.name)

    return sorted(completed, reverse=True)


def get_stale_items(vault_path: Path, hours: int = 48) -> dict:
    """Find items that have been stuck too long."""
    stale = {}
    cutoff = datetime.now() - timedelta(hours=hours)

    for folder in ["Needs_Action", "Pending_Approval", "In_Progress"]:
        path = vault_path / folder
        if not path.exists():
            continue
        stuck = []
        for f in path.iterdir():
            if f.is_file() and not f.name.startswith("."):
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    age_hours = (datetime.now() - mtime).total_seconds() / 3600
                    stuck.append({"name": f.name, "age_hours": round(age_hours)})
        if stuck:
            stale[folder] = stuck

    return stale


def get_audit_summary(vault_path: Path, days: int = 7) -> dict:
    """Summarize audit log entries."""
    logs_dir = vault_path / "Logs"
    summary = {
        "total_entries": 0,
        "errors": 0,
        "by_action_type": {},
        "error_details": [],
    }

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
                except json.JSONDecodeError:
                    continue

                summary["total_entries"] += 1
                action = entry.get("action_type", "unknown")
                summary["by_action_type"][action] = summary["by_action_type"].get(action, 0) + 1

                result = entry.get("result", "")
                if "fail" in result.lower() or "error" in result.lower():
                    summary["errors"] += 1
                    summary["error_details"].append({
                        "action": action,
                        "error": result[:200],
                        "time": entry.get("timestamp", ""),
                    })

    return summary


def get_social_summary(vault_path: Path) -> str:
    """Read the latest social media summary if available."""
    briefings_dir = vault_path / "Briefings"
    if not briefings_dir.exists():
        return ""

    # Find most recent social summary
    summaries = sorted(briefings_dir.glob("social_summary_*.md"), reverse=True)
    if not summaries:
        return ""

    return summaries[0].read_text(encoding="utf-8", errors="replace")


def get_business_goals(vault_path: Path) -> str:
    """Read Business_Goals.md content."""
    goals_file = vault_path / "Business_Goals.md"
    if goals_file.exists():
        return goals_file.read_text(encoding="utf-8", errors="replace")
    return ""


def get_odoo_status(vault_path: Path) -> str:
    """Check Odoo availability from service health."""
    health_file = vault_path / "service_health.json"
    if not health_file.exists():
        return "not_configured"

    try:
        with open(health_file, "r", encoding="utf-8") as f:
            health = json.load(f)
        odoo = health.get("odoo", {})
        return odoo.get("status", "unknown")
    except Exception:
        return "unknown"


def generate_briefing(vault_path: Path, period_days: int = 7) -> str:
    """Generate the full CEO briefing."""
    now = datetime.now()

    # Gather all data
    vault_stats = get_vault_stats(vault_path)
    done_items = get_done_this_week(vault_path, period_days)
    stale_items = get_stale_items(vault_path)
    audit = get_audit_summary(vault_path, period_days)
    social_summary_raw = get_social_summary(vault_path)
    business_goals = get_business_goals(vault_path)
    odoo_status = get_odoo_status(vault_path)

    # Calculate completion rate
    total_done = len(done_items)
    total_pending = vault_stats.get("Needs_Action", 0) + vault_stats.get("In_Progress", 0)
    total_items = total_done + total_pending
    completion_rate = round(total_done / total_items * 100) if total_items > 0 else 0

    # Build briefing
    briefing = f"""---
type: ceo_briefing
date: {now.strftime('%Y-%m-%d')}
generated: {now.isoformat()}
period_days: {period_days}
---

# CEO Briefing — Week of {now.strftime('%B %d, %Y')}

## Executive Summary

"""

    # Executive summary
    if completion_rate >= 80:
        briefing += f"Strong week with a {completion_rate}% task completion rate. "
    elif completion_rate >= 50:
        briefing += f"Moderate progress with a {completion_rate}% completion rate. "
    else:
        briefing += f"Attention needed — only {completion_rate}% completion rate this week. "

    briefing += f"{total_done} tasks completed, {total_pending} still pending."

    if stale_items:
        total_stale = sum(len(items) for items in stale_items.values())
        briefing += f" {total_stale} item(s) are bottlenecked (>48h without progress)."

    if audit["errors"] > 0:
        briefing += f" {audit['errors']} error(s) occurred this week."

    # Revenue & Financials
    briefing += "\n\n## Revenue & Financials\n\n"

    if odoo_status == "healthy":
        briefing += (
            "Odoo is connected. Use `odoo_get_profit_loss` and `odoo_get_account_balance` "
            "MCP tools for live financial data.\n"
        )
    elif odoo_status == "not_configured":
        briefing += (
            "_Odoo is not configured._ Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD "
            "environment variables to enable financial reporting.\n"
        )
    else:
        briefing += f"_Odoo status: {odoo_status}._ Financial data may be unavailable.\n"

    # Check accounting folder
    accounting_dir = vault_path / "Accounting"
    if accounting_dir.exists():
        accounting_files = [f for f in accounting_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
        if accounting_files:
            briefing += f"\n{len(accounting_files)} file(s) in /Accounting/ for reference.\n"

    # Task Completion
    briefing += f"""
## Task Completion

- **Tasks completed this week**: {total_done}
- **Tasks pending action**: {vault_stats.get('Needs_Action', 0)}
- **Tasks in progress**: {vault_stats.get('In_Progress', 0)}
- **Completion rate**: {completion_rate}%
- **Inbox items**: {vault_stats.get('Inbox', 0)}

"""

    if done_items:
        briefing += "### Completed Items\n\n"
        for item in done_items[:15]:  # Top 15
            briefing += f"- {item}\n"
        if len(done_items) > 15:
            briefing += f"- _...and {len(done_items) - 15} more_\n"
        briefing += "\n"

    # Bottlenecks
    briefing += "## Bottlenecks & Blockers\n\n"

    if stale_items:
        for folder, items in stale_items.items():
            for item in items:
                briefing += f"- **{folder}**: {item['name']} (stuck {item['age_hours']}h)\n"
    else:
        briefing += "No bottlenecks detected — all items progressing normally.\n"

    # Pending Approvals
    if vault_stats.get("Pending_Approval", 0) > 0:
        briefing += f"\n**{vault_stats['Pending_Approval']} item(s) awaiting your approval** in /Pending_Approval/.\n"

    # Social Media
    briefing += "\n## Social Media Performance\n\n"

    if social_summary_raw:
        # Extract key metrics from social summary
        # Look for the overview section
        overview_match = None
        for line in social_summary_raw.split("\n"):
            if "Total posts published" in line:
                briefing += f"{line.strip()}\n"
            elif "Posts failed" in line:
                briefing += f"{line.strip()}\n"

        # Check for platform table
        if "| Platform" in social_summary_raw:
            table_start = social_summary_raw.index("| Platform")
            table_lines = []
            for line in social_summary_raw[table_start:].split("\n"):
                if line.strip().startswith("|"):
                    table_lines.append(line)
                elif table_lines:
                    break
            if table_lines:
                briefing += "\n" + "\n".join(table_lines) + "\n"

        briefing += "\n_See full details in latest social_summary report._\n"
    else:
        briefing += "_No social media summary available. Run social_media_summarizer.py to generate._\n"

    # Proactive Suggestions
    briefing += "\n## Proactive Suggestions\n\n"

    suggestions = []

    if vault_stats.get("Inbox", 0) > 5:
        suggestions.append(f"- {vault_stats['Inbox']} items in Inbox — consider triaging")

    if vault_stats.get("Pending_Approval", 0) > 3:
        suggestions.append(f"- {vault_stats['Pending_Approval']} items awaiting approval — review soon")

    if completion_rate < 70:
        suggestions.append("- Completion rate below 70% — consider prioritizing pending items")

    if not social_summary_raw:
        suggestions.append("- No social media activity tracked — consider posting content this week")

    if odoo_status == "not_configured":
        suggestions.append("- Connect Odoo for automated financial tracking and reporting")

    if stale_items.get("In_Progress"):
        suggestions.append("- Some tasks stuck in progress — consider unblocking or re-assigning")

    if not suggestions:
        suggestions.append("- Everything looks good! Consider setting new goals or expanding outreach.")

    briefing += "\n".join(suggestions)

    # Error Summary
    briefing += "\n\n## Error Summary\n\n"

    if audit["errors"] > 0:
        briefing += f"- **Total errors this week**: {audit['errors']}\n"
        for err in audit["error_details"][:5]:
            briefing += f"- {err['action']}: {err['error'][:100]}\n"
        if len(audit["error_details"]) > 5:
            briefing += f"- _...and {len(audit['error_details']) - 5} more_\n"
    else:
        briefing += "No errors recorded this week.\n"

    # Business Goals Reference
    if business_goals:
        briefing += "\n## Business Goals Reference\n\n"
        # Extract just the key metrics section
        for line in business_goals.split("\n"):
            if line.strip().startswith("- Monthly goal") or line.strip().startswith("- Current MTD"):
                briefing += f"{line}\n"

    briefing += f"""
---
*Generated by AI Employee CEO Briefing at {now.strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return briefing


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
    parser = argparse.ArgumentParser(description="AI Employee CEO Briefing Generator")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--period",
        type=int,
        default=7,
        help="Briefing period in days (default: 7)",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    briefings_dir = vault_path / "Briefings"
    briefings_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = vault_path / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    briefing = generate_briefing(vault_path, period_days=args.period)

    today = datetime.now().strftime("%Y-%m-%d")
    output_path = briefings_dir / f"CEO_Briefing_{today}.md"
    output_path.write_text(briefing, encoding="utf-8")

    logger.info(f"CEO Briefing saved: {output_path.name}")
    log_action(logs_dir, "ceo_briefing", f"Generated: {output_path.name}")

    # Also log to audit
    try:
        from scripts.audit_logger import log_audit
        log_audit(
            vault_path,
            action_type="ceo_briefing",
            actor="ceo_briefing_generator",
            target=str(output_path),
            result="success",
        )
    except ImportError:
        pass


if __name__ == "__main__":
    main()
