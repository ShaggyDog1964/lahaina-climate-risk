"""Tests for Pydantic schemas."""
import pytest
from src.api.schemas import LISAResult, GWRSurface, SpatialModelSummary, ClusterCountResponse


def test_lisa_result_valid():
    r = LISAResult(parcel_id="1234", lat=20.87, lon=-156.7, I_local=0.45, p_value=0.01, cluster_label="HH")
    assert r.cluster_label == "HH"


def test_gwr_surface_valid():
    s = GWRSurface(parcel_id="X", lat=20.0, lon=-156.0, beta_dist_to_fire=-0.2, beta_wui=0.1, y_hat=-0.05)
    assert s.beta_dist_to_fire == pytest.approx(-0.2)


def test_cluster_count_valid():
    c = ClusterCountResponse(HH=5, LL=3, HL=1, LH=2, NS=89, total=100)
    assert c.total == 100
