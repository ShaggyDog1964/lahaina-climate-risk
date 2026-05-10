"""Distance band assignment relative to the Lahaina fire perimeter."""

from __future__ import annotations

from typing import Literal

import geopandas as gpd
from shapely.geometry.base import BaseGeometry

BandLabel = Literal["0-2km", "2-5km", "5-10km", "10-25km", "control"]

BAND_THRESHOLDS: list[tuple[float, str]] = [
    (2.0, "0-2km"),
    (5.0, "2-5km"),
    (10.0, "5-10km"),
    (25.0, "10-25km"),
]


def _classify_distance(dist_km: float) -> str:
    """Classify a distance (km) into a treatment band label.

    Args:
        dist_km: Distance from fire perimeter in kilometers.

    Returns:
        Treatment band label string.
    """
    for threshold, label in BAND_THRESHOLDS:
        if dist_km <= threshold:
            return label
    return "control"


def assign_distance_bands(
    gdf: gpd.GeoDataFrame,
    fire_geom: BaseGeometry,
) -> gpd.GeoDataFrame:
    """Assign distance-to-fire and treatment band to each parcel.

    Args:
        gdf: GeoDataFrame with point geometry in any CRS.
        fire_geom: Shapely geometry of the fire perimeter, already projected
            to EPSG:32604 (UTM zone 4N, Hawaii).

    Returns:
        GeoDataFrame with added columns [dist_to_fire_km, treatment_band],
        reprojected back to original CRS.
    """
    orig_crs = gdf.crs
    utm_crs = "EPSG:32604"

    projected = gdf.to_crs(utm_crs).copy()
    projected["dist_to_fire_km"] = projected.geometry.distance(fire_geom) / 1000.0
    projected["treatment_band"] = projected["dist_to_fire_km"].apply(_classify_distance)

    # Reproject back to original CRS
    result = projected.to_crs(orig_crs)
    # Ensure derived columns survive reprojection
    result = result.copy()
    result["dist_to_fire_km"] = projected["dist_to_fire_km"].values
    result["treatment_band"] = projected["treatment_band"].values

    return result
