"""Tests for src/ingest/hta_tourism.py."""

from __future__ import annotations

import pandas as pd
import pytest


def test_fetch_hta_visitors_raises():
    """fetch_hta_visitors raises NotImplementedError."""
    from src.ingest.hta_tourism import fetch_hta_visitors

    with pytest.raises(NotImplementedError):
        fetch_hta_visitors()


def test_load_hta_visitors_dtypes(tmp_path):
    """load_hta_visitors parses numeric columns correctly."""
    from src.ingest.hta_tourism import load_hta_visitors

    csv_path = tmp_path / "hta.csv"
    csv_path.write_text(
        "island,year_month,visitor_arrivals,visitor_expenditure_m\n"
        "Maui,2023-01,120000,250.5\n"
        "Maui,2023-02,115000,240.0\n"
        "Oahu,2023-01,350000,700.0\n"
    )
    df = load_hta_visitors(str(csv_path))
    assert pd.api.types.is_numeric_dtype(df["visitor_arrivals"])
    assert pd.api.types.is_numeric_dtype(df["visitor_expenditure_m"])
    assert len(df) == 3


def test_load_hta_visitors_missing_columns(tmp_path):
    """load_hta_visitors raises KeyError on missing columns."""
    from src.ingest.hta_tourism import load_hta_visitors

    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("island,year_month\nMaui,2023-01\n")
    with pytest.raises(KeyError):
        load_hta_visitors(str(csv_path))
