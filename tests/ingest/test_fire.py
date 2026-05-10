"""Tests for src/ingest/fire.py."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


MOCK_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-156.70, 20.88],
                        [-156.68, 20.88],
                        [-156.68, 20.86],
                        [-156.70, 20.86],
                        [-156.70, 20.88],
                    ]
                ],
            },
            "properties": {"poly_IncidentName": "LAHAINA", "GISAcres": 2170.0},
        }
    ],
}


@pytest.fixture()
def mock_nifc_response():
    """Mock successful NIFC ArcGIS endpoint response."""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = MOCK_GEOJSON
    return mock


def test_load_fire_perimeter_crs(mock_nifc_response, tmp_path, monkeypatch):
    """Fire perimeter GeoDataFrame should have EPSG:4326 CRS."""
    import src.ingest.fire as fire_module

    monkeypatch.setattr(fire_module, "CACHE_PATH", tmp_path / "lahaina_perimeter.geojson")

    with patch("src.ingest.fire.requests.get", return_value=mock_nifc_response):
        gdf = fire_module.load_fire_perimeter()

    assert gdf.crs is not None
    assert gdf.crs.to_epsg() == 4326


def test_load_fire_perimeter_geometry_not_null(mock_nifc_response, tmp_path, monkeypatch):
    """Fire perimeter geometry column should not contain nulls."""
    import src.ingest.fire as fire_module

    monkeypatch.setattr(fire_module, "CACHE_PATH", tmp_path / "lahaina_perimeter.geojson")

    with patch("src.ingest.fire.requests.get", return_value=mock_nifc_response):
        gdf = fire_module.load_fire_perimeter()

    assert not gdf.geometry.isnull().any()


def test_load_fire_perimeter_uses_cache(mock_nifc_response, tmp_path, monkeypatch):
    """Second call reads from cache without making HTTP request."""
    import src.ingest.fire as fire_module

    monkeypatch.setattr(fire_module, "CACHE_PATH", tmp_path / "lahaina_perimeter.geojson")

    with patch("src.ingest.fire.requests.get", return_value=mock_nifc_response) as mock_get:
        fire_module.load_fire_perimeter()
        fire_module.load_fire_perimeter()

    assert mock_get.call_count == 1


def test_load_fire_perimeter_invalid_source(tmp_path, monkeypatch):
    """ValueError raised for unsupported source."""
    import src.ingest.fire as fire_module

    monkeypatch.setattr(fire_module, "CACHE_PATH", tmp_path / "x.geojson")
    with pytest.raises(ValueError, match="Unsupported source"):
        fire_module.load_fire_perimeter(source="unknown")
