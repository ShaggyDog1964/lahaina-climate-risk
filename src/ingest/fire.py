"""NIFC fire perimeter loader for the 2023 Lahaina wildfire."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import requests

NIFC_URL = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "WFIGS_Interagency_Perimeters/FeatureServer/0/query"
)
NIFC_PARAMS = {
    "where": "poly_IncidentName LIKE '%LAHAINA%'",
    "outFields": "*",
    "f": "geojson",
}
CACHE_PATH = Path("data/raw/fire/lahaina_perimeter.geojson")


def load_fire_perimeter(source: str = "nifc") -> gpd.GeoDataFrame:
    """Download or load the 2023 Lahaina fire perimeter.

    Args:
        source: Data source identifier. Currently only "nifc" is supported.

    Returns:
        GeoDataFrame with fire perimeter polygon(s) in EPSG:4326.

    Raises:
        ValueError: If source is not "nifc".
        requests.HTTPError: On failed API requests.
    """
    if source != "nifc":
        raise ValueError(f"Unsupported source: {source!r}. Only 'nifc' is supported.")

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_PATH.exists():
        gdf = gpd.read_file(str(CACHE_PATH))
    else:
        resp = requests.get(NIFC_URL, params=NIFC_PARAMS, timeout=60)
        resp.raise_for_status()
        geojson_data = resp.json()
        CACHE_PATH.write_text(json.dumps(geojson_data))
        gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    if gdf.geometry.isnull().any():
        raise ValueError("Fire perimeter GeoDataFrame contains null geometries.")

    return gdf
