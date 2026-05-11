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
