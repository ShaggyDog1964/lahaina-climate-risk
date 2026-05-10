"""Tests for src/spatial/h3_grid.py."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pytest


@pytest.fixture()
def lahaina_parcels():
    """10-parcel fixture around Lahaina coordinates."""
    rng = np.random.default_rng(0)
    n = 10
    lats = rng.uniform(20.86, 20.90, n)
    lons = rng.uniform(-156.72, -156.66, n)
    prices = rng.uniform(400_000, 1_500_000, n)
    return gpd.GeoDataFrame(
        {
            "parcel_id": [f"P{i}" for i in range(n)],
            "lat": lats,
            "lon": lons,
            "sale_price": prices,
            "log_price": np.log(prices),
        },
        geometry=gpd.points_from_xy(lons, lats),
        crs="EPSG:4326",
    )


def test_assign_h3_index_not_null(lahaina_parcels):
    """h3_index column should be non-null for all parcels."""
    from src.spatial.h3_grid import assign_h3

    parcel_gdf, _ = assign_h3(lahaina_parcels, resolution=8)
    assert "h3_index" in parcel_gdf.columns
    assert parcel_gdf["h3_index"].notna().all()


def test_assign_h3_returns_tuple(lahaina_parcels):
    """assign_h3 returns a tuple of (parcel_gdf, cell_summary_gdf)."""
    from src.spatial.h3_grid import assign_h3

    result = assign_h3(lahaina_parcels, resolution=8)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_assign_h3_cell_summary_columns(lahaina_parcels):
    """Cell summary GeoDataFrame has expected aggregation columns."""
    from src.spatial.h3_grid import assign_h3

    _, cell_gdf = assign_h3(lahaina_parcels, resolution=8)
    for col in ["h3_index", "median_sale_price", "transaction_count", "mean_log_price"]:
        assert col in cell_gdf.columns


def test_assign_h3_cell_count_positive(lahaina_parcels):
    """transaction_count should be positive for all cells."""
    from src.spatial.h3_grid import assign_h3

    _, cell_gdf = assign_h3(lahaina_parcels, resolution=8)
    assert (cell_gdf["transaction_count"] > 0).all()


def test_assign_h3_missing_columns_raises():
    """ValueError raised when required columns are absent."""
    from src.spatial.h3_grid import assign_h3

    gdf = gpd.GeoDataFrame(
        {"parcel_id": ["X"]},
        geometry=gpd.points_from_xy([-156.68], [20.88]),
        crs="EPSG:4326",
    )
    with pytest.raises(ValueError, match="missing required columns"):
        assign_h3(gdf, resolution=8)
