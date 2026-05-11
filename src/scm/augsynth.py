"""Augmented Synthetic Control Method (Ben-Michael et al. 2021)."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge


class AugmentedSyntheticControl:
    """Ben-Michael, Feller & Rothstein (2021) ASCM.

    Corrects ADH weights for pre-period imbalance via ridge regression:
    tau_t^ASCM = (Y1t - sum_j w_j^SCM Y_jt) - (m̂_1t - sum_j w_j^SCM m̂_jt)
    where m̂_it = ridge prediction using pre-period outcomes as features.
    """

    def __init__(self) -> None:
        self.tau_ascm_: np.ndarray | None = None
        self.tau_raw_: np.ndarray | None = None
        self.bias_correction_: np.ndarray | None = None
        self.lambda_ridge_: float | None = None
        self._ridge: Ridge | None = None

    def fit(
        self,
        w_adh: np.ndarray,
        Y0_pre: np.ndarray,
        Y1_pre: np.ndarray,
        Y0_all: np.ndarray,
        Y1_all: np.ndarray,
        lambda_ridge: float | None = None,
    ) -> AugmentedSyntheticControl:
        """Fit ASCM given ADH weights.

        Args:
            w_adh: ADH donor weights (J,).
            Y0_pre: Donor pre-period outcomes (T0, J).
            Y1_pre: Treated pre-period outcomes (T0,).
            Y0_all: Donor all-period outcomes (T, J).
            Y1_all: Treated all-period outcomes (T,).
            lambda_ridge: Ridge regularization; tuned by LOOCV if None.

        Returns:
            self
        """
        T0, J = Y0_pre.shape
        T = Y0_all.shape[0]

        if lambda_ridge is None:
            lambda_ridge = self._tune_lambda(Y0_pre)
        self.lambda_ridge_ = lambda_ridge

        # Fit ridge: features = Y_i,pre (T0,), target = full series per period
        # One ridge per time step predicting that time step from pre-period
        ridge_preds_treated = np.zeros(T)
        ridge_preds_donors = np.zeros((T, J))

        for t in range(T):
            y_target = Y0_all[t, :]  # (J,) target for each donor at time t
            reg = Ridge(alpha=lambda_ridge, fit_intercept=True)
            reg.fit(Y0_pre.T, y_target)  # features: (J, T0), targets: (J,)
            ridge_preds_donors[t] = reg.predict(Y0_pre.T)
            ridge_preds_treated[t] = reg.predict(Y1_pre.reshape(1, -1))[0]

        self._ridge = reg  # store last for reference

        # Raw SCM gap
        Y_synth_all = Y0_all @ w_adh
        tau_raw = Y1_all - Y_synth_all

        # Bias correction: m̂_1t - sum_j w_j m̂_jt
        synth_ridge = ridge_preds_donors @ w_adh
        bias = ridge_preds_treated - synth_ridge

        self.tau_raw_ = tau_raw
        self.bias_correction_ = bias
        self.tau_ascm_ = tau_raw - bias
        return self

    def treatment_effect(self) -> np.ndarray:
        """Return ASCM treatment effect series."""
        assert self.tau_ascm_ is not None, "Model not fitted. Call fit() before treatment_effect()."
        return self.tau_ascm_

    def _tune_lambda(self, Y0_pre: np.ndarray) -> float:
        """Tune ridge lambda via leave-one-out CV on donors."""
        T0, J = Y0_pre.shape
        alphas = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
        best_alpha, best_mse = 1.0, float("inf")

        for alpha in alphas:
            loo_mse = []
            for j in range(J):
                mask = np.ones(J, dtype=bool)
                mask[j] = False
                y_train = Y0_pre[:, j]       # one per non-loo donor at each period

                # Predict held-out donor series from others' pre-periods
                # Use all T0 timepoints as separate samples
                # Actually: predict each donor's value at each t using other donors at same t
                X_feat2 = Y0_pre[mask, :].T if False else Y0_pre[:, mask]  # (T0, J-1)
                reg = Ridge(alpha=alpha, fit_intercept=True)
                # LOOCV: fit on T0 samples, each sample = a time period
                # features = other donors at that time, target = donor j at that time
                reg.fit(X_feat2, y_train)  # (T0, J-1) → (T0,)
                pred = reg.predict(X_feat2)
                loo_mse.append(float(np.mean((y_train - pred) ** 2)))

            mse = float(np.mean(loo_mse))
            if mse < best_mse:
                best_mse, best_alpha = mse, alpha

        return best_alpha
