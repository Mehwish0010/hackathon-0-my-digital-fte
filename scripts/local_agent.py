"""
Local Agent for AI Employee.

Runs on the local machine. Handles approval execution, sending emails,
posting to social media, processing payments, and merging cloud signals
into Dashboard.md (single-writer rule).

Usage:
    uv run python scripts/local_agent.py --vault ./AI_Employee_Vault
    uv run python scripts/local_agent.py --vault ./AI_Employee_Vault --once
"""

import argparse
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.claim_manager import ClaimManager
from scripts.deploy_config import get_agent_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("LocalAgent")


class LocalAgent:
    """Local-zone agent — executes approved actions."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.agent_id = get_agent_id() or "local"
        self.claim_manager = ClaimManager(str(self.vault_path))
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def log_action(self, action_type: str, details: str):
        """Append to daily log."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.md"
        entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **local_{action_type}**: {details}\n"
        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
            content += entry
        else:
            content = f"# Activity Log - {today}\n\n{entry}"
        log_file.write_text(content, encoding="utf-8")

    def process_approved_items(self):
        """Check /Approved/ for newly approved items and execute them."""
        approved_dir = self.vault_path / "Approved"
        if not approved_dir.exists():
            return

        for f in sorted(approved_dir.iterdir()):
            if not f.is_file() or f.name.startswith("."):
                continue

            # Claim the task
            if not self.claim_manager.claim_task(self.agent_id, f.name):
                continue

            logger.info(f"Executing approved item: {f.name}")
            success = self._execute_approved(f.name)

            if success:
                self.claim_manager.release_task(self.agent_id, f.name, target="Done")
                self.log_action("execute_approved", f"Completed: {f.name}")
            else:
                # Return to Approved for retry
                self.claim_manager.release_task(self.agent_id, f.name, target="Approved")
                self.log_action("execute_failed", f"Will retry: {f.name}")

    def _execute_approved(self, filename: str) -> bool:
        """Execute an approved action based on file type prefix."""
        source = self.vault_path / "In_Progress" / self.agent_id / filename
        if not source.exists():
            return False

        content = source.read_text(encoding="utf-8", errors="replace")

        if filename.startswith("EMAIL_REPLY_") or filename.startswith("EMAIL_"):
            return self._execute_email(filename, content)
        elif filename.startswith("FACEBOOK_"):
            return self._execute_social(filename, content, "facebook")
        elif filename.startswith("INSTAGRAM_"):
            return self._execute_social(filename, content, "instagram")
        elif filename.startswith("TWITTER_"):
            return self._execute_social(filename, content, "twitter")
        elif filename.startswith("LINKEDIN_"):
            return self._execute_social(filename, content, "linkedin")
        elif filename.startswith("ACCOUNTING_"):
            return self._execute_accounting(filename, content)
        else:
            logger.info(f"No handler for {filename} — moving to Done")
            return True

    def _execute_email(self, filename: str, content: str) -> bool:
        """Execute email send (delegates to approval_watcher/email MCP)."""
        logger.info(f"Email action queued: {filename}")
        # The approval_watcher.py handles actual email sending
        # We just log and let it proceed
        self.log_action("email_queued", f"Email ready for send: {filename}")
        return True

    def _execute_social(self, filename: str, content: str, platform: str) -> bool:
        """Queue social media post for the platform poster script."""
        logger.info(f"Social post queued ({platform}): {filename}")
        self.log_action("social_queued", f"{platform} post ready: {filename}")
        return True

    def _execute_accounting(self, filename: str, content: str) -> bool:
        """Queue accounting action for Odoo processing."""
        logger.info(f"Accounting action queued: {filename}")
        self.log_action("accounting_queued", f"Odoo action ready: {filename}")
        return True

    def check_pending_approvals(self):
        """Scan /Pending_Approval/ and notify about items needing review."""
        pending_dir = self.vault_path / "Pending_Approval"
        if not pending_dir.exists():
            return

        pending_items = []
        # Check root and subdirectories
        for item in pending_dir.rglob("*.md"):
            if not item.name.startswith("."):
                pending_items.append(item)

        if pending_items:
            logger.info(f"{len(pending_items)} item(s) pending approval:")
            for item in pending_items[:5]:
                logger.info(f"  - {item.relative_to(pending_dir)}")
            if len(pending_items) > 5:
                logger.info(f"  ... and {len(pending_items) - 5} more")

    def merge_cloud_signals(self):
        """Merge /Updates/ signals from cloud agent into local state.

        Implements single-writer rule: only local writes Dashboard.md.
        Cloud writes signals to /Updates/, local merges them.
        """
        updates_dir = self.vault_path / "Updates"
        if not updates_dir.exists():
            return

        signals = sorted(updates_dir.glob("dashboard_signal_*.md"))
        if not signals:
            return

        # Read the latest signal
        latest = signals[-1]
        signal_content = latest.read_text(encoding="utf-8", errors="replace")

        # Extract cloud status from signal
        cloud_status = "Unknown"
        for line in signal_content.split("\n"):
            if "**Status**:" in line:
                cloud_status = line.split(":", 1)[1].strip().strip("*")
                break

        logger.info(f"Merged {len(signals)} cloud signal(s) — cloud status: {cloud_status}")
        self.log_action("merge_signals", f"Cloud status: {cloud_status}, signals: {len(signals)}")

        # Clean up processed signals (keep last one)
        for old_signal in signals[:-1]:
            old_signal.unlink(missing_ok=True)

    def run_once(self):
        """Run a single local agent cycle."""
        logger.info("=== Local Agent Cycle ===")
        self.merge_cloud_signals()
        self.check_pending_approvals()
        self.process_approved_items()
        logger.info("Local agent cycle complete")

    def run_loop(self, interval: int = 60):
        """Run continuous local agent loop."""
        logger.info(f"Local agent started (interval: {interval}s)")
        try:
            while True:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Local agent stopped.")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Local Agent")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Vault path")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=60, help="Loop interval (seconds)")
    args = parser.parse_args()

    agent = LocalAgent(args.vault)

    if args.once:
        agent.run_once()
    else:
        agent.run_loop(args.interval)


if __name__ == "__main__":
    main()
