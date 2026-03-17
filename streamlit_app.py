"""AI Employee Dashboard — Streamlit UI for the Personal AI Employee hackathon project."""

import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
VAULT = Path(__file__).parent / "AI_Employee_Vault"
FOLDERS = ["Inbox", "Needs_Action", "In_Progress", "Pending_Approval", "Approved", "Done", "Rejected"]

st.set_page_config(page_title=" Mehwish Fatima AI Employee", page_icon="🤖", layout="wide")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _real_files(folder: Path) -> list[Path]:
    """Return non-hidden, non-.gitkeep files (recursively)."""
    if not folder.exists():
        return []
    return sorted(
        [f for f in folder.rglob("*") if f.is_file() and f.name not in (".gitkeep", ".git")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def count_items(folder_name: str) -> int:
    return len(_real_files(VAULT / folder_name))


def parse_frontmatter(text: str) -> dict:
    """Extract YAML-ish frontmatter between --- delimiters."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def move_file(src: Path, dest_folder_name: str):
    dest_dir = VAULT / dest_folder_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest_dir / src.name))


def urgency_badge(urgency: str) -> str:
    colors = {"high": "red", "medium": "orange", "low": "green"}
    c = colors.get(urgency.lower(), "gray")
    return f":{c}[{urgency.upper()}]"


def file_type_icon(name: str) -> str:
    n = name.upper()
    if n.startswith("EMAIL"):
        return "📧"
    if n.startswith("LINKEDIN"):
        return "💼"
    if n.startswith("FACEBOOK"):
        return "📘"
    if n.startswith("INSTAGRAM"):
        return "📷"
    if n.startswith("TWITTER"):
        return "🐦"
    if n.startswith("ACCOUNTING") or n.startswith("PAYMENT"):
        return "💰"
    if n.startswith("RALPH"):
        return "🔁"
    if n.startswith("FILE"):
        return "📄"
    return "📋"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🤖 AI Employee")
    st.caption("Personal Digital FTE")
    st.markdown("**Built by Mehwish Fatima**")
    st.divider()
    page = st.radio(
        "Navigate",
        ["Dashboard", "Inbox & Triage", "Approvals", "Completed Work", "Activity Logs", "CEO Briefing"],
        label_visibility="collapsed",
    )
    st.divider()
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    st.caption(f"Vault: {VAULT.name}")


# ===================================================================
# PAGE: Dashboard
# ===================================================================
if page == "Dashboard":
    st.header("Dashboard")

    # --- Metric cards ---
    cols = st.columns(6)
    folder_labels = [
        ("Inbox", "Inbox"),
        ("Needs_Action", "Needs Action"),
        ("In_Progress", "In Progress"),
        ("Pending_Approval", "Pending Approval"),
        ("Approved", "Approved"),
        ("Done", "Done"),
    ]
    for col, (folder, label) in zip(cols, folder_labels):
        col.metric(label, count_items(folder))

    st.divider()

    # --- Charts ---
    col_chart, col_status = st.columns([1, 1])

    with col_chart:
        st.subheader("Item Distribution")
        chart_data = {label: count_items(folder) for folder, label in folder_labels}
        non_zero = {k: v for k, v in chart_data.items() if v > 0}
        if non_zero:
            import pandas as pd
            df = pd.DataFrame({"Folder": list(non_zero.keys()), "Count": list(non_zero.values())})
            st.bar_chart(df, x="Folder", y="Count")
        else:
            st.info("No items in vault yet.")

    with col_status:
        st.subheader("System Status")
        dashboard_file = VAULT / "Dashboard.md"
        if dashboard_file.exists():
            content = dashboard_file.read_text(encoding="utf-8")
            # Parse system status table
            in_table = False
            rows = []
            for line in content.splitlines():
                if "| Component" in line:
                    in_table = True
                    continue
                if in_table and line.startswith("|---"):
                    continue
                if in_table and line.startswith("|"):
                    parts = [p.strip() for p in line.split("|")[1:-1]]
                    if len(parts) >= 2:
                        status = parts[1]
                        indicator = "🟢" if status.lower() in ("ready", "running", "active", "configured", "healthy") else "🟡"
                        rows.append(f"{indicator} **{parts[0]}** — {status}")
                elif in_table:
                    in_table = False
            for r in rows:
                st.markdown(r)
        else:
            st.warning("Dashboard.md not found")

    st.divider()

    # --- Recent Activity ---
    st.subheader("Recent Activity")
    log_dir = VAULT / "Logs"
    log_files = sorted(log_dir.glob("*.md"), reverse=True)
    if log_files:
        latest_log = log_files[0]
        lines = latest_log.read_text(encoding="utf-8").splitlines()
        activity_lines = [l for l in lines if l.startswith("- [")]
        for entry in activity_lines[-15:]:
            st.markdown(entry)
        st.caption(f"From: {latest_log.name}")
    else:
        st.info("No activity logs yet.")

    # --- Deployment info ---
    st.divider()
    dep_col1, dep_col2 = st.columns(2)
    with dep_col1:
        dashboard_file = VAULT / "Dashboard.md"
        if dashboard_file.exists():
            content = dashboard_file.read_text(encoding="utf-8")
            m = re.search(r"Deployment Mode\s*\|\s*(\w+)", content)
            mode = m.group(1) if m else "local"
            st.info(f"**Deployment Mode**: {mode.upper()}")
    with dep_col2:
        m2 = re.search(r"Last Dashboard Refresh\s*\|\s*(.+)", content) if dashboard_file.exists() else None
        if m2:
            st.info(f"**Last Refresh**: {m2.group(1).strip()}")


# ===================================================================
# PAGE: Inbox & Triage
# ===================================================================
elif page == "Inbox & Triage":
    st.header("Inbox & Triage")

    tab_na, tab_inbox = st.tabs(["🔴 Needs Action", "📥 Inbox"])

    for tab, folder_name in [(tab_na, "Needs_Action"), (tab_inbox, "Inbox")]:
        with tab:
            files = _real_files(VAULT / folder_name)
            if not files:
                st.success(f"No items in {folder_name.replace('_', ' ')}.")
                continue
            st.caption(f"{len(files)} item(s)")
            for f in files:
                icon = file_type_icon(f.name)
                with st.expander(f"{icon} {f.name}"):
                    content = f.read_text(encoding="utf-8", errors="replace")
                    meta = parse_frontmatter(content)
                    if meta.get("urgency"):
                        st.markdown(urgency_badge(meta["urgency"]))
                    st.markdown(content[:2000])
                    col1, col2 = st.columns(2)
                    if col1.button("✅ Approve", key=f"approve_{folder_name}_{f.name}"):
                        move_file(f, "Approved")
                        st.toast(f"Moved {f.name} → Approved")
                        st.rerun()
                    if col2.button("❌ Reject", key=f"reject_{folder_name}_{f.name}"):
                        move_file(f, "Rejected")
                        st.toast(f"Moved {f.name} → Rejected")
                        st.rerun()


# ===================================================================
# PAGE: Approvals (HITL)
# ===================================================================
elif page == "Approvals":
    st.header("Pending Approvals (HITL)")

    files = _real_files(VAULT / "Pending_Approval")
    if not files:
        st.success("No items pending approval.")
    else:
        st.caption(f"{len(files)} item(s) awaiting review")

        for f in files:
            icon = file_type_icon(f.name)
            content = f.read_text(encoding="utf-8", errors="replace")
            meta = parse_frontmatter(content)

            urgency = meta.get("urgency", "")
            action_type = meta.get("action_type", meta.get("type", ""))
            created = meta.get("created", "")

            header_parts = [f"{icon} **{f.name}**"]
            if urgency:
                header_parts.append(urgency_badge(urgency))
            if action_type:
                header_parts.append(f"| `{action_type}`")
            if created:
                header_parts.append(f"| {created[:10]}")

            with st.expander(" ".join(header_parts)):
                # Show content without frontmatter
                body = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, flags=re.DOTALL)
                st.markdown(body[:3000])

                col1, col2 = st.columns(2)
                if col1.button("✅ Approve", key=f"hitl_approve_{f.name}", type="primary"):
                    move_file(f, "Approved")
                    st.toast(f"Approved: {f.name}")
                    st.rerun()
                if col2.button("❌ Reject", key=f"hitl_reject_{f.name}"):
                    move_file(f, "Rejected")
                    st.toast(f"Rejected: {f.name}")
                    st.rerun()


# ===================================================================
# PAGE: Completed Work
# ===================================================================
elif page == "Completed Work":
    st.header("Completed Work")

    files = _real_files(VAULT / "Done")
    md_files = [f for f in files if f.suffix == ".md"]
    img_files = [f for f in files if f.suffix in (".png", ".jpg", ".jpeg")]

    st.metric("Total Completed", len(files))

    search = st.text_input("🔍 Filter by filename", "")

    display = md_files
    if search:
        display = [f for f in display if search.lower() in f.name.lower()]

    st.caption(f"Showing {len(display)} markdown file(s)")
    for f in display[:50]:  # cap at 50 for performance
        icon = file_type_icon(f.name)
        with st.expander(f"{icon} {f.name}"):
            content = f.read_text(encoding="utf-8", errors="replace")
            st.markdown(content[:2000])
            # Check for proof screenshots
            proof = f.parent / f"{f.stem}_proof.png"
            if proof.exists():
                st.image(str(proof), caption="Proof screenshot", width=400)


# ===================================================================
# PAGE: Activity Logs
# ===================================================================
elif page == "Activity Logs":
    st.header("Activity Logs")

    log_dir = VAULT / "Logs"
    md_logs = sorted(log_dir.glob("*.md"), reverse=True)
    json_logs = sorted(log_dir.glob("*.json"), reverse=True)

    available_dates = []
    for f in md_logs:
        try:
            available_dates.append(datetime.strptime(f.stem, "%Y-%m-%d").date())
        except ValueError:
            pass

    if available_dates:
        selected = st.date_input("Select date", value=available_dates[0], min_value=min(available_dates), max_value=max(available_dates))

        # Activity log (.md)
        md_file = log_dir / f"{selected}.md"
        if md_file.exists():
            st.subheader(f"Activity Log — {selected}")
            content = md_file.read_text(encoding="utf-8")
            lines = [l for l in content.splitlines() if l.startswith("- [")]
            for line in lines:
                # Parse: - [HH:MM:SS] **action**: details
                m = re.match(r"- \[(\d{2}:\d{2}:\d{2})\] \*\*(\w+)\*\*: (.+)", line)
                if m:
                    time_str, action, details = m.groups()
                    st.markdown(f"`{time_str}` **{action}** — {details}")
                else:
                    st.markdown(line)
        else:
            st.info(f"No activity log for {selected}")

        # Audit log (.json)
        json_file = log_dir / f"{selected}.json"
        if json_file.exists():
            st.subheader(f"Audit Log — {selected}")
            entries = []
            for line in json_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            if entries:
                import pandas as pd
                df = pd.DataFrame(entries)
                st.dataframe(df, use_container_width=True)
    else:
        st.info("No log files found.")


# ===================================================================
# PAGE: CEO Briefing
# ===================================================================
elif page == "CEO Briefing":
    st.header("CEO Briefing")

    briefing_dir = VAULT / "Briefings"
    briefings = sorted(
        [f for f in briefing_dir.glob("*.md") if f.name != ".gitkeep"],
        reverse=True,
    )

    if briefings:
        tabs = st.tabs([f.stem for f in briefings[:5]])
        for tab, f in zip(tabs, briefings[:5]):
            with tab:
                content = f.read_text(encoding="utf-8")
                st.markdown(content)
    else:
        st.info("No briefings generated yet.")
