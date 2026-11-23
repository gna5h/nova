from __future__ import annotations

import tempfile
import os

import pandas as pd
import pytest

from core.steps.io.load import LoadParams, LoadStep


@pytest.fixture
def step() -> LoadStep:
    return LoadStep()


def test_load_csv_utf8(step: LoadStep, tmp_path: pytest.TempPathFactory) -> None:
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")

    result = step.run(pd.DataFrame(), LoadParams(
        file_path=str(csv_file),
        original_filename="test.csv",
    ))

    assert result.data is not None
    assert result.data.shape == (2, 3)
    assert result.facts["row_count"] == 2
    assert result.facts["column_count"] == 3
    assert result.facts["original_filename"] == "test.csv"


def test_load_csv_latin1(step: LoadStep, tmp_path: pytest.TempPathFactory) -> None:
    csv_file = tmp_path / "latin1.csv"
    csv_file.write_bytes("name,value\nélan,1\ncafé,2\n".encode("latin-1"))

    result = step.run(pd.DataFrame(), LoadParams(
        file_path=str(csv_file),
        original_filename="latin1.csv",
    ))

    assert result.data is not None
    assert "élan" in result.data["name"].values or "caf\xe9" in result.data["name"].values
    assert result.data.shape == (2, 2)


def test_load_xlsx(step: LoadStep, tmp_path: pytest.TempPathFactory) -> None:
    df = pd.DataFrame({"x": [10, 20, 30], "y": ["a", "b", "c"]})
    xlsx_file = tmp_path / "test.xlsx"
    df.to_excel(str(xlsx_file), index=False)

    result = step.run(pd.DataFrame(), LoadParams(
        file_path=str(xlsx_file),
        original_filename="test.xlsx",
    ))

    assert result.data is not None
    assert result.data.shape == (3, 2)
    assert result.facts["row_count"] == 3


def test_load_unsupported_ext(step: LoadStep, tmp_path: pytest.TempPathFactory) -> None:
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("some text", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file type"):
        step.run(pd.DataFrame(), LoadParams(
            file_path=str(txt_file),
            original_filename="data.txt",
        ))


def test_load_type_inference(step: LoadStep, tmp_path: pytest.TempPathFactory) -> None:
    csv_file = tmp_path / "nums.csv"
    csv_file.write_text("id,value\n1,1\n2,2\n3,3\n", encoding="utf-8")

    result = step.run(pd.DataFrame(), LoadParams(
        file_path=str(csv_file),
        original_filename="nums.csv",
    ))

    assert result.data is not None
    assert pd.api.types.is_numeric_dtype(result.data["value"])
