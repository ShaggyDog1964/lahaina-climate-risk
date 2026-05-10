"""Hedonic pricing model for Lahaina parcel transactions."""

from __future__ import annotations

import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.regression.linear_model as sm_lm


class HedonicModel:
    """OLS hedonic price model with census-block and year-month fixed effects.

    Specification:
        log_price ~ structure_sqft + land_area_sqft + year_built
                  + C(zoning) + C(fe_block) + C(fe_yearmonth)

    Uses HC3 heteroskedasticity-robust standard errors.
    """

    def __init__(self) -> None:
        """Initialize HedonicModel."""
        self._result: sm_lm.RegressionResultsWrapper | None = None

    def fit(self, panel: pd.DataFrame) -> sm_lm.RegressionResultsWrapper:
        """Fit the hedonic OLS model with HC3 standard errors.

        Args:
            panel: Long-panel DataFrame with columns [log_price, structure_sqft,
                land_area_sqft, year_built, zoning, fe_block, fe_yearmonth].

        Returns:
            Fitted statsmodels RegressionResultsWrapper.

        Raises:
            KeyError: If required columns are missing from panel.
        """
        required = {
            "log_price",
            "structure_sqft",
            "land_area_sqft",
            "year_built",
            "zoning",
            "fe_block",
            "fe_yearmonth",
        }
        missing = required - set(panel.columns)
        if missing:
            raise KeyError(f"Panel missing required columns: {missing}")

        formula = (
            "log_price ~ structure_sqft + land_area_sqft + year_built"
            " + C(zoning) + C(fe_block) + C(fe_yearmonth)"
        )
        model = smf.ols(formula=formula, data=panel)
        self._result = model.fit(cov_type="HC3")
        return self._result

    def summary_table(self) -> pd.DataFrame:
        """Return a tidy summary DataFrame of estimated coefficients.

        Returns:
            DataFrame with columns [coef, se, t, p, ci_lower_95, ci_upper_95].

        Raises:
            RuntimeError: If fit() has not been called.
        """
        if self._result is None:
            raise RuntimeError("Call fit() before summary_table().")

        ci = self._result.conf_int(alpha=0.05)
        table = pd.DataFrame(
            {
                "coef": self._result.params,
                "se": self._result.bse,
                "t": self._result.tvalues,
                "p": self._result.pvalues,
                "ci_lower_95": ci[0],
                "ci_upper_95": ci[1],
            }
        )
        return table
