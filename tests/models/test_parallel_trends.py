"""Tests for src/models/parallel_trends.py."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def flat_pre_trend_df():
    """Event-study DataFrame with flat pre-period ATTs (null data)."""
    rng = np.random.default_rng(0)
    times = list(range(-12, 13))
    atts = [rng.normal(0, 0.005) for _ in times]
    ses = [0.02] * len(times)
    return pd.DataFrame(
        {
            "event_time": times,
            "att": atts,
            "se": ses,
            "ci_lower": [a - 1.96 * s for a, s in zip(atts, ses)],
            "ci_upper": [a + 1.96 * s for a, s in zip(atts, ses)],
        }
    )


def test_parallel_trends_passes_on_flat(flat_pre_trend_df):
    """test_parallel_trends returns passes=True for flat pre-trends."""
    from src.models.parallel_trends import test_parallel_trends

    result = test_parallel_trends(flat_pre_trend_df)
    assert result["passes"] is True


def test_parallel_trends_returns_dict_keys(flat_pre_trend_df):
    """test_parallel_trends returns dict with slope, p_value, passes."""
    from src.models.parallel_trends import test_parallel_trends

    result = test_parallel_trends(flat_pre_trend_df)
    assert "slope" in result
    assert "p_value" in result
    assert "passes" in result


def test_parallel_trends_steep_slope_fails():
    """Steep pre-trend should cause passes=False."""
    from src.models.parallel_trends import test_parallel_trends

    times = list(range(-12, 0))
    atts = [t * 0.05 for t in times]
    ses = [0.005] * 12
    df = pd.DataFrame(
        {
            "event_time": times,
            "att": atts,
            "se": ses,
            "ci_lower": [a - 1.96 * s for a, s in zip(atts, ses)],
            "ci_upper": [a + 1.96 * s for a, s in zip(atts, ses)],
        }
    )
    result = test_parallel_trends(df)
    assert result["passes"] is False


def test_plot_event_study_creates_file(flat_pre_trend_df, tmp_path):
    """plot_event_study saves a PDF file at the specified path."""
    from src.models.parallel_trends import plot_event_study

    out = str(tmp_path / "event_study.pdf")
    plot_event_study(flat_pre_trend_df, out)
    assert Path(out).exists()
    assert Path(out).stat().st_size > 0


def test_parallel_trends_insufficient_data():
    """ValueError raised when fewer than 2 pre-period observations."""
    from src.models.parallel_trends import test_parallel_trends

    df = pd.DataFrame(
        {
            "event_time": [0, 1, 2],
            "att": [0.1, 0.2, 0.3],
            "se": [0.01, 0.01, 0.01],
            "ci_lower": [0.0] * 3,
            "ci_upper": [0.4] * 3,
        }
    )
    with pytest.raises(ValueError, match="pre-period"):
        test_parallel_trends(df)
