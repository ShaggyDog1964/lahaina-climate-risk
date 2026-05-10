"""Maui County assessor parcel loader with pandera schema validation."""

from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pandera as pa

DEFAULT_PATH = "data/raw/parcels/maui_assessor.csv"

PARCEL_SCHEMA = pa.DataFrameSchema(
    {
        "parcel_id": pa.Column(str),
        "sale_price": pa.Column(float, checks=pa.Check.gt(0)),
        "sale_date": pa.Column(pa.dtypes.DateTime),
        "lat": pa.Column(float, checks=[pa.Check.ge(-90), pa.Check.le(90)]),
        "lon": pa.Column(float, checks=[pa.Check.ge(-180), pa.Check.le(180)]),
        "land_area_sqft": pa.Column(float, checks=pa.Check.ge(0)),
        "structure_sqft": pa.Column(float, checks=pa.Check.ge(0)),
        "year_built": pa.Column(int),
        "zoning": pa.Column(str),
        "tract_geoid": pa.Column(str),
    }
)


def load_maui_parcels(path: str = DEFAULT_PATH) -> gpd.GeoDataFrame:
    """Load and validate Maui County assessor parcel data.

    Args:
        path: Path to the assessor CSV or shapefile.

    Returns:
        GeoDataFrame with point geometry, validated schema, and log_price column.

    Raises:
        pandera.errors.SchemaError: If the data fails schema validation.
        FileNotFoundError: If path does not exist.
    """
    fpath = Path(path)
    if not fpath.exists():
        raise FileNotFoundError(f"Parcel file not found: {path}")

    if fpath.suffix.lower() == ".csv":
        df = pd.read_csv(path, parse_dates=["sale_date"])
    else:
        raw = gpd.read_file(path)
        df = pd.DataFrame(raw.drop(columns="geometry", errors="ignore"))

    # Coerce types
    df["parcel_id"] = df["parcel_id"].astype(str)
    df["sale_price"] = pd.to_numeric(df["sale_price"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["land_area_sqft"] = pd.to_numeric(df["land_area_sqft"], errors="coerce")
    df["structure_sqft"] = pd.to_numeric(df["structure_sqft"], errors="coerce")
    df["year_built"] = pd.to_numeric(df["year_built"], errors="coerce").astype("Int64").astype(int)
    df["zoning"] = df["zoning"].astype(str)
    df["tract_geoid"] = df["tract_geoid"].astype(str)
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    # Schema validation
    PARCEL_SCHEMA.validate(df)

    # Derived column
    df["log_price"] = df["sale_price"].apply(math.log)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )
    return gdf
