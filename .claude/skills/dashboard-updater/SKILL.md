---
name: dashboard-updater
description: Use when updating the AI Employee Dashboard.md. Scans vault folders, counts items, updates stats, and refreshes the dashboard with current status.
---

# Dashboard Updater Skill

Update the AI Employee Dashboard with current vault status.

## When to Use
- After processing triage items
- When the user asks for a "status update" or "dashboard refresh"
- At the start of a new work session

## Workflow

### Step 1: Count Items in Each Folder
```bash
ls AI_Employee_Vault/Inbox/ | wc -l
ls AI_Employee_Vault/Needs_Action/ | wc -l
ls AI_Employee_Vault/In_Progress/ | wc -l
ls AI_Employee_Vault/Done/ | wc -l
ls AI_Employee_Vault/Pending_Approval/ | wc -l
```

Exclude `.gitkeep` files from counts.

### Step 2: Read Recent Activity
Check the latest log file in `/Logs/` for today's activity.

### Step 3: Check Pending Actions
Read each file in `/Needs_Action/` and extract:
- Source type (file_drop, email, whatsapp, etc.)
- Summary (from the file content)
- Priority (from frontmatter)
- Created date

### Step 4: Update Dashboard.md
Rewrite `AI_Employee_Vault/Dashboard.md` with the current data:

```markdown
---
last_updated: {current ISO date}
auto_refresh: true
---

# AI Employee Dashboard

## System Status
| Component | Status | Last Check |
|-----------|--------|------------|
| File Watcher | {Running/Stopped} | {timestamp} |
| Vault Integration | Active | {timestamp} |

## Pending Actions
| # | Source | Summary | Priority | Created |
|---|--------|---------|----------|---------|
{table rows from Needs_Action files}

## Recent Activity
{last 10 entries from today's log}

## Quick Stats
- **Inbox items**: {count}
- **Needs Action**: {count}
- **In Progress**: {count}
- **Done (this week)**: {count}
- **Pending Approval**: {count}

## Upcoming Deadlines
{any items with deadline metadata}

---
*Auto-updated by AI Employee. Last refresh: {timestamp}*
```

## Important
- Always preserve the YAML frontmatter format
- Keep the dashboard concise - it's a quick-glance view
- Include the auto-update timestamp at the bottom
