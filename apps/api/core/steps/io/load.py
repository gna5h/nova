from __future__ import annotations

import pandas as pd

from core.registry import register_step
from core.step import StepParams, StepResult


class LoadParams(StepParams):
    file_path: str
    original_filename: str
    sheet_name: str | None = None


@register_step
class LoadStep:
    id = "io.load"
    category = "io"
    title = "Load dataset"
    description = "Load a CSV or XLSX file into a DataFrame."
    Params = LoadParams

    def run(self, df: pd.DataFrame, params: LoadParams) -> StepResult:
        ext = params.original_filename.rsplit(".", 1)[-1].lower()
        if ext not in ("csv", "xlsx"):
            raise ValueError(f"Unsupported file type: .{ext}. Only .csv and .xlsx are supported.")

        if ext == "csv":
            try:
                loaded = pd.read_csv(params.file_path, encoding="utf-8")
            except UnicodeDecodeError:
                loaded = pd.read_csv(params.file_path, encoding="latin-1")
        else:
            sheet = params.sheet_name if params.sheet_name is not None else 0
            loaded = pd.read_excel(params.file_path, engine="openpyxl", sheet_name=sheet)

        # Secondary type-inference pass on object columns only
        for col in loaded.columns[loaded.dtypes == object]:
            converted = pd.to_numeric(loaded[col], errors="coerce")
            if converted.notna().sum() > 0 and loaded[col].notna().sum() > 0:
                if converted.notna().sum() == loaded[col].notna().sum():
                    loaded[col] = converted
                    continue
            try:
                loaded[col] = pd.to_datetime(loaded[col], errors="raise")
            except (ValueError, TypeError):
                pass

        return StepResult(
            data=loaded,
            facts={
                "row_count": len(loaded),
                "column_count": len(loaded.columns),
                "original_filename": params.original_filename,
            },
        )
