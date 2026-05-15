"""Comprehensive test suite for src/ingest/redfin.py.

Tests verify the CORRECT behavior:
- Column name: ``state_or_province``
- Filter value: ``"Hawaii"`` (full state name, not abbreviation)
- Default ``state`` parameter: ``"Hawaii"``

If Agent 1's patch has not yet been applied the current implementation still
uses ``state_code == "HI"``, so tests 1-5 will fail with assertion errors or
ValueError.  That is expected; do NOT modify src/ingest/redfin.py here.
"""
from __future__ import annotations

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

import src.ingest.redfin as redfin_mod

# ---------------------------------------------------------------------------
# Shared column layout (correct schema, post-fix)
# ---------------------------------------------------------------------------

_COLS = [
    "state_or_province",
    "region",
    "period_begin",
    "period_end",
    "median_sale_price",
    "median_ppsf",
    "homes_sold",
    "inventory",
    "days_on_market",
    "sale_to_list",
]


def _make_chunk(rows: list[list]) -> pd.DataFrame:
    """Return a DataFrame with the correct post-fix column layout."""
    return pd.DataFrame(rows, columns=_COLS)


# ---------------------------------------------------------------------------
# Helper: redirect CACHE_PATH to tmp_path and restore on teardown
# ---------------------------------------------------------------------------

class _CacheRedirect:
    """Context manager that points CACHE_PATH at a temp location."""

    def __init__(self, tmp_path, filename="cache.parquet"):
        self._tmp = tmp_path / filename
        self._orig = redfin_mod.CACHE_PATH

    def __enter__(self):
        redfin_mod.CACHE_PATH = self._tmp
        return self._tmp

    def __exit__(self, *_):
        redfin_mod.CACHE_PATH = self._orig


# ===========================================================================
# Test 1 — correct column name and filter value
# ===========================================================================

def test_correct_column_and_value(tmp_path):
    """Only rows where state_or_province == 'Hawaii' should be returned."""
    chunks = [
        _make_chunk([
            ["Hawaii", "Lahaina",     "2023-01-01", "2023-01-31", 800_000, 500, 10, 20, 30, 0.99],
            ["California", "LA",      "2023-01-01", "2023-01-31", 1_200_000, 700, 50, 100, 15, 1.02],
        ]),
        _make_chunk([
            ["Hawaii", "Honolulu",    "2023-03-01", "2023-03-31", 750_000, 480, 25, 40, 18, 0.98],
            ["Washington", "Seattle", "2023-02-01", "2023-02-28", 900_000, 600, 30, 60, 20, 1.01],
        ]),
    ]
    with _CacheRedirect(tmp_path):
        with patch("src.ingest.redfin.pd.read_csv", return_value=iter(chunks)):
            df = redfin_mod.fetch_redfin_neighborhood(force_download=True)

    assert len(df) == 2, f"Expected 2 Hawaii rows, got {len(df)}"
    assert set(df["region"]) == {"Lahaina", "Honolulu"}


# ===========================================================================
# Test 2 — ValueError when no Hawaii rows exist
# ===========================================================================

def test_no_hawaii_rows_raises(tmp_path):
    """ValueError must be raised (message contains 'Hawaii') when no matching rows."""
    chunks = [
        _make_chunk([
            ["California", "LA",      "2023-01-01", "2023-01-31", 1_200_000, 700, 50, 100, 15, 1.02],
            ["Washington", "Seattle", "2023-02-01", "2023-02-28", 900_000, 600, 30, 60, 20, 1.01],
        ]),
    ]
    with _CacheRedirect(tmp_path):
        with patch("src.ingest.redfin.pd.read_csv", return_value=iter(chunks)):
            with pytest.raises(ValueError, match="Hawaii"):
                redfin_mod.fetch_redfin_neighborhood(force_download=True)


# ===========================================================================
# Test 3 — whitespace normalisation on state_or_province
# ===========================================================================

