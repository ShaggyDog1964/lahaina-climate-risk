# Analysis Pipeline Execution Guide

## Prerequisites
- Real parcel transaction data at `data/raw/parcels/maui_assessor.csv` with >1 unique zoning code
- All other raw data present (verify with Step 0)

## Step 0 — Pre-flight data check
```bash
python3 -c "
import pandas as pd, os
checks = {
    'parcels': 'data/raw/parcels/maui_assessor.csv',
    'zhvi': 'data/raw/zillow/zhvi_zip.csv',
    'fhfa': 'data/raw/fhfa/hpi_zip.parquet',
    'census': 'data/raw/census/acs_zip_2022.parquet',
    'fire': 'data/raw/fire/lahaina_perimeter.geojson',
    'wui': 'data/raw/wui/wui_conus.shp',
}
all_ok = True
for name, path in checks.items():
    exists = os.path.exists(path)
    if exists and path.endswith('.csv'):
        df = pd.read_csv(path, nrows=5)
        n_zoning = df['zoning'].nunique() if 'zoning' in df.columns else '?'
        print(f'OK {name}: {path} (zoning unique vals: {n_zoning})')
    elif exists:
        print(f'OK {name}: {path}')
    else:
        print(f'MISSING {name}: {path}')
        all_ok = False
if not all_ok:
    print('FIX MISSING FILES BEFORE PROCEEDING')
"
```

---

## PHASE 1 EXECUTION

### Step A1 — Build parcel panel

The full build chain is: `load_parcels` -> `join_wui` -> `build_h3` -> `assign_bands` -> `build_panel`.
Run all at once targeting the final output:

```bash
snakemake data/final/panel.parquet --cores 4 --forcerun
```

**Runtime:** ~5 minutes
**Verify:**
```bash
python3 -c "
import pandas as pd
panel = pd.read_parquet('data/final/panel.parquet')
print('Shape:', panel.shape)
print('Parcels:', panel['parcel_id'].nunique())
print('Columns:', panel.columns.tolist())
print('Zoning unique:', panel['zoning'].nunique() if 'zoning' in panel.columns else 'N/A')
pre = panel[panel['post']==0]
post = panel[panel['post']==1]
print('Pre-fire obs:', len(pre), '| Post-fire obs:', len(post))
assert len(panel) > 1000, f'Panel too small: {len(panel)}'
assert panel['log_price'].isna().mean() < 0.05, 'Too many missing prices'
print('Has treated col:', 'treated' in panel.columns)
print('treatment_band unique:', panel['treatment_band'].unique() if 'treatment_band' in panel.columns else 'N/A')
print('PANEL OK')
"
```

**Credible result:** >=1000 rows, >=200 parcels, date range spans 2019-2024, both pre and post obs present.
**Suspicious:** Exactly N rows, all same zoning, no variation in dist_to_fire_km.
**If fails:** Check that `data/raw/parcels/maui_assessor.csv` exists and that `src/ingest/parcel.py::load_maui_parcels()` can read it. The rule calls `load_maui_parcels('{input}')` directly.

---

### Step A2 — Add `treated` binary column (CRITICAL FIX)

The panel currently has `treatment_band` (distance band string) and `post` but **no binary `treated` column**. The Callaway-Sant'Anna DiD estimator (`src/models/did_cs.py`) requires a `treated` column. Add it before running hedonic or DiD.

Check first whether it already exists after the panel build:
```bash
python3 -c "
import pandas as pd
panel = pd.read_parquet('data/final/panel.parquet')
if 'treated' in panel.columns:
    print('treated already present:', panel['treated'].value_counts().to_dict())
else:
    print('treated MISSING — run fix below')
    print('treatment_band values:', panel['treatment_band'].unique() if 'treatment_band' in panel.columns else 'MISSING')
"
```

If missing, add it:
```bash
python3 -c "
import pandas as pd
panel = pd.read_parquet('data/final/panel.parquet')
# Treated = within 5km of fire perimeter (bands 0-2km and 2-5km)
panel['treated'] = panel['treatment_band'].isin(['0-2km', '2-5km']).astype(int)
panel.to_parquet('data/final/panel.parquet', index=False)
print('Added treated column.')
print('Treated obs:', panel['treated'].sum())
print('Treated parcels:', panel[panel['treated']==1]['parcel_id'].nunique())
print('Control parcels:', panel[panel['treated']==0]['parcel_id'].nunique())
"
```

**Important:** The `build_panel` Snakemake rule calls `src/spatial/panel_builder.py::build_panel()`. If you re-run `snakemake data/final/panel.parquet --forcerun`, it will overwrite the file and the manually added `treated` column will be lost. Either patch `panel_builder.py` to compute `treated` from `treatment_band`, or run the fix script immediately before the hedonic/DiD rules without re-running `build_panel`.

---

### Step A3 — Run hedonic model

