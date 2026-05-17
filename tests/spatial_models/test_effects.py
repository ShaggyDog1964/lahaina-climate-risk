"""Tests for LeSagePaceEffects."""
import numpy as np
import pytest
import scipy.sparse as sp
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


def make_sdm_model(n: int = 60):
    rng = np.random.default_rng(42)
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
    A = I_n - 0.3 * W_sparse
    WX1 = np.asarray(W_sparse @ X[:, 1]).ravel()
    y = sp.linalg.spsolve(A, X @ np.array([1.0, 1.0]) + WX1 * 0.5 + rng.normal(scale=0.1, size=n))
    from src.spatial_models.sdm import SpatialDurbinModel
    model = SpatialDurbinModel().fit(y, X, W_sparse, eigs, x_names=["intercept", "x1"])
    return model, W_sparse


def test_effects_indirect_nonzero():
    from src.spatial_models.effects import LeSagePaceEffects
    model, W = make_sdm_model()
    effects = LeSagePaceEffects().compute(model, W, n_simulations=200)
    df = effects.summary_table()
    assert len(df) >= 1
    assert df["indirect"].iloc[0] != 0.0


def test_direct_plus_indirect_eq_total():
    from src.spatial_models.effects import LeSagePaceEffects
    model, W = make_sdm_model()
    effects = LeSagePaceEffects().compute(model, W, n_simulations=100)
    df = effects.effects_df_
    for _, row in df.iterrows():
        assert abs(row["direct"] + row["indirect"] - row["total"]) < 1e-8


def test_se_positive():
    from src.spatial_models.effects import LeSagePaceEffects
    model, W = make_sdm_model()
    effects = LeSagePaceEffects().compute(model, W, n_simulations=200)
    df = effects.effects_df_
    assert (df["direct_se"] > 0).all()
    assert (df["indirect_se"] > 0).all()
    assert (df["total_se"] > 0).all()


def test_effects_df_uses_x_names_from_sdm():
    """effects_df_ variable column must use sdm._x_names (excluding intercept)."""
    from src.spatial_models.effects import LeSagePaceEffects
    model, W = make_sdm_model()
    effects = LeSagePaceEffects().compute(model, W, n_simulations=50)
    assert "x1" in effects.effects_df_["variable"].tolist()
    assert "intercept" not in effects.effects_df_["variable"].tolist()
