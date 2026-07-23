"""Mock Interview page: a full 15-question SQL interview with gradually
increasing difficulty, AI grading per question, and an aggregate
strengths/weaknesses/learning-path report at the end."""

import dataclasses
import logging

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.comparison import results_match
from app.core.db.query_runner import UnsafeQueryError, run_read_only_query
from app.core.db.sandbox.loader import get_schema_ddl
from app.core.db.sandbox.schema import DATASETS
from app.core.llm.factory import get_llm_provider
from app.core.practice.constants import COMPANIES
from app.core.practice.evaluator import EvaluationError, evaluate_answer
from app.core.practice.mock_interview import NUM_QUESTIONS, difficulty_for_index, topic_for_index
from app.core.practice.models import InterviewQuestionRecord
from app.core.practice.question_generator import QuestionGenerationError, generate_question
from app.core.practice.report_generator import InterviewReportError, generate_interview_report
from app.core.progress.recorder import record_attempt
from app.ui.hint_section import render_hint_section

logger = logging.getLogger(__name__)

st.title("Mock Interview")
st.caption(f"A full {NUM_QUESTIONS}-question SQL interview with gradually increasing difficulty and a final report.")

if not st.session_state.get("mock_active"):
    st.markdown(
        f"You'll get {NUM_QUESTIONS} questions — Beginner, then Intermediate, then Advanced — each "
        "graded individually. At the end you'll get a strengths/weaknesses report and a "
        "recommended learning path."
    )
    dataset_id = st.selectbox(
        "Dataset", options=list(DATASETS.keys()), format_func=lambda key: DATASETS[key].display_name
    )
    company = st.selectbox("Company style", options=COMPANIES)

    if st.button("Start Mock Interview", type="primary"):
        for key in list(st.session_state.keys()):
            if key.startswith("mock_"):
                del st.session_state[key]
        st.session_state["mock_active"] = True
        st.session_state["mock_dataset_id"] = dataset_id
        st.session_state["mock_company"] = company
        st.session_state["mock_index"] = 0
        st.session_state["mock_records"] = []
        st.session_state["mock_expected_dfs"] = {}
        st.rerun()

else:
    index = st.session_state["mock_index"]
    dataset_id = st.session_state["mock_dataset_id"]
    company = st.session_state["mock_company"]
    records: list[InterviewQuestionRecord] = st.session_state["mock_records"]

    answered_so_far = [record for record in records if record.evaluation is not None]
    if answered_so_far:
        avg_so_far = sum(record.evaluation.score for record in answered_so_far) / len(answered_so_far)
        st.caption(
            f"Progress: {len(answered_so_far)}/{NUM_QUESTIONS} answered · "
            f"average score so far: {avg_so_far:.1f}/10"
        )
    st.progress(min(index, NUM_QUESTIONS) / NUM_QUESTIONS)

    if index < NUM_QUESTIONS:
        if len(records) <= index:
            with st.spinner(f"Generating question {index + 1} of {NUM_QUESTIONS}..."):
                try:
                    difficulty = difficulty_for_index(index)
                    topic = topic_for_index(index)
                    llm = get_llm_provider()
                    question = generate_question(llm, dataset_id, topic, difficulty, company)
                    expected_df = run_read_only_query(question.answer_query)
                    records.append(InterviewQuestionRecord(question=question, evaluation=None))
                    st.session_state["mock_expected_dfs"][index] = expected_df
                except (QuestionGenerationError, UnsafeQueryError, SQLAlchemyError, ValueError) as exc:
                    logger.exception("Mock interview question generation failed")
                    st.error(f"Couldn't generate question {index + 1}: {exc}")
                    st.button("Try again", key=f"mock_retry_{index}")

        if len(records) > index:
            record = records[index]
            question = record.question
            expected_df = st.session_state["mock_expected_dfs"][index]

            st.markdown(f"### Question {index + 1} of {NUM_QUESTIONS}")
            st.markdown(
                f"**Topic:** {question.topic} &nbsp;·&nbsp; **Difficulty:** {question.difficulty} "
                f"&nbsp;·&nbsp; **Company style:** {question.company}"
            )
            st.info(question.question)
            st.caption(f"Tables: {', '.join(question.relevant_tables)}")

            user_sql = st.text_area("Your SQL answer", height=150, key=f"mock_answer_{index}")

            render_hint_section(
                state_key=f"mock_{index}",
                question_text=question.question,
                schema_ddl="\n\n".join(get_schema_ddl(question.dataset_id).values()),
                answer_query=question.answer_query,
                current_attempt=user_sql,
            )

            if record.evaluation is None:
                if st.button("Submit answer", key=f"mock_submit_{index}", type="primary"):
                    user_df, user_error = None, None
                    try:
                        user_df = run_read_only_query(user_sql)
                    except (UnsafeQueryError, SQLAlchemyError) as exc:
                        user_error = str(exc)

                    outputs_match = results_match(user_df, expected_df) if user_df is not None else False

                    with st.spinner("Grading..."):
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
                            records[index] = dataclasses.replace(record, evaluation=evaluation)
                            record_attempt(
                                source="mock_interview",
                                topic=question.topic,
                                difficulty=question.difficulty,
                                dataset_id=question.dataset_id,
                                is_correct=evaluation.is_correct,
                                score=evaluation.score,
                            )
                            st.rerun()
                        except EvaluationError as exc:
                            st.error(f"Couldn't grade your answer: {exc}")
            else:
                evaluation = record.evaluation
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
                    st.dataframe(expected_df, use_container_width=True)
                    st.code(question.answer_query, language="sql")

                button_label = "Finish interview" if index == NUM_QUESTIONS - 1 else "Next question"
                if st.button(button_label, key=f"mock_next_{index}", type="primary"):
                    st.session_state["mock_index"] = index + 1
                    st.rerun()

    else:
        st.divider()
        if "mock_report" not in st.session_state:
            with st.spinner("Compiling your interview report..."):
                try:
                    llm = get_llm_provider()
                    report = generate_interview_report(llm, records)
                    st.session_state["mock_report"] = report
                except InterviewReportError as exc:
                    st.error(f"Couldn't generate your report: {exc}")

        report = st.session_state.get("mock_report")
        if report:
            st.markdown("## Interview Complete")
            score_col, avg_col = st.columns(2)
            score_col.metric("Correct", f"{report.correct_count}/{report.total_questions}")
            avg_col.metric("Average score", f"{report.average_score}/10")

            st.markdown("#### Strengths")
            for item in report.strengths:
                st.markdown(f"- {item}")

            st.markdown("#### Weaknesses")
            for item in report.weaknesses:
                st.markdown(f"- {item}")

            st.markdown("#### Topics to Improve")
            for item in report.topics_to_improve:
                st.markdown(f"- {item}")

            st.markdown("#### Recommended Learning Path")
            st.write(report.recommended_learning_path)

        if st.button("Start a new mock interview"):
            for key in list(st.session_state.keys()):
                if key.startswith("mock_"):
                    del st.session_state[key]
            st.rerun()
