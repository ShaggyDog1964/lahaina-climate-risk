"""Tests for src/spatial/distance_bands.py."""

from __future__ import annotations

import geopandas as gpd
import pyproj
import pytest
from shapely.geometry import Point, Polygon


def _lahaina_utm():
    """Return Lahaina fire center coordinates in UTM 32604."""
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32604", always_xy=True)
    return transformer.transform(-156.685, 20.875)


def _make_fire_geom_utm():
    """Tiny synthetic fire polygon at Lahaina in UTM 32604."""
    cx, cy = _lahaina_utm()
    delta = 50  # 50m square
    return Polygon([
        (cx - delta, cy - delta),
        (cx + delta, cy - delta),
        (cx + delta, cy + delta),
        (cx - delta, cy + delta),
    ])


def _make_parcels_at_distances():
    """5 synthetic points at approximately known distances from Lahaina fire."""
    cx_utm, cy_utm = _lahaina_utm()
    transformer_back = pyproj.Transformer.from_crs("EPSG:32604", "EPSG:4326", always_xy=True)
    offsets_m = [1000, 3000, 7000, 15000, 30000]
    points_wgs84 = []
    for d in offsets_m:
        x, y = transformer_back.transform(cx_utm + d, cy_utm)
        points_wgs84.append(Point(x, y))

    return gpd.GeoDataFrame(
        {"parcel_id": [f"P{i}" for i in range(5)]},
        geometry=points_wgs84,
        crs="EPSG:4326",
    )


def test_assign_distance_bands_labels():
    """Band assignments should match expected labels for known distances."""
    from src.spatial.distance_bands import assign_distance_bands

    fire_geom = _make_fire_geom_utm()
    parcels = _make_parcels_at_distances()
    result = assign_distance_bands(parcels, fire_geom)

    assert "treatment_band" in result.columns
    assert "dist_to_fire_km" in result.columns

    bands = result["treatment_band"].tolist()
    assert bands[0] == "0-2km"
    assert bands[1] == "2-5km"
    assert bands[2] == "5-10km"
    assert bands[3] == "10-25km"
    assert bands[4] == "control"


def test_assign_distance_bands_dist_positive():
    """dist_to_fire_km should be non-negative for all parcels."""
    from src.spatial.distance_bands import assign_distance_bands

    fire_geom = _make_fire_geom_utm()
    parcels = _make_parcels_at_distances()
    result = assign_distance_bands(parcels, fire_geom)
    assert (result["dist_to_fire_km"] >= 0).all()


def test_assign_distance_bands_returns_geodataframe():
    """Result should be a GeoDataFrame."""
    from src.spatial.distance_bands import assign_distance_bands

    fire_geom = _make_fire_geom_utm()
    parcels = _make_parcels_at_distances()
    result = assign_distance_bands(parcels, fire_geom)
    assert isinstance(result, gpd.GeoDataFrame)
