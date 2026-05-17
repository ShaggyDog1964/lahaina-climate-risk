# Lahaina Climate-Risk: Roadmap to Submittable Paper
## Synthesized from: RESEARCH_ASSESSMENT.md, NEXT_STEPS_DATA.md, NEXT_STEPS_ANALYSIS.md, NEXT_STEPS_PAPER.md
## Prepared: 2026-05-16

---

## Executive Summary

The project is structurally sound and the research design is publishable. The pipeline runs
end-to-end and produces output files at every stage. **The single blocking problem is the
transaction data:** `maui_assessor.csv` has a single zoning code across all 2,636
transactions, which is inconsistent with any real multi-zoning Hawaiian residential market.
Every downstream result — hedonic estimates, DiD, spatial autocorrelation, GWR — is
unreliable until this is resolved.

The good news: the fire perimeter, WUI shapefile, FHFA/Zillow/Census data, and code
infrastructure are all real and correct. Once verified transaction data lands, the remaining
pipeline and paper-writing work is tractable in 8–10 weeks.

**Do not write any more code until the data question is resolved.** Every hour spent on
the pipeline is wasted if the input data cannot be verified.

---

## Critical Path

```
[Weeks 1–2]  Obtain verified deed transfer data (BOC or ATTOM)
      |
[Week 2]     Verify + assemble panel; apply 3 code fixes
      |
[Weeks 3–4]  Re-run Phase 1 → Phase 2 → Phase 3 pipeline
      |
[Week 5]     Validate results; decision gates
      |
[Weeks 6–8]  Fill paper, generate tables/figures, submit
```

The SCM donor pool expansion is a parallel workstream that can happen anytime in
Weeks 1–4, independently of the transaction data resolution.

---

## Week 1–2: Data Acquisition

**Owner:** Researcher. **Blocker for everything else.**

### Option A — Hawaii Bureau of Conveyances (Free, 2–4 weeks)

Contact immediately. No code required.

```
Email: BOC@hawaii.gov  |  Phone: (808) 587-0147
Request: "Maui County residential deed transfers, January 2018 – June 2026.
         Fields: TMK, sale date, consideration amount, instrument type.
         Residential arm's-length sales only."
```

The BOC publishes quarterly extracts under Hawaii's open data initiative. Turnaround
is typically 2–3 weeks for a custom pull.

### Option B — ATTOM Data Solutions (Paid, ~$2–5K, 3–5 business days)

Faster if budget is available. Email: solutions@attomdata.com. Request "Maui County,
Hawaii deed transfer extract, 2018–2026, with TMK/APN identifiers."

See `docs/NEXT_STEPS_DATA.md` for full contact details, verification snippets, and
the data assembly sequence (join to `pardat26.txt` assessor roll + shapefile).

### Verification before proceeding

```python
import pandas as pd
df = pd.read_csv("boc_maui_transfers.csv")
assert df["zoning"].nunique() > 5    # passes if real data
assert len(df) >= 5000               # minimum for hedonic with block FE
assert df["sale_date"].lt("2023-08-08").any()
assert df["sale_date"].gt("2023-08-08").any()
```

If this fails → the data is still problematic. Do not proceed.

---

## Week 2: Panel Assembly + Code Fixes

Once verified data arrives, three targeted code fixes are needed before re-running
the pipeline. These are the only code changes required.

### Fix 1 — Add `treated` binary column (15 minutes)

The C&S DiD estimator requires a binary `treated` column. The panel currently only has
`treatment_band`. Add it in `src/spatial/panel_builder.py` after distance bands are assigned:

```python
df["treated"] = (df["treatment_band"].isin(["0-2km", "2-5km"])).astype(int)
```

See `docs/NEXT_STEPS_ANALYSIS.md` §Step A2 for the exact fix location and verification.

### Fix 2 — Add treatment interaction terms to hedonic model (30 minutes)

The hedonic model currently has no `post × treatment_band` interaction. Without this,
there is no treatment effect estimate in the output table. Add to `src/models/hedonic.py`:

```python
for band in ["0-2km", "2-5km", "5-10km"]:
    df[f"post_x_{band}"] = df["post"] * (df["treatment_band"] == band).astype(int)
```

See `docs/NEXT_STEPS_ANALYSIS.md` §Code Fix 2 for the full context.

