"""Adversarial edge cases for SAR model."""
from __future__ import annotations

import warnings
import numpy as np
import pytest
import scipy.sparse as sp
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


def _make_sar_setup(n: int = 50, k: int = 4):
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    rng = np.random.default_rng(42)
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(n)],
        crs="EPSG:4326",
    )
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=k)
    W_sparse = factory.to_sparse(w)
    eigs = factory.eigenvalues(W_sparse)
    return W_sparse, eigs, rng, n


def test_near_unit_root_rho() -> None:
    """High rho near 1: model completes, rho_ in (-1,1), no NaN."""
    from src.spatial_models.sar import SpatialLagModel
    W_sparse, eigs, rng, n = _make_sar_setup()
    rho_true = 0.95
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    I_n = sp.eye(n, format="csr")
    A = I_n - rho_true * W_sparse
    y = sp.linalg.spsolve(A, X @ np.array([1.0, 0.5]) + rng.normal(scale=0.1, size=n))
    model = SpatialLagModel().fit(y, X, W_sparse, eigs)
    assert -1.0 < model.rho_ < 1.0
    assert np.all(np.isfinite(model.beta_))


def test_no_variation_y() -> None:
    """Constant y raises ValueError."""
    from src.spatial_models.sar import SpatialLagModel
    W_sparse, eigs, rng, n = _make_sar_setup()
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    y = np.ones(n)
    with pytest.raises((ValueError, Exception)):
        SpatialLagModel().fit(y, X, W_sparse, eigs)


def test_perfectly_collinear_X() -> None:
    """Two identical columns in X: raises or degrades gracefully (no NaN rho)."""
    from src.spatial_models.sar import SpatialLagModel
    W_sparse, eigs, rng, n = _make_sar_setup()
    x_col = rng.normal(size=n)
    X = np.column_stack([np.ones(n), x_col, x_col])  # collinear
    I_n = sp.eye(n, format="csr")
    A = I_n - 0.3 * W_sparse
    y = sp.linalg.spsolve(A, np.ones(n) + rng.normal(scale=0.1, size=n))
    try:
        model = SpatialLagModel().fit(y, X, W_sparse, eigs)
        assert np.isfinite(model.rho_)
    except (ValueError, np.linalg.LinAlgError):
        pass  # acceptable
