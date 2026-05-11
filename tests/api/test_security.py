"""Security and input-validation tests for the FastAPI spatial results service."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_lisa_clusters_valid_label_hh_returns_200(client):
    with patch("src.api.app._get_db", return_value=None), \
         patch("src.api.app._read_parquet_fallback", return_value=None):
        resp = client.get("/lisa/clusters?cluster_label=HH")
    assert resp.status_code == 200


def test_lisa_clusters_invalid_label_returns_422(client):
    resp = client.get("/lisa/clusters?cluster_label=INVALID")
    assert resp.status_code == 422


def test_lisa_clusters_sql_injection_returns_422(client):
    resp = client.get("/lisa/clusters?cluster_label=' OR 1=1--")
    assert resp.status_code == 422
