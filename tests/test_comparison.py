"""Unit tests for app.core.db.comparison.results_match."""

import pandas as pd

from app.core.db.comparison import results_match


def test_identical_dataframes_match() -> None:
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    assert results_match(df, df.copy())


def test_row_order_is_ignored_by_default() -> None:
    df1 = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    df2 = pd.DataFrame({"a": [2, 1], "b": ["y", "x"]})
    assert results_match(df1, df2)


def test_row_order_matters_when_requested() -> None:
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"a": [2, 1]})
    assert not results_match(df1, df2, ignore_row_order=False)


def test_different_values_do_not_match() -> None:
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"a": [1, 3]})
    assert not results_match(df1, df2)


def test_different_columns_do_not_match() -> None:
    df1 = pd.DataFrame({"a": [1]})
    df2 = pd.DataFrame({"b": [1]})
    assert not results_match(df1, df2)


def test_different_shapes_do_not_match() -> None:
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"a": [1]})
    assert not results_match(df1, df2)
