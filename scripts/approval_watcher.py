"""
Approval Watcher for AI Employee.

Monitors the /Approved/ folder for files that have been human-approved.
When a file appears, triggers the corresponding action based on its type prefix.

Usage:
    uv run python scripts/approval_watcher.py
    uv run python scripts/approval_watcher.py --vault ./AI_Employee_Vault
    uv run python scripts/approval_watcher.py --once
    uv run python scripts/approval_watcher.py --dry-run
"""

import argparse
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ApprovalWatcher")

# Action type handlers mapped by file prefix
ACTION_PREFIXES = {
    "EMAIL_": "email_send",
    "LINKEDIN_": "linkedin_post",
    "PAYMENT_": "payment",
    "COMM_": "external_comm",
    "ACTION_": "general_action",
}


def log_action(logs_dir: Path, action_type: str, details: str):
    """Append to daily log."""
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


def determine_action_type(filename: str) -> str:
    """Determine the action type from the filename prefix."""
    for prefix, action_type in ACTION_PREFIXES.items():
        if filename.upper().startswith(prefix):
            return action_type
    return "unknown"


def execute_action(file_path: Path, vault_path: Path, dry_run: bool = False) -> bool:
    """Execute the action corresponding to an approved file."""
    action_type = determine_action_type(file_path.name)
    logs_dir = vault_path / "Logs"
    done_dir = vault_path / "Done"
    done_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Approved action: {action_type} — {file_path.name}")

    if dry_run:
        logger.info(f"[DRY RUN] Would execute: {action_type} for {file_path.name}")
        return True

    if action_type == "linkedin_post":
        # Trigger LinkedIn poster
        logger.info(f"LinkedIn post approved: {file_path.name}")
        logger.info("Run 'uv run python scripts/linkedin_poster.py' to post.")
        log_action(logs_dir, "approval_granted", f"{file_path.name} (linkedin_post — ready to post)")
        # Don't move — let linkedin_poster.py handle it
        return True

    elif action_type == "email_send":
        # Log that email is approved for sending via MCP
        logger.info(f"Email approved for sending: {file_path.name}")
        logger.info("Use Claude Code email MCP tools to send.")
        log_action(logs_dir, "approval_granted", f"{file_path.name} (email_send — ready via MCP)")

        # Move to Done with status update
        content = file_path.read_text(encoding="utf-8")
        content = content.replace("status: pending_approval", "status: approved")
        content += f"\n\n---\n_Approved at {datetime.now().isoformat()}_\n"
        done_path = done_dir / file_path.name
        done_path.write_text(content, encoding="utf-8")
        file_path.unlink()
        return True

    elif action_type == "payment":
        # Payments are logged but require manual execution
        logger.info(f"Payment approved: {file_path.name}")
        logger.info("MANUAL ACTION REQUIRED — execute payment through proper channels.")
        log_action(logs_dir, "approval_granted", f"{file_path.name} (payment — manual execution needed)")

        content = file_path.read_text(encoding="utf-8")
        content = content.replace("status: pending_approval", "status: approved_manual")
        content += f"\n\n---\n_Approved at {datetime.now().isoformat()} — MANUAL EXECUTION REQUIRED_\n"
        done_path = done_dir / file_path.name
        done_path.write_text(content, encoding="utf-8")
        file_path.unlink()
        return True

    else:
        # General approved actions — log and move to Done
        logger.info(f"Action approved: {file_path.name} (type: {action_type})")
        log_action(logs_dir, "approval_granted", f"{file_path.name} ({action_type})")

        content = file_path.read_text(encoding="utf-8")
        content = content.replace("status: pending_approval", "status: executed")
        content += f"\n\n---\n_Executed at {datetime.now().isoformat()}_\n"
        done_path = done_dir / file_path.name
        done_path.write_text(content, encoding="utf-8")
        file_path.unlink()
        return True


class ApprovalHandler(FileSystemEventHandler):
    """Handles files appearing in the /Approved/ folder."""

    def __init__(self, vault_path: str, dry_run: bool = False):
        self.vault_path = Path(vault_path)
        self.dry_run = dry_run

    def on_created(self, event):
        """Called when a file is created in /Approved/."""
        if event.is_directory:
            return

        source = Path(event.src_path)
        if source.name.startswith("."):
            return

        logger.info(f"New approved file detected: {source.name}")
        execute_action(source, self.vault_path, dry_run=self.dry_run)


def process_existing_approvals(vault_path: Path, dry_run: bool = False):
    """Process any files already in /Approved/."""
    approved_dir = vault_path / "Approved"
    if not approved_dir.exists():
        return

    files = [f for f in approved_dir.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not files:
        logger.info("No pending approved files.")
        return

    logger.info(f"Found {len(files)} approved file(s) to process.")
    for f in files:
        execute_action(f, vault_path, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(description="AI Employee Approval Watcher")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process existing approvals and exit (don't watch)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without executing them",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault).resolve()
    approved_path = vault_path / "Approved"

    if not approved_path.exists():
        logger.error(f"Approved folder not found: {approved_path}")
        logger.info("Create the vault structure first.")
        return

    if args.dry_run:
        logger.info("[DRY RUN MODE] No actions will be executed.")

    # Process any existing files first
    process_existing_approvals(vault_path, dry_run=args.dry_run)

    if args.once:
        logger.info("One-time processing complete.")
        return

    # Watch for new files
    handler = ApprovalHandler(str(vault_path), dry_run=args.dry_run)
    observer = Observer()
    observer.schedule(handler, str(approved_path), recursive=False)
    observer.start()

    logger.info(f"Watching: {approved_path}")
    logger.info("Move files to /Approved/ to trigger execution.")
    logger.info("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Approval watcher stopped.")
    observer.join()


if __name__ == "__main__":
    main()
