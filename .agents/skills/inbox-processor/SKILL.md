---
name: inbox-processor
description: Use when processing the vault end-to-end. Runs the full cycle - triage /Needs_Action, execute actions, update dashboard, and generate daily log summary.
---

# Inbox Processor Skill

Full end-to-end processing of the AI Employee vault.

## When to Use
- When the user says "process everything", "check inbox", or "run cycle"
- For the daily automated processing run
- After the file watcher has queued new items

## Full Processing Cycle

### Phase 1: Read Context
1. Read `AI_Employee_Vault/Company_Handbook.md` for current rules
2. Read `AI_Employee_Vault/Business_Goals.md` for current priorities
3. Read `AI_Employee_Vault/Dashboard.md` for current state

### Phase 2: Process /Needs_Action
For each `.md` file in `/Needs_Action/`:

1. **Read** the file and its frontmatter
2. **Classify** based on type (file_drop, email, whatsapp, etc.)
3. **Decide** action based on Company Handbook rules:
   - Auto-processable? -> Execute and move to `/Done/`
   - Needs approval? -> Create request in `/Pending_Approval/`
   - Complex task? -> Create plan in `/Plans/`
4. **Log** the action in `/Logs/{date}.md`

### Phase 3: Check /Pending_Approval
1. Look for items that have been moved to `/Approved/`
2. Execute the approved actions
3. Move completed approvals to `/Done/`
4. Log execution results

### Phase 4: Update Dashboard
Refresh `Dashboard.md` with:
- Updated counts for all folders
- Recent activity from today's log
- Any new pending actions
- Current system status

### Phase 5: Generate Summary
Output a brief summary to the user:
```
Processing complete:
- X items triaged
- Y items auto-processed
- Z items pending approval
- Dashboard updated
```

## Error Handling
- If a file cannot be read, log the error and skip it
- Never delete files that fail processing - leave them in place
- Log all errors to the daily log file

## Rules Reminder
- Read Company_Handbook.md FIRST every cycle
- High priority items are processed before low
- Payments and external communications always need approval
- All actions are logged
