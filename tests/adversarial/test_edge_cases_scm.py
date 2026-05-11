"""Adversarial edge cases for SCM implementations."""
from __future__ import annotations

import numpy as np
import pytest

np.random.seed(42)


def test_single_donor() -> None:
    """J=1 donor: ADH returns w=[1.0]."""
    from src.scm.adh_scm import ADHSyntheticControl
    rng = np.random.default_rng(42)
    T_pre = 20
    Y0_pre = rng.normal(0, 1, (T_pre, 1))
    Y1_pre = Y0_pre[:, 0] + rng.normal(0, 0.01, T_pre)
    X0 = Y0_pre[:5]    # shape (5, 1): k=5 covariates, J=1 donor
    X1 = Y1_pre[:5]   # shape (5,): k=5 covariates, 1D
    model = ADHSyntheticControl()
    model.fit(X0, X1, Y0_pre, Y1_pre)
    assert model.w_.shape == (1,)
    assert abs(model.w_[0] - 1.0) < 1e-4


def test_all_zero_outcome() -> None:
    """All-zero pre-treatment: pre_rmspe_ = 0 or informative error."""
    from src.scm.adh_scm import ADHSyntheticControl
    rng = np.random.default_rng(42)
    T_pre, J = 20, 5
    Y0_pre = np.zeros((T_pre, J))
    Y1_pre = np.zeros(T_pre)
    X0 = Y0_pre[:3]
    X1 = Y1_pre[:3].reshape(-1, 1)
    model = ADHSyntheticControl()
    try:
        model.fit(X0, X1, Y0_pre, Y1_pre)
        assert model.pre_rmspe_ == pytest.approx(0.0, abs=1e-8)
    except (ValueError, RuntimeError) as exc:
        assert len(str(exc)) > 0  # informative message


def test_perfect_prefit_donor() -> None:
    """Donor that perfectly matches treated: should get w=1 (or close)."""
    from src.scm.adh_scm import ADHSyntheticControl
    rng = np.random.default_rng(42)
    T_pre, J = 24, 5
    Y1_pre = rng.normal(0, 1, T_pre)
    Y0_pre = np.column_stack([rng.normal(0, 1, T_pre) for _ in range(J - 1)] + [Y1_pre])
    X0 = Y0_pre[:4]   # shape (4, J): k=4 covariates
    X1 = Y1_pre[:4]   # shape (4,): k=4 covariates, 1D
    model = ADHSyntheticControl()
    model.fit(X0, X1, Y0_pre, Y1_pre)
    # Last donor is perfect match
    assert model.w_[-1] > 0.7
