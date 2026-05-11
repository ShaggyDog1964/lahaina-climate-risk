# Repository Audit — 2026-05-11

## ZTRAX/CoreLogic references (0 found)
No ZTRAX, CoreLogic, ZTrans, or ZAsmt references found in src/, tests/, docs/, README.md, or Snakefile.
Clean — no paywall data contamination.

## NotImplementedError stubs (1 found)
- `src/ingest/hta_tourism.py:22` — `raise NotImplementedError` — intentional stub for manually-downloaded HTA data. Tests expect this behavior (`tests/ingest/test_hta_tourism.py:13`).

## Ruff violations (123 total, top 12 by count)
| Count | Code | Description |
|-------|------|-------------|
| 36 | F401 | Unused imports |
| 33 | I001 | Unsorted imports |
| 17 | B905 | zip-without-explicit-strict |
| 11 | UP037 | Quoted annotation (use native) |
| 11 | F841 | Unused variable |
| 4  | SIM108 | if-else-block-instead-of-if-exp |
| 3  | E702 | Multiple statements on one line (semicolon) |
| 3  | SIM117 | Multiple with statements |
| 2  | E741 | Ambiguous variable name |
| 1  | B007 | Unused loop control variable |
| 1  | UP024 | os-error-alias |
| 1  | UP035 | deprecated-import |

81 auto-fixable with `--fix`. 32 additional with `--unsafe-fixes`.

Note: pyproject.toml uses deprecated top-level `[tool.ruff]` keys (`ignore`, `select`) — must migrate to `[tool.ruff.lint]`.

## Mypy errors (73 total)
Primary categories:
- `Returning Any from function declared to return X` — sar.py, sem.py, sdm.py, adh_scm.py, rmspe.py, gsynth.py, augsynth.py (numpy return type inference)
- `"object" has no attribute rho_/beta_/theta_` — effects.py uses untyped `object` for SDM model parameter
- `ExtensionArray` vs `ndarray` type narrowing — scm/covariate_matrix.py, spatial_plots.py, scm_plots.py
- `Axes | None` not narrowed — scm_plots.py uses `ax = fig.add_subplot()` assigned to `Axes | None`
- `gsynth.py:84` — `None @ matrix` operator error

## Test baseline (158 passed, 0 failed, 0 errors)
All 158 tests pass across all modules. 19 warnings (divide-by-zero RuntimeWarning in scipy sparse, FutureWarning in libpysal, UserWarning for Queen fallback).

## Snakemake DAG status
Dry-run stalls waiting on missing input files (expected: data/raw/ not present). DAG builds without syntax errors. All rules syntactically valid.

## Credential risks (0 found)
No hardcoded API keys, passwords, or secrets found in src/ or tests/.

## Dead imports (8 found, all auto-fixable with ruff --fix)
All 8 are flagged F401 and auto-fixable.

## Missing __init__.py (0 found in live code)
All `__pycache__/` directories flagged — these are bytecode cache directories and do NOT need `__init__.py`. No missing init files in actual source packages.

## Data source inventory
- `src/ingest/zillow_zip.py` — Zillow ZHVI (free public bulk download)
- `src/ingest/parcel.py` — Maui Assessment Roll via CSV (`data/raw/parcels/maui_assessor.csv`)
- `src/ingest/fred.py` — FRED API (key required)
- `src/ingest/fire.py` — NIFC/ArcGIS REST (free)
- `src/ingest/wui.py` — USFS WUI shapefile (free)
- `src/ingest/census_acs.py` — Census ACS API (key required)
- `src/ingest/hta_tourism.py` — HTA/DBEDT (stub; manual download)
- No FHFA ZIP HPI ingest yet (to be added)
- No Redfin Research Data ingest yet (to be added)

## Action items for agents
1. **Agent 1**: Fix 123 ruff violations; add type annotations; fix 73 mypy errors in boundary files
2. **Agent 2**: Add FHFA ZIP HPI and Redfin ingest; update parcel.py with Maui Assessment Roll URL; create DATA_SOURCES.md
3. **Agent 3**: Add hypothesis property tests, adversarial fixtures, integration tests, benchmarks
4. **Agent 4**: Create numerical_validation/ test suite
5. **Agent 5**: Create paper/, overhaul README.md, METHODOLOGY_NOTES.md
6. **Agent 6**: Harden API, Docker, add Dockerfile, security hardening
7. **Agent 7**: Full Snakefile audit, Makefile expansion, CI workflow, synthetic demo script
