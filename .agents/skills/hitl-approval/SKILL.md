---
name: hitl-approval
description: Use when an action requires human approval before execution. Creates approval request files in /Pending_Approval, monitors /Approved and /Rejected folders, and executes approved actions.
---

# Human-in-the-Loop Approval Skill

Manage the approval workflow for sensitive actions that require human sign-off.

## When to Use
- When an action involves sending emails, posting to social media, or making payments
- When Company_Handbook.md rules flag an item for approval
- When the user asks to "approve", "review pending", or "check approvals"
- When the approval watcher detects new files in `/Approved/`

## Approval Workflow

### Phase 1: Create Approval Request
When Claude determines an action needs human approval, create a file in `/Pending_Approval/`:

```markdown
# AI_Employee_Vault/Pending_Approval/{ACTION_TYPE}_{description}_{date}.md
---
type: approval_request
action_type: email_send|linkedin_post|payment|external_comm
status: pending_approval
created: {ISO timestamp}
urgency: high|medium|low
source_file: {original action file path}
auto_expire: {optional expiry date}
---

## Action Requiring Approval

**Type**: {Human-readable action type}
**Urgency**: {high/medium/low}
**Source**: {What triggered this — email, watcher, manual request}

## Proposed Action
{Detailed description of what will happen if approved}

## Context
{Why this action is being proposed — relevant background}

## Risk Assessment
- **Impact**: {What changes if this executes}
- **Reversible**: {Yes/No}
- **Cost**: {If applicable}

## Instructions for Reviewer
- **To Approve**: Move this file to `/Approved/`
- **To Reject**: Move this file to `/Rejected/`
- **To Edit**: Modify the "Proposed Action" section before approving
```

### Phase 2: Human Reviews in Obsidian
The human opens the vault in Obsidian and:
1. Reads the approval request
2. Optionally edits the proposed action
3. Moves the file to `/Approved/` or `/Rejected/`

### Phase 3: Execute or Archive

**If Approved** (file appears in `/Approved/`):
1. Read the approved file
2. Parse the `action_type` from frontmatter
3. Execute the corresponding action:
   - `email_send` → Use Email MCP server to send
   - `linkedin_post` → Trigger LinkedIn poster
   - `payment` → Log and notify (manual execution)
   - `external_comm` → Execute the specified communication
4. Update file status to "executed"
5. Move to `/Done/`
6. Log execution in `/Logs/`

**If Rejected** (file appears in `/Rejected/`):
1. Read rejection (human may have added notes)
2. Update file status to "rejected"
3. Log rejection in `/Logs/`
4. No action is taken

### Phase 4: Monitor with Approval Watcher
Run the approval watcher to auto-detect approvals:

```bash
uv run python scripts/approval_watcher.py --vault ./AI_Employee_Vault
```

## What Requires Approval (from Company_Handbook.md)
- Sending emails to external contacts
- Posting to social media (LinkedIn, Twitter, etc.)
- Any payment or financial transaction > $50
- Communications to unknown/new contacts
- Deleting or modifying important files
- Any action flagged as "sensitive" by the reasoning loop

## Checking Pending Approvals

### List pending items
```bash
ls AI_Employee_Vault/Pending_Approval/
```

### Check recently approved
```bash
ls AI_Employee_Vault/Approved/
```

### Check rejections
```bash
ls AI_Employee_Vault/Rejected/
```

## Action Type Prefixes
Use these prefixes when creating approval files:
- `EMAIL_` — Email sending/replying
- `LINKEDIN_` — LinkedIn posts
- `PAYMENT_` — Financial transactions
- `COMM_` — Other external communications
- `ACTION_` — General sensitive actions

## Logging
All approval activity is logged to `/Logs/{date}.md`:
```
- [HH:MM:SS] **approval_created**: {filename} (urgency: {level})
- [HH:MM:SS] **approval_granted**: {filename}
- [HH:MM:SS] **approval_rejected**: {filename}
- [HH:MM:SS] **action_executed**: {filename} (result: success|failure)
```

## Safety Rules
- NEVER execute a sensitive action without an approval file in `/Approved/`
- NEVER auto-approve — the human must physically move the file
- Always log both approvals and rejections
- If an approval file is malformed, flag it and do not execute
- Expired approval requests should be moved to `/Rejected/` with a note
