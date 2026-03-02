---
name: ralph-wiggum-loop
description: Use for autonomous task completion with retry logic. Creates a state file, invokes Claude Code, detects completion by file movement to /Done/, and retries with accumulated context on failure. Max iterations safeguard prevents infinite loops.
---

# Ralph Wiggum Loop Skill

Autonomous task completion loop with file-movement-based completion detection and retry logic.

## When to Use
- When the user says "keep trying until it's done", "ralph wiggum this"
- When a task needs multiple attempts to complete
- When autonomous retry with context accumulation is needed
- When a task should run to completion without human intervention (within safety limits)
- **Do NOT use** for simple one-shot tasks — only for complex multi-step work

## How It Works

The Ralph Wiggum loop uses a simple but effective completion detection mechanism:

1. **Create state file** in `/In_Progress/` describing the task
2. **Invoke Claude Code** to work on the task
3. **Check if state file moved** to `/Done/` (= task complete)
4. **If not done**: re-invoke with accumulated context from previous iterations
5. **Repeat** until done or max iterations reached

## Workflow

### Step 1: Identify the Task
Before starting the loop, clearly define:
- What needs to be accomplished (success criteria)
- What file(s) should end up in `/Done/` when complete
- Maximum iterations allowed (default: 10)

### Step 2: Start the Loop
```bash
uv run python scripts/ralph_loop.py \
    --vault ./AI_Employee_Vault \
    --task "Process all pending invoices and send follow-up emails" \
    --max-iterations 10
```

### Step 3: Monitor Progress
The loop creates a state file: `/In_Progress/RALPH_{timestamp}_{task_slug}.md`

```markdown
---
type: ralph_wiggum_loop
status: in_progress
created: {ISO timestamp}
task: {task description}
max_iterations: 10
current_iteration: 3
---

## Task
{Full task description}

## Iteration Log

### Iteration 1 — {timestamp}
- Action: Checked pending invoices, found 5
- Result: Created approval files for 3 invoices
- Status: Partially complete

### Iteration 2 — {timestamp}
- Action: Processed approved invoices
- Result: 2 invoices sent, 1 failed (Odoo unavailable)
- Status: Retrying failed invoice

### Iteration 3 — {timestamp}
- Action: Retried failed invoice
- Result: Success — all invoices processed
- Status: Moving to Done
```

### Step 4: Completion Detection
The loop checks for completion by:
1. Looking for the state file — if it's in `/Done/`, task is complete
2. Checking the state file's `status` field — if "done" or "completed"
3. Verifying success criteria defined in the task

### Step 5: Max Iterations Safeguard
If max iterations is reached without completion:
- The state file is annotated with "MAX_ITERATIONS_REACHED"
- The loop stops and logs the incomplete status
- Human intervention is flagged
- The file stays in `/In_Progress/` for manual review

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--task` | (required) | Task description |
| `--max-iterations` | 10 | Maximum retry attempts |
| `--vault` | ./AI_Employee_Vault | Vault path |
| `--dry-run` | false | Preview without executing |

## When to Use Loop vs Single-Pass

| Scenario | Use Loop? | Why |
|----------|-----------|-----|
| Send one email | No | Single action, no retry needed |
| Process all inbox items | **Yes** | Multiple items, some may fail |
| Post to 4 platforms | **Yes** | Each platform may fail independently |
| Generate CEO briefing | No | Single generation, deterministic |
| Resolve all overdue invoices | **Yes** | Requires multiple steps, may need retry |
| Complex multi-step plan | **Yes** | Steps depend on each other, may fail |

## State File Interpretation

| Status | Meaning |
|--------|---------|
| `in_progress` | Loop is actively working |
| `waiting_approval` | Blocked on human approval |
| `retrying` | Previous attempt failed, trying again |
| `done` | Task completed successfully |
| `max_iterations_reached` | Gave up — needs human help |
| `error` | Unrecoverable error occurred |

## Safety Features
- **Max iterations cap** prevents infinite loops (default: 10, absolute max: 50)
- Each iteration is audit-logged
- State file preserves full context across iterations
- Human can intervene by moving state file to `/Done/` (force complete) or `/Rejected/` (abort)
- The loop respects HITL — it creates approval files, doesn't bypass them
- Errors are caught and logged, not swallowed

## Important Notes
- The loop calls Claude Code as a subprocess — each iteration is a fresh invocation with context
- Context accumulates in the state file, so each iteration is more informed than the last
- Keep task descriptions specific and measurable ("process 5 invoices" not "do invoicing")
- For tasks requiring approval, the loop will pause and resume after approval
- Use `--dry-run` first to verify the loop understands the task

## Integration
- `reasoning-loop` — the Ralph Wiggum loop can invoke the reasoning loop for each iteration
- `hitl-approval` — loop respects and creates approval requests
- `error_recovery.py` — loop uses retry/backoff for external API calls
- `audit_logger.py` — every iteration is audit-logged
- Scheduler can trigger loops for recurring complex tasks