### Fix 3 — Pass hedonic residuals to Phase 3 (1 hour)

Currently `y_residual = NaN` for all 122 spatial observations, so Moran's I and
SAR/SEM/SDM run on raw price change (wrong variable). Fix:

1. At end of `src/models/hedonic.py`, write `results/hedonic_residuals.parquet`
   with `(parcel_id, year_month, hedonic_resid)`.
2. In `src/spatial_models/outcome.py`, load from `hedonic_residuals.parquet` to populate
   `y_residual` instead of attempting to read `att_gt.pkl`.
3. Add `results/hedonic_residuals.parquet` as input to the `build_spatial_outcome`
   Snakefile rule.

See `docs/NEXT_STEPS_ANALYSIS.md` §Code Fix 3 for the exact changes.

### Panel assembly

```bash
cd /Users/noahkoikesmith/lahaina-climate-risk

# 1. Replace maui_assessor.csv:
cp data/raw/parcels/maui_assessor.csv data/raw/parcels/maui_assessor_ORIGINAL.csv
python scripts/assemble_parcels.py \
    --deed data/raw/boc_maui_transfers.csv \
    --assessor "data/raw/Maui Real Property Assessment Roll/pardat26.txt" \
    --shapefile "data/raw/Maui Parcel Shapefile.shp/" \
    --output data/raw/parcels/maui_assessor.csv

# 2. Wipe stale results:
rm -f results/hedonic_results.pkl results/hedonic_table.csv
rm -f results/att_gt.pkl results/event_study.csv
rm -f results/parallel_trends_test.json
rm -f results/decomposition.csv results/triple_diff_results.pkl
rm -f data/final/panel.parquet data/interim/spatial/price_change.parquet
rm -f results/spatial/*.pkl results/spatial/*.parquet results/spatial/*.json
rm -f results/gwr/*.json results/gwr/*.pkl
```

---

## Week 3: Phase 1 Re-run + Validation

**Target:** Non-degenerate hedonic, DiD, and triple-diff results.

```bash
snakemake data/final/panel.parquet --cores 4 --forcerun
# [Verify: len > 1000, zoning.nunique() > 5, both pre and post obs]

snakemake results/hedonic_results.pkl results/hedonic_table.csv --cores 4 --forcerun
# [Verify: R² in [0.3, 0.8], treatment coefficients present]

snakemake results/att_gt.pkl results/event_study.csv --cores 4 --forcerun
# [Verify: ATT std > 0.001, pre-period ATTs near zero, post-period ATT negative]

snakemake results/triple_diff_results.pkl results/decomposition.csv --cores 4 --forcerun
# [Verify: WUI coef != 0, finite SEs]

snakemake results/parallel_trends_test.json figures/event_study.pdf --cores 4 --forcerun
# [Verify: p_value > 0.10, figure shows pre-period flatness]
```

**Phase 1 decision gate:**

| Outcome | Action |
|---|---|
| ATT < 0, p < 0.05, pre-trends pass | Proceed to Phase 3 immediately |
| ATT < 0 but p 0.05–0.15 (thin market) | Report with caveat; note low power; Phase 2 provides independent identification |
| ATT ≈ 0 on verified data | Re-examine treatment definition and panel construction; do not proceed to writing |

---

## Week 3 (parallel): Phase 2 Fix + Re-run

Phase 2 does not depend on Phase 1 hedonic residuals. Run in parallel.

### GSynth and AugSCM fix (30 minutes)

Both models currently produce NaN for `post_rmspe`. Fix by computing it from the
gap series after fitting. See `docs/NEXT_STEPS_ANALYSIS.md` §Code Fix 4.

### Donor pool expansion (optional, increases statistical power)

Current 58 Hawaii ZIPs yield minimum permutation p = 1/59 = 0.017. With p = 0.155,
the null is not rejected. Expand to 100+ donors by adding mainland resort markets
(Malibu, Santa Barbara, Bend, Sedona) — all have FHFA ZIP HPI series. See
`docs/NEXT_STEPS_DATA.md` §Donor Pool Expansion.

