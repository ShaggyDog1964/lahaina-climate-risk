# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0.0-phases-1-3] — 2024-XX-XX

### Added

#### Phase 1 — Causal identification on parcel-level transactions
- Log-hedonic regression with census-block and year-month two-way fixed effects (HC3 robust SE)
- Callaway-Sant'Anna (2021) staggered DiD: ATT(g,t) via doubly-robust IPW, event-study aggregation
- Triple-difference decomposition: WUI × post × distance-band isolates belief-update channel
- H3 hexagonal spatial indexing at resolution 8 for parcel-level panel construction
- Pre-trend WLS regression test for parallel trends assumption

#### Phase 2 — Synthetic control with permutation inference
- ADH (2010) synthetic control via CVXPY bilevel quadratic program (inner QP over w, outer over V)
- Xu (2017) generalized SCM via EM algorithm with interactive fixed effects
- Ben-Michael, Feller & Rothstein (2021) augmented SCM with ridge bias correction
- In-space placebo permutation inference with RMSPE ratio rank statistic
- Leave-one-out stability diagnostics for donor pool robustness

#### Phase 3 — Spatial econometrics for spillover identification
- Global Moran's I with Cliff-Ord analytical moments and 999-permutation inference
- Local Moran's I (LISA) with quadrant classification: HH/LL/HL/LH/NS
- SAR model via concentrated log-likelihood over ρ, numerical Hessian SE
- SEM model via concentrated log-likelihood over λ, numerical Hessian SE
- SDM with LR nesting test (vs. SAR) and Wald common-factor restriction test (vs. SEM)
- LeSage-Pace direct/indirect/total effects via eigenvalue trace approximation (avoids dense inversion)
- GWR with golden-section AICc bandwidth CV and checkpoint/resume for long runs
- Interactive LISA choropleth and GWR coefficient surface maps (Folium)
- FastAPI spatial results service with 6 endpoints and ClickHouse analytical store

#### Infrastructure (Phase 4)
- FHFA ZIP HPI ingest: chunked download, quarterly → annual conversion, Hawaii filter
- Redfin neighborhood market tracker: streaming gzip, HI filter, parquet cache
- Maui County Assessment Roll ingest with pandera schema validation
- Full Snakemake pipeline DAG covering all three phases (~200 rules)
- Synthetic data DGP for CI and demonstration (no real data required)
- Four-tier test suite: unit (pytest), property (Hypothesis), integration, numerical validation
- CI matrix on Python 3.11 + 3.13 via GitHub Actions
- Docker Compose: PostGIS 16 + ClickHouse services

### Data sources integrated
- Maui County Real Property Assessment Roll (primary parcel transaction source)
- Zillow ZHVI by ZIP code (monthly, streaming public bulk CSV)
- FHFA House Price Index by ZIP code (quarterly, public Excel)
- Census ACS 5-year estimates by ZIP (API)
- NIFC / WFIGS 2023 fire perimeters (ArcGIS REST — auto-downloaded)
- USFS Wildland-Urban Interface shapefile (RDS-2015-0047-3)
- FRED macro series (API): MEHOINUSHA672N, DFF, MORTGAGE30US, UNRATE

### Removed
- ZTRAX and CoreLogic references — replaced with fully public sources
- Placeholder SCM benchmark script (functionality moved to `tests/numerical_validation/`)
