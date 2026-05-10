"""Tests for src/models/triple_diff.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _make_triple_diff_panel(
    n_units: int = 80,
    n_periods: int = 24,
    wui_extra_effect: float = -0.10,
    rng_seed: int = 42,
) -> pd.DataFrame:
    """Synthetic panel for triple-difference tests.

    Args:
        n_units: Number of unique parcel units.
        n_periods: Number of time periods.
        wui_extra_effect: Additional price effect for WUI parcels post-fire.
        rng_seed: Random seed for reproducibility.

    Returns:
        Long-panel DataFrame with WUI parcels having extra wui_extra_effect post-fire.
    """
    rng = np.random.default_rng(rng_seed)
    fire_period = 12

    rows = []
    for i in range(n_units):
        is_treated = i < n_units // 2
        # WUI is independent of treatment: alternating within each half so both
        # treated-WUI, treated-nonWUI, control-WUI, control-nonWUI cells exist.
        is_wui = (i % 4) < 2
        band = "0-2km" if is_treated else "control"
        wui_class = "Interface" if is_wui else "None"

        for t in range(n_periods):
            post = int(t >= fire_period)
            event_time = t - fire_period
            y = (
                12.0
                + 0.01 * t
                + (-0.08 * post if is_treated else 0.0)
                + (wui_extra_effect * post if (is_treated and is_wui) else 0.0)
                + rng.normal(0, 0.05)
            )
            rows.append(
                {
                    "parcel_id": f"P{i:04d}",
                    "fe_yearmonth": f"2022-{(t % 12) + 1:02d}",
                    "log_price": y,
                    "treatment_band": band,
                    "wui_class": wui_class,
                    "post": post,
                    "event_time": event_time,
                    "sale_date": pd.Timestamp("2022-01-01") + pd.DateOffset(months=t),
                }
            )

    return pd.DataFrame(rows)


def test_triple_diff_wui_harder_hit():
    """beta_post_treated_wui should be less than beta_post_treated_nowui."""
    from src.models.triple_diff import TripleDifference

    panel = _make_triple_diff_panel(wui_extra_effect=-0.10)
    model = TripleDifference()
    model.fit(panel)
    decomp = model.decompose()

    beta_wui = decomp.loc[decomp["term"] == "beta_post_treated_wui", "coef"].iloc[0]
    beta_nowui = decomp.loc[decomp["term"] == "beta_post_treated_nowui", "coef"].iloc[0]
    assert beta_wui < beta_nowui, (
        f"Expected WUI coef ({beta_wui:.4f}) < non-WUI coef ({beta_nowui:.4f})"
    )


def test_triple_diff_decompose_columns():
    """decompose() returns DataFrame with required columns."""
    from src.models.triple_diff import TripleDifference

    panel = _make_triple_diff_panel()
    model = TripleDifference()
    model.fit(panel)
    decomp = model.decompose()
    for col in ["term", "coef", "se", "interpretation"]:
        assert col in decomp.columns, f"Missing column: {col}"


def test_triple_diff_decompose_three_rows():
    """decompose() should return exactly 3 rows."""
    from src.models.triple_diff import TripleDifference

    panel = _make_triple_diff_panel()
    model = TripleDifference()
    model.fit(panel)
    decomp = model.decompose()
    assert len(decomp) == 3


def test_triple_diff_missing_columns_raises():
    """KeyError raised when required columns are missing."""
    from src.models.triple_diff import TripleDifference

    bad = pd.DataFrame({"log_price": [1.0], "post": [1]})
    with pytest.raises(KeyError):
        TripleDifference().fit(bad)


def test_triple_diff_decompose_raises_before_fit():
    """RuntimeError raised when decompose() called before fit()."""
    from src.models.triple_diff import TripleDifference

    with pytest.raises(RuntimeError, match="fit\\(\\)"):
        TripleDifference().decompose()
