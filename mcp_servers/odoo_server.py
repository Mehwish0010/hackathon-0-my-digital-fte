"""
Odoo Accounting MCP Server for AI Employee.

Exposes Odoo Community accounting tools via the Model Context Protocol.
Uses XML-RPC (stdlib) for Odoo API access.
All write operations create approval files in /Pending_Approval/ (HITL required).

Usage:
    uv run python mcp_servers/odoo_server.py

Register in .claude/settings.json to make tools available to Claude Code.

Config via env vars:
    ODOO_URL      - Odoo server URL (e.g. http://localhost:8069)
    ODOO_DB       - Database name
    ODOO_USERNAME - Login username
    ODOO_PASSWORD - Login password (or API key)
"""

import json
import logging
import os
import xmlrpc.client
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OdooMCP")

# Initialize MCP server
mcp = FastMCP("AI Employee Odoo Accounting Server")

# Vault path
VAULT_PATH = Path(os.environ.get("VAULT_PATH", "./AI_Employee_Vault")).resolve()


def _get_odoo_config() -> dict:
    """Get Odoo connection config from environment variables."""
    url = os.environ.get("ODOO_URL", "")
    db = os.environ.get("ODOO_DB", "")
    username = os.environ.get("ODOO_USERNAME", "")
    password = os.environ.get("ODOO_PASSWORD", "")

    if not all([url, db, username, password]):
        return {}

    return {
        "url": url.rstrip("/"),
        "db": db,
        "username": username,
        "password": password,
    }


def _get_ssl_context():
    """Get SSL context for HTTPS connections."""
    import ssl
    verify_ssl = os.environ.get("ODOO_VERIFY_SSL", "true").lower() != "false"
    if verify_ssl:
        return None  # Use default SSL verification
    else:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


