"""LaTeX table generation for SCM results."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def weights_table_latex(model_registry) -> str:
    """Generate LaTeX table of donor weights with characteristics.

    Args:
        model_registry: ModelRegistry with registered models.

    Returns:
        LaTeX string.
    """
    entry = model_registry.get("ADH")
    model = entry["model"]
    meta = entry["meta"]
    donor_names = meta.get("donor_names", [])
    weights = model.w_ if model.w_ is not None else np.array([])
    acs = meta.get("acs", pd.DataFrame())

    rows = []
    for name, w in zip(donor_names, weights, strict=False):
        if w <= 0.01:
            continue
        income = ""
        zhvi_mean = ""
        if acs is not None and len(acs) > 0 and "zip_code" in acs.columns:
            row = acs[acs["zip_code"] == name]
            if len(row):
                income = f"{row['median_hh_income'].iloc[0]:,.0f}" if "median_hh_income" in row else ""
                zhvi_mean = f"{row.get('zhvi_mean', pd.Series([0])).iloc[0]:,.0f}" if "zhvi_mean" in row else ""
        rows.append(f"    {name} & {w:.3f} & {income} & {zhvi_mean} \\\\")

    body = "\n".join(rows)
    table = f"""\\begin{{table}}[htbp]
\\centering
\\begin{{threeparttable}}
\\caption{{Donor weights — ADH Synthetic Control}}
\\begin{{tabular}}{{lrcc}}
\\hline
Zip Code & Weight & Median HH Income & Mean ZHVI \\\\
\\hline
{body}
\\hline
\\end{{tabular}}
\\begin{{tablenotes}}
\\small
\\item Weights sum to 1.0. Donors with weight $< 0.01$ omitted.
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}"""
    return table


def rmspe_table_latex(model_registry) -> str:
    """Generate LaTeX RMSPE comparison table.

    Args:
        model_registry: ModelRegistry with registered models.

    Returns:
        LaTeX string.
    """
    comp = model_registry.compare_rmspe()
    if comp.empty:
        return ""

    # Identify minimum RMSPE ratio row
    min_ratio_idx = comp["rmspe_ratio"].idxmin() if "rmspe_ratio" in comp.columns else -1

    rows = []
    for i, row in comp.iterrows():
        pre = f"{row['pre_rmspe']:.4f}" if pd.notna(row.get("pre_rmspe")) else "--"
        post = f"{row['post_rmspe']:.4f}" if pd.notna(row.get("post_rmspe")) else "--"
        ratio = f"{row['rmspe_ratio']:.3f}" if pd.notna(row.get("rmspe_ratio")) else "--"
        pval = row.get("p_value", "--")
        pval_str = f"{pval:.3f}" if isinstance(pval, float) else str(pval)
        name = row["model"]
        line = f"    {name} & {pre} & {post} & {ratio} & {pval_str} \\\\"
        if i == min_ratio_idx:
            line = f"    \\textbf{{{name}}} & \\textbf{{{pre}}} & \\textbf{{{post}}} & \\textbf{{{ratio}}} & \\textbf{{{pval_str}}} \\\\"
        rows.append(line)

    body = "\n".join(rows)
    table = f"""\\begin{{table}}[htbp]
\\centering
\\begin{{threeparttable}}
\\caption{{SCM estimator comparison — RMSPE}}
\\begin{{tabular}}{{lcccc}}
\\hline
Estimator & Pre-RMSPE & Post-RMSPE & RMSPE Ratio & $p$-value \\\\
\\hline
{body}
\\hline
\\end{{tabular}}
\\begin{{tablenotes}}
\\small
\\item Bold row has lowest RMSPE ratio. $p$-value from in-space placebo test.
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}"""
    return table


def balance_table_latex(
    X0: np.ndarray,
    X1: np.ndarray,
    donor_names: list[str],
    covariate_names: list[str],
    w_adh: np.ndarray,
) -> str:
    """Generate LaTeX balance table.

    Args:
        X0: Donor covariate matrix (k, J).
        X1: Treated covariate vector (k,).
        donor_names: Donor zip code labels.
        covariate_names: Covariate labels.
        w_adh: ADH donor weights (J,).

    Returns:
        LaTeX string.
    """
    rows = []
    for k, name in enumerate(covariate_names):
        treated_val = X1[k]
        donor_mean = float(np.mean(X0[k]))
        synthetic_val = float(X0[k] @ w_adh)
        rows.append(
            f"    {name.replace('_', ' ').title()} & {treated_val:.3f} & {donor_mean:.3f} & {synthetic_val:.3f} \\\\"
        )

    body = "\n".join(rows)
    table = f"""\\begin{{table}}[htbp]
\\centering
\\begin{{threeparttable}}
\\caption{{Covariate balance — treated vs. synthetic control}}
\\begin{{tabular}}{{lccc}}
\\hline
Covariate & Lahaina (96761) & Donor Mean & Synthetic Lahaina \\\\
\\hline
{body}
\\hline
\\end{{tabular}}
\\begin{{tablenotes}}
\\small
\\item Balance assessed over 2018-01 to 2023-07 pre-treatment window.
\\end{{tablenotes}}
\\end{{threeparttable}}
\\end{{table}}"""
    return table


def save_latex(content: str, filename: str) -> Path:
    """Save LaTeX string to docs/tables/."""
    out_dir = Path("docs/tables")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    out_path.write_text(content)
    return out_path
