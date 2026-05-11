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

ASSESSMENT_ROLL_SCHEMA = pa.DataFrameSchema(
    {
        "parcel_id": pa.Column(str),
        "sale_price": pa.Column(float, checks=pa.Check.gt(0), nullable=True),
        "sale_date": pa.Column(pa.dtypes.DateTime, nullable=True),
        "lat": pa.Column(float, checks=[pa.Check.ge(-90), pa.Check.le(90)], nullable=True),
        "lon": pa.Column(float, checks=[pa.Check.ge(-180), pa.Check.le(180)], nullable=True),
        "land_area_sqft": pa.Column(float, checks=pa.Check.ge(0), nullable=True),
        "structure_sqft": pa.Column(float, checks=pa.Check.ge(0), nullable=True),
        "year_built": pa.Column(float, nullable=True),
        "zoning": pa.Column(str, nullable=True),
        "tax_class": pa.Column(str, nullable=True),
        "assessed_total": pa.Column(float, checks=pa.Check.ge(0), nullable=True),
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


def fetch_maui_assessment_roll(output_dir: str = "data/raw/parcels/") -> gpd.GeoDataFrame:
    """Load Maui County Assessment Roll from local file or raise stub error.

    DATA SOURCE: Maui County Assessment Division Real Property Assessment Roll
    URL: https://www.mauicounty.gov/452/Real-Property-Assessment
    Download the CSV and place at data/raw/parcels/maui_assessment_roll.csv

    Returns GeoDataFrame with columns: parcel_id, sale_price, sale_date, lat, lon,
    land_area_sqft, structure_sqft, year_built, zoning, tax_class, assessed_total,
    log_price, geometry

    Args:
        output_dir: Directory containing the maui_assessment_roll.csv file.

    Returns:
        GeoDataFrame with point geometry, validated schema, and log_price column.

    Raises:
        NotImplementedError: If the CSV file is not present at the expected path.
        pandera.errors.SchemaError: If the data fails schema validation.
    """
    path = Path(output_dir) / "maui_assessment_roll.csv"
    if not path.exists():
        raise NotImplementedError(
            "Maui Assessment Roll not found. "
            "Download from https://www.mauicounty.gov/452/Real-Property-Assessment "
            f"and place at {path}"
        )

    df = pd.read_csv(path)

    # Normalize column names: strip whitespace, lowercase
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Coerce types
    df["parcel_id"] = df["parcel_id"].astype(str)

    if "sale_price" in df.columns:
        df["sale_price"] = pd.to_numeric(
            df["sale_price"].astype(str).str.replace(r"[$,]", "", regex=True),
            errors="coerce",
        )

    if "sale_date" in df.columns:
        df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")

    for col in ("lat", "lon", "land_area_sqft", "structure_sqft", "assessed_total"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "year_built" in df.columns:
        df["year_built"] = pd.to_numeric(df["year_built"], errors="coerce")

    for col in ("zoning", "tax_class"):
        if col in df.columns:
            df[col] = df[col].astype(str)
        else:
            df[col] = pd.NA

    # Ensure required columns exist with defaults where missing
    for col in ("sale_price", "sale_date", "lat", "lon",
                "land_area_sqft", "structure_sqft", "year_built", "assessed_total"):
        if col not in df.columns:
            df[col] = pd.NA

    # Schema validation
    ASSESSMENT_ROLL_SCHEMA.validate(df)

    # Derived column (only for rows with a positive sale_price)
    df["log_price"] = df["sale_price"].apply(
        lambda x: math.log(x) if pd.notna(x) and x > 0 else float("nan")
    )

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["lon"].fillna(0), df["lat"].fillna(0)
        ),
        crs="EPSG:4326",
    )
    return gdf