def _get_odoo_connection(max_retries: int = 3) -> tuple:
    """
    Authenticate with Odoo and return (models_proxy, uid, password, db).

    Supports HTTPS and connection retry with exponential backoff.
    Raises ConnectionError if Odoo is not available.
    """
    config = _get_odoo_config()
    if not config:
        raise ConnectionError(
            "Odoo is not configured. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, "
            "ODOO_PASSWORD environment variables."
        )

    url = config["url"]
    ssl_context = _get_ssl_context()
    import time

    last_error = None
    for attempt in range(max_retries):
        try:
            # Build transport with optional SSL context
            if ssl_context and url.startswith("https"):
                import ssl as _ssl
                transport = xmlrpc.client.SafeTransport(context=ssl_context)
                common = xmlrpc.client.ServerProxy(
                    f"{url}/xmlrpc/2/common", transport=transport, allow_none=True
                )
            else:
                common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)

            uid = common.authenticate(
                config["db"], config["username"], config["password"], {}
            )

            if not uid:
                raise ConnectionError("Odoo authentication failed — check credentials.")

            if ssl_context and url.startswith("https"):
                transport = xmlrpc.client.SafeTransport(context=ssl_context)
                models = xmlrpc.client.ServerProxy(
                    f"{url}/xmlrpc/2/object", transport=transport, allow_none=True
                )
            else:
                models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

            # Record success in health tracker
            try:
                from scripts.error_recovery import ServiceHealthTracker
                tracker = ServiceHealthTracker(str(VAULT_PATH))
                tracker.record_success("odoo")
            except ImportError:
                pass

            return models, uid, config["password"], config["db"]

        except ConnectionRefusedError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning(f"Odoo connection refused, retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
        except ConnectionError:
            raise
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning(f"Odoo error: {e}, retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)

    # Record failure in health tracker
    try:
        from scripts.error_recovery import ServiceHealthTracker
        tracker = ServiceHealthTracker(str(VAULT_PATH))
        tracker.record_failure("odoo", str(last_error))
    except ImportError:
        pass

    if isinstance(last_error, ConnectionRefusedError):
        raise ConnectionError(f"Cannot connect to Odoo at {url} — is the server running?")
    raise ConnectionError(f"Odoo connection error after {max_retries} attempts: {last_error}")


def _create_approval_file(
    action_type: str,
    description: str,
    details: dict,
    urgency: str = "medium",
) -> str:
    """Create an approval file in /Pending_Approval/ for accounting actions."""
    pending_dir = VAULT_PATH / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"ACCOUNTING_{action_type}_{timestamp}.md"
    file_path = pending_dir / filename

    details_formatted = "\n".join(f"- **{k}**: {v}" for k, v in details.items())

    content = f"""---
type: approval_request
action_type: accounting_{action_type}
status: pending_approval
created: {now.isoformat()}
urgency: {urgency}
source_file: odoo_mcp_server
---

## Accounting Action Requiring Approval

**Type**: {action_type.replace('_', ' ').title()}
**Urgency**: {urgency}
**Source**: Odoo MCP Server

## Proposed Action

{description}

## Details

{details_formatted}

## Risk Assessment

- **Impact**: Financial transaction in Odoo
- **Reversible**: Yes (can be reversed with credit note/void)
- **Cost**: See amount above

## Instructions for Reviewer

- **To Approve**: Move this file to /Approved/
- **To Reject**: Move this file to /Rejected/
- **To Edit**: Modify the details above before approving
"""

    file_path.write_text(content, encoding="utf-8")
    logger.info(f"Created approval file: {filename}")
    return filename


def _log_action(action_type: str, details: str):
    """Append to daily markdown log."""
    logs_dir = VAULT_PATH / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.md"
    entry = f"- [{datetime.now().strftime('%H:%M:%S')}] **{action_type}**: {details}\n"

    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        content += entry
    else:
        content = f"# Activity Log - {today}\n\n{entry}"

    log_file.write_text(content, encoding="utf-8")


@mcp.tool()
def odoo_health_check() -> str:
    """Check if Odoo is available and properly configured.

    Returns:
        Status message about Odoo connectivity.
    """
    config = _get_odoo_config()
    if not config:
        return (
            "Odoo is NOT configured. Set these environment variables:\n"
            "- ODOO_URL (e.g. http://localhost:8069)\n"
            "- ODOO_DB (database name)\n"
            "- ODOO_USERNAME\n"
            "- ODOO_PASSWORD"
        )

    try:
        models, uid, password, db = _get_odoo_connection()
        # Test with a simple read
        version_proxy = xmlrpc.client.ServerProxy(
            f"{config['url']}/xmlrpc/2/common", allow_none=True
        )
        version = version_proxy.version()
        server_version = version.get("server_version", "unknown")
        return (
            f"Odoo is connected and healthy.\n"
            f"- URL: {config['url']}\n"
            f"- Database: {config['db']}\n"
            f"- Server version: {server_version}\n"
            f"- Authenticated as UID: {uid}"
        )
    except ConnectionError as e:
        return f"Odoo is NOT available: {e}"
    except Exception as e:
        return f"Odoo health check failed: {e}"


@mcp.tool()
def odoo_create_invoice(
    partner_name: str,
    amount: float,
    description: str,
    invoice_type: str = "out_invoice",
) -> str:
    """Create an invoice in Odoo (requires human approval).

    This creates an approval file in /Pending_Approval/ — the invoice
    is NOT created until a human approves it.

    Args:
        partner_name: Customer/vendor name
        amount: Invoice amount
        description: Line item description
        invoice_type: "out_invoice" (customer) or "in_invoice" (vendor)

    Returns:
        Confirmation that approval file was created.
    """
    type_label = "Customer Invoice" if invoice_type == "out_invoice" else "Vendor Bill"

    details = {
        "Partner": partner_name,
        "Amount": f"${amount:.2f}",
        "Description": description,
        "Type": type_label,
        "Odoo move_type": invoice_type,
    }

    filename = _create_approval_file(
        action_type="create_invoice",
        description=f"Create {type_label} for {partner_name}: ${amount:.2f} — {description}",
        details=details,
        urgency="high" if amount > 500 else "medium",
    )

    _log_action("odoo_invoice_draft", f"Approval requested: {filename}")

    return (
        f"Invoice approval request created: {filename}\n"
        f"- Type: {type_label}\n"
        f"- Partner: {partner_name}\n"
        f"- Amount: ${amount:.2f}\n"
        f"- Description: {description}\n\n"
        f"Move the file from /Pending_Approval/ to /Approved/ to create the invoice in Odoo."
    )


@mcp.tool()
def odoo_record_payment(
    partner_name: str,
    amount: float,
    payment_type: str = "inbound",
    memo: str = "",
) -> str:
    """Record a payment in Odoo (requires human approval).

    Creates an approval file — payment is NOT recorded until approved.

    Args:
        partner_name: Customer/vendor name
        amount: Payment amount
        payment_type: "inbound" (received) or "outbound" (sent)
        memo: Payment reference/memo

    Returns:
        Confirmation that approval file was created.
    """
    direction = "Payment Received" if payment_type == "inbound" else "Payment Sent"

    details = {
        "Partner": partner_name,
        "Amount": f"${amount:.2f}",
        "Direction": direction,
        "Memo": memo or "(none)",
        "Odoo payment_type": payment_type,
    }

    filename = _create_approval_file(
        action_type="record_payment",
        description=f"Record {direction}: ${amount:.2f} {'from' if payment_type == 'inbound' else 'to'} {partner_name}",
        details=details,
        urgency="high",
    )

    _log_action("odoo_payment_draft", f"Approval requested: {filename}")

    return (
        f"Payment approval request created: {filename}\n"
        f"- Direction: {direction}\n"
        f"- Partner: {partner_name}\n"
        f"- Amount: ${amount:.2f}\n"
        f"- Memo: {memo or '(none)'}\n\n"
        f"Move the file from /Pending_Approval/ to /Approved/ to record in Odoo."
    )


@mcp.tool()
def odoo_list_invoices(
    state: str = "posted",
    invoice_type: str = "out_invoice",
    limit: int = 20,
) -> str:
    """List invoices from Odoo.

    Args:
        state: Invoice state — "draft", "posted", or "cancel" (default: "posted")
        invoice_type: "out_invoice" (customer) or "in_invoice" (vendor)
        limit: Max invoices to return (default: 20)

    Returns:
        Formatted list of invoices or error message.
    """
    try:
        models, uid, password, db = _get_odoo_connection()

        invoices = models.execute_kw(
            db, uid, password,
            "account.move", "search_read",
            [[
                ["move_type", "=", invoice_type],
                ["state", "=", state],
            ]],
            {
                "fields": ["name", "partner_id", "amount_total", "invoice_date", "state", "payment_state"],
                "limit": limit,
                "order": "invoice_date desc",
            },
        )

        if not invoices:
            type_label = "customer invoices" if invoice_type == "out_invoice" else "vendor bills"
            return f"No {state} {type_label} found in Odoo."

        type_label = "Customer Invoices" if invoice_type == "out_invoice" else "Vendor Bills"
        lines = [f"**{type_label}** (state: {state}):\n"]

        for inv in invoices:
            partner = inv.get("partner_id", [0, "Unknown"])
            partner_name = partner[1] if isinstance(partner, list) else str(partner)
            lines.append(
                f"- **{inv.get('name', 'N/A')}** | {partner_name} | "
                f"${inv.get('amount_total', 0):.2f} | "
                f"{inv.get('invoice_date', 'N/A')} | "
                f"Payment: {inv.get('payment_state', 'N/A')}"
            )

        return "\n".join(lines)

    except ConnectionError as e:
        return f"Cannot connect to Odoo: {e}"
    except Exception as e:
        logger.error(f"Error listing invoices: {e}")
        return f"Error listing invoices: {e}"


@mcp.tool()
def odoo_get_account_balance() -> str:
    """Get current account balances from Odoo.

    Returns:
        Account balances summary or error message.
    """
    try:
        models, uid, password, db = _get_odoo_connection()

        # Get account balances (trial balance style)
        accounts = models.execute_kw(
            db, uid, password,
            "account.account", "search_read",
            [[]],
            {
                "fields": ["code", "name", "account_type", "current_balance"],
                "order": "code",
            },
        )

        if not accounts:
            return "No accounts found in Odoo."

        lines = ["**Account Balances:**\n"]
        total_assets = 0.0
        total_liabilities = 0.0
        total_equity = 0.0

        for acc in accounts:
            balance = acc.get("current_balance", 0.0)
            if abs(balance) < 0.01:
                continue  # Skip zero-balance accounts

            acc_type = acc.get("account_type", "")
            lines.append(
                f"- **{acc.get('code', '')}** {acc.get('name', 'N/A')}: "
                f"${balance:,.2f} ({acc_type})"
            )

            if "asset" in acc_type or "receivable" in acc_type or "bank" in acc_type:
                total_assets += balance
            elif "liability" in acc_type or "payable" in acc_type:
                total_liabilities += balance
            elif "equity" in acc_type:
                total_equity += balance

        lines.append(f"\n**Summary:**")
        lines.append(f"- Total Assets: ${total_assets:,.2f}")
        lines.append(f"- Total Liabilities: ${total_liabilities:,.2f}")
        lines.append(f"- Total Equity: ${total_equity:,.2f}")

        return "\n".join(lines)

    except ConnectionError as e:
        return f"Cannot connect to Odoo: {e}"
    except Exception as e:
        logger.error(f"Error getting balances: {e}")
        return f"Error getting account balances: {e}"


@mcp.tool()
def odoo_get_profit_loss(date_from: str = "", date_to: str = "") -> str:
    """Get profit and loss summary from Odoo.

    Args:
        date_from: Start date (YYYY-MM-DD). Defaults to first of current month.
        date_to: End date (YYYY-MM-DD). Defaults to today.

    Returns:
        Profit/loss summary or error message.
    """
    now = datetime.now()
    if not date_from:
        date_from = now.strftime("%Y-%m-01")
    if not date_to:
        date_to = now.strftime("%Y-%m-%d")

    try:
        models, uid, password, db = _get_odoo_connection()

        # Get all posted journal items in the date range
        move_lines = models.execute_kw(
            db, uid, password,
            "account.move.line", "search_read",
            [[
                ["date", ">=", date_from],
                ["date", "<=", date_to],
                ["parent_state", "=", "posted"],
            ]],
            {
                "fields": ["account_id", "balance"],
                "limit": 5000,
            },
        )

        # Group by account and classify
        from collections import defaultdict
        account_totals = defaultdict(lambda: {"name": "", "balance": 0.0})

        for ml in move_lines:
            acc = ml.get("account_id", [0, "Unknown"])
            acc_id = acc[0] if isinstance(acc, list) else acc
            acc_name = acc[1] if isinstance(acc, list) else str(acc)
            account_totals[acc_id]["name"] = acc_name
            account_totals[acc_id]["balance"] += ml.get("balance", 0.0)

        # Get account types
        acc_ids = list(account_totals.keys())
        acc_info = {}
        if acc_ids:
            accounts = models.execute_kw(
                db, uid, password,
                "account.account", "search_read",
                [[["id", "in", acc_ids]]],
                {"fields": ["id", "account_type"]},
            )
            for a in accounts:
                acc_info[a["id"]] = a.get("account_type", "")

        total_income = 0.0
        total_expenses = 0.0
        income_details = []
        expense_details = []

        for acc_id, data in account_totals.items():
            acc_type = acc_info.get(acc_id, "")
            balance = data["balance"]
            name = data["name"]

            if "income" in acc_type:
                total_income += abs(balance)
                income_details.append((name, abs(balance)))
            elif "expense" in acc_type:
                total_expenses += abs(balance)
                expense_details.append((name, abs(balance)))

        net_profit = total_income - total_expenses

        lines = [
            f"**Profit & Loss** ({date_from} to {date_to})\n",
            f"**Revenue:**",
        ]

        for name, amount in income_details:
            lines.append(f"- {name}: ${amount:,.2f}")
        if not income_details:
            lines.append("- (no revenue entries)")

        lines.append(f"**Total Revenue: ${total_income:,.2f}**\n")
        lines.append(f"**Expenses:**")

        for name, amount in expense_details:
            lines.append(f"- {name}: ${amount:,.2f}")
        if not expense_details:
            lines.append("- (no expense entries)")

        lines.append(f"**Total Expenses: ${total_expenses:,.2f}**\n")
        lines.append(f"---")
        lines.append(f"**Net {'Profit' if net_profit >= 0 else 'Loss'}: ${net_profit:,.2f}**")

        return "\n".join(lines)

    except ConnectionError as e:
        return f"Cannot connect to Odoo: {e}"
    except Exception as e:
        logger.error(f"Error getting P&L: {e}")
        return f"Error getting profit/loss: {e}"


if __name__ == "__main__":
    mcp.run()
