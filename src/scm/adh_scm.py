"""Abadie-Diamond-Hainmueller (2010) Synthetic Control from scratch."""

from __future__ import annotations

import numpy as np
import scipy.optimize as opt


class ADHSyntheticControl:
    """Abadie, Diamond & Hainmueller (2010) Synthetic Control.

    Solves:  min_w  (X1 - X0 @ w)' V (X1 - X0 @ w)
             s.t.   w >= 0, sum(w) == 1
    V is found by outer loop: min_V  MSPE_pre(w*(V))
    where w*(V) is the inner QP solution.
    """

    def __init__(self) -> None:
        self.w_: np.ndarray | None = None
        self.V_: np.ndarray | None = None
        self.pre_rmspe_: float | None = None
        self.post_rmspe_: float | None = None
        self._donor_names: list[str] | None = None

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------
    def _inner_qp(
        self, X0: np.ndarray, X1: np.ndarray, V: np.ndarray
    ) -> np.ndarray:
        """Solve inner QP: min_w (X1 - X0@w)'V(X1 - X0@w), w>=0, sum=1."""
        import cvxpy as cp

        J = X0.shape[1]
        w = cp.Variable(J, nonneg=True)
        resid = X1 - X0 @ w
        objective = cp.Minimize(cp.quad_form(resid, V))
        constraints = [cp.sum(w) == 1]
        prob = cp.Problem(objective, constraints)

        for solver in [cp.CLARABEL, cp.SCS, cp.ECOS]:
            try:
                prob.solve(solver=solver, verbose=False)
                if w.value is not None:
                    return np.clip(w.value, 0, None)
            except Exception:
                continue

        # Fallback: uniform weights
        return np.ones(J) / J

    def _outer_mspe(
        self,
        v_diag: np.ndarray,
        X0: np.ndarray,
        X1: np.ndarray,
        Y0_pre: np.ndarray,
        Y1_pre: np.ndarray,
    ) -> float:
        """Outer objective: pre-period MSPE given V diagonal."""
        v_diag = np.abs(v_diag)
        v_sum = v_diag.sum()
        if v_sum < 1e-12:
            v_diag = np.ones_like(v_diag)
            v_sum = float(len(v_diag))
        V = np.diag(v_diag / v_sum)
        w = self._inner_qp(X0, X1, V)
        resid = Y1_pre - Y0_pre @ w
        return float(np.mean(resid**2))

    def fit(
        self,
        X0: np.ndarray,
        X1: np.ndarray,
        Y0_pre: np.ndarray,
        Y1_pre: np.ndarray,
        donor_names: list[str] | None = None,
    ) -> ADHSyntheticControl:
        """Fit ADH synthetic control.

        Args:
            X0: Donor covariate matrix (k, J).
            X1: Treated covariate vector (k,).
            Y0_pre: Donor pre-period outcomes (T0, J).
            Y1_pre: Treated pre-period outcomes (T0,).
            donor_names: Optional list of donor labels.

        Returns:
            self
        """
        k = X0.shape[0]
        x0_init = np.ones(k) / k
        bounds = [(0, None)] * k

        result = opt.minimize(
            self._outer_mspe,
            x0=x0_init,
            args=(X0, X1, Y0_pre, Y1_pre),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 500, "ftol": 1e-12},
        )

        v_diag = np.abs(result.x)
        v_sum = v_diag.sum()
        if v_sum < 1e-12:
            v_diag = np.ones(k)
            v_sum = float(k)
        self.V_ = np.diag(v_diag / v_sum)

        self.w_ = self._inner_qp(X0, X1, self.V_)
        self.pre_rmspe_ = float(np.sqrt(np.mean((Y1_pre - Y0_pre @ self.w_) ** 2)))
        self._donor_names = donor_names
        return self

    def predict(self, Y0_all: np.ndarray) -> np.ndarray:
        """Synthetic control series: Y0_all @ w_."""
        return Y0_all @ self.w_

    def treatment_effect(
        self, Y1_all: np.ndarray, Y0_all: np.ndarray
    ) -> np.ndarray:
        """Gap series: Y1_all - synthetic."""
        return Y1_all - self.predict(Y0_all)

    def post_rmspe(self, Y1_post: np.ndarray, Y0_post: np.ndarray) -> float:
        """RMSPE over post-treatment period."""
        val = float(np.sqrt(np.mean((Y1_post - Y0_post @ self.w_) ** 2)))
        self.post_rmspe_ = val
        return val

    def rmspe_ratio(self) -> float:
        """Ratio of post-RMSPE to pre-RMSPE."""
        if self.post_rmspe_ is None or self.pre_rmspe_ is None:
            raise RuntimeError("Call post_rmspe() before rmspe_ratio().")
        if self.pre_rmspe_ < 1e-12:
            return float("inf")
        return self.post_rmspe_ / self.pre_rmspe_

    def summary(self) -> dict:
        """Return model summary dict."""
        weights = {}
        if self._donor_names and self.w_ is not None:
            weights = dict(zip(self._donor_names, self.w_.tolist(), strict=False))
        return {
            "weights": weights,
            "pre_rmspe": self.pre_rmspe_,
            "post_rmspe": self.post_rmspe_,
            "rmspe_ratio": self.post_rmspe_ / self.pre_rmspe_
            if (self.post_rmspe_ and self.pre_rmspe_)
            else None,
        }
