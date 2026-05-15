"""Tests for src/scm/donor_pool.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def synthetic_zip_panel():
    """10-zip × 36-month panel with correlated pre-trends."""
    np.random.seed(42)
    zips = ["96761"] + [f"967{i:02d}" for i in range(1, 10)]
    months = pd.period_range("2020-01", periods=36, freq="M").astype(str)
    treated_base = np.linspace(12.0, 12.5, 36) + np.random.normal(0, 0.02, 36)
    rows = []
    for i, z in enumerate(zips):
        if z == "96761":
            series = treated_base
        else:
            # Highly correlated donors
            corr_noise = np.random.normal(0, 0.03, 36)
            series = treated_base + 0.1 * i + corr_noise
        for j, m in enumerate(months):
            rows.append({"zip_code": z, "year_month": m, "log_zhvi": float(series[j])})
    return pd.DataFrame(rows)


def test_donor_pool_build_excludes_treated(synthetic_zip_panel):
    """build() returns donors that do not include treated zip."""
    from src.scm.donor_pool import DonorPool

    dp = DonorPool(synthetic_zip_panel, treated_zip="96761", pre_end="2022-12")
    donors = dp.build()
    assert "96761" not in donors


def test_donor_pool_build_returns_at_least_two(synthetic_zip_panel):
    """build() returns ≥ 2 donors from 10-zip panel."""
    from src.scm.donor_pool import DonorPool

    dp = DonorPool(synthetic_zip_panel, treated_zip="96761", pre_end="2022-12")
    donors = dp.build(min_r2=0.0)  # relaxed for test
    assert len(donors) >= 2


def test_donor_panel_contains_treated(synthetic_zip_panel):
    """donor_panel property includes treated zip."""
    from src.scm.donor_pool import DonorPool

    dp = DonorPool(synthetic_zip_panel, treated_zip="96761", pre_end="2022-12")
    dp.build(min_r2=0.0)
    assert "96761" in dp.donor_panel["zip_code"].values


def test_donor_pool_raises_before_build(synthetic_zip_panel):
    """donor_panel raises RuntimeError before build()."""
    from src.scm.donor_pool import DonorPool

    dp = DonorPool(synthetic_zip_panel)
    with pytest.raises(RuntimeError):
        _ = dp.donor_panel


def test_screen_on_data_quality_removes_sparse_zips():
    """screen_on_data_quality drops zips with >10% missing log_zhvi."""
    from src.scm.donor_pool import DonorPool

    np.random.seed(0)
    zips = ["96761", "96799", "96700"]
    months = pd.period_range("2020-01", periods=20, freq="M").astype(str)
    rows = []
    for z in zips:
        for j, m in enumerate(months):
            val = float(12.0 + j * 0.01)
            # Give "96700" >10% NaN (only 16 of 20 months have data)
            if z == "96700" and j >= 16:
                val = float("nan")
            rows.append({"zip_code": z, "year_month": m, "log_zhvi": val})
    panel = pd.DataFrame(rows)

    # pre_end must cover all 20 months so NaN at j>=16 falls inside the pre-period
    dp = DonorPool(panel, treated_zip="96761", pre_end="2021-08")
    kept = dp.screen_on_data_quality(max_missing_pct=0.1)
    assert "96700" not in kept
    assert "96799" in kept


def test_dtype_guard_coerces_int_zip():
    """DonorPool warns and coerces int64 zip_code to str."""
    import warnings
    from src.scm.donor_pool import DonorPool

    months = pd.period_range("2020-01", periods=6, freq="M").astype(str)
    rows = []
    for z in [96761, 96799]:
        for m in months:
            rows.append({"zip_code": z, "year_month": m, "log_zhvi": 12.0})
    panel = pd.DataFrame(rows)
    # zip_code is int dtype here
    assert panel["zip_code"].dtype != object

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        dp = DonorPool(panel, treated_zip="96761", pre_end="2020-06")
        assert any("Coercing to str" in str(warning.message) for warning in w)

    assert pd.api.types.is_string_dtype(dp.panel["zip_code"])
    assert dp.treated_zip == "96761"
