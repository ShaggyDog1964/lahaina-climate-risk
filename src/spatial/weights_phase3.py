"""Phase 3 spatial weights factory: KNN, IDW, Queen contiguity."""
from __future__ import annotations
import logging
import os
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import libpysal.weights as lps_weights

logger = logging.getLogger(__name__)


class SpatialWeightsFactory:
    """Build and convert spatial weights matrices for Phase 3."""

    def build_knn(self, gdf: gpd.GeoDataFrame, k: int = 8) -> lps_weights.W:
        """KNN weights, row-standardized, projected EPSG:32604."""
        projected = gdf.to_crs("EPSG:32604")
        w = lps_weights.KNN.from_dataframe(projected, k=k)
        w.transform = "r"
        return w

    def build_idw(self, gdf: gpd.GeoDataFrame, bandwidth_km: float = 10.0) -> lps_weights.W:
        """Inverse-distance weights within bandwidth, row-standardized."""
        projected = gdf.to_crs("EPSG:32604")
        threshold_m = bandwidth_km * 1000.0
        w = lps_weights.DistanceBand.from_dataframe(projected, threshold=threshold_m, binary=False)
        # Replace with 1/d² weights
        coords = list(zip(projected.geometry.x, projected.geometry.y))
        for i in w.neighbors:
            nbrs = w.neighbors[i]
            if nbrs:
                xi, yi = coords[i]
                dists = []
                for j in nbrs:
                    xj, yj = coords[j]
                    d = max(((xi - xj) ** 2 + (yi - yj) ** 2) ** 0.5, 1.0)
                    dists.append(d)
                raw = [1.0 / (d * d) for d in dists]
                total = sum(raw)
                w.weights[i] = [r / total for r in raw]
            else:
                w.weights[i] = []
        w.transform = "r"
        return w

    def build_queen(self, gdf: gpd.GeoDataFrame) -> lps_weights.W:
        """Queen contiguity for polygon geometry; falls back to KNN(6) for points."""
        geom_type = gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else "Point"
        if geom_type in ("Polygon", "MultiPolygon"):
            w = lps_weights.Queen.from_dataframe(gdf)
        else:
            warnings.warn("Queen contiguity requires polygons; falling back to KNN(k=6).", stacklevel=2)
            w = self.build_knn(gdf, k=6)
        w.transform = "r"
        return w

    def build_all(
        self,
        gdf: gpd.GeoDataFrame,
        k: int = 8,
        bandwidth_km: float = 10.0,
    ) -> dict[str, lps_weights.W]:
        return {
            "knn": self.build_knn(gdf, k=k),
            "idw": self.build_idw(gdf, bandwidth_km=bandwidth_km),
            "queen": self.build_queen(gdf),
        }

    def to_sparse(self, w: lps_weights.W) -> sp.csr_matrix:
        """Convert libpysal W to CSR sparse matrix (n×n float64)."""
        sparse = w.to_sparse().astype(np.float64).tocsr()
        # Ensure csr_matrix (not csr_array) for scipy compatibility
        if not isinstance(sparse, sp.csr_matrix):
            sparse = sp.csr_matrix(sparse)
        return sparse

    def eigenvalues(
        self,
        W_sparse: sp.csr_matrix,
        cache_path: str | None = None,
    ) -> np.ndarray:
        """Compute real eigenvalues of W; cache to .npy if path given."""
        if cache_path and Path(cache_path).exists():
            return np.load(cache_path)
        n = W_sparse.shape[0]
        k_eigs = min(n - 2, n)
        try:
            vals, _ = spla.eigs(W_sparse.astype(complex), k=k_eigs, which="LM")
            eigs = np.real(vals)
        except Exception:
            # Dense fallback for small n
            eigs = np.linalg.eigvals(W_sparse.toarray()).real
        eigs = np.sort(eigs)
        if cache_path:
            Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
            np.save(cache_path, eigs)
        return eigs

    def persist_weights_to_postgis(
        self,
        w: lps_weights.W,
        gdf: gpd.GeoDataFrame,
        table: str,
        dsn: str | None = None,
    ) -> None:
        """Write adjacency to PostGIS if POSTGRES_DSN is set."""
        dsn = dsn or os.environ.get("POSTGRES_DSN", "")
        if not dsn:
            logger.warning("POSTGRES_DSN not set; skipping PostGIS persistence.")
            return
        try:
            import sqlalchemy as sa
            engine = sa.create_engine(dsn)
            rows = []
            for i, nbrs in w.neighbors.items():
                for j, wt in zip(nbrs, w.weights[i]):
                    rows.append({"origin_id": i, "dest_id": j, "weight": wt})
            import pandas as pd
            df = pd.DataFrame(rows)
            df.to_sql(table, engine, if_exists="replace", index=False)
            with engine.connect() as conn:
                conn.execute(sa.text(f"CREATE INDEX IF NOT EXISTS idx_{table}_origin ON {table}(origin_id)"))
                conn.commit()
        except Exception as exc:
            logger.error("PostGIS persistence failed: %s", exc)
