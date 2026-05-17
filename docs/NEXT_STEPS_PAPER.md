# Paper Writing Roadmap

## Current state
- Words: 2,784 (target: 8,000–12,000 for most journals)
- Complete sections: Introduction (mostly complete), Data (structure only — all counts and dates are [TBD]), Empirical Strategy (equations and structure only), Spatial Spillover Analysis (methods described, no results), Appendices (placeholder references to methodology docs), Conclusion (structure only — all numbers are [TBD])
- Placeholder sections: ALL results, ALL tables/figures, Abstract numbers, Author info

### Critical pre-writing blockers (from RESEARCH_ASSESSMENT.md §5–6)

The paper cannot be written until the following are resolved. Writing prose around the current result files will produce a fraudulent paper:

| Blocker | Status | Required action |
|---|---|---|
| `maui_assessor.csv` provenance | CRITICAL — single zoning code across 2,636 transactions; pre-2024 data source unknown | Obtain verified deed transfer records from Hawaii Bureau of Conveyances or ATTOM/CoreLogic |
| `results/att_gt.pkl` / `event_study.csv` | DEGENERATE — all ATT = 0.0, SE = 0.05, parallel-trends p = NaN | Fix C&S routine after real data lands; add binary `treated` dummy to panel |
| `results/hedonic_results.pkl` | CORRUPT — statsmodels pickle failure, no treatment coefficient | Rerun hedonic after data fix |
| `results/triple_diff_results.pkl` | CORRUPT — same pickle error | Rerun after hedonic is fixed |
| `results/decomposition.csv` | DEGENERATE — SE = inf, WUI coef = 0 | Rerun triple-diff after Phase 1 is fixed |
| `results/scm/gsynth_results.pkl` | INCOMPLETE — post_rmspe = NaN | Fix GSynth post-period computation |
| `results/scm/augsynth_results.pkl` | INCOMPLETE — all metrics NaN | Fix AugSCM |
| SCM permutation p-value | NOT SIGNIFICANT — p = 0.155 with 58 donors | Expand donor pool or reframe as directional evidence |
| Global Moran's I | WRONG INPUT — computed on raw price change, not hedonic residuals; I = −0.003, p = 0.90 | Rerun on hedonic residuals after Phase 1 is fixed |
| `results/spatial/lesage_pace_effects.parquet` | DEGENERATE — SE ≈ 4×10⁻⁷ (near-zero, physically impossible) | Rerun on larger parcel sample after Phase 1 is fixed |
| GWR optimal bandwidth | EFFECTIVELY GLOBAL — h* = 49.7 km on a 15 km study area | Rerun after spatial sample expands beyond 122 parcels |
| Spatial sample size | TOO THIN — only 122 parcels with both pre- and post-fire transactions | Requires real deed transfer data to expand |

**Estimated timeline to submittable paper:** 12–16 weeks from resolution of the transaction data problem (see RESEARCH_ASSESSMENT.md §6).

---

## BibTeX verification

All `\cite{}` keys in `paper/main.tex` were checked against `paper/references.bib`:

| Cite key | Status | Entry details |
|---|---|---|
| `CS2021` | VERIFIED | Callaway & Sant'Anna (2021), J. Econometrics, vol. 225, pp. 200–230, DOI confirmed |
| `Abadie2010` | VERIFIED | Abadie, Diamond & Hainmueller (2010), JASA, vol. 105, pp. 493–505, DOI confirmed |
| `BenMichael2021` | VERIFIED | Ben-Michael, Feller & Rothstein (2021), JASA, vol. 116, pp. 1789–1803, DOI confirmed |
| `Xu2017` | VERIFIED | Xu (2017), Political Analysis, vol. 25, pp. 57–76, DOI confirmed |
| `LeSage2009` | VERIFIED | LeSage & Pace (2009), CRC Press book, DOI confirmed |
| `Anselin1995` | VERIFIED | Anselin (1995), Geographical Analysis, vol. 27, pp. 93–115, DOI confirmed |
| `CliffOrd1981` | PRESENT but MALFORMED | Entry uses `journal = {Pion}` for a book; should be `@book` type, not `@article`. Publisher is Pion, 1981. Fix before submission |
| `Rosen1974` | VERIFIED | Rosen (1974), J. Political Economy, vol. 82, pp. 34–55, DOI confirmed |
| `Fotheringham2002` | PRESENT but MALFORMED | Entry uses `@article` type but has `publisher` and `address` fields — should be `@book`. Fix before submission |
| `MacKinnon1985` | VERIFIED | MacKinnon & White (1985), J. Econometrics, vol. 29, pp. 305–325, DOI confirmed |
| `Baldauf2020` | VERIFIED | Baldauf, Garlappi & Yannelis (2020), Review of Financial Studies, vol. 33, pp. 1256–1295, DOI confirmed |
| `Bernstein2019` | VERIFIED | Bernstein, Gustafson & Lewis (2019), J. Financial Economics, vol. 134, pp. 253–272, DOI confirmed |

