"""Long-panel construction merging parcel transactions with FRED macro data."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd


def build_panel(
    parcels: gpd.GeoDataFrame,
    fred: pd.DataFrame,
    fire_date: str = "2023-08-08",
) -> pd.DataFrame:
    """Build a long-format panel merging parcel sales with FRED controls.

    Args:
        parcels: GeoDataFrame with parcel-level columns including sale_date,
            parcel_id, tract_geoid, and all spatial features.
        fred: Long-format FRED DataFrame with columns [date, series_id, value].
        fire_date: ISO date string for the Lahaina fire (2023-08-08).

    Returns:
        Long-panel DataFrame sorted by (parcel_id, sale_date) with columns:
            - All parcel columns (minus geometry)
            - FRED macro controls pivoted wide (one column per series_id)
            - post: 1 if sale_date >= fire_date, else 0
            - event_time: integer months since fire (negative=pre, positive=post)
            - fe_block: census-block fixed effect identifier (= tract_geoid)
            - fe_yearmonth: year-month fixed effect string (YYYY-MM)
            - year_month: period string for merge key

    Raises:
        KeyError: If required columns are absent from parcels or fred.
    """
    fire_dt = pd.Timestamp(fire_date)

    df = pd.DataFrame(parcels.drop(columns="geometry", errors="ignore")).copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["year_month"] = df["sale_date"].dt.to_period("M").astype(str)
    df["post"] = (df["sale_date"] >= fire_dt).astype(int)

    fire_period = pd.Period(fire_date, freq="M")
    df["event_time"] = df["sale_date"].dt.to_period("M").apply(
        lambda p: (p - fire_period).n
    )

    df["fe_block"] = df["tract_geoid"].astype(str)
    df["fe_yearmonth"] = df["year_month"]

    # Pivot FRED from long to wide
    fred_copy = fred.copy()
    fred_copy["year_month"] = fred_copy["date"].dt.to_period("M").astype(str)
    fred_wide = (
        fred_copy.groupby(["year_month", "series_id"])["value"]
        .mean()
        .unstack("series_id")
        .reset_index()
    )

    panel = df.merge(fred_wide, on="year_month", how="left")
    panel = panel.sort_values(["parcel_id", "sale_date"]).reset_index(drop=True)

    return panel
