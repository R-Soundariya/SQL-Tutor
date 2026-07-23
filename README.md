# SQL Interview Coach AI

An AI-powered SQL interview preparation platform for aspiring Data Analysts,
Business Analysts, and BI Analysts. Learn SQL concepts, practice real
interview questions, get instant AI feedback, optimize queries, and track
your progress over time.

> **Status:** Under active, phased development. This README is updated as
> each phase lands.

## Features

Planned feature set (built incrementally — see Phases below):

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
      sandbox/
        schema.py          # SQLAlchemy Core table defs + dataset registry
        seed_data.py        # Deterministic (seeded) fake data generators
        loader.py           # Create/reset/seed tables, generate DDL text
    learning/
      models.py            # Lesson dataclass
      lessons.py            # Lesson content (curriculum data)
    llm/
      base.py            # LLMProvider interface
      anthropic_provider.py
      openai_provider.py
      factory.py          # Resolves the configured provider
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
- [ ] Phase 4 — Practice Questions / Interview Mode + AI evaluation
- [ ] Phase 5 — AI Hint System
- [ ] Phase 6 — Explain My Query
- [ ] Phase 7 — Query Optimizer
- [ ] Phase 8 — Mock SQL Interview
- [ ] Phase 9 — Progress Dashboard
- [ ] Phase 10 — Daily Challenge & polish

## Future Enhancements

- User accounts / multi-user support
- Company-specific question banks sourced from real interview reports
- Exportable interview performance reports (PDF)
- Voice-based mock interview mode
