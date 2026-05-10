# Lahaina Climate-Risk Econometrics

![Phase 1](https://img.shields.io/badge/Phase%201-Hedonic%20%2B%20DiD-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Project Overview

This project quantifies the causal impact of the August 2023 Lahaina wildfire on residential property values in Maui County, Hawaii. Using hedonic pricing, staggered difference-in-differences (Callaway-Sant'Anna 2021), and triple-difference methods, we decompose fire-induced price effects into physical damage, displacement, and climate belief-update channels.

## Research Question

**Does exposure to wildfire risk — proxied by WUI classification and distance to the 2023 Lahaina fire perimeter — reduce residential property values, and through which economic channels?**

Secondary questions:
- Do Wildland-Urban Interface (WUI) parcels experience larger price discounts than similarly-distant non-WUI parcels?
- Is the price effect persistent (belief update) or transitory (liquidity/displacement)?
- What is the spatial spillover of climate risk onto properties beyond the fire perimeter?

## Methodology (Phase 1)

| Component | Method | Library |
|-----------|--------|---------|
| Baseline prices | Hedonic OLS with FE | `statsmodels` |
| Causal identification | Callaway-Sant'Anna (2021) | `csdid` |
| Channel decomposition | Triple-difference | `linearmodels` |
| Spatial indexing | H3 hexagonal grid (res=8) | `h3` |
| Spatial weights | KNN (k=8) + inverse-distance | `libpysal` |
| Parallel trends test | Pre-trend WLS regression | `statsmodels` |

### Hedonic Model

$$\log P_{it} = \alpha + \beta X_{it} + \gamma_b + \tau_t + \varepsilon_{it}$$

where $X_{it}$ contains structural attributes (sqft, year built, zoning), $\gamma_b$ are census-block fixed effects, and $\tau_t$ are year-month fixed effects with HC3 robust standard errors.

### Callaway-Sant'Anna DiD

$$ATT(g,t) = \mathbb{E}[Y_t(g) - Y_t(0) \mid G = g]$$

Estimated using doubly-robust inverse probability weighting with "not-yet-treated" control group. Aggregated to event-study and simple weighted-average estimands.

### Triple Difference

$$\log P_{it} = \alpha + \beta_1 (\text{Post} \times \text{Treated} \times \text{WUI}) + \beta_2 (\text{Post} \times \text{Treated}) + \text{FE} + \varepsilon_{it}$$

The difference $\beta_1 - \beta_2$ isolates the pure belief-update channel from displacement/market-friction effects.

## Data Sources

| Dataset | Source | Access |
|---------|--------|--------|
| Maui parcel sales | Maui County Real Property Assessment Division | User must obtain: `data/raw/parcels/maui_assessor.csv` |
| 2023 Lahaina fire perimeter | NIFC/WFIGS ArcGIS FeatureServer | Auto-downloaded via `src/ingest/fire.py` |
| WUI classification | USFS RDS-2015-0047-3 | User must obtain: `data/raw/wui/wui_conus.shp` |
| FRED macro series | St. Louis Fed FRED API (free) | Auto-fetched — requires `FRED_API_KEY` in `.env` |
| Census tract GEOID | Embedded in parcel assessor data | Via `tract_geoid` column |

## Quickstart

```bash
# 1. Clone and install
git clone <repo-url>
cd lahaina-climate-risk
cp .env.example .env          # Fill in FRED_API_KEY etc.
make install                  # uv sync

# 2. Start PostGIS (optional, for spatial SQL)
docker compose up -d

# 3. Obtain proprietary data (see Data Sources table above)
#    Place maui_assessor.csv at:  data/raw/parcels/maui_assessor.csv
#    Place WUI shapefile at:      data/raw/wui/wui_conus.shp

# 4. Run full Phase 1 pipeline
make phase1

# 5. Run test suite
make test

# 6. Lint + type-check
make lint
```

## File Tree

```
lahaina-climate-risk/
├── pyproject.toml          # uv-managed, pinned dependencies
├── Makefile                # Pipeline entrypoint
├── Snakefile               # Snakemake DAG (fetch → spatial → model → output)
├── docker-compose.yml      # PostGIS 16 service
├── .env.example            # Environment variable template
├── data/
│   ├── raw/                # Immutable source data (never modified)
│   │   ├── fred/           # FRED JSON cache + series.parquet
│   │   ├── parcels/        # Maui assessor CSV (user-supplied)
│   │   ├── fire/           # Lahaina perimeter GeoJSON
│   │   └── wui/            # USFS WUI shapefile (user-supplied)
│   ├── interim/            # Processed intermediates (Parquet)
│   └── final/              # Model-ready long panel (Parquet)
├── src/
│   ├── ingest/             # fred.py, parcel.py, fire.py, wui.py
│   ├── spatial/            # h3_grid.py, distance_bands.py, weights.py, panel_builder.py
│   ├── models/             # hedonic.py, did_cs.py, triple_diff.py, parallel_trends.py
│   └── outputs/            # tables.py (LaTeX generation)
├── tests/                  # pytest suite mirroring src/
├── notebooks/
│   └── 01_phase1_eda.ipynb # EDA: summary stats, histograms, map, event study
├── docs/
│   ├── tables/             # Generated .tex files
│   └── PHASE1_CHECKLIST.md # Completion checklist
├── results/                # Model pickles (.pkl) and CSVs
└── figures/                # event_study.pdf and other outputs
```

## Empirical Findings

[TBD after data collection]

The estimated ATT on log prices for parcels within 2 km of the fire perimeter is [TBD after data collection]. WUI-classified parcels show an additional [TBD after data collection] discount relative to non-WUI parcels in the same distance band, consistent with a belief-update channel. Pre-trend tests [TBD after data collection].

## Citation

If you use this code or data in academic work, please cite:

```bibtex
@misc{lahaina_climate_risk_2024,
  title   = {Lahaina Climate-Risk Econometrics: Phase 1},
  author  = {[TBD]},
  year    = {2024},
  url     = {[TBD]},
  note    = {Working paper}
}
```

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker (optional, for PostGIS)
- FRED API key — free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html)
- Census API key — free at [api.census.gov](https://api.census.gov/data/key_signup.html)
