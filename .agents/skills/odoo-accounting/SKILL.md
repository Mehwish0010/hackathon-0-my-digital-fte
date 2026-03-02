---
name: odoo-accounting
description: Manage Odoo accounting — invoices, payments, balances, P&L reports
---

# Odoo Accounting Skill

Use the Odoo MCP tools to manage accounting operations. All financial write operations require human approval via the HITL workflow.

## When to Use

- When the user asks about invoices, payments, or financial data
- When processing emails/files that reference invoices or payments
- When generating financial reports or CEO briefings
- When the user says "create invoice", "record payment", "check balance", "profit and loss"

## Available MCP Tools

| Tool | Action | Needs Approval? |
|------|--------|----------------|
| `odoo_health_check` | Check Odoo connectivity | No |
| `odoo_create_invoice` | Create customer/vendor invoice | **Yes** |
| `odoo_record_payment` | Record payment received/sent | **Yes** |
| `odoo_list_invoices` | List invoices by state/type | No |
| `odoo_get_account_balance` | Get account balances | No |
| `odoo_get_profit_loss` | Get P&L for date range | No |

## Workflow

### Step 1: Check Odoo Availability

Before any accounting operation, verify connectivity:
```
Use odoo_health_check to verify Odoo is available
```
If Odoo is unavailable, inform the user and log the issue. Do NOT retry repeatedly.

### Step 2: Read Operations (No Approval Needed)

For queries, use the tools directly:
```
Use odoo_list_invoices with state="posted" to see current invoices
Use odoo_get_account_balance for current balances
Use odoo_get_profit_loss with date_from="2026-01-01" for monthly P&L
```

### Step 3: Write Operations (Approval Required)

For invoices and payments, the MCP tools automatically create approval files:

1. Call `odoo_create_invoice` or `odoo_record_payment`
2. Tool creates `ACCOUNTING_*.md` in `/Pending_Approval/`
3. Inform the user: "Approval file created — review in /Pending_Approval/"
4. Human moves file to `/Approved/` → approval watcher executes the action
5. Or human moves to `/Rejected/` → action cancelled

### Step 4: Log Everything

After each operation, ensure it's logged:
- Read operations: log to `/Logs/` daily log
- Write operations: automatically logged by the MCP tools

## Important Notes

- **NEVER** create invoices or payments without going through the approval workflow
- If Odoo is down, report clearly — don't crash or retry infinitely
- For amounts over $500, always flag as HIGH urgency
- Cross-reference with Business_Goals.md for revenue tracking
- All Odoo credentials come from environment variables — never store in vault
