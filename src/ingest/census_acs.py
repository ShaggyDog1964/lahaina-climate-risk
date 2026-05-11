"""Census ACS 5-year API ingestion for zip-level covariates."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

ACS_URL = "https://api.census.gov/data/{year}/acs/acs5"

VARIABLE_MAP = {
    "B19013_001E": "median_hh_income",
    "B25077_001E": "median_home_value",
    "B01003_001E": "total_population",
    "B25003_002E": "owner_occupied_units",
    "B25003_003E": "renter_occupied_units",
    "B08301_001E": "total_workers",
}


def fetch_acs_zip(
    variables: list[str] | None = None,
    state_fips: str = "15",
    year: int = 2022,
    cache_dir: Path | None = None,
) -> pd.DataFrame:
    """Fetch ACS 5-year estimates for zip code tabulation areas.

    Args:
        variables: ACS variable codes; defaults to VARIABLE_MAP keys.
        state_fips: State FIPS code (15 = Hawaii).
        year: ACS release year.
        cache_dir: Cache directory; defaults to data/raw/census/.

    Returns:
        DataFrame with columns [zip_code, median_hh_income, median_home_value,
        total_population, owner_occupied_units, renter_occupied_units, total_workers].
    """
    if variables is None:
        variables = list(VARIABLE_MAP.keys())

    cache_dir = Path(cache_dir) if cache_dir else Path("data/raw/census")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"acs_zip_{year}.parquet"

    if cache_path.exists():
        return pd.read_parquet(cache_path)

    api_key = os.environ.get("CENSUS_API_KEY", "")
    var_str = ",".join(["NAME"] + variables)
    url = ACS_URL.format(year=year)
    params = {
        "get": var_str,
        "for": "zip code tabulation area:*",
        "in": f"state:{state_fips}",
    }
    if api_key:
        params["key"] = api_key

    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)

    df = df.rename(columns=VARIABLE_MAP)
    df["zip_code"] = df["zip code tabulation area"].astype(str).str.zfill(5)
    df = df.drop(columns=["NAME", "state", "zip code tabulation area"], errors="ignore")

    numeric_cols = list(VARIABLE_MAP.values())
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["zip_code"])
    df.to_parquet(cache_path, engine="pyarrow")
    return df
