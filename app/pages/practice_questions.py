"""Practice Questions page: generate an AI interview question for a chosen
dataset/topic/difficulty/company, answer it against real sandbox data, and
get AI-graded feedback (score, mistakes, suggestions)."""

import logging

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.comparison import results_match
from app.core.db.query_runner import UnsafeQueryError, run_read_only_query
from app.core.db.sandbox.schema import DATASETS
from app.core.llm.factory import get_llm_provider
from app.core.practice.constants import COMPANIES, DIFFICULTIES, TOPICS
from app.core.practice.evaluator import EvaluationError, evaluate_answer
from app.core.practice.question_generator import QuestionGenerationError, generate_question

logger = logging.getLogger(__name__)

st.title("Practice Questions")
st.caption("Generate a realistic SQL interview question, answer it, and get AI-graded feedback.")

col1, col2, col3, col4 = st.columns(4)
dataset_id = col1.selectbox(
    "Dataset", options=list(DATASETS.keys()), format_func=lambda key: DATASETS[key].display_name
)
topic = col2.selectbox("Topic", options=TOPICS)
difficulty = col3.selectbox("Difficulty", options=DIFFICULTIES)
company = col4.selectbox("Company style", options=COMPANIES)

if st.button("Generate question", type="primary"):
    with st.spinner("Generating question..."):
        try:
            llm = get_llm_provider()
            question = generate_question(llm, dataset_id, topic, difficulty, company)
            expected_df = run_read_only_query(question.answer_query)  # sanity-check it actually runs
            st.session_state["practice_question"] = question
            st.session_state["practice_expected_df"] = expected_df
            st.session_state.pop("practice_evaluation", None)
            st.session_state["practice_user_sql"] = ""
        except (QuestionGenerationError, UnsafeQueryError, SQLAlchemyError, ValueError) as exc:
            logger.exception("Question generation failed")
            st.error(f"Couldn't generate a usable question: {exc}\n\nTry again, or pick a different topic/dataset.")

question = st.session_state.get("practice_question")

if question:
    st.divider()
    st.markdown(
        f"**Topic:** {question.topic} &nbsp;·&nbsp; **Difficulty:** {question.difficulty} "
        f"&nbsp;·&nbsp; **Company style:** {question.company}"
    )
    st.info(question.question)
    st.caption(f"Tables: {', '.join(question.relevant_tables)} (dataset: {DATASETS[question.dataset_id].display_name})")

    user_sql = st.text_area("Your SQL answer", height=160, key="practice_user_sql")

    if st.button("Submit answer"):
        expected_df = st.session_state["practice_expected_df"]
        user_df = None
        user_error = None
        try:
            user_df = run_read_only_query(user_sql)
        except (UnsafeQueryError, SQLAlchemyError) as exc:
            user_error = str(exc)

        outputs_match = results_match(user_df, expected_df) if user_df is not None else False

        if user_error:
            st.error(f"Your query failed to run: {user_error}")
        else:
            st.markdown("**Your output**")
            st.dataframe(user_df, use_container_width=True)

        with st.spinner("Grading your answer..."):
            try:
                llm = get_llm_provider()
                evaluation = evaluate_answer(
                    llm=llm,
                    question=question,
                    user_query=user_sql,
                    user_query_error=user_error,
                    user_result=user_df,
                    expected_result=expected_df,
                    outputs_match=outputs_match,
                )
                st.session_state["practice_evaluation"] = evaluation
            except EvaluationError as exc:
                st.session_state.pop("practice_evaluation", None)
                st.error(f"Couldn't grade your answer: {exc}")

    evaluation = st.session_state.get("practice_evaluation")
    if evaluation:
        st.divider()
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

        with st.expander("Show expected output & model answer"):
            st.dataframe(st.session_state["practice_expected_df"], use_container_width=True)
            st.code(question.answer_query, language="sql")
