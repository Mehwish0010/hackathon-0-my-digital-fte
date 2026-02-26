# Personal AI Employee - Hackathon 0

> Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

A Digital FTE (Full-Time Equivalent) built with Claude Code and Obsidian that proactively manages personal and business affairs using watchers, reasoning, and MCP-based actions.

## Tier Progress

| Tier | Status | Requirements |
|------|--------|-------------|
| **Bronze** | COMPLETED | See checklist below |
| **Silver** | COMPLETED | Gmail watcher, LinkedIn posting, MCP server, HITL, scheduling, reasoning loop |
| **Gold** | Not Started | Odoo, social media, CEO briefing, Ralph Wiggum loop, audit logging |
| **Platinum** | Not Started | Cloud 24/7, work-zone specialization, synced vault |

---

## Architecture

```
EXTERNAL SOURCES (Files, Gmail, LinkedIn, Bank*)
        |
        v
PERCEPTION LAYER (Python Watcher Scripts)
  filesystem_watcher.py | gmail_watcher.py | approval_watcher.py
        |
        v
OBSIDIAN VAULT (Local Markdown)
  /Inbox -> /Needs_Action -> /In_Progress -> /Done
  /Pending_Approval -> /Approved | /Rejected
  Dashboard.md | Company_Handbook.md | Business_Goals.md
        |
        v
REASONING LAYER (Claude Code + Agent Skills)
  reasoning-loop: Read -> Think -> Plan -> Act -> Log
  vault-triage | inbox-processor | dashboard-updater
        |
        v
ACTION LAYER (MCP Servers + Playwright)
  Email MCP (send/draft/list) | LinkedIn Auto-Poster
        |
        v
HUMAN-IN-THE-LOOP (hitl-approval skill)
  /Pending_Approval -> Human Review -> /Approved or /Rejected

(* = Gold tier and above)
```

## Project Structure

```
hackathon-0-final/
├── AI_Employee_Vault/          # Obsidian vault (the dashboard)
│   ├── Inbox/                  # Drop files here for processing
│   ├── Needs_Action/           # Watcher output, pending triage
│   ├── In_Progress/            # Currently being worked on
│   ├── Done/                   # Completed items
│   ├── Plans/                  # Claude-generated Plan.md files
│   ├── Logs/                   # Daily activity logs (YYYY-MM-DD.md)
│   ├── Pending_Approval/       # Items needing human approval
│   ├── Approved/               # Human-approved actions
│   ├── Rejected/               # Human-rejected actions
│   ├── Briefings/              # Daily/weekly briefings
│   ├── Accounting/             # Financial tracking
│   ├── Dashboard.md            # Real-time status overview
│   ├── Company_Handbook.md     # Rules of engagement
│   └── Business_Goals.md       # Objectives and metrics
├── scripts/
│   ├── base_watcher.py         # Base class for all watchers
│   ├── filesystem_watcher.py   # File system watcher (Bronze)
│   ├── gmail_watcher.py        # Gmail watcher (Silver)
│   ├── linkedin_poster.py      # LinkedIn auto-poster (Silver)
│   ├── approval_watcher.py     # Approval watcher (Silver)
│   └── scheduler.py            # Task scheduler (Silver)
├── mcp_servers/
│   └── email_server.py         # Email MCP server (Silver)
├── .agents/skills/             # Agent Skills (8 total)
│   ├── vault-triage/           # Triage /Needs_Action items
│   ├── dashboard-updater/      # Refresh Dashboard.md
│   ├── inbox-processor/        # Full end-to-end processing
│   ├── playwright-browser/     # Browser automation
│   ├── gmail-watcher/          # Gmail monitoring (Silver)
│   ├── linkedin-poster/        # LinkedIn posting (Silver)
│   ├── hitl-approval/          # Approval workflow (Silver)
│   └── reasoning-loop/         # Plan + execute loop (Silver)
├── .claude/settings.json       # MCP server configuration
├── .env.example                # Environment template
├── .gitignore
├── pyproject.toml
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
- Google Cloud project with Gmail API enabled (Silver tier)

### Installation

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd hackathon-0-final

# 2. Install Python dependencies
uv sync
# If uv sync has cache issues on Windows, use:
.venv/Scripts/python.exe -m ensurepip
.venv/Scripts/python.exe -m pip install google-auth-oauthlib google-api-python-client playwright mcp schedule watchdog

# 3. Install Playwright Chromium browser (for LinkedIn posting)
.venv/Scripts/python.exe -m playwright install chromium

# 4. Copy environment file
cp .env.example .env

# 5. Open the vault in Obsidian
# Open Obsidian -> Open folder as vault -> select AI_Employee_Vault/
```