def test_whitespace_normalization(tmp_path):
    """Rows with leading/trailing whitespace in state_or_province should still match.

    The correct implementation uses .str.strip() before comparing, so
    ' Hawaii ' must be treated identically to 'Hawaii'.
    """
    chunks = [
        _make_chunk([
            [" Hawaii ", "Maui",  "2023-01-01", "2023-01-31", 700_000, 420, 8, 15, 28, 0.97],
            ["California", "SF",  "2023-01-01", "2023-01-31", 1_400_000, 850, 40, 80, 10, 1.05],
        ]),
    ]
    with _CacheRedirect(tmp_path):
        with patch("src.ingest.redfin.pd.read_csv", return_value=iter(chunks)):
            df = redfin_mod.fetch_redfin_neighborhood(force_download=True)

    assert len(df) == 1, f"Expected 1 whitespace-normalised Hawaii row, got {len(df)}"
    assert df["region"].iloc[0] == "Maui"


# ===========================================================================
# Test 4 — "HI" abbreviation must NOT match
# ===========================================================================

def test_hi_abbreviation_not_matched(tmp_path):
    """Rows with state_or_province == 'HI' must NOT be treated as Hawaii."""
    chunks = [
        _make_chunk([
            ["HI", "Lahaina",     "2023-01-01", "2023-01-31", 800_000, 500, 10, 20, 30, 0.99],
            ["CA", "LA",          "2023-01-01", "2023-01-31", 1_200_000, 700, 50, 100, 15, 1.02],
        ]),
    ]
    with _CacheRedirect(tmp_path):
        with patch("src.ingest.redfin.pd.read_csv", return_value=iter(chunks)):
            with pytest.raises(ValueError, match="Hawaii"):
                redfin_mod.fetch_redfin_neighborhood(force_download=True)


# ===========================================================================
# Test 5 — Hawaii rows split across chunk boundaries
# ===========================================================================

def test_chunk_boundary_capture(tmp_path):
    """Hawaii rows split across 3 chunks must all be captured in the output."""
    chunks = [
        # chunk 1 — one Hawaii row
        _make_chunk([
            ["Hawaii", "Lahaina",     "2023-01-01", "2023-01-31", 800_000, 500, 10, 20, 30, 0.99],
            ["California", "LA",      "2023-01-01", "2023-01-31", 1_200_000, 700, 50, 100, 15, 1.02],
        ]),
        # chunk 2 — no Hawaii rows
        _make_chunk([
            ["Washington", "Seattle", "2023-02-01", "2023-02-28", 900_000, 600, 30, 60, 20, 1.01],
            ["California", "SF",      "2023-02-01", "2023-02-28", 1_400_000, 850, 40, 80, 10, 1.05],
        ]),
        # chunk 3 — two Hawaii rows
        _make_chunk([
            ["Hawaii", "Honolulu",    "2023-03-01", "2023-03-31", 750_000, 480, 25, 40, 18, 0.98],
            ["Hawaii", "Kihei",       "2023-03-01", "2023-03-31", 680_000, 440, 15, 25, 22, 0.96],
        ]),
    ]
    with _CacheRedirect(tmp_path):
        with patch("src.ingest.redfin.pd.read_csv", return_value=iter(chunks)):
            df = redfin_mod.fetch_redfin_neighborhood(force_download=True)

    assert len(df) == 3, f"Expected 3 Hawaii rows across 3 chunks, got {len(df)}"
    assert set(df["region"]) == {"Lahaina", "Honolulu", "Kihei"}


# ===========================================================================
# Test 6 — cache hit: pd.read_csv must NOT be called
# ===========================================================================

def test_cache_used_when_exists(tmp_path):
    """When a cached parquet exists and force_download=False, read_csv is never called."""
    # Write a minimal parquet to serve as the cache
    cached_df = pd.DataFrame({
        "region": ["Lahaina"],
        "period_begin": [pd.Timestamp("2023-01-01")],
        "period_end": [pd.Timestamp("2023-01-31")],
        "median_sale_price": [800_000.0],
        "median_ppsf": [500.0],
        "homes_sold": [10.0],
        "inventory": [20.0],
        "days_on_market": [30.0],
        "sale_to_list": [0.99],
        "year_month": ["2023-01"],
    })

    cache_file = tmp_path / "cache.parquet"
    cached_df.to_parquet(cache_file, engine="pyarrow")

    orig = redfin_mod.CACHE_PATH
    redfin_mod.CACHE_PATH = cache_file
    try:
        with patch("src.ingest.redfin.pd.read_csv") as mock_read_csv:
            result = redfin_mod.fetch_redfin_neighborhood(force_download=False)
            mock_read_csv.assert_not_called()

        assert len(result) == 1
        assert result["region"].iloc[0] == "Lahaina"
    finally:
        redfin_mod.CACHE_PATH = orig
