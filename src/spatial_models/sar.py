"""Spatial Autoregressive (Lag) Model via concentrated log-likelihood."""
from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import minimize_scalar
from scipy.stats import norm


class SpatialLagModel:
    """SAR: y = rho*Wy + X*beta + eps, eps ~ N(0, sigma^2*I).

    Estimated by concentrated ML over rho.
    """

    rho_: float
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
    ) -> SpatialLagModel:
        n, k = X.shape
        if np.std(y) < 1e-12:
            raise ValueError("y has no variation; SAR model cannot be estimated on a constant outcome.")
        self._n = n
        self._k = k
        self._x_names = x_names or [f"x{i}" for i in range(k)]
        eigenvalues = np.real(eigenvalues).ravel()
        I_n = sp.eye(n, format="csr")

        def _conc_ll(rho: float) -> float:
            A = I_n - rho * W
            Ay = np.asarray(A @ y).ravel()
            beta_rho, _, _, _ = np.linalg.lstsq(X, Ay, rcond=None)
            e = Ay - X @ beta_rho
            sigma2_rho = float(e @ e / n)
            if sigma2_rho <= 0:
                return 1e10
            log_det = float(np.sum(np.log(np.abs(1.0 - rho * eigenvalues))))
            return float(-(log_det - (n / 2.0) * np.log(sigma2_rho)))

        # Bounds from eigenvalues
        rho_min = 1.0 / np.min(eigenvalues) + 1e-4
        rho_max = 1.0 / np.max(eigenvalues) - 1e-4
        rho_min, rho_max = sorted([rho_min, rho_max])
        rho_min = max(rho_min, -0.9999)
        rho_max = min(rho_max, 0.9999)

        result = minimize_scalar(
            _conc_ll,
            bounds=(rho_min, rho_max),
            method="bounded",
            options={"xatol": 1e-6},
        )
        rho_hat = float(result.x)
        self.rho_ = rho_hat

        A_hat = I_n - rho_hat * W
        Ay_hat = np.asarray(A_hat @ y).ravel()
        beta_hat, _, _, _ = np.linalg.lstsq(X, Ay_hat, rcond=None)
        e_hat = Ay_hat - X @ beta_hat
        sigma2_hat = float(e_hat @ e_hat / n)

        self.beta_ = beta_hat
        self.sigma2_ = sigma2_hat

        log_det_hat = float(np.sum(np.log(np.abs(1.0 - rho_hat * eigenvalues))))
        self.log_likelihood_ = float(
            log_det_hat - (n / 2.0) * np.log(2 * np.pi * sigma2_hat) - n / 2.0
        )

        n_params = k + 2  # beta (k) + rho + sigma^2
        self.aic_ = -2.0 * self.log_likelihood_ + 2.0 * n_params
        self.bic_ = -2.0 * self.log_likelihood_ + np.log(n) * n_params

        # Numerical Hessian for [rho, beta] standard errors
        params0 = np.concatenate([[rho_hat], beta_hat])

        def _full_ll_neg(params: np.ndarray) -> float:
            rho_p = params[0]
            beta_p = params[1:]
            if rho_p <= rho_min or rho_p >= rho_max:
                return 1e10
            A_p = I_n - rho_p * W
            e_p = np.asarray(A_p @ y).ravel() - X @ beta_p
            s2 = max(float(e_p @ e_p / n), 1e-12)
            ld = float(np.sum(np.log(np.abs(1.0 - rho_p * eigenvalues))))
            return float(-(ld - (n / 2.0) * np.log(2 * np.pi * s2) - n / 2.0))

        eps_h = 1e-5
        H = _numerical_hessian(_full_ll_neg, params0, eps_h)
        try:
            cov = np.linalg.inv(-H)
            diag = np.diag(cov)
            se = np.sqrt(np.abs(diag))
        except np.linalg.LinAlgError:
            se = np.full(len(params0), np.nan)

        self.se_ = se
        self.t_stats_ = params0 / np.where(se > 0, se, np.nan)
        self.p_values_ = 2.0 * norm.sf(np.abs(self.t_stats_))
        return self

    def predict(self, X: np.ndarray, W: sp.csr_matrix, y: np.ndarray) -> np.ndarray:
        n = X.shape[0]
        A = sp.eye(n, format="csr") - self.rho_ * W
        rhs = X @ self.beta_
        return np.asarray(spla.spsolve(A, rhs)).ravel()

    def residuals(self, y: np.ndarray, X: np.ndarray, W: sp.csr_matrix) -> np.ndarray:
        return np.asarray(y - self.predict(X, W, y))

    def summary(self) -> pd.DataFrame:
        names = ["rho"] + self._x_names
        params = np.concatenate([[self.rho_], self.beta_])
        data = {
            "coef": params,
            "se": self.se_,
            "t_stat": self.t_stats_,
            "p_value": self.p_values_,
            "ci_lo": params - 1.96 * self.se_,
            "ci_hi": params + 1.96 * self.se_,
        }
        return pd.DataFrame(data, index=names)


def _numerical_hessian(f, x0: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    n = len(x0)
    H = np.zeros((n, n))
    f0 = f(x0)
    for i in range(n):
        for j in range(i, n):
            ei = np.zeros(n)
            ei[i] = eps
            ej = np.zeros(n)
            ej[j] = eps
            if i == j:
                H[i, i] = (f(x0 + ei) - 2 * f0 + f(x0 - ei)) / eps**2
            else:
                H[i, j] = H[j, i] = (
                    f(x0 + ei + ej) - f(x0 + ei - ej)
                    - f(x0 - ei + ej) + f(x0 - ei - ej)
                ) / (4 * eps**2)
    return H
