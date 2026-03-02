---
name: ceo-briefing
description: Use when generating or interpreting weekly CEO briefings. Pulls data from vault stats, Odoo financials, social media metrics, audit logs, and business goals into a comprehensive executive summary.
---

# CEO Briefing Skill

Generate comprehensive weekly CEO briefings that synthesize data from all system components.

## When to Use
- When the user says "generate CEO briefing", "weekly briefing", "executive summary"
- When the user asks for a business overview or status report
- On the scheduled weekly briefing (Sunday 9 PM via scheduler)
- When the user says "what happened this week", "business summary"

## Workflow

### Step 1: Generate the Briefing
Run the CEO briefing generator:

```bash
uv run python scripts/ceo_briefing.py --vault ./AI_Employee_Vault
```

Or trigger it via the scheduler (runs automatically Sunday 9 PM).

### Step 2: Data Sources
The briefing pulls from ALL available sources:

| Source | Data | Fallback if Unavailable |
|--------|------|------------------------|
| Vault folders | Task counts, completion rates | Always available |
| `/Logs/*.json` | Audit log entries, error counts | Empty summary |
| Odoo (if configured) | Revenue, invoices, P&L | "Odoo unavailable" section |
| Social media summary | Post counts, engagement | "No social data" |
| `/Briefings/` | Previous briefings for trends | Skip trends |
| `Business_Goals.md` | Objectives and metrics | Skip goals section |

### Step 3: Briefing Structure
The output file is saved to `/Briefings/CEO_Briefing_{date}.md`:

```markdown
# CEO Briefing — Week of {date}

## Executive Summary
{2-3 sentence high-level overview}

## Revenue & Financials
- MTD Revenue: ${amount}
- Outstanding Invoices: {count}
- P&L Summary: {net profit/loss}
(or "Odoo not configured — connect for financial data")

## Task Completion
- Tasks completed this week: {count}
- Tasks pending: {count}
- Completion rate: {percentage}
- Overdue items: {count}

## Bottlenecks & Blockers
- {items that have been in Pending_Approval > 48h}
- {failed actions from audit logs}
- {service health issues}

## Social Media Performance
- Posts published: {count by platform}
- Engagement summary: {if metrics available}
(or "Social media not yet configured")

## Proactive Suggestions
- {AI-generated recommendations based on patterns}
- {e.g. "3 invoices overdue > 30 days — consider follow-up"}
- {e.g. "No LinkedIn posts this week — consider thought leadership content"}

## Error Summary
- Total errors this week: {count}
- Services affected: {list}
- Auto-recovered: {count}
- Needs attention: {count}

## Next Week Priorities
{Based on Business_Goals.md and current backlog}
```

### Step 4: Review and Act
After the briefing is generated:
1. Review in Obsidian at `/Briefings/CEO_Briefing_{date}.md`
2. Act on bottlenecks and suggestions
3. Update Business_Goals.md if priorities changed
4. The briefing becomes input for next week's comparison

## Interpreting Previous Briefings
When the user asks about past performance:
1. Read previous briefings from `/Briefings/`
2. Compare week-over-week metrics
3. Identify trends (improving/declining)
4. Highlight areas that need attention

## Important Notes
- Graceful degradation: if Odoo or social media are unavailable, the briefing still generates with available data
- The briefing never makes up numbers — it reports "unavailable" for missing data
- Error summaries come from JSON audit logs, not markdown logs
- The CEO briefing is the highest-level summary — it references but doesn't duplicate daily briefings
- Scheduled automatically: Sunday 9 PM (after social summary at 8 PM)

## Integration
- `business-audit` — deeper dive on specific areas
- `odoo-accounting` — financial data source
- `social-media-manager` — social metrics source
- `reasoning-loop` — for generating proactive suggestions
- Scheduler triggers weekly generation
