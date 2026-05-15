"""Tests for src/ingest/zip_panel_builder.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.ingest.zip_panel_builder import _coerce_zip_code, build_zip_panel
from src.ingest.exceptions import DataValidationError


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def synthetic_panel():
    """5-zip × 24-month synthetic ZHVI panel (str zip_code, normal path)."""
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
def zhvi_int_dtype():
    """ZHVI with int64 zip_code — exactly what pd.read_csv produces from the Snakefile."""
    np.random.seed(42)
    rows = []
    for zip_int in [96761, 96753, 96732, 96734, 96744]:
        for month in pd.date_range("2021-01", periods=24, freq="MS"):
            rows.append({
                "zip_code": zip_int,
                "year_month": month.strftime("%Y-%m"),
                "zhvi": 800_000 + np.random.default_rng(42).integers(0, 100_000),
            })
    return pd.DataFrame(rows)


@pytest.fixture()
def synthetic_acs():
    """ACS covariates for 5 zips (str zip_code — from parquet)."""
    return pd.DataFrame({
        "zip_code": ["96761", "96793", "96732", "96768", "96779"],
        "median_hh_income": [70000, 65000, 72000, 68000, 60000],
        "median_home_value": [650000, 500000, 480000, 450000, 420000],
        "total_population": [12000, 25000, 18000, 8000, 6000],
        "owner_occupied_units": [3000, 7000, 5000, 2000, 1500],
        "renter_occupied_units": [1500, 3000, 2500, 1000, 800],
        "total_workers": [5000, 10000, 7000, 3000, 2000],
    })


@pytest.fixture()
def acs_str_dtype():
    """ACS with 5 zips matching zhvi_int_dtype (str zip_code — from parquet)."""
    return pd.DataFrame({
        "zip_code": ["96761", "96753", "96732", "96734", "96744"],
        "median_hh_income": [70_000, 65_000, 80_000, 75_000, 72_000],
        "median_home_value": [900_000, 750_000, 850_000, 820_000, 790_000],
        "total_population": [9000, 7000, 12000, 11000, 8000],
        "owner_occupied_units": [3000, 2500, 4500, 4000, 3200],
        "renter_occupied_units": [1500, 1200, 2000, 1800, 1400],
        "total_workers": [4000, 3500, 6000, 5500, 4200],
    })


# ── _coerce_zip_code ──────────────────────────────────────────────────────────

def test_coerce_int_to_str(zhvi_int_dtype):
    result = _coerce_zip_code(zhvi_int_dtype)
    assert pd.api.types.is_string_dtype(result["zip_code"])
    assert result["zip_code"].str.len().eq(5).all()


def test_coerce_str_passthrough(acs_str_dtype):
    result = _coerce_zip_code(acs_str_dtype)
    assert pd.api.types.is_string_dtype(result["zip_code"])
    assert result["zip_code"].tolist() == ["96761", "96753", "96732", "96734", "96744"]


def test_coerce_strips_whitespace():
    df = pd.DataFrame({"zip_code": [" 96761 ", "96753"]})
    result = _coerce_zip_code(df)
    assert result["zip_code"].tolist() == ["96761", "96753"]


def test_coerce_raises_on_missing_column():
    with pytest.raises(DataValidationError, match="missing 'zip_code'"):
        _coerce_zip_code(pd.DataFrame({"region": [96761]}))


def test_coerce_does_not_mutate_original(zhvi_int_dtype):
    original_dtype = zhvi_int_dtype["zip_code"].dtype
    _coerce_zip_code(zhvi_int_dtype)
    assert zhvi_int_dtype["zip_code"].dtype == original_dtype


# ── build_zip_panel — primary regression test ─────────────────────────────────

def test_merge_succeeds_int_zhvi_str_acs(zhvi_int_dtype, acs_str_dtype):
    """PRIMARY REGRESSION TEST: int64 zhvi + str acs must not raise ValueError."""
    panel = build_zip_panel(zhvi_int_dtype, acs_str_dtype, hta=None)
    assert isinstance(panel, pd.DataFrame)
    assert len(panel) > 0


def test_zip_code_str_in_output(zhvi_int_dtype, acs_str_dtype):
    panel = build_zip_panel(zhvi_int_dtype, acs_str_dtype, hta=None)
    assert pd.api.types.is_string_dtype(panel["zip_code"]), "zip_code must be str in output panel"
    assert panel["zip_code"].str.len().eq(5).all()


def test_treated_column_correct(zhvi_int_dtype, acs_str_dtype):
    panel = build_zip_panel(zhvi_int_dtype, acs_str_dtype, hta=None, treated_zip="96761")
    assert panel["treated"].isin([0, 1]).all()
    assert panel.loc[panel["zip_code"] == "96761", "treated"].eq(1).all()
    assert panel.loc[panel["zip_code"] != "96761", "treated"].eq(0).all()


def test_hta_none_does_not_crash(zhvi_int_dtype, acs_str_dtype):
    panel = build_zip_panel(zhvi_int_dtype, acs_str_dtype, hta=None)
    assert "visitor_arrivals" not in panel.columns


def test_log_zhvi_finite(zhvi_int_dtype, acs_str_dtype):
    panel = build_zip_panel(zhvi_int_dtype, acs_str_dtype, hta=None)
    assert np.isfinite(panel["log_zhvi"]).all()
    assert (panel["log_zhvi"] > 0).all()


def test_output_schema(zhvi_int_dtype, acs_str_dtype):
    panel = build_zip_panel(zhvi_int_dtype, acs_str_dtype, hta=None)
    required = {"zip_code", "year_month", "zhvi", "log_zhvi", "treated", "post"}
    assert required.issubset(panel.columns), f"Missing: {required - set(panel.columns)}"


# ── Existing tests (keep passing) ────────────────────────────────────────────

def test_build_zip_panel_treated_column(synthetic_panel, synthetic_acs):
    """treated column == 1 only for Lahaina zip."""
    panel = build_zip_panel(synthetic_panel, synthetic_acs, hta=None)
    n_months = panel["year_month"].nunique()
    assert panel["treated"].sum() == n_months


def test_build_zip_panel_log_zhvi_finite(synthetic_panel, synthetic_acs):
    """log_zhvi is finite for all rows."""
    panel = build_zip_panel(synthetic_panel, synthetic_acs, hta=None)
    assert np.isfinite(panel["log_zhvi"]).all()


def test_build_zip_panel_post_column(synthetic_panel, synthetic_acs):
    """post == 1 for rows on/after 2023-08."""
    panel = build_zip_panel(synthetic_panel, synthetic_acs, hta=None)
    if "2023-08" in panel["year_month"].values:
        assert panel[panel["year_month"] >= "2023-08"]["post"].all()


def test_build_zip_panel_columns(synthetic_panel, synthetic_acs):
    """Panel has required columns."""
    panel = build_zip_panel(synthetic_panel, synthetic_acs, hta=None)
    for col in ["zip_code", "year_month", "zhvi", "log_zhvi", "treated", "post"]:
        assert col in panel.columns, f"Missing: {col}"
