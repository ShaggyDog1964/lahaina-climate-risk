"""Tests for BandwidthSelector."""
import numpy as np
import pytest
import pickle
import tempfile
import os
import geopandas as gpd
from shapely.geometry import Point

np.random.seed(42)


def make_gdf_and_data(n: int = 30):
    rng = np.random.default_rng(42)
    lons = -156.7 + rng.uniform(0, 0.1, n)
    lats = 20.8 + rng.uniform(0, 0.1, n)
    gdf = gpd.GeoDataFrame(
        {"id": range(n)},
        geometry=[Point(lo, la) for lo, la in zip(lons, lats)],
        crs="EPSG:4326",
    )
    # Spatially varying coefficient: beta = 1.5 - 0.5 * x_coord
    projected = gdf.to_crs("EPSG:32604")
    x_coords = projected.geometry.x.values
    x_norm = (x_coords - x_coords.mean()) / (x_coords.std() + 1e-6)
    beta_i = 1.5 - 0.5 * x_norm
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    y = X[:, 0] * beta_i + X[:, 1] * 0.3 + rng.normal(scale=0.1, size=n)
    return gdf, y, X


def test_bandwidth_in_range():
    from src.gwr.bandwidth import BandwidthSelector
    gdf, y, X = make_gdf_and_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt = os.path.join(tmpdir, "bw_checkpoint.pkl")
        sel = BandwidthSelector(gdf, y, X, checkpoint_path=ckpt)
        bw = sel.fit(lower_km=0.1, upper_km=30.0)
    assert 0.1 <= bw <= 30.0


def test_golden_section_convergence():
    from src.gwr.bandwidth import BandwidthSelector
    gdf, y, X = make_gdf_and_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt = os.path.join(tmpdir, "bw_checkpoint.pkl")
        sel = BandwidthSelector(gdf, y, X, checkpoint_path=ckpt)
        bw = sel.golden_section_search(0.1, 30.0, tol=0.5)
        n_evals = len(sel._evaluations)
    # Golden section should converge in few evaluations (each iter uses 2 evals)
    assert n_evals <= 100


def test_checkpoint_save_and_resume():
    from src.gwr.bandwidth import BandwidthSelector
    gdf, y, X = make_gdf_and_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt = os.path.join(tmpdir, "bw_checkpoint.pkl")
        sel1 = BandwidthSelector(gdf, y, X, checkpoint_path=ckpt)
        # Run a few steps manually
        sel1._gwr_aicc(5.0)
        sel1._evaluations.append((5.0, sel1._gwr_aicc(5.0)))
        sel1.checkpoint({"lower": 2.0, "upper": 20.0, "evaluations": sel1._evaluations}, ckpt)
        # Resume
        sel2 = BandwidthSelector(gdf, y, X, checkpoint_path=ckpt)
        state = sel2.resume_from_checkpoint(ckpt)
        assert state is not None
        assert state["lower"] == 2.0
        assert state["upper"] == 20.0
