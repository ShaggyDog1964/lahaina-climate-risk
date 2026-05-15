"""Build zip-level panel from ZHVI, ACS, and HTA data."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.ingest.exceptions import DataValidationError

LAHAINA_ZIP = "96761"
TREATMENT_DATE = "2023-08"
DATE_START = "2018-01"
DATE_END = "2024-12"


def _coerce_zip_code(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize zip_code to zero-padded 5-char string. Returns copy."""
    if "zip_code" not in df.columns:
        raise DataValidationError(
            f"DataFrame missing 'zip_code' column. Got: {df.columns.tolist()}"
        )
    df = df.copy()
    df["zip_code"] = df["zip_code"].astype(str).str.strip().str.zfill(5)
    return df


def build_zip_panel(
    zhvi: pd.DataFrame,
    acs: pd.DataFrame,
    hta: pd.DataFrame | None,
    output_path: str | None = None,
    treated_zip: str = LAHAINA_ZIP,
    fire_date: str = TREATMENT_DATE,
) -> pd.DataFrame:
    """Merge zip-level panel from ZHVI, ACS covariates, and optional HTA data.

    Args:
        zhvi: Long DataFrame with [zip_code, year_month, zhvi].
        acs: DataFrame with [zip_code, median_hh_income, ...].
        hta: Optional HTA visitor DataFrame with [island, year_month, ...].
        output_path: If provided, save parquet to this path.
        treated_zip: ZIP code of the treated unit (default: Lahaina 96761).
        fire_date: Year-month string marking the treatment date (default: 2023-08).

    Returns:
        Panel DataFrame with [zip_code, year_month, zhvi, log_zhvi,
        treated, post, ...covariates].
    """
    # Normalize zip_code to str dtype before any merge
    zhvi = _coerce_zip_code(zhvi)
    acs = _coerce_zip_code(acs) if acs is not None else acs

    # Filter to date range
    panel = zhvi.copy()
    panel = panel[
        (panel["year_month"] >= DATE_START) & (panel["year_month"] <= DATE_END)
    ].copy()

    # Merge ACS covariates (left join on zip_code — time-invariant)
    if acs is not None and len(acs) > 0:
        acs_cols = ["zip_code"] + [c for c in acs.columns if c != "zip_code"]
        panel = panel.merge(acs[acs_cols], on="zip_code", how="left")

    # Merge HTA (island-level, join on year_month only as proxy)
    if hta is not None and len(hta) > 0:
        hta_agg = (
            hta.groupby("year_month")[["visitor_arrivals", "visitor_expenditure_m"]]
            .sum()
            .reset_index()
        )
        panel = panel.merge(hta_agg, on="year_month", how="left")

    # Derived columns
    panel["log_zhvi"] = np.log(panel["zhvi"].clip(lower=1e-6))
    panel["treated"] = (panel["zip_code"] == str(treated_zip).zfill(5)).astype(int)
    panel["post"] = (panel["year_month"] >= fire_date).astype(int)

    if output_path is not None:
        import pathlib
        pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        panel.to_parquet(output_path, engine="pyarrow")

    return panel.reset_index(drop=True)
