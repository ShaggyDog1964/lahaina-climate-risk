"""Interactive spatial visualizations (Folium choropleth + Matplotlib)."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


_LISA_COLORS = {
    "HH": "#d73027",
    "LL": "#4575b4",
    "HL": "#fdae61",
    "LH": "#abd9e9",
    "NS": "#f5f5f5",
}


def plot_lisa_map(gdf: gpd.GeoDataFrame, output_path: str) -> str:
    """Interactive Folium LISA cluster map saved as self-contained HTML."""
    import folium

    center_lat = float(gdf.geometry.centroid.y.mean())
    center_lon = float(gdf.geometry.centroid.x.mean())
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")

    label_col = "cluster_label" if "cluster_label" in gdf.columns else "NS"

    for _, row in gdf.iterrows():
        color = _LISA_COLORS.get(str(row.get("cluster_label", "NS")), "#f5f5f5")
        geom = row.geometry
        if geom is None:
            continue
        lat = float(geom.y) if geom.geom_type == "Point" else float(geom.centroid.y)
        lon = float(geom.x) if geom.geom_type == "Point" else float(geom.centroid.x)
        tooltip = (
            f"ID: {row.get('parcel_id', '')}<br>"
            f"Cluster: {row.get('cluster_label', 'NS')}<br>"
            f"I_local: {row.get('I_local', 0):.4f}<br>"
            f"p-value: {row.get('p_value', 1):.4f}"
        )
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            tooltip=tooltip,
        ).add_to(m)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    m.save(output_path)
    return output_path


def plot_gwr_surface(
    gdf: gpd.GeoDataFrame,
    variable: str,
    output_path: str,
) -> str:
    """Interactive Folium choropleth of a GWR local β surface."""
    import folium
    from branca.colormap import LinearColormap

    col = f"beta_{variable}" if f"beta_{variable}" in gdf.columns else variable
    if col not in gdf.columns:
        raise ValueError(f"Column {col!r} not found in GeoDataFrame.")

    vals = gdf[col].values
    vmin, vmax = float(np.nanpercentile(vals, 5)), float(np.nanpercentile(vals, 95))
    if vmin == vmax:
        vmin -= 0.1; vmax += 0.1

    center_lat = float(gdf.geometry.centroid.y.mean())
    center_lon = float(gdf.geometry.centroid.x.mean())
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")

    colormap = LinearColormap(
        colors=["#4575b4", "#ffffff", "#d73027"],
        vmin=vmin,
        vmax=vmax,
    )
    colormap.caption = f"Local β: {variable}"
    colormap.add_to(m)

    for _, row in gdf.iterrows():
        val = row.get(col, 0)
        if pd.isna(val):
            continue
        geom = row.geometry
        if geom is None:
            continue
        lat = float(geom.y) if geom.geom_type == "Point" else float(geom.centroid.y)
        lon = float(geom.x) if geom.geom_type == "Point" else float(geom.centroid.x)
        color = colormap(float(val))
        t_col = f"t_{variable}" if f"t_{variable}" in gdf.columns else None
        t_val = float(row.get(t_col, 0)) if t_col else 0.0
        tooltip = f"β: {val:.4f}<br>t: {t_val:.3f}"
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            tooltip=tooltip,
        ).add_to(m)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    m.save(output_path)
    return output_path


def plot_spillover_decay(
    effects_df: pd.DataFrame,
    output_path: str,
    dist_col: str = "dist_band_km",
    beta_col: str = "mean_beta",
    se_col: str = "se_beta",
) -> str:
    """Spillover decay: mean local GWR β vs distance band, with fitted decay."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.set_facecolor("#f8f8f8")
    fig.patch.set_facecolor("white")

    x = effects_df[dist_col].values if dist_col in effects_df.columns else np.arange(len(effects_df))
    y = effects_df[beta_col].values if beta_col in effects_df.columns else effects_df.iloc[:, 0].values
    se = effects_df[se_col].values if se_col in effects_df.columns else np.ones_like(y) * 0.01

    ax.errorbar(x, y, yerr=1.96 * se, fmt="o", color="#2166ac", capsize=4, label="Mean local β ± 1.96 SE")

    # Fit exponential decay if y values allow
    valid = y < 0
    if valid.sum() >= 3 and np.all(x > 0):
        try:
            from scipy.optimize import curve_fit
            def exp_decay(x_, a, b): return a * np.exp(-b * x_)
            popt, _ = curve_fit(exp_decay, x[valid], y[valid], p0=[-0.1, 0.1], maxfev=1000)
            x_fit = np.linspace(x.min(), x.max(), 200)
            ax.plot(x_fit, exp_decay(x_fit, *popt), "--", color="#d73027", label="Fitted decay")
        except Exception:
            pass

    ax.axhline(0, color="gray", linewidth=0.8, linestyle=":")
    ax.set_xlabel("Distance from fire (km)", fontsize=11)
    ax.set_ylabel("Mean local β (dist_to_fire)", fontsize=11)
    ax.set_title("Spillover Decay: Price Effect vs Distance", fontsize=12)
    ax.legend(frameon=False)
    plt.tight_layout()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    base = Path(output_path).with_suffix("")
    fig.savefig(str(base) + ".pdf", bbox_inches="tight")
    fig.savefig(str(base) + ".png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_spatial_model_comparison(model_registry, output_path: str) -> str:
    """Bar chart: AIC comparison across spatial models."""
    df = model_registry.compare()
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ["#1f78b4", "#33a02c", "#e31a1c", "#ff7f00"]
    bars = ax.bar(df["model"], df["aic"], color=colors[: len(df)], edgecolor="white")
    for bar, (_, row) in zip(bars, df.iterrows()):
        sp_val = row.get("spatial_param", float("nan"))
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + abs(df["aic"].max() - df["aic"].min()) * 0.01,
            f"ρ={sp_val:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    ax.set_ylabel("AIC")
    ax.set_title("Spatial Model Comparison (AIC)")
    ax.set_facecolor("#f8f8f8")
    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path
