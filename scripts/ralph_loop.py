"""
Ralph Wiggum Loop for AI Employee.

Autonomous task completion with file-movement-based completion detection.
Creates state file in /In_Progress/, invokes Claude Code, checks if file
moved to /Done/, re-invokes with context on retry.

Usage:
    uv run python scripts/ralph_loop.py --vault ./AI_Employee_Vault --task "Process all pending invoices"
    uv run python scripts/ralph_loop.py --task "Triage inbox and post LinkedIn update" --max-iterations 5
    uv run python scripts/ralph_loop.py --task "Send follow-up emails" --dry-run
"""

import argparse
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("RalphLoop")

# Safety limits
DEFAULT_MAX_ITERATIONS = 10
ABSOLUTE_MAX_ITERATIONS = 50
ITERATION_TIMEOUT = 300  # 5 minutes per iteration


def create_state_file(vault_path: Path, task: str, max_iterations: int) -> Path:
    """Create the Ralph Wiggum state file in /In_Progress/."""
    in_progress = vault_path / "In_Progress"
    in_progress.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", task)[:40].strip("_").lower()
    filename = f"RALPH_{timestamp}_{slug}.md"
    file_path = in_progress / filename

    content = f"""---
type: ralph_wiggum_loop
status: in_progress
created: {now.isoformat()}
task: {task}
max_iterations: {max_iterations}
current_iteration: 0
---

## Task

{task}

## Success Criteria

- Task described above is fully completed
- Relevant files moved to /Done/
- All actions logged

## Iteration Log

"""

    file_path.write_text(content, encoding="utf-8")
    logger.info(f"Created state file: {filename}")
    return file_path


def update_state_file(state_path: Path, iteration: int, action: str, result: str, status: str):
    """Append iteration notes to the state file."""
    if not state_path.exists():
        return

    now = datetime.now()
    content = state_path.read_text(encoding="utf-8")

    # Update current_iteration in frontmatter
    content = re.sub(
        r"current_iteration: \d+",
        f"current_iteration: {iteration}",
        content,
    )

    # Update status in frontmatter
    content = re.sub(
        r"status: \w+",
        f"status: {status}",
        content,
    )

    # Append iteration log
    content += f"""### Iteration {iteration} — {now.strftime('%Y-%m-%d %H:%M:%S')}

- **Action**: {action}
- **Result**: {result}
- **Status**: {status}

"""

    state_path.write_text(content, encoding="utf-8")


def check_completion(vault_path: Path, state_filename: str) -> bool:
    """Check if the state file has been moved to /Done/ (= task complete)."""
    done_path = vault_path / "Done" / state_filename
    return done_path.exists()


def check_rejected(vault_path: Path, state_filename: str) -> bool:
    """Check if human has moved state file to /Rejected/ (= abort)."""
    rejected_path = vault_path / "Rejected" / state_filename
    return rejected_path.exists()


def invoke_claude(task: str, context: str, vault_path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """Invoke Claude Code to work on the task."""
    if dry_run:
        logger.info(f"[DRY RUN] Would invoke Claude Code with task: {task[:100]}...")
        return True, "Dry run — no action taken"

    prompt = f"""You are working on a task in the Ralph Wiggum loop (autonomous retry).

TASK: {task}

VAULT PATH: {vault_path}

CONTEXT FROM PREVIOUS ITERATIONS:
{context if context else "(First iteration — no prior context)"}

INSTRUCTIONS:
1. Work on the task described above
2. Use the vault at {vault_path} for all file operations
3. When the task is complete, move the state file from /In_Progress/ to /Done/
4. If you need human approval for something, create a file in /Pending_Approval/
5. Log all actions to /Logs/
6. If you cannot complete the task, explain why in your response
"""

    try:
        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=ITERATION_TIMEOUT,
            cwd=str(vault_path.parent),
        )

        output = result.stdout[:2000] if result.stdout else ""
        error = result.stderr[:500] if result.stderr else ""

        if result.returncode == 0:
            return True, output or "Completed successfully"
        else:
            return False, f"Exit code {result.returncode}: {error or output}"

    except subprocess.TimeoutExpired:
        return False, f"Iteration timed out after {ITERATION_TIMEOUT}s"
    except FileNotFoundError:
        logger.warning("Claude Code CLI not found — falling back to log-only mode")
        return False, "Claude Code CLI not available"
    except Exception as e:
        return False, f"Error invoking Claude: {e}"


def log_action(logs_dir: Path, action_type: str, details: str):
    """Append to daily log."""
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


