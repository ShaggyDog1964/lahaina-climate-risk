"""Spatial weights construction: KNN and inverse-distance."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import libpysal.weights as lps_weights


def build_weights(
    gdf: gpd.GeoDataFrame,
    k: int = 8,
    output_path: str | None = None,
) -> lps_weights.W:
    """Build k-nearest-neighbor spatial weights matrix.

    Args:
        gdf: GeoDataFrame with point geometry.
        k: Number of nearest neighbors.
        output_path: If provided, save weights to this GAL file path.

    Returns:
        Row-standardized KNN weights object (w.transform == 'r').

    Raises:
        ValueError: If GeoDataFrame has fewer than k+1 observations.
    """
    if len(gdf) < k + 1:
        raise ValueError(f"Need at least {k + 1} observations for KNN with k={k}.")

    coords = list(zip(gdf.geometry.x, gdf.geometry.y, strict=False))
    w = lps_weights.KNN(coords, k=k)
    w.transform = "r"

    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        w.to_file(output_path)

    return w


def build_inverse_distance_weights(
    gdf: gpd.GeoDataFrame,
    threshold_km: float = 10.0,
    output_path: str | None = None,
) -> lps_weights.W:
    """Build inverse-distance spatial weights with a distance-band threshold.

    Args:
        gdf: GeoDataFrame with point geometry in EPSG:4326.
        threshold_km: Distance threshold in km; observations beyond this
            receive zero weight.
        output_path: If provided, save weights to this GAL file path.

    Returns:
        Row-standardized inverse-distance weights object.
    """
    projected = gdf.to_crs("EPSG:32604")
    coords = list(zip(projected.geometry.x, projected.geometry.y, strict=False))
    threshold_m = threshold_km * 1000.0

    w = lps_weights.DistanceBand(coords, threshold=threshold_m, binary=False)

    # Apply inverse-distance weighting
    for i in w.neighbors:
        neighbors = w.neighbors[i]
        if neighbors:
            xi, yi = coords[i]
            dists = []
            for j in neighbors:
                xj, yj = coords[j]
                d = ((xi - xj) ** 2 + (yi - yj) ** 2) ** 0.5
                dists.append(max(d, 1.0))
            raw_weights = [1.0 / d for d in dists]
            total = sum(raw_weights)
            w.weights[i] = [wt / total for wt in raw_weights]
        else:
            w.weights[i] = []

    w.transform = "r"

    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        w.to_file(output_path)

    return w
