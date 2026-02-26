"""
Email MCP Server for AI Employee.

Exposes Gmail tools (send_email, draft_email, list_emails) via the
Model Context Protocol so Claude Code can send emails directly.

Usage:
    uv run python mcp_servers/email_server.py

Register in .claude/settings.json to make tools available to Claude Code.
"""

import base64
import json
import logging
from email.mime.text import MIMEText
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmailMCP")

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

# Initialize MCP server
mcp = FastMCP("AI Employee Email Server")


def _get_gmail_service():
    """Get authenticated Gmail API service."""
    token_path = Path("token.json")
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Find credentials file
            project_root = Path(__file__).parent.parent
            creds_files = list(project_root.glob("client_secret_*.json"))
            if not creds_files:
                creds_file = project_root / "credentials.json"
            else:
                creds_file = creds_files[0]

            if not creds_file.exists():
                raise FileNotFoundError(
                    "No Google OAuth credentials found. "
                    "Run gmail_watcher.py first to authenticate."
                )

            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _get_header(headers: list, name: str) -> str:
    """Extract a header value from Gmail message headers."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain text email body

    Returns:
        Confirmation message with sent message ID
    """
    try:
        service = _get_gmail_service()

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId="me",
            body={"raw": raw},
        ).execute()

        msg_id = result.get("id", "unknown")
        logger.info(f"Email sent to {to} (ID: {msg_id})")
        return f"Email sent successfully to {to}. Message ID: {msg_id}"

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return f"Error sending email: {str(e)}"


@mcp.tool()
def draft_email(to: str, subject: str, body: str) -> str:
    """Create a draft email in Gmail (does not send).

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain text email body

    Returns:
        Confirmation message with draft ID
    """
    try:
        service = _get_gmail_service()

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw}},
        ).execute()

        draft_id = result.get("id", "unknown")
        logger.info(f"Draft created for {to} (ID: {draft_id})")
        return f"Draft created successfully for {to}. Draft ID: {draft_id}. Review in Gmail before sending."

    except Exception as e:
        logger.error(f"Failed to create draft: {e}")
        return f"Error creating draft: {str(e)}"


@mcp.tool()
def list_emails(query: str = "is:unread", max_results: int = 10) -> str:
    """List emails from Gmail matching a query.

    Args:
        query: Gmail search query (default: "is:unread"). Examples:
               "is:unread", "from:boss@company.com", "subject:invoice",
               "is:unread category:primary", "newer_than:1d"
        max_results: Maximum number of emails to return (default: 10)

    Returns:
        Formatted list of matching emails with sender, subject, date, and snippet
    """
    try:
        service = _get_gmail_service()

        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()

        messages = results.get("messages", [])

        if not messages:
            return f"No emails found matching query: {query}"

        output_lines = [f"Found {len(messages)} email(s) matching '{query}':\n"]

        for msg_stub in messages:
            msg = service.users().messages().get(
                userId="me",
                id=msg_stub["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()

            headers = msg.get("payload", {}).get("headers", [])
            sender = _get_header(headers, "From")
            subject = _get_header(headers, "Subject") or "(no subject)"
            date = _get_header(headers, "Date")
            snippet = msg.get("snippet", "")

            output_lines.append(f"---")
            output_lines.append(f"**From**: {sender}")
            output_lines.append(f"**Subject**: {subject}")
            output_lines.append(f"**Date**: {date}")
            output_lines.append(f"**Preview**: {snippet[:150]}")
            output_lines.append(f"**ID**: {msg_stub['id']}")

        return "\n".join(output_lines)

    except Exception as e:
        logger.error(f"Failed to list emails: {e}")
        return f"Error listing emails: {str(e)}"


if __name__ == "__main__":
    mcp.run()
