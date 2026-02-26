---
name: gmail-watcher
description: Use when monitoring Gmail for new important emails. Runs the Gmail watcher script, processes unread messages, and creates action files in /Needs_Action with email metadata.
---

# Gmail Watcher Skill

Monitor Gmail for important unread emails and route them into the AI Employee vault.

## When to Use
- When the user says "check email", "watch Gmail", "monitor inbox"
- As part of the scheduled processing cycle
- When the Gmail watcher script needs to be started or checked

## Prerequisites
- Google OAuth credentials file: `client_secret_*.json` in project root
- First run will open browser for OAuth consent (saves `token.json`)
- Gmail API must be enabled in Google Cloud Console

## Running the Watcher

### One-time check
```bash
uv run python scripts/gmail_watcher.py --vault ./AI_Employee_Vault --once
```

### Continuous monitoring (every 2 minutes)
```bash
uv run python scripts/gmail_watcher.py --vault ./AI_Employee_Vault
```

### Dry run (no file changes)
```bash
uv run python scripts/gmail_watcher.py --dry-run
```

## What It Does

1. **Authenticates** with Gmail API using OAuth2 (first run opens browser)
2. **Fetches** unread emails from the primary inbox
3. **Classifies** priority based on sender, subject, and content keywords
4. **Creates** action files in `/Needs_Action/` with format:

```markdown
---
type: email
source: gmail
from: sender@example.com
subject: Email Subject
priority: high|medium|low
message_id: Gmail message ID
status: pending
created: ISO timestamp
---

## New Email for Processing

**From**: sender@example.com
**Subject**: Email Subject
**Date**: received date
**Priority**: high

## Body Preview
(first 1000 chars of email body)

## Suggested Actions
- [ ] Review email content
- [ ] Draft response if needed
- [ ] Take appropriate action
- [ ] Move to /Done when complete
```

5. **Tracks** processed message IDs in `processed_emails.json` to avoid duplicates
6. **Logs** all activity to `/Logs/{date}.md`

## Priority Classification
- **high**: Contains "urgent", "asap", "invoice", "payment", "deadline", "critical", or from known important contacts
- **medium**: Contains "meeting", "project", "review", "update", "client"
- **low**: Everything else

## Troubleshooting

### "credentials.json not found"
Ensure the Google OAuth client secret JSON is in the project root directory.

### "token.json expired"
Delete `token.json` and re-run — it will re-authenticate via browser.

### "Gmail API not enabled"
Go to Google Cloud Console → APIs & Services → Enable Gmail API.

## Integration with Other Skills
- After Gmail watcher creates action files, use `vault-triage` to process them
- Use `inbox-processor` for full end-to-end cycle including email processing
- Sensitive email actions (replies, forwards) go through `hitl-approval`
