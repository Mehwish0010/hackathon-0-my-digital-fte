"""
Odoo Automated Backup for AI Employee.

Creates daily backups of the Odoo database via XML-RPC
with 30-day retention policy.

Usage:
    uv run python scripts/odoo_backup.py
    uv run python scripts/odoo_backup.py --vault ./AI_Employee_Vault
"""

import argparse
import logging
import os
import xmlrpc.client
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OdooBackup")

BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", "./backups/odoo"))
RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "30"))


def backup_odoo(vault_path: str | None = None) -> str | None:
    """Create an Odoo database backup.

    Returns the backup file path on success, None on failure.
    """
    url = os.environ.get("ODOO_URL", "")
    db = os.environ.get("ODOO_DB", "")
    password = os.environ.get("ODOO_PASSWORD", "")

    if not all([url, db]):
        logger.info("Odoo not configured — skipping backup")
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    backup_name = f"odoo_{db}_{now.strftime('%Y%m%d_%H%M%S')}.zip"
    backup_path = BACKUP_DIR / backup_name

    try:
        # Use Odoo's database management RPC
        db_proxy = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/db", allow_none=True)
        backup_data = db_proxy.dump(password, db, "zip")

        # Write backup
        import base64
        with open(backup_path, "wb") as f:
            f.write(base64.b64decode(backup_data))

        size_mb = backup_path.stat().st_size / (1024 * 1024)
        logger.info(f"Backup created: {backup_name} ({size_mb:.1f} MB)")

        # Log to vault
        if vault_path:
            _log_backup(vault_path, backup_name, size_mb)

        return str(backup_path)

    except xmlrpc.client.Fault as e:
        # Backup endpoint may not be available on all Odoo instances
        logger.warning(f"Odoo backup RPC not available: {e.faultString}")
        return None
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None


def cleanup_old_backups() -> int:
    """Delete backups older than retention period. Returns count deleted."""
    if not BACKUP_DIR.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    deleted = 0

    for f in BACKUP_DIR.iterdir():
        if f.is_file() and f.suffix == ".zip":
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
                deleted += 1
                logger.info(f"Deleted old backup: {f.name}")

    return deleted


def _log_backup(vault_path: str, backup_name: str, size_mb: float):
    """Log backup event to vault."""
    logs_dir = Path(vault_path) / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.md"
    entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **odoo_backup**: {backup_name} ({size_mb:.1f} MB)\n"

    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        content += entry
    else:
        content = f"# Activity Log - {today}\n\n{entry}"

    log_file.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Odoo Automated Backup")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Vault path")
    args = parser.parse_args()

    # Create backup
    result = backup_odoo(args.vault)
    if result:
        print(f"Backup saved: {result}")
    else:
        print("Backup skipped or failed")

    # Cleanup old backups
    deleted = cleanup_old_backups()
    if deleted:
        print(f"Cleaned up {deleted} old backup(s)")


if __name__ == "__main__":
    main()
