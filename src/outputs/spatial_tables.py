"""LaTeX table generation for spatial econometrics results."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _stars(p: float) -> str:
    """Return LaTeX significance star string for a given p-value."""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def _fmt(v: float, decimals: int = 3) -> str:
    """Format a float to a fixed-decimal string, returning '--' for NaN."""
    if np.isnan(v):
        return "--"
    return f"{v:.{decimals}f}"


def sar_sem_sdm_latex(model_registry, lrt_sdm_sar: dict | None = None, wald_sdm_sem: dict | None = None) -> str:
    """Generate a LaTeX table comparing SAR, SEM, and SDM estimates.

    Writes the table to docs/tables/phase3_spatial_models.tex as a side-effect.

    Args:
        model_registry: Fitted SpatialModelRegistry with SAR, SEM, SDM registered.
        lrt_sdm_sar: Optional dict from SpatialDurbinModel.test_sar_restriction()
            containing keys lr_stat and p_value.
        wald_sdm_sem: Optional dict from SpatialDurbinModel.test_sem_cf_restriction()
            containing keys W_stat and p_value.

    Returns:
        LaTeX string for the complete table environment.
    """
    df = model_registry.compare()
    models = {row["model"]: model_registry._models[row["model"]] for _, row in df.iterrows()}

    rows_data = []
    for name, m in models.items():
        sp_val = getattr(m, "rho_", getattr(m, "lambda_", float("nan")))
        sp_se = getattr(m, "se_", np.array([float("nan")]))[0]
        sp_p = getattr(m, "p_values_", np.array([float("nan")]))[0]
        rows_data.append({
            "model": name,
            "spatial_param": sp_val,
            "spatial_se": sp_se,
            "spatial_p": sp_p,
            "ll": getattr(m, "log_likelihood_", float("nan")),
            "aic": getattr(m, "aic_", float("nan")),
            "bic": getattr(m, "bic_", float("nan")),
        })

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Spatial Model Estimates: SAR, SEM, SDM}",
        r"\begin{threeparttable}",
        r"\begin{tabular}{lccc}",
        r"\hline\hline",
        r" & SAR & SEM & SDM \\",
        r"\hline",
    ]

    [r["model"] for r in rows_data]
    for rname, key in [("Spatial parameter", "spatial_param"), ("Log-likelihood", "ll"), ("AIC", "aic"), ("BIC", "bic")]:
        vals = [_fmt(r[key]) + _stars(r.get("spatial_p", 1.0) if key == "spatial_param" else 1.0) for r in rows_data]
        lines.append(f"{rname} & " + " & ".join(vals) + r" \\")
        if key == "spatial_param":
            ses = [f"({_fmt(r['spatial_se'])})" for r in rows_data]
            lines.append("  & " + " & ".join(ses) + r" \\")

    if lrt_sdm_sar is not None:
        lr = _fmt(lrt_sdm_sar.get("lr_stat", float("nan")))
        p_lr = lrt_sdm_sar.get("p_value", 1.0)
        lines.append(r"\hline")
        lines.append(f"LR(SDM vs SAR) & & & {lr}{_stars(p_lr)}" + r" \\")

    if wald_sdm_sem is not None:
        w_stat = _fmt(wald_sdm_sem.get("W_stat", float("nan")))
        p_w = wald_sdm_sem.get("p_value", 1.0)
        lines.append(f"Wald(CF: SDM vs SEM) & & & {w_stat}{_stars(p_w)}" + r" \\")

    lines += [
        r"\hline\hline",
        r"\end{tabular}",
        r"\begin{tablenotes}\small",
        r"\item * $p<0.10$; ** $p<0.05$; *** $p<0.01$. HC-robust SE in parentheses.",
        r"\end{tablenotes}",
        r"\end{threeparttable}",
        r"\end{table}",
    ]
    tex = "\n".join(lines)
    Path("docs/tables").mkdir(parents=True, exist_ok=True)
    Path("docs/tables/phase3_spatial_models.tex").write_text(tex)
    return tex


def effects_latex(effects_df: pd.DataFrame) -> str:
    """Generate a LaTeX table of LeSage-Pace direct/indirect/total effects.

    Writes the table to docs/tables/phase3_effects.tex as a side-effect.

    Args:
        effects_df: DataFrame from LeSagePaceEffects.summary_table() with columns
            variable, direct, indirect, total, direct_se, indirect_se, total_se,
            direct_p, indirect_p, total_p.

    Returns:
        LaTeX string for the complete table environment.
    """
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{LeSage-Pace Direct, Indirect, and Total Effects (SDM)}",
        r"\begin{tabular}{lccc}",
        r"\hline\hline",
        r"Variable & Direct & Indirect & Total \\",
        r"\hline",
    ]
    for _, row in effects_df.iterrows():
        d = _fmt(row["direct"])
        i = _fmt(row["indirect"])
        t = _fmt(row["total"])
        d_stars = _stars(row.get("direct_p", 1.0))
        i_stars = _stars(row.get("indirect_p", 1.0))
        t_stars = _stars(row.get("total_p", 1.0))
        lines.append(f"{row['variable']} & {d}{d_stars} & {i}{i_stars} & {t}{t_stars}" + r" \\")
        dse = _fmt(row.get("direct_se", float("nan")))
        ise = _fmt(row.get("indirect_se", float("nan")))
        tse = _fmt(row.get("total_se", float("nan")))
        lines.append(f"  & ({dse}) & ({ise}) & ({tse})" + r" \\")
    lines += [
        r"\hline\hline",
        r"\end{tabular}",
        r"\end{table}",
    ]
    tex = "\n".join(lines)
    Path("docs/tables").mkdir(parents=True, exist_ok=True)
    Path("docs/tables/phase3_effects.tex").write_text(tex)
    return tex


def moran_lisa_latex(global_morans_dict: dict, cluster_counts_dict: dict) -> str:
    """Generate a two-panel LaTeX table for Global Moran's I and LISA cluster counts.

    Writes the table to docs/tables/phase3_moran_lisa.tex as a side-effect.

    Args:
        global_morans_dict: Dict from GlobalMoransI.summary() with keys I, E_I,
            Var_I, z_score, p_value_analytical, p_value_permutation.
        cluster_counts_dict: Dict from LocalMoransI.cluster_counts() with keys
            HH, LL, HL, LH, NS (and optionally total).

    Returns:
        LaTeX string for the complete table environment.
    """
    moran_i = _fmt(global_morans_dict.get("I", float("nan")))
    EI = _fmt(global_morans_dict.get("E_I", float("nan")))
    z = _fmt(global_morans_dict.get("z_score", float("nan")))
    p_a = _fmt(global_morans_dict.get("p_value_analytical", float("nan")), 4)
    p_p = _fmt(global_morans_dict.get("p_value_permutation", float("nan")), 4)
    total = cluster_counts_dict.get("total", sum(v for k, v in cluster_counts_dict.items() if k != "total"))

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Global Moran's I and LISA Cluster Summary}",
        r"\begin{tabular}{lc}",
        r"\hline\hline",
        r"\multicolumn{2}{l}{\textit{Panel A: Global Moran's I}} \\",
        r"\hline",
        f"Moran's $I$ & {moran_i}" + r" \\",
        f"$E[I]$ & {EI}" + r" \\",
        f"$z$-score & {z}" + r" \\",
        f"$p$-value (analytical) & {p_a}" + r" \\",
        f"$p$-value (permutation, 999) & {p_p}" + r" \\",
        r"\hline",
        r"\multicolumn{2}{l}{\textit{Panel B: LISA Cluster Counts}} \\",
        r"\hline",
        r"Cluster & Count (\%) \\",
        r"\hline",
    ]
    for label in ("HH", "LL", "HL", "LH", "NS"):
        cnt = cluster_counts_dict.get(label, 0)
        pct = 100.0 * cnt / max(total, 1)
        lines.append(f"{label} & {cnt} ({pct:.1f}\\%)" + r" \\")
    lines += [
        r"\hline",
        f"Total & {total}" + r" \\",
        r"\hline\hline",
        r"\end{tabular}",
        r"\end{table}",
    ]
    tex = "\n".join(lines)
    Path("docs/tables").mkdir(parents=True, exist_ok=True)
    Path("docs/tables/phase3_moran_lisa.tex").write_text(tex)
    return tex
