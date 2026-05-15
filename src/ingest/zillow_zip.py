"""Zillow ZHVI zip-level data ingestion."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

ZHVI_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)
CACHE_PATH = Path("data/raw/zillow/zhvi_zip.csv")


def fetch_zhvi_by_zip(state: str = "HI", cache_dir: Path | None = None) -> pd.DataFrame:
    """Download Zillow ZHVI single-family monthly CSV, melt to long format.

    Args:
        state: Two-letter state abbreviation to filter (default "HI").
        cache_dir: Directory for raw CSV cache; defaults to data/raw/zillow/.

    Returns:
        Long DataFrame with columns [zip_code, year_month, zhvi].
    """
    cache_path = Path(cache_dir) / "zhvi_zip.csv" if cache_dir else CACHE_PATH
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if not cache_path.exists():
        resp = requests.get(ZHVI_URL, timeout=120)
        if resp.status_code != 200:
            raise ValueError(
                f"HTTP {resp.status_code} from {resp.url}: {resp.text[:400]}"
            )
        resp.raise_for_status()
        cache_path.write_bytes(resp.content)

    raw = pd.read_csv(cache_path, low_memory=False)

    # Filter to requested state
    if "State" in raw.columns:
        raw = raw[raw["State"] == state].copy()

    # Identify date columns (YYYY-MM-DD format)
    date_cols = [c for c in raw.columns if _is_date_col(c)]

    if "RegionName" not in raw.columns:
        raise ValueError("Expected 'RegionName' column in ZHVI CSV")

    # Melt wide → long
    long = raw.melt(
        id_vars=["RegionName"],
        value_vars=date_cols,
        var_name="date_str",
        value_name="zhvi",
    )
    long["zip_code"] = long["RegionName"].astype(str).str.zfill(5)
    long["year_month"] = pd.to_datetime(long["date_str"]).dt.to_period("M").astype(str)
    long = long.dropna(subset=["zhvi"])
    long = long[long["zhvi"] >= 0]

    return long[["zip_code", "year_month", "zhvi"]].reset_index(drop=True)


def _is_date_col(col: str) -> bool:
    """Return True if column looks like YYYY-MM-DD."""
    try:
        pd.to_datetime(col)
        return True
    except (ValueError, TypeError):
        return False
