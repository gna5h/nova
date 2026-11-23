from __future__ import annotations

import pandas as pd
import pytest

from core.steps.profile.summary import SummaryParams, SummaryStep


@pytest.fixture
def step() -> SummaryStep:
    return SummaryStep()


def test_profile_basic_counts(step: SummaryStep) -> None:
    df = pd.DataFrame({
        "a": [1, 2, 3],
        "b": ["x", "y", "z"],
        "c": [1.1, 2.2, 3.3],
    })
    result = step.run(df, SummaryParams())

    assert result.facts["row_count"] == 3
    assert result.facts["column_count"] == 3
    assert len(result.tables) == 1
    assert len(result.tables[0].rows) == 3


def test_profile_null_detection(step: SummaryStep) -> None:
    df = pd.DataFrame({
        "val": [pd.NA, None, "N/A", "real", "other"],
    })
    result = step.run(df, SummaryParams())

    rows = result.tables[0].rows
    # find null_count column index
    col_names = result.tables[0].columns
    null_count_idx = col_names.index("null_count")

    val_row = next(r for r in rows if r[0] == "val")
    # pd.NA + None + "N/A" token = 3 nulls
    assert val_row[null_count_idx] == 3


def test_profile_outlier_detection(step: SummaryStep) -> None:
    df = pd.DataFrame({
        "scores": [1, 2, 3, 4, 100],
    })
    result = step.run(df, SummaryParams())

    col_names = result.tables[0].columns
    outlier_idx = col_names.index("outlier_count")
    scores_row = result.tables[0].rows[0]
    assert scores_row[outlier_idx] == 1


def test_profile_duplicate_rows(step: SummaryStep) -> None:
    df = pd.DataFrame({
        "a": [1, 2, 1],
        "b": ["x", "y", "x"],
    })
    result = step.run(df, SummaryParams())
    assert result.facts["duplicate_row_count"] == 1


def test_profile_no_data_returned(step: SummaryStep) -> None:
    df = pd.DataFrame({"a": [1, 2, 3]})
    result = step.run(df, SummaryParams())
    assert result.data is None
