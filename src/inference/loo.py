"""Leave-one-out robustness diagnostics for synthetic control."""

from __future__ import annotations

import numpy as np

from src.inference.rmspe import gap_series, pre_rmspe


class LeaveOneOutDiagnostic:
    """Leave-one-out robustness check for ADH SCM."""

    def __init__(self) -> None:
        self._result: dict | None = None
        self._base_gap: np.ndarray | None = None

    def run(
        self,
        scm,
        X0: np.ndarray,
        X1: np.ndarray,
        Y0_pre: np.ndarray,
        Y1_pre: np.ndarray,
        Y0_all: np.ndarray,
        Y1_all: np.ndarray,
        donor_names: list[str],
    ) -> dict:
        """Refit SCM dropping each high-weight donor.

        Args:
            scm: Fitted ADHSyntheticControl (or compatible) object.
            X0: Donor covariate matrix (k, J).
            X1: Treated covariate vector (k,).
            Y0_pre: Donor pre-period outcomes (T0, J).
            Y1_pre: Treated pre-period outcomes (T0,).
            Y0_all: Donor all-period outcomes (T, J).
            Y1_all: Treated all-period outcomes (T,).
            donor_names: Donor zip labels.

        Returns:
            Dict with keys loo_gaps, base_gap, pre_rmspes.
        """
        from src.scm.adh_scm import ADHSyntheticControl

        base_synth = Y0_all @ scm.w_
        self._base_gap = gap_series(Y1_all, base_synth)

        loo_gaps: dict[str, np.ndarray] = {}
        pre_rmspes: dict[str, float] = {}

        active = [(j, name) for j, name in enumerate(donor_names) if scm.w_[j] > 0.05]
        if not active:
            import logging
            logging.getLogger(__name__).warning(
                "No donors with weight > 0.05. LOO diagnostic not informative "
                "(all weights near zero). Returning empty result."
            )
            self._result = {
                "loo_gaps": {},
                "base_gap": self._base_gap,
                "pre_rmspes": {},
            }
            return self._result

        for j, name in active:

            mask = np.ones(len(donor_names), dtype=bool)
            mask[j] = False

            X0_loo = X0[:, mask]
            Y0_pre_loo = Y0_pre[:, mask]
            Y0_all_loo = Y0_all[:, mask]

            try:
                loo_model = ADHSyntheticControl()
                loo_model.fit(X0_loo, X1, Y0_pre_loo, Y1_pre)
                synth_loo = Y0_all_loo @ loo_model.w_
                loo_gaps[name] = gap_series(Y1_all, synth_loo)
                pre_rmspes[name] = pre_rmspe(Y1_pre, Y0_pre_loo @ loo_model.w_)
            except Exception:
                pass

        self._result = {
            "loo_gaps": loo_gaps,
            "base_gap": self._base_gap,
            "pre_rmspes": pre_rmspes,
        }
        return self._result

    def stability_score(self) -> float:
        """Max absolute deviation of any LOO gap from base gap (post-period)."""
        if self._result is None or self._base_gap is None:
            raise RuntimeError("Call run() first.")
        base = self._base_gap
        loo_gaps = self._result["loo_gaps"]
        if not loo_gaps:
            return 0.0
        max_dev = 0.0
        for gap in loo_gaps.values():
            n = min(len(gap), len(base))
            dev = float(np.max(np.abs(gap[:n] - base[:n])))
            max_dev = max(max_dev, dev)
        return max_dev
