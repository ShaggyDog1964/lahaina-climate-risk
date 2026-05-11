"""RMSPE utility functions for synthetic control inference."""

from __future__ import annotations

import numpy as np


def pre_rmspe(Y1_pre: np.ndarray, Y_synth_pre: np.ndarray) -> float:
    """Root mean squared prediction error over the pre-treatment period."""
    return float(np.sqrt(np.mean((Y1_pre - Y_synth_pre) ** 2)))


def post_rmspe(Y1_post: np.ndarray, Y_synth_post: np.ndarray) -> float:
    """Root mean squared prediction error over the post-treatment period."""
    return float(np.sqrt(np.mean((Y1_post - Y_synth_post) ** 2)))


def rmspe_ratio(pre: float, post: float) -> float:
    """Ratio of post-RMSPE to pre-RMSPE."""
    if pre < 1e-12:
        return float("inf")
    return post / pre


def gap_series(Y1: np.ndarray, Y_synth: np.ndarray) -> np.ndarray:
    """Element-wise gap: Y1 - synthetic."""
    return Y1 - Y_synth
