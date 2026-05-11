"""Global Moran's I with permutation inference (Anselin 1995)."""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp


class GlobalMoransI:
    """Global Moran's I statistic with analytical and permutation-based inference."""

    I_: float
    E_I_: float
    Var_I_: float
    z_score_: float
    p_value_analytical_: float
    p_value_permutation_: float
    I_perm_distribution_: np.ndarray

    def fit(
        self,
        y: np.ndarray,
        W: sp.csr_matrix,
        n_permutations: int = 999,
        seed: int = 42,
    ) -> "GlobalMoransI":
        n = len(y)
        z = (y - y.mean()) / y.std()
        Wz = W @ z
        S0 = W.sum()
        I = float((z @ Wz) / (z @ z) * (n / S0))
        self.I_ = I

        # Analytical moments (Cliff-Ord normality assumption)
        E_I = -1.0 / (n - 1)
        self.E_I_ = E_I

        S1 = float(0.5 * (W + W.T).power(2).sum())
        row_sums = np.asarray(W.sum(axis=1)).ravel()
        col_sums = np.asarray(W.sum(axis=0)).ravel()
        S2 = float(np.sum((row_sums + col_sums) ** 2))
        n2 = n * n
        A = n * ((n2 - 3 * n + 3) * S1 - n * S2 + 3 * S0 ** 2)
        B = (z ** 4).mean() / ((z ** 2).mean() ** 2)
        C = B * ((n2 - n) * S1 - 2 * n * S2 + 6 * S0 ** 2)
        D = (n - 1) * (n - 2) * (n - 3) * S0 ** 2
        Var_I = (A - C) / D - E_I ** 2
        self.Var_I_ = float(Var_I)
        z_score = (I - E_I) / np.sqrt(max(Var_I, 1e-12))
        self.z_score_ = float(z_score)

        from scipy.stats import norm
        self.p_value_analytical_ = float(2 * norm.sf(abs(z_score)))

        # Permutation inference
        rng = np.random.default_rng(seed)
        I_perm = np.empty(n_permutations)
        for k in range(n_permutations):
            zp = rng.permutation(z)
            Wzp = W @ zp
            I_perm[k] = float((zp @ Wzp) / (zp @ zp) * (n / S0))
        self.I_perm_distribution_ = I_perm
        self.p_value_permutation_ = float(
            (np.sum(I_perm >= I) + 1) / (n_permutations + 1)
        )
        return self

    def summary(self) -> dict:
        return {
            "I": self.I_,
            "E_I": self.E_I_,
            "Var_I": self.Var_I_,
            "z_score": self.z_score_,
            "p_value_analytical": self.p_value_analytical_,
            "p_value_permutation": self.p_value_permutation_,
        }
