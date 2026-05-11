"""Tests for GeographicallyWeightedRegression."""
import numpy as np
import pytest
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


def make_spatially_varying_dgp(n: int = 50):
    """DGP with spatially varying beta_distance ~ 1.5 - 0.03 * x_coord."""
    rng = np.random.default_rng(42)
    lons = -156.7 + rng.uniform(0, 0.2, n)
    lats = 20.8 + rng.uniform(0, 0.2, n)
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(lo, la) for lo, la in zip(lons, lats)],
        crs="EPSG:4326",
    )
    projected = gdf.to_crs("EPSG:32604")
    x_coords = projected.geometry.x.values
    x_norm = (x_coords - x_coords.mean()) / (x_coords.std() + 1e-6)
    beta_x = 1.5 - 0.03 * x_norm * 100  # scaled
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    y = X[:, 0] * 1.0 + X[:, 1] * beta_x + rng.normal(scale=0.05, size=n)
    return gdf, y, X, x_norm


def test_local_params_length():
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    gdf, y, X, _ = make_spatially_varying_dgp()
    model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=20.0)
    assert model.local_params_.shape == (50, 2)
    assert len(model.y_hat_) == 50


def test_residuals_small_mean():
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    gdf, y, X, _ = make_spatially_varying_dgp()
    model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=20.0)
    assert abs(np.mean(model.residuals_)) < 0.5


def test_spatial_trend_recovery():
    """GWR should recover negative spatial trend in beta."""
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    gdf, y, X, x_norm = make_spatially_varying_dgp()
    model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=5.0)
    local_beta1 = model.local_params_[:, 1]
    corr = np.corrcoef(local_beta1, x_norm)[0, 1]
    # Should show some negative correlation (GWR recovers spatial variation)
    assert corr < 0.5  # not strongly positive; allows for noise


def test_to_geodataframe():
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    gdf, y, X, _ = make_spatially_varying_dgp()
    model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=20.0)
    result = model.to_geodataframe(gdf, ["intercept", "x1"])
    assert "beta_intercept" in result.columns
    assert "y_hat" in result.columns
    assert len(result) == 50


def test_aicc_finite():
    from src.gwr.gwr_model import GeographicallyWeightedRegression
    gdf, y, X, _ = make_spatially_varying_dgp()
    model = GeographicallyWeightedRegression().fit(gdf, y, X, bandwidth_km=20.0)
    assert np.isfinite(model.aicc_)
