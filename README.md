# Personal AI Employee - Hackathon 0

> Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

A Digital FTE (Full-Time Equivalent) built with Claude Code and Obsidian that proactively manages personal and business affairs using watchers, reasoning, and MCP-based actions.

## Tier Progress

| Tier | Status | Requirements |
|------|--------|-------------|
| **Bronze** | COMPLETED | Vault structure, file watcher, 4 agent skills |
| **Silver** | COMPLETED | Gmail watcher, LinkedIn posting, Email MCP, HITL, scheduling, reasoning loop |
| **Gold** | COMPLETED | Odoo, social media (FB/IG/Twitter), CEO briefing, Ralph Wiggum loop, audit logging, error recovery |
| **Platinum** | COMPLETED | Cloud 24/7, work-zone specialization, synced vault, security boundaries |

---

## Architecture

```
EXTERNAL SOURCES (Files, Gmail, Facebook, Instagram, Twitter, LinkedIn, Odoo)
        |
        v
PERCEPTION LAYER (Python Watcher Scripts)
  filesystem_watcher | gmail_watcher | approval_watcher
        |
        v
OBSIDIAN VAULT (Local Markdown — Obsidian)
  /Inbox -> /Needs_Action -> /In_Progress -> /Done
  /Pending_Approval -> /Approved | /Rejected
  /Plans | /Briefings | /Accounting | /Logs
  Dashboard.md | Company_Handbook.md | Business_Goals.md
        |
        v
REASONING LAYER (Claude Code + 20 Agent Skills)
  reasoning-loop: Read -> Think -> Plan -> Act -> Log
  ralph-wiggum-loop: Autonomous multi-step completion
  vault-triage | inbox-processor | dashboard-updater | business-audit
  cloud-deployment | vault-sync | work-zone-manager | platinum-demo
        |
        v
ACTION LAYER (3 MCP Servers + Playwright)
  Email MCP: send_email, draft_email, list_emails
  Odoo MCP: create_invoice, record_payment, get_balance, profit_loss
  Social MCP: create_social_post_draft, cross_post, list_pending
  Playwright: LinkedIn, Facebook, Instagram, Twitter auto-posting
        |
        v
HUMAN-IN-THE-LOOP (hitl-approval skill)
  /Pending_Approval -> Human Review -> /Approved or /Rejected
        |
        v
INFRASTRUCTURE (Gold + Platinum)
  audit_logger (JSON) | error_recovery (retry + degradation)
  watchdog_monitor (process health) | scheduler (cron-like)
  vault_sync (Git) | claim_manager | security_check
  cloud_agent | local_agent | deploy_config
```

## Project Structure

