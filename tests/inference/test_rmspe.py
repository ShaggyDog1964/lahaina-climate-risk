"""Tests for src/inference/rmspe.py."""

from __future__ import annotations

import numpy as np
import pytest


def test_pre_rmspe_exact():
    """pre_rmspe returns exact value."""
    from src.inference.rmspe import pre_rmspe

    Y1 = np.array([1.0, 2.0, 3.0])
    Y_s = np.array([1.0, 2.0, 4.0])
    expected = float(np.sqrt(np.mean([0.0, 0.0, 1.0])))
    assert abs(pre_rmspe(Y1, Y_s) - expected) < 1e-10


def test_post_rmspe_exact():
    """post_rmspe returns exact value."""
    from src.inference.rmspe import post_rmspe

    Y1 = np.array([3.0, 4.0, 5.0])
    Y_s = np.array([3.0, 3.0, 3.0])
    expected = float(np.sqrt(np.mean([0.0, 1.0, 4.0])))
    assert abs(post_rmspe(Y1, Y_s) - expected) < 1e-10


def test_rmspe_ratio_exact():
    """rmspe_ratio returns post/pre."""
    from src.inference.rmspe import rmspe_ratio

    assert abs(rmspe_ratio(0.02, 0.10) - 5.0) < 1e-10


def test_rmspe_ratio_zero_pre():
    """rmspe_ratio returns inf when pre_rmspe is zero."""
    from src.inference.rmspe import rmspe_ratio

    assert rmspe_ratio(0.0, 0.05) == float("inf")


def test_gap_series_exact():
    """gap_series is element-wise difference."""
    from src.inference.rmspe import gap_series

    Y1 = np.array([1.0, 2.0, 3.0])
    Y_s = np.array([0.5, 1.5, 2.5])
    gap = gap_series(Y1, Y_s)
    np.testing.assert_array_almost_equal(gap, [0.5, 0.5, 0.5])
