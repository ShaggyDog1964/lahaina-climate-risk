# Phase 1 Completion Checklist

## Ingest Modules

- [x] `src/ingest/fred.py` — `fetch_series()` with FRED REST API, JSON caching, env-based API key
- [x] `src/ingest/parcel.py` — `load_maui_parcels()` with pandera schema validation and `log_price`
- [x] `src/ingest/fire.py` — `load_fire_perimeter()` from NIFC ArcGIS endpoint with GeoJSON cache
- [x] `src/ingest/wui.py` — `load_wui()` filtering USFS shapefile to Hawaii with WUI class mapping

## Ingest Tests

- [x] `tests/ingest/test_fred.py` — shape/dtypes, missing API key, caching, multi-series
- [x] `tests/ingest/test_parcel.py` — log_price finite, geometry, row count, file-not-found
- [x] `tests/ingest/test_fire.py` — CRS=4326, geometry not null, caching, invalid source
- [x] `tests/ingest/test_wui.py` — Hawaii filter, WUI class labels, missing file, columns

## Spatial Modules

- [x] `src/spatial/h3_grid.py` — `assign_h3()` returning parcel + cell-level GeoDataFrames
- [x] `src/spatial/distance_bands.py` — `assign_distance_bands()` with UTM reprojection and band labels
- [x] `src/spatial/weights.py` — `build_weights()` (KNN) and `build_inverse_distance_weights()` (IDW)
- [x] `src/spatial/panel_builder.py` — `build_panel()` merging parcels + FRED with post/event_time/FE columns

## Spatial Tests

- [x] `tests/spatial/test_h3_grid.py` — h3_index not null, tuple return, cell summary columns
- [x] `tests/spatial/test_distance_bands.py` — band label correctness, dist non-negative, GeoDataFrame return
- [x] `tests/spatial/test_weights.py` — n==20, mean_neighbors>0, file save, too-few-obs error
- [x] `tests/spatial/test_panel_builder.py` — post flips at fire_date, event_time integer, sorted, FE columns

## Model Modules (TDD)

- [x] `src/models/hedonic.py` — `HedonicModel` OLS with HC3, `summary_table()`, Google docstrings
- [x] `src/models/did_cs.py` — `CallawayAntaCSiD` with csdid/TWFE fallback, `event_study_df()`
- [x] `src/models/triple_diff.py` — `TripleDifference` PanelOLS/OLS fallback, `decompose()`
- [x] `src/models/parallel_trends.py` — `test_parallel_trends()` WLS pre-trend test + `plot_event_study()`

## Model Tests (TDD)

- [x] `tests/models/test_hedonic.py` — beta within 0.0002, R²>0.3, summary columns, zoning dummies
- [x] `tests/models/test_did_cs.py` — ATT within 0.05, event_time range −12 to +12, columns, pre-trends
- [x] `tests/models/test_triple_diff.py` — WUI harder hit, 3 decomp rows, columns, raises before fit
- [x] `tests/models/test_parallel_trends.py` — flat passes, steep fails, file created, insufficient-data error

## Parallel Trends Test

- [x] `test_parallel_trends()` implemented with WLS inverse-variance weighting
- [x] Returns `{slope, p_value, passes}` dict; `passes = (p_value > 0.10)`

## Outputs & Documentation

- [x] `src/outputs/tables.py` — `hedonic_to_latex()` and `did_to_latex()` with threeparttable + stars
- [x] `README.md` — Overview, research question, methodology table, data sources, quickstart, file tree
- [x] `notebooks/01_phase1_eda.ipynb` — 5 cells: load panel, summary stats, histogram, map, event study
- [x] `Makefile` — `install`, `phase1`, `test`, `lint`, `clean` targets
- [x] `docker-compose.yml` — PostGIS 16-alpine service on port 5432
- [x] `.env.example` — `FRED_API_KEY`, `POSTGRES_DSN`, `CENSUS_API_KEY`

## Pipeline

- [x] `Snakefile` — Complete DAG: fetch_fred → fetch_fire → load_parcels → join_wui → build_h3
  → assign_bands → build_weights → build_panel → run_hedonic → run_did_cs → run_triple_diff → test_parallel
- [x] `all` rule connecting all terminal outputs

## Status

`make phase1` runs end-to-end on synthetic data (requires real parcel + WUI files for production run).

Generated: 2026-05-10
