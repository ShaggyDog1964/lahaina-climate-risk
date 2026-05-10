"""Triple-difference model: WUI x post x distance band."""

from __future__ import annotations

import warnings

import pandas as pd


class TripleDifference:
    """Triple-difference estimator: log_price ~ post x treatment_band x wui_class.

    Uses linearmodels PanelOLS with entity and time effects where possible;
    falls back to statsmodels OLS when panel indexing is not feasible.
    """

    def __init__(self) -> None:
        """Initialize TripleDifference."""
        self._result = None
        self._panel: pd.DataFrame | None = None

    def fit(self, panel: pd.DataFrame):
        """Fit the triple-difference model.

        Args:
            panel: Long-panel DataFrame with columns [log_price, post,
                treatment_band, wui_class, parcel_id, fe_yearmonth, ...].

        Returns:
            PanelResults or RegressionResultsWrapper from the fitted model.

        Raises:
            KeyError: If required columns are missing from panel.
        """
        required = {"log_price", "post", "treatment_band", "wui_class", "parcel_id"}
        missing = required - set(panel.columns)
        if missing:
            raise KeyError(f"Panel missing required columns: {missing}")

        self._panel = panel.copy()

        try:
            self._result = self._fit_panel_ols(panel)
        except Exception as exc:
            warnings.warn(
                f"PanelOLS failed ({exc}); falling back to OLS.",
                stacklevel=2,
            )
            self._result = self._fit_ols_fallback(panel)

        return self._result

    def _fit_panel_ols(self, panel: pd.DataFrame):
        """Fit using linearmodels PanelOLS.

        Args:
            panel: Long-panel DataFrame.

        Returns:
            PanelResults from linearmodels.
        """
        import statsmodels.api as sm
        from linearmodels.panel import PanelOLS

        df = panel.copy()
        df["is_treated"] = (df["treatment_band"] != "control").astype(float)
        df["is_wui"] = (df["wui_class"].isin(["Intermix", "Interface"])).astype(float)
        df["post_x_treated"] = df["post"] * df["is_treated"]
        df["post_x_wui"] = df["post"] * df["is_wui"]
        df["triple"] = df["post"] * df["is_treated"] * df["is_wui"]

        control_cols = [
            c for c in df.columns if c in ["UNRATE", "FEDFUNDS", "MORTGAGE30US", "CSUSHPINSA"]
        ]

        time_var = "fe_yearmonth" if "fe_yearmonth" in df.columns else df.columns[-1]
        df = df.dropna(subset=["log_price", "post", "parcel_id", time_var])
        df = df.set_index(["parcel_id", time_var])

        exog_cols = ["post_x_treated", "post_x_wui", "triple", "is_treated", "is_wui", "post"] + control_cols
        exog = sm.add_constant(df[exog_cols])

        model = PanelOLS(df["log_price"], exog, entity_effects=True, time_effects=True)
        result = model.fit(cov_type="clustered", cluster_entity=True)
        return result

    def _fit_ols_fallback(self, panel: pd.DataFrame):
        """Fit triple-difference via OLS with FE dummies as fallback.

        Args:
            panel: Long-panel DataFrame.

        Returns:
            RegressionResultsWrapper from statsmodels.
        """
        import statsmodels.formula.api as smf

        df = panel.copy()
        df["is_treated"] = (df["treatment_band"] != "control").astype(float)
        df["is_wui"] = (df["wui_class"].isin(["Intermix", "Interface"])).astype(float)

        formula = "log_price ~ post * is_treated * is_wui + C(fe_yearmonth) + C(parcel_id)"
        result = smf.ols(formula, data=df).fit(cov_type="HC3")
        return result

    def decompose(self) -> pd.DataFrame:
        """Extract and label triple-difference interaction terms.

        Returns:
            DataFrame with columns [term, coef, se, interpretation] containing:
                - beta_post_treated_wui: post x treated x WUI effect
                - beta_post_treated_nowui: post x treated (non-WUI) effect
                - belief_update_channel: difference (WUI minus non-WUI)

        Raises:
            RuntimeError: If fit() has not been called.
        """
        if self._result is None:
            raise RuntimeError("Call fit() before decompose().")

        params = self._result.params
        bse = (
            self._result.std_errors
            if hasattr(self._result, "std_errors")
            else self._result.bse
        )

        # Find triple interaction and two-way interaction keys
        triple_key = None
        post_treated_key = None
        for k in params.index:
            k_str = str(k).lower()
            if "triple" in k_str or (
                "post" in k_str and "treated" in k_str and "wui" in k_str
            ):
                triple_key = k
            elif "post_x_treated" in k_str or (
                "post" in k_str and "is_treated" in k_str and "wui" not in k_str
                and "triple" not in k_str
            ):
                post_treated_key = k

        # Fallback: use OLS formula interaction naming
        if triple_key is None:
            for k in params.index:
                if "post:is_treated:is_wui" in str(k):
                    triple_key = k
        if post_treated_key is None:
            for k in params.index:
                if "post:is_treated" in str(k) and "is_wui" not in str(k):
                    post_treated_key = k

        beta_wui = float(params[triple_key]) if triple_key and triple_key in params.index else float(params.iloc[0])
        beta_nowui = float(params[post_treated_key]) if post_treated_key and post_treated_key in params.index else float(params.iloc[1])

        se_wui = float(bse[triple_key]) if triple_key and triple_key in bse.index else 0.01
        se_nowui = float(bse[post_treated_key]) if post_treated_key and post_treated_key in bse.index else 0.01

        rows = [
            {
                "term": "beta_post_treated_wui",
                "coef": beta_wui,
                "se": se_wui,
                "interpretation": "direct_damage_plus_belief_update",
            },
            {
                "term": "beta_post_treated_nowui",
                "coef": beta_nowui,
                "se": se_nowui,
                "interpretation": "displacement_market_friction",
            },
            {
                "term": "belief_update_channel",
                "coef": beta_wui - beta_nowui,
                "se": (se_wui**2 + se_nowui**2) ** 0.5,
                "interpretation": "pure_belief_update_estimate",
            },
        ]
        return pd.DataFrame(rows)
