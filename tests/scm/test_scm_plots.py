"""Tests for src/outputs/scm_plots.py."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def time_periods():
    return [f"2022-{m:02d}" for m in range(1, 13)] + [f"2023-{m:02d}" for m in range(1, 7)]


@pytest.fixture()
def synthetic_series(time_periods):
    np.random.seed(42)
    T = len(time_periods)
    Y1 = np.linspace(12.0, 12.3, T) + np.random.normal(0, 0.02, T)
    Y_s = np.linspace(12.0, 12.4, T)
    return Y1, Y_s


def test_plot_scm_path_creates_file(time_periods, synthetic_series, tmp_path):
    from src.outputs.scm_plots import plot_scm_path

    Y1, Y_s = synthetic_series
    out = tmp_path / "scm_path.pdf"
    plot_scm_path(Y1, Y_s, time_periods, "2023-01", str(out))
    assert out.exists()


def test_plot_placebo_distribution_creates_file(time_periods, synthetic_series, tmp_path):
    from src.outputs.scm_plots import plot_placebo_distribution

    Y1, Y_s = synthetic_series
    T = len(time_periods)
    gap = Y1 - Y_s
    # Fake placebo df
    rows = [{"zip_code": f"9679{i}", "pre_rmspe": 0.01, "post_rmspe": 0.02, "rmspe_ratio": 2.0,
             **{f"gap_t{t}": float(gap[t]) * 0.5 for t in range(T)}} for i in range(5)]
    placebo_df = pd.DataFrame(rows)

    out = tmp_path / "placebo.pdf"
    plot_placebo_distribution(placebo_df, gap, time_periods, "2023-01", str(out))
    assert out.exists()


def test_plot_loo_creates_file(time_periods, synthetic_series, tmp_path):
    from src.outputs.scm_plots import plot_loo

    Y1, Y_s = synthetic_series
    gap = Y1 - Y_s
    loo_gaps = {"96793": gap * 0.9, "96732": gap * 1.1}

    out = tmp_path / "loo.pdf"
    plot_loo(gap, loo_gaps, time_periods, "2023-01", str(out))
    assert out.exists()
