"""In-space placebo inference for synthetic control."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from src.inference.rmspe import gap_series, post_rmspe, pre_rmspe, rmspe_ratio

logger = logging.getLogger(__name__)


class InSpacePlacebo:
    """In-space placebo test: designate each donor as pseudo-treated.

    Args:
        scm_class: Class with .fit(X0, X1, Y0_pre, Y1_pre) interface.
        donor_pool: Fitted DonorPool object.
        covariate_matrix_fn: Callable returning (X0, X1, covariate_names).
    """

    def __init__(self, scm_class, donor_pool, covariate_matrix_fn) -> None:
        """Initialize the in-space placebo runner.

        Args:
            scm_class: SCM class with a .fit(X0, X1, Y0_pre, Y1_pre) interface
                (e.g. ADHSyntheticControl).
            donor_pool: Fitted DonorPool object providing the panel and metadata.
            covariate_matrix_fn: Callable returning (X0, X1, covariate_names) for
                a given DonorPool.

        Attributes:
            scm_class: The SCM class to instantiate for each placebo run.
            donor_pool: The fitted DonorPool object.
            covariate_matrix_fn: Covariate builder callable.
            placebo_df: DataFrame of placebo results (None until run() is called).
            _treated_pre_rmspe: Pre-RMSPE of the actual treated unit (None until set).
        """
        self.scm_class = scm_class
        self.donor_pool = donor_pool
        self.covariate_matrix_fn = covariate_matrix_fn
        self.placebo_df: pd.DataFrame | None = None
        self._treated_pre_rmspe: float | None = None

    def run(self, n_jobs: int = -1) -> pd.DataFrame:
        """Run in-space placebo for each donor zip.

        Args:
            n_jobs: Number of parallel jobs (-1 = all cores).

        Returns:
            DataFrame with [zip_code, pre_rmspe, post_rmspe, rmspe_ratio, gap_*].
        """
        panel = self.donor_pool.donor_panel
        treated_zip = self.donor_pool.treated_zip
        pre_end = self.donor_pool.pre_end

        all_zips = panel["zip_code"].unique().tolist()
        donor_zips = [z for z in all_zips if z != treated_zip]

        if len(donor_zips) < 2:
            raise ValueError(
                f"Need >= 2 donors for placebo test, got {len(donor_zips)}. "
                "Ensure DonorPool.build() has run and returned enough donors."
            )

        results = Parallel(n_jobs=n_jobs, prefer="threads")(
            delayed(self._run_one)(z, panel, pre_end) for z in donor_zips
        )
        results = [r for r in results if r is not None]

        self.placebo_df = pd.DataFrame(results)
        self._n_placebos_full_ = len(self.placebo_df)
        return self.placebo_df

    def _run_one(
        self, pseudo_treated: str, panel: pd.DataFrame, pre_end: str
    ) -> dict | None:
        """Fit SCM with pseudo_treated as treated unit."""
        try:
            other_donors = [
                z for z in panel["zip_code"].unique() if z != pseudo_treated
            ]
            if len(other_donors) < 2:
                return None

            pre = panel[panel["year_month"] <= pre_end].copy()
            post = panel[panel["year_month"] > pre_end].copy()
            months_pre = sorted(pre["year_month"].unique())
            months_post = sorted(post["year_month"].unique())

            def _series(df: pd.DataFrame, zip_code: str, months: list) -> np.ndarray:
                s = df[df["zip_code"] == zip_code].set_index("year_month")["log_zhvi"]
                return np.asarray(s.reindex(months).ffill().bfill()).ravel()

            Y1_pre = _series(pre, pseudo_treated, months_pre)
            Y0_pre = np.column_stack(
                [_series(pre, z, months_pre) for z in other_donors]
            )
            Y1_post = _series(post, pseudo_treated, months_post) if months_post else np.array([])
            Y0_post = (
                np.column_stack([_series(post, z, months_post) for z in other_donors])
                if months_post
                else np.empty((0, len(other_donors)))
            )

            # Simple covariate matrix: pre-period mean per zip
            X1 = np.array([float(np.mean(Y1_pre))])
            X0 = np.array([[float(np.mean(Y0_pre[:, j]))] for j in range(len(other_donors))]).T

            model = self.scm_class()
            model.fit(X0, X1, Y0_pre, Y1_pre)

            pre_r = pre_rmspe(Y1_pre, Y0_pre @ model.w_)

            post_r = post_rmspe(Y1_post, Y0_post @ model.w_) if len(Y1_post) > 0 else pre_r

            ratio = rmspe_ratio(pre_r, post_r)
            gap_pre = gap_series(Y1_pre, Y0_pre @ model.w_)
            gap_post = gap_series(Y1_post, Y0_post @ model.w_) if len(Y1_post) > 0 else np.array([])
            gap_all = np.concatenate([gap_pre, gap_post])

            row: dict = {
                "zip_code": pseudo_treated,
                "pre_rmspe": pre_r,
                "post_rmspe": post_r,
                "rmspe_ratio": ratio,
            }
            for i, g in enumerate(gap_all):
                row[f"gap_t{i}"] = float(g)

            return row
        except Exception as e:
            logger.warning(str(e))
            return None

    def p_value(self, treated_ratio: float) -> float:
        """Fraction of placebos with RMSPE ratio ≥ treated ratio."""
        if self.placebo_df is None or len(self.placebo_df) == 0:
            return 1.0
        rank = (self.placebo_df["rmspe_ratio"] >= treated_ratio).sum()
        return float(rank) / len(self.placebo_df)

    def p_values(self) -> dict:
        """Return dict with p_full and p_trimmed (if discard_poor_fit was called).

        Returns:
            Dict with keys: p_full, p_trimmed, n_placebos_full, n_placebos_trimmed.
        """
        if self.placebo_df is None:
            raise RuntimeError("Call run() first.")
        p_full = self.p_value(getattr(self, "_treated_ratio_cache_", 0.0))
        return {
            "p_full": getattr(self, "_p_value_full_", p_full),
            "p_trimmed": getattr(self, "_p_value_trimmed_", None),
            "n_placebos_full": getattr(self, "_n_placebos_full_", len(self.placebo_df)),
            "n_placebos_trimmed": getattr(self, "_n_placebos_trimmed_", None),
        }

    def discard_poor_fit(
        self, max_pre_rmspe_multiple: float = 2.0
    ) -> InSpacePlacebo:
        """Drop placebos with pre-RMSPE > multiple × treated pre-RMSPE."""
        if self.placebo_df is None:
            raise RuntimeError("Call run() first.")
        if self._treated_pre_rmspe is None:
            return self
        threshold = max_pre_rmspe_multiple * self._treated_pre_rmspe
        self.placebo_df = self.placebo_df[
            self.placebo_df["pre_rmspe"] <= threshold
        ].copy()
        return self

    def set_treated_pre_rmspe(self, value: float) -> None:
        """Set the treated unit's pre-RMSPE for discard_poor_fit."""
        self._treated_pre_rmspe = value
