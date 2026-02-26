"""Base watcher template for all AI Employee watchers."""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime


class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.inbox = self.vault_path / "Inbox"
        self.logs_dir = self.vault_path / "Logs"
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder."""
        pass

    def log_action(self, action_type: str, details: str):
        """Log an action to the daily log file."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.md"

        entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **{action_type}**: {details}\n"

        if log_file.exists():
            content = log_file.read_text()
            content += entry
        else:
            content = f"# Activity Log - {today}\n\n{entry}"

        log_file.write_text(content)

    def run(self):
        """Main loop - continuously check for updates."""
        self.logger.info(f"Starting {self.__class__.__name__}")
        print(f"[{self.__class__.__name__}] Running... Press Ctrl+C to stop.")
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    path = self.create_action_file(item)
                    self.log_action("new_item", f"Created {path.name}")
                    self.logger.info(f"Created action file: {path}")
            except KeyboardInterrupt:
                self.logger.info("Watcher stopped by user")
                print("\nWatcher stopped.")
                break
            except Exception as e:
                self.logger.error(f"Error: {e}")
            time.sleep(self.check_interval)
