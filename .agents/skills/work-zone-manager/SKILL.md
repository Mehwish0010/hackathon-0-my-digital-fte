# Work-Zone Manager Skill

## Description
Manages cloud vs local work-zone routing, ensuring each agent only runs its designated services and tasks are properly distributed.

## Trigger Phrases
- "check deployment mode"
- "which zone am I"
- "configure work zones"
- "switch deployment mode"

## Instructions

### Check Current Mode
1. Run: `python scripts/deploy_config.py`
2. Output shows: mode, agent_id, active services, sync interval

### Zone Rules

**Cloud Zone** (DEPLOYMENT_MODE=cloud):
- Runs: gmail_watcher, social_media_server (draft-only), ceo_briefing, social_media_summarizer, vault_sync, cloud_agent
- NEVER executes: send email, post to social, process payments
- Creates drafts in `/Pending_Approval/`
- Uses `scripts/cloud_agent.py` for email triage

**Local Zone** (DEPLOYMENT_MODE=local):
- Runs: approval_watcher, linkedin_poster, facebook_poster, twitter_poster, odoo_server, email_server, vault_sync, local_agent
- Executes approved actions (send, post, pay)
- Merges cloud signals into Dashboard.md (single-writer)
- Uses `scripts/local_agent.py` for execution

**Hybrid Mode** (DEPLOYMENT_MODE=hybrid):
- Runs everything on a single machine
- Default for development/testing
- Backward-compatible with Silver/Gold tier behavior

### Switching Modes
1. Set env var: `DEPLOYMENT_MODE=cloud|local|hybrid`
2. Or use CLI: `python scripts/scheduler.py --mode cloud`
3. Feature flags: `ENABLE_GMAIL_WATCHER=false` to disable individual services

### Dashboard Single-Writer Rule
- Only local agent writes `Dashboard.md` directly
- Cloud agent writes to `/Updates/dashboard_signal_*.md`
- Local agent merges signals on sync pull

## Files
- `scripts/deploy_config.py` — Zone configuration
- `scripts/cloud_agent.py` — Cloud zone logic
- `scripts/local_agent.py` — Local zone logic
- `scripts/scheduler.py` — Zone-aware scheduler (--mode flag)
