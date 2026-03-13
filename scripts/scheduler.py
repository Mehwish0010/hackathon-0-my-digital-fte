"""
Task Scheduler for AI Employee.

Runs scheduled tasks: Gmail checks, dashboard updates, daily briefings,
social media checks, CEO briefings, Odoo health, and audit retention.
Uses the `schedule` library for simple cron-like scheduling.

Platinum tier adds --mode flag for cloud/local/hybrid deployment zones.

Usage:
    uv run python scripts/scheduler.py
    uv run python scripts/scheduler.py --vault ./AI_Employee_Vault
    uv run python scripts/scheduler.py --mode cloud    # Cloud zone only
    uv run python scripts/scheduler.py --mode local    # Local zone only
    uv run python scripts/scheduler.py --mode hybrid   # All jobs (default)
    uv run python scripts/scheduler.py --create-bat    # Create Windows Task Scheduler .bat file
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

    # === Gold Tier Scheduled Tasks ===

    def check_social_media(self):
        """Scheduled task: Post approved social media content."""
        logger.info("=== Scheduled Social Media Check ===")
        # Facebook/Instagram
        fb_ok = self.run_script("facebook_poster.py", ["--platform", "both"])
        # Twitter
        tw_ok = self.run_script("twitter_poster.py")
        # LinkedIn
        li_ok = self.run_script("linkedin_poster.py")
        results = f"FB/IG: {'ok' if fb_ok else 'fail'}, Twitter: {'ok' if tw_ok else 'fail'}, LinkedIn: {'ok' if li_ok else 'fail'}"
        self.log_action("scheduled_social_check", results)

    def social_summary(self):
        """Scheduled task: Generate weekly social media summary."""
        logger.info("=== Social Media Summary ===")
        success = self.run_script("social_media_summarizer.py")
        self.log_action("scheduled_social_summary", f"Result: {'success' if success else 'failed'}")

    def ceo_briefing(self):
        """Scheduled task: Generate weekly CEO briefing."""
        logger.info("=== CEO Briefing ===")
        success = self.run_script("ceo_briefing.py")
        self.log_action("scheduled_ceo_briefing", f"Result: {'success' if success else 'failed'}")

    def odoo_health_check(self):
        """Scheduled task: Check Odoo connectivity."""
        logger.info("=== Odoo Health Check ===")
        try:
            from scripts.error_recovery import ServiceHealthTracker
            tracker = ServiceHealthTracker(str(self.vault_path))

            import xmlrpc.client
            import os
            odoo_url = os.environ.get("ODOO_URL", "")
            if not odoo_url:
                logger.info("Odoo not configured — skipping health check")
                return

            common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common", allow_none=True)
            common.version()
            tracker.record_success("odoo")
            self.log_action("odoo_health", "Odoo is healthy")
        except Exception as e:
            logger.warning(f"Odoo health check failed: {e}")
            try:
                from scripts.error_recovery import ServiceHealthTracker
                tracker = ServiceHealthTracker(str(self.vault_path))
                tracker.record_failure("odoo", str(e))
            except ImportError:
                pass
            self.log_action("odoo_health", f"Odoo unavailable: {str(e)[:100]}")

    def audit_retention_sweep(self):
        """Scheduled task: Delete audit logs older than 90 days."""
        logger.info("=== Audit Log Retention Sweep ===")
        try:
            from scripts.audit_logger import run_retention_sweep
            deleted = run_retention_sweep(str(self.vault_path))
            self.log_action("audit_retention", f"Deleted {deleted} old log file(s)")
            logger.info(f"Retention sweep: deleted {deleted} old file(s)")
        except ImportError:
            logger.warning("audit_logger not available — skipping retention sweep")

    def vault_sync(self):
        """Scheduled task: Sync vault via Git."""
        logger.info("=== Vault Sync ===")
        try:
            from scripts.vault_sync import VaultSync
            syncer = VaultSync(str(self.vault_path))
            if syncer.is_git_repo():
                ok = syncer.sync()
                syncer.write_sync_status()
                self.log_action("vault_sync", f"Result: {'success' if ok else 'failed'}")
            else:
                logger.info("Vault is not a Git repo — skipping sync")
        except Exception as e:
            logger.warning(f"Vault sync failed: {e}")
            self.log_action("vault_sync", f"Error: {str(e)[:100]}")

    def cloud_agent_cycle(self):
        """Scheduled task: Run cloud agent triage cycle."""
        logger.info("=== Cloud Agent Cycle ===")
        try:
            from scripts.cloud_agent import CloudAgent
            agent = CloudAgent(str(self.vault_path))
            agent.run_once()
            self.log_action("cloud_agent_cycle", "Completed")
        except Exception as e:
            logger.warning(f"Cloud agent cycle failed: {e}")
            self.log_action("cloud_agent_cycle", f"Error: {str(e)[:100]}")

    def local_agent_cycle(self):
        """Scheduled task: Run local agent execution cycle."""
        logger.info("=== Local Agent Cycle ===")
        try:
            from scripts.local_agent import LocalAgent
            agent = LocalAgent(str(self.vault_path))
            agent.run_once()
            self.log_action("local_agent_cycle", "Completed")
        except Exception as e:
            logger.warning(f"Local agent cycle failed: {e}")
            self.log_action("local_agent_cycle", f"Error: {str(e)[:100]}")

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

        # Read service health
        import json
        service_statuses = {}
        health_file = self.vault_path / "service_health.json"
        if health_file.exists():
            try:
                with open(health_file, "r", encoding="utf-8") as f:
                    service_statuses = json.load(f)
            except Exception:
                pass

        def _svc(name):
            info = service_statuses.get(name, {})
            return info.get("status", "Unknown").title()

        # Get deployment info
        import os
        deploy_mode = os.environ.get("DEPLOYMENT_MODE", "hybrid")

        # Get sync status
        sync_status = "Not configured"
        sync_file = self.vault_path / "Updates" / f"sync_status_{os.environ.get('LOCAL_AGENT_ID', 'local')}.md"
        if not sync_file.exists():
            sync_file = self.vault_path / "Updates" / f"sync_status_{os.environ.get('CLOUD_AGENT_ID', 'cloud')}.md"
        if sync_file.exists():
            sync_status = "Active"

        # Cloud agent status from signals
        cloud_status = "Offline"
        updates_dir = self.vault_path / "Updates"
        if updates_dir.exists():
            signals = sorted(updates_dir.glob("dashboard_signal_*.md"))
            if signals:
                cloud_status = "Online"

        # Update dashboard
        dashboard_path = self.vault_path / "Dashboard.md"
        dashboard = f"""---
