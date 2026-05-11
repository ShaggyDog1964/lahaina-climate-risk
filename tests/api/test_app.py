"""Tests for FastAPI spatial results service."""
import json
import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.api.app import app
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_lisa_counts_empty(client):
    with patch("src.api.app._get_db", return_value=None):
        with patch("src.api.app._read_parquet_fallback", return_value=None):
            resp = client.get("/lisa/counts")
    assert resp.status_code == 200
    data = resp.json()
    assert "HH" in data
    assert "total" in data


def test_lisa_clusters_empty(client):
    with patch("src.api.app._get_db", return_value=None):
        with patch("src.api.app._read_parquet_fallback", return_value=None):
            resp = client.get("/lisa/clusters")
    assert resp.status_code == 200
    assert resp.json() == []


def test_gwr_surface_empty(client):
    with patch("src.api.app._get_db", return_value=None):
        with patch("src.api.app._read_parquet_fallback", return_value=None):
            resp = client.get("/gwr/surface")
    assert resp.status_code == 200
    assert resp.json() == []


def test_model_comparison_empty(client):
    with patch("src.api.app._get_db", return_value=None), \
         patch("pathlib.Path.exists", return_value=False):
        resp = client.get("/models/comparison")
    assert resp.status_code == 200


def test_autocorrelation_no_file(client):
    with patch("pathlib.Path.exists", return_value=False):
        resp = client.get("/spatial/autocorrelation")
    assert resp.status_code == 200