```
hackathon-0-final/
├── AI_Employee_Vault/          # Obsidian vault
│   ├── Inbox/                  # Drop files here for processing
│   ├── Needs_Action/           # Watcher output, pending triage
│   ├── In_Progress/            # Currently being worked on / Ralph Wiggum state
│   ├── Done/                   # Completed items
│   ├── Plans/                  # Claude-generated Plan.md files
│   ├── Logs/                   # Activity logs (.md) + Audit logs (.json)
│   ├── Pending_Approval/       # Items needing human approval
│   ├── Approved/               # Human-approved actions
│   ├── Rejected/               # Human-rejected actions
│   ├── Briefings/              # Daily/weekly/CEO briefings
│   ├── Accounting/             # Odoo financial tracking
│   ├── Dashboard.md            # Real-time status overview
│   ├── Company_Handbook.md     # Rules of engagement
│   └── Business_Goals.md       # Objectives and metrics
├── scripts/
│   ├── base_watcher.py         # Base class for watchers (Bronze)
│   ├── filesystem_watcher.py   # File system watcher (Bronze)
│   ├── gmail_watcher.py        # Gmail API watcher (Silver)
│   ├── linkedin_poster.py      # LinkedIn auto-poster (Silver)
│   ├── approval_watcher.py     # Approval watcher (Silver+Gold)
│   ├── scheduler.py            # Task scheduler (Silver+Gold)
│   ├── audit_logger.py         # JSON audit logging module (Gold)
│   ├── error_recovery.py       # Retry + graceful degradation (Gold)
│   ├── watchdog_monitor.py     # Process health monitor (Gold)
│   ├── facebook_poster.py      # Facebook/Instagram poster (Gold)
│   ├── twitter_poster.py       # Twitter/X poster (Gold)
│   ├── social_media_summarizer.py  # Social media metrics (Gold)
│   ├── ceo_briefing.py         # Weekly CEO briefing generator (Gold)
│   ├── ralph_loop.py           # Ralph Wiggum autonomous loop (Gold)
│   ├── deploy_config.py        # Deployment mode configuration (Platinum)
│   ├── vault_sync.py           # Git-based vault synchronization (Platinum)
│   ├── claim_manager.py        # Claim-by-move task ownership (Platinum)
│   ├── cloud_agent.py          # Cloud-zone reasoning/scheduling (Platinum)
│   ├── local_agent.py          # Local-zone reasoning/execution (Platinum)
│   ├── security_check.py       # Pre-sync secrets scanner (Platinum)
│   ├── odoo_backup.py          # Odoo automated backup (Platinum)
│   ├── platinum_demo.py        # End-to-end Platinum demo (Platinum)
│   └── cloud_setup.sh          # Cloud VM setup script (Platinum)
├── mcp_servers/
│   ├── email_server.py         # Email MCP server (Silver)
│   ├── odoo_server.py          # Odoo accounting MCP server (Gold)
│   └── social_media_server.py  # Social media MCP server (Gold)
├── .agents/skills/             # 20 Agent Skills
│   ├── vault-triage/           # Triage /Needs_Action items (Bronze)
│   ├── dashboard-updater/      # Refresh Dashboard.md (Bronze)
│   ├── inbox-processor/        # Full processing cycle (Bronze)
│   ├── playwright-browser/     # Browser automation (Bronze)
│   ├── gmail-watcher/          # Gmail monitoring (Silver)
│   ├── linkedin-poster/        # LinkedIn posting (Silver)
│   ├── hitl-approval/          # Approval workflow (Silver)
│   ├── reasoning-loop/         # Plan + execute loop (Silver)
│   ├── odoo-accounting/        # Odoo invoices/payments (Gold)
│   ├── facebook-poster/        # Facebook posting (Gold)
│   ├── instagram-poster/       # Instagram posting (Gold)
│   ├── twitter-poster/         # Twitter posting (Gold)
│   ├── social-media-manager/   # Cross-platform strategy (Gold)
│   ├── ceo-briefing/           # CEO briefing generation (Gold)
│   ├── business-audit/         # Cross-domain audit (Gold)
│   ├── ralph-wiggum-loop/      # Autonomous completion (Gold)
│   ├── cloud-deployment/       # Cloud setup + monitoring (Platinum)
│   ├── vault-sync/             # Git sync + claim-by-move (Platinum)
│   ├── work-zone-manager/      # Cloud/local routing (Platinum)
│   └── platinum-demo/          # End-to-end demo (Platinum)
├── deploy/
│   ├── Dockerfile.cloud        # Cloud container image (Platinum)
│   ├── docker-compose.yml      # Full stack: Odoo + cloud agent (Platinum)
│   ├── Caddyfile               # HTTPS reverse proxy (Platinum)
│   ├── ai-employee-cloud.service  # Systemd cloud service (Platinum)
│   └── ai-employee-local.service  # Systemd local service (Platinum)
├── .claude/settings.json       # MCP server configuration (3 servers)
├── .env.example                # Environment template
├── .gitignore
├── pyproject.toml
├── ARCHITECTURE.md             # Detailed architecture docs (Gold+Platinum)
├── LESSONS_LEARNED.md          # Architecture decisions + lessons (Gold)
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js v24+ LTS
- Claude Code (active subscription)
- Obsidian v1.10.6+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Google Cloud project with Gmail API enabled (Silver+)
- Odoo Community 19+ (Gold tier — optional, degrades gracefully)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/Mehwish0010/hackathon-0-my-digital-fte.git
cd hackathon-0-my-digital-fte

# 2. Install Python dependencies
.venv/Scripts/python.exe -m ensurepip
.venv/Scripts/python.exe -m pip install google-auth-oauthlib google-api-python-client playwright mcp schedule watchdog python-dotenv

# 3. Install Playwright Chromium browser
.venv/Scripts/python.exe -m playwright install chromium

# 4. Copy environment file and edit with your values
cp .env.example .env

# 5. Open the vault in Obsidian
# Open Obsidian → Open folder as vault → select AI_Employee_Vault/
```

