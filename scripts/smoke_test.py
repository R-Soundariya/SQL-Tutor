"""Manual end-to-end check: run after filling in .env to confirm the database
and active LLM provider are both reachable.

    python scripts/smoke_test.py

Not part of the pytest suite on purpose - this makes a real API call and
should be run deliberately, not on every test run.
"""

from app.core.config import get_settings
from app.core.db.engine import test_connection
from app.core.llm.factory import get_llm_provider


def main() -> None:
    settings = get_settings()

    print("Testing database connection...")
    db_ok, db_message = test_connection()
    print(f"  {'OK' if db_ok else 'FAILED'}: {db_message}")

    print(f"\nTesting LLM provider '{settings.llm_provider}'...")
    try:
        provider = get_llm_provider()
        reply = provider.generate(
            prompt="Reply with exactly the word: pong",
            max_tokens=10,
        )
        print(f"  OK: model replied '{reply.strip()}'")
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic script
        print(f"  FAILED: {exc}")


if __name__ == "__main__":
    main()