```bash
snakemake data/interim/zip_panel.parquet --cores 4 --forcerun
snakemake data/interim/donor_pool.parquet --cores 4 --forcerun
snakemake results/scm/adh_results.pkl results/scm/gsynth_results.pkl \
          results/scm/augsynth_results.pkl --cores 8 --forcerun
snakemake results/inference/p_values.json results/inference/stability_score.json \
          --cores 4 --forcerun
```

**Phase 2 decision gate:**

| Outcome | Action |
|---|---|
| p ≤ 0.05 with expanded donor pool | SCM is primary corroborating evidence — report prominently |
| p 0.05–0.10 | Report as "suggestive" — note limited power explicitly |
| p > 0.10 | Report the RMSPE ratio (3.06) honestly; frame Phase 1 DiD as primary identification |

---

## Week 4: Phase 3 Re-run

Phase 3 must run AFTER Phase 1 produces valid hedonic residuals (Fix 3 applied).

```bash
snakemake data/interim/spatial/price_change.parquet --cores 4 --forcerun
# [Verify: y_residual NaN fraction < 5%]

snakemake data/interim/spatial/weights_knn.pkl \
          data/interim/spatial/eigenvalues_knn.npy --cores 4 --forcerun

snakemake results/esda/global_morans.json \
          results/esda/lisa_stats.parquet --cores 4 --forcerun
# [Verify: Moran's I now on residuals, not raw price change]

snakemake results/spatial/sar_results.pkl results/spatial/sem_results.pkl \
          results/spatial/sdm_results.pkl --cores 4 --forcerun

snakemake results/spatial/lesage_pace_effects.parquet \
          results/spatial/nesting_tests.json --cores 4 --forcerun

snakemake results/gwr/optimal_bandwidth.json --cores 4 --forcerun  # ~45 min
snakemake results/gwr/gwr_surface.parquet --cores 4 --forcerun
```

**Phase 3 decision gate — Moran's I on hedonic residuals:**

| Outcome | Action |
|---|---|
| I > 0.05, p < 0.05 | Full spatial analysis as written; report SAR/SEM/SDM as primary |
| I ≤ 0.05 or p > 0.10 | Move SAR/SEM/SDM to appendix; use "robustness check" framing; report null as valid finding |

**Phase 3 decision gate — GWR bandwidth:**

| Outcome | Action |
|---|---|
| h* < 20 km | GWR produces local variation; report as written |
| h* > 20 km | Force h* = 5 km fixed bandwidth and rerun; report as sensitivity analysis |

---

## Week 5: Results Validation + Figure Generation

Run the final results check before writing any prose:

```bash
python - <<'EOF'
import os, pandas as pd, json, pickle, math

checks = [
    ("Panel", "data/final/panel.parquet"),
    ("Hedonic table", "results/hedonic_table.csv"),
    ("Event study", "results/event_study.csv"),
    ("Parallel trends", "results/parallel_trends_test.json"),
    ("Decomposition", "results/decomposition.csv"),
    ("ADH SCM", "results/scm/adh_results.pkl"),
    ("Model comparison", "results/scm/model_comparison.csv"),
    ("p-values", "results/inference/p_values.json"),
    ("Global Moran's I", "results/esda/global_morans.json"),
    ("LISA stats", "results/esda/lisa_stats.parquet"),
    ("Nesting tests", "results/spatial/nesting_tests.json"),
    ("LeSage-Pace", "results/spatial/lesage_pace_effects.parquet"),
    ("GWR bandwidth", "results/gwr/optimal_bandwidth.json"),
    ("GWR surface", "results/gwr/gwr_surface.parquet"),
]
for name, path in checks:
    print("OK  " if os.path.exists(path) else "MISSING  ", name, path)

# Non-degenerate checks
try:
    es = pd.read_csv("results/event_study.csv")
    print("Event study ATT range:", round(es.iloc[:,1].min(), 4), "to", round(es.iloc[:,1].max(), 4))
    assert es.iloc[:,1].std() > 0.001, "DEGENERATE: all ATT = 0"
except Exception as e:
    print("Event study check failed:", e)

try:
    pv = json.load(open("results/inference/p_values.json"))
    print("SCM p-value:", pv.get("p_value"), "ratio:", pv.get("rmspe_ratio"))
except Exception as e:
    print("p-values check failed:", e)

try:
    mi = json.load(open("results/esda/global_morans.json"))
    print("Moran's I:", mi.get("I"), "p:", mi.get("p_value_permutation", mi.get("p_value")))
except Exception as e:
    print("Moran's I check failed:", e)

try:
    lp = pd.read_parquet("results/spatial/lesage_pace_effects.parquet")
    se_max = lp.filter(like="_se").max().max()
    print("LeSage-Pace max SE:", se_max, "— degenerate?" if se_max < 1e-4 else "— OK")
except Exception as e:
    print("LeSage-Pace check failed:", e)

try:
    bw = json.load(open("results/gwr/optimal_bandwidth.json"))
    print("GWR bandwidth:", bw.get("bandwidth_km"), "km — too large?" if bw.get("bandwidth_km", 0) > 20 else "— OK")
except Exception as e:
    print("GWR bandwidth check failed:", e)
EOF
```

