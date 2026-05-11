"""Tests for src/scm/model_registry.py."""

from __future__ import annotations

import pandas as pd
import pytest


class _FakeModel:
    def __init__(self, pre, post):
        self.pre_rmspe_ = pre
        self.post_rmspe_ = post


def test_registry_register_and_get():
    """register and get work correctly."""
    from src.scm.model_registry import ModelRegistry

    reg = ModelRegistry()
    m = _FakeModel(0.01, 0.05)
    reg.register("ADH", m, {"note": "test"})
    entry = reg.get("ADH")
    assert entry["model"] is m
    assert entry["meta"]["note"] == "test"


def test_registry_compare_rmspe():
    """compare_rmspe returns DataFrame with 3 rows."""
    from src.scm.model_registry import ModelRegistry

    reg = ModelRegistry()
    reg.register("ADH", _FakeModel(0.01, 0.05), {})
    reg.register("GSynth", _FakeModel(0.008, 0.04), {})
    reg.register("ASCM", _FakeModel(0.01, 0.03), {})

    df = reg.compare_rmspe()
    assert len(df) == 3
    assert set(df.columns) == {"model", "pre_rmspe", "post_rmspe", "rmspe_ratio"}


def test_registry_contains():
    """__contains__ works."""
    from src.scm.model_registry import ModelRegistry

    reg = ModelRegistry()
    reg.register("ADH", _FakeModel(0.01, 0.05), {})
    assert "ADH" in reg
    assert "GSynth" not in reg
