# Replication Guide

**Full replication time:** ~4 hours from raw data to compiled PDF (on an M-series MacBook)

---

## Environment Setup

```bash
# Clone and install
git clone https://github.com/[username]/lahaina-climate-risk.git
cd lahaina-climate-risk

# Install uv (fast Python package manager)
pip install uv

# Install all dependencies from lock file
uv sync --dev

# Verify installation
python3 -c "import geopandas, cvxpy, statsmodels, scipy; print('OK')"

# Configure API keys
cp .env.example .env
# Edit .env — add FRED_API_KEY and CENSUS_API_KEY (both free, see docs/data_acquisition.md)
```

**Python version:** 3.11 or 3.12 (3.13 supported but not tested against all dependencies)

**Optional dependencies:**
```bash
# Docker — for PostGIS and ClickHouse (only needed for API endpoint and advanced workflows)
docker compose up -d

# R + gsynth package — only needed to run numerical validation tests
# The core pipeline does not require R
Rscript -e "install.packages(c('Synth', 'gsynth', 'tidyverse'))"
```

---

## Step 1 — Acquire Data

See [docs/data_acquisition.md](data_acquisition.md) for full instructions.

**Quick summary:**
```bash
# Datasets that download automatically
make fetch-data        # runs all ingest modules that auto-download

# Datasets you must obtain manually
# 1. Maui County Assessment Roll → data/raw/parcels/maui_assessor.csv
# 2. USFS WUI Shapefile → data/raw/wui/wui_conus.shp

# Verify all data is present
make data-check
```

Expected output of `make data-check`:
```
OK: data/raw/parcels/maui_assessor.csv
OK: data/raw/fire/lahaina_perimeter.geojson
OK: data/raw/wui/wui_conus.shp
OK: data/raw/zillow/zhvi_zip.csv
OK: data/raw/fhfa/hpi_zip.parquet
OK: data/raw/fred/series.parquet
OK: data/raw/census/acs_zip.parquet
ALL REQUIRED DATA PRESENT
```

---

## Step 2 — Run the Pipeline

### Option A — Full pipeline via Snakemake (recommended)

```bash
# Dry run first — shows every rule that will execute without running them
snakemake --dry-run --cores 4

# Full pipeline (all three phases, ~3 hours)
snakemake --cores 4

# Or phase by phase with Make targets
make phase1    # ~20 min
make phase2    # ~60 min
make phase3    # ~90 min
```

### Option B — Individual Snakemake rules

```bash
# Phase 1
snakemake run_hedonic --cores 1
snakemake test_parallel --cores 1
snakemake run_triple_diff --cores 1

# Phase 2
snakemake build_donor_pool --cores 1
snakemake fit_adh_scm --cores 1
snakemake fit_gsynth --cores 1
snakemake fit_augsynth --cores 1
snakemake run_placebos --cores 4      # parallelizes placebo runs
snakemake compare_scms --cores 1

# Phase 3
snakemake build_spatial_weights --cores 1
snakemake compute_morans --cores 1
snakemake lisa_clusters --cores 1
snakemake fit_sar --cores 1
snakemake fit_sem --cores 1
snakemake fit_sdm --cores 1
snakemake lesage_pace --cores 1
snakemake fit_gwr --cores 4           # bandwidth CV is parallelized
```

### Expected runtimes (M2 MacBook Pro, 8 cores)

| Rule | Runtime |
|------|---------|
| `run_hedonic` | ~2 min |
| `test_parallel` | ~1 min |
| `run_triple_diff` | ~1 min |
| `build_donor_pool` | ~5 min |
| `fit_adh_scm` | ~3 min |
| `fit_gsynth` | ~10 min |
| `fit_augsynth` | ~5 min |
| `run_placebos` | ~25 min (parallelized over donors) |
| `build_spatial_weights` | ~5 min |
| `fit_sar` | ~2 min |
| `fit_sem` | ~2 min |
| `fit_sdm` | ~3 min |
| `lesage_pace` | ~5 min |
| `fit_gwr` | ~60 min (bandwidth CV) |

GWR bandwidth selection checkpoints to `data/interim/spatial/bw_checkpoint.pkl` every 10
iterations. If the run is interrupted, restart with `snakemake fit_gwr` — it will resume
from the last checkpoint.

