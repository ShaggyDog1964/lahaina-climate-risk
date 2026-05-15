"""Tests for src/ingest/census_acs.py — fetch_acs_zip."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_census_response(rows: list[list[str]]) -> MagicMock:
    """Build a mock requests.Response for a successful Census API call.

    The Census API returns a list-of-lists where index 0 is the header row.
    """
    headers = [
        "NAME",
        "B19013_001E",
        "B25077_001E",
        "B01003_001E",
        "B25003_002E",
        "B25003_003E",
        "B08301_001E",
        "state",
        "zip code tabulation area",
    ]
    payload = [headers] + rows
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://api.census.gov/data/2022/acs/acs5"
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status.return_value = None
    return mock_resp


# ---------------------------------------------------------------------------
# Test 1: successful 200 response with valid Census JSON payload
# ---------------------------------------------------------------------------

class TestFetchAcsZipSuccess:
    """Happy-path: mock 200 response with two Hawaii ZIP rows."""

    def test_returns_dataframe_with_hawaii_zips(self, tmp_path):
        """DataFrame must be non-empty and contain zip_code column."""
        # Two Hawaii rows (prefixes 967 and 968)
        rows = [
            ["ZCTA5 96761", "75000", "650000", "12000", "8000", "4000", "6000", "15", "96761"],
            ["ZCTA5 96850", "68000", "580000", "30000", "20000", "10000", "15000", "15", "96850"],
        ]
        mock_resp = _make_census_response(rows)

        # Remove any pre-existing cache so the function issues a real (mocked) request
        cache_path = tmp_path / "acs_zip_2022.parquet"
        if cache_path.exists():
            cache_path.unlink()

        with patch("src.ingest.census_acs.requests.get", return_value=mock_resp) as mock_get:
            from src.ingest.census_acs import fetch_acs_zip

            df = fetch_acs_zip(year=2022, cache_dir=tmp_path)

        mock_get.assert_called_once()
        assert df.shape[0] > 0, "Expected at least one row in returned DataFrame"
        assert "zip_code" in df.columns, "'zip_code' column must be present"

    def test_numeric_columns_coerced(self, tmp_path):
        """Returned DataFrame must have numeric dtype for ACS estimate columns."""
        rows = [
            ["ZCTA5 96761", "75000", "650000", "12000", "8000", "4000", "6000", "15", "96761"],
        ]
        mock_resp = _make_census_response(rows)

        cache_path = tmp_path / "acs_zip_2022.parquet"
        if cache_path.exists():
            cache_path.unlink()

        with patch("src.ingest.census_acs.requests.get", return_value=mock_resp):
            from src.ingest.census_acs import fetch_acs_zip

            df = fetch_acs_zip(year=2022, cache_dir=tmp_path)

        numeric_cols = [
            "median_hh_income",
            "median_home_value",
            "total_population",
            "owner_occupied_units",
            "renter_occupied_units",
            "total_workers",
        ]
        for col in numeric_cols:
            if col in df.columns:
                assert df[col].dtype.kind in ("f", "i", "u"), (
                    f"Column '{col}' should be numeric, got {df[col].dtype}"
                )

    def test_zip_code_zero_padded(self, tmp_path):
        """zip_code values must be zero-padded to 5 characters."""
        rows = [
            ["ZCTA5 96761", "75000", "650000", "12000", "8000", "4000", "6000", "15", "96761"],
        ]
        mock_resp = _make_census_response(rows)

        cache_path = tmp_path / "acs_zip_2022.parquet"
        if cache_path.exists():
            cache_path.unlink()

        with patch("src.ingest.census_acs.requests.get", return_value=mock_resp):
            from src.ingest.census_acs import fetch_acs_zip

            df = fetch_acs_zip(year=2022, cache_dir=tmp_path)

        assert all(df["zip_code"].str.len() == 5), "All zip_code values must be 5 characters"

    def test_result_cached_to_parquet(self, tmp_path):
        """fetch_acs_zip must write a parquet cache file."""
        rows = [
            ["ZCTA5 96761", "75000", "650000", "12000", "8000", "4000", "6000", "15", "96761"],
        ]
        mock_resp = _make_census_response(rows)

        cache_path = tmp_path / "acs_zip_2022.parquet"
        if cache_path.exists():
            cache_path.unlink()

        with patch("src.ingest.census_acs.requests.get", return_value=mock_resp):
            from src.ingest.census_acs import fetch_acs_zip

            fetch_acs_zip(year=2022, cache_dir=tmp_path)

        assert cache_path.exists(), "Parquet cache file was not written"

    def test_cache_hit_skips_network(self, tmp_path):
        """Second call with same cache_dir must not issue a network request."""
        rows = [
            ["ZCTA5 96761", "75000", "650000", "12000", "8000", "4000", "6000", "15", "96761"],
        ]
        mock_resp = _make_census_response(rows)

        cache_path = tmp_path / "acs_zip_2022.parquet"
        if cache_path.exists():
            cache_path.unlink()

        with patch("src.ingest.census_acs.requests.get", return_value=mock_resp) as mock_get:
            from src.ingest.census_acs import fetch_acs_zip

            fetch_acs_zip(year=2022, cache_dir=tmp_path)
            assert mock_get.call_count == 1

            # Second call — cache now exists, should NOT call requests.get again
            fetch_acs_zip(year=2022, cache_dir=tmp_path)
            assert mock_get.call_count == 1, "Second call should read from cache, not network"


# ---------------------------------------------------------------------------
# Test 2: 400 error response
# ---------------------------------------------------------------------------

class TestFetchAcsZipHttpError:
    """After Agent 1's patch a 400 raises ValueError; before patch it raises HTTPError.
    The test accepts either to stay green regardless of patch order.
    """

    def test_400_raises_http_or_value_error(self, tmp_path):
        """A 400 from the Census API must raise HTTPError or ValueError with status info."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.url = "https://api.census.gov/data/2022/acs/acs5"
        mock_resp.text = "Invalid API key"
        # Simulate requests' raise_for_status behaviour
        mock_resp.raise_for_status.side_effect = requests.HTTPError(
            "400 Client Error", response=mock_resp
        )

        cache_path = tmp_path / "acs_zip_2022.parquet"
        if cache_path.exists():
            cache_path.unlink()

        with patch("src.ingest.census_acs.requests.get", return_value=mock_resp):
            from src.ingest.census_acs import fetch_acs_zip

            with pytest.raises((requests.HTTPError, ValueError)) as exc_info:
                fetch_acs_zip(year=2022, cache_dir=tmp_path)

        # If ValueError, it should contain the status code
        exc = exc_info.value
        if isinstance(exc, ValueError):
            assert "400" in str(exc), f"ValueError should mention status 400, got: {exc}"

    def test_500_raises_http_or_value_error(self, tmp_path):
        """A 500 response must also raise HTTPError or ValueError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.url = "https://api.census.gov/data/2022/acs/acs5"
        mock_resp.text = "Internal Server Error"
        mock_resp.raise_for_status.side_effect = requests.HTTPError(
            "500 Server Error", response=mock_resp
        )

        cache_path = tmp_path / "acs_zip_2022.parquet"
        if cache_path.exists():
            cache_path.unlink()

        with patch("src.ingest.census_acs.requests.get", return_value=mock_resp):
            from src.ingest.census_acs import fetch_acs_zip

            with pytest.raises((requests.HTTPError, ValueError)):
                fetch_acs_zip(year=2022, cache_dir=tmp_path)


# ---------------------------------------------------------------------------
# Test 3: network timeout
# ---------------------------------------------------------------------------

class TestFetchAcsZipTimeout:
    """Network timeout must propagate as requests.Timeout (or a subclass)."""

    def test_timeout_propagates(self, tmp_path):
        """When requests.get raises Timeout, fetch_acs_zip must not swallow it."""
        cache_path = tmp_path / "acs_zip_2022.parquet"
        if cache_path.exists():
            cache_path.unlink()

        with patch(
            "src.ingest.census_acs.requests.get",
            side_effect=requests.Timeout("Connection timed out"),
        ):
            from src.ingest.census_acs import fetch_acs_zip

            with pytest.raises(requests.Timeout):
                fetch_acs_zip(year=2022, cache_dir=tmp_path)

    def test_connection_error_propagates(self, tmp_path):
        """A ConnectionError from requests must also propagate unmodified."""
        cache_path = tmp_path / "acs_zip_2022.parquet"
        if cache_path.exists():
            cache_path.unlink()

        with patch(
            "src.ingest.census_acs.requests.get",
            side_effect=requests.ConnectionError("Name resolution failed"),
        ):
            from src.ingest.census_acs import fetch_acs_zip

            with pytest.raises(requests.ConnectionError):
                fetch_acs_zip(year=2022, cache_dir=tmp_path)
