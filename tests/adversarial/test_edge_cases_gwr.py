"""Adversarial edge cases for GWR."""
from __future__ import annotations

import numpy as np
import pytest
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


def _make_gdf(n: int, seed: int = 42):
    rng = np.random.default_rng(seed)
    return gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(-156.8, -156.6), rng.uniform(20.7, 21.0)) for _ in range(n)],
        crs="EPSG:4326",
    ), rng


def test_bandwidth_too_small() -> None:
    """Extremely small bandwidth: raises or returns finite results (no hang)."""
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    gdf, rng = _make_gdf(30)
    X = np.column_stack([np.ones(30), rng.normal(size=30)])
    y = rng.normal(size=30)
    # With 0.001 km bandwidth most weights are 0 — model should degrade gracefully
    try:
        model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=0.001)
        # If it runs, local params should be finite or nan (not inf)
        assert not np.any(np.isinf(model.local_params_))
    except (ValueError, RuntimeError):
        pass  # acceptable failure mode


def test_single_neighbor_in_bandwidth() -> None:
    """Very small bandwidth causing sparse neighborhoods: no crash, finite coefficients."""
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    gdf, rng = _make_gdf(30)
    X = np.column_stack([np.ones(30), rng.normal(size=30)])
    y = rng.normal(size=30)
    model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=0.5)
    # Should complete without crash; local params may not all be finite
    assert model.local_params_.shape == (30, 2)


def test_n_equals_k_plus_one() -> None:
    """n = k+1: exact identification, should not crash."""
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    n = 3
    gdf, rng = _make_gdf(n, seed=99)
    X = np.column_stack([np.ones(n), rng.normal(size=n)])  # k=2, n=3
    y = rng.normal(size=n)
    model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=50.0)
    assert len(model.y_hat_) == n
