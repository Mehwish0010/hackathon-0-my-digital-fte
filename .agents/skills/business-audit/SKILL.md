---
name: business-audit
description: Use for comprehensive cross-domain business audits. Reviews vault activity, financial data, communication logs, social media performance, and compliance against Company Handbook rules.
---

# Business Audit Skill

Perform a full cross-domain audit of business operations, compliance, and performance.

## When to Use
- When the user says "run a business audit", "full audit", "compliance check"
- When the user asks "how is the business doing", "are we on track"
- When reviewing operations before an important meeting or decision
- When checking compliance with Company_Handbook.md rules

## Workflow

### Step 1: Read Company Handbook and Business Goals
```
Read AI_Employee_Vault/Company_Handbook.md for rules of engagement
Read AI_Employee_Vault/Business_Goals.md for current objectives and metrics
```

### Step 2: Vault Activity Audit
Scan all vault folders and assess:

| Check | How |
|-------|-----|
| Inbox zero | Count files in `/Inbox/` — should be 0 |
| Stale items | Files in `/Needs_Action/` older than 48h |
| Stuck approvals | Files in `/Pending_Approval/` older than 48h |
| Completion rate | `/Done/` items this week vs total created |
| In-progress duration | Files in `/In_Progress/` — flag if > 7 days |

### Step 3: Financial Audit (if Odoo available)
```
Use odoo_health_check to verify Odoo connectivity
Use odoo_list_invoices to check outstanding invoices
Use odoo_get_account_balance for current balances
Use odoo_get_profit_loss for monthly P&L
```

Check against Business_Goals.md:
- Revenue vs monthly target
- Outstanding receivables > 30 days
- Unusual expenses

### Step 4: Communication Audit
Review audit logs for:
- Emails sent/received this week
- Response time (email received → action taken)
- Unanswered emails > 48h
- External communications sent

### Step 5: Social Media Audit
Review social activity:
- Posts published per platform this week
- Engagement trends (if summarizer data available)
- Posting frequency vs recommended schedule
- Content alignment with business goals

### Step 6: Compliance Check
Verify against Company_Handbook.md rules:
- [ ] All payments > $50 went through approval
- [ ] No credentials stored in vault files
- [ ] All external communications approved
- [ ] High-priority items processed within 24h
- [ ] Daily logs maintained
- [ ] No auto-approved actions that should need HITL

### Step 7: Error and Health Audit
Review from audit logs and service health:
- Service uptime/availability
- Error rates by service
- Auto-recovery success rate
- Watchdog restarts

### Step 8: Generate Audit Report
Create the report at `/Briefings/business_audit_{date}.md`:

```markdown
---
type: business_audit
date: {date}
generated: {ISO timestamp}
auditor: ai_employee
---

# Business Audit Report — {date}

## Overall Health Score: {A/B/C/D/F}

## Executive Summary
{2-3 sentences on overall business health}

## Vault Operations
- Inbox: {count} items (target: 0)
- Stale items: {count} (> 48h without action)
- Completion rate: {percentage}
- Stuck approvals: {count}

## Financial Health
{Odoo data or "Odoo not configured"}
- Revenue vs target: {on track / behind / ahead}
- Outstanding invoices: {count}, ${total}
- Overdue receivables: {count}

## Communication Health
- Response time: {average}
- Unanswered items: {count}
- External comms this week: {count}

## Social Media Health
- Posts this week: {count by platform}
- Frequency vs target: {on track / below}
- Engagement trend: {up / down / stable}

## Compliance
- [x] Payment approvals ✓
- [x] No credential leaks ✓
- [ ] 2 high-priority items exceeded 24h SLA ✗

## Errors & Incidents
- Total errors: {count}
- Services affected: {list}
- Resolution rate: {percentage}

## Recommendations
1. {Actionable recommendation}
2. {Actionable recommendation}
3. {Actionable recommendation}

## Health Score Breakdown
| Category | Score | Weight | Notes |
|----------|-------|--------|-------|
| Task completion | {A-F} | 25% | {detail} |
| Financial health | {A-F} | 25% | {detail} |
| Communication | {A-F} | 20% | {detail} |
| Compliance | {A-F} | 20% | {detail} |
| System health | {A-F} | 10% | {detail} |
```

## Health Score Criteria
| Grade | Criteria |
|-------|---------|
| A | > 90% completion, no overdue, all compliant |
| B | > 80% completion, < 3 overdue items |
| C | > 70% completion, some compliance issues |
| D | > 50% completion, multiple compliance issues |
| F | < 50% completion or critical compliance failures |

## Important Notes
- Audits are read-only — they report but don't modify data
- If Odoo or social media are unavailable, score those sections as "N/A"
- The audit report feeds into the CEO Briefing
- Run weekly (or on-demand) for best value
- Always reference Company_Handbook.md rules, not assumptions

## Integration
- `ceo-briefing` — audit data feeds into weekly briefing
- `odoo-accounting` — financial data source
- `social-media-manager` — social metrics source
- `reasoning-loop` — for generating recommendations
