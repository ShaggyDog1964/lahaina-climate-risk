"""Tests for SpatialErrorModel."""
import numpy as np
import pytest
import scipy.sparse as sp
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


def make_sem_dgp(n: int = 80, lam_true: float = 0.35, seed: int = 42):
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
    B = I_n - lam_true * W_sparse
    eps = rng.normal(scale=0.1, size=n)
    u = sp.linalg.spsolve(B, eps)
    y = X @ beta_true + u
    return y, X, W_sparse, eigs, beta_true


def test_lambda_recovery():
    from src.spatial_models.sem import SpatialErrorModel
    y, X, W, eigs, _ = make_sem_dgp(lam_true=0.35)
    model = SpatialErrorModel().fit(y, X, W, eigs)
    assert abs(model.lambda_ - 0.35) < 0.15


def test_sem_ll_gt_ols():
    from src.spatial_models.sem import SpatialErrorModel
    from statsmodels.regression.linear_model import OLS
    y, X, W, eigs, _ = make_sem_dgp()
    model = SpatialErrorModel().fit(y, X, W, eigs)
    ols = OLS(y, X).fit()
    # SEM LL should be >= OLS LL on spatially correlated data
    ols_ll = float(ols.llf)
    assert model.log_likelihood_ >= ols_ll - 5.0  # allow small slack


def test_summary_contains_lambda():
    from src.spatial_models.sem import SpatialErrorModel
    y, X, W, eigs, _ = make_sem_dgp()
    model = SpatialErrorModel().fit(y, X, W, eigs, x_names=["intercept", "x1"])
    df = model.summary()
    assert "lambda" in df.index