Missing from `references.bib` (cited in paper but not in bib):
- Murphy & Schwartz (2022) — Camp Fire study cited in research assessment context but not yet in the paper or bib. Add before submission.
- Sutter & Poitras (2010) — same situation.

Missing from `references.bib` (will be needed once results section is written):
- `Abadie2015` is in the bib but not cited in main.tex — either cite or remove.
- `Kousky2018` is in the bib but not cited in main.tex — either cite in introduction or remove.

---

## Section completion guide

### Abstract
**Current state:** Written prose describing the methodology, but ALL quantitative results are absent. The abstract correctly previews all four phases and the belief-update channel framing.

**What needs to be filled in:** ATT point estimate and CI, triple-diff belief-update share, SCM RMSPE ratio and permutation p-value, Moran's I, spatial indirect/total ratio.

**Template (post-results):**
```
We estimate the causal effect of the August 2023 Lahaina wildfire on residential
property values in Maui County, Hawaii, using [N] parcel-level transactions from [START]
to [END]. Our Callaway-Sant'Anna difference-in-differences estimates find an average
treatment effect of [ATT]% (95% CI: [LB]% to [UB]%) for parcels within [D] km of the
fire perimeter. A triple-difference decomposition reveals that [BELIEF_UPDATE_PCT]% of
the total effect operates through a forward-looking risk-belief channel on WUI-classified
parcels beyond the physical destruction zone. Synthetic control estimates for the Lahaina
ZIP-level price index corroborate these findings, with an RMSPE ratio of [RATIO]
(permutation p = [P]). Spatial Durbin model estimates detect [SIGN] indirect spillovers
onto neighboring parcels (indirect effect: [INDIRECT]; total: [TOTAL]), with
geographically weighted regression identifying the steepest discounts in [AREA].
```

**Source files to populate placeholders:**
- `[N]`, `[START]`, `[END]`: `data/final/panel.parquet` — `panel.shape[0]`, `panel['sale_date'].min()`, `panel['sale_date'].max()`
- `[ATT]`, `[LB]`, `[UB]`: `results/att_gt.pkl` — `obj['agg_simple']` for point estimate; bootstrap CI from `obj['agg_dynamic']`
- `[D]`: defined by treatment band design (currently 0–2 km for innermost band; confirm in panel)
- `[BELIEF_UPDATE_PCT]`: `results/decomposition.csv` — `belief_update_channel / beta_post_treated_nowui * 100`
- `[RATIO]`, `[P]`: `results/inference/p_values.json` — `rmspe_ratio`, `p_value`
- `[INDIRECT]`, `[TOTAL]`: `results/spatial/lesage_pace_effects.parquet` — `indirect` and `total` columns for `dist_to_fire_km` row
- `[SIGN]`: derived from sign of indirect effect
- `[AREA]`: `results/gwr/gwr_surface.parquet` — the centroid of parcels where local beta is most negative

**Current blocker:** All of these files are either degenerate, corrupt, or produce statistically null results. Abstract numbers cannot be filled until pipeline is fixed.

---

### Author block (main.tex lines 55–57)
**Current state:**
```latex
\author{[Author TBD]\\
\small [Affiliation TBD]\\
\small \href{mailto:}{[email TBD]}}
```
**Action:** Replace with real name, department, university, and email before any public circulation. If co-authors are added later, use `\and` in the `\author{}` block and add acknowledgments.

---

### Section 1 (Introduction)
**Current state:** Mostly complete. The three research questions are stated clearly. The four-phase empirical strategy is previewed. The roadmap paragraph at the end is functional.

**What is missing:**
- Preview sentence with the headline result number (e.g., "We find that parcels within 2 km of the fire perimeter sell at a [X]% discount..."). This should be added after ATT is estimated.
- The comparison to the literature (Baldauf 2020: 10–15%, Bernstein 2019: 7%, Murphy & Schwartz 2022: 20–40% within 1 km) should be added to the introduction once the paper's own estimates are known, to contextualize the magnitude.
- Add Murphy & Schwartz (2022) Camp Fire citation to `references.bib` if the Camp Fire comparison is included.

**Template for headline sentence (insert after paragraph 2):**
```
Our preferred estimates imply that fire proximity reduced prices by approximately
[ATT]% within 2 km of the perimeter --- larger than the flood-risk discounts
documented by \citet{Bernstein2019} (7\%) and \citet{Baldauf2020} (10--15\%),
and comparable in magnitude to the Camp Fire price effects reported by
\citet{MurphySchwartz2022} (20--40\% within 1 km).
```

