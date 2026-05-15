"""Tests for src/ingest/census_acs.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


@pytest.fixture()
def mock_census_response():
    """Minimal Census API response (list of lists)."""
    return [
        ["NAME", "B19013_001E", "B25077_001E", "B01003_001E",
         "B25003_002E", "B25003_003E", "B08301_001E", "state", "zip code tabulation area"],
        ["ZCTA5 96761", "75000", "650000", "12000", "3000", "1500", "5000", "15", "96761"],
        ["ZCTA5 96793", "65000", "500000", "25000", "7000", "3000", "10000", "15", "96793"],
    ]


def _make_mock_resp(json_data):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def test_fetch_acs_zip_columns(mock_census_response, tmp_path):
    """fetch_acs_zip returns DataFrame with renamed columns."""
    from src.ingest.census_acs import fetch_acs_zip

    with patch("src.ingest.census_acs.requests.get", return_value=_make_mock_resp(mock_census_response)):
        df = fetch_acs_zip(year=2022, cache_dir=tmp_path)

    expected_cols = {
        "zip_code", "median_hh_income", "median_home_value",
        "total_population", "owner_occupied_units",
        "renter_occupied_units", "total_workers",
    }
    assert expected_cols.issubset(set(df.columns))


def test_fetch_acs_zip_no_null_zip(mock_census_response, tmp_path):
    """fetch_acs_zip has no nulls in zip_code."""
    from src.ingest.census_acs import fetch_acs_zip

    with patch("src.ingest.census_acs.requests.get", return_value=_make_mock_resp(mock_census_response)):
        df = fetch_acs_zip(year=2022, cache_dir=tmp_path)

    assert df["zip_code"].notna().all()


def test_fetch_acs_zip_numeric(mock_census_response, tmp_path):
    """Numeric columns are float dtype."""
    from src.ingest.census_acs import fetch_acs_zip

    with patch("src.ingest.census_acs.requests.get", return_value=_make_mock_resp(mock_census_response)):
        df = fetch_acs_zip(year=2022, cache_dir=tmp_path)

    assert pd.api.types.is_numeric_dtype(df["median_hh_income"])


def test_fetch_acs_zip_caches(mock_census_response, tmp_path):
    """Second call uses parquet cache, not API."""
    from src.ingest.census_acs import fetch_acs_zip

    with patch("src.ingest.census_acs.requests.get", return_value=_make_mock_resp(mock_census_response)) as mock_get:
        fetch_acs_zip(year=2022, cache_dir=tmp_path)
        fetch_acs_zip(year=2022, cache_dir=tmp_path)

    assert mock_get.call_count == 1


def test_fetch_acs_zip_zip_code_is_str(mock_census_response, tmp_path):
    """zip_code column is str dtype with 5 chars."""
    from src.ingest.census_acs import fetch_acs_zip

    with patch("src.ingest.census_acs.requests.get", return_value=_make_mock_resp(mock_census_response)):
        df = fetch_acs_zip(year=2022, cache_dir=tmp_path)

    assert pd.api.types.is_string_dtype(df["zip_code"])
    assert df["zip_code"].str.len().eq(5).all()


def test_fetch_acs_zip_filters_hawaii(tmp_path):
    """fetch_acs_zip filters to Hawaii ZCTAs (967xx, 968xx)."""
    from src.ingest.census_acs import fetch_acs_zip

    response_with_non_hi = [
        ["NAME", "B19013_001E", "B25077_001E", "B01003_001E",
         "B25003_002E", "B25003_003E", "B08301_001E", "state", "zip code tabulation area"],
        ["ZCTA5 96761", "75000", "650000", "12000", "3000", "1500", "5000", "15", "96761"],
        ["ZCTA5 10001", "60000", "500000", "30000", "10000", "5000", "15000", "36", "10001"],  # NY
    ]
    with patch("src.ingest.census_acs.requests.get", return_value=_make_mock_resp(response_with_non_hi)):
        df = fetch_acs_zip(year=2023, cache_dir=tmp_path)

    assert all(df["zip_code"].str.startswith(("967", "968")))
    assert len(df) == 1
