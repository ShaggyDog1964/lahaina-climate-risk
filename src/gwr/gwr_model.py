"""Geographically Weighted Regression (GWR)."""
from __future__ import annotations

import geopandas as gpd
import numpy as np


class GeographicallyWeightedRegression:
    """GWR with bisquare or gaussian kernel.

    NEVER inverts (I-rhoW) as a dense matrix.
    Uses local WLS at each observation.
    """

    local_params_: np.ndarray   # (n, k)
    local_se_: np.ndarray       # (n, k)
    local_t_: np.ndarray        # (n, k)
    y_hat_: np.ndarray          # (n,)
    residuals_: np.ndarray      # (n,)
    hat_diag_: np.ndarray       # (n,)
    sigma2_local_: np.ndarray   # (n,)
    effective_df_: float
    aicc_: float

    def _kernel_weights(self, dists: np.ndarray, bandwidth_m: float, kernel: str) -> np.ndarray:
        """Compute kernel weights vector for distances from one observation."""
        if kernel == "bisquare":
            u = dists / bandwidth_m
            w = np.where(u < 1.0, (1.0 - u ** 2) ** 2, 0.0)
        else:  # gaussian
            w = np.exp(-0.5 * (dists / bandwidth_m) ** 2)
        return w

    def _fit_internal(
        self,
        y: np.ndarray,
        X: np.ndarray,
        dists: np.ndarray,
        bandwidth_km: float,
        kernel: str = "bisquare",
    ) -> None:
        """Core fitting routine accepting precomputed distance matrix."""
        n, k = X.shape
        bandwidth_m = bandwidth_km * 1000.0
        local_params = np.zeros((n, k))
        local_se = np.zeros((n, k))
        hat_diag = np.zeros(n)
        y_hat = np.zeros(n)
        sigma2_local = np.zeros(n)

        for i in range(n):
            w_i = self._kernel_weights(dists[i], bandwidth_m, kernel)
            W_diag = np.diag(w_i)
            XtW = X.T @ W_diag
            XtWX = XtW @ X
            XtWy = XtW @ y
            try:
                XtWX_inv = np.linalg.inv(XtWX + np.eye(k) * 1e-10)
            except np.linalg.LinAlgError:
                XtWX_inv = np.linalg.pinv(XtWX)
            beta_i = XtWX_inv @ XtWy
            local_params[i] = beta_i
            y_hat_i = float(X[i] @ beta_i)
            y_hat[i] = y_hat_i
            # Hat matrix diagonal
            h_ii = float(X[i] @ XtWX_inv @ X[i])
            hat_diag[i] = h_ii
            # Local residual variance
            e_i = y - X @ beta_i
            sigma2_i = float(np.sum(w_i * e_i ** 2) / max(np.sum(w_i) - k, 1.0))
            sigma2_local[i] = sigma2_i
            se_i = np.sqrt(np.abs(sigma2_i * np.diag(XtWX_inv)))
            local_se[i] = se_i

        self.local_params_ = local_params
        self.local_se_ = local_se
        self.local_t_ = local_params / np.where(local_se > 0, local_se, np.nan)
        self.y_hat_ = y_hat
        self.residuals_ = y - y_hat
        self.hat_diag_ = hat_diag
        self.sigma2_local_ = sigma2_local
        self.effective_df_ = float(np.sum(hat_diag))
        # AICc
        sigma2_hat = float(np.mean((y - y_hat) ** 2))
        sigma2_hat = max(sigma2_hat, 1e-12)
        tr_H = self.effective_df_
        n_float = float(n)
        denom_aicc = n_float - 2.0 - tr_H
        if abs(denom_aicc) < 1e-6:
            denom_aicc = 1e-6
        self.aicc_ = (
            2.0 * n_float * np.log(sigma2_hat)
            + n_float * np.log(2 * np.pi)
            + n_float * (n_float + tr_H) / denom_aicc
        )

    def fit(
        self,
        gdf: gpd.GeoDataFrame,
        y: np.ndarray,
        X: np.ndarray,
        bandwidth_km: float,
        kernel: str = "bisquare",
    ) -> GeographicallyWeightedRegression:
        projected = gdf.to_crs("EPSG:32604").reset_index(drop=True)
        coords = np.column_stack([projected.geometry.x, projected.geometry.y])
        from scipy.spatial.distance import cdist
        dists = cdist(coords, coords)
        self._fit_internal(y, X, dists, bandwidth_km, kernel)
        return self

    def to_geodataframe(
        self,
        gdf: gpd.GeoDataFrame,
        x_names: list[str],
    ) -> gpd.GeoDataFrame:
        result = gdf.copy().reset_index(drop=True)
        for j, name in enumerate(x_names):
            result[f"beta_{name}"] = self.local_params_[:, j]
            result[f"t_{name}"] = self.local_t_[:, j]
        result["y_hat"] = self.y_hat_
        result["residual"] = self.residuals_
        result["sigma2_local"] = self.sigma2_local_
        return result

    def coefficient_surface(self, var_name: str, x_names: list[str]) -> np.ndarray:
        idx = x_names.index(var_name)
        return self.local_params_[:, idx]
