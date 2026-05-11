"""HTA monthly visitor data ingestion."""

from __future__ import annotations

import pandas as pd


def fetch_hta_visitors() -> pd.DataFrame:
    """Load HTA monthly visitor data for Hawaii.

    Primary source: DBEDT/HTA monthly visitor CSV.
    # DATA SOURCE: DBEDT HTA monthly visitors — download manually from
    # https://dbedt.hawaii.gov/visitor/tourism-data/

    Returns:
        DataFrame with columns [island, year_month, visitor_arrivals,
        visitor_expenditure_m].

    Raises:
        NotImplementedError: Always — data must be downloaded manually.
    """
    raise NotImplementedError(
        "HTA visitor data requires manual download from "
        "https://dbedt.hawaii.gov/visitor/tourism-data/. "
        "Save as data/raw/hta/hta_monthly_visitors.csv and implement loader."
    )


def load_hta_visitors(path: str) -> pd.DataFrame:
    """Load pre-downloaded HTA visitor CSV.

    Args:
        path: Path to local HTA CSV file.

    Returns:
        DataFrame with columns [island, year_month, visitor_arrivals,
        visitor_expenditure_m].
    """
    df = pd.read_csv(path)
    required = {"island", "year_month", "visitor_arrivals", "visitor_expenditure_m"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"HTA CSV missing columns: {missing}")

    df["year_month"] = df["year_month"].astype(str)
    df["visitor_arrivals"] = pd.to_numeric(df["visitor_arrivals"], errors="coerce")
    df["visitor_expenditure_m"] = pd.to_numeric(
        df["visitor_expenditure_m"], errors="coerce"
    )
    return df[list(required)].reset_index(drop=True)