```bash
snakemake results/hedonic_results.pkl results/hedonic_table.csv --cores 4 --forcerun
```

**Runtime:** ~3 minutes
**Verify:**
```bash
python3 -c "
import pickle, pandas as pd
with open('results/hedonic_results.pkl', 'rb') as f:
    model = pickle.load(f)
print('Model type:', type(model).__name__)
print('R2:', round(model.rsquared, 4) if hasattr(model, 'rsquared') else 'N/A')
table = pd.read_csv('results/hedonic_table.csv')
print('Coef table rows:', len(table))
print('First column name:', table.columns[0])
print('Coef names (first 10):', table.iloc[:, 0].tolist()[:10])
for term in ['dist_to_fire', 'post', 'treated', 'treatment']:
    matches = table[table.iloc[:, 0].str.contains(term, case=False, na=False)]
    if len(matches):
        print(f'Found {term}:', matches.iloc[:, 1].values)
"
```

**Credible result:** R2 in [0.3, 0.8]; `dist_to_fire_km` coefficient negative; `post` coefficient present with finite SE.
**Suspicious:** R2 = 1.0 (overfit on synthetic data); all coefficients = 0; pickle fails to load.
**If pickle fails to load** (statsmodels serialization error):
```bash
pip install statsmodels --upgrade
snakemake results/hedonic_results.pkl --forcerun --cores 1
```

---

### Step A4 — Run Callaway-Sant'Anna DiD

The rule is `run_did_cs`. It calls `src/models/did_cs.py::CallawayAntaCSiD`. Output: `results/att_gt.pkl` and `results/event_study.csv`.

```bash
snakemake results/att_gt.pkl results/event_study.csv --cores 4 --forcerun
```

**Runtime:** ~5 minutes
**Verify:**
```bash
python3 -c "
import pandas as pd, pickle
es = pd.read_csv('results/event_study.csv')
print('Event study shape:', es.shape)
print('Columns:', es.columns.tolist())
print('ATT range:', round(es['att'].min(), 4), 'to', round(es['att'].max(), 4))
print('ATT std:', round(es['att'].std(), 6))
pre = es[es['event_time'] < 0]
post = es[es['event_time'] >= 0]
print('Pre-period ATT all zero?', (pre['att'] == 0).all())
assert es['att'].std() > 0.001, 'Event study still degenerate — all ATT = 0'
print('Post-fire mean ATT:', round(post['att'].mean(), 4))
sig = (post['att'].abs() / post['se'] > 1.96).any() if 'se' in post.columns else 'se column missing'
print('Any post-period significant:', sig)
"
```

**Publishable result:**
- Pre-period ATT values scatter around 0 (not all exactly 0.0)
- Post-period ATT < 0 (price fell near fire)
- Magnitude: -0.05 to -0.35 log points (-5% to -30%) at peak
- At least some post-period estimates with |ATT/SE| > 1.96

**If still all zeros** — the C&S estimator is silently failing. Diagnose:
```bash
python3 -c "
import pandas as pd
panel = pd.read_parquet('data/final/panel.parquet')
print('treated unique:', panel['treated'].unique() if 'treated' in panel.columns else 'MISSING')
print('post unique:', panel['post'].unique())
print('Treatment structure:')
print(panel.groupby(['treated', 'post']).size())
# C&S needs parcel_id, year (or time), treated, log_price at minimum
for col in ['parcel_id', 'treated', 'post', 'log_price']:
    print(f'  {col} present:', col in panel.columns)
"
```

---

### Step A5 — Run triple-difference

The rule is `run_triple_diff`. It calls `src/models/triple_diff.py::TripleDifference`.

```bash
snakemake results/triple_diff_results.pkl results/decomposition.csv --cores 4 --forcerun
```

**Runtime:** ~3 minutes
**Verify:**
```bash
python3 -c "
import pickle, pandas as pd
with open('results/triple_diff_results.pkl', 'rb') as f:
    model = pickle.load(f)
print('Model type:', type(model).__name__)
dc = pd.read_csv('results/decomposition.csv')
print('Decomposition:')
print(dc.to_string())
# Check WUI coefficient is not zero and has finite SE
if 'term' in dc.columns:
    wui_row = dc[dc['term'].str.contains('wui', case=False, na=False)]
    if len(wui_row):
        coef_val = wui_row.iloc[:, 1].values[0] if len(wui_row.columns) > 1 else None
        print('WUI coef:', coef_val)
        assert coef_val != 0.0, 'WUI coefficient still zero'
    else:
        print('WARNING: no WUI row found in decomposition — check term names')
import math
if 'se' in dc.columns:
    assert not any(math.isinf(x) for x in dc['se'].dropna()), 'Infinite SEs in decomposition'
print('Triple-diff OK')
"
```

