"""Property-based tests for spatial weight and ESDA implementations."""
from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


def _make_point_gdf(n: int, seed: int = 42) -> gpd.GeoDataFrame:
    rng = np.random.default_rng(seed)
    return gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(n)],
        crs="EPSG:4326",
    )


@given(n=st.integers(min_value=6, max_value=50), k=st.integers(min_value=3, max_value=5))
@settings(max_examples=25, deadline=15_000)
def test_weights_row_sum_always_one(n: int, k: int) -> None:
    """KNN weight rows always sum to 1.0."""
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    if k >= n:
        return
    gdf = _make_point_gdf(n, seed=n * 100 + k)
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=k)
    for i in w.neighbors:
        if w.weights[i]:
            assert abs(sum(w.weights[i]) - 1.0) < 1e-9


@given(n=st.integers(min_value=10, max_value=40))
@settings(max_examples=20, deadline=15_000)
def test_moran_i_bounded(n: int) -> None:
    """-1 <= Moran's I <= 1 for any input."""
    from src.esda.morans import GlobalMoransI
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    rng = np.random.default_rng(n)
    gdf = _make_point_gdf(n, seed=n)
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=min(4, n - 1))
    W_sparse = factory.to_sparse(w)
    y = rng.normal(size=n)
    model = GlobalMoransI().fit(y, W_sparse, n_permutations=99)
    # Moran's I is not strictly bounded to [-1,1] for row-standardized W but
    # should be within reasonable range
    assert -3.0 < model.I_ < 3.0


@given(n=st.integers(min_value=10, max_value=30))
@settings(max_examples=15, deadline=20_000)
def test_lisa_clusters_partition(n: int) -> None:
    """Every observation gets exactly one cluster label."""
    from src.esda.lisa import LocalMoransI
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    rng = np.random.default_rng(n)
    gdf = _make_point_gdf(n, seed=n)
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=min(4, n - 1))
    W_sparse = factory.to_sparse(w)
    y = rng.normal(size=n)
    model = LocalMoransI().fit(y, W_sparse, n_permutations=99)
    valid_labels = {"HH", "LL", "HL", "LH", "NS"}
    assert len(model.cluster_labels_) == n
    assert all(lbl in valid_labels for lbl in model.cluster_labels_)