---

### Section 2 (Data) — §2.1 Maui County Parcel Sales
**Current state:** Subsection structure exists. Data source is described correctly. All specific counts and date ranges are [TBD]. Deflation base year is [TBD].

**What needs to be filled in:**
```
The data span [START_DATE] to [END_DATE] and cover approximately [N] residential
transactions for [M] unique parcels. Of these, [N_TREATED] transactions occur in
parcels within 5 km of the Lahaina fire perimeter (ZIP codes 96761 and adjacent areas).
All prices are deflated to [BASE_YEAR] dollars using the Hawaii component of the
FHFA All-Transactions House Price Index.
```

**Source code to generate these numbers:**
```python
import pandas as pd
panel = pd.read_parquet('data/final/panel.parquet')
print(f"N = {panel.shape[0]}")
print(f"Unique parcels = {panel['parcel_id'].nunique()}")
print(f"Date range: {panel['sale_date'].min()} to {panel['sale_date'].max()}")
print(f"Treatment band counts:\n{panel['treatment_band'].value_counts()}")
print(f"N treated (<=5km): {panel[panel['dist_to_fire_km'] <= 5].shape[0]}")
print(f"Price range: ${panel['sale_price'].min():,.0f} to ${panel['sale_price'].max():,.0f}")
```

**Full §2.1 template:**
```
The Maui County Real Property Assessment Roll contains [N] arm's-length transactions
for [M] unique residential parcels spanning [START_DATE] to [END_DATE]. We restrict
to transactions with sale prices between \$50{,}000 and \$10{,}000{,}000 to exclude
non-arm's-length transfers and extreme outliers. All prices are deflated to [BASE_YEAR]
dollars using the Hawaii component of the FHFA All-Transactions House Price Index.
Of these transactions, [N_0_2] occur in parcels within 0--2 km of the fire perimeter,
[N_2_5] within 2--5 km, [N_5_10] within 5--10 km, and [N_CONTROL] beyond 10 km
(the control group).
```

---

### Section 2 — §2.2 Fire Perimeter
**Current state:** Correctly describes the NIFC WFIGS source and H3 indexing. One [TBD]: the perimeter date ("as of [TBD]").

**Fix:** `data/raw/fire/lahaina_perimeter.geojson` — check the `PerimeterDateTime` or `CreateDate` field in the GeoJSON properties. The IRWIN record is confirmed (RESEARCH_ASSESSMENT.md §1).

---

### Section 2 — §2.3–2.6 (WUI, FRED, FHFA, Redfin)
**Current state:** All four subsections are complete prose with no [TBD] placeholders. No changes needed until reviewer requests.

---

### Section 3 (Empirical Strategy)
**Current state:** All four estimator descriptions (hedonic, C&S, triple-diff, SCM) are complete with equations. No [TBD] placeholders. Methods prose is complete.

**What is missing:** Once results exist, add a short paragraph at the top of §3.1 (Identification) noting the result of the pre-trend test: "Formal tests of the parallel-trends assumption, reported in Section~\ref{sec:results}, yield $p = [PRE_TREND_P]$, supporting the identifying assumption."

---

### Section 4 (Spatial Spillover Analysis)
**Current state:** Methods for spatial weights, Moran's I / LISA, SAR/SEM/SDM, and GWR are all written. No [TBD] placeholders. Complete.

---

### Section 5 (Results) — §5.1 Summary Statistics
**Current state:** Table environment exists, calls `\input{../docs/tables/summary_stats.tex}`. The .tex file does not exist yet.

**Table generation command:**
```python
import pandas as pd
panel = pd.read_parquet('data/final/panel.parquet')
# Split by treatment group and compute means for key variables
groups = ['0-2km', '2-5km', '5-10km', '>10km (control)']
vars = ['sale_price', 'log_price', 'sqft', 'age', 'bedrooms', 'bathrooms',
        'lot_size', 'waterfront', 'wui', 'dist_to_fire_km']
# Pivot by treatment_band and compute mean/sd for each var
```
Write output to `docs/tables/summary_stats.tex`.

---

### Section 5 — §5.2 Hedonic Estimates
**Current state:** Table environment exists (commented out, with [TBD] placeholder). Text placeholder: "parcels within 0–2 km sell at a discount of approximately [TBD]%".

**Table generation command:**
```bash
python3 -c "from src.outputs.tables import generate_hedonic_table; generate_hedonic_table()" 2>/dev/null || \
python3 -c "
import pandas as pd
df = pd.read_csv('results/hedonic_table.csv')
key = df[df.iloc[:,0].str.contains('dist_to_fire|post|wui|intercept', case=False, na=False)]
print(key.to_string())
"
```