---

## Step 3 — Generate Paper

```bash
cd paper
make all
```

This runs `pdflatex → bibtex → pdflatex → pdflatex` and produces `paper/main.pdf`.

**Requirements:** TeX Live 2023 or MacTeX 2023. If LaTeX is not installed:
```bash
# macOS
brew install --cask mactex

# Ubuntu/Debian
sudo apt-get install texlive-full biber
```

---

## Output Map

Every table and figure in the paper corresponds to a Snakemake rule and an output file.

| Paper element | Output file | Snakemake rule | Source module |
|---------------|-------------|----------------|---------------|
| Table 1 — Hedonic regression | `docs/tables/phase1_hedonic.tex` | `run_hedonic` | `src/outputs/tables.py` |
| Figure 1 — Event study | `figures/event_study.pdf` | `test_parallel` | `src/outputs/tables.py` |
| Table 2 — Parallel trends test | `docs/tables/phase1_pretrend.tex` | `test_parallel` | `src/outputs/tables.py` |
| Table 3 — Triple-difference | `docs/tables/phase1_triple.tex` | `run_triple_diff` | `src/outputs/tables.py` |
| Table 4 — SCM donor weights | `docs/tables/phase2_weights.tex` | `compare_scms` | `src/outputs/scm_tables.py` |
| Figure 2 — SCM path plot | `figures/scm_adh_path.pdf` | `fit_adh_scm` | `src/outputs/scm_plots.py` |
| Figure 3 — Placebo inference | `figures/scm_placebo.pdf` | `run_placebos` | `src/outputs/scm_plots.py` |
| Table 5 — Spatial model comparison | `docs/tables/phase3_spatial.tex` | `fit_sdm` | `src/outputs/spatial_tables.py` |
| Table 6 — LeSage-Pace effects | `docs/tables/phase3_effects.tex` | `lesage_pace` | `src/outputs/spatial_tables.py` |
| Table 7 — Moran's I and LISA | `docs/tables/phase3_morans.tex` | `lisa_clusters` | `src/outputs/spatial_tables.py` |
| Figure 4 — LISA cluster map | `figures/lisa_map.html` | `lisa_clusters` | `src/outputs/spatial_plots.py` |
| Figure 5 — GWR coefficient surface | `figures/gwr_dist_to_fire.html` | `fit_gwr` | `src/outputs/spatial_plots.py` |

---

## Verification Checks

After the pipeline completes, run automated verification:

```bash
# Verify all expected output files exist
make check-outputs

# Run the full test suite against real data
make test-integration

# Compare spatial model results against spdep reference values
make test-numerical
```

---

## Common Issues

**`ModuleNotFoundError: No module named 'src'`**
The package is not installed in editable mode. Run `uv sync` or `pip install -e .` from the
repository root.

**`FileNotFoundError: data/raw/parcels/maui_assessor.csv`**
The Maui Assessment Roll is not auto-downloaded. See Step 2 of `docs/data_acquisition.md`.

**`ConvergenceWarning` from ADH SCM**
The outer optimization did not converge within 500 iterations. The best-found solution is used.
This typically happens with very few donor units. Check `results/scm/adh_summary.json` for the
`converged` flag and `pre_rmspe` — if pre-period RMSPE is below 0.05, the weights are usable.

**GWR run killed by OOM**
Reduce the bandwidth candidate grid with `BandwidthSelector(n_candidates=20)` instead of the
default 30. Or run with `--cores 1` to avoid memory multiplication from parallel workers.

**`KeyError: 'date'` in spatial outcome builder**
The parcel CSV does not have a column named `date`. Check `src/spatial_models/outcome.py` —
the module uses dynamic column resolution and will look for `sale_date`, `SaleDate`, or `DATE`.
If your column has a different name, add it to the `DATE_COLUMNS` list in that module.

**LaTeX compilation fails with `undefined control sequence`**
Run `make clean && make all` in `paper/`. The first LaTeX pass sometimes fails if `main.aux`
contains stale cross-references from a previous partial compile.

**Snakemake reports `Nothing to be done`**
All targets are already up to date. To force a rebuild:
```bash
snakemake --forceall --cores 4
```
Or delete specific output files: `rm results/scm/adh_summary.json && snakemake fit_adh_scm`.
