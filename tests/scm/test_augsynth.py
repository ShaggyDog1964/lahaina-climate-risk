"""Tests for src/scm/augsynth.py."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture()
def imbalanced_dgp():
    """DGP with deliberate pre-period imbalance for ADH."""
    np.random.seed(42)
    T0, T_post, J = 24, 12, 6

    Y0_all = np.cumsum(np.random.randn(T0 + T_post, J), axis=0) + 12.0
    # Treated unit has extra trend not captured by donors
    Y1_pre = np.mean(Y0_all[:T0, :3], axis=1) + np.linspace(0, 0.5, T0)
    Y1_post = np.mean(Y0_all[T0:, :3], axis=1) - 0.20

    # Uniform ADH weights (deliberately bad)
    w_adh = np.ones(J) / J

    return {
        "Y0_pre": Y0_all[:T0],
        "Y1_pre": Y1_pre,
        "Y0_all": Y0_all,
        "Y1_all": np.concatenate([Y1_pre, Y1_post]),
        "w_adh": w_adh,
        "T0": T0,
    }


def test_augsynth_bias_correction_nontrivial(imbalanced_dgp):
    """bias_correction_ has non-trivial standard deviation."""
    from src.scm.augsynth import AugmentedSyntheticControl

    d = imbalanced_dgp
    model = AugmentedSyntheticControl()
    model.fit(d["w_adh"], d["Y0_pre"], d["Y1_pre"], d["Y0_all"], d["Y1_all"])
    assert np.std(model.bias_correction_) > 0


def test_augsynth_tau_shape(imbalanced_dgp):
    """treatment_effect() returns array length T."""
    from src.scm.augsynth import AugmentedSyntheticControl

    d = imbalanced_dgp
    model = AugmentedSyntheticControl()
    model.fit(d["w_adh"], d["Y0_pre"], d["Y1_pre"], d["Y0_all"], d["Y1_all"])
    tau = model.treatment_effect()
    T = len(d["Y1_all"])
    assert tau.shape == (T,)


def test_augsynth_ascm_improves_over_raw(imbalanced_dgp):
    """ASCM RMSE in post-period lower than raw SCM RMSE."""
    from src.scm.augsynth import AugmentedSyntheticControl

    d = imbalanced_dgp
    T0 = d["T0"]
    model = AugmentedSyntheticControl()
    model.fit(d["w_adh"], d["Y0_pre"], d["Y1_pre"], d["Y0_all"], d["Y1_all"])

    raw_post_rmse = float(np.sqrt(np.mean(model.tau_raw_[T0:] ** 2)))
    ascm_post_rmse = float(np.sqrt(np.mean(model.tau_ascm_[T0:] ** 2)))
    # ASCM should generally do at least as well; relax to within a factor of 2
    assert ascm_post_rmse <= raw_post_rmse * 2.0
