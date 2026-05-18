"""GWR bandwidth selection via golden-section search on AICc."""
from __future__ import annotations

import logging
import math
import pickle
from collections.abc import Generator
from pathlib import Path

import geopandas as gpd
import numpy as np

logger = logging.getLogger(__name__)

_PHI = (math.sqrt(5) - 1) / 2.0  # golden ratio conjugate ≈ 0.618


class BandwidthSelector:
    """Select optimal GWR bandwidth via golden-section AICc minimization."""

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        y: np.ndarray,
        X: np.ndarray,
        kernel: str = "bisquare",
        criterion: str = "AICc",
        checkpoint_path: str = "data/interim/spatial/bw_checkpoint.pkl",
    ) -> None:
        """Initialize the bandwidth selector and precompute pairwise distances.

        Args:
            gdf: GeoDataFrame of observation locations (any CRS; reprojected to EPSG:32604).
            y: Outcome vector of length n.
            X: Design matrix of shape (n, k).
            kernel: Kernel type — "bisquare" or "gaussian".
            criterion: Information criterion to minimize — currently "AICc".
            checkpoint_path: Path for pickle-based search state checkpointing.

        Attributes:
            _gdf: Reprojected GeoDataFrame (EPSG:32604, index reset).
            _y: Outcome array.
            _X: Design matrix.
            _kernel: Kernel function name.
            _criterion: Selection criterion name.
            _checkpoint_path: Checkpoint file path string.
            _evaluations: List of (bandwidth_km, criterion_value) pairs evaluated so far.
            _dists: Precomputed pairwise Euclidean distance matrix (n x n, metres).
        """
        self._gdf = gdf.to_crs("EPSG:32604").reset_index(drop=True)
        self._y = y
        self._X = X
        self._kernel = kernel
        self._criterion = criterion
        self._checkpoint_path = checkpoint_path
        self._evaluations: list[tuple[float, float]] = []
        # Precompute pairwise distances
        coords = np.column_stack([self._gdf.geometry.x, self._gdf.geometry.y])
        from scipy.spatial.distance import cdist
        self._dists = cdist(coords, coords)  # n×n matrix in metres

    def _gwr_aicc(self, bandwidth_km: float) -> float:
        """Fit local WLS and return AICc."""
        from src.gwr.gwr_model import GeographicallyWeightedRegression
        model = GeographicallyWeightedRegression()
        try:
            model._fit_internal(self._y, self._X, self._dists, bandwidth_km, self._kernel)
        except Exception:
            return 1e10
        return model.aicc_

    def _golden_section_gen(
        self,
        lower: float,
        upper: float,
        tol: float = 1.0,
    ) -> Generator[tuple[int, float, float], None, float]:
        """Golden-section search generator; yields (iteration, bandwidth, aicc)."""
        iteration = 0
        while (upper - lower) > tol:
            d = _PHI * (upper - lower)
            x1 = upper - d
            x2 = lower + d
            f1 = self._gwr_aicc(x1)
            f2 = self._gwr_aicc(x2)
            self._evaluations.append((x1, f1))
            self._evaluations.append((x2, f2))
            yield iteration, (x1 + x2) / 2.0, min(f1, f2)
            if f1 < f2:
                upper = x2
            else:
                lower = x1
            iteration += 1
        return (lower + upper) / 2.0

    def checkpoint(self, state: dict, path: str | None = None) -> None:
        """Pickle the current search state to disk.

        Args:
            state: Dict to serialize (typically contains lower, upper, evaluations).
            path: Override checkpoint file path; uses self._checkpoint_path if None.
        """
        p = Path(path or self._checkpoint_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as fh:
            pickle.dump(state, fh)

    def resume_from_checkpoint(self, path: str | None = None) -> dict | None:
        """Load a previously saved search state from disk.

        Args:
            path: Override checkpoint file path; uses self._checkpoint_path if None.

        Returns:
            Unpickled state dict if the checkpoint file exists, else None.
        """
        p = Path(path or self._checkpoint_path)
        if p.exists():
            with open(p, "rb") as fh:
                return pickle.load(fh)
        return None

    def golden_section_search(
        self,
        lower: float,
        upper: float,
        tol: float = 1.0,
    ) -> float:
        """Run golden-section search with periodic checkpointing."""
        # Try to resume from checkpoint
        state = self.resume_from_checkpoint()
        if state:
            lower = state.get("lower", lower)
            upper = state.get("upper", upper)
            self._evaluations = state.get("evaluations", [])
            logger.info("Resumed bandwidth search from checkpoint: [%.2f, %.2f] km", lower, upper)

        iteration = 0
        checkpoint_every = 5

        while (upper - lower) > tol:
            d = _PHI * (upper - lower)
            x1 = upper - d
            x2 = lower + d
            f1 = self._gwr_aicc(x1)
            f2 = self._gwr_aicc(x2)
            self._evaluations.append((x1, f1))
            self._evaluations.append((x2, f2))

            if f1 < f2:
                upper = x2
            else:
                lower = x1

            iteration += 1
            if iteration % checkpoint_every == 0:
                self.checkpoint({
                    "lower": lower,
                    "upper": upper,
                    "evaluations": self._evaluations,
                })
                logger.debug("Bandwidth search checkpoint at iteration %d: [%.3f, %.3f] km", iteration, lower, upper)

        optimal = (lower + upper) / 2.0
        self.checkpoint({"lower": lower, "upper": upper, "evaluations": self._evaluations})
        return optimal

    def fit(self, lower_km: float = 1.0, upper_km: float = 50.0) -> float:
        """Select the optimal GWR bandwidth by minimizing AICc over [lower_km, upper_km].

        Resumes from a checkpoint if one exists; persists the final state afterward.

        Args:
            lower_km: Lower bound of the search interval in kilometres.
            upper_km: Upper bound of the search interval in kilometres.

        Returns:
            Optimal bandwidth in kilometres (midpoint of converged golden-section interval).
        """
        return self.golden_section_search(lower_km, upper_km)
