from __future__ import annotations

from typing import Any

import pandas as pd

from core.registry import register_step
from core.step import ResultTable, StepParams, StepResult

_MISSING_TOKENS = {"", "N/A", "-", "?", "null", "none", "NULL"}


class SummaryParams(StepParams):
    pass


@register_step
class SummaryStep:
    id = "profile.summary"
    category = "profile"
    title = "Profile dataset"
    description = "Generate a statistical profile of every column in the dataset."
    Params = SummaryParams

    def run(self, df: pd.DataFrame, params: SummaryParams) -> StepResult:
        work = df.copy()

        # Replace missing tokens with pd.NA on object columns.
        # Use element-wise apply to avoid pd.NA propagation in .isin().
        def _replace_tokens(x: object) -> object:
            if pd.isna(x):
                return x
            if isinstance(x, str) and x in _MISSING_TOKENS:
                return pd.NA
            return x

        # Apply to all non-numeric, non-bool, non-datetime columns (handles both
        # legacy object dtype and pandas 3.x StringDtype).
        for col in work.columns:
            dtype = work[col].dtype
            if (
                not pd.api.types.is_numeric_dtype(dtype)
                and not pd.api.types.is_bool_dtype(dtype)
                and not pd.api.types.is_datetime64_any_dtype(dtype)
            ):
                work[col] = work[col].apply(_replace_tokens)

        total_cells = len(work) * len(work.columns) if len(work.columns) > 0 else 1
        total_missing = int(work.isna().sum().sum())
        total_missing_pct = round(total_missing / total_cells * 100, 2)
        duplicate_row_count = int(work.duplicated().sum())

        columns: list[str] = [
            "column", "dtype_inferred", "null_count", "null_pct",
            "unique_count", "sample_values", "outlier_count", "min", "max",
        ]
        rows: list[list[Any]] = []

        for col in work.columns:
            series = work[col]
            null_count = int(series.isna().sum())
            null_pct = round(null_count / len(series) * 100, 2) if len(series) > 0 else 0.0
            unique_count = int(series.nunique(dropna=True))

            non_null = series.dropna()
            sample_vals = [str(v)[:50] for v in non_null.head(3).tolist()]

            # Infer dtype label
            if pd.api.types.is_integer_dtype(series):
                dtype_label = "integer"
            elif pd.api.types.is_float_dtype(series):
                dtype_label = "float"
            elif pd.api.types.is_datetime64_any_dtype(series):
                dtype_label = "datetime"
            elif pd.api.types.is_bool_dtype(series):
                dtype_label = "boolean"
            elif pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
                # Check for mixed types among non-null values (object dtype only;
                # pandas 3.x StringDtype is always homogeneous strings).
                if pd.api.types.is_object_dtype(series):
                    types_seen = {type(v) for v in non_null}
                    dtype_label = "mixed" if len(types_seen) > 1 else "string"
                else:
                    dtype_label = "string"
            else:
                dtype_label = str(series.dtype)

            # Outlier detection: IQR method on numeric columns
            outlier_count = 0
            col_min: Any = ""
            col_max: Any = ""
            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                numeric_vals = non_null
                if len(numeric_vals) >= 4:
                    q1 = float(numeric_vals.quantile(0.25))
                    q3 = float(numeric_vals.quantile(0.75))
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outlier_count = int(((numeric_vals < lower) | (numeric_vals > upper)).sum())
                if len(numeric_vals) > 0:
                    col_min = numeric_vals.min().item()  # convert numpy scalar → Python
                    col_max = numeric_vals.max().item()
            elif pd.api.types.is_datetime64_any_dtype(series) and len(non_null) > 0:
                col_min = str(non_null.min())
                col_max = str(non_null.max())

            rows.append([
                col,
                dtype_label,
                null_count,
                null_pct,
                unique_count,
                sample_vals,
                outlier_count,
                col_min,
                col_max,
            ])

        table = ResultTable(title="Column Profile", columns=columns, rows=rows)

        return StepResult(
            data=None,
            tables=[table],
            facts={
                "row_count": len(work),
                "column_count": len(work.columns),
                "duplicate_row_count": duplicate_row_count,
                "total_missing_pct": total_missing_pct,
            },
        )
