"""Query Optimizer page: paste a query, see deterministic static findings
immediately, then get an AI-generated rewrite, index recommendations, and
performance notes - grounded in a real MySQL EXPLAIN plan when a sandbox
dataset context is available."""

import logging

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.explain_plan import get_explain_plan
from app.core.db.query_runner import UnsafeQueryError
from app.core.db.sandbox.loader import get_schema_ddl
from app.core.db.sandbox.schema import DATASETS
from app.core.llm.factory import get_llm_provider
from app.core.optimizer.optimizer import OptimizationError, optimize_query
from app.core.optimizer.static_analysis import analyze_query

logger = logging.getLogger(__name__)

_NO_DATASET = "None / Generic"
_SEVERITY_RENDER = {"critical": st.error, "warning": st.warning, "info": st.info}

st.title("Query Optimizer")
st.caption("Paste a query and get static analysis findings plus an AI-suggested rewrite.")

dataset_options = [_NO_DATASET] + list(DATASETS.keys())
dataset_choice = st.selectbox(
    "Context dataset (optional)",
    options=dataset_options,
    format_func=lambda key: _NO_DATASET if key == _NO_DATASET else DATASETS[key].display_name,
)
st.caption(
    "Optional: pick a loaded sandbox dataset to ground recommendations in a real "
    "MySQL EXPLAIN plan. Leave as 'None / Generic' for static + AI analysis only."
)

sql_input = st.text_area(
    "SQL query to optimize",
    height=180,
    placeholder="SELECT * FROM ecom_orders WHERE YEAR(order_date) = 2025;",
)

if st.button("Analyze query", type="primary"):
    if not sql_input.strip():
        st.warning("Paste a query first.")
    else:
        st.session_state["optimizer_sql"] = sql_input
        st.session_state["optimizer_static_findings"] = analyze_query(sql_input)
        st.session_state.pop("optimizer_result", None)
        st.session_state.pop("optimizer_explain_plan", None)

        explain_plan_df = None
        if dataset_choice != _NO_DATASET:
            try:
                explain_plan_df = get_explain_plan(sql_input)
                st.session_state["optimizer_explain_plan"] = explain_plan_df
            except (UnsafeQueryError, SQLAlchemyError) as exc:
                st.caption(f"Could not fetch a live EXPLAIN plan: {exc}")

        with st.spinner("Getting AI recommendations..."):
            try:
                llm = get_llm_provider()
                schema_ddl = (
                    "\n\n".join(get_schema_ddl(dataset_choice).values()) if dataset_choice != _NO_DATASET else None
                )
                explain_text = explain_plan_df.to_string(index=False) if explain_plan_df is not None else None
                result = optimize_query(
                    llm,
                    sql_input,
                    static_findings=st.session_state["optimizer_static_findings"],
                    schema_ddl=schema_ddl,
                    explain_plan_text=explain_text,
                )
                st.session_state["optimizer_result"] = result
            except OptimizationError as exc:
                st.error(f"Couldn't get AI recommendations: {exc}")

if st.session_state.get("optimizer_sql") == sql_input and "optimizer_static_findings" in st.session_state:
    static_findings = st.session_state["optimizer_static_findings"]

    st.divider()
    st.markdown("#### Static Analysis Findings")
    if static_findings:
        for finding in static_findings:
            render = _SEVERITY_RENDER.get(finding.severity, st.info)
            render(f"**[{finding.category}]** {finding.message}")
    else:
        st.success("No obvious static issues found.")

    explain_plan_df = st.session_state.get("optimizer_explain_plan")
    if explain_plan_df is not None:
        st.markdown("#### Live EXPLAIN Plan")
        st.dataframe(explain_plan_df, use_container_width=True)

    result = st.session_state.get("optimizer_result")
    if result:
        st.markdown("#### Suggested Rewrite")
        st.code(result.rewritten_query, language="sql")

        st.markdown("#### Performance Notes")
        st.write(result.performance_notes)

        if result.index_recommendations:
            st.markdown("#### Index Recommendations")
            for recommendation in result.index_recommendations:
                st.code(recommendation, language="sql")

        st.markdown("#### Estimated Impact")
        st.write(result.estimated_impact)
