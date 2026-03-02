# Lessons Learned — AI Employee Hackathon

## Architecture Decisions

### Why Obsidian as the message bus?
We considered SQLite, Redis, and custom JSON stores. Obsidian markdown files won because:
- Zero infrastructure (no server to run)
- Human-readable and editable in Obsidian
- Git-friendly (diffs make sense)
- File watchers are trivial in Python
- The user can intervene by simply moving files between folders

### Why Playwright over official APIs?
LinkedIn, Facebook, Instagram, and Twitter either:
- Don't offer posting APIs to individuals
- Require business verification and complex OAuth
- Rate-limit aggressively

Playwright with persistent browser sessions provides reliable posting with a one-time manual login. The tradeoff is UI fragility — platform redesigns can break selectors.

### Why file prefixes for routing?
We considered frontmatter parsing, folder-based routing, and filename conventions. File prefixes (`EMAIL_`, `LINKEDIN_`, `ACCOUNTING_`, etc.) won because:
- Instantly visible in file explorers and Obsidian
- Fast to check (string prefix, no file parsing)
- Easy to extend (add a prefix to `ACTION_PREFIXES` dict)
- Works with glob patterns (`LINKEDIN_*.md`)

### Why XML-RPC for Odoo?
Odoo Community's XML-RPC API is:
- Available in stdlib (`xmlrpc.client` — zero dependencies)
- Stable across Odoo versions
- Well-documented
- Works with both Community and Enterprise editions

### Why separate JSON audit logs?
Markdown logs are great for humans but hard to query programmatically. JSON-lines format:
- One entry per line, easy to parse
- Supports structured queries (by action type, actor, date range)
- 90-day retention keeps disk usage bounded
- Powers the CEO briefing error summaries

## Patterns That Worked

### 1. The Approval Pipeline
`/Pending_Approval/` → human moves → `/Approved/` → watcher executes → `/Done/`

This pattern is simple, visible, and safe. The human always has final say on external actions.

### 2. Shared `log_action()` Pattern
Every script has the same logging helper. This ensures consistent log format across all components.

### 3. `--once` and `--dry-run` Flags
Every watcher and poster supports these flags. Makes testing trivial and scheduled execution clean.

### 4. Persistent Browser Sessions
Storing Playwright sessions in `linkedin_session/`, `facebook_session/`, `twitter_session/` avoids re-authentication. Sessions survive script restarts.

### 5. Graceful Service Checks
Every component that depends on an external service checks availability first and returns clear messages instead of crashing.

## What We'd Do Differently

### 1. Unified logging from the start
The markdown `log_action()` pattern was duplicated across 6+ scripts before we created `audit_logger.py`. A shared module from day one would have been cleaner.

### 2. Config management
Environment variables work but are scattered. A centralized config module (loading from `.env` + defaults) would reduce boilerplate.

### 3. Integration testing harness
Each component was tested manually. A test harness that creates a temporary vault, runs scripts, and verifies file movements would catch regressions.

### 4. Approval watcher could be event-driven
Currently `approval_watcher.py` uses file system events (watchdog) but the scheduler also polls it. Pure event-driven with watchdog would be cleaner.

## Gold Tier Additions Summary

| Component | What It Adds |
|-----------|-------------|
| `audit_logger.py` | Structured JSON audit trail, 90-day retention |
| `error_recovery.py` | Retry decorator, service health tracking, graceful degradation |
| `watchdog_monitor.py` | Process health monitoring, auto-restart |
| `odoo_server.py` | Full accounting via Odoo XML-RPC |
| `social_media_server.py` | Cross-platform social media drafting |
| `facebook_poster.py` | Facebook + Instagram via Playwright |
| `twitter_poster.py` | Twitter/X via Playwright, 280-char enforcement |
| `social_media_summarizer.py` | Weekly social engagement reports |
| `ceo_briefing.py` | Comprehensive weekly executive summary |
| `ralph_loop.py` | Autonomous retry with completion detection |
| 8 new skills | Odoo, social platforms, CEO briefing, audit, Ralph Wiggum |