**Credible result:**
- WUI interaction coefficient < non-WUI coefficient (belief-update channel)
- Finite standard errors on both interaction terms
- Belief-update estimate = WUI_coef - non-WUI_coef, should be negative

---

### Step A6 — Test parallel trends

The rule is `test_parallel`. It reads `results/event_study.csv` (output of `run_did_cs`) and writes `results/parallel_trends_test.json` and `figures/event_study.pdf`.

```bash
snakemake results/parallel_trends_test.json figures/event_study.pdf --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import json, math
with open('results/parallel_trends_test.json') as f: d = json.load(f)
print('Parallel trends result:', d)
assert d.get('p_value') is not None, 'p_value is None'
assert not math.isnan(float(d['p_value'])), 'p_value is NaN — event study was degenerate'
if d['p_value'] > 0.10:
    print('PARALLEL TRENDS OK: p =', d['p_value'])
else:
    print('PARALLEL TRENDS BORDERLINE: p =', d['p_value'], '— inspect pre-period event study plot')
"
```

**Credible result:** p > 0.10 (fail to reject parallel trends). Inspect `figures/event_study.pdf` visually: pre-period ATTs should lie near zero with overlapping confidence intervals.

---

## PHASE 2 EXECUTION

### Step B1 — Build zip panel

The rule is `build_zip_panel`. Inputs: `data/raw/zillow/zhvi_zip.csv` and `data/raw/census/acs_zip_2022.parquet`. If either is missing, run the fetch rules first:

```bash
snakemake data/raw/zillow/zhvi_zip.csv data/raw/census/acs_zip_2022.parquet --cores 4
snakemake data/interim/zip_panel.parquet --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import pandas as pd
zp = pd.read_parquet('data/interim/zip_panel.parquet')
print('Shape:', zp.shape)
print('Columns:', zp.columns.tolist())
print('zip_code dtype:', zp['zip_code'].dtype)
print('ZIPs:', zp['zip_code'].nunique())
print('Date range:', zp['year_month'].min() if 'year_month' in zp.columns else 'no year_month col', 'to', zp['year_month'].max() if 'year_month' in zp.columns else '')
print('Treated zip present:', '96761' in zp['zip_code'].astype(str).values)
assert zp['zip_code'].nunique() >= 8, 'Too few ZIPs for SCM'
print('ZIP PANEL OK')
"
```

**Note on zip_code dtype:** The `build_zip_panel` rule logs `zip_code dtype` explicitly. If it is int64 but the donor pool or SCM code expects str, you will get a merge KeyError downstream. Verify dtype matches across all Phase 2 parquet files.

---

### Step B2 — Build donor pool

The rule is `build_donor_pool`. Outputs: `data/interim/donor_pool.parquet` and `data/interim/covariate_matrix.npz`.

```bash
snakemake data/interim/donor_pool.parquet data/interim/covariate_matrix.npz --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import pandas as pd, numpy as np
dp = pd.read_parquet('data/interim/donor_pool.parquet')
print('Shape:', dp.shape)
print('Columns:', dp.columns.tolist())
n_donors = dp['zip_code'].nunique() if 'zip_code' in dp.columns else len(dp)
print('Donor ZIPs:', n_donors)
assert n_donors >= 8, f'Too few donors: {n_donors}. SCM is underpowered.'
cov = np.load('data/interim/covariate_matrix.npz', allow_pickle=True)
print('covariate_matrix keys:', list(cov.keys()))
print('X0 shape:', cov['X0'].shape, '| Y0_pre shape:', cov['Y0_pre'].shape)
print('DONOR POOL OK')
"
```

