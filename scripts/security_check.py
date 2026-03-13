"""
Pre-Sync Security Scanner for AI Employee Vault.

Scans staged vault files for secret patterns (API keys, passwords, tokens)
and blocks sync if any are detected. Used as a pre-push hook by vault_sync.py.

Usage:
    uv run python scripts/security_check.py --vault ./AI_Employee_Vault
    uv run python scripts/security_check.py --vault ./AI_Employee_Vault --fix
"""

import argparse
import logging
import re
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SecurityCheck")

# Patterns that indicate secrets in file content
SECRET_PATTERNS = [
    (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']{8,}', "Password assignment"),
    (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}', "API key"),
    (r'(?i)(secret|token)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}', "Secret/token assignment"),
    (r'(?i)(access[_-]?key|aws[_-]?key)\s*[=:]\s*["\']?[A-Z0-9]{16,}', "Access key"),
    (r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----', "Private key file"),
    (r'(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}', "Bearer token"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub personal access token"),
    (r'sk-[A-Za-z0-9]{32,}', "API secret key (OpenAI/Stripe style)"),
    (r'(?i)client[_-]?secret\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}', "Client secret"),
]

# File extensions that should never be synced
BLOCKED_EXTENSIONS = {".key", ".pem", ".p12", ".pfx", ".jks", ".keystore"}

# Filenames that should never be synced
BLOCKED_FILENAMES = {
    ".env", "token.json", "credentials.json",
    "service_health.json", "process_health.json",
}


def scan_file(filepath: Path) -> list[str]:
    """Scan a single file for secret patterns.

    Returns list of issue descriptions (empty = clean).
    """
    issues = []

    # Check filename
    if filepath.name in BLOCKED_FILENAMES:
        issues.append(f"Blocked filename: {filepath.name}")
        return issues

    if filepath.name.startswith("client_secret_"):
        issues.append(f"Blocked filename pattern: {filepath.name}")
        return issues

    # Check extension
    if filepath.suffix.lower() in BLOCKED_EXTENSIONS:
        issues.append(f"Blocked extension: {filepath.suffix}")
        return issues

    # Skip binary files
    try:
        content = filepath.read_text(encoding="utf-8", errors="strict")
    except (UnicodeDecodeError, OSError):
        return issues  # Skip binary/unreadable files

    # Scan content for secret patterns
    for pattern, label in SECRET_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            issues.append(f"{label} detected in {filepath.name}")

    return issues


def scan_staged_files(vault_path: str) -> list[str]:
    """Scan all staged files in the vault Git repo for secrets.

    Returns list of issue descriptions (empty = clean, safe to push).
    """
    vault = Path(vault_path).resolve()
    all_issues = []

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(vault),
            capture_output=True,
            text=True,
            timeout=10,
        )
        staged_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # If git fails, scan all tracked .md files instead
        staged_files = []
        for f in vault.rglob("*"):
            if f.is_file() and not ".git" in f.parts:
                staged_files.append(str(f.relative_to(vault)))

    for rel_path in staged_files:
        filepath = vault / rel_path
        if filepath.exists() and filepath.is_file():
            issues = scan_file(filepath)
            for issue in issues:
                all_issues.append(f"{rel_path}: {issue}")

    return all_issues


def scan_directory(vault_path: str) -> list[str]:
    """Full scan of all vault files (not just staged)."""
    vault = Path(vault_path).resolve()
    all_issues = []

    for filepath in vault.rglob("*"):
        if filepath.is_file() and ".git" not in filepath.parts:
            issues = scan_file(filepath)
            for issue in issues:
                rel = filepath.relative_to(vault)
                all_issues.append(f"{rel}: {issue}")

    return all_issues


def main():
    parser = argparse.ArgumentParser(description="Vault Security Scanner")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Vault path")
    parser.add_argument("--staged", action="store_true", help="Only scan staged files")
    args = parser.parse_args()

    if args.staged:
        issues = scan_staged_files(args.vault)
    else:
        issues = scan_directory(args.vault)

    if issues:
        print(f"SECURITY CHECK FAILED — {len(issues)} issue(s):\n")
        for issue in issues:
            print(f"  [!] {issue}")
        print("\nFix these issues before syncing.")
        return 1
    else:
        print("Security check passed — no secrets detected.")
        return 0


if __name__ == "__main__":
    exit(main())
