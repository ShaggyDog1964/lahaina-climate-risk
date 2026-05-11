# Lahaina Climate-Risk Econometrics

![Phase 1](https://img.shields.io/badge/Phase%201-Hedonic%20%2B%20DiD-blue)
![Phase 2](https://img.shields.io/badge/Phase%202-SCM%20Variants-blue)
![Phase 3](https://img.shields.io/badge/Phase%203-Spatial%20Econometrics-blue)
![Phase 4](https://img.shields.io/badge/Phase%204-Data%20%2B%20CI-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Project Overview

This project quantifies the causal impact of the August 2023 Lahaina wildfire on residential property values in Maui County, Hawaii. Using hedonic pricing, staggered difference-in-differences (Callaway-Sant'Anna 2021), triple-difference decomposition, synthetic control methods, and spatial econometrics, we decompose fire-induced price effects into physical damage, displacement, and climate belief-update channels, and estimate spatial spillovers to properties beyond the fire perimeter.

## Research Questions

**Primary:** Does exposure to wildfire risk — proxied by WUI classification and distance to the 2023 Lahaina fire perimeter — reduce residential property values, and through which economic channels?

**Secondary:**
- Do Wildland-Urban Interface (WUI) parcels experience larger price discounts than similarly-distant non-WUI parcels?
- Is the price effect persistent (belief update) or transitory (liquidity/displacement)?
- What is the spatial extent of wildfire spillovers onto properties beyond the fire perimeter?
- Do synthetic control counterfactuals corroborate the DiD estimates of aggregate market impact?

## Methodology

| Phase | Component | Method | Library |
|-------|-----------|--------|---------|
| 1 | Baseline prices | Hedonic OLS with block + time FE | `statsmodels` |
| 1 | Causal identification | Callaway-Sant'Anna ATT(g,t) | `csdid`, `drdid` |
| 1 | Channel decomposition | Triple-difference (WUI x Post x Treated) | `linearmodels` |
| 1 | Spatial indexing | H3 hexagonal grid (resolution 8) | `h3` |
| 1 | Parallel trends | Pre-trend WLS regression | `statsmodels` |
| 2 | Counterfactual | ADH Synthetic Control (inner QP, outer V) | `cvxpy` |
| 2 | Counterfactual | Generalized Synthetic Control (GSynth) | `cvxpy`, `sklearn` |
| 2 | Counterfactual | Augmented Synthetic Control (AugSynth) | `cvxpy`, `sklearn` |
| 2 | Placebo inference | In-space placebo + LOO donor robustness | custom |
| 2 | Permutation inference | Rank-based RMSPE ratio | custom |
| 3 | Spatial dependence | SAR concentrated ML over rho | `scipy.sparse` |
| 3 | Spatial dependence | SEM concentrated ML over lambda | `scipy.sparse` |
| 3 | Spatial dependence | SDM with LR nesting + CF Wald tests | `scipy.sparse` |
| 3 | Spillover effects | LeSage-Pace direct/indirect/total | eigenvalue trace |
| 3 | Local dependence | Global Moran's I (Cliff-Ord moments, 999-perm) | custom |
| 3 | Local dependence | LISA quadrant classification (HH/LL/HL/LH) | custom |
| 3 | Local heterogeneity | GWR with golden-section bandwidth CV | `mgwr` |
| 3 | API | FastAPI REST, 6 endpoints, ClickHouse fallback | `fastapi` |
| 4 | Data ingest | FHFA ZIP HPI (quarterly repeat-sales) | `requests`, `pandas` |
| 4 | Data ingest | Redfin neighborhood market tracker | `requests`, `pandas` |
| 4 | Testing | Property tests, adversarial fixtures, numerical validation | `hypothesis`, `pytest` |

### Hedonic Model

$$\log P_{it} = \alpha + \beta X_{it} + \gamma_b + \tau_t + \varepsilon_{it}$$

where $X_{it}$ contains structural attributes (sqft, year built, zoning), $\gamma_b$ are census-block fixed effects, $\tau_t$ are year-month fixed effects, and standard errors are HC3 heteroskedasticity-robust.

### Callaway-Sant'Anna DiD

$$ATT(g,t) = \mathbb{E}[Y_t(g) - Y_t(0) \mid G = g]$$

Estimated via doubly-robust inverse probability weighting with a "not-yet-treated" control group. Aggregated to event-study and simple weighted-average estimands.

### Triple Difference

$$\log P_{it} = \alpha + \beta_1 (\text{Post} \times \text{Treated} \times \text{WUI}) + \beta_2 (\text{Post} \times \text{Treated}) + \text{FE} + \varepsilon_{it}$$

The coefficient $\beta_1 - \beta_2$ isolates the belief-update channel from displacement and market-friction effects.

### Synthetic Control (ADH)

Weights $w^*$ are found by minimizing pre-treatment RMSPE subject to a convex combination constraint, with the V-matrix determined by outer minimization over post-treatment fit. Permutation inference uses the rank of the treated unit's RMSPE ratio among all donor placebos.

### Spatial Models

SAR and SEM are estimated by concentrated maximum likelihood over scalar parameters $\rho$ and $\lambda$ respectively. SDM nests both and tests the common-factor restriction via a likelihood ratio. Indirect effects (spatial spillovers) are computed using the LeSage-Pace eigenvalue trace approximation, avoiding dense $(I - \rho W)^{-1}$ inversion.

## Data Sources

| Dataset | Source | Access | Phase |
|---------|--------|--------|-------|
| Maui parcel sales | Maui County Real Property Assessment Division | User must supply: `data/raw/parcels/maui_assessor.csv` | 1 |
| 2023 Lahaina fire perimeter | NIFC/WFIGS ArcGIS FeatureServer | Auto-downloaded via `src/ingest/fire.py` | 1 |
| WUI classification | USFS RDS-2015-0047-3 (Silvis Lab) | User must supply: `data/raw/wui/wui_conus.shp` | 1 |
| FRED macro series | St. Louis Fed FRED API | Auto-fetched; requires `FRED_API_KEY` in `.env` | 1 |
| Census ACS 5-Year | Census Bureau API | Auto-fetched; requires `CENSUS_API_KEY` in `.env` | 1 |
| Zillow ZHVI by ZIP | Zillow Research (public bulk CSV) | Auto-downloaded via `src/ingest/zillow_zip.py` | 2 |
| FHFA ZIP HPI | FHFA (quarterly repeat-sales Excel) | Auto-downloaded via `src/ingest/fred.py` | 4 |
| Redfin neighborhood tracker | Redfin Research (public S3 gzip) | Auto-downloaded via `src/ingest/redfin.py` | 4 |
| Hawaii Tourism Authority | HTA/DBEDT (manual download) | Stub; see `src/ingest/hta_tourism.py` | 1 |

See `docs/DATA_SOURCES.md` for full URLs, coverage notes, and local paths.

## Quickstart

```bash
# 1. Clone and install
git clone <repo-url>
cd lahaina-climate-risk
cp .env.example .env          # Fill in FRED_API_KEY and CENSUS_API_KEY
make install                  # uv pip install -e ".[dev]"

# 2. Start PostGIS and ClickHouse (optional)
docker compose up -d

# 3. Obtain proprietary data (see Data Sources table above)
#    Place maui assessor CSV at:  data/raw/parcels/maui_assessor.csv
#    Place WUI shapefile at:       data/raw/wui/wui_conus.shp

# 4. Run pipelines by phase
make phase1     # Hedonic + DiD + triple-diff + spatial panel
make phase2     # SCM variants + placebo inference
make phase3     # SAR/SEM/SDM/GWR/LISA + FastAPI

# 5. Run test suites
make test              # Core unit tests (158 tests)
make test-all          # All tests including property, adversarial, numerical
make test-properties   # Hypothesis + adversarial + numerical validation only

# 6. Lint and format
make lint
make fmt
```

## File Tree

```
lahaina-climate-risk/
├── pyproject.toml              # uv-managed, pinned dependencies
├── Makefile                    # Pipeline entrypoints (phase1/phase2/phase3/test/lint)
├── Snakefile                   # Snakemake DAG (fetch -> spatial -> model -> output)
├── docker-compose.yml          # PostGIS 16 + ClickHouse services
├── .env.example                # Environment variable template
├── data/
│   ├── raw/                    # Immutable source data (never modified)
│   │   ├── fred/               # FRED JSON cache + series.parquet
│   │   ├── parcels/            # Maui assessor CSV (user-supplied)
│   │   ├── fire/               # Lahaina perimeter GeoJSON
│   │   ├── wui/                # USFS WUI shapefile (user-supplied)
│   │   └── fhfa/               # FHFA ZIP HPI Excel (auto-downloaded)
│   ├── interim/                # Processed intermediates (Parquet)
│   │   └── spatial/            # Spatial weights + bandwidth checkpoint
│   └── final/                  # Model-ready long panel (Parquet)
├── src/
│   ├── ingest/                 # Data ingest modules
│   │   ├── fred.py             # FRED API + FHFA ZIP HPI
│   │   ├── parcel.py           # Maui Assessment Roll
│   │   ├── fire.py             # NIFC/ArcGIS fire perimeter
│   │   ├── wui.py              # USFS WUI shapefile
│   │   ├── redfin.py           # Redfin neighborhood tracker
│   │   ├── zillow_zip.py       # Zillow ZHVI by ZIP
│   │   ├── census_acs.py       # Census ACS 5-Year
│   │   ├── hta_tourism.py      # HTA/DBEDT (stub)
│   │   └── zip_panel_builder.py
│   ├── spatial/                # Phase 1 spatial utilities
│   │   ├── h3_grid.py          # H3 hexagonal indexing (res=8)
│   │   ├── distance_bands.py   # Fire perimeter distance bands
│   │   ├── weights.py          # Phase 1 spatial weights
│   │   ├── weights_phase3.py   # SpatialWeightsFactory (KNN/IDW/Queen)
│   │   └── panel_builder.py    # Long panel assembly
│   ├── models/                 # Phase 1 econometric models
│   │   ├── hedonic.py          # Hedonic OLS with FE
│   │   ├── did_cs.py           # Callaway-Sant'Anna ATT(g,t)
│   │   ├── triple_diff.py      # Triple-difference decomposition
│   │   └── parallel_trends.py  # Pre-trend test
│   ├── scm/                    # Phase 2 synthetic control
│   │   ├── adh_scm.py          # ADH inner QP + outer V-matrix
│   │   ├── gsynth.py           # Generalized Synthetic Control
│   │   ├── augsynth.py         # Augmented Synthetic Control
│   │   ├── covariate_matrix.py # Pre-treatment covariate assembly
│   │   ├── donor_pool.py       # Donor pool construction + filtering
│   │   └── model_registry.py   # AIC/BIC model comparison
│   ├── inference/              # Phase 2 permutation inference
│   │   ├── placebo.py          # In-space placebo inference
│   │   ├── loo.py              # Leave-one-out donor robustness
│   │   └── rmspe.py            # RMSPE ratio rank statistic
│   ├── esda/                   # Phase 3 spatial autocorrelation
│   │   ├── morans.py           # Global Moran's I (Cliff-Ord + 999-perm)
│   │   └── lisa.py             # Local Moran's I + quadrant labels
│   ├── spatial_models/         # Phase 3 spatial regression
│   │   ├── sar.py              # SAR concentrated ML over rho
│   │   ├── sem.py              # SEM concentrated ML over lambda
│   │   ├── sdm.py              # SDM with LR nesting + CF Wald tests
│   │   ├── effects.py          # LeSage-Pace direct/indirect/total
│   │   ├── outcome.py          # Outcome variable preparation
│   │   └── model_registry.py   # AIC/BIC + LRT comparison
│   ├── gwr/                    # Phase 3 geographically weighted regression
│   │   ├── bandwidth.py        # BandwidthSelector (golden-section CV)
│   │   └── gwr_model.py        # GWR local WLS, bisquare/gaussian kernel
│   ├── api/                    # Phase 3 REST API
│   │   ├── app.py              # FastAPI, 6 endpoints, ClickHouse fallback
│   │   ├── db.py               # ClickHouseClient (gated on CH_HOST)
│   │   └── schemas.py          # Pydantic response schemas
│   └── outputs/                # Table and figure generation
│       ├── tables.py           # Phase 1 LaTeX tables
│       ├── scm_tables.py       # Phase 2 LaTeX tables
│       ├── scm_plots.py        # Phase 2 figures
│       ├── spatial_tables.py   # Phase 3 LaTeX tables
│       └── spatial_plots.py    # Phase 3 Folium/Matplotlib figures
├── tests/                      # pytest suite mirroring src/
│   ├── ingest/
│   ├── models/
│   ├── scm/
│   ├── inference/
│   ├── esda/
│   ├── spatial_models/
│   ├── gwr/
│   ├── api/
│   ├── properties/             # Hypothesis property tests
│   ├── adversarial/            # Adversarial fixtures
│   ├── numerical_validation/   # Numerical precision tests
│   └── integration/            # End-to-end integration tests
├── benchmarks/                 # Performance benchmarks
│   └── scm_benchmark.py
├── notebooks/
│   └── 01_phase1_eda.ipynb     # EDA: summary stats, histograms, map, event study
├── docs/
│   ├── tables/                 # Generated .tex files
│   ├── DATA_SOURCES.md         # Full data source inventory
│   ├── METHODOLOGY_NOTES.md    # Full econometric methodology reference
│   ├── AUDIT_LOG.md            # Repository audit findings
│   ├── PHASE1_CHECKLIST.md
│   ├── PHASE2_CHECKLIST.md
│   └── PHASE3_CHECKLIST.md
├── paper/
│   ├── main.tex                # Working paper LaTeX source
│   ├── references.bib          # BibTeX entries
│   └── Makefile                # pdflatex + bibtex build
├── results/                    # Model pickles (.pkl) and CSVs
└── figures/                    # event_study.pdf, LISA map, GWR surface, etc.
```

## Empirical Findings

[TBD after data collection]

The estimated ATT on log prices for parcels within 2 km of the fire perimeter is [TBD]. WUI-classified parcels show an additional [TBD] discount relative to non-WUI parcels in the same distance band, consistent with a belief-update channel. Synthetic control estimates corroborate the DiD findings with a treatment effect of [TBD] on the Maui ZIP aggregate price index. Spatial models detect significant positive spatial autocorrelation (Moran's I = [TBD]) and estimate indirect spillover effects of [TBD] at the median distance from the fire perimeter. Pre-trend tests [TBD].

## Citation

If you use this code or data in academic work, please cite:

```bibtex
@misc{lahaina_climate_risk_2024,
  title   = {Wildfire Risk and Residential Property Values: Evidence from the 2023 Lahaina Fire},
  author  = {[TBD]},
  year    = {2024},
  url     = {[TBD]},
  note    = {Working paper}
}
```

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker (optional — for PostGIS and ClickHouse)
- FRED API key — free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html)
- Census API key — free at [api.census.gov](https://api.census.gov/data/key_signup.html)

Key Python dependencies: `geopandas`, `statsmodels`, `linearmodels`, `csdid`, `drdid`, `libpysal`, `esda`, `mgwr`, `spreg`, `scipy`, `cvxpy`, `scikit-learn`, `fastapi`, `folium`, `h3`, `hypothesis`, `pandera`. See `pyproject.toml` for the full pinned dependency list.