**Minimum viable:** 8 donor ZIPs. With fewer, permutation inference (58 placebos) is unreliable.
**If too few donors** — expand ZHVI coverage by checking pre-fire data completeness:
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('data/raw/zillow/zhvi_zip.csv')
pre_cols = [c for c in df.columns if any(y in c for y in ['2019', '2020', '2021', '2022', '2023'])]
complete = df[pre_cols].notna().all(axis=1)
print('ZIPs with complete 2019-2023 data:', complete.sum())
print('Total ZIPs in file:', len(df))
"
```

---

### Step B3 — Fit ADH SCM

The rule is `fit_adh_scm`. The treated ZIP is hardcoded as `'96761'` in the Snakefile. Output: `results/scm/adh_results.pkl` and `results/scm/adh_gap_series.parquet`.

```bash
snakemake results/scm/adh_results.pkl results/scm/adh_gap_series.parquet --cores 4 --forcerun
```

**Runtime:** ~10 minutes
**Verify:**
```bash
python3 -c "
import pickle
with open('results/scm/adh_results.pkl', 'rb') as f: adh = pickle.load(f)
print('pre_rmspe:', round(adh.pre_rmspe_, 4))
print('post_rmspe:', round(adh.post_rmspe_, 4) if adh.post_rmspe_ is not None else 'None — post not fitted yet')
print('is_post_fitted:', adh.is_post_fitted if hasattr(adh, 'is_post_fitted') else 'attr missing')
w = adh.w_
nonzero = [(i, round(float(w[i]), 3)) for i in range(len(w)) if float(w[i]) > 0.01]
print('Nonzero donor weights (index, weight):', nonzero)
assert adh.pre_rmspe_ < 0.05, f'Poor pre-period fit: RMSPE={adh.pre_rmspe_} — check donor pool quality'
print('ADH OK')
"
```

**Credible result:** pre_rmspe < 0.05, rmspe_ratio > 1.5, 2-5 donors with substantial weight.
**Note:** The `run_placebos` rule checks `adh.is_post_fitted` and raises `RuntimeError` if it is False (stale pickle). If this error appears, delete `results/scm/adh_results.pkl` and re-run `fit_adh_scm`.

---

### Step B4 — Fit GSynth and AugSCM

The rules are `fit_gsynth` and `fit_augsynth`. Note that `fit_gsynth` currently passes `Y0_pre` twice (for both pre and all-period arrays), which causes `post_rmspe` to be NaN. This is the known bug.

```bash
snakemake results/scm/gsynth_results.pkl results/scm/gsynth_gap_series.parquet \
          results/scm/augsynth_results.pkl results/scm/augsynth_gap_series.parquet \
          --cores 4 --forcerun
```

**Verify GSynth:**
```bash
python3 -c "
import pickle
with open('results/scm/gsynth_results.pkl', 'rb') as f: gs = pickle.load(f)
print('pre_rmspe:', round(gs.pre_rmspe_, 4) if hasattr(gs, 'pre_rmspe_') else 'attr missing')
post = gs.post_rmspe_ if hasattr(gs, 'post_rmspe_') else None
print('post_rmspe:', round(post, 4) if post is not None else 'None — BUG: Y0_all not passed post-period data')
"
```

**If GSynth post_rmspe is None:** The `fit_gsynth` Snakefile rule passes `Y0_pre` for both the pre and all-period `model.fit()` call (`model.fit(Y0_pre, Y1_pre, Y0_pre, Y1_pre, r=2)`). Fix by loading the full pivot and passing the complete `Y0_all`/`Y1_all` arrays (as done in `fit_adh_scm`). Until fixed, GSynth rows will show NaN in `model_comparison.csv`.

---

### Step B5 — Compare SCMs

The rule is `compare_scms`. It calls `src/scm/model_registry.py::ModelRegistry.compare_rmspe()`.

```bash
snakemake results/scm/model_comparison.csv --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('results/scm/model_comparison.csv')
print(df.to_string())
assert df['pre_rmspe'].notna().any(), 'All pre_rmspe are NaN'
missing_post = df['rmspe_ratio'].isna().sum()
if missing_post > 0:
    print(f'WARNING: {missing_post} models have NaN rmspe_ratio (incomplete post-period fit)')
"
```

---

### Step B6 — Permutation inference (in-space placebo)

The rule is `run_placebos`. Runs 58 placebo SCM fits (one per donor ZIP). Outputs: `results/inference/placebo_distribution.parquet` and `results/inference/p_values.json`.

```bash
snakemake results/inference/placebo_distribution.parquet results/inference/p_values.json --cores 4 --forcerun
```

**Runtime:** ~20 minutes
**Verify:**
```bash
python3 -c "
import json
with open('results/inference/p_values.json') as f: d = json.load(f)
print('p_value:', round(d['p_value'], 4))
print('rmspe_ratio:', round(d['rmspe_ratio'], 4))
print('pre_rmspe:', round(d['pre_rmspe'], 4))
print('post_rmspe:', round(d['post_rmspe'], 4))
if d['p_value'] > 0.10:
    print('NOTE: SCM not significant at 10% (p =', d['p_value'], '). Report honestly.')
    print('Consider: expand donor pool, verify treated ZIP price trajectory, check ZHVI coverage.')
else:
    print('SCM SIGNIFICANT at', d['p_value'])
