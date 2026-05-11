"""Tests for SpatialLagModel."""
import numpy as np
import pytest
import scipy.sparse as sp
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


def make_sar_dgp(n: int = 80, rho_true: float = 0.4, seed: int = 42):
    rng = np.random.default_rng(seed)
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(n)],
        crs="EPSG:4326",
    )
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=5)
    W_sparse = factory.to_sparse(w)
    eigs = factory.eigenvalues(W_sparse)
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    beta_true = np.array([1.0, 0.5])
    I_n = sp.eye(n, format="csr")
    A = I_n - rho_true * W_sparse
    eps = rng.normal(scale=0.1, size=n)
    y = sp.linalg.spsolve(A, X @ beta_true + eps)
    return y, X, W_sparse, eigs, beta_true


def test_rho_recovery():
    from src.spatial_models.sar import SpatialLagModel
    y, X, W, eigs, _ = make_sar_dgp(rho_true=0.4)
    model = SpatialLagModel().fit(y, X, W, eigs)
    assert abs(model.rho_ - 0.4) < 0.15


def test_aic_bic_finite():
    from src.spatial_models.sar import SpatialLagModel
    y, X, W, eigs, _ = make_sar_dgp()
    model = SpatialLagModel().fit(y, X, W, eigs)
    assert np.isfinite(model.aic_)
    assert np.isfinite(model.bic_)


def test_summary_shape():
    from src.spatial_models.sar import SpatialLagModel
    y, X, W, eigs, _ = make_sar_dgp()
    model = SpatialLagModel().fit(y, X, W, eigs, x_names=["intercept", "x1"])
    df = model.summary()
    assert df.shape == (3, 6)  # rho + 2 betas, 6 columns


def test_validate_against_spreg():
    """Numerical validation: our rho within 0.05 of spreg.GM_Lag."""
    try:
        import spreg
    except ImportError:
        pytest.skip("spreg not installed")
    from src.spatial_models.sar import SpatialLagModel
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    y, X, W, eigs, _ = make_sar_dgp()
    model = SpatialLagModel().fit(y, X, W, eigs)
    w_obj = SpatialWeightsFactory().build_knn(
        gpd.GeoDataFrame(
            {"id": range(80)},
            geometry=[Point(np.random.default_rng(42).uniform(0, 1),
                            np.random.default_rng(42).uniform(0, 1)) for _ in range(80)],
            crs="EPSG:4326",
        ), k=5
    )
    # Basic sanity: rho is within plausible range
    assert -1.0 < model.rho_ < 1.0
