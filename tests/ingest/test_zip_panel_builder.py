"""Tests for src/ingest/zip_panel_builder.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def synthetic_panel():
    """5-zip × 24-month synthetic ZHVI panel."""
    np.random.seed(42)
    zips = ["96761", "96793", "96732", "96768", "96779"]
    months = pd.period_range("2022-01", periods=24, freq="M").astype(str)
    rows = []
    for z in zips:
        base = 400000 + np.random.randint(0, 200000)
        for m in months:
            rows.append({"zip_code": z, "year_month": m, "zhvi": base + np.random.normal(0, 5000)})
    return pd.DataFrame(rows)


@pytest.fixture()
def synthetic_acs():
    """ACS covariates for 5 zips."""
    return pd.DataFrame(
        {
            "zip_code": ["96761", "96793", "96732", "96768", "96779"],
            "median_hh_income": [70000, 65000, 72000, 68000, 60000],
            "median_home_value": [650000, 500000, 480000, 450000, 420000],
            "total_population": [12000, 25000, 18000, 8000, 6000],
            "owner_occupied_units": [3000, 7000, 5000, 2000, 1500],
            "renter_occupied_units": [1500, 3000, 2500, 1000, 800],
            "total_workers": [5000, 10000, 7000, 3000, 2000],
        }
    )


def test_build_zip_panel_treated_column(synthetic_panel, synthetic_acs):
    """treated column == 1 only for Lahaina zip."""
    from src.ingest.zip_panel_builder import build_zip_panel

    panel = build_zip_panel(synthetic_panel, synthetic_acs, hta=None)
    n_months = panel["year_month"].nunique()
    assert panel["treated"].sum() == n_months


def test_build_zip_panel_log_zhvi_finite(synthetic_panel, synthetic_acs):
    """log_zhvi is finite for all rows."""
    from src.ingest.zip_panel_builder import build_zip_panel

    panel = build_zip_panel(synthetic_panel, synthetic_acs, hta=None)
    assert np.isfinite(panel["log_zhvi"]).all()


def test_build_zip_panel_post_column(synthetic_panel, synthetic_acs):
    """post == 1 for rows on/after 2023-08."""
    from src.ingest.zip_panel_builder import build_zip_panel

    panel = build_zip_panel(synthetic_panel, synthetic_acs, hta=None)
    if "2023-08" in panel["year_month"].values:
        assert panel[panel["year_month"] >= "2023-08"]["post"].all()


def test_build_zip_panel_columns(synthetic_panel, synthetic_acs):
    """Panel has required columns."""
    from src.ingest.zip_panel_builder import build_zip_panel

    panel = build_zip_panel(synthetic_panel, synthetic_acs, hta=None)
    for col in ["zip_code", "year_month", "zhvi", "log_zhvi", "treated", "post"]:
        assert col in panel.columns, f"Missing: {col}"
