"""Streamlit entry point: configures logging and wires up page navigation."""

import streamlit as st

from app.core.logging_config import setup_logging

setup_logging()

st.set_page_config(page_title="SQL Interview Coach AI", page_icon=":bar_chart:", layout="wide")

pages = [
    st.Page("pages/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("pages/daily_challenge.py", title="Daily Challenge", icon=":material/today:"),
    st.Page("pages/database_sandbox.py", title="Database Sandbox", icon=":material/storage:"),
    st.Page("pages/learn_sql.py", title="Learn SQL", icon=":material/school:"),
    st.Page("pages/practice_questions.py", title="Practice Questions", icon=":material/quiz:"),
    st.Page("pages/mock_interview.py", title="Mock Interview", icon=":material/mic:"),
    st.Page("pages/query_optimizer.py", title="Query Optimizer", icon=":material/speed:"),
    st.Page("pages/explain_sql.py", title="Explain SQL", icon=":material/lightbulb:"),
    st.Page("pages/progress_dashboard.py", title="Progress Dashboard", icon=":material/insights:"),
    st.Page("pages/settings.py", title="Settings", icon=":material/settings:"),
]

navigation = st.navigation(pages)
navigation.run()
