"""
Gmail Watcher for AI Employee.

Monitors Gmail for unread important emails and creates action files
in /Needs_Action/ for Claude Code to process.

Usage:
    uv run python scripts/gmail_watcher.py
    uv run python scripts/gmail_watcher.py --vault ./AI_Employee_Vault
    uv run python scripts/gmail_watcher.py --once
    uv run python scripts/gmail_watcher.py --dry-run
"""

import argparse
import base64
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("GmailWatcher")

# Gmail API scope (read-only for watcher)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

# Priority keywords
HIGH_PRIORITY_KEYWORDS = ["urgent", "asap", "invoice", "payment", "deadline", "critical", "important"]
MEDIUM_PRIORITY_KEYWORDS = ["meeting", "project", "review", "update", "client", "proposal", "schedule"]

# Path to track processed emails
PROCESSED_FILE = "processed_emails.json"


def get_credentials(credentials_path: str, token_path: str) -> Credentials:
    """Get or refresh Gmail API credentials."""
    creds = None

    if Path(token_path).exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
        else:
            logger.info("Starting OAuth flow — browser will open for consent...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        Path(token_path).write_text(creds.to_json())
        logger.info(f"Token saved to {token_path}")

    return creds


def load_processed_ids(path: Path) -> set:
    """Load set of already-processed message IDs."""
    if path.exists():
        data = json.loads(path.read_text())
        return set(data)
    return set()


def save_processed_ids(path: Path, ids: set):
    """Save processed message IDs."""
    path.write_text(json.dumps(list(ids), indent=2))


def classify_priority(subject: str, body: str, sender: str) -> str:
    """Classify email priority based on content."""
    text = f"{subject} {body} {sender}".lower()
    if any(kw in text for kw in HIGH_PRIORITY_KEYWORDS):
        return "high"
    if any(kw in text for kw in MEDIUM_PRIORITY_KEYWORDS):
        return "medium"
    return "low"


def extract_body(payload: dict) -> str:
    """Extract plain text body from Gmail message payload."""
    body = ""

    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    elif payload.get("parts"):
        for part in payload["parts"]:
            mime = part.get("mimeType", "")
            if mime == "text/plain" and part.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                break
            elif mime.startswith("multipart/") and part.get("parts"):
                # Nested multipart
                for sub in part["parts"]:
                    if sub.get("mimeType") == "text/plain" and sub.get("body", {}).get("data"):
                        body = base64.urlsafe_b64decode(sub["body"]["data"]).decode("utf-8", errors="replace")
                        break
                if body:
                    break

    return body


def get_header(headers: list, name: str) -> str:
    """Get a specific header value from message headers."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def create_action_file(vault_path: Path, msg_data: dict) -> Path:
    """Create an action file in /Needs_Action/ for an email."""
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    headers = msg_data.get("payload", {}).get("headers", [])
    sender = get_header(headers, "From")
    subject = get_header(headers, "Subject") or "(no subject)"
    date = get_header(headers, "Date")
    message_id = msg_data["id"]

    body = extract_body(msg_data.get("payload", {}))
    priority = classify_priority(subject, body, sender)

    # Sanitize subject for filename
    safe_subject = "".join(c if c.isalnum() or c in " -_" else "" for c in subject)[:50].strip()
    safe_subject = safe_subject.replace(" ", "_")

    action_filename = f"EMAIL_{timestamp}_{safe_subject}.md"
    needs_action = vault_path / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)
    action_path = needs_action / action_filename

    # Truncate body preview
    body_preview = body[:1000]
    if len(body) > 1000:
        body_preview += "\n\n_(truncated — full email available via Gmail)_"

    content = f"""---
type: email
source: gmail
from: {sender}
subject: "{subject}"
priority: {priority}
message_id: {message_id}
status: pending
created: {now.isoformat()}
---

## New Email for Processing

**From**: {sender}
**Subject**: {subject}
**Date**: {date}
**Priority**: {priority}

## Body Preview

```
{body_preview}
```

## Suggested Actions
- [ ] Review email content
- [ ] Draft response if needed
- [ ] Take appropriate action
- [ ] Move to /Done when complete
"""

    action_path.write_text(content, encoding="utf-8")
    return action_path


def log_action(vault_path: Path, action_type: str, details: str):
    """Append to daily log."""
    logs_dir = vault_path / "Logs"
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


def check_gmail(service, vault_path: Path, processed_ids: set, dry_run: bool = False) -> set:
    """Check Gmail for unread messages and create action files."""
    new_ids = set()

    try:
        # Fetch unread messages from primary inbox
        results = service.users().messages().list(
            userId="me",
            q="is:unread category:primary",
            maxResults=10,
        ).execute()

        messages = results.get("messages", [])

        if not messages:
            logger.info("No new unread emails.")
            return new_ids

        for msg_stub in messages:
            msg_id = msg_stub["id"]

            if msg_id in processed_ids:
                continue

            # Fetch full message
            msg = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full",
            ).execute()

            headers = msg.get("payload", {}).get("headers", [])
            subject = get_header(headers, "Subject") or "(no subject)"
            sender = get_header(headers, "From")

            if dry_run:
                logger.info(f"[DRY RUN] Would process: {subject} from {sender}")
            else:
                action_path = create_action_file(vault_path, msg)
                log_action(vault_path, "gmail_email", f"From: {sender} | Subject: {subject}")
                logger.info(f"Created action file: {action_path.name}")

            new_ids.add(msg_id)

    except Exception as e:
        logger.error(f"Error checking Gmail: {e}")

    return new_ids


def find_credentials_file() -> str:
    """Find the Google OAuth client secret file."""
    project_root = Path(__file__).parent.parent

    # Check for common names
    for pattern in ["client_secret_*.json", "credentials.json"]:
        matches = list(project_root.glob(pattern))
        if matches:
            return str(matches[0])

    raise FileNotFoundError(
        "No Google OAuth credentials file found. "
        "Download from Google Cloud Console and place in project root as 'credentials.json' "
        "or 'client_secret_*.json'"
    )


def main():
    parser = argparse.ArgumentParser(description="AI Employee Gmail Watcher")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=120,
        help="Check interval in seconds (default: 120)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (don't loop)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without creating files",
    )
    parser.add_argument(
        "--credentials",
        default=None,
        help="Path to Google OAuth credentials JSON",
    )
    parser.add_argument(
        "--token",
        default="token.json",
        help="Path to save/load OAuth token (default: token.json)",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    # Find credentials
    creds_path = args.credentials or find_credentials_file()
    logger.info(f"Using credentials: {creds_path}")

    # Authenticate
    creds = get_credentials(creds_path, args.token)
    service = build("gmail", "v1", credentials=creds)
    logger.info("Gmail API connected successfully.")

    # Load processed IDs
    processed_path = Path(PROCESSED_FILE)
    processed_ids = load_processed_ids(processed_path)
    logger.info(f"Tracking {len(processed_ids)} previously processed emails.")

    if args.dry_run:
        logger.info("[DRY RUN MODE] No files will be created.")

    if args.once:
        new_ids = check_gmail(service, vault_path, processed_ids, dry_run=args.dry_run)
        processed_ids.update(new_ids)
        if not args.dry_run:
            save_processed_ids(processed_path, processed_ids)
        logger.info(f"Processed {len(new_ids)} new emails.")
        return

    # Continuous monitoring loop
    logger.info(f"Watching Gmail every {args.interval}s. Press Ctrl+C to stop.")
    try:
        while True:
            new_ids = check_gmail(service, vault_path, processed_ids, dry_run=args.dry_run)
            processed_ids.update(new_ids)
            if new_ids and not args.dry_run:
                save_processed_ids(processed_path, processed_ids)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Gmail watcher stopped.")
        if not args.dry_run:
            save_processed_ids(processed_path, processed_ids)


if __name__ == "__main__":
    main()
