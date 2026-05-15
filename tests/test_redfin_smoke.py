"""Smoke test for fetch_redfin_neighborhood chunked filtering.

Updated to match the corrected implementation which uses
``state_or_province`` (full name) instead of ``state_code`` (abbreviation).
"""
import pandas as pd
import pytest
from unittest.mock import patch

import src.ingest.redfin as redfin_mod


_COLS = [
    "state_or_province", "region", "period_begin", "period_end",
    "median_sale_price", "median_ppsf", "homes_sold",
    "inventory", "days_on_market", "sale_to_list",
]


def _chunk(rows):
    return pd.DataFrame(rows, columns=_COLS)


CHUNKS = [
    _chunk([
        ["Hawaii",     "Lahaina", "2023-01-01", "2023-01-31", 800000, 500, 10, 20, 30, 0.99],
        ["California", "LA",      "2023-01-01", "2023-01-31", 1200000, 700, 50, 100, 15, 1.02],
    ]),
    _chunk([
        ["Washington", "Seattle", "2023-02-01", "2023-02-28", 900000, 600, 30, 60, 20, 1.01],
    ]),
    _chunk([
        ["Hawaii",     "Honolulu", "2023-03-01", "2023-03-31", 750000, 480, 25, 40, 18, 0.98],
    ]),
]


def test_only_hawaii_rows_returned(tmp_path):
    orig = redfin_mod.CACHE_PATH
    redfin_mod.CACHE_PATH = tmp_path / "hawaii_neighborhoods.parquet"
    try:
        with patch("src.ingest.redfin.pd.read_csv", return_value=iter(CHUNKS)):
            df = redfin_mod.fetch_redfin_neighborhood(force_download=True)
        assert len(df) == 2, f"Expected 2 Hawaii rows, got {len(df)}"
        assert set(df["region"]) == {"Lahaina", "Honolulu"}
    finally:
        redfin_mod.CACHE_PATH = orig


def test_no_indexing_error_with_missing_column(tmp_path):
    """Chunk missing state_or_province should be skipped, not raise IndexingError."""
    orig = redfin_mod.CACHE_PATH
    redfin_mod.CACHE_PATH = tmp_path / "hawaii_neighborhoods.parquet"

    bad_chunk = pd.DataFrame({"region": ["Unknown"], "period_begin": ["2023-01-01"]})
    good_chunk = _chunk([
        ["Hawaii", "Maui", "2023-01-01", "2023-01-31", 700000, 400, 5, 10, 25, 0.97],
    ])

    try:
        with patch("src.ingest.redfin.pd.read_csv", return_value=iter([bad_chunk, good_chunk])):
            df = redfin_mod.fetch_redfin_neighborhood(force_download=True)
        assert len(df) == 1
        assert df["region"].iloc[0] == "Maui"
    except Exception as exc:
        pytest.fail(f"Unexpected {type(exc).__name__}: {exc}")
    finally:
        redfin_mod.CACHE_PATH = orig
