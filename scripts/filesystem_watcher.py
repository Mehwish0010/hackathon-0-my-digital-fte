"""
File System Watcher for AI Employee.

Monitors the /Inbox folder for new files and creates action items
in /Needs_Action for Claude Code to process.

Usage:
    uv run python scripts/filesystem_watcher.py
    uv run python scripts/filesystem_watcher.py --vault ./AI_Employee_Vault
    uv run python scripts/filesystem_watcher.py --dry-run
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
logger = logging.getLogger("FileWatcher")

# Keywords for priority classification
HIGH_PRIORITY_KEYWORDS = ["urgent", "asap", "invoice", "payment", "deadline", "critical"]
MEDIUM_PRIORITY_KEYWORDS = ["client", "project", "meeting", "review", "update"]


def classify_priority(filename: str, content: str = "") -> str:
    """Classify file priority based on name and content."""
    text = (filename + " " + content).lower()
    if any(kw in text for kw in HIGH_PRIORITY_KEYWORDS):
        return "high"
    if any(kw in text for kw in MEDIUM_PRIORITY_KEYWORDS):
        return "medium"
    return "low"


class InboxHandler(FileSystemEventHandler):
    """Handles new files dropped into the /Inbox folder."""

    def __init__(self, vault_path: str, dry_run: bool = False):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        self.dry_run = dry_run

        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def on_created(self, event):
        """Called when a file is created in /Inbox."""
        if event.is_directory:
            return

        source = Path(event.src_path)

        # Skip hidden files and .gitkeep
        if source.name.startswith("."):
            return

        logger.info(f"New file detected: {source.name}")
        self._process_file(source)

    def _process_file(self, source: Path):
        """Process a new file from Inbox."""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

        # Read content if it's a text file
        content = ""
        try:
            if source.suffix in [".md", ".txt", ".csv", ".json", ".log"]:
                content = source.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass

        priority = classify_priority(source.name, content)

        # Create action metadata file
        action_filename = f"FILE_{timestamp}_{source.stem}.md"
        action_path = self.needs_action / action_filename

        metadata = f"""---
type: file_drop
source: inbox
original_name: {source.name}
file_type: {source.suffix or 'unknown'}
size_bytes: {source.stat().st_size}
priority: {priority}
status: pending
created: {now.isoformat()}
---

## New File for Processing

**File**: `{source.name}`
**Size**: {source.stat().st_size:,} bytes
**Priority**: {priority}
**Detected**: {now.strftime('%Y-%m-%d %H:%M:%S')}

## Content Preview
"""
        if content:
            # Include first 500 chars as preview
            preview = content[:500]
            if len(content) > 500:
                preview += "\n\n_(truncated - see original file)_"
            metadata += f"\n```\n{preview}\n```\n"
        else:
            metadata += f"\n_Binary file or empty - see original: `{source.name}`_\n"

        metadata += """
## Suggested Actions
- [ ] Review file contents
- [ ] Classify and categorize
- [ ] Take appropriate action
- [ ] Move to /Done when complete
"""

        if self.dry_run:
            logger.info(f"[DRY RUN] Would create: {action_path}")
            logger.info(f"[DRY RUN] Would copy: {source.name} -> Needs_Action/")
            return

        # Write action file
        action_path.write_text(metadata, encoding="utf-8")

        # Copy original file to Needs_Action (keep original in Inbox for safety)
        dest = self.needs_action / source.name
        if not dest.exists():
            shutil.copy2(source, dest)

        # Log the action
        self._log_action(source.name, priority)

        logger.info(f"Created action file: {action_filename} (priority: {priority})")

    def _log_action(self, filename: str, priority: str):
        """Append to daily log."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.md"
        entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **file_drop**: `{filename}` (priority: {priority})\n"

        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
            content += entry
        else:
            content = f"# Activity Log - {today}\n\n{entry}"

        log_file.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="AI Employee File System Watcher")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without executing them",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault).resolve()
    inbox_path = vault_path / "Inbox"

    if not inbox_path.exists():
        logger.error(f"Inbox folder not found: {inbox_path}")
        logger.info("Create the vault structure first.")
        return

    if args.dry_run:
        logger.info("[DRY RUN MODE] No files will be modified.")

    handler = InboxHandler(str(vault_path), dry_run=args.dry_run)
    observer = Observer()
    observer.schedule(handler, str(inbox_path), recursive=False)
    observer.start()

    logger.info(f"Watching: {inbox_path}")
    logger.info("Drop files into the Inbox folder to trigger processing.")
    logger.info("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Watcher stopped.")
    observer.join()


if __name__ == "__main__":
    main()
