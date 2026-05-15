# Phase 2 Checklist — Synthetic Control Method

Generated: 2026-05-10

## Data Ingestion
- [x] Zillow ZHVI zip-level panel built (`src/ingest/zillow_zip.py`)
- [x] Census ACS covariates fetched (`src/ingest/census_acs.py`)
- [x] HTA visitor stub implemented (`src/ingest/hta_tourism.py`)
- [x] Zip-level panel merged and saved (`src/ingest/zip_panel_builder.py`)

## Donor Pool
- [x] Donor pool screened on pre-trend R² ≥ 0.6 (`src/scm/donor_pool.py`)
- [x] Donor pool screened on data quality (≤ 10% missing) (`src/scm/donor_pool.py`)
- [x] Covariate matrix built with 6 standardized covariates (`src/scm/covariate_matrix.py`)

## SCM Estimators
- [x] ADH SCM implemented from scratch with CVXPY (`src/scm/adh_scm.py`)
- [x] Generalized SCM (Xu 2017 IFE) implemented from scratch (`src/scm/gsynth.py`)
- [x] Augmented SCM (Ben-Michael 2021 ridge) implemented from scratch (`src/scm/augsynth.py`)
- [x] Model registry for comparison (`src/scm/model_registry.py`)

## Inference
- [x] In-space placebo p-values computed (`src/inference/placebo.py`)
- [x] Leave-one-out stability diagnostics complete (`src/inference/loo.py`)
- [x] RMSPE utilities implemented (`src/inference/rmspe.py`)

## Outputs
- [x] SCM path plot generated (`src/outputs/scm_plots.py`)
- [x] Placebo distribution plot generated (`src/outputs/scm_plots.py`)
- [x] LOO robustness plot generated (`src/outputs/scm_plots.py`)
- [x] Model comparison plot implemented (`src/outputs/scm_plots.py`)
- [x] LaTeX weights table (`src/outputs/scm_tables.py`)
- [x] LaTeX RMSPE comparison table (`src/outputs/scm_tables.py`)
- [x] LaTeX balance table (`src/outputs/scm_tables.py`)

## Pipeline
- [x] Snakefile phase2 rules added
- [x] `make phase2` runs end-to-end on synthetic data

## Constraints Verified
- [x] No external SCM library used (CVXPY + scipy.optimize only)
- [x] No hardcoded API keys (os.environ + python-dotenv)
- [x] All random seeds fixed (np.random.seed(42) in fixtures)
- [x] Parallel placebo uses joblib threads (not multiprocessing)

## Pending (real data)
- [ ] Real Zillow ZHVI CSV downloaded and cached
- [ ] Real Census ACS API key set in .env
- [ ] HTA visitor data downloaded manually from DBEDT
- [ ] `make phase2` validated on real Maui data
- [ ] Empirical RMSPE ratio and p-value reported

---

## Phase 2 QC Checklist — 2026-05-15

### Bug Fixes
- [x] zip_code int64/str merge error resolved in zip_panel_builder.py
- [x] _coerce_zip_code() normalizer added and called before all merges
- [x] hta=None handled gracefully — no crash when HTA data absent
- [x] Snakemake build_zip_panel rule updated with log/benchmark directives

### Ingest Hardening
- [x] zillow_zip.py: zip_code normalized to str at source (already correct)
- [x] census_acs.py: zip_code normalized to str at source (already correct)
- [x] hta_tourism.py: NotImplementedError stub properly documented
- [x] test_census_acs.py: mock status_code=200 fix, 5 tests passing
- [x] test_zillow_zip.py: mock status_code=200 fix, dtype regression test added

### SCM Pipeline
- [x] donor_pool.py: zip_code dtype guard added (warns and coerces if int)
- [x] covariate_matrix.py: Census -666666666 sentinel replaced before float extraction
- [x] adh_scm.py: convergence tracking added (converged_ attr), summary() None guard fixed
- [x] model_registry.py: register+get round-trip and compare_rmspe columns tested

### Inference
- [x] placebo.py: empty pool guard (ValueError if <2 donors), p_values() method added
- [x] loo.py: empty active donors handled gracefully (returns empty dict)

### Outputs
- [x] scm_plots.py: Path.mkdir(parents=True) guard + plt.close(fig) on all plot functions

### Snakemake
- [x] build_zip_panel rule: log + benchmark directives added
- [x] fetch_zhvi rule: log + benchmark directives added
- [x] fetch_acs rule: log + benchmark directives added
- [x] build_donor_pool rule: log + benchmark directives added
- [x] fit_adh_scm rule: log + benchmark directives added
- [x] fit_gsynth rule: log + benchmark directives added
- [x] fit_augsynth rule: log + benchmark directives added

### Tests
- [x] test_zip_panel_builder.py: int-dtype fixtures, regression test for primary bug
- [x] test_census_acs.py: all 4 mock failures fixed + 2 new tests
- [x] test_zillow_zip.py: caches mock fix + str dtype regression test
- [x] test_adh_scm.py: runtime benchmark + summary keys tests added
- [x] test_model_registry.py: register/get round-trip + compare_rmspe columns
- [x] test_placebo.py: empty pool raises ValueError
- [x] test_loo.py: empty active donors graceful return
