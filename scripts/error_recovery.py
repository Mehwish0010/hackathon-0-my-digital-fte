"""
Error Recovery Module for AI Employee.

Provides retry with backoff, service health tracking, and graceful degradation.
No external dependencies — stdlib only.

Usage:
    from scripts.error_recovery import retry_with_backoff, ServiceHealthTracker

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def call_external_api():
        ...

    tracker = ServiceHealthTracker("./AI_Employee_Vault")
    tracker.record_success("odoo")
    tracker.record_failure("odoo", "Connection refused")
    if tracker.is_healthy("odoo"):
        ...
"""

import functools
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("ErrorRecovery")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retries (default: 3).
        base_delay: Initial delay in seconds (default: 1.0).
        max_delay: Maximum delay in seconds (default: 30.0).
        exceptions: Tuple of exception types to catch (default: all).
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"[Retry {attempt + 1}/{max_retries}] {func.__name__} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"[Failed] {func.__name__} failed after {max_retries} retries: {e}"
                        )
            raise last_exception

        return wrapper

    return decorator


class ServiceHealthTracker:
    """
    Tracks service availability in service_health.json.

    Monitors external services (Odoo, Gmail, LinkedIn, Facebook, Twitter)
    and provides health status for dashboard and graceful degradation.
    """

    def __init__(self, vault_path: str | Path):
        self.vault_path = Path(vault_path)
        self.health_file = self.vault_path / "service_health.json"
        self._health = self._load()

    def _load(self) -> dict:
        """Load health data from file."""
        if self.health_file.exists():
            try:
                with open(self.health_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self):
        """Save health data to file."""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        with open(self.health_file, "w", encoding="utf-8") as f:
            json.dump(self._health, f, indent=2, ensure_ascii=False)

    def record_success(self, service: str):
        """Record a successful interaction with a service."""
        if service not in self._health:
            self._health[service] = {}

        self._health[service]["last_success"] = datetime.now().isoformat()
        self._health[service]["status"] = "healthy"
        self._health[service]["consecutive_failures"] = 0
        self._health[service]["last_error"] = ""
        self._save()

    def record_failure(self, service: str, error_message: str):
        """Record a failed interaction with a service."""
        if service not in self._health:
            self._health[service] = {"consecutive_failures": 0}

        self._health[service]["last_failure"] = datetime.now().isoformat()
        self._health[service]["last_error"] = str(error_message)[:500]
        self._health[service]["consecutive_failures"] = (
            self._health[service].get("consecutive_failures", 0) + 1
        )

        failures = self._health[service]["consecutive_failures"]
        if failures >= 3:
            self._health[service]["status"] = "down"
        elif failures >= 1:
            self._health[service]["status"] = "degraded"

        self._save()

    def is_healthy(self, service: str) -> bool:
        """Check if a service is considered healthy."""
        info = self._health.get(service, {})
        return info.get("status", "unknown") in ("healthy", "unknown")

    def get_status(self, service: str) -> dict:
        """Get full status info for a service."""
        return self._health.get(service, {
            "status": "unknown",
            "consecutive_failures": 0,
            "last_error": "",
        })

    def get_all_statuses(self) -> dict:
        """Get status of all tracked services."""
        return dict(self._health)

    def reset(self, service: str):
        """Reset health tracking for a service."""
        if service in self._health:
            self._health[service] = {
                "status": "unknown",
                "consecutive_failures": 0,
                "last_error": "",
                "reset_at": datetime.now().isoformat(),
            }
            self._save()


class GracefulDegradation:
    """
    Helper for graceful degradation when services are down.

    Queues actions when a service is unavailable and provides
    clear error messages instead of crashing.
    """

    def __init__(self, vault_path: str | Path, health_tracker: ServiceHealthTracker):
        self.vault_path = Path(vault_path)
        self.health_tracker = health_tracker

    def try_or_queue(
        self,
        service: str,
        action_func,
        file_path: Path | None = None,
        error_note: str = "",
        *args,
        **kwargs,
    ) -> tuple[bool, str]:
        """
        Try to execute an action. If the service is down, queue it.

        Args:
            service: Service name (e.g. "odoo", "facebook").
            action_func: Function to call.
            file_path: Optional file to annotate with error note on failure.
            error_note: Note to add to file on failure.

        Returns:
            Tuple of (success: bool, message: str).
        """
        if not self.health_tracker.is_healthy(service):
            status = self.health_tracker.get_status(service)
            msg = (
                f"Service '{service}' is currently {status.get('status', 'unavailable')}. "
                f"Last error: {status.get('last_error', 'unknown')}. "
                f"Action queued — file remains in /Approved/ for retry."
            )
            if file_path and file_path.exists():
                self._annotate_file(file_path, error_note or msg)
            return False, msg

        try:
            result = action_func(*args, **kwargs)
            self.health_tracker.record_success(service)
            return True, str(result)
        except Exception as e:
            self.health_tracker.record_failure(service, str(e))
            msg = f"Service '{service}' failed: {e}. Action queued for retry."
            if file_path and file_path.exists():
                self._annotate_file(file_path, error_note or msg)
            return False, msg

    def _annotate_file(self, file_path: Path, note: str):
        """Add an error note to a file without moving it."""
        try:
            content = file_path.read_text(encoding="utf-8")
            timestamp = datetime.now().isoformat()
            content += f"\n\n---\n_Error at {timestamp}: {note}_\n"
            file_path.write_text(content, encoding="utf-8")
        except OSError as e:
            logger.error(f"Could not annotate file {file_path}: {e}")


if __name__ == "__main__":
    # Quick test
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./AI_Employee_Vault"

    tracker = ServiceHealthTracker(vault)
    tracker.record_success("test_service")
    print(f"Healthy: {tracker.is_healthy('test_service')}")

    tracker.record_failure("test_service", "Connection refused")
    tracker.record_failure("test_service", "Connection refused")
    tracker.record_failure("test_service", "Connection refused")
    print(f"After 3 failures — Healthy: {tracker.is_healthy('test_service')}")
    print(f"Status: {tracker.get_status('test_service')}")

    tracker.reset("test_service")
    print(f"After reset — Status: {tracker.get_status('test_service')}")