"
```

**Current known result:** p = 0.155, rmspe_ratio = 3.06 (not significant at 10%). If the underlying data is unchanged, this result will reproduce identically. Report it honestly. Phase 1 DiD provides independent identification.

---

### Step B7 — LOO stability

The rule is `run_loo`. Outputs: `results/inference/loo_gaps.parquet` and `results/inference/stability_score.json`.

```bash
snakemake results/inference/loo_gaps.parquet results/inference/stability_score.json --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import json, pandas as pd
with open('results/inference/stability_score.json') as f: s = json.load(f)
print('Stability score:', s)
gaps = pd.read_parquet('results/inference/loo_gaps.parquet')
print('LOO gaps shape:', gaps.shape)
"
```

---

## PHASE 3 EXECUTION

### Step C0 — Critical prerequisite: Phase 1 -> Phase 3 linkage

Phase 3 spatial models run on `y_raw` (raw log-price change per parcel) and optionally `y_residual` (hedonic residual). The `build_spatial_outcome` rule (`src/spatial_models/outcome.py::build_price_change`) reads `data/final/panel.parquet` and `results/att_gt.pkl`.

The `y_residual` column is populated only if `results/att_gt.pkl` loads successfully **and** contains a DataFrame with columns `['parcel_id', 'residual']`. The current C&S implementation pickles `model._results` directly. Check the actual type:

```bash
python3 -c "
import pickle
with open('results/att_gt.pkl', 'rb') as f: att = pickle.load(f)
print('Type:', type(att))
if hasattr(att, 'columns'):
    print('Columns:', att.columns.tolist())
    print('Has residual col:', 'residual' in att.columns)
    print('Has parcel_id col:', 'parcel_id' in att.columns)
else:
    print('Not a DataFrame — y_residual will be NaN in price_change.parquet')
    print('Fix: ensure did_cs.py._results is a DataFrame with parcel_id and residual columns')
"
```

If `att_gt.pkl` is not a DataFrame with `parcel_id` and `residual`, the `build_price_change` function will log a warning and set `y_residual = NaN` for all parcels (this is the current state). For Phase 3 spatial models, `y_raw` is still usable (Moran's I and SAR/SEM/SDM all run on `y_raw` via `df['y_raw'].fillna(0).values`). Fix the residual linkage after Phase 1 is working.

Verify Phase 3 can run even with NaN residuals:
```bash
python3 -c "
import pandas as pd
if __import__('os').path.exists('data/interim/spatial/price_change.parquet'):
    pc = pd.read_parquet('data/interim/spatial/price_change.parquet')
    print('price_change shape:', pc.shape)
    print('y_raw null:', pc['y_raw'].isna().sum())
    print('y_residual null:', pc['y_residual'].isna().sum(), '(OK if Phase 1 broken)')
    print('y_raw mean:', round(pc['y_raw'].mean(), 4), 'std:', round(pc['y_raw'].std(), 4))
else:
    print('price_change.parquet not yet built')
"
```

---

### Step C1 — Build spatial outcome

The rule is `build_spatial_outcome`. Input: `data/final/panel.parquet`. Output: `data/interim/spatial/price_change.parquet`.

```bash
snakemake data/interim/spatial/price_change.parquet --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import pandas as pd
pc = pd.read_parquet('data/interim/spatial/price_change.parquet')
print('Shape:', pc.shape)
print('Columns:', pc.columns.tolist())
print('y_raw: mean=', round(pc['y_raw'].mean(), 4), 'std=', round(pc['y_raw'].std(), 4), 'null=', pc['y_raw'].isna().sum())
print('y_residual null:', pc['y_residual'].isna().sum(), 'of', len(pc))
assert pc['y_raw'].isna().sum() < len(pc) * 0.5, 'More than 50% of y_raw is NaN'
assert 'lat' in pc.columns and 'lon' in pc.columns, 'Missing lat/lon columns'
print('Lat range:', round(pc['lat'].min(), 3), 'to', round(pc['lat'].max(), 3))
print('Lon range:', round(pc['lon'].min(), 3), 'to', round(pc['lon'].max(), 3))
"
```

---

### Step C2 — Build spatial weights (Phase 3)

The rule is `build_weights_phase3`. Uses `src/spatial/weights_phase3.py::SpatialWeightsFactory`. KNN k=8 (from Snakefile config). Outputs: `data/interim/spatial/weights_knn.pkl`, `data/interim/spatial/weights_idw.pkl`, `data/interim/spatial/eigenvalues_knn.npy`.

```bash
snakemake data/interim/spatial/weights_knn.pkl data/interim/spatial/weights_idw.pkl data/interim/spatial/eigenvalues_knn.npy --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import pickle, numpy as np
with open('data/interim/spatial/weights_knn.pkl', 'rb') as f: w = pickle.load(f)
print('W type:', type(w))
import scipy.sparse as sp
W_dense = w if not sp.issparse(w) else None
# Check row standardization
try:
    from src.spatial.weights_phase3 import SpatialWeightsFactory
    factory = SpatialWeightsFactory()
    W_sparse = factory.to_sparse(w)
    row_sums = np.array(W_sparse.sum(axis=1)).flatten()
    print('W row sums min:', round(row_sums.min(), 4), 'max:', round(row_sums.max(), 4))
    print('Row-standardized (all sums ~1.0):', abs(row_sums - 1.0).max() < 0.01)
except Exception as e:
    print('Could not verify row standardization:', e)
