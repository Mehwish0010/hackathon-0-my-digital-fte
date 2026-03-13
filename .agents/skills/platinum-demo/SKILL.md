# Platinum Demo Skill

## Description
Runs and interprets the Platinum tier end-to-end demo, verifying the minimum passing gate: Email → Cloud Draft → Sync → Approve → Send → Done → Logged.

## Trigger Phrases
- "run platinum demo"
- "test platinum tier"
- "verify cloud deployment"
- "end-to-end test"

## Instructions

### Run Demo (Dry Run)
```bash
python scripts/platinum_demo.py --vault ./AI_Employee_Vault
```

### Run Demo (Live — actually sends email)
```bash
python scripts/platinum_demo.py --vault ./AI_Employee_Vault --live
```

### Demo Steps
The demo verifies these 7 steps:
1. **Simulate email** — Creates test `EMAIL_*.md` in `/Needs_Action/`
2. **Cloud triage** — Cloud agent processes email, creates draft in `/Pending_Approval/email/`
3. **Sync check** — Verifies vault sync infrastructure is available
4. **Approve** — Moves draft to `/Approved/` (simulates human approval)
5. **Local execute** — Local agent processes approved item
6. **Verify Done** — Confirms file reached `/Done/` folder
7. **Audit trail** — Checks log entries exist

### Interpreting Results
- **ALL PASSED**: Platinum minimum gate achieved
- **Step 2 FAIL**: Cloud agent not triaging — check `scripts/cloud_agent.py`
- **Step 4 FAIL**: Approval file not found — check `/Pending_Approval/email/`
- **Step 5 FAIL**: Local execution failed — check `scripts/local_agent.py`
- **Step 7 FAIL**: No audit entries — check `AI_Employee_Vault/Logs/`

### After Demo
- Demo auto-cleans test files
- Check `AI_Employee_Vault/Logs/YYYY-MM-DD.md` for activity log
- Review `Dashboard.md` for updated deployment status

## Files
- `scripts/platinum_demo.py` — Demo script
- `scripts/cloud_agent.py` — Cloud agent (tested in step 2)
- `scripts/local_agent.py` — Local agent (tested in step 5)
- `scripts/vault_sync.py` — Sync infrastructure (tested in step 3)
