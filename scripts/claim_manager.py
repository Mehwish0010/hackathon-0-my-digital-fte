"""
Claim-by-Move Task Manager for AI Employee.

Prevents double-work between cloud and local agents by atomically
moving files through In_Progress/<agent_id>/ subdirectories.

Usage:
    from scripts.claim_manager import ClaimManager
    cm = ClaimManager("./AI_Employee_Vault")
    cm.claim_task("cloud", "EMAIL_2026-03-14_urgent.md")
    cm.release_task("cloud", "EMAIL_2026-03-14_urgent.md", target="Done")
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ClaimManager")


class ClaimManager:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self._ensure_directories()

    def _ensure_directories(self):
        """Create required subdirectories."""
        dirs = [
            "In_Progress/cloud",
            "In_Progress/local",
            "Needs_Action/email",
            "Needs_Action/social",
            "Needs_Action/accounting",
            "Pending_Approval/email",
            "Pending_Approval/social",
            "Pending_Approval/accounting",
            "Plans/email",
            "Plans/social",
            "Plans/accounting",
            "Updates",
        ]
        for d in dirs:
            (self.vault_path / d).mkdir(parents=True, exist_ok=True)

    def _find_file(self, filename: str, search_dirs: list[str] | None = None) -> Path | None:
        """Find a file in vault directories (checks root and subdirectories)."""
        if search_dirs is None:
            search_dirs = ["Needs_Action", "Pending_Approval", "Approved"]

        for dir_name in search_dirs:
            dir_path = self.vault_path / dir_name
            # Check root of directory
            candidate = dir_path / filename
            if candidate.exists():
                return candidate
            # Check subdirectories
            if dir_path.exists():
                for sub in dir_path.iterdir():
                    if sub.is_dir():
                        candidate = sub / filename
                        if candidate.exists():
                            return candidate
        return None

    def is_claimed(self, filename: str) -> str | None:
        """Check if a file is already claimed by any agent.

        Returns the agent_id if claimed, None otherwise.
        """
        in_progress = self.vault_path / "In_Progress"
        if not in_progress.exists():
            return None

        for agent_dir in in_progress.iterdir():
            if agent_dir.is_dir() and (agent_dir / filename).exists():
                return agent_dir.name

        return None

    def claim_task(self, agent_id: str, filename: str) -> bool:
        """Atomically claim a task by moving it to /In_Progress/<agent_id>/.

        Args:
            agent_id: "cloud" or "local"
            filename: Name of the file to claim

        Returns:
            True if claimed successfully, False if already claimed or not found.
        """
        # Check if already claimed
        claimed_by = self.is_claimed(filename)
        if claimed_by:
            logger.warning(f"'{filename}' already claimed by '{claimed_by}'")
            return False

        # Find the file
        source = self._find_file(filename)
        if not source:
            logger.warning(f"File not found: {filename}")
            return False

        # Move to In_Progress/<agent_id>/
        target_dir = self.vault_path / "In_Progress" / agent_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / filename

        try:
            shutil.move(str(source), str(target))
            logger.info(f"Claimed '{filename}' for agent '{agent_id}'")
            return True
        except (OSError, shutil.Error) as e:
            logger.error(f"Failed to claim '{filename}': {e}")
            return False

    def release_task(self, agent_id: str, filename: str, target: str = "Done") -> bool:
        """Release a claimed task by moving it to target folder.

        Args:
            agent_id: Agent that claimed the task
            filename: Name of the file
            target: Destination folder ("Done", "Needs_Action", "Rejected")

        Returns:
            True if released successfully.
        """
        source = self.vault_path / "In_Progress" / agent_id / filename
        if not source.exists():
            logger.warning(f"File not in In_Progress/{agent_id}/: {filename}")
            return False

        target_dir = self.vault_path / target
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / filename

        try:
            shutil.move(str(source), str(dest))
            logger.info(f"Released '{filename}' → /{target}/")
            return True
        except (OSError, shutil.Error) as e:
            logger.error(f"Failed to release '{filename}': {e}")
            return False

    def list_claimed(self, agent_id: str | None = None) -> list[dict]:
        """List all currently claimed tasks.

        Args:
            agent_id: Filter by agent (None = all agents)
        """
        in_progress = self.vault_path / "In_Progress"
        results = []

        if not in_progress.exists():
            return results

        for agent_dir in sorted(in_progress.iterdir()):
            if not agent_dir.is_dir():
                continue
            if agent_id and agent_dir.name != agent_id:
                continue
            for f in sorted(agent_dir.iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    results.append({
                        "agent_id": agent_dir.name,
                        "filename": f.name,
                        "path": str(f),
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    })

        return results

    def list_available(self) -> list[str]:
        """List files in /Needs_Action/ that are not yet claimed."""
        available = []
        needs_action = self.vault_path / "Needs_Action"

        if not needs_action.exists():
            return available

        # Check root
        for f in sorted(needs_action.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                if not self.is_claimed(f.name):
                    available.append(f.name)
            elif f.is_dir():
                # Check subdirectories
                for sub_f in sorted(f.iterdir()):
                    if sub_f.is_file() and not sub_f.name.startswith("."):
                        if not self.is_claimed(sub_f.name):
                            available.append(sub_f.name)

        return available


if __name__ == "__main__":
    import json
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./AI_Employee_Vault"
    cm = ClaimManager(vault)

    print("Available tasks:")
    for name in cm.list_available():
        print(f"  - {name}")

    print("\nClaimed tasks:")
    for task in cm.list_claimed():
        print(f"  - [{task['agent_id']}] {task['filename']}")
