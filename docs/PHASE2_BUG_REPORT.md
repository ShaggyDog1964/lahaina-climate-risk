# Phase 2 Bug Report — 2026-05-15

## Primary Bug: zip_code dtype mismatch

- **ZHVI dtype**: int64 (pandas infers 96xxx 5-digit zips as integers when re-read from CSV)
- **ACS dtype**: object/str (parquet preserves str from `fetch_acs_zip`)
- **Merge line**: `zip_panel_builder.py:41` — `panel.merge(acs[acs_cols], on="zip_code", how="left")`
- **Root cause (full causal chain)**:
  1. `fetch_zhvi` Snakefile rule calls `fetch_zhvi_by_zip('HI')` which returns long-format DataFrame with `zip_code` as `object`/str (line 58: `.astype(str).str.zfill(5)`). It saves to `data/raw/zillow/zhvi_zip.csv`.
  2. `build_zip_panel` Snakefile rule reads this CSV back at line 352: `zhvi = pd.read_csv('{input.zhvi}')`. Since Hawaii zip codes are 5-digit integers (96xxx) with **no leading zeros**, pandas infers `zip_code` as `int64`.
  3. `build_zip_panel(zhvi, acs, hta)` is called where `zhvi["zip_code"]` is int64 and `acs["zip_code"]` (from parquet) is str. The merge at line 41 raises: `ValueError: You are trying to merge on object and int64 columns. If you wish to proceed you should use pd.concat`.
  4. Secondary consequence: even if merge succeeded, line 54 `panel["treated"] = (panel["zip_code"] == LAHAINA_ZIP).astype(int)` would be all-zeros (int 96761 != str "96761"), silently producing a broken treated column.

## Cascading risks identified

- `DonorPool.filter_hawaii_zips` line 42: `z != self.treated_zip` — silent all-False if zip_code is int and treated_zip is str "96761"
- `DonorPool.screen_on_data_quality` line 52: `pre[pre["zip_code"] == z]` — silent empty result if z is int
- `covariate_matrix.py:45`: `acs[acs["zip_code"] == zip_code]` — int vs str mismatch when acs lookup is performed
- `Snakefile:535`: `donors = [z for z in pool['zip_code'].unique() if z != '96761']` — int vs str comparison

## hta=None handling

**Yes — guarded.** `zip_panel_builder.py:44` checks `if hta is not None and len(hta) > 0`. Snakefile explicitly sets `hta = None`. No crash. HTA stub in `hta_tourism.py` raises `NotImplementedError` correctly.

## Test baseline

- **11 failed, 61 passed** (Phase 2 tests: ingest, scm, inference)
- Failures:
  - `test_census_acs.py` (4): mock missing `mock_resp.status_code = 200` → `ValueError: Census API returned HTTP <MagicMock...>`
  - `test_zillow_zip.py::test_fetch_zhvi_caches` (1): same mock issue
  - `test_fire.py` (3): same mock issue
  - `test_fred.py` (3): same mock issue
- All 4 census_acs test failures trace to: mock `status_code` not set, so `resp.status_code != 200` evaluates to True and raises before API response is used

## Ruff violations

- **0 total** — `ruff check src/ingest/ src/scm/ src/inference/` exits clean

## Mypy errors

- Not checked (mypy not installed in env)

## NotImplementedError stubs

- `src/ingest/hta_tourism.py:22` — `fetch_hta_visitors()` raises `NotImplementedError` (intentional, documented)
- No others found in Phase 2 source

## Dead code identified

- None found in Phase 2 source via ruff F401/F841

## Fix plan

1. `src/ingest/zip_panel_builder.py`: add `_coerce_zip_code()`, call before all merges
2. `src/ingest/exceptions.py`: create `DataValidationError`
3. `tests/ingest/test_zip_panel_builder.py`: add int-dtype fixtures, regression test
4. `tests/ingest/test_census_acs.py`: add `mock_resp.status_code = 200` to all mocks
5. `tests/ingest/test_zillow_zip.py`: add `mock_resp.status_code = 200`
6. `src/scm/donor_pool.py`: add zip_code dtype guard
7. `src/outputs/scm_plots.py`: add `Path.mkdir` + `plt.close()` guards
8. `Snakefile`: update `build_zip_panel` rule with log/benchmark directives
