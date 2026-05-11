"""Tests for src/scm/covariate_matrix.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def five_zip_panel():
    """5-zip × 36-month panel."""
    np.random.seed(42)
    zips = ["96761", "96793", "96732", "96768", "96779"]
    months = pd.period_range("2020-01", periods=36, freq="M").astype(str)
    base = np.linspace(12.0, 12.5, 36)
    rows = []
    for i, z in enumerate(zips):
        for j, m in enumerate(months):
            rows.append({"zip_code": z, "year_month": m, "log_zhvi": base[j] + 0.05 * i})
    return pd.DataFrame(rows)


@pytest.fixture()
def five_zip_acs():
    """ACS covariates for 5 zips."""
    return pd.DataFrame(
        {
            "zip_code": ["96761", "96793", "96732", "96768", "96779"],
            "median_hh_income": [70000.0, 65000.0, 72000.0, 68000.0, 60000.0],
            "median_home_value": [650000.0, 500000.0, 480000.0, 450000.0, 420000.0],
            "total_population": [12000.0, 25000.0, 18000.0, 8000.0, 6000.0],
            "owner_occupied_units": [3000.0, 7000.0, 5000.0, 2000.0, 1500.0],
            "renter_occupied_units": [1500.0, 3000.0, 2500.0, 1000.0, 800.0],
            "total_workers": [5000.0, 10000.0, 7000.0, 3000.0, 2000.0],
        }
    )


@pytest.fixture()
def donor_pool(five_zip_panel):
    from src.scm.donor_pool import DonorPool

    dp = DonorPool(five_zip_panel, treated_zip="96761", pre_end="2022-12")
    dp.build(min_r2=0.0)
    return dp


def test_covariate_matrix_shape(donor_pool, five_zip_acs):
    """X0 shape is (k, J) and X1 shape is (k,)."""
    from src.scm.covariate_matrix import build_covariate_matrix

    X0, X1, names = build_covariate_matrix(donor_pool, five_zip_acs)
    J = len([z for z in donor_pool.donor_panel["zip_code"].unique() if z != "96761"])
    assert X0.shape[1] == J
    assert X0.shape[0] == X1.shape[0]
    assert len(names) == X0.shape[0]


def test_covariate_matrix_no_nan(donor_pool, five_zip_acs):
    """X0 and X1 contain no NaN values."""
    from src.scm.covariate_matrix import build_covariate_matrix

    X0, X1, _ = build_covariate_matrix(donor_pool, five_zip_acs)
    assert not np.isnan(X0).any()
    assert not np.isnan(X1).any()


def test_outcome_matrix_shape(donor_pool):
    """Y0_pre shape is (T0, J) and Y1_pre shape is (T0,)."""
    from src.scm.covariate_matrix import build_outcome_matrices

    Y0_pre, Y1_pre, times = build_outcome_matrices(donor_pool)
    J = len([z for z in donor_pool.donor_panel["zip_code"].unique() if z != "96761"])
    T0 = len(times)
    assert Y0_pre.shape == (T0, J)
    assert Y1_pre.shape == (T0,)
