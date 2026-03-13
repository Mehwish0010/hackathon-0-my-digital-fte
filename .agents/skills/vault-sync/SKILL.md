# Vault Sync Skill

## Description
Manages Git-based vault synchronization between cloud and local instances, including conflict resolution and claim-by-move task ownership.

## Trigger Phrases
- "sync vault"
- "check sync status"
- "resolve sync conflict"
- "claim task"

## Instructions

### Initialize Vault Sync
1. Set `VAULT_GIT_REMOTE` env var to a private Git repository URL
2. Run: `python scripts/vault_sync.py --vault ./AI_Employee_Vault --init`
3. Verify: check `AI_Employee_Vault/.git/` exists

### Manual Sync
1. Run: `python scripts/vault_sync.py --vault ./AI_Employee_Vault --once`
2. Check result in `AI_Employee_Vault/Updates/sync_status_*.md`

### Claim-by-Move
1. Use `scripts/claim_manager.py` to prevent double-work:
   - `claim_task("cloud", "EMAIL_*.md")` → moves to `/In_Progress/cloud/`
   - `release_task("cloud", "EMAIL_*.md", target="Done")` → moves to `/Done/`
2. If file is already in `/In_Progress/<agent>/`, claim is rejected
3. Check available tasks: `python scripts/claim_manager.py ./AI_Employee_Vault`

### Conflict Resolution
- **Last-write-wins** for `.md` files during pull
- Cloud signals go to `/Updates/` (never direct Dashboard writes)
- Local agent merges signals (single-writer rule for Dashboard.md)

### Security
- `scripts/security_check.py` runs before every push
- Blocks sync if secrets detected (API keys, passwords, tokens)
- Run manual scan: `python scripts/security_check.py --vault ./AI_Employee_Vault`

## Files
- `scripts/vault_sync.py` — Git sync engine
- `scripts/claim_manager.py` — Claim-by-move task ownership
- `scripts/security_check.py` — Pre-sync secrets scanner
- `AI_Employee_Vault/.gitignore` — Vault sync security filter
