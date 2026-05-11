"""Build zip-level panel from ZHVI, ACS, and HTA data."""

from __future__ import annotations

import numpy as np
import pandas as pd

LAHAINA_ZIP = "96761"
TREATMENT_DATE = "2023-08"
DATE_START = "2018-01"
DATE_END = "2024-12"


def build_zip_panel(
    zhvi: pd.DataFrame,
    acs: pd.DataFrame,
    hta: pd.DataFrame | None,
    output_path: str | None = None,
) -> pd.DataFrame:
    """Merge zip-level panel from ZHVI, ACS covariates, and optional HTA data.

    Args:
        zhvi: Long DataFrame with [zip_code, year_month, zhvi].
        acs: DataFrame with [zip_code, median_hh_income, ...].
        hta: Optional HTA visitor DataFrame with [island, year_month, ...].
        output_path: If provided, save parquet to this path.

    Returns:
        Panel DataFrame with [zip_code, year_month, zhvi, log_zhvi,
        treated, post, ...covariates].
    """
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
    panel["treated"] = (panel["zip_code"] == LAHAINA_ZIP).astype(int)
    panel["post"] = (panel["year_month"] >= TREATMENT_DATE).astype(int)

    if output_path is not None:
        import pathlib
        pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        panel.to_parquet(output_path, engine="pyarrow")

    return panel.reset_index(drop=True)
