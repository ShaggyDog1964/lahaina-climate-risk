"""Spatial Durbin Model (SDM) via concentrated log-likelihood."""
from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.optimize import minimize_scalar
from scipy.stats import chi2, norm

from src.spatial_models.sar import _numerical_hessian


class SpatialDurbinModel:
    """SDM: y = rho*Wy + X*beta + W*X*theta + eps.

    Augments the design matrix with spatially lagged covariates W@X
    (excluding the spatial lag of the intercept column).
    """

    rho_: float
    beta_: np.ndarray    # k params for X
    theta_: np.ndarray   # k params for WX (excl. intercept)
    sigma2_: float
    log_likelihood_: float
    aic_: float
    bic_: float
    se_: np.ndarray
    t_stats_: np.ndarray
    p_values_: np.ndarray
    x_names_: list[str]
    wx_names_: list[str]
    all_names_: list[str]

    def fit(
        self,
        y: np.ndarray,
        X: np.ndarray,
        W: sp.csr_matrix,
        eigenvalues: np.ndarray,
        x_names: list[str] | None = None,
    ) -> SpatialDurbinModel:
        """Fit the Spatial Durbin Model via concentrated log-likelihood.

        NOTE: The keyword argument is lowercase ``x_names``, not ``X_names``.
        """
        n, k = X.shape
        self._n = n
        self._k = k
        self._x_names = x_names or [f"x{i}" for i in range(k)]
        eigenvalues = np.real(eigenvalues).ravel()
        I_n = sp.eye(n, format="csr")

        # Detect intercept column (constant column)
        intercept_col = None
        for c in range(k):
            if np.allclose(X[:, c], 1.0):
                intercept_col = c
                break

        # Build WX, excluding the intercept column
        WX_parts = []
        wx_names = []
        for c in range(k):
            if c == intercept_col:
                continue
            WX_parts.append(np.asarray(W @ X[:, c]).ravel())
            wx_names.append(f"W_{self._x_names[c]}" if self._x_names else f"Wx{c}")

        WX = np.column_stack(WX_parts) if WX_parts else np.empty((n, 0))

        X_aug = np.hstack([X, WX])
        self._k_aug = X_aug.shape[1]
        self._wx_names = wx_names
        self.x_names_ = self._x_names
        self.wx_names_ = self._wx_names
        self.all_names_ = self._x_names + self._wx_names

        def _conc_ll(rho: float) -> float:
            A = I_n - rho * W
            Ay = np.asarray(A @ y).ravel()
            beta_aug, _, _, _ = np.linalg.lstsq(X_aug, Ay, rcond=None)
            e = Ay - X_aug @ beta_aug
            sigma2 = float(e @ e / n)
            if sigma2 <= 0:
                return 1e10
            log_det = float(np.sum(np.log(np.abs(1.0 - rho * eigenvalues))))
            return float(-(log_det - (n / 2.0) * np.log(sigma2)))

        rho_min = 1.0 / np.min(eigenvalues) + 1e-4
        rho_max = 1.0 / np.max(eigenvalues) - 1e-4
        rho_min, rho_max = sorted([rho_min, rho_max])
        rho_min = max(rho_min, -0.9999)
        rho_max = min(rho_max, 0.9999)

        res = minimize_scalar(
            _conc_ll,
            bounds=(rho_min, rho_max),
            method="bounded",
            options={"xatol": 1e-6},
        )
        rho_hat = float(res.x)
        self.rho_ = rho_hat

        A_hat = I_n - rho_hat * W
        Ay_hat = np.asarray(A_hat @ y).ravel()
        beta_aug_hat, _, _, _ = np.linalg.lstsq(X_aug, Ay_hat, rcond=None)
        e_hat = Ay_hat - X_aug @ beta_aug_hat
        sigma2_hat = float(e_hat @ e_hat / n)

        self.beta_ = beta_aug_hat[:k]
        self.theta_ = beta_aug_hat[k:]
        self.sigma2_ = sigma2_hat

        log_det_hat = float(np.sum(np.log(np.abs(1.0 - rho_hat * eigenvalues))))
        self.log_likelihood_ = float(
            log_det_hat - (n / 2.0) * np.log(2 * np.pi * sigma2_hat) - n / 2.0
        )

        n_params = self._k_aug + 2
        self.aic_ = -2.0 * self.log_likelihood_ + 2.0 * n_params
        self.bic_ = -2.0 * self.log_likelihood_ + np.log(n) * n_params

        # SE via numerical Hessian of [rho, beta_aug]
        params0 = np.concatenate([[rho_hat], beta_aug_hat])

        def _full_ll_neg(params: np.ndarray) -> float:
            rho_p = params[0]
            beta_p = params[1:]
            if rho_p <= rho_min or rho_p >= rho_max:
                return 1e10
            A_p = I_n - rho_p * W
            e_p = np.asarray(A_p @ y).ravel() - X_aug @ beta_p
            s2 = max(float(e_p @ e_p / n), 1e-12)
            ld = float(np.sum(np.log(np.abs(1.0 - rho_p * eigenvalues))))
            return float(-(ld - (n / 2.0) * np.log(2 * np.pi * s2) - n / 2.0))

        H = _numerical_hessian(_full_ll_neg, params0)
        try:
            cov = np.linalg.inv(-H)
            se = np.sqrt(np.abs(np.diag(cov)))
        except np.linalg.LinAlgError:
            se = np.full(len(params0), np.nan)

        self.se_ = se
        self.t_stats_ = params0 / np.where(se > 0, se, np.nan)
        self.p_values_ = 2.0 * norm.sf(np.abs(self.t_stats_))
        self._cov_ = np.linalg.inv(-H) if np.isfinite(np.linalg.det(-H)) else np.diag(se**2)
        self._beta_aug_ = beta_aug_hat
        self._rho_min = rho_min
        self._rho_max = rho_max
        return self

    def test_sar_restriction(self, sar_model: object) -> dict:
        """LR test of theta=0 (SDM vs SAR); df = len(theta_)."""
        df = len(self.theta_)
        ll_sdm = self.log_likelihood_
        ll_sar = getattr(sar_model, "log_likelihood_", float("nan"))
        lr_stat = max(0.0, 2.0 * (ll_sdm - ll_sar))
        p_value = float(chi2.sf(lr_stat, df))
        return {"lr_stat": float(lr_stat), "df": df, "p_value": p_value}

    def test_sem_cf_restriction(self, sem_model: object, beta_sem: np.ndarray) -> dict:
        """Wald test of common-factor restriction: theta + rho*beta = 0."""
        k_wx = len(self.theta_)
        if k_wx == 0:
            return {"W_stat": 0.0, "df": 0, "p_value": 1.0}
        # Build R = theta + rho * beta[non-intercept]
        beta_non_intercept = self.beta_[-k_wx:] if len(self.beta_) >= k_wx else self.beta_
        R = self.theta_ + self.rho_ * beta_non_intercept[:k_wx]
        # Variance of R via delta method using self._cov_
        # params = [rho, beta..., theta...]
        # R_i = theta_i + rho * beta_j(i) where j(i) is the non-intercept index
        J = np.zeros((k_wx, len(self._beta_aug_) + 1))
        for i in range(k_wx):
            J[i, 0] = beta_non_intercept[i] if i < len(beta_non_intercept) else 0.0
            k_offset = 1 + self._k + i
            if k_offset < J.shape[1]:
                J[i, k_offset] = 1.0
        cov_R = J @ self._cov_ @ J.T
        try:
            W_stat = float(R @ np.linalg.inv(cov_R) @ R)
        except np.linalg.LinAlgError:
            W_stat = float("nan")
        p_value = float(chi2.sf(W_stat, k_wx))
        return {"W_stat": W_stat, "df": k_wx, "p_value": p_value}

    def summary(self) -> pd.DataFrame:
        """Return a DataFrame of parameter estimates and inference statistics.

        Returns:
            DataFrame indexed by ["rho"] + x_names + wx_names with columns:
            coef, se, t_stat, p_value.

        Raises:
            AttributeError: If fit() has not been called yet.
        """
        names = ["rho"] + self._x_names + self._wx_names
        params = np.concatenate([[self.rho_], self.beta_, self.theta_])
        return pd.DataFrame({
            "coef": params,
            "se": self.se_,
            "t_stat": self.t_stats_,
            "p_value": self.p_values_,
        }, index=names)
