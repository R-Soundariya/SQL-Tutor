"""Unit tests for sandbox table definitions and DDL generation.
CreateTable().compile() does not require a live database connection."""

from app.core.db.sandbox.loader import get_schema_ddl
from app.core.db.sandbox.schema import DATASETS


def test_all_datasets_have_at_least_one_table() -> None:
    for dataset in DATASETS.values():
        assert len(dataset.tables) >= 1


def test_every_table_has_a_primary_key() -> None:
    for dataset in DATASETS.values():
        for table in dataset.tables:
            assert len(table.primary_key.columns) >= 1, f"{table.name} has no primary key"


def test_schema_ddl_compiles_for_every_dataset() -> None:
    for dataset_id, dataset in DATASETS.items():
        ddl_by_table = get_schema_ddl(dataset_id)
        assert set(ddl_by_table.keys()) == {t.name for t in dataset.tables}
        for ddl in ddl_by_table.values():
            assert "CREATE TABLE" in ddl.upper()
