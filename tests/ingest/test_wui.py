"""Tests for src/ingest/wui.py."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point


def _make_wui_fixture(tmp_path: Path) -> str:
    """Create a synthetic WUI shapefile with 3 WUI classes plus one non-Hawaii row."""
    gdf = gpd.GeoDataFrame(
        {
            "STATE_NAME": ["Hawaii", "Hawaii", "Hawaii", "California"],
            "WUICLASS10": [1, 2, 0, 1],
            "parcel_id": ["H001", "H002", "H003", "C001"],
            "geometry": [
                Point(-156.7, 20.88),
                Point(-156.68, 20.86),
                Point(-156.66, 20.84),
                Point(-118.0, 34.0),
            ],
        },
        crs="EPSG:4326",
    )
    path = tmp_path / "wui_conus.shp"
    gdf.to_file(str(path))
    return str(path)


def test_load_wui_filters_hawaii(tmp_path):
    """load_wui returns only Hawaii rows."""
    path = _make_wui_fixture(tmp_path)
    from src.ingest.wui import load_wui

    result = load_wui(path)
    assert len(result) == 3


def test_load_wui_wui_class_values(tmp_path):
    """wui_class column contains only expected labels."""
    path = _make_wui_fixture(tmp_path)
    from src.ingest.wui import load_wui

    result = load_wui(path)
    assert set(result["wui_class"].unique()).issubset({"Intermix", "Interface", "None"})
    assert "Intermix" in result["wui_class"].values
    assert "Interface" in result["wui_class"].values


def test_load_wui_missing_file():
    """FileNotFoundError raised for missing shapefile."""
    from src.ingest.wui import load_wui

    with pytest.raises(FileNotFoundError):
        load_wui("data/raw/wui/does_not_exist.shp")


def test_load_wui_columns(tmp_path):
    """Result contains parcel_id and wui_class columns."""
    path = _make_wui_fixture(tmp_path)
    from src.ingest.wui import load_wui

    result = load_wui(path)
    assert "parcel_id" in result.columns
    assert "wui_class" in result.columns
