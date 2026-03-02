"""
JSON Audit Logger for AI Employee.

Shared module imported by all scripts/MCP servers for structured audit logging.
Writes JSON-lines to /Logs/YYYY-MM-DD.json with 90-day retention.

Usage:
    from scripts.audit_logger import log_audit, query_audit, run_retention_sweep

    log_audit(vault_path, action_type="email_send", actor="scheduler",
              target="boss@example.com", parameters={"subject": "Update"},
              approval_status="approved", approved_by="human", result="success")
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Default retention period
RETENTION_DAYS = 90


def _get_log_dir(vault_path: str | Path) -> Path:
    """Get the Logs directory, creating it if needed."""
    logs_dir = Path(vault_path) / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _get_json_log_path(vault_path: str | Path, date: datetime | None = None) -> Path:
    """Get the JSON log file path for a given date."""
    if date is None:
        date = datetime.now()
    logs_dir = _get_log_dir(vault_path)
    return logs_dir / f"{date.strftime('%Y-%m-%d')}.json"


def log_audit(
    vault_path: str | Path,
    action_type: str,
    actor: str = "system",
    target: str = "",
    parameters: dict | None = None,
    approval_status: str = "",
    approved_by: str = "",
    result: str = "",
) -> dict:
    """
    Write a single audit entry as JSON-lines to /Logs/YYYY-MM-DD.json.

    Args:
        vault_path: Path to the Obsidian vault root.
        action_type: Type of action (e.g. "email_send", "invoice_create", "social_post").
        actor: Who/what performed the action (e.g. "scheduler", "approval_watcher").
        target: The target of the action (e.g. email address, invoice ID).
        parameters: Dict of action parameters.
        approval_status: "pending", "approved", "rejected", or "".
        approved_by: Who approved (e.g. "human", "auto").
        result: Outcome (e.g. "success", "failed", error message).

    Returns:
        The audit entry dict that was written.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": action_type,
        "actor": actor,
        "target": target,
        "parameters": parameters or {},
        "approval_status": approval_status,
        "approved_by": approved_by,
        "result": result,
    }

    log_path = _get_json_log_path(vault_path)

    # Append JSON-line
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def query_audit(
    vault_path: str | Path,
    days: int = 7,
    action_type: str | None = None,
    actor: str | None = None,
    approval_status: str | None = None,
) -> list[dict]:
    """
    Query audit logs across multiple days with optional filters.

    Args:
        vault_path: Path to the Obsidian vault root.
        days: Number of days to look back (default: 7).
        action_type: Filter by action type.
        actor: Filter by actor.
        approval_status: Filter by approval status.

    Returns:
        List of matching audit entries (newest first).
    """
    results = []
    logs_dir = _get_log_dir(vault_path)
    now = datetime.now()

    for i in range(days):
        date = now - timedelta(days=i)
        log_path = logs_dir / f"{date.strftime('%Y-%m-%d')}.json"

        if not log_path.exists():
            continue

        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Apply filters
                if action_type and entry.get("action_type") != action_type:
                    continue
                if actor and entry.get("actor") != actor:
                    continue
                if approval_status and entry.get("approval_status") != approval_status:
                    continue

                results.append(entry)

    # Newest first
    results.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return results


def get_audit_summary(vault_path: str | Path, days: int = 7) -> dict:
    """
    Get a summary of audit activity over a period.

    Returns:
        Dict with counts by action_type, actor, approval_status, and total.
    """
    entries = query_audit(vault_path, days=days)

    summary = {
        "total_entries": len(entries),
        "period_days": days,
        "by_action_type": {},
        "by_actor": {},
        "by_approval_status": {},
        "errors": 0,
    }

    for entry in entries:
        action = entry.get("action_type", "unknown")
        summary["by_action_type"][action] = summary["by_action_type"].get(action, 0) + 1

        actor = entry.get("actor", "unknown")
        summary["by_actor"][actor] = summary["by_actor"].get(actor, 0) + 1

        status = entry.get("approval_status", "")
        if status:
            summary["by_approval_status"][status] = summary["by_approval_status"].get(status, 0) + 1

        if "fail" in entry.get("result", "").lower() or "error" in entry.get("result", "").lower():
            summary["errors"] += 1

    return summary


def run_retention_sweep(vault_path: str | Path, retention_days: int = RETENTION_DAYS) -> int:
    """
    Delete JSON audit logs older than retention_days.

    Args:
        vault_path: Path to the Obsidian vault root.
        retention_days: Days to keep (default: 90).

    Returns:
        Number of files deleted.
    """
    logs_dir = _get_log_dir(vault_path)
    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted = 0

    for log_file in logs_dir.glob("*.json"):
        try:
            # Parse date from filename
            date_str = log_file.stem  # e.g. "2026-01-15"
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                log_file.unlink()
                deleted += 1
        except (ValueError, OSError):
            continue

    return deleted


if __name__ == "__main__":
    # Quick test
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./AI_Employee_Vault"

    # Write a test entry
    entry = log_audit(
        vault,
        action_type="test",
        actor="audit_logger_self_test",
        target="self",
        parameters={"test": True},
        result="success",
    )
    print(f"Wrote test entry: {json.dumps(entry, indent=2)}")

    # Query
    results = query_audit(vault, days=1, action_type="test")
    print(f"Found {len(results)} test entries")

    # Summary
    summary = get_audit_summary(vault, days=1)
    print(f"Summary: {json.dumps(summary, indent=2)}")