### Gmail API Setup (Silver Tier)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project or select existing one
3. Enable the **Gmail API** under APIs & Services
4. Create **OAuth 2.0 credentials** (Desktop application)
5. Download the client secret JSON file to the project root
6. Add your email as a **test user** under OAuth consent screen → Audience
7. First run of `gmail_watcher.py` will open browser for OAuth consent

### LinkedIn Setup (Silver Tier)

```bash
# One-time login — opens browser, log in manually, then close
.venv/Scripts/python.exe scripts/linkedin_poster.py --login
```

Session is saved to `linkedin_session/` for future automated posts.

---

## Agent Skills Reference

All AI functionality is implemented as Agent Skills. Claude Code uses these skills to process tasks autonomously.

| Skill | Tier | Purpose | How to Trigger |
|-------|------|---------|----------------|
| `vault-triage` | Bronze | Process /Needs_Action items, classify priority, route to Done or Approval | "triage actions", "process needs action" |
| `dashboard-updater` | Bronze | Scan vault folders, count items, refresh Dashboard.md | "update dashboard", "status update" |
| `inbox-processor` | Bronze | Full end-to-end cycle: triage → execute → log → update dashboard | "process everything", "run cycle" |
| `playwright-browser` | Bronze | Browser automation: screenshots, scraping, form filling | "take screenshot", "scrape website" |
| `gmail-watcher` | Silver | Monitor Gmail via API, create action files from emails | "check email", "watch Gmail" |
| `linkedin-poster` | Silver | Post approved drafts to LinkedIn via Playwright | "post to LinkedIn", "publish post" |
| `hitl-approval` | Silver | Create approval requests, route sensitive actions for human review | "approve", "review pending", "flag for approval" |
| `reasoning-loop` | Silver | Read → Think → Plan → Act → Log structured reasoning | "create a plan", "reason about this", "think through" |

### How Skills Work

Skills are markdown files in `.agents/skills/` that give Claude Code instructions for specific tasks. When you trigger a skill (by saying the trigger phrase in Claude Code), Claude follows the step-by-step workflow defined in that skill's `SKILL.md`.

---

## Bronze Tier — Local Vault + File Watcher

### What It Does
- Obsidian vault with structured folders for task lifecycle
- File system watcher monitors `/Inbox/` for new files
- Automatic priority classification (high/medium/low)
- Action files created in `/Needs_Action/` for Claude to triage
- Agent Skills for triage, dashboard updates, and full processing

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
In Claude Code, say:
```
triage the action items in Needs_Action
```
Expected: Claude uses `vault-triage` skill → reads each file → classifies priority → moves simple items to `/Done/` → flags complex items for approval → logs everything.

**Test 3: Dashboard Update (Agent Skill)**
In Claude Code, say:
```
update the dashboard
```
Expected: Claude uses `dashboard-updater` skill → counts items in each folder → updates `Dashboard.md` with current stats.

**Test 4: Full Processing Cycle (Agent Skill)**
In Claude Code, say:
```
process everything in the vault
```
Expected: Claude uses `inbox-processor` skill → reads Company_Handbook → triages all items → executes actions → updates dashboard → generates summary.

---

## Silver Tier — Real Integrations + HITL + Reasoning