**Text template (after results exist):**
```
Table~\ref{tab:hedonic} reports hedonic OLS estimates from
equation~(\ref{eq:hedonic_treatment}). The baseline distance gradient
$\hat{\delta}_1$ = [DIST_COEF] (SE = [DIST_SE]), indicating that each additional
kilometer from the fire perimeter is associated with a [DIST_PCT]\% change in log
price, conditional on parcel attributes and block fixed effects. The post-fire
indicator $\hat{\delta}_2$ = [POST_COEF] (SE = [POST_SE]). The model achieves
$R^2 = $ [R2] with [N] observations and [K] block-level fixed effects.
```

**Source files:**
- Coefficients: `results/hedonic_table.csv` (once fixed) or `results/hedonic_results.pkl`
- R²: from model object `.rsquared`
- Convert log-point coefficient to percent: `(exp(coef) - 1) * 100`

---

### Section 5 — §5.3 Callaway-Sant'Anna Event Study
**Current state:** Figure environment exists (commented out, [TBD] placeholder). Text placeholder: "Pre-period estimates are statistically indistinguishable from zero (p-value = [TBD])."

**Figure generation command (once event_study.csv has real estimates):**
```python
import pandas as pd, matplotlib.pyplot as plt
es = pd.read_csv('results/event_study.csv')
fig, ax = plt.subplots(figsize=(8, 4))
ax.errorbar(es['event_time'], es['att'], yerr=1.96 * es['se'],
            fmt='o', capsize=3, color='steelblue')
ax.axhline(0, color='k', linewidth=0.5)
ax.axvline(0, color='r', linewidth=1, linestyle='--', label='Fire (Aug 2023)')
ax.set_xlabel('Event time (months)')
ax.set_ylabel('ATT (log price)')
ax.set_title("Callaway-Sant'Anna Event Study")
ax.legend()
plt.tight_layout()
plt.savefig('figures/event_study.pdf', dpi=150)
```

**Text template:**
```
Figure~\ref{fig:event_study} plots event-study estimates from \citet{CS2021}.
Pre-period estimates (event time $< 0$) are jointly insignificant
($p = $ [PRE_TREND_P]), supporting the parallel trends assumption.
Post-fire ATT estimates peak at $-$[PEAK_ATT]\% in month [PEAK_MONTH] relative
to the fire date and [recover/persist] through the end of the sample at
event time [LAST_PERIOD] months.
```

**Source files:**
- `[PRE_TREND_P]`: `results/parallel_trends_test.json` — `p_value`
- `[PEAK_ATT]`, `[PEAK_MONTH]`: `results/event_study.csv` — row with minimum `att` value among `event_time > 0`

---

### Section 5 — §5.4 Triple Difference
**Current state:** Table environment exists ([TBD] placeholder). Text: "$\hat\beta_1$ is [TBD], implying an additional discount of approximately [TBD]% for WUI-classified treated parcels."

**Text template:**
```
Table~\ref{tab:triple_diff} reports triple-difference estimates from
equation~(\ref{eq:triple_diff}). The coefficient on the triple interaction
$\hat{\beta}_1$ (Post $\times$ Treated $\times$ WUI) = [BETA1] (SE = [BETA1_SE]),
while the double interaction $\hat{\beta}_2$ (Post $\times$ Treated) = [BETA2]
(SE = [BETA2_SE]). The belief-update channel estimate $\hat{\beta}_1 - \hat{\beta}_2$
= [BELIEF_UPDATE] (SE = [BELIEF_SE]) implies that WUI-classified treated parcels
experience an additional [BELIEF_PCT]\% discount beyond the physical displacement
channel, accounting for approximately [BELIEF_SHARE]\% of the total treatment effect.
```

**Source file:** `results/decomposition.csv`
- `[BETA1]`: `beta_post_treated_wui`
- `[BETA2]`: `beta_post_treated_nowui`
- `[BELIEF_UPDATE]`: `belief_update_channel`
- `[BELIEF_SHARE]`: `belief_update_channel / beta_post_treated_nowui * 100`

---

### Section 5 — §5.5 Synthetic Control
**Current state:** Table environment exists ([TBD] placeholder). Text: "permutation p-value of [TBD] for the ADH estimator."

**Current actual values (from RESEARCH_ASSESSMENT.md §3):**
- ADH RMSPE ratio: **3.06** (pre-RMSPE = 0.0154, post-RMSPE = 0.0471)
- Permutation p-value: **0.155** (not significant at conventional levels)
- Donor weights concentrate on 5 of 58 ZIPs (d20 = 0.609, d21 = 0.145, d37 = 0.066, d50 = 0.168, d12 = 0.009)
- GSynth: pre-RMSPE = 0.0198, post-RMSPE = NaN (incomplete)
- AugSCM: all metrics NaN (incomplete)

