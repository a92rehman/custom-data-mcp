"""Governance Coverage — which tables have governed query rules."""

import sys as _sys
from pathlib import Path as _Path
_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

import pandas as pd
import streamlit as st

from custom_data_mcp.dashboard.data.projects import (
    get_all_tables,
    get_governance_coverage,
    load_projects,
    format_rows,
)
from custom_data_mcp.dashboard.components.styles import (
    COLORS, inject_page_css, page_header, section_header,
)

inject_page_css()

# -- Header --
page_header("Governance Coverage", "Which BigQuery tables are covered by governed query rules?")

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

section_header("Summary", "purple")
c1, c2, c3, c4 = st.columns(4)

_card_base = (
    "position:relative;background:white;border:1px solid #E2E8F0;border-radius:14px;"
    "padding:16px 18px;text-align:center;min-height:80px;"
    "box-shadow:0 1px 4px rgba(0,0,0,0.04);"
)
_accent = (
    "position:absolute;top:0;left:0;right:0;height:4px;"
    "border-radius:14px 14px 0 0;background:{gradient};"
)

with c1:
    st.markdown(
        f'<div style="{_card_base}">'
        f'<div style="{_accent.format(gradient="linear-gradient(135deg,#3B82F6,#6366F1)")}"></div>'
        f'<div style="font-weight:500;color:#64748B;font-size:0.82rem;">Total Tables</div>'
        f'<div style="font-size:1.55rem;font-weight:700;color:#1E293B;margin:4px 0 0;">{total}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div style="{_card_base}">'
        f'<div style="{_accent.format(gradient="linear-gradient(135deg,#10B981,#14B8A6)")}"></div>'
        f'<div style="font-weight:500;color:#64748B;font-size:0.82rem;">Governed</div>'
        f'<div style="font-size:1.55rem;font-weight:700;color:#065F46;margin:4px 0 0;">{governed_count}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div style="{_card_base}">'
        f'<div style="{_accent.format(gradient="linear-gradient(135deg,#EF4444,#EC4899)")}"></div>'
        f'<div style="font-weight:500;color:#64748B;font-size:0.82rem;">Ungoverned</div>'
        f'<div style="font-size:1.55rem;font-weight:700;color:#991B1B;margin:4px 0 0;">{ungoverned_count}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f'<div style="{_card_base}">'
        f'<div style="{_accent.format(gradient="linear-gradient(135deg,#8B5CF6,#6366F1)")}"></div>'
        f'<div style="font-weight:500;color:#64748B;font-size:0.82rem;">Coverage</div>'
        f'<div style="font-size:1.55rem;font-weight:700;color:#1E293B;margin:4px 0 0;">{coverage_pct}%</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# -- Filters --
section_header("Filters")
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
    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;'
    f'padding:8px 14px;font-size:0.85rem;color:#475569;margin-bottom:0.5rem;">'
    f'Showing <strong>{n_shown}</strong> tables &mdash; '
    f'<span style="color:#065F46;font-weight:600;">{n_gov_shown} governed</span> / '
    f'<span style="color:#991B1B;font-weight:600;">{n_ungov_shown} ungoverned</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# -- Data table --
section_header("Table Details", "teal")

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