eigs = np.load('data/interim/spatial/eigenvalues_knn.npy', allow_pickle=True)
print('Eigenvalues shape:', eigs.shape)
print('Eigenvalue range:', round(eigs.min(), 4), 'to', round(eigs.max(), 4))
"
```

**If rho or lambda is negative and large in magnitude** (Steps C4), verify here that row sums are all 1.0. Non-row-standardized W produces atypical spatial parameter estimates.

---

### Step C3 — Global Moran's I

The rule is `global_morans`. Runs on `y_raw` (not residuals — see known issue). Output: `results/esda/global_morans.json`.

```bash
snakemake results/esda/global_morans.json --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import json
with open('results/esda/global_morans.json') as f: d = json.load(f)
print('Moran I:', round(d['I'], 4))
print('z-score:', round(d.get('z_score', float('nan')), 4))
print('p-value (permutation):', round(d.get('p_value_permutation', d.get('p_value', float('nan'))), 4))
print('Full result:', d)
"
```

**Known issue:** The `global_morans` rule uses `y_raw` (`df['y_raw'].fillna(0).values`), not hedonic residuals. The current result (I = -0.003, p = 0.90) is computed on raw price changes. After Phase 1 is fixed, rerun with `y_residual` for the publishable Moran's I test.

**Publishable result:** I > 0.10, p < 0.05.
**If I is insignificant on real data:** Drop SAR/SEM/SDM as primary results. Move to appendix. Report: "We test for spatial autocorrelation in hedonic residuals and find no significant clustering (I = X, p = Y), indicating the hedonic model adequately absorbs spatial structure." This is a valid finding, not a failure.

---

### Step C4 — LISA clusters

The rule is `local_morans`. Outputs: `results/esda/lisa_stats.parquet` and `results/esda/cluster_labels.parquet`.

```bash
snakemake results/esda/lisa_stats.parquet results/esda/cluster_labels.parquet --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import pandas as pd
labels = pd.read_parquet('results/esda/cluster_labels.parquet')
print('LISA labels shape:', labels.shape)
print('cluster_label value counts:')
print(labels['cluster_label'].value_counts())
# Expected: HH, HL, LH, LL, NS quadrant labels
stats = pd.read_parquet('results/esda/lisa_stats.parquet')
print('LISA stats shape:', stats.shape)
print('LISA stats columns:', stats.columns.tolist())
"
```

---

### Step C5 — SAR, SEM, SDM

Rules: `fit_sar`, `fit_sem`, `fit_sdm`. All use `y_raw` and `dist_to_fire_km` as the only covariate (plus intercept). `fit_sdm` depends on `results/spatial/sar_results.pkl` (for initialization). Run in order:

```bash
snakemake results/spatial/sar_results.pkl results/spatial/sem_results.pkl --cores 4 --forcerun
snakemake results/spatial/sdm_results.pkl --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import pickle
for name, path, param_attr in [
    ('SAR', 'results/spatial/sar_results.pkl', 'rho_'),
    ('SEM', 'results/spatial/sem_results.pkl', 'lambda_'),
    ('SDM', 'results/spatial/sdm_results.pkl', 'rho_'),
]:
    with open(path, 'rb') as f: m = pickle.load(f)
    param = getattr(m, param_attr, None)
    aic = getattr(m, 'aic_', None)
    print(f'{name}: {param_attr}={round(param, 4) if param is not None else None}, AIC={round(aic, 2) if aic is not None else None}')
    if param is not None and param < -0.5:
        print(f'  WARNING: {name} {param_attr}={param} is very negative (unusual for housing markets)')
        print(f'  Check W is row-standardized and y_raw has no extreme outliers')
"
```

**Credible result:** |rho| < 0.5, rho > 0 (positive spatial lag is typical in housing markets), AIC difference > 2 between best and worst model.
**Known issue:** Current results show SAR rho = -0.182, SEM lambda = -0.191 (negative, unusual). Root cause is likely that Moran's I is near zero (no actual spatial autocorrelation in the synthetic data), making spatial parameter estimates unstable. Re-run after Phase 1 produces real residuals.

---

### Step C6 — LeSage-Pace direct/indirect/total effects

The rule is `lesage_pace`. Input: `results/spatial/sdm_results.pkl` and `data/interim/spatial/weights_knn.pkl`. Output: `results/spatial/lesage_pace_effects.parquet`.

```bash
snakemake results/spatial/lesage_pace_effects.parquet --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import pandas as pd
lp = pd.read_parquet('results/spatial/lesage_pace_effects.parquet')
print('Columns:', lp.columns.tolist())
print(lp.to_string())
# Check SEs are not degenerate
if 'direct_se' in lp.columns:
    assert lp['direct_se'].max() > 1e-4, 'Direct SE still degenerate (~0) — Monte Carlo simulation failed'
    assert lp['indirect_se'].max() > 1e-4, 'Indirect SE still degenerate'
    if lp['total'].values[0] != 0:
        print('Spillover ratio (indirect/total):', round(float(lp['indirect'].values[0]) / float(lp['total'].values[0]), 4))
