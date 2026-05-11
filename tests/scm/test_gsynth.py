"""Tests for src/scm/gsynth.py."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture()
def two_factor_dgp():
    """Synthetic DGP with 2 true latent factors."""
    np.random.seed(42)
    T0, T_post, J, r_true = 30, 12, 8, 2

    # True factors and loadings
    F_true = np.random.randn(T0 + T_post, r_true)
    Lambda_donors = np.random.randn(r_true, J)
    lambda_treated = np.random.randn(r_true)

    Y0_all = (F_true @ Lambda_donors) + np.random.normal(0, 0.05, (T0 + T_post, J))
    Y1_pre = F_true[:T0] @ lambda_treated + np.random.normal(0, 0.05, T0)
    Y1_post = F_true[T0:] @ lambda_treated - 0.10  # treatment effect
    Y1_all = np.concatenate([Y1_pre, Y1_post])

    return {
        "Y0_pre": Y0_all[:T0],
        "Y1_pre": Y1_pre,
        "Y0_all": Y0_all,
        "Y1_all": Y1_all,
        "T0": T0,
        "r_true": r_true,
    }


def test_gsynth_pre_rmspe_finite(two_factor_dgp):
    """pre_rmspe_ is finite after fitting."""
    from src.scm.gsynth import GeneralizedSyntheticControl

    d = two_factor_dgp
    model = GeneralizedSyntheticControl()
    model.fit(d["Y0_pre"], d["Y1_pre"], d["Y0_all"], d["Y1_all"], r=2)
    assert np.isfinite(model.pre_rmspe_)


def test_gsynth_treatment_effect_shape(two_factor_dgp):
    """treatment_effect returns array of length T."""
    from src.scm.gsynth import GeneralizedSyntheticControl

    d = two_factor_dgp
    model = GeneralizedSyntheticControl()
    model.fit(d["Y0_pre"], d["Y1_pre"], d["Y0_all"], d["Y1_all"], r=2)
    gap = model.treatment_effect(d["Y1_all"])
    assert gap.shape == d["Y1_all"].shape


def test_gsynth_pre_period_near_zero(two_factor_dgp):
    """Pre-period treatment effect (gap) RMSE < 0.15."""
    from src.scm.gsynth import GeneralizedSyntheticControl

    d = two_factor_dgp
    model = GeneralizedSyntheticControl()
    model.fit(d["Y0_pre"], d["Y1_pre"], d["Y0_all"], d["Y1_all"], r=2)
    gap = model.treatment_effect(d["Y1_all"])
    pre_rmse = float(np.sqrt(np.mean(gap[:d["T0"]] ** 2)))
    assert pre_rmse < 0.15, f"Pre-period gap RMSE = {pre_rmse:.4f}"


def test_gsynth_select_r_returns_valid(two_factor_dgp):
    """select_r returns integer in [1, r_max]."""
    from src.scm.gsynth import GeneralizedSyntheticControl

    d = two_factor_dgp
    model = GeneralizedSyntheticControl()
    r = model.select_r(d["Y0_pre"], d["Y1_pre"], r_max=4)
    assert 1 <= r <= 4
