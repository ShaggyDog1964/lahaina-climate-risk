"""Tests for src/ingest/zillow_zip.py."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


@pytest.fixture()
def mock_zhvi_csv() -> str:
    """Minimal ZHVI CSV fixture (wide format)."""
    return (
        "RegionID,SizeRank,RegionName,RegionType,StateName,State,City,Metro,CountyName,"
        "2022-01-31,2022-02-28,2022-03-31\n"
        "1,1,96761,zip,Hawaii,HI,Lahaina,,,500000,510000,520000\n"
        "2,2,96793,zip,Hawaii,HI,Wailuku,,,400000,405000,410000\n"
        "3,3,90210,zip,California,CA,Beverly Hills,,,1000000,1010000,1020000\n"
    )


def test_fetch_zhvi_long_format(mock_zhvi_csv, tmp_path):
    """fetch_zhvi_by_zip returns long DataFrame with correct columns."""
    from src.ingest.zillow_zip import fetch_zhvi_by_zip

    cache_csv = tmp_path / "zhvi_zip.csv"
    cache_csv.write_text(mock_zhvi_csv)

    df = fetch_zhvi_by_zip(state="HI", cache_dir=tmp_path)

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == {"zip_code", "year_month", "zhvi"}
    # 2 HI zips × 3 date columns = 6 rows
    assert len(df) == 6


def test_fetch_zhvi_filters_state(mock_zhvi_csv, tmp_path):
    """fetch_zhvi_by_zip filters to requested state."""
    from src.ingest.zillow_zip import fetch_zhvi_by_zip

    cache_csv = tmp_path / "zhvi_zip.csv"
    cache_csv.write_text(mock_zhvi_csv)

    df = fetch_zhvi_by_zip(state="CA", cache_dir=tmp_path)
    assert all(df["zip_code"] == "90210")


def test_fetch_zhvi_no_negative_values(mock_zhvi_csv, tmp_path):
    """fetch_zhvi_by_zip drops negative ZHVI values."""
    from src.ingest.zillow_zip import fetch_zhvi_by_zip

    # Inject negative value
    csv_neg = mock_zhvi_csv.replace("500000", "-1")
    cache_csv = tmp_path / "zhvi_zip.csv"
    cache_csv.write_text(csv_neg)

    df = fetch_zhvi_by_zip(state="HI", cache_dir=tmp_path)
    assert (df["zhvi"] >= 0).all()


def test_fetch_zhvi_caches(mock_zhvi_csv, tmp_path):
    """fetch_zhvi_by_zip uses cache on second call."""
    from src.ingest.zillow_zip import fetch_zhvi_by_zip

    mock_resp = MagicMock()
    mock_resp.content = mock_zhvi_csv.encode()
    mock_resp.raise_for_status.return_value = None

    with patch("src.ingest.zillow_zip.requests.get", return_value=mock_resp) as mock_get:
        fetch_zhvi_by_zip(state="HI", cache_dir=tmp_path)
        fetch_zhvi_by_zip(state="HI", cache_dir=tmp_path)

    assert mock_get.call_count == 1


def test_fetch_zhvi_year_month_format(mock_zhvi_csv, tmp_path):
    """year_month column is in YYYY-MM format."""
    from src.ingest.zillow_zip import fetch_zhvi_by_zip

    cache_csv = tmp_path / "zhvi_zip.csv"
    cache_csv.write_text(mock_zhvi_csv)

    df = fetch_zhvi_by_zip(state="HI", cache_dir=tmp_path)
    assert df["year_month"].str.match(r"^\d{4}-\d{2}$").all()
