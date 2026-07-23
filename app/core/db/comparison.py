"""Compares two query result sets, e.g. a user's answer against the
expected output for a practice question. Used by Learn SQL today; Practice
Mode / Mock Interview scoring in a later phase reuses the same check as
one input to their AI-assisted evaluation."""

from __future__ import annotations

import pandas as pd


def results_match(actual: pd.DataFrame, expected: pd.DataFrame, ignore_row_order: bool = True) -> bool:
    """Return True if two query result DataFrames contain the same data.

    Values are stringified before comparison so equivalent values with
    different dtypes (e.g. Decimal vs float) still match. Column names and
    order must match exactly; row order is ignored by default since most
    practice questions don't require a specific order unless the question
    itself calls for ORDER BY.
    """
    if list(actual.columns) != list(expected.columns):
        return False
    if actual.shape != expected.shape:
        return False

    actual_norm = actual.astype(str)
    expected_norm = expected.astype(str)

    if ignore_row_order:
        columns = list(actual_norm.columns)
        actual_norm = actual_norm.sort_values(by=columns).reset_index(drop=True)
        expected_norm = expected_norm.sort_values(by=columns).reset_index(drop=True)

    return actual_norm.equals(expected_norm)