### What It Does
- **Gmail Watcher**: Monitors Gmail API for unread emails, creates action files with email metadata
- **LinkedIn Auto-Poster**: Posts approved drafts to LinkedIn via Playwright browser automation
- **Email MCP Server**: Exposes `send_email`, `draft_email`, `list_emails` as Claude Code tools
- **Approval Watcher**: Monitors `/Approved/` folder, triggers actions when human approves
- **HITL Workflow**: Sensitive actions routed to `/Pending_Approval/` for human review
- **Reasoning Loop**: Claude creates structured Plan.md files, executes step-by-step
- **Scheduler**: Automated task scheduling (Gmail every 2min, dashboard every 15min, daily briefing at 8AM)

### Silver Checklist
- [x] Gmail Watcher (monitor important emails via Gmail API)
- [x] LinkedIn auto-posting via Playwright
- [x] Email MCP server (send_email, draft_email, list_emails)
- [x] Human-in-the-loop approval workflow (/Pending_Approval → /Approved)
- [x] Approval Watcher (monitors /Approved, triggers actions)
- [x] Scheduled tasks via `schedule` library (Gmail, dashboard, briefings)
- [x] Claude reasoning loop with Plan.md files
- [x] Four new Agent Skills (gmail-watcher, linkedin-poster, hitl-approval, reasoning-loop)

### Running Silver Components

```bash
# Gmail Watcher
.venv/Scripts/python.exe scripts/gmail_watcher.py                # Continuous (every 2 min)
.venv/Scripts/python.exe scripts/gmail_watcher.py --once         # One-time check
.venv/Scripts/python.exe scripts/gmail_watcher.py --dry-run      # Preview without creating files

# LinkedIn Poster
.venv/Scripts/python.exe scripts/linkedin_poster.py --login      # First-time LinkedIn login
.venv/Scripts/python.exe scripts/linkedin_poster.py              # Post approved drafts
.venv/Scripts/python.exe scripts/linkedin_poster.py --dry-run    # Preview without posting

# Approval Watcher
.venv/Scripts/python.exe scripts/approval_watcher.py             # Continuous watch
.venv/Scripts/python.exe scripts/approval_watcher.py --once      # One-time check

# Scheduler (runs everything on schedule)
.venv/Scripts/python.exe scripts/scheduler.py                    # Start scheduler
.venv/Scripts/python.exe scripts/scheduler.py --create-bat       # Create Windows Task Scheduler .bat
```

### How to Test Silver

**Test 1: Gmail Watcher → Action Files**
```bash
# Send yourself a test email, then:
.venv/Scripts/python.exe scripts/gmail_watcher.py --vault ./AI_Employee_Vault --once
```
Expected: OAuth flow (first run) → fetches unread emails → creates `EMAIL_*.md` files in `/Needs_Action/` with from, subject, body, priority.

**Test 2: Gmail Triage (Agent Skill)**
After Gmail watcher creates action files, say in Claude Code:
```
triage the action items
```
Expected: Claude uses `vault-triage` skill → classifies emails by priority → archives newsletters to `/Done/` → flags invoices/payments for approval in `/Pending_Approval/`.

**Test 3: Human-in-the-Loop Approval Workflow**
```bash
# 1. Claude creates approval file (via hitl-approval skill)
# 2. Review the file in Obsidian at /Pending_Approval/
# 3. Move the file to /Approved/ (to approve) or /Rejected/ (to reject)
# 4. Run approval watcher to trigger the action:
.venv/Scripts/python.exe scripts/approval_watcher.py --once
```
Or in Claude Code, say:
```
flag this email for approval — it involves sending money
```
Expected: Claude uses `hitl-approval` skill → creates approval file in `/Pending_Approval/` → waits for human to move to `/Approved/` → approval watcher executes action.

