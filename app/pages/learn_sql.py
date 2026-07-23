"""Learn SQL page: browse a concept lesson, then practice it against real
sandbox data with an instant right/wrong check (no AI call needed - that's
reserved for the dedicated Interview/Mock Interview scoring in a later phase)."""

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.comparison import results_match
from app.core.db.query_runner import UnsafeQueryError, run_read_only_query
from app.core.db.sandbox.schema import DATASETS
from app.core.learning.lessons import LESSONS, LESSONS_BY_ID

st.title("Learn SQL")
st.caption("Pick a topic, read through it, then practice against real sandbox data.")

lesson_id = st.selectbox(
    "Topic",
    options=[lesson.id for lesson in LESSONS],
    format_func=lambda lid: f"{LESSONS_BY_ID[lid].category} — {LESSONS_BY_ID[lid].title}",
)
lesson = LESSONS_BY_ID[lesson_id]
dataset = DATASETS[lesson.dataset_id]

st.subheader(lesson.title)
st.caption(f"{lesson.category} · {lesson.difficulty}")

st.markdown("#### Explanation")
st.markdown(lesson.explanation)

st.markdown("#### Syntax")
st.code(lesson.syntax, language="sql")

st.markdown("#### Visual Example")
st.markdown(lesson.visual_example)

st.markdown("#### Business Use Case")
st.markdown(lesson.business_use_case)

st.divider()
st.markdown("#### Practice Question")
st.info(lesson.practice_question)
st.caption(
    f"This question uses the **{dataset.display_name}** dataset — load it from "
    "Database Sandbox first if you haven't already."
)

user_sql = st.text_area("Your SQL answer", height=140, key=f"answer_{lesson.id}")
check_col, reveal_col = st.columns(2)
check_clicked = check_col.button("Run & check my answer", key=f"check_{lesson.id}")
reveal_clicked = reveal_col.button("Show expected output", key=f"reveal_{lesson.id}")

if check_clicked:
    try:
        user_df = run_read_only_query(user_sql)
        expected_df = run_read_only_query(lesson.answer_query)
        if results_match(user_df, expected_df):
            st.success("Correct — your output matches the expected result.")
        else:
            st.warning("Not quite yet — compare your output against the expected result below.")
        st.markdown("**Your output**")
        st.dataframe(user_df, use_container_width=True)
        st.markdown("**Expected output**")
        st.dataframe(expected_df, use_container_width=True)
    except UnsafeQueryError as exc:
        st.error(str(exc))
    except SQLAlchemyError as exc:
        st.error(f"Query failed — is the '{dataset.display_name}' dataset loaded? {exc}")

if reveal_clicked:
    try:
        expected_df = run_read_only_query(lesson.answer_query)
        st.markdown("**Expected output**")
        st.dataframe(expected_df, use_container_width=True)
        with st.expander("Show model SQL answer"):
            st.code(lesson.answer_query, language="sql")
    except SQLAlchemyError as exc:
        st.error(f"Could not run the model query — is the '{dataset.display_name}' dataset loaded? {exc}")

st.divider()
st.markdown("#### Common Interview Questions")
for question in lesson.common_interview_questions:
    st.markdown(f"- {question}")
