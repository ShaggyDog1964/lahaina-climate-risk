"""Pydantic v2 schemas for spatial results API."""
from __future__ import annotations

from pydantic import BaseModel


class LISAResult(BaseModel):
    parcel_id: str
    lat: float
    lon: float
    I_local: float
    p_value: float
    cluster_label: str


class GWRSurface(BaseModel):
    parcel_id: str
    lat: float
    lon: float
    beta_dist_to_fire: float
    beta_wui: float
    y_hat: float


class SpatialModelSummary(BaseModel):
    model_name: str
    spatial_param: float
    log_likelihood: float
    aic: float
    bic: float
    p_value: float


class ClusterCountResponse(BaseModel):
    HH: int
    LL: int
    HL: int
    LH: int
    NS: int
    total: int
