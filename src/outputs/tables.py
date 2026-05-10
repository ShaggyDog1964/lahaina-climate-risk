"""Publication-quality LaTeX table generation for Phase 1 results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _stars(p: float) -> str:
    """Return significance stars based on p-value.

    Args:
        p: p-value.

    Returns:
        String of stars: *** p<0.01, ** p<0.05, * p<0.10, else empty string.
    """
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def _fmt_coef(coef: float, se: float, p: float) -> tuple[str, str]:
    """Format coefficient and standard error for a LaTeX table cell.

    Args:
        coef: Coefficient estimate.
        se: Standard error.
        p: p-value.

    Returns:
        Tuple of (coef_string_with_stars, se_string_in_parentheses).
    """
    return f"{coef:.4f}{_stars(p)}", f"({se:.4f})"


def hedonic_to_latex(results_path: str, output_dir: str = "docs/tables") -> str:
    """Format hedonic regression results as a publication-quality LaTeX table.

    Produces a threeparttable with Panel A (structural controls) and
    Panel B (treatment indicators / FE) with HC3 note.

    Args:
        results_path: Path to hedonic_table.csv from HedonicModel.summary_table().
        output_dir: Directory to save the generated .tex file.

    Returns:
        LaTeX string for the threeparttable.

    Raises:
        FileNotFoundError: If results_path does not exist.
    """
    df = pd.read_csv(results_path, index_col=0)

    structural_terms = ["structure_sqft", "land_area_sqft", "year_built", "Intercept", "const"]
    panel_a_rows = [idx for idx in df.index if any(t in str(idx) for t in structural_terms)]
    panel_b_rows = [idx for idx in df.index if idx not in panel_a_rows]

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\begin{threeparttable}",
        r"\caption{Hedonic Pricing Model: Effect of Lahaina Fire on Property Values}",
        r"\label{tab:hedonic}",
        r"\begin{tabular}{lcc}",
        r"\toprule",
        r"Variable & Coefficient & Std. Error \\",
        r"\midrule",
        r"\multicolumn{3}{l}{\textit{Panel A: Structural Controls}} \\",
    ]

    for idx in panel_a_rows:
        row = df.loc[idx]
        coef_s, se_s = _fmt_coef(row["coef"], row["se"], row["p"])
        label = str(idx).replace("_", r"\_")
        lines.append(f"{label} & {coef_s} & {se_s} \\\\")

    lines += [
        r"\midrule",
        r"\multicolumn{3}{l}{\textit{Panel B: Treatment Indicators}} \\",
    ]

    for idx in panel_b_rows[:15]:
        row = df.loc[idx]
        coef_s, se_s = _fmt_coef(row["coef"], row["se"], row["p"])
        label = str(idx).replace("_", r"\_")
        lines.append(f"{label} & {coef_s} & {se_s} \\\\")

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}",
        r"\small",
        r"\item \textit{Notes:} HC3 robust standard errors in parentheses. "
        r"Census-block and year-month fixed effects included. "
        r"* p$<$0.10, ** p$<$0.05, *** p$<$0.01.",
        r"\end{tablenotes}",
        r"\end{threeparttable}",
        r"\end{table}",
    ]

    latex_str = "\n".join(lines)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "hedonic_table.tex").write_text(latex_str)
    return latex_str


def did_to_latex(event_study_path: str, output_dir: str = "docs/tables") -> str:
    """Format Callaway-Sant'Anna event-study ATTs as a LaTeX table.

    Produces a threeparttable with Panel A (pre-treatment) and
    Panel B (post-treatment) rows.

    Args:
        event_study_path: Path to event_study.csv from CallawayAntaCSiD.event_study_df().
        output_dir: Directory to save the generated .tex file.

    Returns:
        LaTeX string for the event-study table.

    Raises:
        FileNotFoundError: If event_study_path does not exist.
    """
    df = pd.read_csv(event_study_path)

    pre_df = df[df["event_time"] < 0].sort_values("event_time")
    post_df = df[df["event_time"] >= 0].sort_values("event_time")

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\begin{threeparttable}",
        r"\caption{Event-Study Estimates: Callaway-Sant'Anna ATT(g,t)}",
        r"\label{tab:event_study}",
        r"\begin{tabular}{rrrr}",
        r"\toprule",
        r"Event Time & ATT & Std. Error & 95\% CI \\",
        r"\midrule",
        r"\multicolumn{4}{l}{\textit{Panel A: Pre-Treatment Periods}} \\",
    ]

    for _, row in pre_df.iterrows():
        ci = f"[{row['ci_lower']:.4f}, {row['ci_upper']:.4f}]"
        lines.append(
            f"$t={int(row['event_time'])}$ & {row['att']:.4f} & {row['se']:.4f} & {ci} \\\\"
        )

    lines += [
        r"\midrule",
        r"\multicolumn{4}{l}{\textit{Panel B: Post-Treatment Periods}} \\",
    ]

    for _, row in post_df.iterrows():
        ci = f"[{row['ci_lower']:.4f}, {row['ci_upper']:.4f}]"
        lines.append(
            f"$t={int(row['event_time'])}$ & {row['att']:.4f} & {row['se']:.4f} & {ci} \\\\"
        )

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}",
        r"\small",
        r"\item \textit{Notes:} Callaway-Sant'Anna (2021) group-time ATTs aggregated "
        r"to dynamic event-study estimates. 95\% pointwise confidence intervals shown. "
        r"$t=0$ indicates August 2023 (fire month).",
        r"\end{tablenotes}",
        r"\end{threeparttable}",
        r"\end{table}",
    ]

    latex_str = "\n".join(lines)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "event_study_table.tex").write_text(latex_str)
    return latex_str
