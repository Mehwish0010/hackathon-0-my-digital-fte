---
name: vault-triage
description: Use when processing items in /Needs_Action. Reads pending action files, classifies priority, creates plans, and moves completed items to /Done.
---

# Vault Triage Skill

Process pending action items in the AI Employee vault.

## When to Use
- When there are new files in `/AI_Employee_Vault/Needs_Action/`
- When the user asks to "process inbox" or "triage actions"
- When the file system watcher creates new action files

## Workflow

### Step 1: Scan Needs_Action
```bash
ls AI_Employee_Vault/Needs_Action/
```

Read each `.md` file to understand the pending items.

### Step 2: Classify and Prioritize
Read the frontmatter of each file. Priority levels:
- **high**: Contains "urgent", "payment", "invoice", "deadline" keywords
- **medium**: Client communication, project updates
- **low**: Informational, no deadline

### Step 3: Create Plan (if needed)
For complex items, create a plan file:

```markdown
# AI_Employee_Vault/Plans/PLAN_{description}_{date}.md
---
created: {ISO timestamp}
status: in_progress
related_action: {original action filename}
---

## Objective
{What needs to be done}

## Steps
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Notes
{Any relevant context}
```

### Step 4: Process Simple Items
For straightforward items (file categorization, info logging):
1. Read the content
2. Take the appropriate action
3. Update the action file status to "done"
4. Move the file to `/Done/`

### Step 5: Flag for Approval
If an action requires human approval (payments, external comms):
1. Create an approval request in `/Pending_Approval/`
2. Update the action file status to "awaiting_approval"
3. Do NOT proceed until the file appears in `/Approved/`

### Step 6: Log Everything
Append all actions to `/Logs/{YYYY-MM-DD}.md`

## Rules (from Company_Handbook.md)
- Never delete files - always move them
- Flag payments > $50 for approval
- Never auto-send to unknown contacts
- Process high priority items first

## Completion
After processing all items in /Needs_Action:
1. Update Dashboard.md with current stats
2. Log a summary in the daily log
