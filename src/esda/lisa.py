"""Local Moran's I (LISA) with permutation inference (Anselin 1995)."""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import scipy.sparse as sp


class LocalMoransI:
    """Local Moran's I statistics with HH/LL/HL/LH/NS cluster labels."""

    I_local_: np.ndarray
    p_values_: np.ndarray
    cluster_labels_: np.ndarray

    def fit(
        self,
        y: np.ndarray,
        W: sp.csr_matrix,
        n_permutations: int = 999,
        seed: int = 42,
        alpha: float = 0.05,
    ) -> LocalMoransI:
        n = len(y)
        z = (y - y.mean()) / y.std()
        Wz = np.asarray(W @ z).ravel()
        I_local = z * Wz
        self.I_local_ = I_local

        # Per-observation permutation p-values
        rng = np.random.default_rng(seed)
        counts = np.zeros(n, dtype=int)
        for _ in range(n_permutations):
            z_perm = rng.permutation(z)
            Wz_perm = np.asarray(W @ z_perm).ravel()
            I_perm_k = z * Wz_perm
            counts += (I_perm_k >= I_local).astype(int)
        p_values = (counts + 1) / (n_permutations + 1)
        self.p_values_ = p_values

        # Cluster labels (Anselin 1995 quadrant scheme)
        sig = p_values < alpha
        labels = np.where(
            ~sig, "NS",
            np.where(
                (z > 0) & (Wz > 0), "HH",
                np.where(
                    (z < 0) & (Wz < 0), "LL",
                    np.where(
                        (z > 0) & (Wz < 0), "HL",
                        "LH",
                    ),
                ),
            ),
        )
        self.cluster_labels_ = labels
        return self

    def cluster_counts(self) -> dict[str, int]:
        unique, counts = np.unique(self.cluster_labels_, return_counts=True)
        result = {str(k): int(v) for k, v in zip(unique, counts, strict=False)}
        for label in ("HH", "LL", "HL", "LH", "NS"):
            result.setdefault(label, 0)
        return result

    def to_geodataframe(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        result = gdf.copy()
        result["I_local"] = self.I_local_
        result["p_value"] = self.p_values_
        result["cluster_label"] = self.cluster_labels_
        return result