**Test 4: LinkedIn Auto-Post**
```bash
# 1. First-time login (opens browser)
.venv/Scripts/python.exe scripts/linkedin_poster.py --login

# 2. Create a draft in /Pending_Approval/
# (or ask Claude: "draft a LinkedIn post about AI automation")

# 3. Move approved draft to /Approved/LINKEDIN_*.md

# 4. Post it
.venv/Scripts/python.exe scripts/linkedin_poster.py
```
Expected: Reads `LINKEDIN_*.md` from `/Approved/` → posts via Playwright → saves proof screenshot → moves to `/Done/`.

**Test 5: Email MCP Server**
The MCP server is registered in `.claude/settings.json`. In Claude Code, say:
```
draft an email to test@example.com about the project status
```
Expected: Claude uses `draft_email` MCP tool → creates draft in Gmail → confirms with draft ID.

Other MCP commands:
```
send an email to boss@company.com about the weekly update
list my unread emails
```

**Test 6: Reasoning Loop (Agent Skill)**
In Claude Code, say:
```
create a plan for processing all pending items and posting a LinkedIn update
```
Expected: Claude uses `reasoning-loop` skill → reads vault context → creates `Plan.md` in `/Plans/` with status, steps, approval flags → executes each step → updates plan as steps complete → logs results.

**Test 7: Scheduler**
```bash
.venv/Scripts/python.exe scripts/scheduler.py
```
Expected: Runs continuously with:
- Gmail check every 2 minutes
- Dashboard update every 15 minutes
- Approval check every 5 minutes
- Daily briefing at 8:00 AM (saved to `/Briefings/`)

**Test 8: Windows Task Scheduler Integration**
```bash
.venv/Scripts/python.exe scripts/scheduler.py --create-bat
```
Expected: Creates `run_scheduler.bat` → instructions to add to Windows Task Scheduler for auto-start.

### Silver Workflow End-to-End

Here's how all Silver components work together:

```
1. Gmail Watcher runs (via scheduler, every 2 min)
   → Detects unread email from client about invoice
   → Creates EMAIL_*.md in /Needs_Action/ (priority: high)

2. Claude Code triages (vault-triage skill)
   → Reads the email action file
   → Detects "invoice" keyword → high priority
   → Creates approval request in /Pending_Approval/

3. Human reviews in Obsidian
   → Opens /Pending_Approval/PAYMENT_*.md
   → Reviews the invoice details
   → Moves file to /Approved/

4. Approval Watcher detects the move
   → Triggers the approved action
   → Logs the approval in /Logs/

5. Claude drafts reply (reasoning-loop + email MCP)
   → Creates Plan.md with steps
   → Uses draft_email MCP tool to create Gmail draft
   → Updates plan status to "done"

6. Dashboard auto-updates (scheduler, every 15 min)
   → Reflects current counts and recent activity

7. Daily briefing generated at 8 AM
   → Summary of pending items, approvals, activity
```

---

## Security

- Credentials stored in `.env` and `token.json` (never committed — see `.gitignore`)
- `client_secret_*.json` is gitignored for safety
- Sensitive actions (payments, external comms) always require human approval
- All actions audit-logged in `/Logs/YYYY-MM-DD.md`
- Local-first: all data stays on your machine
- LinkedIn session stored locally in `linkedin_session/` (gitignored)
- See `Company_Handbook.md` for full security rules

---

## Gold Tier Roadmap

- [ ] Odoo Community integration (accounting)
- [ ] Facebook/Instagram integration
- [ ] Twitter (X) integration
- [ ] Weekly Business Audit + CEO Briefing
- [ ] Ralph Wiggum loop for autonomous completion
- [ ] Error recovery and graceful degradation
- [ ] Comprehensive audit logging

## Platinum Tier Roadmap

- [ ] Cloud VM deployment (24/7)
- [ ] Cloud/Local work-zone specialization
- [ ] Synced vault via Git
- [ ] Odoo on cloud with HTTPS
- [ ] A2A upgrade (optional)

---

*Built for Personal AI Employee Hackathon 0 - Building Autonomous FTEs in 2026*
