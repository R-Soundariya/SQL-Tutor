"""Creates and seeds sandbox dataset tables in the configured MySQL database."""

from __future__ import annotations

import logging

from sqlalchemy import Engine
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

from app.core.db.engine import ensure_database_exists, get_engine
from app.core.db.sandbox.schema import DATASETS, sandbox_metadata
from app.core.db.sandbox.seed_data import SEED_BUILDERS

logger = logging.getLogger(__name__)


def load_dataset(dataset_id: str, engine: Engine | None = None) -> dict[str, int]:
    """Drop, recreate, and reseed every table belonging to `dataset_id`.

    Returns a mapping of table name -> row count inserted, so callers (e.g.
    the Sandbox page) can confirm what was loaded.
    """
    if dataset_id not in DATASETS:
        raise ValueError(f"Unknown dataset '{dataset_id}'. Valid options: {list(DATASETS)}")

    if engine is None:
        ensure_database_exists()
    engine = engine or get_engine()
    dataset = DATASETS[dataset_id]
    rows_by_table = SEED_BUILDERS[dataset_id]()

    logger.info("Loading sandbox dataset '%s' (%d tables)", dataset_id, len(dataset.tables))

    sandbox_metadata.drop_all(engine, tables=dataset.tables, checkfirst=True)
    sandbox_metadata.create_all(engine, tables=dataset.tables, checkfirst=True)

    inserted_counts: dict[str, int] = {}
    with engine.begin() as conn:
        for table in dataset.tables:
            rows = rows_by_table.get(table.name, [])
            if rows:
                conn.execute(table.insert(), rows)
            inserted_counts[table.name] = len(rows)

    logger.info("Loaded dataset '%s': %s", dataset_id, inserted_counts)
    return inserted_counts


def load_all_datasets(engine: Engine | None = None) -> dict[str, dict[str, int]]:
    """Load every registered sandbox dataset. Returns per-dataset row counts."""
    engine = engine or get_engine()
    return {dataset_id: load_dataset(dataset_id, engine=engine) for dataset_id in DATASETS}


def get_schema_ddl(dataset_id: str) -> dict[str, str]:
    """Return CREATE TABLE DDL (MySQL dialect) for each table in a dataset,
    without requiring a live database connection."""
    if dataset_id not in DATASETS:
        raise ValueError(f"Unknown dataset '{dataset_id}'. Valid options: {list(DATASETS)}")

    dialect = mysql.dialect()
    return {
        table.name: str(CreateTable(table).compile(dialect=dialect)).strip()
        for table in DATASETS[dataset_id].tables
    }
