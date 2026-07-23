"""Home page: product overview and quick links."""

import streamlit as st

st.title("SQL Interview Coach AI")
st.subheader("Your AI-powered SQL interview prep platform")

st.markdown(
    """
Welcome! This app helps you learn SQL, practice interview questions,
get instant AI feedback, optimize queries, and track your progress
over time.

**Use the sidebar to navigate:**
- **Learn SQL** — interactive concept lessons
- **Practice Questions** — topic/difficulty/company-targeted questions
- **Mock Interview** — a full 15-question timed interview
- **Query Optimizer** — paste a query, get performance suggestions
- **Explain SQL** — clause-by-clause breakdown of any query
- **Progress Dashboard** — accuracy, streaks, topic mastery
- **Settings** — configure LLM provider and database connection

*Features are being built incrementally, phase by phase — check back as
new pages come online.*
"""
)
