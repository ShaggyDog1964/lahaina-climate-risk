"""Census ACS 5-year API ingestion for zip-level covariates."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

ACS_URL = "https://api.census.gov/data/{year}/acs/acs5"

# Hawaii ZIP code prefixes: 967xx and 968xx
_HI_ZIP_PREFIXES = ("967", "968")

# Maximum retries and base backoff in seconds for Census API requests
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0

VARIABLE_MAP = {
    "B19013_001E": "median_hh_income",
    "B25077_001E": "median_home_value",
    "B01003_001E": "total_population",
    "B25003_002E": "owner_occupied_units",
    "B25003_003E": "renter_occupied_units",
    "B08301_001E": "total_workers",
}


def _fetch_with_retry(url: str, params: dict, timeout: int = 60) -> requests.Response:
    """GET url with exponential backoff retry on transient errors.

    Args:
        url: Request URL.
        params: Query parameters dict.
        timeout: Per-attempt timeout in seconds.

    Returns:
        Successful Response object.

    Raises:
        ValueError: If the Census API returns a non-200 status after all retries.
        requests.RequestException: On network-level failure after all retries.
    """
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code != 200:
                raise ValueError(
                    f"Census API returned HTTP {resp.status_code} on attempt {attempt}."
                    f"\nURL: {resp.url}"
                    f"\nResponse: {resp.text[:500]}"
                )
            return resp
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                wait = _BACKOFF_BASE * (2 ** (attempt - 1))
                log.warning(
                    "Census API request failed (attempt %d/%d): %s. Retrying in %.1fs.",
                    attempt,
                    _MAX_RETRIES,
                    exc,
                    wait,
                )
                time.sleep(wait)
    raise last_exc  # type: ignore[misc]


def fetch_acs_zip(
    variables: list[str] | None = None,
    state_fips: str = "15",
    year: int = 2022,
    cache_dir: Path | None = None,
) -> pd.DataFrame:
    """Fetch ACS 5-year estimates for zip code tabulation areas.

    Fetches ALL ZCTAs nationally (the Census API does not support the `in=state`
    filter for ZCTAs), then filters to Hawaii ZIP codes in Python using the
    ``_HI_ZIP_PREFIXES`` constant (967xx, 968xx).  The ``state_fips`` parameter
    is retained for API compatibility but is not sent to the Census endpoint.

    Args:
        variables: ACS variable codes; defaults to VARIABLE_MAP keys.
        state_fips: Unused by the Census request; kept for call-site compatibility.
        year: ACS release year.
        cache_dir: Cache directory; defaults to data/raw/census/.

    Returns:
        DataFrame with columns [zip_code, median_hh_income, median_home_value,
        total_population, owner_occupied_units, renter_occupied_units, total_workers]
        filtered to Hawaii ZIP codes.
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

    # NOTE: ZCTAs do NOT support `in=state:XX` in the Census ACS5 API.
    # Fetch all ZCTAs nationally and filter to Hawaii in Python.
    params: dict[str, str] = {
        "get": var_str,
        "for": "zip code tabulation area:*",
    }
    if api_key:
        params["key"] = api_key

    log.info("Fetching ACS5 %d ZCTAs from Census API (all states, will filter to HI).", year)
    resp = _fetch_with_retry(url, params, timeout=60)
    data: list[list[str]] = resp.json()

    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)

    df = df.rename(columns=VARIABLE_MAP)
    df["zip_code"] = df["zip code tabulation area"].astype(str).str.zfill(5)
    df = df.drop(columns=["NAME", "state", "zip code tabulation area"], errors="ignore")

    # Filter to Hawaii ZIP codes (967xx, 968xx)
    df = df[df["zip_code"].str.startswith(_HI_ZIP_PREFIXES)].copy()

    numeric_cols = list(VARIABLE_MAP.values())
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["zip_code"])

    log.info("ACS5 %d: retained %d Hawaii ZCTAs after national fetch.", year, len(df))
    df.to_parquet(cache_path, engine="pyarrow")
    return df