**Honest framing given p = 0.155:**
```
Figure~\ref{fig:scm_gap} plots the synthetic control gap series for Lahaina
(ZIP 96761). The pre-period RMSPE is [PRE_RMSPE] log points; the post-period
RMSPE rises to [POST_RMSPE], yielding an RMSPE ratio of [RATIO]. In-space
permutation inference across [N_DONORS] Hawaii donor ZIPs yields a one-sided
p-value of [P_VALUE]. While the RMSPE ratio is economically large, the
permutation distribution with a limited donor pool of [N_DONORS] units provides
limited power; expanding the donor pool to include mainland resort-market
comparators is a robustness check currently in progress.
```

**Source files:**
- `results/scm/adh_results.pkl`
- `results/inference/p_values.json`
- `results/scm/model_comparison.csv`

**Action required before writing:** Fix GSynth and AugSCM post-period computation so the model comparison table can be populated with all three estimators. Consider expanding donor pool to increase permutation test power.

---

### Section 5 — §5.6 Spatial Autocorrelation
**Current state:** Text placeholder: "$I = $ [TBD] ($z = $ [TBD], $p < $ [TBD])". LISA map is [TBD].

**Current actual values (WRONG INPUT — from raw price change, not hedonic residuals):**
- I = −0.0034, z = 0.125, p = 0.90 (analytical), p = 0.42 (permutation)
- LISA: 3 HH, 1 LL, 118 NS out of 122 parcels

**These values must NOT be reported in the paper.** They are computed on the wrong variable (raw price change instead of hedonic residuals) and are statistically null regardless.

**Action required:** After Phase 1 is fixed, rerun Moran's I on hedonic residuals. If the result is still null, the spatial section must be reframed: report the null result and note that spatial autoregressive models are estimated as a robustness check regardless.

**Text template (for non-null result):**
```
The global Moran's I for OLS hedonic residuals is $I = $ [I] ($z = $ [Z],
permutation $p = $ [P]), indicating [significant/no] positive spatial
autocorrelation [at the 5\% level] and [motivating/not motivating] the
spatial regression analysis in Section~\ref{sec:spatial}.
```

**Text template (for null result — honest framing):**
```
The global Moran's I for OLS hedonic residuals is $I = $ [I] ($z = $ [Z],
$p = $ [P]), indicating no statistically significant spatial autocorrelation.
We nonetheless estimate spatial regression models as a robustness check, given
that the 122-parcel sample may have insufficient power to detect modest spatial
dependence, and the theoretical motivation for price spillovers across neighboring
parcels in a fire-risk context is strong.
```

**Source:** `results/esda/global_morans.json` (after rerunning on hedonic residuals)

---

### Section 5 — §5.7 Spatial Regression
**Current state:** Text placeholder: "The preferred model by AIC is [TBD]."

**Current actual values (from RESEARCH_ASSESSMENT.md §4):**
- SAR: ρ = −0.182, AIC = 264.23
- SEM: λ = −0.191, AIC = 264.16
- SDM: ρ = −0.165, AIC = 265.82
- AIC gap between SAR/SEM/SDM: < 2 points — indistinguishable
- LR test SDM vs. SAR: p = 0.520

**These values may not be publishable as-is** — negative spatial parameters on 122 observations are consistent with noise. Must rerun on larger parcel sample with hedonic residuals as the spatial lag input.

**Text template:**
```
Table~\ref{tab:spatial} compares SAR, SEM, and SDM estimates. The preferred
model by AIC is [MODEL] (AIC = [AIC]; $\Delta$AIC from next-best: [DELTA_AIC]).
The spatial autoregressive parameter $\hat{\rho} = $ [RHO] ([SE]),
[indicating/not indicating] significant spatial dependence ($p = $ [P_RHO]).
A likelihood ratio test of the SDM against the SAR yields
$\chi^2 = $ [LR_STAT] ($p = $ [LR_P]), [rejecting/not rejecting] the
common-factor restriction.
```

**Source files:** `results/spatial/nesting_tests.json`, `results/spatial/sdm_results.pkl`

---

### Section 5 — §5.8 LeSage-Pace Effects
**Current state:** Text placeholder: "The indirect (spillover) effect ... is [TBD] at the median distance."

**Current actual values (DEGENERATE — SE ≈ 4×10⁻⁷):**
- Direct: −0.0079, Indirect: +0.0225 (opposite sign), Total: +0.0146

These values cannot be reported. Standard errors are physically impossible. Must rerun after sample expansion and Phase 1 fix.

