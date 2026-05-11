"""Tests for GlobalMoransI."""
import numpy as np
import pytest
import scipy.sparse as sp

np.random.seed(42)


def make_clustered_data():
    """Load Columbus example from libpysal."""
    import libpysal
    ds = libpysal.examples.load_example("Columbus")
    import geopandas as gpd
    gdf = gpd.read_file(ds.get_path("columbus.shp"))
    import libpysal.weights as lps
    w = lps.Queen.from_dataframe(gdf)
    w.transform = "r"
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    W_sparse = SpatialWeightsFactory().to_sparse(w)
    y = gdf["HOVAL"].values
    return y, W_sparse


def test_positive_moran_clustered():
    from src.esda.morans import GlobalMoransI
    y, W = make_clustered_data()
    model = GlobalMoransI().fit(y, W, n_permutations=499)
    assert model.I_ > 0
    assert model.p_value_permutation_ < 0.05


def test_random_moran_near_expected():
    from src.esda.morans import GlobalMoransI
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    import geopandas as gpd
    from shapely.geometry import Point
    rng = np.random.default_rng(42)
    n = 30
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(n)],
        crs="EPSG:4326",
    )
    factory = SpatialWeightsFactory()
    w = factory.build_knn(gdf, k=4)
    W_sparse = factory.to_sparse(w)
    y_rand = rng.normal(size=n)
    model = GlobalMoransI().fit(y_rand, W_sparse, n_permutations=499)
    E_I = -1.0 / (n - 1)
    assert abs(model.I_ - E_I) < 0.4


def test_summary_keys():
    from src.esda.morans import GlobalMoransI
    y, W = make_clustered_data()
    model = GlobalMoransI().fit(y, W, n_permutations=99)
    s = model.summary()
    for key in ("I", "E_I", "Var_I", "z_score", "p_value_analytical", "p_value_permutation"):
        assert key in s
