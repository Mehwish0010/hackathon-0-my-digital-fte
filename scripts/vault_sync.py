"""
Git-based Vault Synchronization for AI Employee.

Keeps AI_Employee_Vault/ in sync between cloud and local instances
via a separate Git repository. Handles push/pull with last-write-wins
conflict resolution for .md files.

Usage:
    uv run python scripts/vault_sync.py --vault ./AI_Employee_Vault
    uv run python scripts/vault_sync.py --vault ./AI_Employee_Vault --once
    uv run python scripts/vault_sync.py --vault ./AI_Employee_Vault --init

Config via env vars:
    VAULT_GIT_REMOTE      - Git remote URL (required for sync)
    VAULT_SYNC_INTERVAL   - Seconds between syncs (default: 60)
"""

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.deploy_config import get_agent_id, get_vault_git_remote, get_sync_interval

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("VaultSync")


class VaultSync:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.agent_id = get_agent_id()
        self.remote_url = get_vault_git_remote()
        self.last_sync: str | None = None
        self.sync_count = 0
        self.error_count = 0

    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command in the vault directory."""
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=str(self.vault_path),
            capture_output=True,
            text=True,
            timeout=30,
            check=check,
        )

    def is_git_repo(self) -> bool:
        """Check if the vault is already a Git repository."""
        return (self.vault_path / ".git").is_dir()

    def init_repo(self) -> bool:
        """Initialize the vault as a Git repository."""
        if self.is_git_repo():
            logger.info("Vault is already a Git repository.")
            return True

        try:
            self._run_git("init")
            logger.info("Initialized vault as Git repository.")

            # Create .gitignore for vault
            self._ensure_gitignore()

            # Initial commit
            self._run_git("add", "-A")
            self._run_git("commit", "-m", "Initial vault commit")
            logger.info("Created initial commit.")

            # Add remote if configured
            if self.remote_url:
                self._run_git("remote", "add", "origin", self.remote_url)
                logger.info(f"Added remote: {self.remote_url}")

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize repo: {e.stderr}")
            return False

    def _ensure_gitignore(self):
        """Ensure vault .gitignore exists."""
        gitignore_path = self.vault_path / ".gitignore"
        if not gitignore_path.exists():
            logger.info("Vault .gitignore not found — will be created by security_check")

    def sync_push(self) -> bool:
        """Stage, commit, and push vault changes to remote."""
        if not self.is_git_repo():
            logger.error("Vault is not a Git repository. Run --init first.")
            return False

        try:
            # Run security check before push
            try:
                from scripts.security_check import scan_staged_files
                self._run_git("add", "-A")
                issues = scan_staged_files(str(self.vault_path))
                if issues:
                    logger.error(f"Security check blocked push: {len(issues)} issue(s) found")
                    for issue in issues:
                        logger.error(f"  - {issue}")
                    self._run_git("reset", "HEAD")
                    return False
            except ImportError:
                self._run_git("add", "-A")

            # Check if there are changes to commit
            status = self._run_git("status", "--porcelain")
            if not status.stdout.strip():
                return True  # Nothing to sync

            # Commit
            now = datetime.now().isoformat()
            msg = f"vault sync [{self.agent_id}] {now}"
            self._run_git("commit", "-m", msg)

            # Push if remote is configured
            if self.remote_url:
                result = self._run_git("push", "origin", "main", check=False)
                if result.returncode != 0:
                    # Try pushing to current branch
                    result = self._run_git("push", check=False)
                    if result.returncode != 0:
                        logger.warning(f"Push failed: {result.stderr[:200]}")
                        return False

            self.sync_count += 1
            self.last_sync = now
            logger.info(f"Pushed vault changes (sync #{self.sync_count})")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Sync push failed: {e.stderr[:200] if e.stderr else str(e)}")
            self.error_count += 1
            return False

    def sync_pull(self) -> bool:
        """Pull remote changes with last-write-wins conflict resolution."""
        if not self.is_git_repo():
            logger.error("Vault is not a Git repository. Run --init first.")
            return False

        if not self.remote_url:
            return True  # No remote configured, skip

        try:
            # Stash local changes
            self._run_git("stash", check=False)

            # Pull with rebase
            result = self._run_git("pull", "--rebase", "origin", "main", check=False)

            if result.returncode != 0:
                # Conflict — resolve with last-write-wins (accept theirs for .md)
                logger.warning("Merge conflict detected — applying last-write-wins")
                self._run_git("rebase", "--abort", check=False)
                self._run_git("pull", "--strategy-option=theirs", "origin", "main", check=False)

            # Restore stashed changes
            self._run_git("stash", "pop", check=False)

            self.last_sync = datetime.now().isoformat()
            logger.info("Pulled vault changes from remote")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Sync pull failed: {e.stderr[:200] if e.stderr else str(e)}")
            self.error_count += 1
            return False

    def sync(self) -> bool:
        """Full sync cycle: pull then push."""
        pull_ok = self.sync_pull()
        push_ok = self.sync_push()
        return pull_ok and push_ok

    def get_status(self) -> dict:
        """Return current sync status."""
        return {
            "is_git_repo": self.is_git_repo(),
            "remote": self.remote_url or "(none)",
            "agent_id": self.agent_id,
            "last_sync": self.last_sync or "never",
            "sync_count": self.sync_count,
            "error_count": self.error_count,
        }

    def write_sync_status(self):
        """Write sync status to Updates/ for dashboard integration."""
        updates_dir = self.vault_path / "Updates"
        updates_dir.mkdir(parents=True, exist_ok=True)

        status = self.get_status()
        now = datetime.now()
        status_file = updates_dir / f"sync_status_{self.agent_id}.md"
        content = f"""---
type: sync_status
agent_id: {self.agent_id}
last_sync: {status['last_sync']}
sync_count: {status['sync_count']}
error_count: {status['error_count']}
updated: {now.isoformat()}
---

# Vault Sync Status — {self.agent_id}

- **Last Sync**: {status['last_sync']}
- **Total Syncs**: {status['sync_count']}
- **Errors**: {status['error_count']}
- **Remote**: {status['remote']}
"""
        status_file.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Vault Git Sync")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Vault path")
    parser.add_argument("--init", action="store_true", help="Initialize vault as Git repo")
    parser.add_argument("--once", action="store_true", help="Run a single sync cycle")
    args = parser.parse_args()

    syncer = VaultSync(args.vault)

    if args.init:
        ok = syncer.init_repo()
        print(f"Init: {'success' if ok else 'failed'}")
        return

    if args.once:
        ok = syncer.sync()
        syncer.write_sync_status()
        print(f"Sync: {'success' if ok else 'failed'}")
        return

    # Continuous sync loop
    interval = get_sync_interval()
    logger.info(f"Starting continuous vault sync (every {interval}s)")
    try:
        while True:
            syncer.sync()
            syncer.write_sync_status()
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Vault sync stopped.")


if __name__ == "__main__":
    main()