Generate all tables and figures:

```bash
python3 -c "from src.outputs.tables import generate_all_tables; generate_all_tables()" 2>/dev/null
python3 -c "from src.outputs.spatial_tables import generate_spatial_tables; generate_spatial_tables()" 2>/dev/null
python3 -c "from src.outputs.spatial_plots import generate_all_plots; generate_all_plots()" 2>/dev/null

# Compile paper to check for missing references:
cd /Users/noahkoikesmith/lahaina-climate-risk/paper
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

---

## Weeks 6–7: Write the Paper

See `docs/NEXT_STEPS_PAPER.md` for the complete section-by-section guide with:
- Exact source files for each quantitative placeholder
- Templates for each results subsection
- Handling guidance for null/borderline results (null Moran's I, p = 0.155 SCM)

**Writing sequence (4 focused days after results are valid):**

| Day | Task |
|---|---|
| Day 1 | Fill in all §5 (Results) numbers mechanically from result files |
| Day 2 | Write §5 prose; update Conclusion with real numbers |
| Day 3 | Update §2.1 Data with row counts; generate all tables/figures; verify \ref{} labels |
| Day 4 | Add headline number to Introduction; polish Abstract (≤ 150 words); read cover-to-cover |

**Pre-writing blockers (do not write until ALL pass):**
- `event_study.csv` ATT std > 0.001 (non-degenerate)
- `parallel_trends_test.json` p_value is not NaN
- `results/hedonic_results.pkl` loads without error and has treatment coefficients
- `results/decomposition.csv` has finite SEs
- `results/spatial/lesage_pace_effects.parquet` SEs are not 4e-7
- `results/gwr/optimal_bandwidth.json` bandwidth_km < 20

---

## Week 8: Polish + Submit

### Bibliography fixes required before submission

Two BibTeX entries are malformed (see `docs/NEXT_STEPS_PAPER.md` §BibTeX verification):

```bibtex
% Fix 1: CliffOrd1981 — change @article to @book
@book{CliffOrd1981,
  author    = {Cliff, Andrew D. and Ord, J. Keith},
  title     = {Spatial Processes: Models and Applications},
  publisher = {Pion},
  year      = {1981}
}

