# Architecture — Personal AI Employee

## System Overview

The AI Employee is a local-first autonomous agent system built on Claude Code and Obsidian. It uses a file-based message bus (the Obsidian vault) to coordinate between perception (watchers), reasoning (Claude + skills), and action (MCP servers + Playwright).

```
EXTERNAL SOURCES
  Gmail | Files | LinkedIn | Facebook | Instagram | Twitter | Odoo
        |
        v
PERCEPTION LAYER (Python Watcher Scripts)
  filesystem_watcher.py | gmail_watcher.py | approval_watcher.py
        |
        v
OBSIDIAN VAULT (Local Markdown — the message bus)
  /Inbox → /Needs_Action → /In_Progress → /Done
  /Pending_Approval → /Approved | /Rejected
  /Logs | /Briefings | /Accounting | /Plans
  Dashboard.md | Company_Handbook.md | Business_Goals.md
        |
        v
REASONING LAYER (Claude Code + 20 Agent Skills)
  reasoning-loop | vault-triage | inbox-processor | ceo-briefing
  business-audit | ralph-wiggum-loop | social-media-manager
  cloud-deployment | vault-sync | work-zone-manager | platinum-demo
        |
        v
ACTION LAYER (MCP Servers + Playwright Automation)
  Email MCP | Odoo MCP | Social Media MCP
  LinkedIn Poster | Facebook/IG Poster | Twitter Poster
        |
        v
HUMAN-IN-THE-LOOP (HITL Approval Workflow)
  /Pending_Approval → Human Review → /Approved or /Rejected
        |
        v
INFRASTRUCTURE (Cross-cutting concerns)
  audit_logger.py | error_recovery.py | watchdog_monitor.py | scheduler.py
  vault_sync.py | claim_manager.py | security_check.py | deploy_config.py
  cloud_agent.py | local_agent.py | odoo_backup.py
```

## Data Flow

### Happy Path: Email → Invoice → Payment
1. `gmail_watcher.py` detects email with "invoice" keyword
2. Creates `EMAIL_*.md` in `/Needs_Action/` (priority: high)
3. Claude triages with `vault-triage` skill → detects financial content
4. Creates `ACCOUNTING_create_invoice_*.md` in `/Pending_Approval/`
5. Human reviews in Obsidian → moves to `/Approved/`
6. `approval_watcher.py` detects approval → logs it
7. Odoo MCP creates invoice (if Odoo configured)
8. File moves to `/Done/` with timestamps

### Happy Path: Cross-Platform Social Post
1. Claude uses `social-media-manager` skill
2. Calls `cross_post` MCP tool → creates 4 draft files in `/Pending_Approval/`
3. Human reviews each platform's version
4. Moves approved ones to `/Approved/`
5. `scheduler.py` triggers posters every 30 min
6. Each poster reads its `{PLATFORM}_*.md`, posts via Playwright
7. Screenshot proof saved, file moved to `/Done/`

## Component Map

### Scripts (`scripts/`)

| Script | Role | Runs As |
|--------|------|---------|
| `base_watcher.py` | Abstract base class for watchers | Imported |
| `filesystem_watcher.py` | Monitors `/Inbox/` for new files | Long-running |
| `gmail_watcher.py` | Polls Gmail API for unread emails | Scheduled (2 min) |
| `approval_watcher.py` | Monitors `/Approved/` folder | Long-running / Scheduled |
| `linkedin_poster.py` | Posts to LinkedIn via Playwright | Scheduled (30 min) |
| `facebook_poster.py` | Posts to Facebook/Instagram via Playwright | Scheduled (30 min) |
| `twitter_poster.py` | Posts to Twitter/X via Playwright | Scheduled (30 min) |
| `social_media_summarizer.py` | Generates social media reports | Scheduled (weekly) |
| `ceo_briefing.py` | Generates comprehensive CEO briefing | Scheduled (weekly) |
| `ralph_loop.py` | Autonomous task completion loop | On-demand |
| `scheduler.py` | Orchestrates all scheduled tasks | Long-running |
| `audit_logger.py` | JSON audit logging module | Imported |
| `error_recovery.py` | Retry, backoff, health tracking | Imported |
| `watchdog_monitor.py` | Process health monitoring | Long-running |

### MCP Servers (`mcp_servers/`)

| Server | Tools | Registered In |
|--------|-------|--------------|
| `email_server.py` | `send_email`, `draft_email`, `list_emails` | `.claude/settings.json` |
| `odoo_server.py` | `odoo_create_invoice`, `odoo_record_payment`, `odoo_list_invoices`, `odoo_get_account_balance`, `odoo_get_profit_loss`, `odoo_health_check` | `.claude/settings.json` |
| `social_media_server.py` | `create_social_post_draft`, `list_pending_social_posts`, `get_social_post_status`, `cross_post` | `.claude/settings.json` |

