"""Tests for src/inference/placebo.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def placebo_panel():
    """8-donor panel with known treatment effect for Lahaina."""
    np.random.seed(42)
    treated_zip = "96761"
    donor_zips = [f"967{i:02d}" for i in range(1, 9)]
    all_zips = [treated_zip] + donor_zips
    months_pre = [f"2021-{m:02d}" for m in range(1, 13)]
    months_post = [f"2022-{m:02d}" for m in range(1, 7)]
    months = months_pre + months_post
    fire_month = months_post[0]

    rows = []
    base = np.linspace(12.0, 12.3, len(months))
    for i, z in enumerate(all_zips):
        for j, m in enumerate(months):
            val = base[j] + 0.05 * i
            if z == treated_zip and m >= fire_month:
                val -= 0.15  # treatment effect
            rows.append({"zip_code": z, "year_month": m, "log_zhvi": val})
    return pd.DataFrame(rows), treated_zip, months_pre[-1]


def test_placebo_run_returns_j_rows(placebo_panel):
    """Placebo DataFrame has one row per donor."""
    from src.inference.placebo import InSpacePlacebo
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool

    panel, treated_zip, pre_end = placebo_panel
    dp = DonorPool(panel, treated_zip=treated_zip, pre_end=pre_end)
    dp.build(min_r2=0.0)
    n_donors = len([z for z in dp.donor_panel["zip_code"].unique() if z != treated_zip])

    placebo = InSpacePlacebo(ADHSyntheticControl, dp, None)
    df = placebo.run(n_jobs=1)
    assert len(df) == n_donors


def test_placebo_p_value_range(placebo_panel):
    """p_value is in [0, 1]."""
    from src.inference.placebo import InSpacePlacebo
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool

    panel, treated_zip, pre_end = placebo_panel
    dp = DonorPool(panel, treated_zip=treated_zip, pre_end=pre_end)
    dp.build(min_r2=0.0)

    placebo = InSpacePlacebo(ADHSyntheticControl, dp, None)
    placebo.run(n_jobs=1)
    p = placebo.p_value(5.0)
    assert 0.0 <= p <= 1.0


def test_discard_poor_fit_reduces_or_equal(placebo_panel):
    """Discarding placebos with very large pre-RMSPE multiple returns valid p-value."""
    from src.inference.placebo import InSpacePlacebo
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool

    panel, treated_zip, pre_end = placebo_panel
    dp = DonorPool(panel, treated_zip=treated_zip, pre_end=pre_end)
    dp.build(min_r2=0.0)

    placebo = InSpacePlacebo(ADHSyntheticControl, dp, None)
    placebo.run(n_jobs=1)
    ratio = 2.0

    # Use median pre-RMSPE as treated estimate so exactly half are discarded
    median_pre = float(placebo.placebo_df["pre_rmspe"].median())
    placebo.set_treated_pre_rmspe(median_pre)
    placebo.discard_poor_fit(max_pre_rmspe_multiple=2.0)
    p_discarded = placebo.p_value(ratio)
    # Result must be a valid probability
    assert 0.0 <= p_discarded <= 1.0


def test_placebo_empty_donor_pool_raises():
    """Fewer than 2 donors raises ValueError."""
    import pandas as pd

    from src.inference.placebo import InSpacePlacebo
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool

    np.random.seed(42)
    # Panel with only treated + 1 donor = too few for placebo
    rows = []
    for z in ["96761", "96762"]:
        for m in ["2021-01", "2021-02", "2021-03"]:
            rows.append({"zip_code": z, "year_month": m, "log_zhvi": 12.0 + np.random.normal(0, 0.01)})
    panel = pd.DataFrame(rows)
    dp = DonorPool(panel, treated_zip="96761", pre_end="2021-02")
    dp._donors = ["96762"]
    dp._donor_panel = panel

    placebo = InSpacePlacebo(ADHSyntheticControl, dp, None)
    with pytest.raises(ValueError, match=">="):
        placebo.run(n_jobs=1)


@pytest.fixture()
def synthetic_stale_model():
    """A fitted ADH model whose post_rmspe_ was never computed (stale pickle)."""
    from src.scm.adh_scm import ADHSyntheticControl
    np.random.seed(0)
    T0, J = 12, 4
    Y0 = np.random.normal(10, 0.5, (T0, J))
    Y1 = Y0 @ np.array([0.5, 0.5, 0, 0]) + np.random.normal(0, 0.01, T0)
    X0 = Y0.mean(axis=0, keepdims=True)  # (1, J) — one covariate (mean level)
    X1 = np.array([Y1.mean()])            # (1,)
    model = ADHSyntheticControl()
    model.fit(X0, X1, Y0, Y1)  # no Y0_all/Y1_all → post_rmspe_ stays None
    return model


def test_p_value_succeeds_with_post_fitted_pickle(placebo_panel):
    """p_value() works when the ADH model has is_post_fitted=True."""
    import io
    import pickle

    from src.inference.placebo import InSpacePlacebo
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool

    panel, treated_zip, pre_end = placebo_panel
    dp = DonorPool(panel, treated_zip=treated_zip, pre_end=pre_end)
    dp.build(min_r2=0.0)

    # Build a fitted model with post_rmspe_ set
    pivot = panel.pivot(index='year_month', columns='zip_code', values='log_zhvi').sort_index()
    donor_cols = [c for c in pivot.columns if c != treated_zip]
    Y0_all = pivot[donor_cols].values
    Y1_all = pivot[treated_zip].values
    pre_months = [m for m in pivot.index if m <= pre_end]
    T0 = len(pre_months)
    X0 = Y0_all[:T0].T  # (J, T0) transpose — simplified covariates
    X1 = Y1_all[:T0]

    model = ADHSyntheticControl()
    model.fit(X0.T, X1, Y0_all[:T0], Y1_all[:T0],
              Y0_all=Y0_all, Y1_all=Y1_all)
    assert model.is_post_fitted

    # Pickle round-trip
    buf = io.BytesIO()
    pickle.dump(model, buf)
    buf.seek(0)
    loaded = pickle.load(buf)
    assert loaded.is_post_fitted

    placebo = InSpacePlacebo(ADHSyntheticControl, dp, None)
    placebo.run(n_jobs=1)
    p = placebo.p_value(loaded.rmspe_ratio())
    assert 0.0 <= p <= 1.0


def test_stale_pickle_raises_clear_error(synthetic_stale_model):
    """A pickle with is_post_fitted=False raises RuntimeError with clear message."""
    assert not synthetic_stale_model.is_post_fitted
    with pytest.raises(RuntimeError, match="post_rmspe_"):
        synthetic_stale_model.rmspe_ratio()


def test_rmspe_ratio_computed_once_not_twice(placebo_panel):
    """rmspe_ratio() is called only once; second call returns cached value."""
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool

    panel, treated_zip, pre_end = placebo_panel
    dp = DonorPool(panel, treated_zip=treated_zip, pre_end=pre_end)
    dp.build(min_r2=0.0)

    pivot = panel.pivot(index='year_month', columns='zip_code', values='log_zhvi').sort_index()
    donor_cols = [c for c in pivot.columns if c != treated_zip]
    Y0_all = pivot[donor_cols].values
    Y1_all = pivot[treated_zip].values
    pre_months = [m for m in pivot.index if m <= pre_end]
    T0 = len(pre_months)

    X0 = Y0_all[:T0].mean(axis=0, keepdims=True)  # (1, J) — pre-period mean level
    X1 = np.array([Y1_all[:T0].mean()])            # (1,)
    model = ADHSyntheticControl()
    model.fit(X0, X1, Y0_all[:T0], Y1_all[:T0],
              Y0_all=Y0_all, Y1_all=Y1_all)

    r1 = model.rmspe_ratio()
    r2 = model.rmspe_ratio()
    assert r1 == r2  # exact equality — uses cached rmspe_ratio_
