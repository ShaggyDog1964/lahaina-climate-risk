"""Shared fixtures for numerical validation tests."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

_RECORDS: list[dict] = []


@pytest.fixture(autouse=True, scope="session")
def deviation_logger():
    yield _RECORDS
    Path("results/numerical_validation").mkdir(parents=True, exist_ok=True)
    if _RECORDS:
        pd.DataFrame(_RECORDS).to_csv(
            "results/numerical_validation/deviations.csv", index=False
        )


def log_result(records, test_name: str, n_problems: int, max_deviation: float, threshold: float):
    records.append({
        "test_name": test_name,
        "n_problems": n_problems,
        "max_deviation": max_deviation,
        "threshold": threshold,
        "pass_fail": "PASS" if max_deviation <= threshold else "FAIL",
    })
