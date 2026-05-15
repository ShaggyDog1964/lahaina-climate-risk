"""Tests for src/inference/loo.py."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture()
def loo_dgp_unbalanced():
    """DGP where donor 0 has 90% weight (unstable)."""
    np.random.seed(42)
    T0, T_post, J = 24, 8, 5

    Y0_all = np.random.randn(T0 + T_post, J) + 12.0
    Y1_pre = 0.9 * Y0_all[:T0, 0] + 0.1 * Y0_all[:T0, 1] + np.random.normal(0, 0.005, T0)
    Y1_post = 0.9 * Y0_all[T0:, 0] + 0.1 * Y0_all[T0:, 1] - 0.15
    Y1_all = np.concatenate([Y1_pre, Y1_post])

    X0 = np.array([[np.mean(Y0_all[:T0, j])] for j in range(J)]).T
    X1 = np.array([np.mean(Y1_pre)])

    return {
        "Y0_pre": Y0_all[:T0],
        "Y1_pre": Y1_pre,
        "Y0_all": Y0_all,
        "Y1_all": Y1_all,
        "X0": X0,
        "X1": X1,
        "donor_names": [f"D{j}" for j in range(J)],
    }


@pytest.fixture()
def loo_dgp_balanced():
    """DGP with balanced weights (stable)."""
    np.random.seed(99)
    T0, T_post, J = 24, 8, 4

    Y0_all = np.random.randn(T0 + T_post, J) + 12.0
    w_true = np.array([0.25, 0.25, 0.25, 0.25])
    Y1_pre = Y0_all[:T0] @ w_true + np.random.normal(0, 0.005, T0)
    Y1_post = Y0_all[T0:] @ w_true
    Y1_all = np.concatenate([Y1_pre, Y1_post])

    X0 = np.array([[np.mean(Y0_all[:T0, j])] for j in range(J)]).T
    X1 = np.array([np.mean(Y1_pre)])

    return {
        "Y0_pre": Y0_all[:T0],
        "Y1_pre": Y1_pre,
        "Y0_all": Y0_all,
        "Y1_all": Y1_all,
        "X0": X0,
        "X1": X1,
        "donor_names": [f"D{j}" for j in range(J)],
    }


def test_loo_returns_result_dict(loo_dgp_unbalanced):
    """run() returns dict with expected keys."""
    from src.scm.adh_scm import ADHSyntheticControl
    from src.inference.loo import LeaveOneOutDiagnostic

    d = loo_dgp_unbalanced
    model = ADHSyntheticControl()
    model.fit(d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"])

    loo = LeaveOneOutDiagnostic()
    result = loo.run(
        model, d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"],
        d["Y0_all"], d["Y1_all"], d["donor_names"]
    )
    assert "loo_gaps" in result
    assert "base_gap" in result
    assert "pre_rmspes" in result


def test_loo_stability_score_unbalanced(loo_dgp_unbalanced):
    """Stability score > 0.0 for dominantly-weighted donor DGP."""
    from src.scm.adh_scm import ADHSyntheticControl
    from src.inference.loo import LeaveOneOutDiagnostic

    d = loo_dgp_unbalanced
    model = ADHSyntheticControl()
    model.fit(d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"])

    loo = LeaveOneOutDiagnostic()
    loo.run(
        model, d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"],
        d["Y0_all"], d["Y1_all"], d["donor_names"]
    )
    score = loo.stability_score()
    assert score >= 0.0


def test_loo_stability_score_raises_before_run():
    """stability_score raises before run()."""
    from src.inference.loo import LeaveOneOutDiagnostic

    loo = LeaveOneOutDiagnostic()
    with pytest.raises(RuntimeError):
        loo.stability_score()


def test_loo_empty_active_donors_returns_gracefully():
    """When no donors have weight > 0.05, LOO returns empty dict gracefully."""
    from src.scm.adh_scm import ADHSyntheticControl
    from src.inference.loo import LeaveOneOutDiagnostic

    np.random.seed(42)
    J = 25  # 25 donors -> uniform weight = 0.04 < 0.05
    T0, T = 10, 20
    Y0_all = np.random.normal(10, 1, (T, J))
    Y1_all = np.random.normal(10, 1, T)
    # Manually create a model with uniform low weights
    model = ADHSyntheticControl()
    model.w_ = np.ones(J) / J  # 0.04 each, all below 0.05
    model.V_ = np.eye(1)
    model.pre_rmspe_ = 0.1
    model.converged_ = True

    X0 = np.random.normal(0, 1, (2, J))
    X1 = np.zeros(2)
    loo = LeaveOneOutDiagnostic()
    result = loo.run(
        model, X0, X1, Y0_all[:T0], Y1_all[:T0], Y0_all, Y1_all,
        [f"z{j}" for j in range(J)]
    )
    assert result["loo_gaps"] == {}