"
```

**Known issue:** Current LeSage-Pace SEs = 4e-7 (degenerate). Root cause is the Monte Carlo simulation in `src/spatial_models/effects.py`. Fix: increase `n_simulations`, verify eigenvalue approximation does not produce near-singular matrix.

---

### Step C7 — Nesting tests (LRT)

The rule is `nesting_tests`. Calls `src/spatial_models/model_registry.py::SpatialModelRegistry`. Output: `results/spatial/nesting_tests.json`.

```bash
snakemake results/spatial/nesting_tests.json --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import json
with open('results/spatial/nesting_tests.json') as f: d = json.load(f)
print('Nesting test keys:', list(d.keys()))
if 'lrt_sdm_vs_sar' in d:
    print('LRT SDM vs SAR:', d['lrt_sdm_vs_sar'])
if 'comparison' in d:
    import pandas as pd
    comp = pd.DataFrame(d['comparison'])
    print('Model comparison:')
    print(comp.to_string())
"
```

---

### Step C8 — GWR bandwidth selection

The rule is `gwr_bandwidth`. Uses `src/gwr/bandwidth.py::BandwidthSelector`. Golden-section search between 1.0 and 50.0 km. Checkpoint saved at `data/interim/spatial/bw_checkpoint.pkl` (resumes if interrupted). Outputs: `results/gwr/optimal_bandwidth.json` and `data/interim/spatial/bw_checkpoint.pkl`.

```bash
snakemake results/gwr/optimal_bandwidth.json data/interim/spatial/bw_checkpoint.pkl --cores 4 --forcerun
```

**Runtime:** ~30-60 minutes (bandwidth cross-validation by leave-one-out)
**Verify:**
```bash
python3 -c "
import json
with open('results/gwr/optimal_bandwidth.json') as f: bw = json.load(f)
print('Optimal bandwidth:', bw['bandwidth_km'], 'km')
if bw['bandwidth_km'] > 20:
    print('WARNING: Bandwidth > 20km. GWR approaches global regression.')
    print('With real data this should be tighter (5-15km for a 15km study area).')
    print('Consider forcing a fixed bandwidth — see decision points below.')
elif bw['bandwidth_km'] < 1:
    print('WARNING: Bandwidth < 1km. May overfit local noise.')
else:
    print('Bandwidth within plausible range for Lahaina study area.')
"
```

---

### Step C9 — Fit GWR surface

The rule is `fit_gwr`. Input: `data/interim/spatial/price_change.parquet` and `results/gwr/optimal_bandwidth.json`. Output: `results/gwr/gwr_surface.parquet`.

```bash
snakemake results/gwr/gwr_surface.parquet --cores 4 --forcerun
```

**Verify:**
```bash
python3 -c "
import pandas as pd
surf = pd.read_parquet('results/gwr/gwr_surface.parquet')
print('GWR surface shape:', surf.shape)
print('Columns:', surf.columns.tolist())
beta_col = 'beta_dist_to_fire_km'
if beta_col in surf.columns:
    print('Local beta range:', round(surf[beta_col].min(), 4), 'to', round(surf[beta_col].max(), 4))
    print('Spatial variation (std):', round(surf[beta_col].std(), 4))
    if surf[beta_col].std() < 0.001:
        print('WARNING: No spatial variation in local betas. GWR collapsed to global OLS.')
        print('This usually means bandwidth is too large. See decision points below.')
else:
    print('WARNING: beta_dist_to_fire_km column not found. Columns:', surf.columns.tolist())
"
```

---

## Complete execution sequence

Run this top-to-bottom after the pre-flight check passes. Estimated total runtime: 2-3 hours on MacBook Pro M-series.

```bash
# Step 0: Pre-flight
python3 -c "
import pandas as pd, os
checks = {
    'parcels': 'data/raw/parcels/maui_assessor.csv',
    'zhvi': 'data/raw/zillow/zhvi_zip.csv',
    'fhfa': 'data/raw/fhfa/hpi_zip.parquet',
    'census': 'data/raw/census/acs_zip_2022.parquet',
    'fire': 'data/raw/fire/lahaina_perimeter.geojson',
    'wui': 'data/raw/wui/wui_conus.shp',
}
for name, path in checks.items():
    print('OK' if os.path.exists(path) else 'MISSING', name, path)
"

# Phase 1
snakemake data/final/panel.parquet --cores 4 --forcerun
# [Manual: verify and add treated column if missing — see Step A2]
snakemake results/hedonic_results.pkl results/hedonic_table.csv --cores 4 --forcerun
snakemake results/att_gt.pkl results/event_study.csv --cores 4 --forcerun
snakemake results/triple_diff_results.pkl results/decomposition.csv --cores 4 --forcerun
snakemake results/parallel_trends_test.json figures/event_study.pdf --cores 4 --forcerun

