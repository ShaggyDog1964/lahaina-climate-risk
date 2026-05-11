"""Tests for SpatialWeightsFactory."""
import numpy as np
import pytest
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import scipy.sparse as sp

np.random.seed(42)


def make_points_gdf(n: int = 20) -> gpd.GeoDataFrame:
    rng = np.random.default_rng(42)
    lons = -156.7 + rng.uniform(0, 0.1, n)
    lats = 20.8 + rng.uniform(0, 0.1, n)
    geom = [Point(lo, la) for lo, la in zip(lons, lats)]
    return gpd.GeoDataFrame({"id": range(n)}, geometry=geom, crs="EPSG:4326")


@pytest.fixture
def gdf():
    return make_points_gdf(20)


def test_knn_n_and_neighbors(gdf):
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    factory = SpatialWeightsFactory()
    k = 4
    w = factory.build_knn(gdf, k=k)
    assert w.n == 20
    assert abs(w.mean_neighbors - k) < 0.5


def test_knn_row_standardized(gdf):
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=4)
    for i in w.neighbors:
        if w.weights[i]:
            assert abs(sum(w.weights[i]) - 1.0) < 1e-10


def test_idw_row_standardized(gdf):
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    factory = SpatialWeightsFactory()
    w = factory.build_idw(gdf, bandwidth_km=50.0)
    for i in w.neighbors:
        if w.weights[i]:
            assert abs(sum(w.weights[i]) - 1.0) < 1e-10


def test_queen_fallback_for_points(gdf):
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    import warnings
    factory = SpatialWeightsFactory()
    with warnings.catch_warnings(record=True) as w_list:
        warnings.simplefilter("always")
        w = factory.build_queen(gdf)
    assert w.n == 20
    assert any("fallback" in str(warning.message).lower() or "knn" in str(warning.message).lower()
               for warning in w_list)


def test_to_sparse_shape(gdf):
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=4)
    W_sparse = factory.to_sparse(w)
    assert isinstance(W_sparse, sp.csr_matrix)
    assert W_sparse.shape == (20, 20)


def test_eigenvalues_length(gdf):
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=4)
    W_sparse = factory.to_sparse(w)
    eigs = factory.eigenvalues(W_sparse)
    assert len(eigs) >= 18  # at least n-2


def test_build_all_returns_three(gdf):
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    factory = SpatialWeightsFactory()
    weights = factory.build_all(gdf, k=4, bandwidth_km=50.0)
    assert set(weights.keys()) == {"knn", "idw", "queen"}
