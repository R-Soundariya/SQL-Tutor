"""Database Sandbox page: load seeded practice datasets and query them
directly. Backs Feature 10 (Database Sandbox) and doubles as the primary
way to verify Phase 2's data layer end-to-end."""

import logging

import pandas as pd
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.engine import get_engine
from app.core.db.query_runner import UnsafeQueryError, run_read_only_query
from app.core.db.sandbox.loader import get_schema_ddl, load_dataset
from app.core.db.sandbox.schema import DATASETS

logger = logging.getLogger(__name__)

st.title("Database Sandbox")
st.caption("Load a seeded practice dataset, inspect its schema, and run your own SQL against it.")

dataset_id = st.selectbox(
    "Dataset",
    options=list(DATASETS.keys()),
    format_func=lambda key: DATASETS[key].display_name,
)
dataset = DATASETS[dataset_id]
st.write(dataset.description)

if st.button("Load / Reset sample data for this dataset", type="primary"):
    with st.spinner(f"Loading '{dataset.display_name}'..."):
        try:
            counts = load_dataset(dataset_id)
            st.success(
                "Loaded: " + ", ".join(f"{table} ({n} rows)" for table, n in counts.items())
            )
        except SQLAlchemyError as exc:
            logger.exception("Failed to load dataset '%s'", dataset_id)
            st.error(f"Could not load data. Check your database connection in Settings.\n\n{exc}")

schema_tab, preview_tab, query_tab = st.tabs(["Schema", "Preview Data", "Run a Query"])

with schema_tab:
    for table in dataset.tables:
        st.markdown(f"**`{table.name}`**")
        st.code(get_schema_ddl(dataset_id)[table.name], language="sql")

with preview_tab:
    engine = get_engine()
    for table in dataset.tables:
        st.markdown(f"**`{table.name}`**")
        try:
            df = pd.read_sql(f"SELECT * FROM {table.name} LIMIT 50", engine)
            st.dataframe(df, use_container_width=True)
        except SQLAlchemyError:
            st.info("Not loaded yet. Click 'Load / Reset sample data' above.")

with query_tab:
    st.caption("Only SELECT / WITH ... SELECT statements are allowed. Results are capped at 200 rows.")
    default_table = dataset.tables[0].name
    sql_input = st.text_area(
        "SQL query",
        value=f"SELECT * FROM {default_table} LIMIT 10",
        height=150,
    )
    if st.button("Run query"):
        try:
            result_df = run_read_only_query(sql_input)
            st.dataframe(result_df, use_container_width=True)
            st.caption(f"{len(result_df)} row(s) returned.")
        except UnsafeQueryError as exc:
            st.error(str(exc))
        except SQLAlchemyError as exc:
            st.error(f"Query failed: {exc}")