def log_audit(vault_path: Path, action_type: str, target: str, result: str):
    """Log to JSON audit log if available."""
    try:
        from scripts.audit_logger import log_audit as _log_audit
        _log_audit(
            vault_path,
            action_type=action_type,
            actor="ralph_loop",
            target=target,
            result=result,
        )
    except ImportError:
        pass


def run_loop(
    vault_path: Path,
    task: str,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    dry_run: bool = False,
):
    """Run the Ralph Wiggum autonomous completion loop."""
    logs_dir = vault_path / "Logs"

    # Clamp max iterations
    max_iterations = min(max_iterations, ABSOLUTE_MAX_ITERATIONS)

    logger.info(f"Starting Ralph Wiggum loop")
    logger.info(f"Task: {task}")
    logger.info(f"Max iterations: {max_iterations}")

    # Create state file
    state_path = create_state_file(vault_path, task, max_iterations)
    state_filename = state_path.name

    log_action(logs_dir, "ralph_loop_start", f"Task: {task} | Max: {max_iterations}")
    log_audit(vault_path, "ralph_loop_start", task, f"max_iterations={max_iterations}")

    context_log = ""

    for iteration in range(1, max_iterations + 1):
        logger.info(f"=== Iteration {iteration}/{max_iterations} ===")

        # Check if human aborted
        if check_rejected(vault_path, state_filename):
            logger.info("Task rejected by human — stopping loop")
            log_action(logs_dir, "ralph_loop_rejected", f"Iteration {iteration}: Human rejected")
            log_audit(vault_path, "ralph_loop_rejected", task, f"iteration={iteration}")
            return

        # Check if already done (human or previous iteration moved it)
        if check_completion(vault_path, state_filename):
            logger.info(f"Task completed! (detected at iteration {iteration})")
            log_action(logs_dir, "ralph_loop_done", f"Completed at iteration {iteration}")
            log_audit(vault_path, "ralph_loop_done", task, f"completed_at_iteration={iteration}")
            return

        # Invoke Claude Code
        success, result_text = invoke_claude(task, context_log, vault_path, dry_run=dry_run)

        # Update state file
        status = "in_progress" if not success else "in_progress"
        update_state_file(
            state_path, iteration,
            action=f"Claude invocation {'succeeded' if success else 'failed'}",
            result=result_text[:500],
            status=status,
        )

        # Accumulate context
        context_log += f"\n--- Iteration {iteration} ---\n"
        context_log += f"Success: {success}\n"
        context_log += f"Result: {result_text[:500]}\n"

        log_action(
            logs_dir, "ralph_loop_iteration",
            f"Iteration {iteration}: {'success' if success else 'failed'} — {result_text[:100]}",
        )
        log_audit(
            vault_path, "ralph_loop_iteration", task,
            f"iteration={iteration}, success={success}",
        )

        # Check completion after iteration
        if check_completion(vault_path, state_filename):
            logger.info(f"Task completed after iteration {iteration}!")
            log_action(logs_dir, "ralph_loop_done", f"Completed at iteration {iteration}")
            log_audit(vault_path, "ralph_loop_done", task, f"completed_at_iteration={iteration}")
            return

        if dry_run:
            logger.info("[DRY RUN] Would continue to next iteration")
            if iteration >= 2:
                logger.info("[DRY RUN] Stopping after 2 iterations for preview")
                break

        # Brief pause between iterations
        time.sleep(2)

    # Max iterations reached
    logger.warning(f"Max iterations ({max_iterations}) reached without completion")

    update_state_file(
        state_path, max_iterations,
        action="Max iterations reached",
        result="Task not completed within iteration limit",
        status="max_iterations_reached",
    )

    log_action(
        logs_dir, "ralph_loop_max_iterations",
        f"Stopped after {max_iterations} iterations — manual intervention needed",
    )
    log_audit(vault_path, "ralph_loop_max_iterations", task, f"stopped_at={max_iterations}")

    logger.info(f"State file remains in /In_Progress/: {state_filename}")
    logger.info("Manual intervention required to complete or abort this task.")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Ralph Wiggum Loop")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to the Obsidian vault (default: ./AI_Employee_Vault)",
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Task description for the loop to complete",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Maximum iterations (default: {DEFAULT_MAX_ITERATIONS}, max: {ABSOLUTE_MAX_ITERATIONS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mode — don't actually invoke Claude Code",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return

    run_loop(
        vault_path,
        task=args.task,
        max_iterations=args.max_iterations,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
