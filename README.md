# SQL Interview Coach AI

An AI-powered SQL interview preparation platform for aspiring Data Analysts,
Business Analysts, and BI Analysts. Learn SQL concepts, practice real
interview questions, get instant AI feedback, optimize queries, and track
your progress over time.

> **Status:** All 10 planned phases are implemented and unit-tested. Live
> end-to-end verification against a real MySQL server and LLM API key is
> still outstanding — see "Live Verification" below.

## Features

- SQL Interview Mode — leveled practice questions with AI scoring & feedback
- SQL Learning Mode — interactive lessons per concept
- Query Optimizer — performance/index suggestions for pasted queries
- Daily Challenge — one timed question per day
- Mock SQL Interview — full 15-question scored interview with a learning path
- Progress Dashboard — accuracy, streaks, topic mastery
- AI Hint System — progressive hints without revealing the answer
- Explain My Query — clause-by-clause query explanations
- Company-targeted practice question generation
- Database Sandbox — practice against seeded datasets: HR/Employees,
  E-commerce Orders, Streaming Catalog (more coming: Spotify, Anime, Food
  Delivery)

## Architecture

- **UI:** Streamlit multi-page app (`st.navigation`)
- **Database:** MySQL via SQLAlchemy (`pymysql` driver)
- **LLM layer:** provider-agnostic interface (`app/core/llm`) with
  interchangeable Anthropic and OpenAI backends, selected via config
- **Config:** typed settings loaded from `.env` (`app/core/config.py`)
- **Logging:** console + rotating file handler (`logs/app.log`)
- **Sandbox datasets:** SQLAlchemy Core tables + deterministic (seeded)
  Faker-generated rows (`app/core/db/sandbox`), so a reset always reproduces
  the exact same data — required for later phases to grade a user's query
  against a fixed expected output
- **Query safety:** all user-submitted SQL is validated as a single
  read-only `SELECT`/`WITH` statement and row-capped before execution
  (`app/core/db/query_runner.py`), reused by every feature that runs a
  user's own SQL
- **AI question generation & grading:** the LLM is asked to return JSON
  only (`app/core/llm/json_utils.py` tolerates stray markdown fences), and
  a generated question's answer query is validated + sanity-executed
  before being shown to the user. Correctness (`is_correct`) is always
  decided by a deterministic output comparison, never by the model's own
  opinion — the LLM only supplies the score, mistakes, and suggestions
- **AI hints:** hint generation is decoupled from both Learn SQL lessons
  and AI-generated practice questions (`app/core/hints/generator.py` takes
  plain strings, not either type), so the same progressive-hint UI
  component (`app/ui/hint_section.py`) works on both pages
- **Explain SQL:** reuses the same read-only validator every other feature
  uses before asking the LLM to explain a query, and optionally grounds
  the explanation in a real sandbox schema for a live output preview
- **Query Optimizer:** static analysis (`app/core/optimizer/static_analysis.py`)
  is pure string/paren analysis with no LLM or DB dependency, so findings
  are instant and free; the AI rewrite step layers on top and, when a
  sandbox dataset is loaded, is grounded in a real `EXPLAIN` plan
  (`app/core/db/explain_plan.py`) rather than guessing at index impact
- **Mock Interview:** an orchestration layer, not a reimplementation - it
  drives the same `generate_question`/`evaluate_answer` functions from
  Practice Questions and the same hint widget from Phase 5, one question
  at a time (lazily generated, not all 15 upfront) with a deterministic
  difficulty/topic schedule (`app/core/practice/mock_interview.py`)
- **Progress persistence:** `app/core/progress/models.py` defines the
  app's own `Attempt` ORM table on `Base` (reserved for exactly this since
  Phase 1, separate from the sandbox datasets' own `MetaData`).
  `record_attempt()` is best-effort and never raises, so a DB hiccup can't
  break a grading flow that already succeeded. Every aggregation in
  `app/core/progress/stats.py` accepts an optional pre-loaded DataFrame,
  so the stats logic is unit-tested with synthetic data, no database
  required
- **Daily Challenge:** the *category* (dataset/topic/difficulty) is picked
  by a pure function seeded from the calendar date
  (`app/core/daily_challenge/provider.py::schedule_for_date`), but the
  actual question text is generated once via the LLM and persisted -
  determinism alone can't produce question text, only which category to
  ask about. The provider takes an injectable `engine` parameter so its
  caching behavior is tested against an in-memory SQLite database rather
  than requiring real MySQL

