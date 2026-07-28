from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from dpo_system.src import ledger_io

NOTEBOOK_PATHS = {
    "Clause Intelligence Console": "dpo_system/notebooks/clause-intelligence-console.ipynb",
    "Law Ingestion Console": "dpo_system/notebooks/law-ingestion-console.ipynb",
    "Docassemble Governance Console": "dpo_system/notebooks/docassemble-governance-console.ipynb",
    "Orchestrator Console": "dpo_system/notebooks/orchestrator-console.ipynb",
}

QUEUE_SHEETS = {
    "Ingestion Queue": "INGESTION_QUEUE",
    "Clause Queue": "CLAUSE_QUEUE",
    "CRM Queue": "CRM_QUEUE",
    "Governance Queue": "GOVERNANCE_QUEUE",
}

REQUIRED_SHEETS = [
    "REPO_STATE",
    "INGESTION_QUEUE",
    "CLAUSE_QUEUE",
    "CRM_QUEUE",
    "GOVERNANCE_QUEUE",
    "OPERATOR_LOG",
]

REPO_WEB_BASE = "https://github.com/SuffolkLITLab/legal-tech-class/blob/main"


def _load_rows(sheet_name: str) -> list[dict]:
    return ledger_io.read_sheet(sheet_name)


def _status_counter(rows: list[dict], field: str = "status") -> dict[str, int]:
    values = [str(r.get(field, "")).strip() for r in rows if str(r.get(field, "")).strip()]
    return dict(Counter(values))


def _render_table(rows: list[dict], caption: str) -> None:
    st.caption(caption)
    if not rows:
        st.info("No rows found.")
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _repo_file_link(path: str) -> str:
    return f"{REPO_WEB_BASE}/{quote(path)}"


def _render_quick_links() -> None:
    st.markdown("### Quick Links")
    c1, c2 = st.columns(2)
    c1.link_button(
        "Cockpit Runbook",
        "https://github.com/SuffolkLITLab/legal-tech-class/blob/main/dpo_system/dashboard/README.md",
        use_container_width=True,
    )
    c2.link_button(
        "Docassemble Setup Guide",
        "https://github.com/SuffolkLITLab/legal-tech-class/blob/main/docs/practical-guide-docassemble/installing-production-app.md",
        use_container_width=True,
    )

    st.markdown("### Notebook Launch Surfaces")
    c3, c4 = st.columns(2)
    c3.link_button(
        "Clause Intelligence Console",
        _repo_file_link("dpo_system/notebooks/clause-intelligence-console.ipynb"),
        use_container_width=True,
    )
    c4.link_button(
        "Law Ingestion Console",
        _repo_file_link("dpo_system/notebooks/law-ingestion-console.ipynb"),
        use_container_width=True,
    )
    c5, c6 = st.columns(2)
    c5.link_button(
        "Docassemble Governance Console",
        _repo_file_link("dpo_system/notebooks/docassemble-governance-console.ipynb"),
        use_container_width=True,
    )
    c6.link_button(
        "Orchestrator Console",
        _repo_file_link("dpo_system/notebooks/orchestrator-console.ipynb"),
        use_container_width=True,
    )


