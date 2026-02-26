---
name: reasoning-loop
description: Use when Claude needs to reason through a complex task. Reads /Needs_Action items, creates structured Plan.md files with steps, executes the plan step-by-step, and updates progress as each step completes.
---

# Claude Reasoning Loop Skill

Structured reasoning and planning for complex tasks in the AI Employee vault.

## When to Use
- When a task in `/Needs_Action/` requires multiple steps
- When the user says "create a plan", "think through this", "reason about"
- For any non-trivial action that benefits from step-by-step execution
- When orchestrating multiple skills together

## The Reasoning Loop: Read → Think → Plan → Act → Log

### Step 1: READ — Gather Context
```
1. Read AI_Employee_Vault/Company_Handbook.md (rules)
2. Read AI_Employee_Vault/Business_Goals.md (priorities)
3. Read AI_Employee_Vault/Dashboard.md (current state)
4. Read the specific item(s) in /Needs_Action/ to process
5. Check /Pending_Approval/ for any awaiting items
6. Check /Approved/ for any ready-to-execute items
```

### Step 2: THINK — Analyze and Decide
Evaluate each item:
- What type of task is this?
- What is the priority?
- Can it be auto-processed or does it need approval?
- What skills/tools are needed?
- What are the dependencies?
- What could go wrong?

### Step 3: PLAN — Create Plan.md
For complex tasks, create a plan file:

```markdown
# AI_Employee_Vault/Plans/PLAN_{description}_{date}.md
---
status: pending
created: {ISO timestamp}
source: {what triggered this plan}
related_files:
  - {path to related action file}
estimated_steps: {number}
requires_approval: true|false
---

## Objective
{Clear statement of what needs to be accomplished}

## Context
{Background information, business goals alignment, relevant handbook rules}

## Steps
- [ ] Step 1: {description}
  - Tool/Skill: {what will be used}
  - Expected output: {what this produces}
- [ ] Step 2: {description}
  - Tool/Skill: {what will be used}
  - Expected output: {what this produces}
- [ ] Step 3: {description}
  - Tool/Skill: {what will be used}
  - Expected output: {what this produces}

## Approval Required
{List any steps that need human approval before execution}

## Rollback Plan
{What to do if something goes wrong}

## Success Criteria
{How to verify the plan was executed correctly}
```

### Step 4: ACT — Execute the Plan
Process each step sequentially:

1. Update plan status to `in_progress`
2. For each step:
   a. Check if the step requires approval → route through `hitl-approval`
   b. Execute the step using the appropriate skill/tool
   c. Mark the step as complete: `- [x] Step N`
   d. Log the result
   e. If a step fails, stop and log the error
3. After all steps complete, update plan status to `done`

### Step 5: LOG — Record Everything
After execution:
1. Log results to `/Logs/{date}.md`
2. Update `/Dashboard.md` via `dashboard-updater` skill
3. Move completed action files to `/Done/`
4. Move completed plan to `/Done/`

## Plan Status Values
- `pending` — Plan created, not yet started
- `in_progress` — Currently executing steps
- `blocked` — Waiting for approval or external input
- `done` — All steps completed successfully
- `failed` — A step failed, see error notes

## Example: Processing an Important Email

```
READ:  New email from client about invoice in /Needs_Action/EMAIL_2026-02-25_invoice.md
THINK: This is a payment-related email (high priority). Needs approval per handbook.
PLAN:  1. Extract invoice details  2. Create approval request  3. After approval, draft reply
ACT:   Execute step 1 → Create approval file → Wait for human
LOG:   "Email processed, pending approval for payment action"
```

## Example: LinkedIn Content Creation

```
READ:  Business goal says "post 3x/week on LinkedIn about AI automation"
THINK: Need to create a post aligned with business goals. Requires approval.
PLAN:  1. Research trending topics  2. Draft post content  3. Create approval request
ACT:   Draft content → Create LINKEDIN_*.md in /Pending_Approval/
LOG:   "LinkedIn draft created, pending human review"
```

## Integration with Other Skills
- `vault-triage` — For initial classification of /Needs_Action items
- `hitl-approval` — For routing sensitive steps through approval
- `gmail-watcher` — Source of email-based action items
- `linkedin-poster` — For executing approved LinkedIn posts
- `dashboard-updater` — For updating status after plan execution
- `inbox-processor` — Can trigger reasoning loop for complex items

## Rules
- Always read Company_Handbook.md before creating a plan
- Never skip the planning step for multi-step tasks
- Always create a plan file for tasks with 3+ steps
- Update plan status in real-time as steps complete
- If a step fails, do NOT continue — log the error and stop
- Sensitive actions always go through approval, even if planned
