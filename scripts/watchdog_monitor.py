"""
Watchdog Monitor for AI Employee.

Monitors critical processes (scheduler, watchers, MCP servers).
Auto-restarts failed processes, logs restarts to audit log.
Writes health status for dashboard consumption.

Usage:
    uv run python scripts/watchdog_monitor.py
    uv run python scripts/watchdog_monitor.py --vault ./AI_Employee_Vault
    uv run python scripts/watchdog_monitor.py --once
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("WatchdogMonitor")

# Check interval in seconds
CHECK_INTERVAL = 60

# Max restart attempts before giving up on a process
MAX_RESTART_ATTEMPTS = 5

# Process definitions: name -> command
MONITORED_PROCESSES = {
    "scheduler": {
        "script": "scripts/scheduler.py",
        "args": [],
        "critical": True,
        "description": "Task scheduler (Gmail, dashboard, approvals)",
    },
    "file_watcher": {
        "script": "scripts/filesystem_watcher.py",
        "args": [],
        "critical": True,
        "description": "File system watcher (/Inbox monitoring)",
    },
    "approval_watcher": {
        "script": "scripts/approval_watcher.py",
        "args": [],
        "critical": True,
        "description": "Approval watcher (/Approved monitoring)",
    },
}


class ProcessMonitor:
    """Monitors and auto-restarts critical processes."""

    def __init__(self, vault_path: str, project_root: str):
        self.vault_path = Path(vault_path).resolve()
        self.project_root = Path(project_root).resolve()
        self.processes: dict[str, subprocess.Popen | None] = {}
        self.restart_counts: dict[str, int] = {}
        self.status_file = self.vault_path / "process_health.json"
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _log_audit(self, action_type: str, actor: str, target: str, result: str):
        """Log to JSON audit log if audit_logger is available."""
        try:
            from scripts.audit_logger import log_audit
            log_audit(
                self.vault_path,
                action_type=action_type,
                actor=actor,
                target=target,
                result=result,
            )
        except ImportError:
            pass

    def _log_markdown(self, action_type: str, details: str):
        """Append to daily markdown log."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.md"
        entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **{action_type}**: {details}\n"

        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
            content += entry
        else:
            content = f"# Activity Log - {today}\n\n{entry}"

        log_file.write_text(content, encoding="utf-8")

    def start_process(self, name: str, config: dict) -> bool:
        """Start a monitored process."""
        script_path = self.project_root / config["script"]
        if not script_path.exists():
            logger.warning(f"Script not found: {script_path} — skipping {name}")
            return False

        cmd = [sys.executable, str(script_path), "--vault", str(self.vault_path)]
        cmd.extend(config.get("args", []))

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.processes[name] = proc
            self.restart_counts[name] = self.restart_counts.get(name, 0)
            logger.info(f"Started {name} (PID: {proc.pid})")
            self._log_markdown("process_started", f"{name} (PID: {proc.pid})")
            self._log_audit("process_start", "watchdog_monitor", name, "success")
            return True
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            self._log_audit("process_start", "watchdog_monitor", name, f"failed: {e}")
            return False

    def check_process(self, name: str) -> bool:
        """Check if a process is still running."""
        proc = self.processes.get(name)
        if proc is None:
            return False
        return proc.poll() is None  # None means still running

    def restart_process(self, name: str, config: dict) -> bool:
        """Restart a failed process."""
        count = self.restart_counts.get(name, 0)
        if count >= MAX_RESTART_ATTEMPTS:
            logger.error(
                f"{name} has failed {count} times — not restarting. "
                f"Manual intervention required."
            )
            self._log_markdown(
                "process_abandoned",
                f"{name} — exceeded max restart attempts ({MAX_RESTART_ATTEMPTS})",
            )
            return False

        # Kill old process if it exists
        proc = self.processes.get(name)
        if proc:
            try:
                proc.kill()
                proc.wait(timeout=5)
            except Exception:
                pass

        logger.info(f"Restarting {name} (attempt {count + 1}/{MAX_RESTART_ATTEMPTS})")
        self._log_markdown("process_restart", f"{name} (attempt {count + 1})")
        self._log_audit(
            "process_restart", "watchdog_monitor", name,
            f"attempt {count + 1}/{MAX_RESTART_ATTEMPTS}",
        )

        success = self.start_process(name, config)
        if success:
            self.restart_counts[name] = count + 1
        return success

    def check_all(self) -> dict:
        """Check all monitored processes and restart failed ones."""
        status = {}
        now = datetime.now().isoformat()

        for name, config in MONITORED_PROCESSES.items():
            running = self.check_process(name)

            if running:
                proc = self.processes[name]
                status[name] = {
                    "status": "running",
                    "pid": proc.pid if proc else None,
                    "restarts": self.restart_counts.get(name, 0),
                    "last_check": now,
                    "description": config["description"],
                }
            elif name in self.processes:
                # Was running, now stopped — restart
                logger.warning(f"{name} has stopped — attempting restart")
                restarted = self.restart_process(name, config)
                proc = self.processes.get(name)
                status[name] = {
                    "status": "restarted" if restarted else "failed",
                    "pid": proc.pid if proc and restarted else None,
                    "restarts": self.restart_counts.get(name, 0),
                    "last_check": now,
                    "description": config["description"],
                }
            else:
                # Never started
                status[name] = {
                    "status": "not_started",
                    "pid": None,
                    "restarts": 0,
                    "last_check": now,
                    "description": config["description"],
                }

        # Write status file for dashboard
        self._write_status(status)
        return status

    def _write_status(self, status: dict):
        """Write process health status to JSON for dashboard."""
        data = {
            "last_check": datetime.now().isoformat(),
            "processes": status,
        }
        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def start_all(self):
        """Start all monitored processes."""
        for name, config in MONITORED_PROCESSES.items():
            self.start_process(name, config)

    def stop_all(self):
        """Stop all monitored processes."""
        for name, proc in self.processes.items():
            if proc and proc.poll() is None:
                logger.info(f"Stopping {name} (PID: {proc.pid})")
                try:
                    proc.terminate()
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                except Exception:
                    pass


def main():
    parser = argparse.ArgumentParser(description="AI Employee Watchdog Monitor")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Check status once and exit (don't start processes)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    vault_path = Path(args.vault).resolve()

    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    monitor = ProcessMonitor(str(vault_path), str(project_root))

    if args.once:
        # Just check and report
        status = monitor.check_all()
        for name, info in status.items():
            print(f"  {name}: {info['status']} (PID: {info.get('pid', 'N/A')})")
        return

    # Start all processes and monitor them
    logger.info("Starting Watchdog Monitor...")
    logger.info(f"Monitoring {len(MONITORED_PROCESSES)} processes")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    logger.info("Press Ctrl+C to stop.")

    monitor.start_all()

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            status = monitor.check_all()
            running = sum(1 for s in status.values() if s["status"] == "running")
            total = len(status)
            logger.info(f"Health check: {running}/{total} processes running")
    except KeyboardInterrupt:
        logger.info("Stopping watchdog monitor...")
        monitor.stop_all()
        logger.info("All processes stopped.")


if __name__ == "__main__":
    main()
