"""Tests for src/models/hedonic.py using TDD."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def dgp_panel():
    """Synthetic 200-observation DGP panel with known beta_structure=0.0003."""
    rng = np.random.default_rng(123)
    n = 200
    structure_sqft = rng.uniform(800, 5_000, n)
    land_area_sqft = rng.uniform(4_000, 40_000, n)
    year_built = rng.integers(1950, 2022, n)
    zoning = rng.choice(["R1", "R2", "C1"], n)
    fe_block = rng.choice([f"B{i}" for i in range(10)], n)
    fe_yearmonth = rng.choice([f"2022-{m:02d}" for m in range(1, 13)], n)

    beta_structure = 0.0003
    log_price = (
        12.5
        + beta_structure * structure_sqft
        + 0.000005 * land_area_sqft
        + 0.002 * (year_built - 1980)
        + rng.normal(0, 0.1, n)
    )

    return pd.DataFrame(
        {
            "log_price": log_price,
            "structure_sqft": structure_sqft,
            "land_area_sqft": land_area_sqft,
            "year_built": year_built,
            "zoning": zoning,
            "fe_block": fe_block,
            "fe_yearmonth": fe_yearmonth,
        }
    )


def test_hedonic_beta_structure_close_to_truth(dgp_panel):
    """Estimated beta_structure should be within 0.0002 of the true 0.0003."""
    from src.models.hedonic import HedonicModel

    model = HedonicModel()
    result = model.fit(dgp_panel)
    beta = result.params["structure_sqft"]
    assert abs(beta - 0.0003) < 0.0002, f"beta={beta:.6f} not within 0.0002 of 0.0003"


def test_hedonic_r_squared_above_threshold(dgp_panel):
    """R-squared should exceed 0.3 on the DGP panel."""
    from src.models.hedonic import HedonicModel

    model = HedonicModel()
    result = model.fit(dgp_panel)
    assert result.rsquared > 0.3, f"R²={result.rsquared:.3f} < 0.3"


def test_hedonic_summary_table_columns(dgp_panel):
    """summary_table() returns DataFrame with expected columns."""
    from src.models.hedonic import HedonicModel

    model = HedonicModel()
    model.fit(dgp_panel)
    table = model.summary_table()
    for col in ["coef", "se", "t", "p", "ci_lower_95", "ci_upper_95"]:
        assert col in table.columns, f"Missing column: {col}"


def test_hedonic_zoning_dummies_in_index(dgp_panel):
    """Zoning dummies should appear in results params index."""
    from src.models.hedonic import HedonicModel

    model = HedonicModel()
    result = model.fit(dgp_panel)
    params_str = " ".join(str(k) for k in result.params.index)
    assert "zoning" in params_str.lower() or "C(zoning)" in params_str


def test_hedonic_missing_columns_raises():
    """KeyError raised when required columns are missing."""
    from src.models.hedonic import HedonicModel

    bad_panel = pd.DataFrame({"log_price": [1.0], "structure_sqft": [1000.0]})
    with pytest.raises(KeyError, match="missing required columns"):
        HedonicModel().fit(bad_panel)


def test_hedonic_summary_table_raises_before_fit():
    """RuntimeError raised when summary_table() called before fit()."""
    from src.models.hedonic import HedonicModel

    with pytest.raises(RuntimeError, match="fit\\(\\)"):
        HedonicModel().summary_table()