**Text template (for valid results):**
```
The LeSage-Pace decomposition (Table~\ref{tab:effects}) finds a direct effect of
distance on log price of [DIRECT] (SE = [DIRECT_SE]) and an indirect (spillover)
effect of [INDIRECT] (SE = [INDIRECT_SE]). The indirect-to-total ratio of
[IND_TOTAL_RATIO] implies that [IND_TOTAL_PCT]\% of the total price response
propagates through spatial spillovers to neighboring parcels, indicating that
aggregate market-wide effects substantially [exceed/fall short of] the direct
treatment effect on immediately proximate parcels.
```

**Source file:** `results/spatial/lesage_pace_effects.parquet`

---

### Section 5 — §5.9 GWR Spatial Heterogeneity
**Current state:** Text placeholder: "bandwidth is $h^* = $ [TBD] meters."

**Current actual value:** h* = 49.7 km (effectively global — no local variation detectable). Local betas range 0.02973–0.03007 (0.034% variation — numerical noise). Must rerun after sample expansion.

**Text template (for valid results):**
```
Leave-one-out cross-validation selects an optimal bandwidth of $h^* = $ [BW] km
(Figure~\ref{fig:gwr_surface}). Local estimates of the distance-to-perimeter
coefficient range from [MIN_BETA] to [MAX_BETA] log points per km, with the
steepest discounts concentrated in [AREA] and the smallest discounts in [AREA_2].
This spatial heterogeneity is consistent with [explanation — e.g., differential
insurance repricing, variation in flood/fire exposure, proximity to alternative
amenities].
```

**Source files:**
- `results/gwr/optimal_bandwidth.json` — `h_star`
- `results/gwr/gwr_surface.parquet` — local beta coefficients and parcel coordinates

---

### Section 6 (Conclusion)
**Current state:** Prose structure is complete but all numbers are [TBD]. The three substantive paragraphs (headline ATT, indirect spillovers, policy implications) are written correctly around placeholders.

**Template fill-in (all from result files listed above):**
- Paragraph 1: Replace "[TBD]%" with ATT estimate; replace "[TBD]%" belief-update share with decomposition result
- Paragraph 2: Replace "[TBD] times the direct effect" with LeSage-Pace indirect/direct ratio
- Paragraph 3: No numbers needed; prose is complete

---

## Table and figure inventory

All tables should be `.tex` files in `docs/tables/`. All figures should be `.pdf` in `figures/`. The paper references them via `\input{}` and `\includegraphics{}`.

| Output | Paper reference | Generator | Status |
|---|---|---|---|
| `docs/tables/summary_stats.tex` | `\ref{tab:summary}` | manual pandas pivot | MISSING |
| `docs/tables/hedonic.tex` | `\ref{tab:hedonic}` | `src/outputs/tables.py` | MISSING (pickle corrupt) |
| `docs/tables/triple_diff.tex` | `\ref{tab:triple_diff}` | `src/outputs/tables.py` | MISSING (pickle corrupt) |
| `docs/tables/scm_results.tex` | `\ref{tab:scm}` | `src/outputs/scm_tables.py` | MISSING (GSynth/AugSCM incomplete) |
| `docs/tables/spatial_models.tex` | `\ref{tab:spatial}` | `src/outputs/spatial_tables.py` | MISSING |
| `docs/tables/effects.tex` | `\ref{tab:effects}` | `src/outputs/spatial_tables.py` | MISSING (degenerate SEs) |
| `figures/event_study.pdf` | `\ref{fig:event_study}` | `src/outputs/tables.py` | EXISTS but all-zero estimates |
| `figures/lisa_map.pdf` | `\ref{fig:lisa}` | `src/outputs/spatial_plots.py` | MISSING |
| `figures/gwr_surface.pdf` | `\ref{fig:gwr}` | `src/outputs/spatial_plots.py` | MISSING |
| `figures/scm_gap.pdf` | `\ref{fig:scm_gap}` | (not yet in main.tex, needs adding) | MISSING |
| `figures/map_study_area.pdf` | (not yet in main.tex, needs adding) | custom geopandas/folium | MISSING |

**Bulk generation commands (run after all models produce valid results):**
```bash
python3 -c "from src.outputs.tables import generate_all_tables; generate_all_tables()" 2>/dev/null
python3 -c "from src.outputs.spatial_tables import generate_spatial_tables; generate_spatial_tables()" 2>/dev/null
python3 -c "from src.outputs.spatial_plots import generate_all_plots; generate_all_plots()" 2>/dev/null
```

