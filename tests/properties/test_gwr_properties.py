"""Property-based tests for GWR."""
from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


@given(n=st.integers(min_value=20, max_value=60))
@settings(max_examples=10, deadline=30_000)
def test_gwr_local_params_finite(n: int) -> None:
    """All local GWR coefficients are finite."""
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    rng = np.random.default_rng(n)
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(-156.8, -156.6), rng.uniform(20.7, 21.0)) for _ in range(n)],
        crs="EPSG:4326",
    )
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    y = X @ np.array([1.0, 0.5]) + rng.normal(scale=0.1, size=n)
    model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=20.0)
    assert np.all(np.isfinite(model.local_params_))


@given(n=st.integers(min_value=10, max_value=50))
@settings(max_examples=10, deadline=30_000)
def test_gwr_yhat_length(n: int) -> None:
    """y_hat_ always has length n."""
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    rng = np.random.default_rng(n * 7)
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(-156.8, -156.6), rng.uniform(20.7, 21.0)) for _ in range(n)],
        crs="EPSG:4326",
    )
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    y = rng.normal(size=n)
    model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=15.0)
    assert len(model.y_hat_) == n
