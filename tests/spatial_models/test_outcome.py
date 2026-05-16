"""Tests for src/spatial_models/outcome.py"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import geopandas as gpd
from shapely.geometry import Point

from src.spatial_models.outcome import (
    _resolve_coord_columns,
    _resolve_date_column,
    _to_year_month,
    build_price_change,
)

RNG = np.random.default_rng(42)


def _make_panel(
    n_parcels: int = 20,
    n_months: int = 36,
    date_col: str = "sale_date",
    lat_col: str = "lat",
    lon_col: str = "lon",
    fire_month: str = "2023-08",
) -> pd.DataFrame:
    """Synthetic Phase 1 panel with configurable column names."""
    parcels = [f"TMK{i:04d}" for i in range(n_parcels)]
    months = pd.date_range("2021-01", periods=n_months, freq="MS")
    rows = []
    for pid in parcels:
        base_price = RNG.uniform(12.5, 14.0)
        lat = RNG.uniform(20.5, 21.0)
        lon = RNG.uniform(-157.0, -155.5)
        for month in months:
            ym = month.strftime("%Y-%m")
            post = 1 if ym >= fire_month else 0
            price = base_price - (0.12 * post) + RNG.normal(0, 0.05)
            rows.append({
                "parcel_id": pid,
                date_col: month if date_col == "sale_date" else ym,
                "log_price": price,
                lat_col: lat,
                lon_col: lon,
                "treatment_band": "0-2km" if int(pid[3:]) < 3 else "control",
                "wui_class": "Intermix",
                "dist_to_fire_km": RNG.uniform(0.5, 20.0),
            })
    return pd.DataFrame(rows)


@pytest.fixture()
def panel_sale_date():
    return _make_panel(date_col="sale_date")


@pytest.fixture()
def panel_fe_yearmonth():
    return _make_panel(date_col="fe_yearmonth")


@pytest.fixture()
def panel_year_month():
    return _make_panel(date_col="year_month")


# -- _resolve_date_column -----------------------------------------------------

def test_resolves_sale_date(panel_sale_date):
    assert _resolve_date_column(panel_sale_date) == "sale_date"


def test_resolves_fe_yearmonth(panel_fe_yearmonth):
    assert _resolve_date_column(panel_fe_yearmonth) == "fe_yearmonth"


def test_resolves_year_month(panel_year_month):
    assert _resolve_date_column(panel_year_month) == "year_month"


def test_raises_keyerror_with_actionable_message():
    df = pd.DataFrame({"parcel_id": [1], "log_price": [13.0], "wrong_col": ["2023-01"]})
    with pytest.raises(KeyError, match="Actual columns"):
        _resolve_date_column(df)


# -- _to_year_month -----------------------------------------------------------

def test_converts_datetime_series():
    s = pd.Series(pd.date_range("2021-01", periods=3, freq="MS"))
    result = _to_year_month(s, "sale_date")
    assert result.tolist() == ["2021-01", "2021-02", "2021-03"]


def test_passthrough_yyyy_mm_string():
    s = pd.Series(["2021-01", "2021-02", "2023-08"])
    result = _to_year_month(s, "fe_yearmonth")
    assert result.tolist() == ["2021-01", "2021-02", "2023-08"]


def test_converts_datetime_string():
    s = pd.Series(["2021-01-01", "2021-02-01"])
    result = _to_year_month(s, "sale_date")
    assert result.tolist() == ["2021-01", "2021-02"]


# -- _resolve_coord_columns ---------------------------------------------------

def test_resolves_lat_lon():
    df = _make_panel(lat_col="lat", lon_col="lon")
    assert _resolve_coord_columns(df) == ("lat", "lon")


def test_resolves_latitude_longitude():
    df = _make_panel(lat_col="latitude", lon_col="longitude")
    assert _resolve_coord_columns(df) == ("latitude", "longitude")


def test_raises_if_coords_missing():
    df = pd.DataFrame({"parcel_id": [1], "log_price": [13.0], "sale_date": ["2021-01"]})
    with pytest.raises(KeyError, match="lat/lon"):
        _resolve_coord_columns(df)


# -- build_price_change -------------------------------------------------------

@pytest.mark.parametrize(
    "fixture_name",
    ["panel_sale_date", "panel_fe_yearmonth", "panel_year_month"],
)
def test_succeeds_for_all_date_column_variants(fixture_name, request):
    """Primary regression: KeyError 'date' must not recur for any date column name."""
    panel = request.getfixturevalue(fixture_name)
    gdf = build_price_change(panel, pre_end="2023-07", post_start="2023-09")
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) > 0


def test_output_is_geodataframe(panel_sale_date):
    gdf = build_price_change(panel_sale_date)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf.crs.to_epsg() == 4326


def test_geometry_is_point(panel_sale_date):
    gdf = build_price_change(panel_sale_date)
    assert all(isinstance(g, Point) for g in gdf.geometry)


def test_required_columns_present(panel_sale_date):
    gdf = build_price_change(panel_sale_date)
    required = {"parcel_id", "lat", "lon", "y_raw", "y_residual", "geometry"}
    assert required.issubset(gdf.columns), f"Missing: {required - set(gdf.columns)}"


def test_y_raw_negative_for_treated_parcels(panel_sale_date):
    """Treatment effect is -0.12 in DGP -- treated parcels should show negative y_raw."""
    gdf = build_price_change(panel_sale_date, pre_end="2023-07", post_start="2023-09")
    treated = gdf[gdf["treatment_band"] == "0-2km"]
    if len(treated) > 0:
        assert treated["y_raw"].mean() < 0


def test_y_raw_finite(panel_sale_date):
    gdf = build_price_change(panel_sale_date)
    assert np.isfinite(gdf["y_raw"]).all()


def test_y_residual_nan_when_att_gt_absent(panel_sale_date, tmp_path):
    gdf = build_price_change(
        panel_sale_date, att_gt_path=str(tmp_path / "nonexistent.pkl")
    )
    assert gdf["y_residual"].isna().all()


def test_raises_if_no_pre_period(panel_sale_date):
    with pytest.raises(ValueError, match="No pre-period"):
        build_price_change(panel_sale_date, pre_end="2019-01", post_start="2023-09")


def test_raises_if_no_post_period(panel_sale_date):
    with pytest.raises(ValueError, match="No post-period"):
        build_price_change(panel_sale_date, pre_end="2023-07", post_start="2030-01")


def test_raises_if_log_price_missing():
    df = pd.DataFrame({
        "parcel_id": ["A"],
        "sale_date": ["2021-01"],
        "lat": [20.8],
        "lon": [-156.5],
    })
    with pytest.raises(KeyError, match="log_price"):
        build_price_change(df)


def test_drop_geometry_produces_parquet_compatible_df(panel_sale_date, tmp_path):
    """Regression: Snakemake rule calls gdf.drop(columns='geometry') before parquet."""
    gdf = build_price_change(panel_sale_date)
    df = gdf.drop(columns="geometry")
    out = tmp_path / "price_change.parquet"
    df.to_parquet(out, engine="pyarrow")
    loaded = pd.read_parquet(out)
    assert "geometry" not in loaded.columns
    assert "y_raw" in loaded.columns
    assert len(loaded) == len(gdf)


def test_one_row_per_parcel(panel_sale_date):
    gdf = build_price_change(panel_sale_date)
    assert not gdf["parcel_id"].duplicated().any()


def test_covariates_attached_when_present(panel_sale_date):
    gdf = build_price_change(panel_sale_date)
    assert "treatment_band" in gdf.columns
    assert "dist_to_fire_km" in gdf.columns
