"""Pydantic v2 schemas for spatial results API."""
from __future__ import annotations

from pydantic import BaseModel


class LISAResult(BaseModel):
    """Response schema for a single LISA cluster observation.

    Attributes:
        parcel_id: Unique parcel identifier string.
        lat: Latitude in decimal degrees (WGS 84).
        lon: Longitude in decimal degrees (WGS 84).
        I_local: Local Moran's I statistic for this observation.
        p_value: Permutation-based p-value for the local statistic.
        cluster_label: LISA quadrant label — one of HH, LL, HL, LH, NS.
    """

    parcel_id: str
    lat: float
    lon: float
    I_local: float
    p_value: float
    cluster_label: str


class GWRSurface(BaseModel):
    """Response schema for a single GWR coefficient surface observation.

    Attributes:
        parcel_id: Unique parcel identifier string.
        lat: Latitude in decimal degrees (WGS 84).
        lon: Longitude in decimal degrees (WGS 84).
        beta_dist_to_fire: Local GWR coefficient for distance-to-fire predictor.
        beta_wui: Local GWR coefficient for the WUI class predictor.
        y_hat: GWR fitted value (log price or price change) at this location.
    """

    parcel_id: str
    lat: float
    lon: float
    beta_dist_to_fire: float
    beta_wui: float
    y_hat: float


class SpatialModelSummary(BaseModel):
    """Response schema for a single entry in the spatial model comparison table.

    Attributes:
        model_name: Model identifier (e.g. "SAR", "SEM", "SDM").
        spatial_param: Estimated spatial parameter (rho for SAR/SDM, lambda for SEM).
        log_likelihood: Maximized log-likelihood value.
        aic: Akaike Information Criterion (-2*LL + 2*k).
        bic: Bayesian Information Criterion (-2*LL + k*log(n)).
        p_value: P-value for the spatial parameter (two-sided z-test).
    """

    model_name: str
    spatial_param: float
    log_likelihood: float
    aic: float
    bic: float
    p_value: float


class ClusterCountResponse(BaseModel):
    """Response schema for LISA cluster count summary.

    Attributes:
        HH: Count of High-High (spatial cluster) observations.
        LL: Count of Low-Low (spatial cluster) observations.
        HL: Count of High-Low (spatial outlier) observations.
        LH: Count of Low-High (spatial outlier) observations.
        NS: Count of Not Significant observations.
        total: Total number of observations across all labels.
    """

    HH: int
    LL: int
    HL: int
    LH: int
    NS: int
    total: int
