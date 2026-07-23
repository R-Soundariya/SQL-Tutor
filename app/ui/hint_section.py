"""Reusable Streamlit UI block: progressive AI hints for a practice
question. Shared by Learn SQL and Practice Questions so hint behavior
stays consistent everywhere a user can get stuck."""

import streamlit as st

from app.core.hints.generator import HintGenerationError, generate_hints
from app.core.llm.factory import get_llm_provider


def render_hint_section(
    state_key: str,
    question_text: str,
    schema_ddl: str,
    answer_query: str,
    current_attempt: str,
) -> None:
    """Render a 'Get a hint' control that reveals up to 3 progressive hints.

    All 3 hints are generated in a single LLM call on first request, then
    revealed one at a time on later clicks (no extra calls needed).
    `state_key` must be unique per question instance so hints reset when
    the underlying question changes.
    """
    hints_state_key = f"hints_{state_key}"
    revealed_state_key = f"hints_revealed_{state_key}"
    revealed_count = st.session_state.get(revealed_state_key, 0)

    with st.expander("Need a hint?"):
        if revealed_count == 0:
            if st.button("Get hint 1", key=f"hint_button_{state_key}"):
                try:
                    llm = get_llm_provider()
                    hints = generate_hints(
                        llm=llm,
                        question_text=question_text,
                        schema_ddl=schema_ddl,
                        answer_query=answer_query,
                        user_attempt=current_attempt,
                    )
                    st.session_state[hints_state_key] = hints
                    st.session_state[revealed_state_key] = 1
                    st.rerun()
                except HintGenerationError as exc:
                    st.error(f"Couldn't generate a hint: {exc}")
        else:
            hints = st.session_state[hints_state_key]
            for i in range(revealed_count):
                st.markdown(f"**Hint {i + 1}:** {hints[i]}")
            if revealed_count < 3:
                if st.button(f"Get hint {revealed_count + 1}", key=f"hint_button_{state_key}_{revealed_count}"):
                    st.session_state[revealed_state_key] = revealed_count + 1
                    st.rerun()
