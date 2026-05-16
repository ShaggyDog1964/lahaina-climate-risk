"""
src/spatial_models/outcome.py

Constructs the parcel-level spatial outcome variable (price change)
for use in Phase 3 spatial econometric models.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

logger = logging.getLogger(__name__)

_DATE_COLUMN_CANDIDATES = ["sale_date", "fe_yearmonth", "year_month", "date"]


def _resolve_date_column(panel: pd.DataFrame) -> str:
    """Identify the year-month column by checking known candidates in order.

    Raises
    ------
    KeyError
        If none of the candidate columns are found.
    """
    for candidate in _DATE_COLUMN_CANDIDATES:
        if candidate in panel.columns:
            logger.debug("Using '%s' as date column.", candidate)
            return candidate
    raise KeyError(
        f"No date column found in panel. Tried: {_DATE_COLUMN_CANDIDATES}. "
        f"Actual columns: {panel.columns.tolist()}. "
        "Check that Phase 1 panel_builder.py produced the expected schema."
    )


def _to_year_month(series: pd.Series, col_name: str) -> pd.Series:
    """Normalize any date-like series to YYYY-MM string.

    Handles: datetime64, datetime string, existing YYYY-MM string.
    """
    sample = str(series.dropna().iloc[0]) if not series.dropna().empty else ""
    if len(sample) == 7 and sample[4] == "-" and sample[:4].isdigit():
        return series.astype(str)
    try:
        return pd.to_datetime(series).dt.to_period("M").astype(str)
    except Exception as exc:
        raise ValueError(
            f"Column '{col_name}' (sample: '{sample}') cannot be converted to "
            "YYYY-MM period. Provide a datetime or YYYY-MM string column."
        ) from exc


def _resolve_coord_columns(panel: pd.DataFrame) -> tuple[str, str]:
    """Identify lat/lon columns in the panel.

    Returns
    -------
    tuple[str, str]
        (lat_col, lon_col) names.

    Raises
    ------
    KeyError
        If coordinate columns cannot be found.
    """
    lat_candidates = ["lat", "latitude", "LAT", "y"]
    lon_candidates = ["lon", "longitude", "LON", "lng", "x"]
    lat_col = next((c for c in lat_candidates if c in panel.columns), None)
    lon_col = next((c for c in lon_candidates if c in panel.columns), None)
    if lat_col is None or lon_col is None:
        raise KeyError(
            f"Could not find lat/lon columns. "
            f"Tried lat: {lat_candidates}, lon: {lon_candidates}. "
            f"Actual columns: {panel.columns.tolist()}"
        )
    return lat_col, lon_col


def build_price_change(
    panel: pd.DataFrame,
    pre_end: str = "2023-07",
    post_start: str = "2023-09",
    att_gt_path: str = "results/att_gt.pkl",
) -> gpd.GeoDataFrame:
    """Construct parcel-level spatial outcome variable from Phase 1 panel.

    For each parcel i:
        y_raw      = mean(log_price, post) - mean(log_price, pre)
        y_residual = Callaway-Sant'Anna ATT residual if available, else NaN

    Parameters
    ----------
    panel : pd.DataFrame
        Phase 1 long panel from data/final/panel.parquet.
    pre_end : str
        Last pre-period year-month, inclusive (YYYY-MM).
    post_start : str
        First post-period year-month, inclusive (YYYY-MM).
    att_gt_path : str
        Path to pickled Callaway-Sant'Anna ATT results. Missing/unreadable
        produces y_residual=NaN silently (logged at INFO).

    Returns
    -------
    gpd.GeoDataFrame
        One row per parcel with columns: parcel_id, lat, lon, y_raw, y_residual,
        treatment_band, wui_class, dist_to_fire_km, geometry (Point, EPSG:4326).

    Raises
    ------
    KeyError
        If required columns are missing from the panel.
    ValueError
        If pre or post period yields no observations, or no parcels have both.
    """
    panel = panel.copy()

    # 1. Resolve and normalise the date column
    date_col = _resolve_date_column(panel)
    panel["_year_month"] = _to_year_month(panel[date_col], date_col)

    # 2. Validate required columns
    required = {"parcel_id", "log_price"}
    missing = required - set(panel.columns)
    if missing:
        raise KeyError(
            f"Panel missing required columns: {sorted(missing)}. "
            f"Actual columns: {panel.columns.tolist()}"
        )

    # 3. Pre/post masks
    pre_mask = panel["_year_month"] <= pre_end
    post_mask = panel["_year_month"] >= post_start

    if pre_mask.sum() == 0:
        raise ValueError(
            f"No pre-period observations found with _year_month <= '{pre_end}'. "
            f"year_month range: {panel['_year_month'].min()} "
            f"to {panel['_year_month'].max()}"
        )
    if post_mask.sum() == 0:
        raise ValueError(
            f"No post-period observations found with _year_month >= '{post_start}'. "
            f"year_month range: {panel['_year_month'].min()} "
            f"to {panel['_year_month'].max()}"
        )

    # 4. Per-parcel mean log_price pre and post
    pre_means = (
        panel.loc[pre_mask]
        .groupby("parcel_id")["log_price"]
        .mean()
        .rename("log_price_pre")
    )
    post_means = (
        panel.loc[post_mask]
        .groupby("parcel_id")["log_price"]
        .mean()
        .rename("log_price_post")
    )
    price_change = pd.concat([pre_means, post_means], axis=1).dropna()
    price_change["y_raw"] = price_change["log_price_post"] - price_change["log_price_pre"]
    price_change = price_change.reset_index()

    if len(price_change) == 0:
        raise ValueError(
            "No parcels have observations in both pre and post periods. "
            "Check pre_end and post_start arguments."
        )

    # 5. Merge parcel-level covariates
    covariate_cols = [
        c for c in ["treatment_band", "wui_class", "dist_to_fire_km"]
        if c in panel.columns
    ]
    if covariate_cols:
        covariates = (
            panel.groupby("parcel_id")[covariate_cols]
            .first()
            .reset_index()
        )
        price_change = price_change.merge(covariates, on="parcel_id", how="left")
    else:
        logger.warning(
            "No covariate columns found (%s). Columns will be absent.",
            ["treatment_band", "wui_class", "dist_to_fire_km"],
        )

    # 6. Callaway-Sant'Anna ATT residuals (optional -- degrade to NaN if absent)
    att_path = Path(att_gt_path)
    if att_path.exists():
        try:
            with open(att_path, "rb") as f:
                att_gt = pickle.load(f)
            if isinstance(att_gt, pd.DataFrame) and "parcel_id" in att_gt.columns:
                residuals = att_gt[["parcel_id", "residual"]].rename(
                    columns={"residual": "y_residual"}
                )
                price_change = price_change.merge(residuals, on="parcel_id", how="left")
            else:
                logger.warning(
                    "att_gt.pkl type %s not recognized for residual extraction. "
                    "y_residual will be NaN.",
                    type(att_gt),
                )
                price_change["y_residual"] = np.nan
        except Exception as exc:
            logger.warning("Failed to load att_gt.pkl (%s). y_residual set to NaN.", exc)
            price_change["y_residual"] = np.nan
    else:
        logger.info("att_gt.pkl not found at '%s'. y_residual set to NaN.", att_gt_path)
        price_change["y_residual"] = np.nan

    # 7. Attach coordinates and build GeoDataFrame
    lat_col, lon_col = _resolve_coord_columns(panel)
    coords = (
        panel.groupby("parcel_id")[[lat_col, lon_col]]
        .first()
        .reset_index()
        .rename(columns={lat_col: "lat", lon_col: "lon"})
    )
    price_change = price_change.merge(coords, on="parcel_id", how="left")

    n_missing = price_change[["lat", "lon"]].isna().any(axis=1).sum()
    if n_missing > 0:
        logger.warning("%d parcels missing lat/lon -- dropping.", n_missing)
        price_change = price_change.dropna(subset=["lat", "lon"])

    geometry = [
        Point(lon, lat)
        for lon, lat in zip(price_change["lon"], price_change["lat"], strict=False)
    ]
    gdf = gpd.GeoDataFrame(price_change, geometry=geometry, crs="EPSG:4326")

    logger.info(
        "build_price_change: %d parcels, y_raw mean=%.4f std=%.4f",
        len(gdf),
        gdf["y_raw"].mean(),
        gdf["y_raw"].std(),
    )
    return gdf


def build_zip_price_change(
    parcel_gdf: gpd.GeoDataFrame, zip_col: str = "zip_code"
) -> pd.DataFrame:
    """Aggregate parcel-level price change to zip level."""
    if zip_col not in parcel_gdf.columns:
        raise ValueError(f"Column '{zip_col}' not found.")
    return (
        parcel_gdf.groupby(zip_col)[["y_raw", "y_residual", "dist_to_fire_km"]]
        .mean()
        .reset_index()
    )
