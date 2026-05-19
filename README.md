# Lahaina Climate Risk
## Quantifying Climate Tail-Risk Repricing After the 2023 Lahaina Wildfire


[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Phase 1](https://img.shields.io/badge/Phase%201-Hedonic%20%2B%20DiD-4c72b0)]()
[![Phase 2](https://img.shields.io/badge/Phase%202-Synthetic%20Control-55a868)]()
[![Phase 3](https://img.shields.io/badge/Phase%203-Spatial%20Econometrics-c44e52)]()

---

## What This Is

On **August 8, 2023**, the Lahaina wildfire killed 101 people and destroyed over 2,200 structures on
Maui — the deadliest U.S. wildfire in more than a century. This repository implements a three-phase
econometric study of how that catastrophe was priced into Hawaiian property markets.

**Central question:** Did the Lahaina fire trigger a *structural* repricing of climate tail risk and
can that repricing be decomposed into direct damage, belief updating about disaster probabilities, and
spatial spillover to unaffected neighboring properties?

**Why it matters:** Climate risk pricing is one of the most consequential open problems in modern asset
pricing. Hawaii's geographic isolation, thin listed equity universe, and the fire's exogenous
meteorological trigger (Hurricane Dora's downslope winds) provide unusually clean identification
unavailable in mainland disaster studies.

---

## Methods

Every estimator below is implemented from first principles. External libraries are used only for
numerical validation.

| Phase | Method | File | Identification |
|-------|--------|------|----------------|
| 1 | Log-hedonic regression with two-way FE | [`src/models/hedonic.py`](src/models/hedonic.py) | Conditional independence within census block |
| 1 | Callaway-Sant'Anna (2021) staggered DiD | [`src/models/did_cs.py`](src/models/did_cs.py) | Parallel trends + no anticipation |
| 1 | Triple-difference (WUI × post × distance) | [`src/models/triple_diff.py`](src/models/triple_diff.py) | Additivity of treatment effects |
| 2 | ADH (2010) synthetic control via CVXPY | [`src/scm/adh_scm.py`](src/scm/adh_scm.py) | Pre-period covariate + outcome balance |
| 2 | Xu (2017) generalized SCM (IFE) | [`src/scm/gsynth.py`](src/scm/gsynth.py) | Interactive fixed effects |
| 2 | Ben-Michael et al. (2021) augmented SCM | [`src/scm/augsynth.py`](src/scm/augsynth.py) | Ridge bias correction |
| 2 | In-space placebo permutation inference | [`src/inference/placebo.py`](src/inference/placebo.py) | Exchangeability of donor units |
| 3 | Global & Local Moran's I (LISA) | [`src/esda/`](src/esda/) | Spatial randomization null |
| 3 | SAR / SEM via concentrated log-likelihood | [`src/spatial_models/sar.py`](src/spatial_models/sar.py) | Correctly specified W matrix |
| 3 | SDM + LeSage-Pace direct/indirect effects | [`src/spatial_models/sdm.py`](src/spatial_models/sdm.py) | No omitted spatially lagged variables |
| 3 | GWR with golden-section bandwidth CV | [`src/gwr/`](src/gwr/) | Local stationarity within bandwidth |

---

## Quickstart — 5 Minutes to Running Demo

```bash
# 1. Clone and install
git clone https://github.com/[username]/lahaina-climate-risk.git
cd lahaina-climate-risk
pip install uv && uv sync

# 2. Configure API keys (both free — see docs/data_acquisition.md)
cp .env.example .env
# Edit .env: add FRED_API_KEY and CENSUS_API_KEY

# 3. Run full pipeline on synthetic data (no real data required)
make demo

# 4. Run tests
make test
```

`make demo` generates synthetic data with a known DGP (ATT = −0.12, ρ_SAR = 0.35) and runs the
complete pipeline in ~15 minutes. All outputs are labeled **SYNTHETIC — NOT EMPIRICAL FINDINGS**.

---

## Reproducing Empirical Results

> See [docs/data_acquisition.md](docs/data_acquisition.md) for step-by-step data download (~2 hours).
> See [docs/replication_guide.md](docs/replication_guide.md) for exact reproduction steps.

```bash
make data-check     # verify all required data files are present
make phase1         # ~20 min — hedonic + DiD + triple-diff
make phase2         # ~60 min — three SCM variants + placebo inference
make phase3         # ~90 min — SAR/SEM/SDM/GWR/LISA + spatial API
make all-phases     # run all three in sequence (~3 hours)
```

---

## Data Sources

| Source | What it provides | Phase | Auto-downloaded |
|--------|-----------------|-------|-----------------|
| Maui County Assessment Roll | Parcel-level transactions, 2018–2024 | 1 | No — see [data guide](docs/data_acquisition.md) |
| Zillow ZHVI (bulk CSV) | Monthly ZIP-level house price index | 2 | Yes |
| FHFA House Price Index by ZIP | Quarterly ZIP HPI, 1996–present | 2 | Yes |
| Census ACS 5-year (API) | Demographics and income by ZIP | 1, 2 | Yes |
| NIFC / WFIGS fire perimeters | 2023 Lahaina fire boundary | 1, 3 | Yes |
| USFS WUI Shapefile | Wildland-urban interface classification | 1, 3 | No — see [data guide](docs/data_acquisition.md) |
| FRED (API) | Macro controls: HPI, rates, unemployment | 1, 2 | Yes |

Free API keys: [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) · [Census](https://api.census.gov/data/key_signup.html)

---

## Empirical Findings

*Pending real data acquisition.* Results below are from the synthetic DGP and should not be interpreted
as empirical findings. Estimates will be updated upon completion of data collection.

| Estimator | Parameter | Synthetic estimate | Synthetic SE |
|-----------|-----------|-------------------|--------------|
| Callaway-Sant'Anna ATT | Log price effect (0–2 km) | −0.118 | 0.031 |
| ADH SCM RMSPE ratio | Post/pre RMSPE | 3.41 | — |
| SAR ρ | Spatial autocorrelation | 0.347 | 0.028 |
| LeSage-Pace indirect/total | Spillover fraction | 0.41 | — |
| Global Moran's I | Spatial clustering | 0.312 | — |

---

## Repository Structure

```
lahaina-climate-risk/
├── src/
│   ├── ingest/                 # Data acquisition (FRED, Census, Zillow, Redfin, parcels)
│   ├── models/                 # Phase 1: hedonic.py, did_cs.py, triple_diff.py
│   ├── scm/                    # Phase 2: adh_scm.py, gsynth.py, augsynth.py, donor_pool.py
│   ├── inference/              # Phase 2: placebo.py, loo.py, rmspe.py
│   ├── spatial/                # Spatial utilities: weights, H3 grid, distance bands
│   ├── spatial_models/         # Phase 3: sar.py, sem.py, sdm.py, effects.py
│   ├── esda/                   # Phase 3: morans.py, lisa.py
│   ├── gwr/                    # Phase 3: bandwidth.py, gwr_model.py
│   ├── api/                    # FastAPI spatial results service (port 8001)
│   └── outputs/                # LaTeX table and figure generators
├── tests/                      # Unit, property (Hypothesis), integration, numerical validation
├── docs/                       # Data guide, methodology notes, replication guide, API reference
├── Snakefile                   # Full pipeline DAG (~200 rules, all three phases)
├── Makefile                    # Developer targets (test/lint/demo/phase1/phase2/phase3)
├── docker-compose.yml          # PostGIS 16 + ClickHouse services
└── pyproject.toml              # uv-managed dependencies
```

---

## Mathematical Formulations

### Hedonic Model (Phase 1)

$$\log P_{it} = \alpha + \beta X_{it} + \gamma_b + \tau_t + \varepsilon_{it}$$

Structural attributes $X_{it}$ (sqft, year built, zoning), census-block FE $\gamma_b$, year-month FE
$\tau_t$, HC3 heteroskedasticity-robust SE.

### Callaway-Sant'Anna ATT(g,t) (Phase 1)

$$ATT(g,t) = \mathbb{E}[Y_t(g) - Y_t(0) \mid G = g]$$

Estimated via doubly-robust IPW with "not-yet-treated" control group. Aggregated to event-study and
simple weighted-average estimands. See [`src/models/did_cs.py`](src/models/did_cs.py).

### ADH Synthetic Control (Phase 2)

Outer: $\min_V \text{MSPE}_{\text{pre}}(w^*(V))$ · Inner: $\min_w \; (X_1 - X_0 w)' V (X_1 - X_0 w)$
subject to $w \geq 0$, $\mathbf{1}'w = 1$. Permutation p-value from RMSPE ratio rank among donor
placebos. See [`src/scm/adh_scm.py`](src/scm/adh_scm.py).

### Spatial Durbin Model (Phase 3)

$$y = \rho W y + X\beta + W X\theta + \varepsilon, \quad \varepsilon \sim \mathcal{N}(0, \sigma^2 I)$$

LR test of $\theta = 0$ nests SAR; Wald common-factor test of $\theta + \rho\beta = 0$ nests SEM.
LeSage-Pace indirect effects via eigenvalue trace: avoids dense $(I - \rho W)^{-1}$.

---

## Identification Advantage

Three features of this setting provide cleaner identification than typical wildfire studies:

1. **Exogenous trigger.** Hurricane Dora's downslope winds caused rapid spread — a meteorological
   event orthogonal to Lahaina's pre-fire property market trajectory.
2. **Geographic isolation.** Hawaii's island economy contains financial transmission in a small,
   identifiable set of instruments (Hawaiian Electric, Maui County GO bonds).
3. **Thin donor pool.** ~30 Hawaii ZIP codes with complete ZHVI history; no contamination from
   mainland disaster contagion.

Known limitations: Assessment-roll data may lag market transactions by 6–12 months. The SCM
donor pool assumes no comparable climate shock in any Hawaii ZIP in the post-period.

---

## Development

```bash
make test           # full test suite (~5 min on synthetic data)
make test-unit      # unit tests only (~1 min)
make lint           # ruff check + ruff format
make type-check     # mypy
make api            # start FastAPI service on port 8001
make docker-up      # start PostGIS + ClickHouse
```

**Requirements:** Python 3.11+, `uv`. Optional: Docker (PostGIS/ClickHouse), R with `Synth` and
`gsynth` packages (for numerical validation tests only).

---

## Citation

```bibtex
@techreport{KoikeSmith2024lahaina,
  title       = {Catastrophe Capitalization: A Quasi-Experimental
                 Analysis of Climate Tail-Risk Pricing Following the
                 2023 Lahaina Wildfire},
  author      = {Noah Koike Smith},
  year        = {2026},
  institution = {Brandeis University},
  note        = {Preliminary draft. Code: https://github.com/[username]/lahaina-climate-risk}
}
```

See [`CITATION.cff`](CITATION.cff) for machine-readable citation metadata.

---

## Development Notes

Claude (Anthropic) was used in the refinement of code and in analyzing data for this project.

---

## License

[MIT License](LICENSE). Data sourced from public U.S. government databases and Zillow Research.
See [docs/data_acquisition.md](docs/data_acquisition.md) for terms of use applicable to each source.
