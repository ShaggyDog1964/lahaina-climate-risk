"""H3 hexagonal grid assignment for parcel-level spatial indexing."""

from __future__ import annotations

import geopandas as gpd
import h3
import pandas as pd
from shapely.geometry import Polygon


def assign_h3(
    gdf: gpd.GeoDataFrame,
    resolution: int = 8,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Assign H3 cell index to each parcel and produce a cell-level summary.

    Args:
        gdf: GeoDataFrame with point geometry and columns [sale_price, log_price].
        resolution: H3 resolution level (0=coarsest, 15=finest). Default 8.

    Returns:
        Tuple of (parcel_gdf, cell_summary_gdf):
            - parcel_gdf: Original GeoDataFrame with added h3_index column.
            - cell_summary_gdf: Cell-level GeoDataFrame with columns
              [h3_index, median_sale_price, transaction_count, mean_log_price].

    Raises:
        ValueError: If gdf lacks required price columns.
    """
    required = {"sale_price", "log_price"}
    missing = required - set(gdf.columns)
    if missing:
        raise ValueError(f"GeoDataFrame missing required columns: {missing}")

    gdf = gdf.copy()
    if "lat" not in gdf.columns or "lon" not in gdf.columns:
        gdf["lat"] = gdf.geometry.y
        gdf["lon"] = gdf.geometry.x

    gdf["h3_index"] = gdf.apply(
        lambda row: h3.latlng_to_cell(row["lat"], row["lon"], resolution),
        axis=1,
    )

    # Cell-level aggregation
    agg = (
        gdf.groupby("h3_index")
        .agg(
            median_sale_price=("sale_price", "median"),
            transaction_count=("sale_price", "count"),
            mean_log_price=("log_price", "mean"),
        )
        .reset_index()
    )

    def _h3_to_polygon(h3_index: str) -> Polygon:
        """Convert H3 cell index to Shapely Polygon.

        Args:
            h3_index: H3 cell identifier string.

        Returns:
            Shapely Polygon of the cell boundary.
        """
        boundary = h3.cell_to_boundary(h3_index)
        return Polygon([(lng, lat) for lat, lng in boundary])

    agg["geometry"] = agg["h3_index"].apply(_h3_to_polygon)
    cell_gdf = gpd.GeoDataFrame(agg, geometry="geometry", crs="EPSG:4326")

    return gdf, cell_gdf
