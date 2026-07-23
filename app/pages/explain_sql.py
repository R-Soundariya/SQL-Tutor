"""Explain SQL page: paste any SELECT/WITH query and get a clause-by-clause
breakdown, logical execution order, business meaning, output description,
and complexity notes - plus a live result preview if grounded in a loaded
sandbox dataset."""

import logging

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.query_runner import UnsafeQueryError, run_read_only_query
from app.core.db.sandbox.loader import get_schema_ddl
from app.core.db.sandbox.schema import DATASETS
from app.core.explain.explainer import ExplanationError, explain_query
from app.core.llm.factory import get_llm_provider

logger = logging.getLogger(__name__)

_NO_DATASET = "None / Generic"

st.title("Explain SQL")
st.caption("Paste a query and get a clause-by-clause explanation, execution order, and business meaning.")

dataset_options = [_NO_DATASET] + list(DATASETS.keys())
dataset_choice = st.selectbox(
    "Context dataset (optional)",
    options=dataset_options,
    format_func=lambda key: _NO_DATASET if key == _NO_DATASET else DATASETS[key].display_name,
)
st.caption(
    "Optional: pick a sandbox dataset to ground the explanation in real table/column "
    "names and get a live output preview. Leave as 'None / Generic' to explain any SQL as-is."
)

sql_input = st.text_area(
    "SQL query",
    height=180,
    placeholder="SELECT department_id, AVG(salary) FROM hr_employees GROUP BY department_id;",
)

if st.button("Explain this query", type="primary"):
    if not sql_input.strip():
        st.warning("Paste a query first.")
    else:
        schema_ddl = None
        if dataset_choice != _NO_DATASET:
            schema_ddl = "\n\n".join(get_schema_ddl(dataset_choice).values())

        with st.spinner("Explaining..."):
            try:
                llm = get_llm_provider()
                explanation = explain_query(llm, sql_input, schema_ddl=schema_ddl)
                st.session_state["explain_result"] = explanation
                st.session_state["explain_sql"] = sql_input
                st.session_state["explain_dataset_choice"] = dataset_choice
            except (ExplanationError, UnsafeQueryError) as exc:
                st.session_state.pop("explain_result", None)
                st.error(str(exc))

explanation = st.session_state.get("explain_result")
if explanation and st.session_state.get("explain_sql") == sql_input:
    st.divider()

    st.markdown("#### Clause-by-Clause Breakdown")
    for clause in explanation.clauses:
        st.markdown(f"**{clause.clause}**")
        st.write(clause.explanation)

    st.markdown("#### Execution Order")
    for step_number, step in enumerate(explanation.execution_order, start=1):
        st.markdown(f"{step_number}. {step}")

    st.markdown("#### Business Meaning")
    st.write(explanation.business_meaning)

    st.markdown("#### Output")
    st.write(explanation.output_description)

    active_dataset = st.session_state.get("explain_dataset_choice", _NO_DATASET)
    if active_dataset != _NO_DATASET:
        try:
            preview_df = run_read_only_query(st.session_state["explain_sql"])
            st.markdown("**Live preview (from your loaded dataset):**")
            st.dataframe(preview_df, use_container_width=True)
        except (UnsafeQueryError, SQLAlchemyError) as exc:
            st.caption(f"Could not run a live preview — is the dataset loaded? {exc}")

    st.markdown("#### Complexity Notes")
    st.write(explanation.complexity_notes)
