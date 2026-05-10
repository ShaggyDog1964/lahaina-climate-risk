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
    "MEHOINUSHAWIA672N",
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
        raise EnvironmentError("FRED_API_KEY environment variable not set.")

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
