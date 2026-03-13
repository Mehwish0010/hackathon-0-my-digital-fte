"""
Cloud Agent for AI Employee.

Runs on the cloud VM. Handles email triage, draft generation, briefings,
and social media summaries. NEVER executes send/post — only creates
drafts and approval files for the local agent.

Usage:
    uv run python scripts/cloud_agent.py --vault ./AI_Employee_Vault
    uv run python scripts/cloud_agent.py --vault ./AI_Employee_Vault --once
"""

import argparse
import logging
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
logger = logging.getLogger("CloudAgent")


class CloudAgent:
    """Cloud-zone agent — drafts only, never sends."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.agent_id = get_agent_id() or "cloud"
        self.claim_manager = ClaimManager(str(self.vault_path))
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def log_action(self, action_type: str, details: str):
        """Append to daily log."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.md"
        entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **cloud_{action_type}**: {details}\n"
        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
            content += entry
        else:
            content = f"# Activity Log - {today}\n\n{entry}"
        log_file.write_text(content, encoding="utf-8")

    def triage_emails(self):
        """Process new email files in /Needs_Action/ and create drafts."""
        needs_action = self.vault_path / "Needs_Action"
        email_dirs = [needs_action, needs_action / "email"]

        for search_dir in email_dirs:
            if not search_dir.exists():
                continue

            for f in sorted(search_dir.iterdir()):
                if not f.is_file() or not f.name.startswith("EMAIL_"):
                    continue
                if f.name.startswith("."):
                    continue

                # Try to claim
                if not self.claim_manager.claim_task(self.agent_id, f.name):
                    continue

                logger.info(f"Triaging email: {f.name}")
                self._process_email(f.name)

    def _process_email(self, filename: str):
        """Triage a single email and create draft reply."""
        source = self.vault_path / "In_Progress" / self.agent_id / filename
        if not source.exists():
            return

        content = source.read_text(encoding="utf-8", errors="replace")

        # Extract email metadata from frontmatter
        subject = ""
        sender = ""
        priority = "medium"
        for line in content.split("\n"):
            line_stripped = line.strip()
            if line_stripped.startswith("subject:"):
                subject = line_stripped.split(":", 1)[1].strip()
            elif line_stripped.startswith("from:"):
                sender = line_stripped.split(":", 1)[1].strip()
            elif line_stripped.startswith("priority:"):
                priority = line_stripped.split(":", 1)[1].strip()

        # Determine if reply is needed (simple heuristic)
        needs_reply = any(kw in content.lower() for kw in [
            "action required", "urgent", "please respond", "reply",
            "invoice", "payment", "meeting", "confirm", "deadline",
        ])

        if needs_reply:
            self._create_draft_reply(filename, subject, sender, content, priority)
            self.log_action("email_triage", f"Draft reply created for: {filename}")
        else:
            # Archive informational emails
            self.claim_manager.release_task(self.agent_id, filename, target="Done")
            self.log_action("email_triage", f"Archived (no action needed): {filename}")

    def _create_draft_reply(self, original_filename: str, subject: str,
                            sender: str, original_content: str, priority: str):
        """Create a draft reply in /Pending_Approval/email/."""
        approval_dir = self.vault_path / "Pending_Approval" / "email"
        approval_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        draft_filename = f"EMAIL_REPLY_{timestamp}_{original_filename[:40]}.md"
        draft_path = approval_dir / draft_filename

        # Generate draft reply placeholder
        content = f"""---
type: email_reply_draft
status: pending_approval
created: {now.isoformat()}
priority: {priority}
source: cloud_agent
original_file: {original_filename}
to: {sender}
subject: Re: {subject}
---

## Draft Email Reply

**To**: {sender}
**Subject**: Re: {subject}
**Priority**: {priority}
**Drafted by**: Cloud Agent

## Proposed Reply

> [Cloud agent has flagged this email for reply. Edit the reply below before approving.]

Thank you for your email regarding "{subject}".

[EDIT THIS REPLY BEFORE APPROVING]

Best regards

## Original Email

{original_content[:500]}

## Instructions

- **To Send**: Move this file to /Approved/
- **To Edit**: Modify the reply above, then move to /Approved/
- **To Discard**: Move to /Rejected/
"""
        draft_path.write_text(content, encoding="utf-8")
        logger.info(f"Created draft reply: {draft_filename}")

        # Release original from In_Progress to Done
        self.claim_manager.release_task(self.agent_id, original_filename, target="Done")

    def generate_briefing_signal(self):
        """Write a dashboard update signal for the local agent."""
        updates_dir = self.vault_path / "Updates"
        updates_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        signal = updates_dir / f"dashboard_signal_{now.strftime('%Y%m%d_%H%M%S')}.md"

        # Gather quick stats
        folders = ["Needs_Action", "Pending_Approval", "In_Progress", "Done"]
        stats = {}
        for folder in folders:
            path = self.vault_path / folder
            count = 0
            if path.exists():
                for item in path.rglob("*"):
                    if item.is_file() and not item.name.startswith("."):
                        count += 1
            stats[folder] = count

        content = f"""---
type: dashboard_signal
source: cloud_agent
created: {now.isoformat()}
---

## Cloud Agent Status Update

- **Timestamp**: {now.strftime('%Y-%m-%d %H:%M:%S')}
- **Agent**: {self.agent_id}
- **Status**: Running
- **Needs Action**: {stats.get('Needs_Action', 0)}
- **Pending Approval**: {stats.get('Pending_Approval', 0)}
- **In Progress**: {stats.get('In_Progress', 0)}
- **Done**: {stats.get('Done', 0)}
"""
        signal.write_text(content, encoding="utf-8")
        logger.info("Dashboard signal written")

    def run_once(self):
        """Run a single cloud agent cycle."""
        logger.info("=== Cloud Agent Cycle ===")
        self.triage_emails()
        self.generate_briefing_signal()
        logger.info("Cloud agent cycle complete")

    def run_loop(self, interval: int = 120):
        """Run continuous cloud agent loop."""
        logger.info(f"Cloud agent started (interval: {interval}s)")
        try:
            while True:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Cloud agent stopped.")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Cloud Agent")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Vault path")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=120, help="Loop interval (seconds)")
    args = parser.parse_args()

    agent = CloudAgent(args.vault)

    if args.once:
        agent.run_once()
    else:
        agent.run_loop(args.interval)


if __name__ == "__main__":
    main()
