"""Tests for LocalMoransI."""
import numpy as np
import pytest
import geopandas as gpd
from shapely.geometry import Point
import scipy.sparse as sp

np.random.seed(42)


def make_clustered_gdf_and_W(n_cluster: int = 10, n_total: int = 30):
    """Synthetic spatial dataset with a known HH cluster in the SW corner."""
    rng = np.random.default_rng(42)
    # Cluster points in SW: x in [0, 0.2], y in [0, 0.2]
    cluster_x = rng.uniform(0, 0.2, n_cluster)
    cluster_y = rng.uniform(0, 0.2, n_cluster)
    noise_x = rng.uniform(0.3, 1.0, n_total - n_cluster)
    noise_y = rng.uniform(0.3, 1.0, n_total - n_cluster)
    x = np.concatenate([cluster_x, noise_x])
    y_coords = np.concatenate([cluster_y, noise_y])
    gdf = gpd.GeoDataFrame(
        {"id": range(n_total)},
        geometry=[Point(xi, yi) for xi, yi in zip(x, y_coords)],
        crs="EPSG:4326",
    )
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=4)
    W_sparse = factory.to_sparse(w)
    # y: high values in cluster, low elsewhere
    y_values = np.concatenate([rng.uniform(2, 3, n_cluster), rng.uniform(-1, 0, n_total - n_cluster)])
    return gdf, W_sparse, y_values


def test_hh_labels_in_cluster():
    from src.esda.lisa import LocalMoransI
    gdf, W, y = make_clustered_gdf_and_W()
    model = LocalMoransI().fit(y, W, n_permutations=499)
    assert np.sum(model.cluster_labels_[:10] == "HH") >= 2


def test_labels_length():
    from src.esda.lisa import LocalMoransI
    gdf, W, y = make_clustered_gdf_and_W(n_total=30)
    model = LocalMoransI().fit(y, W, n_permutations=99)
    assert len(model.cluster_labels_) == 30


def test_cluster_counts_sum():
    from src.esda.lisa import LocalMoransI
    gdf, W, y = make_clustered_gdf_and_W(n_total=30)
    model = LocalMoransI().fit(y, W, n_permutations=99)
    counts = model.cluster_counts()
    total = sum(v for k, v in counts.items() if k in ("HH", "LL", "HL", "LH", "NS"))
    assert total == 30


def test_random_data_mostly_ns():
    from src.esda.lisa import LocalMoransI
    gdf, W, y_clustered = make_clustered_gdf_and_W(n_total=30)
    rng = np.random.default_rng(99)
    y_rand = rng.normal(size=30)
    model = LocalMoransI().fit(y_rand, W, n_permutations=499)
    ns_frac = np.mean(model.cluster_labels_ == "NS")
    assert ns_frac > 0.70


def test_to_geodataframe():
    from src.esda.lisa import LocalMoransI
    gdf, W, y = make_clustered_gdf_and_W(n_total=20)
    model = LocalMoransI().fit(y, W, n_permutations=99)
    result = model.to_geodataframe(gdf)
    assert "I_local" in result.columns
    assert "cluster_label" in result.columns
    assert len(result) == 20
