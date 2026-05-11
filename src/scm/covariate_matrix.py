"""Build covariate and outcome matrices for synthetic control."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from src.scm.donor_pool import DonorPool


def build_covariate_matrix(
    donor_pool: DonorPool,
    acs: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build standardized covariate matrices X0 (donors) and X1 (treated).

    Covariates:
        - pre-period log_zhvi mean
        - pre-period log_zhvi OLS trend (slope)
        - median_hh_income
        - median_home_value
        - ownership_rate = owner_occupied / (owner + renter)
        - labor_attachment = total_workers / total_population

    Returns:
        (X0, X1, covariate_names) where X0 shape (k, J), X1 shape (k,).
    """
    panel = donor_pool.donor_panel
    pre = panel[panel["year_month"] <= donor_pool.pre_end].copy()
    pre = pre.sort_values("year_month")
    donors = [z for z in panel["zip_code"].unique() if z != donor_pool.treated_zip]
    months = sorted(pre["year_month"].unique())
    t_vals = np.arange(len(months), dtype=float).reshape(-1, 1)

    def _extract(zip_code: str) -> np.ndarray:
        zdf = pre[pre["zip_code"] == zip_code].set_index("year_month")["log_zhvi"]
        zdf = zdf.reindex(months).ffill().bfill()
        y = np.asarray(zdf)

        mean_zhvi = float(np.mean(y))
        reg = LinearRegression().fit(t_vals, y)
        trend = float(reg.coef_[0])

        acs_row = acs[acs["zip_code"] == zip_code]
        med_income = float(acs_row["median_hh_income"].iloc[0]) if len(acs_row) else 0.0
        med_value = float(acs_row["median_home_value"].iloc[0]) if len(acs_row) else 0.0
        owner = float(acs_row["owner_occupied_units"].iloc[0]) if len(acs_row) else 0.0
        renter = float(acs_row["renter_occupied_units"].iloc[0]) if len(acs_row) else 0.0
        workers = float(acs_row["total_workers"].iloc[0]) if len(acs_row) else 0.0
        pop = float(acs_row["total_population"].iloc[0]) if len(acs_row) else 1.0

        ownership = owner / max(owner + renter, 1.0)
        labor = workers / max(pop, 1.0)

        return np.array([mean_zhvi, trend, med_income, med_value, ownership, labor])

    covariate_names = [
        "log_zhvi_mean",
        "log_zhvi_trend",
        "median_hh_income",
        "median_home_value",
        "ownership_rate",
        "labor_attachment",
    ]

    X1 = _extract(donor_pool.treated_zip)
    X0_cols = np.column_stack([_extract(z) for z in donors])  # (k, J)

    # Standardize: subtract X1, divide by std of X0 row
    stds = np.std(X0_cols, axis=1, ddof=1)
    stds[stds < 1e-10] = 1.0
    X0_norm = (X0_cols - X1[:, None]) / stds[:, None]
    X1_norm = np.zeros(len(X1))  # treated is reference

    return X0_norm, X1_norm, covariate_names


def build_outcome_matrices(
    donor_pool: DonorPool,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build pre-period outcome matrices Y0_pre and Y1_pre.

    Returns:
        (Y0_pre, Y1_pre, time_periods_pre) where Y0_pre shape (T0, J),
        Y1_pre shape (T0,).
    """
    panel = donor_pool.donor_panel
    pre = panel[panel["year_month"] <= donor_pool.pre_end].copy()
    pre = pre.sort_values("year_month")
    months = sorted(pre["year_month"].unique())
    donors = [z for z in panel["zip_code"].unique() if z != donor_pool.treated_zip]

    def _series(zip_code: str) -> np.ndarray:
        zdf = pre[pre["zip_code"] == zip_code].set_index("year_month")["log_zhvi"]
        return np.asarray(zdf.reindex(months).ffill().bfill())

    Y1_pre = _series(donor_pool.treated_zip)
    Y0_pre = np.column_stack([_series(z) for z in donors])  # (T0, J)

    return Y0_pre, Y1_pre, months
