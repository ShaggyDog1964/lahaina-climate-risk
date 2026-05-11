"""Tests for src/outputs/scm_tables.py."""

from __future__ import annotations

import numpy as np
import pytest


class _FakeModel:
    def __init__(self):
        self.w_ = np.array([0.0, 0.6, 0.0, 0.4])
        self.pre_rmspe_ = 0.01
        self.post_rmspe_ = 0.05


def _make_registry():
    from src.scm.model_registry import ModelRegistry

    reg = ModelRegistry()
    m = _FakeModel()
    reg.register(
        "ADH",
        m,
        {"donor_names": ["96793", "96732", "96768", "96779"], "acs": None},
    )
    reg.register("GSynth", _FakeModel(), {})
    reg.register("ASCM", _FakeModel(), {})
    return reg


def test_weights_table_latex_has_table(tmp_path):
    from src.outputs.scm_tables import weights_table_latex

    reg = _make_registry()
    latex = weights_table_latex(reg)
    assert r"\begin{table}" in latex


def test_rmspe_table_latex_has_table():
    from src.outputs.scm_tables import rmspe_table_latex

    reg = _make_registry()
    latex = rmspe_table_latex(reg)
    assert r"\begin{table}" in latex


def test_balance_table_latex_has_table():
    from src.outputs.scm_tables import balance_table_latex

    np.random.seed(42)
    k, J = 4, 3
    X0 = np.random.randn(k, J)
    X1 = np.zeros(k)
    w = np.array([0.5, 0.3, 0.2])
    cov_names = ["log_zhvi_mean", "log_zhvi_trend", "median_hh_income", "ownership_rate"]
    donor_names = ["96793", "96732", "96768"]

    latex = balance_table_latex(X0, X1, donor_names, cov_names, w)
    assert r"\begin{table}" in latex