# Phase 2
snakemake data/raw/zillow/zhvi_zip.csv data/raw/census/acs_zip_2022.parquet --cores 4
snakemake data/interim/zip_panel.parquet --cores 4 --forcerun
snakemake data/interim/donor_pool.parquet data/interim/covariate_matrix.npz --cores 4 --forcerun
snakemake results/scm/adh_results.pkl results/scm/adh_gap_series.parquet --cores 4 --forcerun
snakemake results/scm/gsynth_results.pkl results/scm/gsynth_gap_series.parquet \
          results/scm/augsynth_results.pkl results/scm/augsynth_gap_series.parquet \
          --cores 4 --forcerun
snakemake results/scm/model_comparison.csv --cores 4 --forcerun
snakemake results/inference/placebo_distribution.parquet results/inference/p_values.json \
          --cores 4 --forcerun  # ~20 min
snakemake results/inference/loo_gaps.parquet results/inference/stability_score.json \
          --cores 4 --forcerun

# Phase 3 (after Phase 1 panel is correct)
snakemake data/interim/spatial/price_change.parquet --cores 4 --forcerun
snakemake data/interim/spatial/weights_knn.pkl data/interim/spatial/weights_idw.pkl \
          data/interim/spatial/eigenvalues_knn.npy --cores 4 --forcerun
snakemake results/esda/global_morans.json \
          results/esda/lisa_stats.parquet results/esda/cluster_labels.parquet \
          --cores 4 --forcerun
snakemake results/spatial/sar_results.pkl results/spatial/sem_results.pkl --cores 4 --forcerun
snakemake results/spatial/sdm_results.pkl --cores 4 --forcerun
snakemake results/spatial/lesage_pace_effects.parquet results/spatial/nesting_tests.json \
          --cores 4 --forcerun
snakemake results/gwr/optimal_bandwidth.json data/interim/spatial/bw_checkpoint.pkl \
          --cores 4 --forcerun  # ~45 min
snakemake results/gwr/gwr_surface.parquet --cores 4 --forcerun

# Figures and remaining outputs
snakemake --cores 4

echo "=== FINAL RESULTS CHECK ==="
python3 -c "
import os
results = {
    'hedonic_table':   'results/hedonic_table.csv',
    'event_study':     'results/event_study.csv',
    'parallel_trends': 'results/parallel_trends_test.json',
    'decomposition':   'results/decomposition.csv',
    'adh_scm':         'results/scm/adh_results.pkl',
    'p_values':        'results/inference/p_values.json',
    'model_comparison':'results/scm/model_comparison.csv',
    'global_morans':   'results/esda/global_morans.json',
    'nesting_tests':   'results/spatial/nesting_tests.json',
    'lesage_pace':     'results/spatial/lesage_pace_effects.parquet',
    'gwr_bandwidth':   'results/gwr/optimal_bandwidth.json',
    'gwr_surface':     'results/gwr/gwr_surface.parquet',
}
for name, path in results.items():
    print('  OK' if os.path.exists(path) else '  MISSING', name)
"
```

---

## Decision points after Phase 1

**If ATT is not significant (|t| < 1.6):**
- Do not abandon. Thin housing markets (few transactions) have low statistical power.
- Report ATT with wide CI, note power limitation explicitly.
- Phase 2 SCM provides independent corroboration even if Phase 1 is weak.

**If Moran's I is insignificant on real hedonic residuals:**
- Drop SAR/SEM/SDM as primary results. Move to appendix as robustness check.
- Report: "We test for spatial autocorrelation in hedonic residuals and find no significant clustering (I = X, p = Y), indicating the hedonic model adequately absorbs spatial structure."
- This is a valid finding, not a failure. Simplify Phase 3 to descriptive spatial analysis.

**If GWR bandwidth > 20 km:**
Force a fixed 5 km bandwidth and rerun:
```bash
python3 -c "
import json
with open('results/gwr/optimal_bandwidth.json', 'w') as f:
    json.dump({'bandwidth_km': 5.0, 'method': 'fixed_override', 'note': 'Cross-validation gave implausibly large bandwidth; fixed at 5km matching study area scale'}, f, indent=2)
"
snakemake results/gwr/gwr_surface.parquet --forcerun --cores 4
```

**If SCM p-value remains > 0.10 on real data:**
- Report honestly: "We cannot reject the null that the Lahaina ZIP code's post-fire price trajectory falls within the placebo distribution (p = 0.155)."
- This may reflect thin ZIP-level data rather than no effect. Phase 1 parcel-level DiD is the primary estimator; SCM is corroborating evidence.

**If LeSage-Pace SEs remain degenerate on real data:**
- Report direct and indirect point estimates only, note SEs could not be computed reliably.
- Alternatively, use analytical SEs from the SDM Hessian (if implemented in `src/spatial_models/sdm.py`) rather than Monte Carlo simulation.
