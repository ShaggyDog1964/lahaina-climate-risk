"""Tests for src/ingest/fred.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


@pytest.fixture()
def fred_json_response():
    """Minimal FRED API response fixture."""
    return {
        "observations": [
            {"date": "2023-01-01", "value": "75000.0"},
            {"date": "2023-02-01", "value": "75500.0"},
            {"date": "2023-03-01", "value": "."},
        ]
    }


@pytest.fixture()
def mock_env(monkeypatch):
    """Set FRED_API_KEY in environment."""
    monkeypatch.setenv("FRED_API_KEY", "test_key_12345")


def test_fetch_series_shape_and_dtypes(fred_json_response, mock_env, tmp_path):
    """fetch_series returns DataFrame with correct shape and dtypes."""
    from src.ingest.fred import fetch_series

    mock_response = MagicMock()
    mock_response.json.return_value = fred_json_response
    mock_response.raise_for_status.return_value = None

    with patch("src.ingest.fred.requests.get", return_value=mock_response):
        df = fetch_series(
            series_ids=["MEHOINUSHAWIA672N"],
            start="2023-01-01",
            end="2023-12-31",
            cache_dir=tmp_path,
        )

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == {"date", "series_id", "value"}
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.api.types.is_string_dtype(df["series_id"]) or df["series_id"].dtype == object
    assert pd.api.types.is_float_dtype(df["value"])
    assert len(df) == 3


def test_fetch_series_missing_api_key(monkeypatch, tmp_path):
    """fetch_series raises EnvironmentError when FRED_API_KEY is missing."""
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    # Reload module to pick up env change
    import importlib
    import src.ingest.fred as fred_mod
    importlib.reload(fred_mod)

    with pytest.raises(EnvironmentError, match="FRED_API_KEY"):
        fred_mod.fetch_series(["UNRATE"], "2023-01-01", "2023-12-31", cache_dir=tmp_path)


def test_fetch_series_caches_to_disk(fred_json_response, mock_env, tmp_path):
    """fetch_series writes raw JSON to cache directory and uses it on second call."""
    from src.ingest.fred import fetch_series

    mock_response = MagicMock()
    mock_response.json.return_value = fred_json_response
    mock_response.raise_for_status.return_value = None

    with patch("src.ingest.fred.requests.get", return_value=mock_response) as mock_get:
        fetch_series(["FEDFUNDS"], "2023-01-01", "2023-12-31", cache_dir=tmp_path)
        fetch_series(["FEDFUNDS"], "2023-01-01", "2023-12-31", cache_dir=tmp_path)

    # Second call should use cache, so requests.get called only once
    assert mock_get.call_count == 1


def test_fetch_multiple_series(mock_env, tmp_path):
    """fetch_series handles multiple series IDs."""
    from src.ingest.fred import fetch_series

    def side_effect(url, params, timeout):
        mock = MagicMock()
        mock.raise_for_status.return_value = None
        mock.json.return_value = {
            "observations": [{"date": "2023-01-01", "value": "1.0"}]
        }
        return mock

    with patch("src.ingest.fred.requests.get", side_effect=side_effect):
        df = fetch_series(
            ["UNRATE", "FEDFUNDS"],
            "2023-01-01",
            "2023-12-31",
            cache_dir=tmp_path,
        )

    assert set(df["series_id"].unique()) == {"UNRATE", "FEDFUNDS"}