**Compile the paper:**
```bash
cd /Users/noahkoikesmith/lahaina-climate-risk/paper
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

---

## Journal targeting

### Target 1: Journal of Urban Economics (JUE)
**Rationale:** Natural experiment studies of local housing market shocks are core JUE content. Direct methodological precedent: Bernstein et al. (2019) on sea-level risk (JFE, same method), Murphy & Schwartz (2022) Camp Fire. No peer-reviewed Lahaina paper published as of May 2026. The multi-method design (hedonic + DiD + SCM + spatial) matches the JUE standard for applied microeconometrics.
**Word limit:** ~12,000 words
**Submission system:** Elsevier Editorial Manager
**Expected turnaround:** 6–9 months to first decision
**Fit:** Direct match on hedonic methodology, disaster economics, and housing market focus
**Caution:** JUE referees will scrutinize sample size (N ≈ 2,636 transactions, 122 spatial parcels is thin). Expand to 5,000+ transactions before submitting.

### Target 2: Real Estate Economics (REE)
**Rationale:** Hedonic + spatial econometrics combination is the core REE methodology. REE publishes applied housing market papers with smaller N than top journals and is more tolerant of Hawaii-specific scope. The spatial Durbin / GWR component is a genuine methodological contribution at REE standards.
**Word limit:** ~10,000 words
**Submission system:** Wiley ScholarOne
**Expected turnaround:** 4–6 months to first decision
**Fit:** Strong methodology match. The belief-update channel decomposition is novel relative to typical REE hedonic papers.

### Target 3: Journal of Environmental Economics and Management (JEEM)
**Rationale:** The climate risk capitalization framing and the belief-update channel finding position this squarely in JEEM's property value / environmental disamenity literature. Baldauf et al. (2020) and Bernstein et al. (2019) are both cited in JEEM-adjacent work. The WUI framing explicitly links to climate adaptation policy.
**Word limit:** ~10,000 words
**Submission system:** Elsevier
**Expected turnaround:** 5–8 months to first decision
**Fit:** The WUI/belief-update framing differentiates this from a generic fire-and-prices paper. The indirect spillover result (if significant) speaks directly to JEEM's interest in externality propagation.

### Journals to avoid at initial submission
- AER, QJE, JPE, Econometrica, ReStud: sample size too small; identification requires near-perfect parallel trends with thin post-fire transaction data; the spatial analysis does not add enough to clear the theory bar these journals require.
- Journal of Financial Economics (JFE): possible after JUE rejection if belief-update channel is the paper's strongest result (Bernstein et al. 2019 published the sea-level paper there), but JFE expects a finance mechanism story.
- Consider an NBER working paper before journal submission if the results are strong — this increases citation pickup and signals quality to referees.

---

## Final submission checklist

```
PAPER CONTENT
[ ] All [TBD] replaced with actual estimates
[ ] All [Author TBD] replaced with real author name, affiliation, and email
[ ] Abstract revised to include all quantitative results and trimmed to ≤ 150 words
[ ] Paper total word count within target journal limit
[ ] Introduction includes headline result number and comparison to literature
[ ] All tables cited in text with \ref{}
[ ] All figures cited in text with \ref{}
[ ] Figure for SCM gap series added to paper (currently not in main.tex)
[ ] Figure for study area map added to paper (recommended; currently absent)
[ ] Conclusion section updated with all estimated numbers (remove all [TBD])
[ ] Acknowledgments section added before references

TABLES AND FIGURES
[ ] Table 1: Summary statistics by treatment band — docs/tables/summary_stats.tex
[ ] Table 2: Hedonic estimates (treatment bands, WUI, post interactions) — docs/tables/hedonic.tex
[ ] Table 3: Triple-difference decomposition — docs/tables/triple_diff.tex
[ ] Table 4: SCM model comparison (ADH, GSynth, AugSCM) — docs/tables/scm_results.tex
[ ] Table 5: SAR/SEM/SDM comparison with LR test — docs/tables/spatial_models.tex
[ ] Table 6: LeSage-Pace direct/indirect/total effects — docs/tables/effects.tex
[ ] Figure 1: Map of study area with fire perimeter and parcel treatment bands — figures/map_study_area.pdf
[ ] Figure 2: Event-study plot (C&S, non-degenerate) — figures/event_study.pdf
[ ] Figure 3: SCM gap series with placebo distribution — figures/scm_gap.pdf
[ ] Figure 4: LISA cluster map (after rerunning on hedonic residuals) — figures/lisa_map.pdf
[ ] Figure 5: GWR coefficient surface (after sample expansion) — figures/gwr_surface.pdf
[ ] All figures saved at print resolution (≥ 300 dpi for raster; prefer vector PDF)

