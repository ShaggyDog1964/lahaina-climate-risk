"""Benchmark ADHSyntheticControl fit() for varying donor pool sizes."""

from __future__ import annotations

import time

import numpy as np


def _make_dgp(T0: int, J: int, seed: int = 42):
    rng = np.random.default_rng(seed)
    Y0_pre = rng.standard_normal((T0, J)) + 12.0
    Y1_pre = Y0_pre[:, 0] * 0.6 + Y0_pre[:, 1] * 0.4 + rng.normal(0, 0.01, T0)
    X0 = np.mean(Y0_pre, axis=0, keepdims=True)  # (1, J)
    X1 = np.array([np.mean(Y1_pre)])
    return X0, X1, Y0_pre, Y1_pre


def run_benchmark(J: int, T0: int = 30, max_seconds: float = 30.0) -> float:
    """Fit ADH SCM with J donors and return elapsed seconds."""
    from src.scm.adh_scm import ADHSyntheticControl

    X0, X1, Y0_pre, Y1_pre = _make_dgp(T0, J)
    model = ADHSyntheticControl()
    start = time.perf_counter()
    model.fit(X0, X1, Y0_pre, Y1_pre)
    elapsed = time.perf_counter() - start
    assert elapsed < max_seconds, f"J={J} took {elapsed:.1f}s > {max_seconds}s limit"
    return elapsed


if __name__ == "__main__":
    for j in [5, 20, 50]:
        t = run_benchmark(j)
        print(f"J={j:3d}: {t:.2f}s")
    print("All benchmarks passed.")
