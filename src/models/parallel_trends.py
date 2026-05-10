"""Parallel trends testing and event-study visualization."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def test_parallel_trends(event_study_df: pd.DataFrame) -> dict:
    """Test for parallel pre-trends by regressing pre-period ATTs on event_time.

    Args:
        event_study_df: DataFrame with columns [event_time, att, se, ci_lower, ci_upper].

    Returns:
        Dictionary with keys:
            - slope: OLS slope of pre-period ATTs on event_time
            - p_value: p-value for the slope coefficient
            - passes: True if p_value > 0.10 (fail to reject flat pre-trends)

    Raises:
        ValueError: If fewer than 2 pre-period observations are present.
    """
    pre = event_study_df[event_study_df["event_time"] < 0].copy()
    if len(pre) < 2:
        raise ValueError(
            f"Need at least 2 pre-period observations for parallel trends test; got {len(pre)}."
        )

    pre["weight"] = 1.0 / np.maximum(pre["se"] ** 2, 1e-10)

    model = smf.wls("att ~ event_time", data=pre, weights=pre["weight"])
    result = model.fit()

    slope = float(result.params["event_time"])
    p_value = float(result.pvalues["event_time"])
    passes = bool(p_value > 0.10)

    return {"slope": slope, "p_value": p_value, "passes": passes}


def plot_event_study(event_study_df: pd.DataFrame, output_path: str) -> None:
    """Plot event-study ATT coefficients with 95% CI ribbon.

    NBER working paper aesthetic: white background, minimal spines, 10pt font.

    Args:
        event_study_df: DataFrame with columns [event_time, att, ci_lower, ci_upper].
        output_path: File path for the saved figure (PDF or PNG).

    Returns:
        None. Saves figure to output_path.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    df = event_study_df.sort_values("event_time").copy()

    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)

    ax.fill_between(
        df["event_time"],
        df["ci_lower"],
        df["ci_upper"],
        alpha=0.2,
        color="#2166ac",
        label="95% CI",
    )
    ax.plot(
        df["event_time"],
        df["att"],
        color="#2166ac",
        linewidth=1.5,
        marker="o",
        markersize=3,
        label="ATT",
    )

    ax.axvline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.axhline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.7)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel("Event Time (months relative to fire)", fontsize=10)
    ax.set_ylabel("ATT (log price)", fontsize=10)
    ax.set_title("Event Study: Effect of Lahaina Fire on Property Prices", fontsize=10)
    ax.tick_params(labelsize=9)
    ax.legend(fontsize=9)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
