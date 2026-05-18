"""Donor pool construction for synthetic control."""

from __future__ import annotations

import logging
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


class DonorPool:
    """Screen and manage the donor pool for synthetic control.

    Args:
        panel: Zip-level panel with [zip_code, year_month, log_zhvi, ...].
        treated_zip: Zip code of treated unit.
        pre_end: Last pre-treatment year_month (inclusive), e.g. "2023-07".
    """

    def __init__(
        self,
        panel: pd.DataFrame,
        treated_zip: str = "96761",
        pre_end: str = "2023-07",
    ) -> None:
        """Initialize the DonorPool with a zip-level panel.

        Args:
            panel: DataFrame with at least columns [zip_code, year_month, log_zhvi].
                zip_code will be coerced to zero-padded 5-character str if needed.
            treated_zip: Zip code of the treated unit (Lahaina, default "96761").
            pre_end: Last pre-treatment period as "YYYY-MM" (inclusive).

        Attributes:
            panel: Copy of the input panel with zip_code coerced to str.
            treated_zip: Zero-padded treated zip code string.
            pre_end: Pre-treatment end period string.
            _donors: Cached list of donor zip codes after build(); None until then.
            _donor_panel: Subset of panel containing donors + treated; None until build().
        """
        self.panel = panel.copy()
        # Ensure zip_code is str — guard against int64 from CSV round-trip
        if (
            "zip_code" in self.panel.columns
            and not pd.api.types.is_string_dtype(self.panel["zip_code"])
        ):
            import warnings
            warnings.warn(
                f"DonorPool received zip_code as {self.panel['zip_code'].dtype}, "
                "expected str. Coercing to str. Run build_zip_panel with the latest "
                "_coerce_zip_code fix to avoid this warning.",
                stacklevel=2,
            )
            self.panel["zip_code"] = self.panel["zip_code"].astype(str).str.zfill(5)
        if isinstance(treated_zip, int):
            treated_zip = str(treated_zip).zfill(5)
        self.treated_zip = treated_zip
        self.pre_end = pre_end
        self._donors: list[str] | None = None
        self._donor_panel: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Screening methods
    # ------------------------------------------------------------------
    def filter_hawaii_zips(self) -> list[str]:
        """Return all zips except treated."""
        all_zips = self.panel["zip_code"].unique().tolist()
        return [z for z in all_zips if z != self.treated_zip]

    def screen_on_data_quality(self, max_missing_pct: float = 0.1) -> list[str]:
        """Drop zips with >max_missing_pct missing log_zhvi months."""
        pre = self.panel[self.panel["year_month"] <= self.pre_end]
        total_months = pre["year_month"].nunique()
        candidates = self.filter_hawaii_zips()

        keep = []
        for z in candidates:
            zdf = pre[pre["zip_code"] == z]
            n_obs = zdf["log_zhvi"].notna().sum()
            if total_months == 0 or (n_obs / total_months) >= (1 - max_missing_pct):
                keep.append(z)
        return keep

    def screen_on_pretrend(self, min_r2: float = 0.6) -> list[str]:
        """Keep donors with pre-period R² ≥ min_r2 AND correlation ≥ 0.5 with treated."""
        pre = self.panel[self.panel["year_month"] <= self.pre_end].copy()
        pre = pre.sort_values("year_month")

        # Treated pre-series
        treated_series = (
            pre[pre["zip_code"] == self.treated_zip]
            .set_index("year_month")["log_zhvi"]
        )
        months = treated_series.index.tolist()
        t_vals = np.arange(len(months), dtype=float).reshape(-1, 1)

        candidates = self.screen_on_data_quality()
        keep = []
        for z in candidates:
            zdf = pre[pre["zip_code"] == z].set_index("year_month")["log_zhvi"]
            zdf = zdf.reindex(months)
            if zdf.isna().any():
                continue

            y = zdf.values.reshape(-1, 1)
            reg = LinearRegression().fit(t_vals, y)
            r2 = reg.score(t_vals, y)
            if r2 < min_r2:
                continue

            corr = float(np.corrcoef(np.asarray(treated_series), np.asarray(zdf))[0, 1])
            if corr >= 0.5:
                keep.append(z)
        return keep

    def build(self, min_r2: float = 0.6) -> list[str]:
        """Run all screens and cache donor list.

        Returns:
            List of donor zip codes.
        """
        donors = self.screen_on_pretrend(min_r2=min_r2)
        self._donors = donors
        all_zips = donors + [self.treated_zip]
        self._donor_panel = self.panel[self.panel["zip_code"].isin(all_zips)].copy()
        self._persist_to_postgres()
        return donors

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def donor_panel(self) -> pd.DataFrame:
        """Return the screened panel containing donors and the treated unit.

        Returns:
            DataFrame filtered to only the zips passing all screening criteria
            plus the treated unit.

        Raises:
            RuntimeError: If build() has not been called yet.
        """
        if self._donor_panel is None:
            raise RuntimeError("Call build() first.")
        return self._donor_panel

    # ------------------------------------------------------------------
    # Optional PostGIS persistence
    # ------------------------------------------------------------------
    def _persist_to_postgres(self) -> None:
        """Write the donor panel to PostgreSQL if POSTGRES_DSN is set.

        Silently skips (with a warning log) if the connection fails or if
        POSTGRES_DSN is not configured. Never raises.
        """
        dsn = os.environ.get("POSTGRES_DSN")
        if not dsn or self._donor_panel is None:
            return
        try:
            import psycopg2  # noqa: F401
            from sqlalchemy import create_engine

            engine = create_engine(dsn)
            self._donor_panel.to_sql(
                "donor_panel", engine, if_exists="replace", index=False
            )
        except Exception as e:
            logger.warning(str(e))  # Postgres optional; never block execution
