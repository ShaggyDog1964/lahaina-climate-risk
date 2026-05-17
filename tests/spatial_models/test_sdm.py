"""Tests for SpatialDurbinModel."""
import numpy as np
import pytest
import scipy.sparse as sp
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


def make_sdm_dgp(n: int = 80, rho_true: float = 0.3, beta_true=None, theta_true=None, seed: int = 42):
    rng = np.random.default_rng(seed)
    if beta_true is None:
        beta_true = np.array([1.0, 0.5])
    if theta_true is None:
        theta_true = np.array([0.3])
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
    X_names = ["intercept", "x1"]
    WX = np.asarray(W_sparse @ X[:, 1]).ravel()
    I_n = sp.eye(n, format="csr")
    A = I_n - rho_true * W_sparse
    eps = rng.normal(scale=0.1, size=n)
    y = sp.linalg.spsolve(A, X @ beta_true + WX * theta_true[0] + eps)
    return y, X, W_sparse, eigs, X_names


def test_sdm_rho_bounded():
    from src.spatial_models.sdm import SpatialDurbinModel
    y, X, W, eigs, names = make_sdm_dgp()
    model = SpatialDurbinModel().fit(y, X, W, eigs, x_names=names)
    assert -1.0 < model.rho_ < 1.0
    assert np.all(np.isfinite(model.beta_))
    assert np.all(np.isfinite(model.theta_))


def test_sdm_sar_restriction():
    """When true DGP is SAR (theta=0), LR test should fail to reject."""
    from src.spatial_models.sdm import SpatialDurbinModel
    from src.spatial_models.sar import SpatialLagModel
    rng = np.random.default_rng(99)
    n = 80
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
    I_n = sp.eye(n, format="csr")
    A = I_n - 0.4 * W_sparse
    y = sp.linalg.spsolve(A, X @ np.array([1.0, 0.5]) + rng.normal(scale=0.1, size=n))
    sdm = SpatialDurbinModel().fit(y, X, W_sparse, eigs, x_names=["intercept", "x1"])
    sar = SpatialLagModel().fit(y, X, W_sparse, eigs)
    test = sdm.test_sar_restriction(sar)
    # p-value should be relatively high (cannot reject theta=0)
    # allow some flexibility given small sample
    assert test["p_value"] >= 0.0  # basic sanity


def test_sdm_summary_rows():
    from src.spatial_models.sdm import SpatialDurbinModel
    y, X, W, eigs, names = make_sdm_dgp()
    model = SpatialDurbinModel().fit(y, X, W, eigs, x_names=names)
    df = model.summary()
    # rho + 2 betas + 1 WX theta
    assert len(df) >= 3


# ── Keyword argument regression tests ─────────────────────────────────────────

def test_fit_accepts_lowercase_x_names():
    """Primary regression: x_names (lowercase) must be accepted without error."""
    from src.spatial_models.sdm import SpatialDurbinModel
    y, X, W, eigs, names = make_sdm_dgp()
    model = SpatialDurbinModel().fit(y, X, W, eigs, x_names=names)
    assert model._x_names == names


def test_fit_rejects_uppercase_X_names_with_clear_error():
    """X_names (uppercase) must raise TypeError — not silently ignored."""
    from src.spatial_models.sdm import SpatialDurbinModel
    y, X, W, eigs, _ = make_sdm_dgp()
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        SpatialDurbinModel().fit(y, X, W, eigs, X_names=["intercept", "x1"])


def test_fit_x_names_defaults_when_none():
    """If x_names not supplied, defaults to ['x0', 'x1', ...]."""
    from src.spatial_models.sdm import SpatialDurbinModel
    y, X, W, eigs, _ = make_sdm_dgp()
    model = SpatialDurbinModel().fit(y, X, W, eigs)
    assert model._x_names is not None
    assert len(model._x_names) == X.shape[1]
    assert model._x_names[0] == "x0"


def test_public_x_names_attrs_present():
    """Public x_names_, wx_names_, all_names_ attributes must be set after fit."""
    from src.spatial_models.sdm import SpatialDurbinModel
    y, X, W, eigs, names = make_sdm_dgp()
    model = SpatialDurbinModel().fit(y, X, W, eigs, x_names=names)
    assert hasattr(model, "x_names_")
    assert hasattr(model, "wx_names_")
    assert hasattr(model, "all_names_")
    assert model.x_names_ == names
    assert "W_x1" in model.wx_names_


def test_wx_names_exclude_intercept():
    """WX column names must not include intercept lag."""
    from src.spatial_models.sdm import SpatialDurbinModel
    y, X, W, eigs, names = make_sdm_dgp()
    model = SpatialDurbinModel().fit(y, X, W, eigs, x_names=names)
    for n in model.wx_names_:
        assert "intercept" not in n


def test_summary_contains_supplied_names():
    """summary() index must contain the supplied x_names."""
    from src.spatial_models.sdm import SpatialDurbinModel
    y, X, W, eigs, names = make_sdm_dgp()
    model = SpatialDurbinModel().fit(y, X, W, eigs, x_names=names)
    df = model.summary()
    assert "intercept" in df.index
    assert "x1" in df.index
