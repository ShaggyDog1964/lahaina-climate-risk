# Phase 3 Checklist — Spatial Econometrics

- [x] Three spatial W matrices built (KNN, IDW, queen) — `src/spatial/weights_phase3.py`
- [x] Global Moran's I with permutation inference — `src/esda/morans.py`
- [x] Local Moran's I (LISA) with HH/LL/HL/LH/NS cluster map — `src/esda/lisa.py`
- [x] SAR from scratch — concentrated LL + numerical Hessian SE — `src/spatial_models/sar.py`
- [x] SEM from scratch — same — `src/spatial_models/sem.py`
- [x] SDM from scratch + SAR nesting LR test + SEM CF Wald test — `src/spatial_models/sdm.py`
- [x] LeSage-Pace direct/indirect/total with simulation SE — `src/spatial_models/effects.py`
- [x] Spatial model registry with AIC/BIC comparison and LRT — `src/spatial_models/model_registry.py`
- [x] GWR bandwidth via golden-section search with checkpoint — `src/gwr/bandwidth.py`
- [x] GWR local coefficient surfaces computed — `src/gwr/gwr_model.py`
- [x] ClickHouse tables defined (lisa_results, gwr_surfaces, model_comparison) — `src/api/db.py`
- [x] FastAPI spatial results service (6 endpoints) — `src/api/app.py`
- [x] LISA HTML map and GWR surface HTML maps generated — `src/outputs/spatial_plots.py`
- [x] Spillover decay plot generated — `src/outputs/spatial_plots.py`
- [x] LaTeX tables (SAR/SEM/SDM, effects, Moran) generated — `src/outputs/spatial_tables.py`
- [x] `make phase3` target added to Makefile and Snakefile
- [x] 158 tests pass (0 failures, 0 regressions)

## Run Phase 3 end-to-end (requires data from Phase 1)

```bash
make phase3
```

Or run just the spatial models on synthetic data:

```bash
pytest tests/esda/ tests/spatial_models/ tests/gwr/ tests/api/ tests/outputs/
```

## ClickHouse service

```bash
docker-compose up clickhouse -d
export CH_HOST=localhost CH_PORT=9000 CH_DB=lahaina
```

## API service

```bash
uvicorn src.api.app:app --port 8001 --reload
```

Endpoints: `/health`, `/lisa/clusters`, `/lisa/counts`, `/gwr/surface`,
`/models/comparison`, `/spatial/autocorrelation`.
