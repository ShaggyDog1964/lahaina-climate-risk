"""Generalized Synthetic Control (Xu 2017) — interactive fixed effects."""

from __future__ import annotations

import numpy as np


class GeneralizedSyntheticControl:
    """Xu (2017) Generalized Synthetic Control via EM/IFE.

    Model: Y_it = delta_it * D_it + lambda_i' F_t + eps_it
    Estimate F (T x r) and Lambda (r x J) from donor panel via alternating LS.
    """

    def __init__(self) -> None:
        """Initialize an unfitted GeneralizedSyntheticControl.

        Attributes:
            F_: Pre-period factor matrix (T0 x r); None until fit.
            F_full_: Full-period factor matrix (T x r) extending F_ to post period; None until fit.
            lambda_1_: Treated unit factor loadings (r,); None until fit.
            lambda_0_: Donor factor loadings (r x J); None until fit.
            pre_rmspe_: Pre-period root mean squared prediction error; None until fit.
            r_: Number of latent factors used in the fitted model; None until fit.
        """
        self.F_: np.ndarray | None = None          # (T0, r) pre-period factors
        self.F_full_: np.ndarray | None = None      # (T_all, r)
        self.lambda_1_: np.ndarray | None = None    # (r,) treated loadings
        self.lambda_0_: np.ndarray | None = None    # (r, J) donor loadings
        self.pre_rmspe_: float | None = None
        self.r_: int | None = None

    def fit(
        self,
        Y0_pre: np.ndarray,
        Y1_pre: np.ndarray,
        Y0_all: np.ndarray,
        Y1_all: np.ndarray,
        r: int = 2,
    ) -> GeneralizedSyntheticControl:
        """Fit IFE model via alternating LS (EM-like).

        Args:
            Y0_pre: Donor pre-period outcomes (T0, J).
            Y1_pre: Treated pre-period outcomes (T0,).
            Y0_all: Donor full-period outcomes (T, J).
            Y1_all: Treated full-period outcomes (T,).
            r: Number of latent factors.

        Returns:
            self
        """
        T0, J = Y0_pre.shape
        self.r_ = r

        # Initialize F via SVD of donor pre-period matrix
        U, S, Vt = np.linalg.svd(Y0_pre, full_matrices=False)
        F = U[:, :r] * S[:r]  # (T0, r)

        for _ in range(200):
            F_old = F.copy()

            # E-step: OLS lambda for each donor
            Lambda0 = np.linalg.lstsq(F, Y0_pre, rcond=None)[0]  # (r, J)

            # OLS lambda for treated
            lambda_1 = np.linalg.lstsq(F, Y1_pre, rcond=None)[0]  # (r,)

            # M-step: update F
            F = np.linalg.lstsq(Lambda0.T, Y0_pre.T, rcond=None)[0].T  # (T0, r)

            if np.linalg.norm(F - F_old, "fro") < 1e-6:
                break

        self.F_ = F
        self.lambda_0_ = Lambda0
        self.lambda_1_ = lambda_1

        # Extend F to full period using donor post-period data
        T_all = Y0_all.shape[0]
        if T_all > T0:
            Y0_post = Y0_all[T0:]
            F_post = np.linalg.lstsq(Lambda0.T, Y0_post.T, rcond=None)[0].T
            self.F_full_ = np.vstack([F, F_post])
        else:
            self.F_full_ = F

        resid = Y1_pre - F @ lambda_1
        self.pre_rmspe_ = float(np.sqrt(np.mean(resid**2)))
        return self

    def treatment_effect(self, Y1_all: np.ndarray) -> np.ndarray:
        """Gap series: Y1_all - counterfactual."""
        if self.F_full_ is None or self.lambda_1_ is None:
            raise RuntimeError("Model not fitted. Call fit() before treatment_effect().")
        counterfactual = self.F_full_ @ self.lambda_1_
        return Y1_all - counterfactual

    def select_r(
        self,
        Y0_pre: np.ndarray,
        Y1_pre: np.ndarray,
        r_max: int = 5,
    ) -> int:
        """Select r via leave-one-out CV on donors.

        Returns:
            Optimal r in {1, ..., r_max}.
        """
        T0, J = Y0_pre.shape
        best_r, best_mse = 1, float("inf")

        for r in range(1, min(r_max, T0, J) + 1):
            loo_mse = []
            for j in range(J):
                mask = np.ones(J, dtype=bool)
                mask[j] = False
                Y0_loo = Y0_pre[:, mask]

                try:
                    U, S, Vt = np.linalg.svd(Y0_loo, full_matrices=False)
                    F_r = U[:, :r] * S[:r]
                    np.linalg.lstsq(F_r, Y0_loo, rcond=None)[0]
                    lambda_j = np.linalg.lstsq(
                        F_r, Y0_pre[:, j], rcond=None
                    )[0]
                    pred = F_r @ lambda_j
                    loo_mse.append(np.mean((Y0_pre[:, j] - pred) ** 2))
                except np.linalg.LinAlgError:
                    loo_mse.append(float("inf"))

            mse = float(np.mean(loo_mse))
            if mse < best_mse:
                best_mse, best_r = mse, r

        return best_r
