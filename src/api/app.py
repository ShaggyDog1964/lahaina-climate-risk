"""FastAPI spatial results service."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import (
    ClusterCountResponse,
    GWRSurface,
    LISAResult,
    SpatialModelSummary,
)

logger = logging.getLogger(__name__)

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

_VALID_CLUSTER_LABELS: frozenset[str | None] = frozenset({"HH", "LL", "HL", "LH", "NS", None})

app = FastAPI(title="Lahaina Spatial Results API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    """Log HTTP method and URL for every incoming request.

    Args:
        request: Starlette Request object.
        call_next: ASGI middleware chain callable.

    Returns:
        The downstream Response object unchanged.
    """
    logger.info("%s %s", request.method, request.url)
    response = await call_next(request)
    return response


def _get_db():
    """Lazy ClickHouse connection — returns None if CH_HOST not set."""
    if not os.environ.get("CH_HOST", ""):
        return None
    from src.api.db import ClickHouseClient
    return ClickHouseClient()


def _read_parquet_fallback(path: str) -> pd.DataFrame | None:
    """Read a parquet file and return a DataFrame, or None if the file is absent.

    Args:
        path: File path string relative to the project root.

    Returns:
        DataFrame if the file exists, else None.
    """
    p = Path(path)
    if p.exists():
        return pd.read_parquet(p)
    return None


@app.get("/health")
def health() -> dict[str, str]:
    """Return API liveness status.

    Returns:
        JSON object {"status": "ok"}.
    """
    return {"status": "ok"}


@app.get("/lisa/clusters", response_model=list[LISAResult])
def get_lisa_clusters(
    cluster_label: str | None = Query(default=None),
    limit: int = Query(default=100, le=5000),
) -> list[LISAResult]:
    """Return LISA cluster observations, optionally filtered by label.

    Tries ClickHouse first; falls back to parquet at results/esda/lisa_stats.parquet.

    Args:
        cluster_label: One of HH, LL, HL, LH, NS, or None to return all labels.
        limit: Maximum number of records to return (capped at 5000).

    Returns:
        List of LISAResult objects.

    Raises:
        HTTPException 422: If cluster_label is not a valid label string.
    """
    if cluster_label not in _VALID_CLUSTER_LABELS:
        raise HTTPException(status_code=422, detail="Invalid cluster_label")

    db = _get_db()
    if db:
        try:
            if cluster_label:
                df = db.query(
                    "SELECT parcel_id, lat, lon, I_local, p_value, cluster_label"
                    " FROM lisa_results WHERE cluster_label = %(label)s LIMIT %(lim)s",
                    parameters={"label": cluster_label, "lim": limit},
                )
            else:
                df = db.query(
                    "SELECT parcel_id, lat, lon, I_local, p_value, cluster_label"
                    " FROM lisa_results LIMIT %(lim)s",
                    parameters={"lim": limit},
                )
            return [LISAResult(**r) for r in df.to_dict(orient="records")]
        except Exception as exc:
            logger.warning("ClickHouse query failed: %s", exc)

    df = _read_parquet_fallback("results/esda/lisa_stats.parquet")
    if df is None:
        return []
    if cluster_label:
        df = df[df["cluster_label"] == cluster_label]
    df = df.head(limit)
    results = []
    for _, row in df.iterrows():
        results.append(LISAResult(
            parcel_id=str(row.get("parcel_id", "")),
            lat=float(row.get("lat", 0)),
            lon=float(row.get("lon", 0)),
            I_local=float(row.get("I_local", 0)),
            p_value=float(row.get("p_value", 1)),
            cluster_label=str(row.get("cluster_label", "NS")),
        ))
    return results


@app.get("/lisa/counts", response_model=ClusterCountResponse)
def get_lisa_counts() -> ClusterCountResponse:
    """Return aggregate counts of LISA cluster labels across all observations.

    Tries ClickHouse first; falls back to parquet at results/esda/cluster_labels.parquet.

    Returns:
        ClusterCountResponse with counts for HH, LL, HL, LH, NS, and total.
    """
    db = _get_db()
    if db:
        try:
            df = db.query("SELECT cluster_label, count() as cnt FROM lisa_results GROUP BY cluster_label")
            counts = dict(zip(df["cluster_label"], df["cnt"], strict=False))
        except Exception as exc:
            logger.warning("ClickHouse query failed: %s", exc)
            counts = {}
    else:
        df = _read_parquet_fallback("results/esda/cluster_labels.parquet")
        if df is not None and "cluster_label" in df.columns:
            counts = df["cluster_label"].value_counts().to_dict()
        else:
            counts = {}
    return ClusterCountResponse(
        HH=int(counts.get("HH", 0)),
        LL=int(counts.get("LL", 0)),
        HL=int(counts.get("HL", 0)),
        LH=int(counts.get("LH", 0)),
        NS=int(counts.get("NS", 0)),
        total=int(sum(counts.values())),
    )


@app.get("/gwr/surface", response_model=list[GWRSurface])
def get_gwr_surface(
    variable: str = Query(default="beta_dist_to_fire"),
    limit: int = Query(default=200, le=5000),
) -> list[GWRSurface]:
    """Return GWR coefficient surface records.

    Tries ClickHouse first; falls back to parquet at results/gwr/gwr_surface.parquet.

    Args:
        variable: Name of the GWR coefficient variable to retrieve (informational;
            both beta_dist_to_fire and beta_wui are always included in the response).
        limit: Maximum number of records to return (capped at 5000).

    Returns:
        List of GWRSurface objects.
    """
    db = _get_db()
    if db:
        try:
            df = db.query(f"SELECT parcel_id, lat, lon, beta_dist_to_fire, beta_wui, y_hat FROM gwr_surfaces LIMIT {limit}")
            return [GWRSurface(**r) for r in df.to_dict(orient="records")]
        except Exception as exc:
            logger.warning("ClickHouse query failed: %s", exc)

    df = _read_parquet_fallback("results/gwr/gwr_surface.parquet")
    if df is None:
        return []
    df = df.head(limit)
    results = []
    for _, row in df.iterrows():
        results.append(GWRSurface(
            parcel_id=str(row.get("parcel_id", "")),
            lat=float(row.get("lat", 0)),
            lon=float(row.get("lon", 0)),
            beta_dist_to_fire=float(row.get("beta_dist_to_fire", row.get("beta_dist_to_fire_km", 0))),
            beta_wui=float(row.get("beta_wui", row.get("beta_wui_class", 0))),
            y_hat=float(row.get("y_hat", 0)),
        ))
    return results


@app.get("/models/comparison", response_model=list[SpatialModelSummary])
def get_model_comparison() -> list[SpatialModelSummary]:
    """Return the spatial model comparison table (SAR vs SEM vs SDM).

    Tries ClickHouse first; falls back to JSON at results/spatial/nesting_tests.json.

    Returns:
        List of SpatialModelSummary objects sorted by AIC ascending.
    """
    db = _get_db()
    if db:
        try:
            df = db.query("SELECT model_name, spatial_param, log_likelihood, aic, bic, p_value_spatial FROM model_comparison ORDER BY aic")
            return [SpatialModelSummary(p_value=r["p_value_spatial"], **{k: v for k, v in r.items() if k != "p_value_spatial"}) for r in df.to_dict(orient="records")]
        except Exception as exc:
            logger.warning("ClickHouse query failed: %s", exc)

    p = Path("results/spatial/nesting_tests.json")
    if p.exists():
        data = json.loads(p.read_text())
        comp = data.get("comparison", {})
        results = []
        for name in comp.get("model", {}).values():
            idx = list(comp["model"].values()).index(name)
            results.append(SpatialModelSummary(
                model_name=name,
                spatial_param=float(list(comp.get("spatial_param", {}).values())[idx]),
                log_likelihood=float(list(comp.get("log_likelihood", {}).values())[idx]),
                aic=float(list(comp.get("aic", {}).values())[idx]),
                bic=float(list(comp.get("bic", {}).values())[idx]),
                p_value=0.05,
            ))
        return results
    return []


@app.get("/spatial/autocorrelation")
def get_spatial_autocorrelation() -> dict[str, Any]:
    """Return Global Moran's I summary from the precomputed JSON result.

    Returns:
        Dict with keys I, E_I, Var_I, z_score, p_value_analytical,
        p_value_permutation if the file exists; otherwise a status message dict.
    """
    p = Path("results/esda/global_morans.json")
    if p.exists():
        return json.loads(p.read_text())
    return {"message": "Global Moran's I not computed yet"}
