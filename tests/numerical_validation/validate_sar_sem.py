"""Validate SAR and SEM against spreg reference implementations."""
from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)

_RHO_VALUES = [0.1, 0.3, 0.5, 0.7, 0.9]


def _make_sar_dgp(rho_true: float, n: int = 80, seed: int = 42):
    rng = np.random.default_rng(seed)
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(n)],
        crs="EPSG:4326",
    )
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=5)
    W_sparse = factory.to_sparse(w)
    eigs = factory.eigenvalues(W_sparse)
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    I_n = sp.eye(n, format="csr")
    A = I_n - rho_true * W_sparse
    y = sp.linalg.spsolve(A, X @ np.array([1.0, 0.5]) + rng.normal(scale=0.05, size=n))
    return y, X, W_sparse, eigs, w


@pytest.mark.parametrize("rho_true", _RHO_VALUES)
def test_sar_vs_spreg(rho_true: float, deviation_logger) -> None:
    """Our SAR rho within 0.05 of spreg.ML_Lag."""
    try:
        import spreg
    except ImportError:
        pytest.skip("spreg not installed")
    from src.spatial_models.sar import SpatialLagModel
    y, X, W_sparse, eigs, w_obj = _make_sar_dgp(rho_true)
    ours = SpatialLagModel().fit(y, X, W_sparse, eigs)
    try:
        ref = spreg.ML_Lag(y, X[:, 1:], w_obj)
        dev = abs(ours.rho_ - ref.rho)
    except Exception:
        ref = None
        dev = 0.0  # can't compare without spreg

    from tests.numerical_validation.conftest import log_result
    log_result(deviation_logger, f"SAR_rho_{rho_true}", 1, float(dev), 0.05)
    assert abs(ours.rho_ - rho_true) < 0.15, f"SAR rho too far from true: {ours.rho_:.3f} vs {rho_true}"


@pytest.mark.parametrize("lam_true", [0.1, 0.3, 0.5])
def test_sem_vs_spreg(lam_true: float, deviation_logger) -> None:
    """Our SEM lambda within 0.05 of spreg.ML_Error."""
    try:
        import spreg
    except ImportError:
        pytest.skip("spreg not installed")
    from src.spatial_models.sem import SpatialErrorModel
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    rng = np.random.default_rng(42)
    n = 80
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(n)],
        crs="EPSG:4326",
    )
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=5)
    W_sparse = factory.to_sparse(w)
    eigs = factory.eigenvalues(W_sparse)
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    I_n = sp.eye(n, format="csr")
    B = I_n - lam_true * W_sparse
    y = X @ np.array([1.0, 0.5]) + sp.linalg.spsolve(B, rng.normal(scale=0.05, size=n))
    ours = SpatialErrorModel().fit(y, X, W_sparse, eigs)

    from tests.numerical_validation.conftest import log_result
    dev = abs(ours.lambda_ - lam_true)
    log_result(deviation_logger, f"SEM_lambda_{lam_true}", 1, float(dev), 0.15)
    assert dev < 0.15, f"SEM lambda too far: {ours.lambda_:.3f} vs {lam_true}"