## Folder Structure

```
app/
  main.py              # Streamlit entry point / page navigation
  pages/               # One module per Streamlit page
  core/
    config.py           # Typed settings (.env)
    logging_config.py   # Logging setup
    db/
      engine.py          # SQLAlchemy engine/session + connection test
      models.py          # ORM models (added per-phase)
      query_runner.py     # Safe execution of user-submitted read-only SQL
      comparison.py        # Compare a query's output against an expected result
      explain_plan.py      # Real MySQL EXPLAIN plan for a read-only query
      sandbox/
        schema.py          # SQLAlchemy Core table defs + dataset registry
        seed_data.py        # Deterministic (seeded) fake data generators
        loader.py           # Create/reset/seed tables, generate DDL text
    learning/
      models.py            # Lesson dataclass
      lessons.py            # Lesson content (curriculum data)
    practice/
      models.py            # GeneratedQuestion / EvaluationResult / InterviewQuestionRecord / InterviewReport
      constants.py          # Selectable topics/difficulties/companies
      question_generator.py # LLM -> validated GeneratedQuestion
      evaluator.py           # LLM + deterministic comparison -> EvaluationResult
      mock_interview.py      # Difficulty/topic schedule for the 15-question interview
      report_generator.py    # LLM -> aggregate strengths/weaknesses/learning path
    progress/
      models.py            # Attempt ORM model + table lifecycle
      recorder.py            # Best-effort attempt logging (never raises)
      stats.py                # Accuracy/mastery/streak/history aggregation
    daily_challenge/
      models.py            # DailyChallengeRow ORM model + table lifecycle
      provider.py            # Date-seeded scheduling + get-or-create-and-persist
    timeutils.py           # utc_now() - naive-UTC helper used across models
    hints/
      generator.py          # LLM -> 3 progressive hints, provider-agnostic
    explain/
      models.py            # ClauseExplanation / ExplanationResult
      explainer.py           # LLM -> clause breakdown, execution order, etc.
    optimizer/
      models.py            # StaticFinding / OptimizationResult
      static_analysis.py    # Deterministic anti-pattern checks, no LLM/DB
      optimizer.py           # LLM (+ static findings + EXPLAIN) -> rewrite
    llm/
      base.py            # LLMProvider interface
      anthropic_provider.py
      openai_provider.py
      factory.py          # Resolves the configured provider
      json_utils.py        # Tolerant JSON extraction from LLM responses
  ui/
    hint_section.py       # Shared Streamlit hint widget (Learn SQL + Practice)
tests/                 # Unit tests (no real network/DB calls)
scripts/
  smoke_test.py         # Manual real DB + LLM connectivity check
  load_sandbox_data.py  # Manual: load/reset all sandbox datasets
```

## Installation

1. Clone the repo and create a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your MySQL credentials and at
   least one LLM API key (Anthropic and/or OpenAI). The database named by
   `DB_NAME` is created automatically the first time you load a sandbox
   dataset (no manual `CREATE DATABASE` needed).

## Usage

```
streamlit run app/main.py
```

Optional: verify your `.env` is wired correctly (real DB + LLM call):

```
python scripts/smoke_test.py
```

Run the unit test suite (no credentials required):

```
pytest
```

## Live Verification

All 98 unit tests pass without any real credentials — every AI feature is
tested against a fake LLM provider, and every DB-dependent function either
accepts an injectable engine/DataFrame or is exercised through its
error-handling path. What hasn't been verified yet is a real end-to-end run:
actual Claude/GPT output quality (question wording, hint usefulness,
optimizer rewrites) and actual MySQL behavior under the app's real schema.
Recommended before treating this as production-ready:

1. Fill in `.env` with real MySQL credentials and at least one LLM API key.
2. `python scripts/load_sandbox_data.py` to seed all three datasets.
3. `python scripts/smoke_test.py` to confirm connectivity.
4. Click through each AI feature once for real: Practice Questions, Hints,
   Explain SQL, Query Optimizer, Mock Interview, Daily Challenge.

## Known Scope Gaps

Called out explicitly, not hidden:

- **Sandbox datasets:** 3 of the spec's 8 (HR, E-commerce, Streaming). The
  loader architecture (`app/core/db/sandbox/`) extends to Spotify, Anime,
  and Food Delivery with no new plumbing - just table defs + seed data.
