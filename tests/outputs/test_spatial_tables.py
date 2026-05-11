"""Tests for spatial LaTeX table generation."""
import pytest


def make_mock_registry():
    from unittest.mock import MagicMock
    import numpy as np
    reg = MagicMock()
    import pandas as pd
    reg.compare.return_value = pd.DataFrame({
        "model": ["SAR", "SEM", "SDM"],
        "aic": [-100.0, -102.0, -108.0],
    })
    mock_sar = MagicMock()
    mock_sar.rho_ = 0.35
    mock_sar.log_likelihood_ = -45.0
    mock_sar.aic_ = -100.0
    mock_sar.bic_ = -98.0
    mock_sar.se_ = np.array([0.05, 0.1])
    mock_sar.p_values_ = np.array([0.001, 0.05])
    reg._models = {"SAR": mock_sar, "SEM": mock_sar, "SDM": mock_sar}
    return reg


def test_moran_lisa_latex_contains_begin_table():
    from src.outputs.spatial_tables import moran_lisa_latex
    morans = {"I": 0.35, "E_I": -0.02, "z_score": 4.1, "p_value_analytical": 0.0001, "p_value_permutation": 0.002}
    counts = {"HH": 10, "LL": 8, "HL": 2, "LH": 3, "NS": 77, "total": 100}
    tex = moran_lisa_latex(morans, counts)
    assert r"\begin{table}" in tex
    assert "Moran" in tex


def test_effects_latex_contains_begin_table():
    import pandas as pd
    from src.outputs.spatial_tables import effects_latex
    effects_df = pd.DataFrame([{
        "variable": "dist_to_fire_km",
        "direct": -0.1, "indirect": -0.05, "total": -0.15,
        "direct_se": 0.02, "indirect_se": 0.01, "total_se": 0.03,
        "direct_p": 0.001, "indirect_p": 0.01, "total_p": 0.001,
    }])
    tex = effects_latex(effects_df)
    assert r"\begin{table}" in tex
