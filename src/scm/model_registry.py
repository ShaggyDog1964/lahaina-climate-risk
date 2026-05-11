"""Model registry for SCM variants."""

from __future__ import annotations

import pandas as pd


class ModelRegistry:
    """Dict-like container mapping model name → fitted SCM + metadata."""

    def __init__(self) -> None:
        self._models: dict[str, dict] = {}

    def register(self, name: str, model: object, meta: dict) -> None:
        """Register a fitted model.

        Args:
            name: Model identifier (e.g. "ADH", "GSynth", "ASCM").
            model: Fitted SCM object.
            meta: Arbitrary metadata dict.
        """
        self._models[name] = {"model": model, "meta": meta}

    def get(self, name: str) -> dict:
        """Return registered entry by name."""
        return self._models[name]

    def compare_rmspe(self) -> pd.DataFrame:
        """Return DataFrame comparing pre-RMSPE, post-RMSPE, ratio across models."""
        rows = []
        for name, entry in self._models.items():
            m = entry["model"]
            pre = getattr(m, "pre_rmspe_", None)
            post = getattr(m, "post_rmspe_", None)
            ratio = (post / pre) if (pre and post and pre > 0) else None
            rows.append(
                {
                    "model": name,
                    "pre_rmspe": pre,
                    "post_rmspe": post,
                    "rmspe_ratio": ratio,
                }
            )
        return pd.DataFrame(rows)

    def __len__(self) -> int:
        return len(self._models)

    def __contains__(self, name: str) -> bool:
        return name in self._models