def _render_wave4_banner() -> None:
    st.markdown(
        """
    <div style="padding: 14px; background-color: #1f1f1f; border-radius: 6px; margin-bottom: 12px;">
        <h3 style="color: #ffffff; margin-bottom: 6px;">Wave 4 - Read-Only Operator Mode</h3>
        <p style="color: #cccccc; margin: 0;">
            No Execution - No Ingestion - No External Calls - No Telephony<br>
            Ledger-Only Data Source - Control-Plane Visibility Only
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_ledger_health() -> None:
    try:
        workbook = ledger_io.safe_load_workbook()
    except Exception as exc:
        st.error(f"Ledger Health: unable to open ledger: {exc}")
        return

    present_sheets = workbook.sheetnames
    missing_sheets = [name for name in REQUIRED_SHEETS if name not in present_sheets]
    if missing_sheets:
        st.error(f"Ledger Health: MISSING sheets -> {missing_sheets}")
    else:
        st.success("Ledger Health: OK - all required sheets present")

    header_issues: list[str] = []
    for sheet_name in REQUIRED_SHEETS:
        if sheet_name not in present_sheets:
            continue
        ws = workbook[sheet_name]
        actual_headers = [cell.value for cell in ws[1]]
        expected_headers = ledger_io.SHEET_HEADERS.get(sheet_name, [])
        if actual_headers != expected_headers:
            header_issues.append(sheet_name)

    if header_issues:
        st.warning(
            "Ledger header integrity issues in: " + ", ".join(sorted(header_issues))
        )
    else:
        st.info("Ledger Header Check: OK")


def _render_cockpit() -> None:
    st.subheader("Operator Cockpit")

    repo_rows = _load_rows("REPO_STATE")
    ingestion_rows = _load_rows("INGESTION_QUEUE")
    clause_rows = _load_rows("CLAUSE_QUEUE")
    crm_rows = _load_rows("CRM_QUEUE")
    gov_rows = _load_rows("GOVERNANCE_QUEUE")
    log_rows = _load_rows("OPERATOR_LOG")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Repos", len(repo_rows))
    c2.metric("Ingestion", len(ingestion_rows))
    c3.metric("Clause", len(clause_rows))
    c4.metric("CRM", len(crm_rows))
    c5.metric("Governance", len(gov_rows))
    c6.metric("Audit Logs", len(log_rows))

    st.markdown("### Queue Status Overview")
    queue_status = {
        "INGESTION_QUEUE": _status_counter(ingestion_rows),
        "CLAUSE_QUEUE": _status_counter(clause_rows),
        "CRM_QUEUE": _status_counter(crm_rows),
        "GOVERNANCE_QUEUE": _status_counter(gov_rows),
    }
    st.json(queue_status)

    st.markdown("### Recent Operator Log Entries")
    tail = log_rows[-20:] if log_rows else []
    _render_table(tail, "Last 20 OPERATOR_LOG rows")


def _render_repo_control() -> None:
    st.subheader("Repo Control")
    rows = _load_rows("REPO_STATE")

    needs_update = [r for r in rows if str(r.get("status", "")).strip() == "NEEDS_UPDATE"]
    st.metric("Repos Needing Update", len(needs_update))

    _render_table(rows, "REPO_STATE")


def _render_queue_center() -> None:
    st.subheader("Queue Command Center")

    queue_name = st.selectbox("Queue", list(QUEUE_SHEETS.keys()))
    sheet_name = QUEUE_SHEETS[queue_name]

    rows = _load_rows(sheet_name)
    st.json({"status_counts": _status_counter(rows)})
    _render_table(rows, sheet_name)


def _render_audit() -> None:
    st.subheader("Audit and Governance")
    rows = _load_rows("OPERATOR_LOG")

    status_counts = _status_counter(rows)
    st.json({"operator_log_status": status_counts})
    _render_table(rows, "OPERATOR_LOG")


def _render_runbooks() -> None:
    st.subheader("Runbooks and Navigation")
    st.markdown("Use these notebook anchors for Wave 4 orchestration-only operations.")

    for label, path in NOTEBOOK_PATHS.items():
        exists = Path(path).exists()
        repo_link = _repo_file_link(path)
        status = "found" if exists else "missing"
        st.markdown(f"- [{label}]({repo_link}) - {status}")

    st.markdown("### Helpful Links")
    st.markdown(
        "- [Dashboard README](https://github.com/SuffolkLITLab/legal-tech-class/blob/main/dpo_system/dashboard/README.md)"
    )
    st.markdown(
        "- [Ledger I/O Module](https://github.com/SuffolkLITLab/legal-tech-class/blob/main/dpo_system/src/ledger_io.py)"
    )
    st.markdown(
        "- [Operator Actions Module](https://github.com/SuffolkLITLab/legal-tech-class/blob/main/dpo_system/src/operator_actions.py)"
    )

    st.markdown("### Operating Boundaries")
    st.write("- Read-only dashboard")
    st.write("- No ingestion execution")
    st.write("- No external API calls")
    st.write("- No outbound automation")


def main() -> None:
    st.set_page_config(
        page_title="LAW LAB Operator Cockpit",
        page_icon="LL",
        layout="wide",
    )

    _render_wave4_banner()
    _render_ledger_health()

    st.title("LAW LAB Operator Cockpit")
    st.caption("Wave 4 governance surface: read-only visibility over ledger state.")
    _render_quick_links()

    try:
        sheets = ledger_io.list_sheets()
    except FileNotFoundError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Failed to load ledger: {exc}")
        return

    st.sidebar.header("Navigation")
    page = st.sidebar.radio(
        "Page",
        [
            "Cockpit",
            "Repo Control",
            "Queue Command Center",
            "Audit and Governance",
            "Runbooks and Navigation",
        ],
    )

    st.sidebar.markdown("### Ledger")
    st.sidebar.write(str(ledger_io.LEDGER_PATH))
    st.sidebar.write(f"Sheets: {', '.join(sheets)}")
    st.sidebar.info("Read-only dashboard. No queue mutations from UI.")
    st.sidebar.markdown("### Quick Links")
    st.sidebar.markdown(
        "[Cockpit Runbook](https://github.com/SuffolkLITLab/legal-tech-class/blob/main/dpo_system/dashboard/README.md)"
    )
    st.sidebar.markdown(
        "[Docassemble Setup Guide](https://github.com/SuffolkLITLab/legal-tech-class/blob/main/docs/practical-guide-docassemble/installing-production-app.md)"
    )

    if page == "Cockpit":
        _render_cockpit()
    elif page == "Repo Control":
        _render_repo_control()
    elif page == "Queue Command Center":
        _render_queue_center()
    elif page == "Audit and Governance":
        _render_audit()
    else:
        _render_runbooks()


if __name__ == "__main__":
    main()
