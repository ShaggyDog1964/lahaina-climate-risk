"""Redfin Research Data ingest — neighborhood market tracker."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

REDFIN_URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/neighborhood_market_tracker.tsv000.gz"
CACHE_PATH = Path("data/raw/redfin/hawaii_neighborhoods.parquet")

_KEEP_COLS = [
    "region", "period_begin", "period_end",
    "median_sale_price", "median_ppsf", "homes_sold",
    "inventory", "days_on_market", "sale_to_list",
]


def fetch_redfin_neighborhood(
    state: str = "Hawaii",
    force_download: bool = False,
    url: str = REDFIN_URL,
) -> pd.DataFrame:
    """Fetch Redfin neighborhood market tracker data for Hawaii.

    Streams and decompresses the gzipped TSV in chunks.
    Caches filtered result to data/raw/redfin/hawaii_neighborhoods.parquet.

    Args:
        state: State name to filter (default "Hawaii").
        force_download: Re-download even if cache exists.
        url: Override download URL.

    Returns:
        DataFrame with columns: region, period_begin, period_end,
        median_sale_price, median_ppsf, homes_sold, inventory,
        days_on_market, sale_to_list, year_month.
    """
    if CACHE_PATH.exists() and not force_download:
        logger.info("Loading Redfin data from cache: %s", CACHE_PATH)
        return pd.read_parquet(CACHE_PATH)

    logger.info("Downloading Redfin neighborhood data from %s", url)
    chunks = []
    try:
        for chunk in pd.read_csv(
            url,
            compression="gzip",
            chunksize=50_000,
            sep="\t",
            on_bad_lines="skip",
        ):
            hi_mask = chunk.get("state_code", pd.Series(dtype=str)) == "HI"
            filtered = chunk[hi_mask]
            if not filtered.empty:
                chunks.append(filtered)
    except Exception as exc:
        raise NotImplementedError(
            f"Redfin download failed: {exc}. "
            "Place data manually at data/raw/redfin/hawaii_neighborhoods.parquet"
        ) from exc

    if not chunks:
        raise ValueError(f"No {state} data found in Redfin market tracker.")

    df = pd.concat(chunks, ignore_index=True)

    # Keep only needed columns (ignore missing ones gracefully)
    available = [c for c in _KEEP_COLS if c in df.columns]
    df = df[available].copy()

    if "period_begin" in df.columns:
        df["period_begin"] = pd.to_datetime(df["period_begin"], errors="coerce")
        df["year_month"] = df["period_begin"].dt.to_period("M").astype(str)

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE_PATH, engine="pyarrow")
    logger.info("Cached %d Redfin rows to %s", len(df), CACHE_PATH)
    return df
