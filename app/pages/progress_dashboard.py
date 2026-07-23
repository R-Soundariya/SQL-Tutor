"""Progress Dashboard page: accuracy, average score, topic mastery,
weakest concepts, daily streak, and practice history across every logged
attempt (Learn SQL, Practice Questions, Mock Interview)."""

import plotly.express as px
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from app.core.progress.stats import (
    get_daily_activity,
    get_summary_stats,
    get_topic_mastery,
    get_weakest_topics,
    load_attempts,
)

# Single-hue sequential blue ramp (validated palette, light->dark) - magnitude
# encoding, never a rainbow. See app/core/progress for the underlying stats.
_SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
_PRIMARY_BLUE = "#2a78d6"

st.title("Progress Dashboard")
st.caption("Tracks every graded attempt from Learn SQL, Practice Questions, and Mock Interview.")

try:
    attempts = load_attempts()
except SQLAlchemyError as exc:
    attempts = None
    st.error(f"Could not load progress data. Check your database connection in Settings.\n\n{exc}")

if attempts is None:
    pass
elif attempts.empty:
    st.info(
        "No attempts logged yet. Complete a question in Learn SQL, Practice Questions, "
        "or Mock Interview and it'll show up here."
    )
else:
    summary = get_summary_stats(attempts)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Questions Attempted", summary.total_attempts)
    col2.metric("Accuracy", f"{summary.accuracy_pct}%")
    col3.metric("Average Score", f"{summary.average_score}/10" if summary.average_score is not None else "—")
    col4.metric("Daily Streak", f"{summary.current_streak_days} day(s)")

    st.divider()

    mastery_col, weak_col = st.columns([2, 1])

    with mastery_col:
        st.markdown("#### Topic Mastery")
        mastery = get_topic_mastery(attempts)
        fig = px.bar(
            mastery,
            x="accuracy_pct",
            y="topic",
            orientation="h",
            color="accuracy_pct",
            color_continuous_scale=_SEQUENTIAL_BLUE,
            range_color=(0, 100),
            labels={"accuracy_pct": "Accuracy (%)", "topic": ""},
            hover_data={"attempts": True, "average_score": True},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("View topic mastery as a table"):
            st.dataframe(mastery, use_container_width=True)

    with weak_col:
        st.markdown("#### Weakest Concepts")
        weakest = get_weakest_topics(attempts)
        if weakest:
            for topic in weakest:
                st.warning(topic)
        else:
            st.success("No weak spots yet — keep practicing to build up topic data.")

    st.divider()

    st.markdown("#### Daily Activity")
    daily = get_daily_activity(attempts)
    activity_fig = px.bar(
        daily,
        x="date",
        y="attempts",
        labels={"date": "", "attempts": "Questions attempted"},
    )
    activity_fig.update_traces(marker_color=_PRIMARY_BLUE)
    activity_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(activity_fig, use_container_width=True)

    st.divider()

    st.markdown("#### Practice History")
    history = attempts.sort_values("created_at", ascending=False).head(100)
    st.dataframe(
        history[["created_at", "source", "topic", "difficulty", "is_correct", "score"]],
        use_container_width=True,
        hide_index=True,
    )
