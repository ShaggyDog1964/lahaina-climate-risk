"""Tests for src/scm/adh_scm.py."""

from __future__ import annotations

import time

import numpy as np
import pytest


@pytest.fixture()
def synthetic_dgp():
    """10-donor DGP with known true weights w=[0.3, 0.7, 0, ..., 0].

    Donors 0 and 1 exactly span the treated pre-period series (tiny noise),
    making them the only rational choice for the synthetic control.
    """
    np.random.seed(42)
    T0, T_post, J = 30, 12, 10
    T = T0 + T_post

    # True donor series: deterministic trends so covariates are distinctive
    t = np.linspace(0, 1, T)
    Y0_all = np.zeros((T, J))
    Y0_all[:, 0] = 12.0 + 0.5 * t               # donor 0: upward trend
    Y0_all[:, 1] = 11.5 + 0.3 * t               # donor 1: similar upward
    for j in range(2, J):
        # Other donors have very different levels/trends
        Y0_all[:, j] = 9.0 + j * 0.4 + t * (j % 3 - 1)

    # Treated is 0.3*donor0 + 0.7*donor1 + tiny noise
    noise = np.random.normal(0, 0.005, T)
    Y_clean = 0.3 * Y0_all[:, 0] + 0.7 * Y0_all[:, 1]
    Y1_all = Y_clean + noise
    Y1_all[T0:] -= 0.15   # inject treatment effect post-T0

    Y1_pre = Y1_all[:T0]
    Y1_post = Y1_all[T0:]

    # Covariates: pre-period mean and slope — distinctive across donors
    t_idx = np.arange(T0, dtype=float)
    X1 = np.array([np.mean(Y1_pre), np.polyfit(t_idx, Y1_pre, 1)[0]])
    X0 = np.vstack([
        [np.mean(Y0_all[:T0, j]) for j in range(J)],
        [np.polyfit(t_idx, Y0_all[:T0, j], 1)[0] for j in range(J)],
    ])  # (2, J)

    return {
        "Y0_pre": Y0_all[:T0],
        "Y1_pre": Y1_pre,
        "Y0_post": Y0_all[T0:],
        "Y1_post": Y1_post,
        "Y0_all": Y0_all,
        "Y1_all": Y1_all,
        "X0": X0,
        "X1": X1,
        "T0": T0,
    }


def test_adh_weights_sum_to_one(synthetic_dgp):
    """Weights sum to approximately 1."""
    from src.scm.adh_scm import ADHSyntheticControl

    d = synthetic_dgp
    model = ADHSyntheticControl()
    model.fit(d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"])
    assert abs(model.w_.sum() - 1.0) < 1e-4


def test_adh_weights_non_negative(synthetic_dgp):
    """All weights are non-negative."""
    from src.scm.adh_scm import ADHSyntheticControl

    d = synthetic_dgp
    model = ADHSyntheticControl()
    model.fit(d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"])
    assert (model.w_ >= -1e-6).all()


def test_adh_beats_uniform_weights(synthetic_dgp):
    """Fitted SCM pre-RMSPE ≤ uniform weights pre-RMSPE."""
    from src.scm.adh_scm import ADHSyntheticControl

    d = synthetic_dgp
    J = d["Y0_pre"].shape[1]
    model = ADHSyntheticControl()
    model.fit(d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"])

    uniform_w = np.ones(J) / J
    uniform_rmspe = float(np.sqrt(np.mean((d["Y1_pre"] - d["Y0_pre"] @ uniform_w) ** 2)))
    assert model.pre_rmspe_ <= uniform_rmspe + 1e-6, (
        f"SCM RMSPE {model.pre_rmspe_:.4f} > uniform {uniform_rmspe:.4f}"
    )


def test_adh_pre_rmspe_low(synthetic_dgp):
    """Pre-RMSPE < 0.05 on well-fitting DGP."""
    from src.scm.adh_scm import ADHSyntheticControl

    d = synthetic_dgp
    model = ADHSyntheticControl()
    model.fit(d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"])
    assert model.pre_rmspe_ < 0.05, f"pre_rmspe = {model.pre_rmspe_:.4f}"


def test_adh_rmspe_ratio_gt_one_with_effect(synthetic_dgp):
    """RMSPE ratio > 1.0 when treatment effect injected."""
    from src.scm.adh_scm import ADHSyntheticControl

    d = synthetic_dgp
    model = ADHSyntheticControl()
    model.fit(d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"])
    post_r = model.post_rmspe(d["Y1_post"], d["Y0_post"])
    assert model.rmspe_ratio() > 1.0


def test_adh_treatment_effect_shape(synthetic_dgp):
    """treatment_effect returns array of correct shape."""
    from src.scm.adh_scm import ADHSyntheticControl

    d = synthetic_dgp
    model = ADHSyntheticControl()
    model.fit(d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"])
    gap = model.treatment_effect(d["Y1_all"], d["Y0_all"])
    assert gap.shape == d["Y1_all"].shape


@pytest.mark.parametrize("J,T0", [(5, 24), (10, 48)])
def test_adh_runtime(J, T0):
    """ADH fit completes within time limit."""
    from src.scm.adh_scm import ADHSyntheticControl

    rng = np.random.default_rng(42)
    Y0_pre = rng.normal(10, 1, (T0, J))
    Y1_pre = Y0_pre[:, 0] * 0.6 + Y0_pre[:, 1] * 0.4 + rng.normal(0, 0.05, T0)
    X0 = rng.normal(0, 1, (3, J))
    X1 = X0[:, 0] * 0.6 + X0[:, 1] * 0.4
    model = ADHSyntheticControl()
    t0 = time.perf_counter()
    model.fit(X0, X1, Y0_pre, Y1_pre)
    elapsed = time.perf_counter() - t0
    limit = {5: 10, 10: 20}[J]
    assert elapsed < limit, f"ADH fit took {elapsed:.1f}s for J={J} (limit {limit}s)"


def test_adh_summary_keys(synthetic_dgp):
    """summary() returns dict with expected keys."""
    from src.scm.adh_scm import ADHSyntheticControl

    d = synthetic_dgp
    model = ADHSyntheticControl()
    model.fit(d["X0"], d["X1"], d["Y0_pre"], d["Y1_pre"])
    s = model.summary()
    assert "weights" in s
    assert "pre_rmspe" in s
    assert "post_rmspe" in s
    assert "rmspe_ratio" in s
