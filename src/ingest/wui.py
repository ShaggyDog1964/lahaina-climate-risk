"""USFS Wildland-Urban Interface (WUI) shapefile loader."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

DEFAULT_PATH = "data/raw/wui/wui_conus.shp"
# DATA SOURCE: https://www.fs.usda.gov/rds/archive/catalog/RDS-2015-0047-3
# User must obtain and place at data/raw/wui/wui_conus.shp


def load_wui(path: str = DEFAULT_PATH) -> gpd.GeoDataFrame:
    """Load USFS WUI shapefile and filter to Hawaii parcels.

    Args:
        path: Path to the USFS WUI shapefile.

    Returns:
        GeoDataFrame with columns [parcel_id, wui_class, geometry] where
        wui_class is one of "Intermix", "Interface", or "None".

    Raises:
        FileNotFoundError: If path does not exist.
        KeyError: If expected columns are missing from the shapefile.
    """
    fpath = Path(path)
    if not fpath.exists():
        raise FileNotFoundError(
            f"WUI shapefile not found: {path}\n"
            "# DATA SOURCE: https://www.fs.usda.gov/rds/archive/catalog/RDS-2015-0047-3"
            " — user must obtain and place at data/raw/wui/wui_conus.shp"
        )

    gdf = gpd.read_file(path)

    if "STATE_NAME" not in gdf.columns:
        raise KeyError("Expected column 'STATE_NAME' not found in WUI shapefile.")

    hawaii = gdf[gdf["STATE_NAME"] == "Hawaii"].copy()

    # Map WUI class codes to human-readable labels
    # WUICLASS10 field: 1=Intermix, 2=Interface, others=None
    wui_class_col = None
    for candidate in ["WUICLASS10", "WUICLASS", "wui_class", "WUI_CLASS"]:
        if candidate in hawaii.columns:
            wui_class_col = candidate
            break

    if wui_class_col is not None:
        class_map = {
            1: "Intermix",
            2: "Interface",
            "Intermix": "Intermix",
            "Interface": "Interface",
        }
        hawaii["wui_class"] = hawaii[wui_class_col].map(class_map).fillna("None")
    else:
        hawaii["wui_class"] = "None"

    # Generate parcel_id from index if not present
    if "parcel_id" not in hawaii.columns:
        hawaii = hawaii.reset_index(drop=True)
        hawaii["parcel_id"] = hawaii.index.astype(str)

    return hawaii[["parcel_id", "wui_class", "geometry"]].reset_index(drop=True)