### Gmail API Setup (Silver+)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project or select existing
3. Enable the **Gmail API** under APIs & Services
4. Create **OAuth 2.0 credentials** (Desktop application)
5. Download the client secret JSON to the project root
6. Add your email as a **test user** under OAuth consent screen → Audience
7. First run of `gmail_watcher.py` opens browser for OAuth consent → saves `token.json`

### Social Media Setup (Silver+Gold)

```bash
# LinkedIn (Silver) — one-time login
.venv/Scripts/python.exe scripts/linkedin_poster.py --login

# Facebook/Instagram (Gold) — one-time login
.venv/Scripts/python.exe scripts/facebook_poster.py --login

# Twitter/X (Gold) — one-time login
.venv/Scripts/python.exe scripts/twitter_poster.py --login
```

Sessions saved to `linkedin_session/`, `facebook_session/`, `twitter_session/` (all gitignored).

### Odoo Setup (Gold — Optional)

1. Install [Odoo Community 19+](https://www.odoo.com/page/download)
2. Start Odoo locally: `python odoo-bin -d mydb`
3. Edit `.env` with Odoo connection details:
   ```
   ODOO_URL=http://localhost:8069
   ODOO_DB=mydb
   ODOO_USERNAME=admin
   ODOO_PASSWORD=admin
   ```
4. The Odoo MCP server degrades gracefully if Odoo is unavailable.

---

## Agent Skills Reference (16 Total)

All AI functionality is implemented as Agent Skills. Claude Code uses these to process tasks autonomously.

### Bronze Skills (4)
| Skill | Purpose | How to Trigger |
|-------|---------|----------------|
| `vault-triage` | Process /Needs_Action items, classify priority, route to Done or Approval | "triage actions", "process needs action" |
| `dashboard-updater` | Scan vault folders, count items, refresh Dashboard.md | "update dashboard", "status update" |
| `inbox-processor` | Full end-to-end cycle: triage → execute → log → update dashboard | "process everything", "run cycle" |
| `playwright-browser` | Browser automation: screenshots, scraping, form filling | "take screenshot", "scrape website" |

### Silver Skills (4)
| Skill | Purpose | How to Trigger |
|-------|---------|----------------|
| `gmail-watcher` | Monitor Gmail via API, create action files from emails | "check email", "watch Gmail" |
| `linkedin-poster` | Post approved drafts to LinkedIn via Playwright | "post to LinkedIn", "publish post" |
| `hitl-approval` | Create approval requests, route sensitive actions for human review | "approve", "review pending", "flag for approval" |
| `reasoning-loop` | Read → Think → Plan → Act → Log structured reasoning | "create a plan", "reason about this" |

### Gold Skills (8)
| Skill | Purpose | How to Trigger |
|-------|---------|----------------|
| `odoo-accounting` | Create invoices, record payments, run P&L reports via Odoo MCP | "create invoice", "record payment", "accounting report" |
| `facebook-poster` | Post to Facebook via Playwright with proof screenshots | "post to Facebook", "share on Facebook" |
| `instagram-poster` | Post to Instagram via mobile viewport Playwright automation | "post to Instagram", "share on Instagram" |
| `twitter-poster` | Post to Twitter/X with 280-char limit enforcement | "tweet", "post to Twitter" |
| `social-media-manager` | Cross-platform content strategy, adapts content per platform | "cross-post", "social media strategy" |
| `ceo-briefing` | Generate weekly CEO briefing from all data sources | "generate briefing", "CEO report" |
| `business-audit` | Full cross-domain audit: financials + tasks + social + compliance | "audit business", "review performance" |
| `ralph-wiggum-loop` | Autonomous task completion with file-movement completion detection | "run autonomously", "ralph wiggum" |

### How Skills Work
Skills are markdown files in `.agents/skills/[name]/SKILL.md`. When you say a trigger phrase in Claude Code, it loads the skill and follows the step-by-step instructions. Skills chain together — for example, `inbox-processor` calls `vault-triage`, which may call `hitl-approval`, which creates files that `approval_watcher.py` processes.

---

## Bronze Tier — Local Vault + File Watcher

### What It Does
- Obsidian vault with structured folders for complete task lifecycle
- File system watcher monitors `/Inbox/` for new files
- Automatic priority classification (high/medium/low based on keywords)
- Action files created in `/Needs_Action/` for Claude to triage
- 4 Agent Skills for triage, dashboard, processing, and browser automation

### Bronze Checklist
- [x] Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- [x] One working Watcher script (file system monitoring)
- [x] Claude Code reading from and writing to the vault
- [x] Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- [x] AI functionality implemented as Agent Skills (4 skills)

### How to Test Bronze

**Test 1: File Watcher**
```bash
# Terminal 1 — Start the watcher
.venv/Scripts/python.exe scripts/filesystem_watcher.py

# Terminal 2 — Drop a test file
echo "test urgent invoice for Client A" > AI_Employee_Vault/Inbox/urgent_invoice_request.txt
```
Expected: Watcher detects file → creates `FILE_*.md` in `/Needs_Action/` with priority classification.

**Test 2: Vault Triage (Agent Skill)**
In Claude Code, say: `triage the action items in Needs_Action`
Expected: Claude uses `vault-triage` skill → classifies by priority → moves simple items to `/Done/` → flags complex items for approval.

**Test 3: Dashboard Update (Agent Skill)**
In Claude Code, say: `update the dashboard`
Expected: Claude uses `dashboard-updater` skill → counts items → updates `Dashboard.md`.

**Test 4: Full Processing Cycle (Agent Skill)**
In Claude Code, say: `process everything in the vault`
Expected: Claude uses `inbox-processor` skill → reads Company_Handbook → triages → executes → updates dashboard → generates summary.

---

## Silver Tier — Real Integrations + HITL + Reasoning

### What It Does
- **Gmail Watcher**: Monitors Gmail for unread emails, creates action files with metadata
- **LinkedIn Auto-Poster**: Posts approved drafts via Playwright browser automation
- **Email MCP Server**: `send_email`, `draft_email`, `list_emails` tools for Claude
- **Approval Watcher**: Monitors `/Approved/`, triggers corresponding actions
- **HITL Workflow**: Sensitive actions routed to `/Pending_Approval/` for human review
- **Reasoning Loop**: Claude creates structured Plan.md files, executes step-by-step
- **Scheduler**: Gmail (2min), dashboard (15min), approvals (5min), daily briefing (8AM)

### Silver Checklist
- [x] Gmail Watcher (Gmail API + OAuth)
- [x] LinkedIn auto-posting via Playwright
- [x] Email MCP server (send/draft/list)
- [x] Human-in-the-loop approval workflow
- [x] Approval Watcher (monitors /Approved)
- [x] Scheduled tasks via `schedule` library
- [x] Claude reasoning loop with Plan.md files
- [x] 4 new Agent Skills (gmail-watcher, linkedin-poster, hitl-approval, reasoning-loop)

### Running Silver Components

```bash
# Gmail Watcher
.venv/Scripts/python.exe scripts/gmail_watcher.py                # Continuous
.venv/Scripts/python.exe scripts/gmail_watcher.py --once         # One-time check
.venv/Scripts/python.exe scripts/gmail_watcher.py --dry-run      # Preview only

# LinkedIn Poster
.venv/Scripts/python.exe scripts/linkedin_poster.py --login      # First-time login
.venv/Scripts/python.exe scripts/linkedin_poster.py              # Post approved drafts

# Approval Watcher
.venv/Scripts/python.exe scripts/approval_watcher.py             # Continuous
.venv/Scripts/python.exe scripts/approval_watcher.py --once      # One-time check

# Scheduler
.venv/Scripts/python.exe scripts/scheduler.py                    # Start scheduler
.venv/Scripts/python.exe scripts/scheduler.py --create-bat       # Windows Task Scheduler
```

### How to Test Silver

**Test 1: Gmail Watcher**
```bash
.venv/Scripts/python.exe scripts/gmail_watcher.py --once
```
Expected: OAuth flow (first run) → fetches unread emails → creates `EMAIL_*.md` in `/Needs_Action/`.

**Test 2: Triage Gmail Emails (Agent Skill)**
Say in Claude Code: `triage the action items`
Expected: Classifies emails → archives newsletters to `/Done/` → flags invoices for approval.

**Test 3: HITL Approval Workflow**
```bash
# 1. Claude creates approval file (or say: "flag this for approval")
# 2. Review in Obsidian at /Pending_Approval/
# 3. Move file to /Approved/ or /Rejected/
# 4. Run:
.venv/Scripts/python.exe scripts/approval_watcher.py --once
```

**Test 4: LinkedIn Auto-Post**
```bash
.venv/Scripts/python.exe scripts/linkedin_poster.py --login   # First time
# Create LINKEDIN_*.md in /Approved/, then:
.venv/Scripts/python.exe scripts/linkedin_poster.py
```
Expected: Posts content → saves proof screenshot → moves to `/Done/`.

**Test 5: Email MCP Tools**
In Claude Code: `draft an email to test@example.com about the project status`
Expected: Claude uses `draft_email` MCP tool → creates Gmail draft.

**Test 6: Reasoning Loop (Agent Skill)**
Say: `create a plan for processing all pending items`
Expected: Creates `Plan.md` in `/Plans/` with steps → executes → updates progress.

---

## Gold Tier — Autonomous Employee

### What It Does
- **Odoo Accounting MCP**: Create invoices, record payments, run P&L reports (with HITL approval)
- **Facebook/Instagram Poster**: Auto-post via Playwright with proof screenshots
- **Twitter/X Poster**: Auto-post with 280-char limit enforcement
- **Social Media MCP**: Cross-platform draft creation and content adaptation
- **Social Media Summarizer**: Scrapes engagement metrics for CEO briefing
- **CEO Briefing Generator**: Weekly cross-domain report (vault + Odoo + social + audit)
- **Ralph Wiggum Loop**: Autonomous multi-step task completion with retry logic
- **JSON Audit Logger**: Structured audit logs with 90-day retention
- **Error Recovery**: Exponential backoff retry, service health tracking, graceful degradation
- **Watchdog Monitor**: Process health monitoring with auto-restart
- **8 new Agent Skills** (16 total across all tiers)

### Gold Checklist
- [x] Odoo Community accounting integration via MCP server (JSON-RPC/XML-RPC)
- [x] Facebook + Instagram integration via Playwright
- [x] Twitter (X) integration via Playwright
- [x] Multiple MCP servers (3: Email, Odoo, Social Media)
- [x] Weekly CEO Briefing with cross-domain data
- [x] Business Audit skill (cross-domain integration)
- [x] Ralph Wiggum loop (file-movement completion detection)
- [x] Error recovery + graceful degradation
- [x] Comprehensive JSON audit logging (90-day retention)
- [x] Watchdog process monitor
- [x] 8 new Agent Skills (16 total)
- [x] Architecture documentation (ARCHITECTURE.md)
- [x] Lessons learned documentation (LESSONS_LEARNED.md)

### Running Gold Components

```bash
# Facebook/Instagram Poster
.venv/Scripts/python.exe scripts/facebook_poster.py --login      # First-time FB/IG login
.venv/Scripts/python.exe scripts/facebook_poster.py              # Post approved FB/IG drafts
.venv/Scripts/python.exe scripts/facebook_poster.py --dry-run    # Preview only

# Twitter/X Poster
.venv/Scripts/python.exe scripts/twitter_poster.py --login       # First-time Twitter login
.venv/Scripts/python.exe scripts/twitter_poster.py               # Post approved tweets
.venv/Scripts/python.exe scripts/twitter_poster.py --dry-run     # Preview only

# CEO Briefing (manual run)
.venv/Scripts/python.exe scripts/ceo_briefing.py                 # Generate briefing now

# Social Media Summary
.venv/Scripts/python.exe scripts/social_media_summarizer.py      # Generate summary

# Ralph Wiggum Loop
.venv/Scripts/python.exe scripts/ralph_loop.py "Process all Needs_Action items and update dashboard" --max-iterations 5

# Watchdog Monitor
.venv/Scripts/python.exe scripts/watchdog_monitor.py             # Monitor processes

# Full Scheduler (includes ALL Silver + Gold jobs)
.venv/Scripts/python.exe scripts/scheduler.py
```

### Scheduler — All Jobs

| Job | Frequency | Tier |
|-----|-----------|------|
| Gmail check | Every 2 minutes | Silver |
| Dashboard update | Every 15 minutes | Silver |
| Approval check | Every 5 minutes | Silver |
| Daily briefing | 8:00 AM daily | Silver |
| Social media post check | Every 30 minutes | Gold |
| Odoo health check | Every 15 minutes | Gold |
| Social media summary | Sunday 8:00 PM | Gold |
| CEO briefing | Sunday 9:00 PM | Gold |
| Audit log retention sweep | Midnight daily | Gold |

### MCP Servers (3 Total)

All registered in `.claude/settings.json`, automatically available as Claude Code tools.

**Email MCP** (`mcp_servers/email_server.py`)
- `send_email(to, subject, body)` — Send email via Gmail
- `draft_email(to, subject, body)` — Create Gmail draft
- `list_emails(query, max_results)` — Search Gmail

**Odoo MCP** (`mcp_servers/odoo_server.py`)
- `odoo_create_invoice(partner, lines, due_date)` — Create draft invoice (requires approval)
- `odoo_record_payment(invoice_id, amount, method)` — Record payment (requires approval)
- `odoo_list_invoices(status, date_range)` — Query invoices
- `odoo_get_account_balance(account_type)` — Account balances
- `odoo_get_profit_loss(date_from, date_to)` — P&L report
- `odoo_health_check()` — Check Odoo connectivity

**Social Media MCP** (`mcp_servers/social_media_server.py`)
- `create_social_post_draft(platform, content, hashtags)` — Create draft in /Pending_Approval/
- `cross_post(content, platforms, hashtags)` — Draft for multiple platforms at once
- `list_pending_social_posts()` — List pending social media posts
- `get_social_post_status(filename)` — Check post status

### How to Test Gold

**Test 1: Odoo MCP (without Odoo running)**
In Claude Code: `check if Odoo is available`
Expected: Claude calls `odoo_health_check()` → returns graceful "Odoo not available" message.

**Test 2: Odoo MCP (with Odoo running)**
In Claude Code: `create an invoice for Client A for $500`
Expected: Claude calls `odoo_create_invoice()` → creates approval file in `/Pending_Approval/ACCOUNTING_*.md` → waits for human approval.

**Test 3: Social Media MCP — Cross-Post**
In Claude Code: `create a social media post about AI automation for all platforms`
Expected: Claude uses `cross_post()` → creates `FACEBOOK_*.md`, `INSTAGRAM_*.md`, `TWITTER_*.md`, `LINKEDIN_*.md` in `/Pending_Approval/` (Twitter content truncated to 280 chars).

**Test 4: Facebook/Instagram Poster**
```bash
.venv/Scripts/python.exe scripts/facebook_poster.py --login   # First time
# Move a FACEBOOK_*.md to /Approved/, then:
.venv/Scripts/python.exe scripts/facebook_poster.py
```

**Test 5: Twitter Poster**
```bash
.venv/Scripts/python.exe scripts/twitter_poster.py --login   # First time
# Move a TWITTER_*.md to /Approved/, then:
.venv/Scripts/python.exe scripts/twitter_poster.py
```

**Test 6: CEO Briefing**
```bash
.venv/Scripts/python.exe scripts/ceo_briefing.py
```
Expected: Generates `/Briefings/CEO_Briefing_*.md` with Executive Summary, Revenue, Tasks, Bottlenecks, Social Media, Suggestions, Error Summary. Falls back gracefully if Odoo/social data unavailable.

**Test 7: Business Audit (Agent Skill)**
In Claude Code: `audit the business — review everything`
Expected: Claude uses `business-audit` skill → reviews vault activity, financials, communications, social performance, compliance.

**Test 8: Ralph Wiggum Loop**
```bash
# Simple task — should complete in 1-2 iterations
.venv/Scripts/python.exe scripts/ralph_loop.py "Triage all items in Needs_Action and update the dashboard" --max-iterations 5
```
Expected: Creates state file in `/In_Progress/` → invokes Claude → checks if file moved to `/Done/` → completes or retries with context.

**Test 9: Audit Logger**
In Claude Code: `check the audit logs for today`
Expected: Reads `/Logs/YYYY-MM-DD.json` — each line is a JSON object with `timestamp`, `action_type`, `actor`, `target`, `parameters`, `approval_status`, `result`.

**Test 10: Error Recovery**
Simulate: Stop Odoo → run scheduler → Odoo health check fails
Expected: Failure logged, service marked as "degraded" in `service_health.json`, dashboard shows "Unavailable". Retry on next check.

### Gold Workflow End-to-End

```
1. Scheduler runs all jobs automatically
   → Gmail checked every 2 min, social media every 30 min

2. Gmail Watcher detects client email about invoice
   → Creates EMAIL_*.md in /Needs_Action/ (priority: high)

3. Claude triages (vault-triage skill)
   → Detects "invoice" → creates Plan.md (reasoning-loop)
   → Step 1: Create Odoo invoice via odoo_create_invoice MCP
   → Step 2: Draft reply email via draft_email MCP
   → Step 3: Post LinkedIn update about new client
   → All sensitive steps create approval files

4. Human reviews approvals in Obsidian
   → Moves ACCOUNTING_*.md to /Approved/ (invoice approved)
   → Moves EMAIL_*.md to /Approved/ (reply approved)
   → Moves LINKEDIN_*.md to /Approved/ (post approved)

5. Approval Watcher + Poster scripts execute
   → Odoo invoice created, email sent, LinkedIn posted
   → Proof screenshots saved, all actions audit-logged (JSON)

6. Sunday: CEO Briefing auto-generated
   → Revenue from Odoo, tasks from vault, social metrics, audit analysis
   → Saved to /Briefings/CEO_Briefing_*.md

7. Ralph Wiggum loop handles complex multi-step tasks
   → Autonomous completion with file-movement detection
   → Max iterations safeguard prevents infinite loops
```

---

## Security

- Credentials: `.env`, `token.json`, `client_secret_*.json` all gitignored
- Social media sessions: `linkedin_session/`, `facebook_session/`, `twitter_session/` all gitignored
- Sensitive actions (payments, invoices, external comms) always require HITL approval
- JSON audit logs: every action logged with actor, target, approval status, result
- 90-day audit log retention (automatic sweep at midnight)
- Error recovery: exponential backoff prevents API hammering
- Graceful degradation: services queue when unavailable, never lose data
- Local-first: all data stays on your machine
- See `Company_Handbook.md` for full security rules

---

## Platinum Tier — Cloud 24/7 + Work Zones

### What It Does
- **Cloud/Local Work Zones**: Cloud agent handles email triage, drafts, briefings (never sends). Local agent executes approved actions.
- **Git-Based Vault Sync**: Vault syncs every 60s between cloud and local via separate Git repo
- **Claim-by-Move**: Prevents double-work between agents via `/In_Progress/<agent_id>/` directories
- **Security Boundaries**: Pre-sync secrets scanner blocks API keys, passwords, tokens from being pushed
- **Cloud Deployment**: Docker + systemd support for Oracle Cloud Free Tier / any Linux VM
- **Cloud Odoo**: Docker Compose with PostgreSQL, auto-HTTPS via Caddy reverse proxy
- **Odoo Backup**: Automated daily backups with 30-day retention
- **Platinum Demo**: End-to-end test proving the minimum gate

### Platinum Checklist
- [x] Deployment configuration (cloud/local/hybrid modes)
- [x] Git-based vault sync with conflict resolution
- [x] Claim-by-move task ownership (prevents double-work)
- [x] Vault security scanner (blocks secrets from sync)
- [x] Cloud agent (draft-only, never sends)
- [x] Local agent (executes approved actions)
- [x] Scheduler with `--mode cloud|local|hybrid` flag
- [x] Docker deployment (Dockerfile.cloud + docker-compose.yml)
- [x] Systemd services (cloud + local)
- [x] Cloud setup script (Ubuntu/Oracle Cloud)
- [x] Caddy HTTPS reverse proxy for Odoo
- [x] Odoo HTTPS support + connection retry
- [x] Odoo automated backup with retention
- [x] Platinum end-to-end demo script
- [x] 4 new Agent Skills (20 total)
- [x] Dashboard with deployment/sync status

### Running Platinum Components

```bash
# Deploy config check
python scripts/deploy_config.py

# Vault sync
python scripts/vault_sync.py --vault ./AI_Employee_Vault --init   # Initialize
python scripts/vault_sync.py --vault ./AI_Employee_Vault --once   # Single sync

# Security scan
python scripts/security_check.py --vault ./AI_Employee_Vault

# Cloud agent (draft-only)
python scripts/cloud_agent.py --vault ./AI_Employee_Vault --once

# Local agent (execute approved)
python scripts/local_agent.py --vault ./AI_Employee_Vault --once

# Scheduler with mode
python scripts/scheduler.py --mode cloud    # Cloud zone only
python scripts/scheduler.py --mode local    # Local zone only
python scripts/scheduler.py --mode hybrid   # All jobs (default)

# Platinum demo (dry run)
python scripts/platinum_demo.py --vault ./AI_Employee_Vault

# Docker deployment
cd deploy && docker compose up -d

# Odoo backup
python scripts/odoo_backup.py --vault ./AI_Employee_Vault
```

### Scheduler — All Jobs (Platinum)

| Job | Frequency | Zone | Tier |
|-----|-----------|------|------|
| Vault sync | Every 1 minute | All | Platinum |
| Cloud agent cycle | Every 2 minutes | Cloud | Platinum |
| Local agent cycle | Every 5 minutes | Local | Platinum |
| Gmail check | Every 2 minutes | Cloud | Silver |
| Dashboard update | Every 15 minutes | Local | Silver |
| Approval check | Every 5 minutes | Local | Silver |
| Daily briefing | 8:00 AM daily | Cloud | Silver |
| Social media post check | Every 30 minutes | Local | Gold |
| Odoo health check | Every 15 minutes | Local | Gold |
| Social media summary | Sunday 8:00 PM | Cloud | Gold |
| CEO briefing | Sunday 9:00 PM | Cloud | Gold |
| Audit log retention sweep | Midnight daily | All | Gold |

### Platinum Skills (4 new, 20 total)
| Skill | Purpose | How to Trigger |
|-------|---------|----------------|
| `cloud-deployment` | Cloud VM setup, Docker deployment, monitoring | "deploy to cloud", "cloud setup" |
| `vault-sync` | Git sync, conflict resolution, claim-by-move | "sync vault", "claim task" |
| `work-zone-manager` | Cloud vs local routing, zone ownership | "check deployment mode" |
| `platinum-demo` | End-to-end demo of cloud→local flow | "run platinum demo" |

### How to Test Platinum

**Test 1: Deploy Config**
```bash
python scripts/deploy_config.py
```
Expected: JSON output showing mode, agent_id, active services.

**Test 2: Vault Sync Init**
```bash
python scripts/vault_sync.py --vault ./AI_Employee_Vault --init
```
Expected: Vault initialized as Git repo with .gitignore.

**Test 3: Claim Manager**
```bash
python scripts/claim_manager.py ./AI_Employee_Vault
```
Expected: Lists available and claimed tasks.

**Test 4: Security Check**
```bash
python scripts/security_check.py --vault ./AI_Employee_Vault
```
Expected: "Security check passed" or lists detected issues.

**Test 5: Cloud Agent (Dry Run)**
```bash
python scripts/cloud_agent.py --vault ./AI_Employee_Vault --once
```
Expected: Triages emails in /Needs_Action/, creates drafts in /Pending_Approval/email/.

**Test 6: Local Agent**
```bash
python scripts/local_agent.py --vault ./AI_Employee_Vault --once
```
Expected: Merges cloud signals, processes approved items, checks pending approvals.

**Test 7: Scheduler Modes**
```bash
python scripts/scheduler.py --mode cloud   # Only cloud jobs scheduled
python scripts/scheduler.py --mode local   # Only local jobs scheduled
python scripts/scheduler.py --mode hybrid  # All jobs (backward compat)
```

**Test 8: Platinum Demo (Dry Run)**
```bash
python scripts/platinum_demo.py --vault ./AI_Employee_Vault
```
Expected: 7/7 steps pass — Email → Cloud Draft → Sync → Approve → Execute → Done → Logged.

**Test 9: Docker Build**
```bash
docker build -f deploy/Dockerfile.cloud .
```
Expected: Image builds successfully.

### Platinum Workflow End-to-End

```
1. Cloud VM running scheduler --mode cloud (24/7)
   → Gmail checked every 2 min, briefings generated

2. Email arrives: "Send invoice for Q1 services"
   → gmail_watcher creates EMAIL_*.md in /Needs_Action/

3. Cloud agent triages email
   → Claims task in /In_Progress/cloud/
   → Creates draft reply in /Pending_Approval/email/
   → Original archived to /Done/

4. Vault syncs (every 60s)
   → Git push from cloud → Git pull on local
   → Draft appears on local machine

5. Human reviews in Obsidian
   → Edits draft reply
   → Moves to /Approved/

6. Local agent detects approval
   → Claims task in /In_Progress/local/
   → Sends email via Email MCP
   → Moves to /Done/

7. Vault syncs back
   → Cloud sees completion in /Done/
   → Dashboard updated with results
   → Audit log captures full chain
```

---

*Built for Personal AI Employee Hackathon 0 - Building Autonomous FTEs in 2026*
