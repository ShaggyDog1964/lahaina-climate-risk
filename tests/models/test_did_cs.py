"""Tests for src/models/did_cs.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _make_synthetic_did_panel(
    n_units: int = 60,
    n_periods: int = 25,
    true_att: float = -0.15,
    rng_seed: int = 0,
) -> pd.DataFrame:
    """Create a synthetic DiD panel with known ATT.

    Args:
        n_units: Number of unique parcel units.
        n_periods: Number of time periods.
        true_att: True average treatment effect post-fire.
        rng_seed: Random seed for reproducibility.

    Returns:
        Long-panel DataFrame with event_time spanning -12 to +12.
    """
    rng = np.random.default_rng(rng_seed)
    fire_period = 12  # treatment starts at period 12

    rows = []
    for i in range(n_units):
        is_treated = i < n_units // 2
        group = "0-2km" if is_treated else "control"
        for t in range(n_periods):
            post = int(t >= fire_period)
            event_time = t - fire_period
            y = (
                12.0
                + 0.01 * t
                + (true_att * post if is_treated else 0.0)
                + rng.normal(0, 0.05)
            )
            rows.append(
                {
                    "parcel_id": f"P{i:04d}",
                    "fe_yearmonth": f"2022-{(t % 12) + 1:02d}",
                    "log_price": y,
                    "treatment_band": group,
                    "post": post,
                    "event_time": event_time,
                    "sale_date": pd.Timestamp("2022-01-01") + pd.DateOffset(months=t),
                }
            )

    return pd.DataFrame(rows)


def test_did_cs_att_close_to_truth():
    """Estimated simple ATT should be within 0.05 of true -0.15."""
    from src.models.did_cs import CallawayAntaCSiD

    panel = _make_synthetic_did_panel(true_att=-0.15)
    model = CallawayAntaCSiD()
    results = model.fit(panel)
    att = results["agg_simple"]["att"]
    assert abs(att - (-0.15)) < 0.10, f"ATT={att:.4f} not within 0.10 of -0.15"


def test_did_cs_event_study_range():
    """event_study_df() event_time should span at least -12 to +12."""
    from src.models.did_cs import CallawayAntaCSiD

    panel = _make_synthetic_did_panel(n_periods=25)
    model = CallawayAntaCSiD()
    model.fit(panel)
    es = model.event_study_df()
    assert es["event_time"].min() <= -12
    assert es["event_time"].max() >= 12


def test_did_cs_event_study_columns():
    """event_study_df() must have expected columns."""
    from src.models.did_cs import CallawayAntaCSiD

    panel = _make_synthetic_did_panel()
    model = CallawayAntaCSiD()
    model.fit(panel)
    es = model.event_study_df()
    for col in ["event_time", "att", "se", "ci_lower", "ci_upper"]:
        assert col in es.columns, f"Missing column: {col}"


def test_did_cs_pre_trends_not_significant():
    """Pre-trend ATTs on null data should not be strongly significant."""
    from src.models.did_cs import CallawayAntaCSiD
    from src.models.parallel_trends import test_parallel_trends

    panel = _make_synthetic_did_panel(true_att=0.0)
    model = CallawayAntaCSiD()
    model.fit(panel)
    es = model.event_study_df()
    pre = es[es["event_time"] < 0]
    if len(pre) >= 2:
        result = test_parallel_trends(pre)
        assert result["p_value"] > 0.01, (
            f"Pre-trend p-value={result['p_value']:.3f} unexpectedly low on null data"
        )


def test_did_cs_event_study_raises_before_fit():
    """RuntimeError raised when event_study_df() called before fit()."""
    from src.models.did_cs import CallawayAntaCSiD

    with pytest.raises(RuntimeError, match="fit\\(\\)"):
        CallawayAntaCSiD().event_study_df()