BIBLIOGRAPHY (paper/references.bib)
[ ] CliffOrd1981 entry type changed from @article to @book (currently malformed)
[ ] Fotheringham2002 entry type changed from @article to @book (currently malformed)
[ ] Murphy & Schwartz (2022) Camp Fire entry added if cited in introduction
[ ] Sutter & Poitras (2010) added if cited
[ ] Abadie2015 either cited in text or removed from bib
[ ] Kousky2018 either cited in text or removed from bib
[ ] All DOIs verified accessible
[ ] All \cite{} keys in main.tex have matching entries in references.bib (verify with: bibtex main)

DATA AND REPLICATION
[ ] Transaction data provenance documented: confirm maui_assessor.csv source (Bureau of Conveyances or title vendor)
[ ] Data availability statement added to paper (§A.1 or footnote 1)
[ ] .env.example updated with all required API keys (FRED, Census, etc.)
[ ] README.md updated with data acquisition instructions for verified transaction data
[ ] Replication package assembled: code + data dictionary + README
[ ] No hardcoded API keys in any committed file
[ ] Snakemake DAG runs end-to-end on verified data producing non-degenerate results

RESULTS VALIDATION (before writing)
[ ] C&S ATT is non-zero and statistically significant (event_study.csv has real estimates)
[ ] Parallel-trends test p-value is not NaN
[ ] Hedonic pickle loads without error; treatment coefficients are present in output table
[ ] Triple-diff SE is finite; WUI interaction coefficient is non-zero
[ ] GSynth and AugSCM post-period RMSPE are computed (not NaN)
[ ] SCM permutation p-value ≤ 0.10 (currently 0.155 — needs donor pool expansion)
[ ] Global Moran's I is computed on hedonic residuals (not raw price change)
[ ] Spatial model parameters are positive (not negative, which signals noise on 122 obs)
[ ] LeSage-Pace SEs are finite and plausible (not 4×10⁻⁷)
[ ] GWR bandwidth is less than the study area diameter (~15 km), not 49.7 km

SUBMISSION MECHANICS
[ ] JEL codes confirmed: R31 (Housing), Q54 (Climate), C21 (Cross-section), C23 (Panel)
[ ] Keywords finalized: 5–7 terms matching target journal style
[ ] Cover letter drafted (1 page: motivation, contribution, no prior submission)
[ ] Conflict of interest statement prepared (none expected)
[ ] Blinded version prepared if target journal uses double-blind review (JUE does; REE does not)
[ ] PDF compiles without LaTeX errors or missing reference warnings
```

---

## Writing sequence (after all results are valid)

**Day 1:** Fill in all numbers in §5 (Results). This is mechanical — copy estimates directly from result files listed above. Do not write prose yet.

**Day 2:** Write §5 prose around the numbers. Focus on: what the number says, its sign and magnitude, comparison to the literature, and what it implies for the next sub-result. Write Conclusion (replace all [TBD] with real values; add one paragraph on policy implications if not already there).

**Day 3:** Update §2.1 (Data) with real row counts, parcel counts, date ranges, and price ranges. Generate all tables and figures. Verify all \ref{} labels resolve.

**Day 4:** Add headline result to Introduction (one sentence after the three research questions). Polish Abstract to ≤ 150 words. Run spell-check. Compile full PDF and read once from cover to cover.

**Day 5:** Fix any remaining issues. Verify bibliography. Submit to target journal or post as working paper.

---

## Quick reference: result file → paper location mapping

| Result file | Paper location | Key quantity |
|---|---|---|
| `results/att_gt.pkl` | Abstract, §5.3, Conclusion | ATT point estimate, 95% CI |
| `results/event_study.csv` | §5.3, Figure 2 | Event-study ATT by month |
| `results/parallel_trends_test.json` | §3.1, §5.3 | Pre-trend p-value |
| `results/hedonic_table.csv` | §5.2, Table 2 | Distance gradient, post coefficient, R² |
| `results/decomposition.csv` | Abstract, §5.4, Table 3, Conclusion | Belief-update channel magnitude |
| `results/inference/p_values.json` | Abstract, §5.5 | SCM permutation p-value |
| `results/scm/adh_results.pkl` | §5.5, Table 4 | RMSPE ratio, donor weights |
| `results/scm/model_comparison.csv` | §5.5, Table 4 | ADH vs. GSynth vs. AugSCM |
| `results/esda/global_morans.json` | §5.6 | Moran's I, z, p |
| `results/esda/cluster_labels.parquet` | §5.6, Figure 4 | HH/LL/HL/LH counts |
| `results/spatial/nesting_tests.json` | §5.7, Table 5 | LR test, AIC comparison |
| `results/spatial/lesage_pace_effects.parquet` | Abstract, §5.8, Table 6, Conclusion | Direct, indirect, total effects |
| `results/gwr/optimal_bandwidth.json` | §5.9, Figure 5 | h* in km |
| `results/gwr/gwr_surface.parquet` | §5.9, Figure 5 | Local beta coefficients |
