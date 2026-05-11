"""Publication-quality SCM visualizations."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }
)

TREATED_COLOR = "#185FA5"
SYNTH_COLOR = "#888780"
FIRE_LINE_COLOR = "#CC2529"


def plot_scm_path(
    Y1_all: np.ndarray,
    Y_synth_all: np.ndarray,
    time_periods: list[str],
    fire_date: str,
    output_path: str | Path,
    title: str = "Lahaina vs. synthetic Lahaina",
    ax: plt.Axes | None = None,
) -> None:
    """Plot treated and synthetic paths with shaded gap.

    Args:
        Y1_all: Treated unit outcome series (T,).
        Y_synth_all: Synthetic control series (T,).
        time_periods: List of year_month strings length T.
        fire_date: Year-month of fire (e.g. "2023-08").
        output_path: File path (PDF + PNG saved).
        title: Plot title.
        ax: Existing axes; created if None.
    """
    created = ax is None
    if created:
        fig, ax = plt.subplots(figsize=(8, 4))

    x = np.arange(len(time_periods))
    ax.plot(x, Y1_all, color=TREATED_COLOR, linewidth=1.8, label="Lahaina (96761)")
    ax.plot(x, Y_synth_all, color=SYNTH_COLOR, linewidth=1.4, linestyle="--", label="Synthetic Lahaina")

    # Shade gap
    ax.fill_between(x, Y1_all, Y_synth_all, alpha=0.15, color=FIRE_LINE_COLOR, label="_nolegend_")

    # Fire date line
    if fire_date in time_periods:
        fire_x = time_periods.index(fire_date)
        ax.axvline(fire_x, color=FIRE_LINE_COLOR, linestyle="--", linewidth=1.2, label="Fire (Aug 2023)")

    _format_x_axis(ax, time_periods)
    ax.set_ylabel("Log ZHVI")
    ax.set_title(title)
    ax.legend(frameon=False, fontsize=9)

    if created:
        _save(fig, output_path)


def plot_placebo_distribution(
    placebo_df: pd.DataFrame,
    treated_gap_series: np.ndarray,
    time_periods: list[str],
    fire_date: str,
    output_path: str | Path,
    ax: plt.Axes | None = None,
) -> None:
    """Plot gap series for all placebos + treated unit.

    Args:
        placebo_df: DataFrame from InSpacePlacebo.run().
        treated_gap_series: Treated unit gap (T,).
        time_periods: Year-month list length T.
        fire_date: Fire year-month string.
        output_path: Output file path.
        ax: Existing axes.
    """
    created = ax is None
    if created:
        fig, ax = plt.subplots(figsize=(8, 4))

    gap_cols = [c for c in placebo_df.columns if c.startswith("gap_t")]
    x = np.arange(len(time_periods))

    for _, row in placebo_df.iterrows():
        vals = row[gap_cols].values.astype(float)
        n = min(len(vals), len(x))
        ax.plot(x[:n], vals[:n], color="gray", linewidth=0.5, alpha=0.35)

    ax.plot(x, treated_gap_series, color=TREATED_COLOR, linewidth=2.0, label="Lahaina")

    if fire_date in time_periods:
        fire_x = time_periods.index(fire_date)
        ax.axvline(fire_x, color=FIRE_LINE_COLOR, linestyle="--", linewidth=1.2)

    ax.axhline(0, color="black", linewidth=0.6, linestyle=":")
    _format_x_axis(ax, time_periods)
    ax.set_ylabel("Gap (log ZHVI)")
    ax.set_title("In-space placebo distribution")
    ax.legend(frameon=False, fontsize=9)

    if created:
        _save(fig, output_path)


def plot_loo(
    base_gap: np.ndarray,
    loo_gaps: dict[str, np.ndarray],
    time_periods: list[str],
    fire_date: str,
    output_path: str | Path,
    ax: plt.Axes | None = None,
) -> None:
    """Plot leave-one-out gap series vs base gap.

    Args:
        base_gap: Base gap series (T,).
        loo_gaps: Dict mapping donor name → LOO gap series.
        time_periods: Year-month list.
        fire_date: Fire year-month string.
        output_path: Output file path.
        ax: Existing axes.
    """
    created = ax is None
    if created:
        fig, ax = plt.subplots(figsize=(8, 4))

    x = np.arange(len(time_periods))

    for name, gap in loo_gaps.items():
        n = min(len(gap), len(x))
        ax.plot(x[:n], gap[:n], linewidth=0.8, linestyle="--", alpha=0.6, label=f"Drop {name}")

    ax.plot(x, base_gap, color=TREATED_COLOR, linewidth=2.0, label="Base SCM")

    if fire_date in time_periods:
        fire_x = time_periods.index(fire_date)
        ax.axvline(fire_x, color=FIRE_LINE_COLOR, linestyle="--", linewidth=1.2)

    ax.axhline(0, color="black", linewidth=0.6, linestyle=":")
    _format_x_axis(ax, time_periods)
    ax.set_ylabel("Gap (log ZHVI)")
    ax.set_title("Leave-one-out robustness")
    ax.legend(frameon=False, fontsize=8, ncol=2)

    if created:
        _save(fig, output_path)


def plot_model_comparison(
    model_registry,
    time_periods: list[str],
    fire_date: str,
    output_path: str | Path,
    ax: plt.Axes | None = None,
) -> None:
    """Plot gap series for ADH, GSynth, ASCM side-by-side.

    Args:
        model_registry: ModelRegistry with registered models.
        time_periods: Year-month list.
        fire_date: Fire year-month string.
        output_path: Output file path.
        ax: Existing axes.
    """
    created = ax is None
    if created:
        fig, ax = plt.subplots(figsize=(8, 4))

    colors = {"ADH": TREATED_COLOR, "GSynth": "#E15759", "ASCM": "#59A14F"}
    x = np.arange(len(time_periods))

    for name, color in colors.items():
        if name not in model_registry:
            continue
        entry = model_registry.get(name)
        gap = entry["meta"].get("gap_series")
        if gap is None:
            continue
        n = min(len(gap), len(x))
        ax.plot(x[:n], gap[:n], color=color, linewidth=1.5, label=name)

    if fire_date in time_periods:
        fire_x = time_periods.index(fire_date)
        ax.axvline(fire_x, color=FIRE_LINE_COLOR, linestyle="--", linewidth=1.2)

    ax.axhline(0, color="black", linewidth=0.6, linestyle=":")
    _format_x_axis(ax, time_periods)
    ax.set_ylabel("Gap (log ZHVI)")
    ax.set_title("SCM model comparison")
    ax.legend(frameon=False, fontsize=9)

    if created:
        _save(fig, output_path)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _format_x_axis(ax: plt.Axes, time_periods: list[str]) -> None:
    n = len(time_periods)
    step = max(1, n // 8)
    ticks = list(range(0, n, step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([time_periods[i] for i in ticks], rotation=45, ha="right", fontsize=8)


def _save(fig: plt.Figure, output_path: str | Path) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    if out.suffix == ".pdf":
        fig.savefig(out.with_suffix(".png"))
    plt.close(fig)
