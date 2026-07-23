"""Daily Challenge page: one AI-generated question per calendar day (same
question all day for everyone), a live timer, submission grading, and a
full clause-by-clause explanation of the model answer afterward."""

import logging
import time
from datetime import date

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from app.core.daily_challenge.provider import get_or_create_daily_challenge
from app.core.db.comparison import results_match
from app.core.db.query_runner import UnsafeQueryError, run_read_only_query
from app.core.db.sandbox.loader import get_schema_ddl
from app.core.db.sandbox.schema import DATASETS
from app.core.explain.explainer import ExplanationError, explain_query
from app.core.llm.factory import get_llm_provider
from app.core.practice.evaluator import EvaluationError, evaluate_answer
from app.core.practice.models import GeneratedQuestion
from app.core.practice.question_generator import QuestionGenerationError
from app.core.progress.recorder import record_attempt
from app.ui.hint_section import render_hint_section

logger = logging.getLogger(__name__)

st.title("Daily Challenge")
st.caption("One new SQL question every day — the same question for everyone, all day.")

today = date.today()

if st.session_state.get("daily_challenge_date") != today:
    for key in list(st.session_state.keys()):
        if key.startswith("daily_"):
            del st.session_state[key]
    st.session_state["daily_challenge_date"] = today

if "daily_challenge_data" not in st.session_state:
    with st.spinner("Loading today's challenge..."):
        try:
            llm = get_llm_provider()
            challenge = get_or_create_daily_challenge(llm, today)
            st.session_state["daily_challenge_data"] = challenge
            st.session_state["daily_start_time"] = time.time()
        except (QuestionGenerationError, SQLAlchemyError, ValueError) as exc:
            logger.exception("Daily challenge could not be loaded")
            st.error(f"Couldn't load today's challenge: {exc}")
            st.button("Try again")

challenge = st.session_state.get("daily_challenge_data")


@st.fragment(run_every="1s")
def _live_timer(start_time: float) -> None:
    elapsed = int(time.time() - start_time)
    st.caption(f"Time elapsed: {elapsed // 60:02d}:{elapsed % 60:02d}")


if challenge:
    dataset = DATASETS[challenge.dataset_id]
    st.markdown(f"**{today.strftime('%A, %B %d, %Y')}**")
    st.markdown(f"**Topic:** {challenge.topic} &nbsp;·&nbsp; **Difficulty:** {challenge.difficulty}")
    st.info(challenge.question_text)
    st.caption(f"Dataset: {dataset.display_name} — load it from Database Sandbox if you haven't already.")

    evaluation = st.session_state.get("daily_evaluation")

    if evaluation is None:
        _live_timer(st.session_state["daily_start_time"])
    else:
        elapsed_seconds = st.session_state.get("daily_elapsed_seconds", 0)
        st.caption(f"Completed in {elapsed_seconds // 60:02d}:{elapsed_seconds % 60:02d}")

    user_sql = st.text_area("Your SQL answer", height=150, key="daily_user_sql")

    render_hint_section(
        state_key=f"daily_{today.isoformat()}",
        question_text=challenge.question_text,
        schema_ddl="\n\n".join(get_schema_ddl(challenge.dataset_id).values()),
        answer_query=challenge.answer_query,
        current_attempt=user_sql,
    )

    if evaluation is None:
        if st.button("Submit answer", type="primary"):
            elapsed_seconds = int(time.time() - st.session_state["daily_start_time"])
            user_df, user_error = None, None
            try:
                user_df = run_read_only_query(user_sql)
            except (UnsafeQueryError, SQLAlchemyError) as exc:
                user_error = str(exc)

            try:
                expected_df = run_read_only_query(challenge.answer_query)
            except SQLAlchemyError as exc:
                st.error(f"Could not compute the expected output — is the dataset loaded? {exc}")
                st.stop()

            outputs_match = results_match(user_df, expected_df) if user_df is not None else False

            question_for_eval = GeneratedQuestion(
                question=challenge.question_text,
                topic=challenge.topic,
                difficulty=challenge.difficulty,
                company=challenge.company,
                dataset_id=challenge.dataset_id,
                relevant_tables=tuple(table.name for table in dataset.tables),
                answer_query=challenge.answer_query,
            )

            with st.spinner("Grading..."):
                try:
                    llm = get_llm_provider()
                    evaluation = evaluate_answer(
                        llm=llm,
                        question=question_for_eval,
                        user_query=user_sql,
                        user_query_error=user_error,
                        user_result=user_df,
                        expected_result=expected_df,
                        outputs_match=outputs_match,
                    )
                    st.session_state["daily_evaluation"] = evaluation
                    st.session_state["daily_elapsed_seconds"] = elapsed_seconds
                    st.session_state["daily_expected_df"] = expected_df
                    record_attempt(
                        source="daily_challenge",
                        topic=challenge.topic,
                        difficulty=challenge.difficulty,
                        dataset_id=challenge.dataset_id,
                        is_correct=evaluation.is_correct,
                        score=evaluation.score,
                    )
                    st.rerun()
                except EvaluationError as exc:
                    st.error(f"Couldn't grade your answer: {exc}")
    else:
        if evaluation.is_correct:
            st.success(f"Correct — Score: {evaluation.score}/10")
        else:
            st.warning(f"Not quite — Score: {evaluation.score}/10")
        st.write(evaluation.summary)

        if evaluation.mistakes:
            st.markdown("**Mistakes**")
            for mistake in evaluation.mistakes:
                st.markdown(f"- {mistake}")

        if evaluation.suggestions:
            st.markdown("**Suggestions**")
            for suggestion in evaluation.suggestions:
                st.markdown(f"- {suggestion}")

        st.markdown("**Expected output**")
        st.dataframe(st.session_state["daily_expected_df"], use_container_width=True)

        if st.button("Explain the model answer"):
            with st.spinner("Explaining..."):
                try:
                    llm = get_llm_provider()
                    schema_ddl = "\n\n".join(get_schema_ddl(challenge.dataset_id).values())
                    explanation = explain_query(llm, challenge.answer_query, schema_ddl=schema_ddl)
                    st.session_state["daily_explanation"] = explanation
                except ExplanationError as exc:
                    st.error(f"Couldn't explain the answer: {exc}")

        explanation = st.session_state.get("daily_explanation")
        if explanation:
            st.markdown("#### Clause-by-Clause Breakdown")
            for clause in explanation.clauses:
                st.markdown(f"**{clause.clause}**")
                st.write(clause.explanation)

            st.markdown("#### Business Meaning")
            st.write(explanation.business_meaning)