- **Learn SQL:** 8 of ~18 topics. RIGHT/FULL/SELF JOIN, UNION, LAG/LEAD,
  running totals, and date functions follow the same `Lesson` shape.
- **Practice Questions / Mock Interview topics:** Views, Indexes, and Query
  Optimization are intentionally excluded from the AI question generator -
  they don't fit a "write a SELECT, compare output" loop the way the other
  13 topics do.

## Development Phases

- [x] **Phase 1 — Project architecture & setup:** folder structure, config,
      logging, DB engine, LLM provider abstraction, Streamlit page shell.
- [x] **Phase 2 — Database Sandbox & sample datasets:** HR, E-commerce, and
      Streaming Catalog datasets with deterministic seed data; safe
      read-only query execution; Sandbox page (load/reset, schema, preview,
      run-a-query).
- [x] **Phase 3 — SQL Learning Mode (batch 1):** lesson content model,
      8 lessons (SELECT/WHERE/ORDER BY, GROUP BY, HAVING, INNER JOIN,
      LEFT JOIN, CASE, CTE, ranking window functions) each with
      explanation/syntax/visual example/practice question/business use
      case/interview questions, self-check against sandbox data (no AI
      call). Remaining topics (RIGHT/FULL/SELF JOIN, UNION, LAG/LEAD,
      running totals, date functions) follow the same pattern.
- [x] **Phase 4 — Practice Questions / Interview Mode + AI evaluation:**
      LLM-generated interview questions grounded in a real sandbox schema
      (topic/difficulty/company-style selectable), user answers executed
      against live data, AI-graded feedback (score/10, mistakes,
      suggestions) with correctness decided deterministically rather than
      by the model's own opinion. Views/Indexes/Optimization topics
      deferred to the Query Optimizer phase.
- [x] **Phase 5 — AI Hint System:** progressive 3-level hints
      (concept → specifics → structural sketch) available from both Learn
      SQL and Practice Questions, generated in a single LLM call and
      revealed one at a time. A hint that leaks the full answer query is
      rejected programmatically, not just by prompt instruction.
- [x] **Phase 6 — Explain My Query:** paste any SELECT/WITH query and get
      a clause-by-clause breakdown, logical execution order, business
      meaning, expected output, and lightweight complexity notes.
      Optionally grounded in a real sandbox dataset for a live result
      preview. Deep index/rewrite recommendations are left to the Query
      Optimizer phase.
- [x] **Phase 7 — Query Optimizer:** deterministic static analysis
      (SELECT *, missing WHERE, non-sargable predicates, leading-wildcard
      LIKE, implicit cross joins, repeated subqueries, redundant
      DISTINCT+GROUP BY) runs instantly with no LLM call, feeding into an
      AI-generated rewrite, index recommendations, and impact estimate -
      grounded in a real MySQL EXPLAIN plan when a sandbox dataset is
      loaded.
- [x] **Phase 8 — Mock SQL Interview:** 15 AI-generated questions per
      session (5 Beginner, 5 Intermediate, 5 Advanced, cycling through all
      13 topics for breadth), graded one at a time by reusing the Practice
      Questions evaluator, hints available via the same shared widget, and
      an aggregate strengths/weaknesses/topics-to-improve/learning-path
      report at the end. Correct count and average score are computed
      deterministically, not asserted by the LLM.
- [x] **Phase 9 — Progress Dashboard:** the first real write-path - every
      graded attempt from Learn SQL, Practice Questions, and Mock
      Interview is logged to a new `progress_attempts` table
      (auto-created, best-effort so a logging failure never breaks the
      grading flow that already succeeded). Dashboard shows questions
      attempted, accuracy, average score, topic mastery (chart + table),
      weakest concepts, daily streak, daily activity chart, and practice
      history.
- [x] **Phase 10 — Daily Challenge:** one AI-generated question per
      calendar day, persisted (`daily_challenges` table) so every visit
      that day reuses the same question instead of calling the LLM again;
      deterministic date-seeded topic/difficulty/dataset selection; a live
      timer (`st.fragment(run_every="1s")`); grading via the same
      evaluator as Practice Questions; and a full explanation of the model
      answer afterward via the same explainer from Phase 6. This completes
      every feature from the original spec.

## Future Enhancements

- User accounts / multi-user support
- Company-specific question banks sourced from real interview reports
- Exportable interview performance reports (PDF)
- Voice-based mock interview mode
