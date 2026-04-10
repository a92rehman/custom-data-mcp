"""Governance Coverage — which tables have governed query rules."""

import sys as _sys
from pathlib import Path as _Path
_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.data.projects import (
    get_all_tables,
    get_governance_coverage,
    load_projects,
    format_rows,
)

# -- Custom CSS --
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Fira Sans', system-ui, sans-serif; }
    .block-container { padding-top: 1.2rem; padding-bottom: 0.5rem; }

    .kpi-card {
        background: white; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 16px 18px; text-align: center; min-height: 80px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .kpi-card .kpi-label { font-weight: 500; color: #64748B; font-size: 0.82rem; }
    .kpi-card .kpi-value { font-size: 1.55rem; font-weight: 700; color: #1E293B; margin: 4px 0 0; }

    .section-header {
        font-size: 0.95rem; font-weight: 600; color: #1E293B;
        margin: 0.6rem 0 0.3rem; border-bottom: 2px solid #3B82F6;
        padding-bottom: 0.2rem;
    }

    .summary-bar {
        background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;
        padding: 8px 14px; font-size: 0.85rem; color: #475569;
        margin-bottom: 0.5rem;
    }
    .summary-bar .governed { color: #16A34A; font-weight: 600; }
    .summary-bar .ungoverned { color: #DC2626; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# -- Header --
st.title("Governance Coverage")
st.caption(
    "Which BigQuery tables are covered by governed query rules? "
    "Governed tables have explicit query definitions in .claude/rules/ — "
    "ungoverned tables have no rule file and should not be queried ad-hoc."
)

# -- Load data --
projects = load_projects()
active_projects = [p for p in projects if p.get("status") == "active" and p.get("dataset")]
datasets = list({p["dataset"] for p in active_projects})

if not datasets:
    st.warning(
        "No active projects with datasets found. "
        "Check that projects.yaml has entries with status: active and a dataset field."
    )
    st.stop()

with st.spinner("Loading table metadata from BigQuery..."):
    try:
        tables_df = get_all_tables(datasets)
    except Exception as e:
        st.error(f"Could not load table list from BigQuery: {e}")
        st.stop()

if tables_df.empty:
    st.warning("No tables found for the active datasets. Check BigQuery permissions.")
    st.stop()

with st.spinner("Loading governance map..."):
    try:
        gov_map = get_governance_coverage()
    except Exception as e:
        st.error(f"Could not load governance map: {e}")
        st.stop()

# -- Join governance data --
def _governed_info(row: pd.Series) -> tuple[bool, str, str]:
    """Return (governed, rule_file, domain) for a table row."""
    key = (row["dataset"], row["table_name"])
    info = gov_map.get(key)
    if info:
        rule_files = info.get("rule_files", [])
        rule_file_str = ", ".join(rule_files) if rule_files else info.get("rule_file", "")
        domain = info.get("domain", "")
        return True, rule_file_str, domain
    return False, "", ""

governed_col, rule_col, domain_col = zip(*tables_df.apply(_governed_info, axis=1))
tables_df = tables_df.copy()
tables_df["governed"] = governed_col
tables_df["rule_file"] = rule_col
tables_df["domain"] = domain_col

# -- KPI row --
total = len(tables_df)
governed_count = int(tables_df["governed"].sum())
ungoverned_count = total - governed_count
coverage_pct = round(governed_count / total * 100, 1) if total > 0 else 0.0

st.markdown('<p class="section-header">Summary</p>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">Total Tables</div>'
        f'<div class="kpi-value">{total}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">Governed</div>'
        f'<div class="kpi-value" style="color:#16A34A">{governed_count}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">Ungoverned</div>'
        f'<div class="kpi-value" style="color:#DC2626">{ungoverned_count}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">Coverage</div>'
        f'<div class="kpi-value">{coverage_pct}%</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# -- Filters --
st.markdown('<p class="section-header">Filters</p>', unsafe_allow_html=True)
f1, f2 = st.columns(2)

with f1:
    dataset_options = ["All datasets"] + sorted(datasets)
    selected_dataset = st.selectbox("Dataset", options=dataset_options, key="gov_dataset")

with f2:
    status_options = ["All", "Governed only", "Ungoverned only"]
    selected_status = st.selectbox("Governed status", options=status_options, key="gov_status")

# -- Apply filters --
filtered = tables_df.copy()

if selected_dataset != "All datasets":
    filtered = filtered[filtered["dataset"] == selected_dataset]

if selected_status == "Governed only":
    filtered = filtered[filtered["governed"]]
elif selected_status == "Ungoverned only":
    filtered = filtered[~filtered["governed"]]

n_shown = len(filtered)
n_gov_shown = int(filtered["governed"].sum())
n_ungov_shown = n_shown - n_gov_shown

# -- Summary bar --
st.markdown(
    f'<div class="summary-bar">'
    f'Showing <strong>{n_shown}</strong> tables — '
    f'<span class="governed">{n_gov_shown} governed</span> / '
    f'<span class="ungoverned">{n_ungov_shown} ungoverned</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# -- Data table --
st.markdown('<p class="section-header">Table Details</p>', unsafe_allow_html=True)

display_df = filtered[["dataset", "table_name", "row_count", "governed", "rule_file", "domain"]].copy()
display_df["row_count"] = display_df["row_count"].apply(
    lambda x: format_rows(int(x)) if pd.notna(x) else "—"
)
display_df["governed"] = display_df["governed"].apply(lambda x: "Yes" if x else "No")

display_df.columns = ["Dataset", "Table", "Rows", "Governed", "Rule File", "Domain"]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Dataset": st.column_config.TextColumn("Dataset", width="small"),
        "Table": st.column_config.TextColumn("Table", width="medium"),
        "Rows": st.column_config.TextColumn("Rows", width="small"),
        "Governed": st.column_config.TextColumn("Governed", width="small"),
        "Rule File": st.column_config.TextColumn("Rule File", width="large"),
        "Domain": st.column_config.TextColumn("Domain", width="small"),
    },
)
