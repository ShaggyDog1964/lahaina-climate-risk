"""Build spatial outcome variable (price change) for Phase 3 spatial models."""

from __future__ import annotations

import logging
import pickle
from pathlib import Path

import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)

PRE_END = "2023-07"
POST_START = "2023-09"


def build_price_change(
    panel: pd.DataFrame,
    pre_end: str = PRE_END,
    post_start: str = POST_START,
    att_pkl: str | None = None,
) -> gpd.GeoDataFrame:
    """Compute per-parcel log-price change (crude unit-level DiD).

    Args:
        panel: Phase 1 panel with columns parcel_id, date, log_price, lat, lon,
               treatment_band, wui_class, dist_to_fire_km.
        pre_end: Last pre-period month (inclusive), YYYY-MM.
        post_start: First post-period month (inclusive), YYYY-MM.
        att_pkl: Path to results/att_gt.pkl. If provided, loads C-S ATT residuals.

    Returns:
        GeoDataFrame with columns: parcel_id, lat, lon, y_raw, y_residual,
        treatment_band, wui_class, dist_to_fire_km, geometry.
    """
    if "date" not in panel.columns and "period" in panel.columns:
        panel = panel.rename(columns={"period": "date"})

    panel["date"] = pd.to_datetime(panel["date"]).dt.to_period("M").astype(str)

    pre_mask = panel["date"] <= pre_end
    post_mask = panel["date"] >= post_start

    pre_mean = (
        panel[pre_mask].groupby("parcel_id")["log_price"].mean().rename("log_price_pre")
    )
    post_mean = (
        panel[post_mask].groupby("parcel_id")["log_price"].mean().rename("log_price_post")
    )

    change = pd.concat([pre_mean, post_mean], axis=1).dropna()
    change["y_raw"] = change["log_price_post"] - change["log_price_pre"]

    # Covariates — take the last available row per parcel
    covariate_cols = [
        c for c in ["lat", "lon", "treatment_band", "wui_class", "dist_to_fire_km"]
        if c in panel.columns
    ]
    covs = (
        panel.sort_values("date")
        .groupby("parcel_id")[covariate_cols]
        .last()
    )
    result = change.join(covs, how="left").reset_index()

    # ATT residuals (optional)
    if att_pkl is not None and Path(att_pkl).exists():
        try:
            with open(att_pkl, "rb") as fh:
                att_results = pickle.load(fh)
            if hasattr(att_results, "att_gt"):
                att_df = att_results.att_gt
                if "parcel_id" in att_df.columns and "att" in att_df.columns:
                    att_agg = att_df.groupby("parcel_id")["att"].mean()
                    result = result.merge(
                        att_agg.rename("att_residual").reset_index(),
                        on="parcel_id",
                        how="left",
                    )
                    result["y_residual"] = result["att_residual"].fillna(result["y_raw"])
                else:
                    result["y_residual"] = result["y_raw"]
            else:
                result["y_residual"] = result["y_raw"]
        except Exception as exc:
            logger.warning("Could not load ATT results: %s", exc)
            result["y_residual"] = result["y_raw"]
    else:
        result["y_residual"] = result["y_raw"]

    if "lat" not in result.columns or "lon" not in result.columns:
        raise ValueError("Panel must contain lat and lon columns.")

    gdf = gpd.GeoDataFrame(
        result,
        geometry=gpd.points_from_xy(result["lon"], result["lat"]),
        crs="EPSG:4326",
    )
    return gdf


def build_zip_price_change(parcel_gdf: gpd.GeoDataFrame, zip_col: str = "zip_code") -> pd.DataFrame:
    """Aggregate parcel-level price change to zip level."""
    if zip_col not in parcel_gdf.columns:
        raise ValueError(f"Column '{zip_col}' not found.")
    agg = (
        parcel_gdf.groupby(zip_col)[["y_raw", "y_residual", "dist_to_fire_km"]]
        .mean()
        .reset_index()
    )
    return agg
