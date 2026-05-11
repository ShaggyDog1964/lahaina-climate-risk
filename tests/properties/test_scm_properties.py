"""Property-based tests for SCM implementations."""
from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

np.random.seed(42)


def _make_scm_data(rho_true: float, n: int, J: int, T: int = 30):
    """Synthetic SCM panel data."""
    rng = np.random.default_rng(abs(int(rho_true * 1000)) % 2**31)
    # Donor outcomes
    Y0 = rng.normal(0, 1, (T, J))
    # Treated: weighted combo + noise
    w_true = rng.dirichlet(np.ones(J))
    Y1 = Y0 @ w_true + rng.normal(0, 0.05, T)
    # Pre-period only
    T_pre = T // 2
    return Y0[:T_pre], Y1[:T_pre], w_true


@given(
    rho_true=st.floats(min_value=-0.8, max_value=0.8),
    n=st.integers(min_value=10, max_value=30),
    J=st.integers(min_value=3, max_value=8),
)
@settings(max_examples=20, deadline=30_000)
def test_adh_weights_sum_to_one(rho_true: float, n: int, J: int) -> None:
    """ADH weights always sum to 1 and are non-negative."""
    from src.scm.adh_scm import ADHSyntheticControl
    Y0_pre, Y1_pre, _ = _make_scm_data(rho_true, n, J)
    X0 = Y0_pre[:3] if Y0_pre.shape[0] >= 3 else Y0_pre
    X1 = Y1_pre[:3] if Y1_pre.shape[0] >= 3 else Y1_pre
    model = ADHSyntheticControl()
    model.fit(X0, X1, Y0_pre, Y1_pre)
    assert abs(model.w_.sum() - 1.0) < 1e-4
    assert np.all(model.w_ >= -1e-6)


@given(rho_true=st.floats(min_value=0.05, max_value=0.85))
@settings(max_examples=15, deadline=60_000)
def test_sar_rho_in_bounds(rho_true: float) -> None:
    """SAR estimated rho always in (-1, 1)."""
    import scipy.sparse as sp
    import geopandas as gpd
    from shapely.geometry import Point
    from src.spatial_models.sar import SpatialLagModel
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    rng = np.random.default_rng(42)
    n = 40
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(n)],
        crs="EPSG:4326",
    )
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=4)
    W_sparse = factory.to_sparse(w)
    eigs = factory.eigenvalues(W_sparse)
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    I_n = sp.eye(n, format="csr")
    A = I_n - rho_true * W_sparse
    y = sp.linalg.spsolve(A, X @ np.array([1.0, 0.5]) + rng.normal(scale=0.1, size=n))
    model = SpatialLagModel().fit(y, X, W_sparse, eigs)
    assert -1.0 < model.rho_ < 1.0
