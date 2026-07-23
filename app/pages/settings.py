"""Settings page: shows current configuration and lets the user verify
that the database and LLM provider are reachable before using the rest
of the app."""

import streamlit as st

from app.core.config import get_settings
from app.core.db.engine import test_connection

st.title("Settings")

settings = get_settings()

st.subheader("LLM Provider")
st.write(f"Active provider: `{settings.llm_provider}`")

anthropic_key_set = bool(settings.anthropic_api_key)
openai_key_set = bool(settings.openai_api_key)

col1, col2 = st.columns(2)
with col1:
    st.metric("Anthropic API key", "Set" if anthropic_key_set else "Missing")
    st.caption(f"Model: `{settings.anthropic_model}`")
with col2:
    st.metric("OpenAI API key", "Set" if openai_key_set else "Missing")
    st.caption(f"Model: `{settings.openai_model}`")

active_key_set = anthropic_key_set if settings.llm_provider == "anthropic" else openai_key_set
if not active_key_set:
    st.warning(
        f"No API key found for the active provider ('{settings.llm_provider}'). "
        "Add it to your .env file."
    )

st.divider()

st.subheader("Database")
st.write(f"Host: `{settings.db_host}:{settings.db_port}`  |  Database: `{settings.db_name}`")

if st.button("Test database connection"):
    with st.spinner("Connecting..."):
        success, message = test_connection()
    if success:
        st.success(message)
    else:
        st.error(f"Connection failed: {message}")