last_updated: {now.strftime('%Y-%m-%d')}
auto_refresh: true
---

# AI Employee Dashboard

## Deployment Status
| Setting | Value |
|---------|-------|
| Deployment Mode | {deploy_mode} |
| Vault Sync | {sync_status} |
| Cloud Agent | {cloud_status} |
| Last Dashboard Refresh | {now.strftime('%Y-%m-%d %H:%M:%S')} |

## System Status
| Component | Status | Last Check |
|-----------|--------|------------|
| File Watcher | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| Gmail Watcher | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| Approval Watcher | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| LinkedIn Poster | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| Facebook/IG Poster | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| Twitter/X Poster | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| Email MCP Server | Configured | {now.strftime('%Y-%m-%d %H:%M')} |
| Odoo MCP Server | {_svc('odoo')} | {now.strftime('%Y-%m-%d %H:%M')} |
| Social Media MCP | Configured | {now.strftime('%Y-%m-%d %H:%M')} |
| Scheduler | Running | {now.strftime('%Y-%m-%d %H:%M')} |
| Watchdog Monitor | Ready | {now.strftime('%Y-%m-%d %H:%M')} |
| Audit Logger | Active | {now.strftime('%Y-%m-%d %H:%M')} |

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
                source = f.name.split("_")[0] if "_" in f.name else "unknown"
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
        "--mode",
        choices=["cloud", "local", "hybrid"],
        default=None,
        help="Deployment mode: cloud, local, or hybrid (default: from DEPLOYMENT_MODE env)",
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

    # Set deployment mode from CLI flag if provided
    import os
    if args.mode:
        os.environ["DEPLOYMENT_MODE"] = args.mode

    from scripts.deploy_config import get_mode, should_run, DeploymentMode
    mode = get_mode()

    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    sched = AIEmployeeScheduler(str(vault_path), str(project_root))

    # === Platinum: Vault sync (runs in all modes) ===
    schedule.every(1).minutes.do(sched.vault_sync)

    if mode in (DeploymentMode.LOCAL, DeploymentMode.HYBRID):
        # Local-zone jobs
        schedule.every(5).minutes.do(sched.check_approvals)
        schedule.every(15).minutes.do(sched.update_dashboard)
        schedule.every(30).minutes.do(sched.check_social_media)
        schedule.every(15).minutes.do(sched.odoo_health_check)
        schedule.every(5).minutes.do(sched.local_agent_cycle)

    if mode in (DeploymentMode.CLOUD, DeploymentMode.HYBRID):
        # Cloud-zone jobs
        schedule.every(2).minutes.do(sched.check_gmail)
        schedule.every(2).minutes.do(sched.cloud_agent_cycle)
        schedule.every().day.at("08:00").do(sched.daily_briefing)
        schedule.every().sunday.at("20:00").do(sched.social_summary)
        schedule.every().sunday.at("21:00").do(sched.ceo_briefing)

    # Jobs that run in all modes
    schedule.every().day.at("00:00").do(sched.audit_retention_sweep)

    logger.info(f"AI Employee Scheduler started (mode: {mode.value}).")
    logger.info("Schedule:")
    logger.info(f"  - Deployment mode: {mode.value}")
    logger.info("  - Vault sync: every 1 minute")

    if mode in (DeploymentMode.LOCAL, DeploymentMode.HYBRID):
        logger.info("  - Approval check: every 5 minutes")
        logger.info("  - Dashboard update: every 15 minutes")
        logger.info("  - Social media post check: every 30 minutes")
        logger.info("  - Odoo health check: every 15 minutes")
        logger.info("  - Local agent cycle: every 5 minutes")

    if mode in (DeploymentMode.CLOUD, DeploymentMode.HYBRID):
        logger.info("  - Gmail check: every 2 minutes")
        logger.info("  - Cloud agent cycle: every 2 minutes")
        logger.info("  - Daily briefing: 8:00 AM")
        logger.info("  - Social media summary: Sunday 8:00 PM")
        logger.info("  - CEO briefing: Sunday 9:00 PM")

    logger.info("  - Audit retention sweep: midnight")
    logger.info("Press Ctrl+C to stop.")

    # Run initial tasks
    sched.update_dashboard()
    if mode in (DeploymentMode.LOCAL, DeploymentMode.HYBRID):
        sched.check_approvals()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
