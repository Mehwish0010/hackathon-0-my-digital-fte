"""
Task Scheduler for AI Employee.

Runs scheduled tasks: Gmail checks, dashboard updates, daily briefings.
Uses the `schedule` library for simple cron-like scheduling.

Usage:
    uv run python scripts/scheduler.py
    uv run python scripts/scheduler.py --vault ./AI_Employee_Vault
    uv run python scripts/scheduler.py --create-bat   # Create Windows Task Scheduler .bat file
"""

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Scheduler")


class AIEmployeeScheduler:
    def __init__(self, vault_path: str, project_root: str):
        self.vault_path = Path(vault_path).resolve()
        self.project_root = Path(project_root).resolve()
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def log_action(self, action_type: str, details: str):
        """Append to daily log."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.md"
        entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **{action_type}**: {details}\n"

        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
            content += entry
        else:
            content = f"# Activity Log - {today}\n\n{entry}"

        log_file.write_text(content, encoding="utf-8")

    def run_script(self, script_name: str, args: list[str] | None = None) -> bool:
        """Run a Python script from the scripts/ directory."""
        script_path = self.project_root / "scripts" / script_name
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False

        cmd = [sys.executable, str(script_path), "--vault", str(self.vault_path)]
        if args:
            cmd.extend(args)

        try:
            logger.info(f"Running: {script_name} {' '.join(args or [])}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_root),
            )
            if result.returncode == 0:
                logger.info(f"{script_name} completed successfully.")
                return True
            else:
                logger.error(f"{script_name} failed: {result.stderr[:500]}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"{script_name} timed out after 120s.")
            return False
        except Exception as e:
            logger.error(f"Error running {script_name}: {e}")
            return False

    def check_gmail(self):
        """Scheduled task: Check Gmail for new emails."""
        logger.info("=== Scheduled Gmail Check ===")
        success = self.run_script("gmail_watcher.py", ["--once"])
        self.log_action("scheduled_gmail_check", f"Result: {'success' if success else 'failed'}")

    def update_dashboard(self):
        """Scheduled task: Update the dashboard with current stats."""
        logger.info("=== Scheduled Dashboard Update ===")
        now = datetime.now()

        # Count items in each folder
        folders = {
            "Inbox": self.vault_path / "Inbox",
            "Needs_Action": self.vault_path / "Needs_Action",
            "In_Progress": self.vault_path / "In_Progress",
            "Done": self.vault_path / "Done",
            "Pending_Approval": self.vault_path / "Pending_Approval",
            "Approved": self.vault_path / "Approved",
        }

        counts = {}
        for name, path in folders.items():
            if path.exists():
                files = [f for f in path.iterdir() if f.is_file() and not f.name.startswith(".")]
                counts[name] = len(files)
            else:
                counts[name] = 0

        # Read recent log entries
        today = now.strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.md"
        recent_activity = []
        if log_file.exists():
            lines = log_file.read_text(encoding="utf-8").strip().split("\n")
            recent_activity = [l for l in lines if l.startswith("- [")][-10:]

        # Update dashboard
        dashboard_path = self.vault_path / "Dashboard.md"
        dashboard = f"""---
last_updated: {now.strftime('%Y-%m-%d')}
auto_refresh: true
---

# AI Employee Dashboard

## System Status
| Component | Status | Last Check |
|-----------|--------|------------|
| File Watcher | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| Gmail Watcher | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| Approval Watcher | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| LinkedIn Poster | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| Email MCP Server | Configured | {now.strftime('%Y-%m-%d %H:%M')} |
| Scheduler | Running | {now.strftime('%Y-%m-%d %H:%M')} |
| Vault Integration | Active | {now.strftime('%Y-%m-%d %H:%M')} |

## Pending Actions
| # | Source | Summary | Priority | Created |
|---|--------|---------|----------|---------|
"""
        # Add pending action rows
        needs_action = self.vault_path / "Needs_Action"
        if needs_action.exists():
            action_files = sorted(needs_action.glob("*.md"))
            for i, f in enumerate(action_files, 1):
                if f.name.startswith("."):
                    continue
                content = f.read_text(encoding="utf-8", errors="replace")
                # Extract source type from filename prefix
                source = f.name.split("_")[0] if "_" in f.name else "unknown"
                # Extract priority from frontmatter
                priority = "medium"
                for line in content.split("\n"):
                    if line.strip().startswith("priority:"):
                        priority = line.split(":", 1)[1].strip()
                        break
                dashboard += f"| {i} | {source} | {f.stem[:40]} | {priority} | {f.stat().st_mtime:.0f} |\n"

        if counts["Needs_Action"] == 0:
            dashboard += "| - | - | No pending actions | - | - |\n"

        dashboard += f"""
## Recent Activity
"""
        if recent_activity:
            dashboard += "\n".join(recent_activity) + "\n"
        else:
            dashboard += f"- [{now.strftime('%Y-%m-%d')}] Scheduler running\n"

        dashboard += f"""
## Quick Stats
- **Inbox items**: {counts.get('Inbox', 0)}
- **Needs Action**: {counts.get('Needs_Action', 0)}
- **In Progress**: {counts.get('In_Progress', 0)}
- **Pending Approval**: {counts.get('Pending_Approval', 0)}
- **Done (this week)**: {counts.get('Done', 0)}

