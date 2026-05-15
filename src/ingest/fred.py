"""FRED API ingestion for Hawaii climate-risk macroeconomic controls."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
DEFAULT_SERIES = [
    "MEHOINUSHIA672N",
    "HISTHPI",
    "CSUSHPINSA",
    "UNRATE",
    "FEDFUNDS",
    "MORTGAGE30US",
]
CACHE_DIR = Path("data/raw/fred")


def fetch_series(
    series_ids: list[str],
    start: str,
    end: str,
    cache_dir: Path = CACHE_DIR,
) -> pd.DataFrame:
    """Fetch FRED time series and return a tidy long DataFrame.

    Args:
        series_ids: List of FRED series identifiers.
        start: Observation start date, ISO format (YYYY-MM-DD).
        end: Observation end date, ISO format (YYYY-MM-DD).
        cache_dir: Directory for caching raw JSON responses.

    Returns:
        DataFrame with columns [date, series_id, value] sorted by (series_id, date).

    Raises:
        EnvironmentError: If FRED_API_KEY is not set.
        requests.HTTPError: On non-2xx API responses.
    """
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise OSError("FRED_API_KEY environment variable not set.")

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []

    for sid in series_ids:
        cache_file = cache_dir / f"{sid}.json"
        if cache_file.exists():
            raw = json.loads(cache_file.read_text())
        else:
            resp = requests.get(
                FRED_BASE,
                params={
                    "series_id": sid,
                    "observation_start": start,
                    "observation_end": end,
                    "api_key": api_key,
                    "file_type": "json",
                },
                timeout=30,
            )
            if resp.status_code != 200:
                raise ValueError(
                    f"HTTP {resp.status_code} from {resp.url}: {resp.text[:400]}"
                )
            resp.raise_for_status()
            raw = resp.json()
            cache_file.write_text(json.dumps(raw))

        obs = raw.get("observations", [])
        df = pd.DataFrame(obs)[["date", "value"]].copy()
        df["series_id"] = sid
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        frames.append(df)

    result = pd.concat(frames, ignore_index=True).sort_values(["series_id", "date"])
    result = result[["date", "series_id", "value"]].reset_index(drop=True)
    return result


FHFA_ZIP_URL = "https://www.fhfa.gov/document/d/hpi/hpi_at_bdl_zip5.xlsx"
FHFA_CACHE = Path("data/raw/fhfa/hpi_zip.parquet")

# Hawaii ZIP prefixes
_HI_PREFIXES = ("967", "968")

_QTR_TO_MONTH = {"1": "01", "2": "04", "3": "07", "4": "10"}


def fetch_fhfa_zip_hpi(
    output_dir: str = "data/raw/fhfa/",
    force_download: bool = False,
    url: str = FHFA_ZIP_URL,
) -> pd.DataFrame:
    """Fetch FHFA House Price Index at ZIP code level.

    DATA SOURCE: Federal Housing Finance Agency All-Transactions HPI by ZIP
    URL: https://www.fhfa.gov/document/d/hpi/hpi_at_bdl_zip5.xlsx

    Args:
        output_dir: Directory for cached parquet.
        force_download: Re-download even if cache exists.
        url: Override FHFA download URL.

    Returns:
        DataFrame with columns: ZIP5, yr, qtr, index_nsa, year_month.
        Filtered to Hawaii ZIP codes (prefix 967 or 968).
    """
    cache = Path(output_dir) / "hpi_zip.parquet"
    if cache.exists() and not force_download:
        return pd.read_parquet(cache)

    try:
        df = pd.read_excel(url, sheet_name=0, skiprows=6, dtype=str)
    except Exception as exc:
        raise NotImplementedError(
            f"FHFA ZIP HPI download failed: {exc}. "
            f"Download from {url} and place at {cache}"
        ) from exc

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("%", "pct") for c in df.columns]

    # Current file columns (annual format, skiprows=6):
    # "five-digit_zip_code", "year", "annual_change_pct", "hpi",
    # "hpi_with_1990_base", "hpi_with_2000_base"
    zip_col = next((c for c in df.columns if "zip" in c), None)
    yr_col = next((c for c in df.columns if c == "year" or c.startswith("yr")), None)
    # Prefer the plain "hpi" column (base=100 when first recorded)
    idx_col = next((c for c in df.columns if c == "hpi"), None) or \
              next((c for c in df.columns if "hpi" in c), None)

    if not all([zip_col, yr_col, idx_col]):
        raise ValueError(
            f"Could not identify required columns in FHFA data. Found: {list(df.columns)}"
        )

    df = df.rename(columns={zip_col: "ZIP5", yr_col: "yr", idx_col: "index_nsa"})
    df["ZIP5"] = df["ZIP5"].astype(str).str.strip().str.zfill(5)
    df["yr"] = pd.to_numeric(df["yr"], errors="coerce")
    df["index_nsa"] = pd.to_numeric(df["index_nsa"], errors="coerce")
    df = df.dropna(subset=["ZIP5", "yr", "index_nsa"])

    # Filter to Hawaii
    hi_mask = df["ZIP5"].str.startswith(_HI_PREFIXES)
    df = df[hi_mask].copy()

    if df.empty:
        raise ValueError("No Hawaii ZIP codes found in FHFA data.")

    # Annual data — assign to Q1 of each year for year_month compatibility
    df["qtr"] = "1"
    df["year_month"] = df["yr"].astype(int).astype(str) + "-01"

    cache.parent.mkdir(parents=True, exist_ok=True)
    df[["ZIP5", "yr", "qtr", "index_nsa", "year_month"]].to_parquet(cache, engine="pyarrow")
    return df
