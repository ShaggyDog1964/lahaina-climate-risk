"""Tests for src/spatial/panel_builder.py."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def synthetic_panel_inputs():
    """Synthetic 3-parcel x 24-month inputs for panel builder."""
    rng = np.random.default_rng(42)

    dates = pd.date_range("2022-01-01", periods=24, freq="MS")
    rows = []
    for pid in ["P001", "P002", "P003"]:
        for d in dates:
            price = rng.uniform(400_000, 1_000_000)
            rows.append(
                {
                    "parcel_id": pid,
                    "sale_date": d,
                    "sale_price": price,
                    "lat": 20.88,
                    "lon": -156.68,
                    "land_area_sqft": 8_000.0,
                    "structure_sqft": 1_500.0,
                    "year_built": 1985,
                    "zoning": "R1",
                    "tract_geoid": "150090401001",
                    "log_price": np.log(price),
                    "treatment_band": "5-10km",
                    "wui_class": "Interface",
                    "h3_index": "88754e6499fffff",
                    "dist_to_fire_km": 7.0,
                }
            )

    parcels_df = pd.DataFrame(rows)
    parcels = gpd.GeoDataFrame(
        parcels_df,
        geometry=gpd.points_from_xy(parcels_df.lon, parcels_df.lat),
        crs="EPSG:4326",
    )

    fred_rows = []
    for sid in ["UNRATE", "FEDFUNDS"]:
        for d in dates:
            fred_rows.append({"date": d, "series_id": sid, "value": rng.uniform(1.0, 8.0)})
    fred = pd.DataFrame(fred_rows)

    return parcels, fred


def test_post_flips_at_fire_date(synthetic_panel_inputs):
    """post == 0 before fire_date, post == 1 on/after fire_date."""
    from src.spatial.panel_builder import build_panel

    parcels, fred = synthetic_panel_inputs
    panel = build_panel(parcels, fred, fire_date="2023-08-08")

    pre = panel[panel["sale_date"] < "2023-08-08"]["post"]
    post = panel[panel["sale_date"] >= "2023-08-08"]["post"]
    assert (pre == 0).all()
    assert (post == 1).all()


def test_event_time_is_integer(synthetic_panel_inputs):
    """event_time column must contain integer values."""
    from src.spatial.panel_builder import build_panel

    parcels, fred = synthetic_panel_inputs
    panel = build_panel(parcels, fred, fire_date="2023-08-08")

    assert panel["event_time"].apply(lambda x: float(x) == int(x)).all()


def test_panel_sorted_by_parcel_date(synthetic_panel_inputs):
    """Panel should be sorted by (parcel_id, sale_date)."""
    from src.spatial.panel_builder import build_panel

    parcels, fred = synthetic_panel_inputs
    panel = build_panel(parcels, fred, fire_date="2023-08-08")

    expected = panel.sort_values(["parcel_id", "sale_date"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(
        panel[["parcel_id", "sale_date"]].reset_index(drop=True),
        expected[["parcel_id", "sale_date"]].reset_index(drop=True),
    )


def test_panel_has_fe_columns(synthetic_panel_inputs):
    """Panel should contain fe_block and fe_yearmonth columns."""
    from src.spatial.panel_builder import build_panel

    parcels, fred = synthetic_panel_inputs
    panel = build_panel(parcels, fred, fire_date="2023-08-08")

    assert "fe_block" in panel.columns
    assert "fe_yearmonth" in panel.columns
