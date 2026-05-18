"""Spatial Error Model (SEM) via concentrated log-likelihood."""
from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.optimize import minimize_scalar
from scipy.stats import chi2, norm

from src.spatial_models.sar import _numerical_hessian


class SpatialErrorModel:
    """SEM: y = X*beta + u, u = lambda*W*u + eps, eps ~ N(0, sigma^2*I)."""

    lambda_: float
    beta_: np.ndarray
    sigma2_: float
    log_likelihood_: float
    aic_: float
    bic_: float
    se_: np.ndarray
    t_stats_: np.ndarray
    p_values_: np.ndarray

    def fit(
        self,
        y: np.ndarray,
        X: np.ndarray,
        W: sp.csr_matrix,
        eigenvalues: np.ndarray,
        x_names: list[str] | None = None,
    ) -> SpatialErrorModel:
        """Fit the SEM y = X*beta + (I - lambda*W)^{-1}*eps via concentrated ML.

        The Kelejian-Prucha (1998) concentrated log-likelihood over lambda is:
          L(lambda) = log|I - lambda*W| - (n/2) * log(sigma^2(lambda))
        where the filtered system is B*y ~ B*X with B = I - lambda*W, and
        beta(lambda) is obtained by GLS (OLS on filtered data).

        Args:
            y: Outcome vector of length n.
            X: Design matrix (n, k), including intercept if desired.
            W: Row-standardized spatial weights matrix (n x n, csr_matrix).
            eigenvalues: Real eigenvalues of W; used for the log-determinant term
                and to bound lambda within stationarity constraints.
            x_names: Column labels for X; defaults to ["x0", "x1", ...].

        Returns:
            self, with lambda_, beta_, sigma2_, log_likelihood_, aic_, bic_,
            se_, t_stats_, p_values_ populated.

        References:
            Anselin (1988), Spatial Econometrics: Methods and Models, Kluwer, ch. 6.
        """
        n, k = X.shape
        self._n = n
        self._k = k
        self._x_names = x_names or [f"x{i}" for i in range(k)]
        eigenvalues = np.real(eigenvalues).ravel()
        I_n = sp.eye(n, format="csr")

        def _conc_ll(lam: float) -> float:
            B = I_n - lam * W
            By = np.asarray(B @ y).ravel()
            BX = B @ X
            beta_lam, _, _, _ = np.linalg.lstsq(BX, By, rcond=None)
            e = By - BX @ beta_lam
            sigma2_lam = float(e @ e / n)
            if sigma2_lam <= 0:
                return 1e10
            log_det = float(np.sum(np.log(np.abs(1.0 - lam * eigenvalues))))
            return float(-(log_det - (n / 2.0) * np.log(sigma2_lam)))

        lam_min = 1.0 / np.min(eigenvalues) + 1e-4
        lam_max = 1.0 / np.max(eigenvalues) - 1e-4
        lam_min, lam_max = sorted([lam_min, lam_max])
        lam_min = max(lam_min, -0.9999)
        lam_max = min(lam_max, 0.9999)

        result = minimize_scalar(
            _conc_ll,
            bounds=(lam_min, lam_max),
            method="bounded",
            options={"xatol": 1e-6},
        )
        lam_hat = float(result.x)
        self.lambda_ = lam_hat

        B_hat = I_n - lam_hat * W
        By_hat = np.asarray(B_hat @ y).ravel()
        BX_hat = B_hat @ X
        beta_hat, _, _, _ = np.linalg.lstsq(BX_hat, By_hat, rcond=None)
        e_hat = By_hat - BX_hat @ beta_hat
        sigma2_hat = float(e_hat @ e_hat / n)

        self.beta_ = beta_hat
        self.sigma2_ = sigma2_hat

        log_det_hat = float(np.sum(np.log(np.abs(1.0 - lam_hat * eigenvalues))))
        self.log_likelihood_ = float(
            log_det_hat - (n / 2.0) * np.log(2 * np.pi * sigma2_hat) - n / 2.0
        )

        n_params = k + 2
        self.aic_ = -2.0 * self.log_likelihood_ + 2.0 * n_params
        self.bic_ = -2.0 * self.log_likelihood_ + np.log(n) * n_params

        params0 = np.concatenate([[lam_hat], beta_hat])

        def _full_ll_neg(params: np.ndarray) -> float:
            lam_p = params[0]
            beta_p = params[1:]
            if lam_p <= lam_min or lam_p >= lam_max:
                return 1e10
            B_p = I_n - lam_p * W
            e_p = np.asarray(B_p @ y).ravel() - np.asarray(B_p @ X).ravel() @ beta_p if X.shape[1] == 1 else np.asarray(B_p @ y).ravel() - (B_p @ X) @ beta_p
            s2 = max(float(e_p @ e_p / n), 1e-12)
            ld = float(np.sum(np.log(np.abs(1.0 - lam_p * eigenvalues))))
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
        return self

    def breusch_pagan(self, residuals: np.ndarray, X: np.ndarray) -> dict:
        """Spatial Breusch-Pagan test for heteroskedasticity."""
        len(residuals)
        e2 = residuals ** 2
        sigma2 = e2.mean()
        g = e2 / sigma2 - 1.0
        _, _, _, _ = np.linalg.lstsq(X, g, rcond=None)
        import statsmodels.api as sm
        from statsmodels.regression.linear_model import OLS
        exog = sm.add_constant(X) if X.shape[1] > 1 else X
        res_aux = OLS(g, exog).fit()
        bp_stat = float(res_aux.ess / 2.0)
        df = X.shape[1] - 1
        p_val = float(chi2.sf(bp_stat, df))
        return {"bp_stat": bp_stat, "df": df, "p_value": p_val}

    def summary(self) -> pd.DataFrame:
        """Return a DataFrame of parameter estimates and inference statistics.

        Returns:
            DataFrame indexed by ["lambda"] + x_names with columns:
            coef, se, t_stat, p_value, ci_lo, ci_hi.

        Raises:
            AttributeError: If fit() has not been called yet.
        """
        names = ["lambda"] + self._x_names
        params = np.concatenate([[self.lambda_], self.beta_])
        return pd.DataFrame({
            "coef": params,
            "se": self.se_,
            "t_stat": self.t_stats_,
            "p_value": self.p_values_,
            "ci_lo": params - 1.96 * self.se_,
            "ci_hi": params + 1.96 * self.se_,
        }, index=names)
