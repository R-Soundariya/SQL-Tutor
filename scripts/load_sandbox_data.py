"""Load (or reset) all sandbox datasets against the configured MySQL database.

    python scripts/load_sandbox_data.py

Requires a real .env with working DB credentials - this makes real DDL/DML
calls, so it is a manual script rather than a pytest test.
"""

from app.core.db.sandbox.loader import load_all_datasets


def main() -> None:
    print("Loading all sandbox datasets...")
    results = load_all_datasets()
    for dataset_id, table_counts in results.items():
        print(f"\n[{dataset_id}]")
        for table_name, row_count in table_counts.items():
            print(f"  {table_name}: {row_count} rows")


if __name__ == "__main__":
    main()
