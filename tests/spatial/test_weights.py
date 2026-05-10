"""Tests for src/spatial/weights.py."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pytest


@pytest.fixture()
def parcel_gdf_20():
    """20-parcel fixture spread around Maui."""
    rng = np.random.default_rng(7)
    n = 20
    lons = rng.uniform(-156.9, -156.3, n)
    lats = rng.uniform(20.7, 21.1, n)
    return gpd.GeoDataFrame(
        {"parcel_id": [f"P{i}" for i in range(n)]},
        geometry=gpd.points_from_xy(lons, lats),
        crs="EPSG:4326",
    )


def test_build_weights_n(parcel_gdf_20):
    """KNN weights object should have n == 20."""
    from src.spatial.weights import build_weights

    w = build_weights(parcel_gdf_20, k=8)
    assert w.n == 20


def test_build_weights_mean_neighbors(parcel_gdf_20):
    """KNN weights should have mean_neighbors > 0."""
    from src.spatial.weights import build_weights

    w = build_weights(parcel_gdf_20, k=8)
    assert w.mean_neighbors > 0


def test_build_inverse_distance_weights_n(parcel_gdf_20):
    """IDW weights object should have n == 20."""
    from src.spatial.weights import build_inverse_distance_weights

    w = build_inverse_distance_weights(parcel_gdf_20, threshold_km=50.0)
    assert w.n == 20


def test_build_inverse_distance_weights_mean_neighbors(parcel_gdf_20):
    """IDW weights should have mean_neighbors > 0."""
    from src.spatial.weights import build_inverse_distance_weights

    w = build_inverse_distance_weights(parcel_gdf_20, threshold_km=50.0)
    assert w.mean_neighbors > 0


def test_build_weights_saves_file(parcel_gdf_20, tmp_path):
    """build_weights saves GAL file when output_path is provided."""
    import os
    from src.spatial.weights import build_weights

    out = str(tmp_path / "weights_knn.gal")
    build_weights(parcel_gdf_20, k=4, output_path=out)
    assert os.path.exists(out)


def test_build_weights_too_few_obs():
    """ValueError raised when n < k+1."""
    from src.spatial.weights import build_weights

    gdf = gpd.GeoDataFrame(
        {"parcel_id": ["A", "B"]},
        geometry=gpd.points_from_xy([-156.68, -156.67], [20.88, 20.87]),
        crs="EPSG:4326",
    )
    with pytest.raises(ValueError, match="at least"):
        build_weights(gdf, k=8)
