"""Tests for src/ingest/parcel.py."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def synthetic_parcel_csv(tmp_path):
    """Create a 20-row synthetic parcel CSV matching the expected schema."""
    rng = np.random.default_rng(42)
    n = 20
    df = pd.DataFrame(
        {
            "parcel_id": [f"P{i:04d}" for i in range(n)],
            "sale_price": rng.uniform(300_000, 2_000_000, n),
            "sale_date": pd.date_range("2020-01-01", periods=n, freq="ME").strftime("%Y-%m-%d"),
            "lat": rng.uniform(20.7, 21.0, n),
            "lon": rng.uniform(-156.9, -156.4, n),
            "land_area_sqft": rng.uniform(5_000, 50_000, n),
            "structure_sqft": rng.uniform(800, 5_000, n),
            "year_built": rng.integers(1950, 2020, n),
            "zoning": rng.choice(["R1", "R2", "C1"], n),
            "tract_geoid": [f"15009{i:06d}" for i in range(n)],
        }
    )
    path = tmp_path / "maui_assessor.csv"
    df.to_csv(path, index=False)
    return str(path)


def test_load_maui_parcels_log_price_finite(synthetic_parcel_csv):
    """log_price should be finite for all positive sale prices."""
    from src.ingest.parcel import load_maui_parcels

    gdf = load_maui_parcels(synthetic_parcel_csv)
    assert "log_price" in gdf.columns
    assert gdf["log_price"].apply(math.isfinite).all()


def test_load_maui_parcels_geometry(synthetic_parcel_csv):
    """GeoDataFrame should have point geometry and EPSG:4326 CRS."""
    import geopandas as gpd
    from src.ingest.parcel import load_maui_parcels

    gdf = load_maui_parcels(synthetic_parcel_csv)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf.crs.to_epsg() == 4326
    assert gdf.geometry.geom_type.eq("Point").all()


def test_load_maui_parcels_row_count(synthetic_parcel_csv):
    """GeoDataFrame should have 20 rows matching the fixture."""
    from src.ingest.parcel import load_maui_parcels

    gdf = load_maui_parcels(synthetic_parcel_csv)
    assert len(gdf) == 20


def test_load_maui_parcels_file_not_found():
    """FileNotFoundError raised for missing file."""
    from src.ingest.parcel import load_maui_parcels

    with pytest.raises(FileNotFoundError):
        load_maui_parcels("data/raw/parcels/does_not_exist.csv")