% Fix 2: Fotheringham2002 — change @article to @book
@book{Fotheringham2002,
  author    = {Fotheringham, A. Stewart and Brunsdon, Chris and Charlton, Martin},
  title     = {Geographically Weighted Regression: The Analysis of Spatially Varying Relationships},
  publisher = {Wiley},
  year      = {2002}
}
```

Also: `Abadie2015` and `Kousky2018` are in the bib but not cited — either add citations
in the introduction or remove from `references.bib`.

### Target journal

**Primary: Journal of Urban Economics (JUE)**
- Elsevier Editorial Manager
- Word limit ~12,000 words
- Expected turnaround: 6–9 months
- Requires N ≥ 5,000 transactions (expand from ~2,636 with real deed data)

**Backup: Real Estate Economics (REE)**
- More tolerant of smaller N; strong methodology match
- Wiley ScholarOne

See `docs/NEXT_STEPS_PAPER.md` §Journal targeting for full rationale.

### Final submission checklist

Before clicking Submit, verify the complete checklist in `docs/NEXT_STEPS_PAPER.md`
§Final submission checklist. Key items:

```
[ ] All [TBD] replaced with actual estimates
[ ] Author name, affiliation, email filled in (paper/main.tex lines 55–57)
[ ] All 5 figures and 6 tables compiled without LaTeX errors
[ ] CliffOrd1981 and Fotheringham2002 bib entries corrected to @book type
[ ] Blinded version prepared (JUE uses double-blind review)
[ ] Data availability statement added
[ ] Replication package assembled (code + data dictionary)
[ ] PDF compiles without warnings or missing references
```

---

## Summary Table: All Required Actions

| # | Action | Effort | Week | Dependency | Source doc |
|---|---|---|---|---|---|
| D1 | Contact Hawaii BOC for deed transfers | 1 hour | 1 | None | NEXT_STEPS_DATA.md |
| D2 | Verify received deed data (zoning, N, date range) | 2 hours | 2 | D1 | NEXT_STEPS_DATA.md |
| D3 | Assemble verified `maui_assessor.csv` from BOC + pardat26 + shapefile | 4 hours | 2 | D2 | NEXT_STEPS_DATA.md |
| A1 | Code fix: add `treated` binary column to panel_builder.py | 15 min | 2 | D2 | NEXT_STEPS_ANALYSIS.md |
| A2 | Code fix: add treatment interaction terms to hedonic model | 30 min | 2 | D2 | NEXT_STEPS_ANALYSIS.md |
| A3 | Code fix: write hedonic_residuals.parquet; update outcome.py and Snakefile | 1 hour | 2 | D2 | NEXT_STEPS_ANALYSIS.md |
| A4 | Code fix: GSynth and AugSCM post_rmspe computation | 30 min | 3 | None | NEXT_STEPS_ANALYSIS.md |
| A5 | Wipe stale results; re-run Phase 1 | 30 min + runtime | 3 | D3, A1, A2 | NEXT_STEPS_ANALYSIS.md |
| A6 | Validate Phase 1 results (non-degenerate event study, finite SEs) | 1 hour | 3 | A5 | NEXT_STEPS_ANALYSIS.md |
| A7 | Re-run Phase 2 (ADH, GSynth, AugSCM, placebos) | 30 min + runtime | 3 | A4 | NEXT_STEPS_ANALYSIS.md |
| A8 | Apply Phase 3 decision gates; re-run Phase 3 | 30 min + runtime | 4 | A5, A3 | NEXT_STEPS_ANALYSIS.md |
| D4 | (Optional) Expand SCM donor pool to mainland resort ZIPs | 2 hours | 3 | None | NEXT_STEPS_DATA.md |
| P1 | Generate all tables and figures | 2 hours | 5 | A6, A8 | NEXT_STEPS_PAPER.md |
| P2 | Fill in §5 (Results) numbers mechanically | 4 hours | 6 | P1 | NEXT_STEPS_PAPER.md |
| P3 | Write §5 prose + update Conclusion | 4 hours | 6 | P2 | NEXT_STEPS_PAPER.md |
| P4 | Update §2.1 Data with real counts; add headline to Introduction | 2 hours | 7 | P3 | NEXT_STEPS_PAPER.md |
| P5 | Fix CliffOrd1981 + Fotheringham2002 bib entries | 15 min | 7 | None | NEXT_STEPS_PAPER.md |
| P6 | Polish Abstract (≤150 words); read cover-to-cover | 2 hours | 7 | P4 | NEXT_STEPS_PAPER.md |
| P7 | Prepare blinded version; assemble replication package | 4 hours | 8 | P6 | NEXT_STEPS_PAPER.md |
| P8 | Submit to JUE | 1 hour | 8 | P7 | NEXT_STEPS_PAPER.md |

**Total effort estimate (excluding waiting for data):** ~35 hours of researcher time over 8 weeks.
**Estimated time to submission:** 10–16 weeks depending on BOC response time.

---

## Reference Documents

| Document | Contents |
|---|---|
| `docs/RESEARCH_ASSESSMENT.md` | Full audit of current result files; what is degenerate and why |
| `docs/NEXT_STEPS_DATA.md` | Data acquisition guide: BOC contact info, ATTOM option, assembly sequence, verification |
| `docs/NEXT_STEPS_ANALYSIS.md` | Step-by-step Snakemake execution with verification commands and decision gates |
| `docs/NEXT_STEPS_PAPER.md` | Section-by-section paper writing guide with templates, source-file mapping, bibliography fixes, journal targeting, full submission checklist |