## Upcoming Deadlines
_No deadlines set._

---
*Auto-updated by AI Employee Scheduler. Last refresh: {now.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        dashboard_path.write_text(dashboard, encoding="utf-8")
        logger.info("Dashboard updated.")
        self.log_action("scheduled_dashboard_update", f"Counts: {counts}")

    def check_approvals(self):
        """Scheduled task: Check for newly approved items."""
        logger.info("=== Scheduled Approval Check ===")
        success = self.run_script("approval_watcher.py", ["--once"])
        self.log_action("scheduled_approval_check", f"Result: {'success' if success else 'failed'}")

    def daily_briefing(self):
        """Scheduled task: Generate morning briefing."""
        logger.info("=== Daily Briefing ===")
        now = datetime.now()
        briefings_dir = self.vault_path / "Briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)

        # Gather stats
        folders = ["Inbox", "Needs_Action", "In_Progress", "Pending_Approval", "Done"]
        stats = {}
        for folder in folders:
            path = self.vault_path / folder
            if path.exists():
                files = [f for f in path.iterdir() if f.is_file() and not f.name.startswith(".")]
                stats[folder] = len(files)
            else:
                stats[folder] = 0

        briefing = f"""---
type: daily_briefing
date: {now.strftime('%Y-%m-%d')}
generated: {now.isoformat()}
---

# Daily Briefing - {now.strftime('%A, %B %d, %Y')}

## Overview
Good morning! Here's your AI Employee status report.

## Vault Status
| Folder | Items |
|--------|-------|
"""
        for folder, count in stats.items():
            briefing += f"| {folder} | {count} |\n"

        briefing += f"""
## Action Items
"""
        # List items needing action
        needs_action = self.vault_path / "Needs_Action"
        if needs_action.exists():
            action_files = sorted(needs_action.glob("*.md"))
            if action_files:
                for f in action_files:
                    if not f.name.startswith("."):
                        briefing += f"- **{f.stem}**\n"
            else:
                briefing += "- No items need action\n"
        else:
            briefing += "- No items need action\n"

        # List items pending approval
        pending = self.vault_path / "Pending_Approval"
        if pending.exists():
            pending_files = [f for f in pending.iterdir() if f.is_file() and not f.name.startswith(".")]
            if pending_files:
                briefing += "\n## Pending Your Approval\n"
                for f in pending_files:
                    briefing += f"- **{f.stem}** — review and move to /Approved/ or /Rejected/\n"

        briefing += f"""
## Schedule for Today
- Gmail monitored every 2 minutes
- Dashboard updates every 15 minutes
- Approval checks every 5 minutes

---
*Generated by AI Employee Scheduler at {now.strftime('%H:%M:%S')}*
"""
        briefing_path = briefings_dir / f"briefing_{now.strftime('%Y-%m-%d')}.md"
        briefing_path.write_text(briefing, encoding="utf-8")
        logger.info(f"Daily briefing saved: {briefing_path.name}")
        self.log_action("daily_briefing", f"Generated: {briefing_path.name}")


def create_bat_file(project_root: Path):
    """Create a .bat file for Windows Task Scheduler."""
    bat_content = f"""@echo off
REM AI Employee Scheduler - Windows Task Scheduler entry point
REM Schedule this .bat file to run at system startup or on a schedule.

cd /d "{project_root}"
"{project_root / '.venv' / 'Scripts' / 'python.exe'}" scripts/scheduler.py --vault ./AI_Employee_Vault
"""
    bat_path = project_root / "run_scheduler.bat"
    bat_path.write_text(bat_content)
    logger.info(f"Created: {bat_path}")
    logger.info("Add this .bat file to Windows Task Scheduler for auto-start.")
    print(f"\nBat file created: {bat_path}")
    print("To schedule:")
    print("  1. Open Task Scheduler (taskschd.msc)")
    print("  2. Create Basic Task → 'AI Employee Scheduler'")
    print(f"  3. Action → Start a Program → {bat_path}")
    print("  4. Trigger → At startup (or daily)")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Task Scheduler")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--create-bat",
        action="store_true",
        help="Create a .bat file for Windows Task Scheduler",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    if args.create_bat:
        create_bat_file(project_root)
        return

    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    sched = AIEmployeeScheduler(str(vault_path), str(project_root))

    # Schedule tasks
    schedule.every(2).minutes.do(sched.check_gmail)
    schedule.every(15).minutes.do(sched.update_dashboard)
    schedule.every(5).minutes.do(sched.check_approvals)
    schedule.every().day.at("08:00").do(sched.daily_briefing)

    logger.info("AI Employee Scheduler started.")
    logger.info("Schedule:")
    logger.info("  - Gmail check: every 2 minutes")
    logger.info("  - Dashboard update: every 15 minutes")
    logger.info("  - Approval check: every 5 minutes")
    logger.info("  - Daily briefing: 8:00 AM")
    logger.info("Press Ctrl+C to stop.")

    # Run initial tasks
    sched.update_dashboard()
    sched.check_approvals()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
