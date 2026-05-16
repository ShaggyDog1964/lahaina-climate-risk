# Outcome Bug Report — 2026-05-16

## Primary bug
- **File**: `src/spatial_models/outcome.py:40`
- **Column assumed**: `"date"`
- **Actual date-like columns in panel**:
  - `sale_date`: dtype=`datetime64[us]`, sample=`[Timestamp('2022-05-03'), Timestamp('2023-06-29'), ...]`
  - `year_month`: dtype=`str`, sample=`['2022-05', '2023-06', '2022-05']`
  - `fe_yearmonth`: dtype=`str`, sample=`['2022-05', '2023-06', '2022-05']`
  - `year_built`: dtype=`int64` (not relevant)
  - `event_time`: dtype=`int64` (not relevant)
- **Column to use**: `year_month` (already YYYY-MM str; also `sale_date` and `fe_yearmonth` are valid)
- **Crash line**: `panel["date"] = pd.to_datetime(panel["date"])...` → `KeyError: 'date'`
- **Partial mitigation that fails**: line 37 renames `"period"` → `"date"` but panel has neither `"period"` nor `"date"`

## Secondary risks
- **att_gt.pkl present**: YES — but type is `dict` with len=3, NOT a DataFrame. Current code calls `att_results.att_gt` (attribute access on a dict) → `AttributeError`. y_residual will silently fall back to y_raw.
- **lat/lon columns present**: YES — `lat` (float64) and `lon` (float64) are present in panel
- **geometry column in output**: YES — `build_price_change` returns GeoDataFrame
- **Snakemake rule drops geometry before parquet**: YES — `gdf.drop(columns='geometry').to_parquet(...)` — will fail with `KeyError: ['geometry']` if GDF is ever returned as plain DataFrame (defensive fix needed)
- **Output directory `data/interim/spatial/` creation**: NOT GUARANTEED — rule has no `mkdir -p`; will raise `OSError` if directory absent

## All column name assumptions in outcome.py
- Line 37: `"period"` (rename fallback — never present)
- Line 40: `"date"` — **DOES NOT EXIST** in panel
- Line 42-43: `"date"` (pre/post masks)
- Line 46: `"parcel_id"`, `"log_price"`
- Line 57: `"lat"`, `"lon"`, `"treatment_band"`, `"wui_class"`, `"dist_to_fire_km"`
- Line 61: `"date"` (sort_values)
- Line 92: `"lat"`, `"lon"`
- Line 74: `"parcel_id"`, `"att"` (in ATT DataFrame — type mismatch: actual is dict)

## All column name assumptions in other Phase 3 files
- `src/spatial_models/sar.py`: reads `price_change.parquet` — assumes `y_raw`, `geometry`
- `src/spatial_models/sem.py`: same
- `src/spatial_models/sdm.py`: same
- `src/esda/morans.py`: no direct panel column access
- `src/esda/lisa.py`: no direct panel column access
- `src/gwr/gwr_model.py`: no direct panel column access

## Test baseline
- **13 passed / 0 failed** (tests/spatial_models/ — no test_outcome.py existed)
- Ruff: **0 violations** in src/spatial_models/, src/esda/, src/gwr/

## Panel schema (confirmed)
```
Columns: ['parcel_id', 'sale_price', 'sale_date', 'lat', 'lon', 'land_area_sqft',
          'structure_sqft', 'year_built', 'zoning', 'tract_geoid', 'log_price',
          'wui_class', 'h3_index', 'dist_to_fire_km', 'treatment_band', 'year_month',
          'post', 'event_time', 'fe_block', 'fe_yearmonth', 'CSUSHPINSA', 'FEDFUNDS',
          'HISTHPI', 'MEHOINUSHIA672N', 'MORTGAGE30US', 'UNRATE']
Shape: (2636, 26)
```

## Fix plan
1. `outcome.py`: replace hardcoded `"date"` with `_resolve_date_column()` — tries `sale_date`, `fe_yearmonth`, `year_month`, `date` in order; returns first match; raises `KeyError` with actionable message if none found
2. `outcome.py`: add `_to_year_month()` to normalize any date-like series to YYYY-MM string
3. `outcome.py`: add `_resolve_coord_columns()` for lat/lon defensive lookup
4. `outcome.py`: fix att_gt handling — type is `dict`, not object with `.att_gt` attribute; degrade gracefully to `y_residual = NaN`
5. `Snakefile build_spatial_outcome`: add `Path('{output}').parent.mkdir(parents=True, exist_ok=True)`, `log:`, `benchmark:` directives
6. `tests/spatial_models/test_outcome.py`: create from scratch with parametrized date column tests