### Agent Skills (`.agents/skills/`)

| Tier | Skills |
|------|--------|
| Bronze (4) | `vault-triage`, `dashboard-updater`, `inbox-processor`, `playwright-browser` |
| Silver (4) | `gmail-watcher`, `linkedin-poster`, `hitl-approval`, `reasoning-loop` |
| Gold (8) | `odoo-accounting`, `facebook-poster`, `instagram-poster`, `twitter-poster`, `social-media-manager`, `ceo-briefing`, `business-audit`, `ralph-wiggum-loop` |
| Platinum (4) | `cloud-deployment`, `vault-sync`, `work-zone-manager`, `platinum-demo` |

## Cloud/Local Topology (Platinum)

```
CLOUD VM (24/7 — Oracle Cloud / Docker)           LOCAL MACHINE (on-demand)
┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐
│  scheduler.py --mode cloud          │    │  scheduler.py --mode local          │
│                                     │    │                                     │
│  gmail_watcher.py (poll Gmail)      │    │  approval_watcher.py                │
│  cloud_agent.py (triage + draft)    │    │  local_agent.py (execute actions)   │
│  ceo_briefing.py                    │    │  linkedin_poster.py                 │
│  social_media_summarizer.py         │    │  facebook_poster.py                 │
│  vault_sync.py (push/pull)          │    │  twitter_poster.py                  │
│                                     │    │  odoo_server.py (MCP)               │
│  NEVER sends/posts/pays             │    │  email_server.py (MCP)              │
│  Only creates drafts + approvals    │    │  vault_sync.py (push/pull)          │
│                                     │    │                                     │
│  /Pending_Approval/ ← writes here   │    │  /Approved/ → executes from here    │
│  /Updates/ ← dashboard signals      │    │  Dashboard.md ← single writer       │
└──────────────┬──────────────────────┘    └──────────────┬──────────────────────┘
               │                                          │
               └────────── Git Vault Sync ────────────────┘
                    (every 60s, separate repo)
                    security_check.py pre-push
                    claim_manager.py prevents double-work
```

### Data Flow: Email → Cloud Triage → Vault Sync → Local Approval → Action

```
1. Gmail → gmail_watcher.py → EMAIL_*.md in /Needs_Action/
2. cloud_agent.py claims → /In_Progress/cloud/ → triages
3. Draft reply → /Pending_Approval/email/ → original → /Done/
4. vault_sync.py pushes (cloud) → pulls (local)
5. Human reviews in Obsidian → moves to /Approved/
6. local_agent.py claims → /In_Progress/local/ → executes
7. Email sent via MCP → file → /Done/ → audit logged
8. vault_sync.py pushes (local) → pulls (cloud)
```

### Security Boundaries

| Boundary | Enforcement |
|----------|-------------|
| Cloud never sends | cloud_agent.py only writes drafts to /Pending_Approval/ |
| Secrets never synced | AI_Employee_Vault/.gitignore + security_check.py pre-push |
| No double-work | claim_manager.py with /In_Progress/<agent_id>/ |
| Dashboard single-writer | Only local writes Dashboard.md; cloud writes to /Updates/ |
| HTTPS for cloud Odoo | Caddy reverse proxy with auto-TLS |
| Credentials isolated | deploy/*.env excluded from Git, /etc/ai-employee/.env on server |

## Key Design Decisions

### File-Based Message Bus
All communication flows through markdown files in the Obsidian vault. This provides:
- **Visibility**: Human can see everything in Obsidian
- **Auditability**: Every state change is a file operation
- **Durability**: Files persist across crashes
- **Simplicity**: No database, no message queue

### HITL by Default
All external actions require human approval. Files move through:
`/Pending_Approval/` → human moves to → `/Approved/` or `/Rejected/`

### Playwright Over APIs
LinkedIn, Facebook, Instagram, and Twitter don't provide easy posting APIs. Playwright browser automation with persistent sessions provides reliable access without OAuth complexity.

### Graceful Degradation
Every external service (Odoo, Gmail, social platforms) can be unavailable. The system:
- Reports clear status in the dashboard
- Queues actions for retry (files stay in `/Approved/`)
- Generates partial briefings with "unavailable" sections
- Never crashes on a missing service

### Audit Logging (Dual Format)
- **Markdown logs** (`/Logs/YYYY-MM-DD.md`): Human-readable, viewable in Obsidian
- **JSON logs** (`/Logs/YYYY-MM-DD.json`): Machine-readable, queryable by scripts
