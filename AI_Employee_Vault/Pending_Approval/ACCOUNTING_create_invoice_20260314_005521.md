---
type: approval_request
action_type: accounting_create_invoice
status: pending_approval
created: 2026-03-14T00:55:21.461686
urgency: medium
source_file: odoo_mcp_server
---

## Accounting Action Requiring Approval

**Type**: Create Invoice
**Urgency**: medium
**Source**: Odoo MCP Server

## Proposed Action

Create Customer Invoice for Test Client ABC: $250.00 — AI Employee Setup - March 2026

## Details

- **Partner**: Test Client ABC
- **Amount**: $250.00
- **Description**: AI Employee Setup - March 2026
- **Type**: Customer Invoice
- **Odoo move_type**: out_invoice

## Risk Assessment

- **Impact**: Financial transaction in Odoo
- **Reversible**: Yes (can be reversed with credit note/void)
- **Cost**: See amount above

## Instructions for Reviewer

- **To Approve**: Move this file to /Approved/
- **To Reject**: Move this file to /Rejected/
- **To Edit**: Modify the details above before approving
