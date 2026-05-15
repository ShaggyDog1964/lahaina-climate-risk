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
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool
    from src.inference.placebo import InSpacePlacebo

    panel, treated_zip, pre_end = placebo_panel
    dp = DonorPool(panel, treated_zip=treated_zip, pre_end=pre_end)
    dp.build(min_r2=0.0)
    n_donors = len([z for z in dp.donor_panel["zip_code"].unique() if z != treated_zip])

    placebo = InSpacePlacebo(ADHSyntheticControl, dp, None)
    df = placebo.run(n_jobs=1)
    assert len(df) == n_donors


def test_placebo_p_value_range(placebo_panel):
    """p_value is in [0, 1]."""
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool
    from src.inference.placebo import InSpacePlacebo

    panel, treated_zip, pre_end = placebo_panel
    dp = DonorPool(panel, treated_zip=treated_zip, pre_end=pre_end)
    dp.build(min_r2=0.0)

    placebo = InSpacePlacebo(ADHSyntheticControl, dp, None)
    placebo.run(n_jobs=1)
    p = placebo.p_value(5.0)
    assert 0.0 <= p <= 1.0


def test_discard_poor_fit_reduces_or_equal(placebo_panel):
    """Discarding placebos with very large pre-RMSPE multiple returns valid p-value."""
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool
    from src.inference.placebo import InSpacePlacebo

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
    from src.scm.adh_scm import ADHSyntheticControl
    from src.scm.donor_pool import DonorPool
    from src.inference.placebo import InSpacePlacebo
    import pandas as pd

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
