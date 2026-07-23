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
- Database Sandbox — practice against sample datasets (Employees, Sales,
  Netflix, Spotify, etc.)

## Architecture

- **UI:** Streamlit multi-page app (`st.navigation`)
- **Database:** MySQL via SQLAlchemy (`pymysql` driver)
- **LLM layer:** provider-agnostic interface (`app/core/llm`) with
  interchangeable Anthropic and OpenAI backends, selected via config
- **Config:** typed settings loaded from `.env` (`app/core/config.py`)
- **Logging:** console + rotating file handler (`logs/app.log`)

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
    llm/
      base.py            # LLMProvider interface
      anthropic_provider.py
      openai_provider.py
      factory.py          # Resolves the configured provider
tests/                 # Unit tests (no real network/DB calls)
scripts/
  smoke_test.py         # Manual real DB + LLM connectivity check
```

## Installation

1. Clone the repo and create a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your MySQL credentials and at
   least one LLM API key (Anthropic and/or OpenAI).
3. Create the MySQL database referenced by `DB_NAME` in `.env`.

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
- [ ] Phase 2 — Database Sandbox & sample datasets
- [ ] Phase 3 — SQL Learning Mode
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
