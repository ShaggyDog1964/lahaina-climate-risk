"""Registry for comparing spatial models."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2


class SpatialModelRegistry:
    """Register and compare spatial models by AIC/BIC/LL."""

    def __init__(self) -> None:
        self._models: dict[str, object] = {}

    def register(self, name: str, model: object) -> None:
        self._models[name] = model

    def compare(self) -> pd.DataFrame:
        rows = []
        for name, m in self._models.items():
            spatial_param = getattr(m, "rho_", getattr(m, "lambda_", float("nan")))
            rows.append({
                "model": name,
                "spatial_param": spatial_param,
                "log_likelihood": getattr(m, "log_likelihood_", float("nan")),
                "aic": getattr(m, "aic_", float("nan")),
                "bic": getattr(m, "bic_", float("nan")),
            })
        df = pd.DataFrame(rows).sort_values("aic")
        return df

    def lrt(self, model_a: str, model_b: str) -> dict:
        """LR test: H0 = model_b is correctly specified (model_a is unrestricted)."""
        ma = self._models[model_a]
        mb = self._models[model_b]
        ll_a = getattr(ma, "log_likelihood_", float("nan"))
        ll_b = getattr(mb, "log_likelihood_", float("nan"))
        lr_stat = 2.0 * (ll_a - ll_b)
        # df: difference in number of free parameters
        k_a = getattr(ma, "_k", 0) + 2  # k betas + spatial param + sigma2
        k_b = getattr(mb, "_k", 0) + 2
        df = max(abs(k_a - k_b), 1)
        p_value = float(chi2.sf(lr_stat, df))
        return {"lr_stat": float(lr_stat), "df": df, "p_value": p_value}
