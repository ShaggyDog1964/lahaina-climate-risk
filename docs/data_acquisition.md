# Data Acquisition Guide

**Time required:** ~2 hours (mostly waiting for downloads)

**Prerequisites:** FRED API key, Census API key (both free — see Step 1)

---

## Step 1 — API Keys (10 minutes)

Both keys are free and arrive within minutes of registration.

### FRED (macro controls)

1. Go to: https://fred.stlouisfed.org/docs/api/api_key.html
2. Click **Request or view your API keys** — sign in or create a free account
3. Generate a key — copy it immediately
4. Add to `.env`: `FRED_API_KEY=your_key_here`

**Verification:**
```bash
curl "https://api.stlouisfed.org/fred/series?series_id=UNRATE&api_key=${FRED_API_KEY}&file_type=json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK:', d['seriess'][0]['id'])"
# Expected: OK: UNRATE
```

### Census ACS (demographic covariates)

1. Go to: https://api.census.gov/data/key_signup.html
2. Complete the form — key arrives by email in ~5 minutes
3. Add to `.env`: `CENSUS_API_KEY=your_key_here`

**Verification:**
```bash
curl "https://api.census.gov/data/2022/acs/acs5?get=NAME&for=state:15&key=${CENSUS_API_KEY}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK:', d[1][0])"
# Expected: OK: Hawaii
```

---

## Step 2 — Property Data (most important, 30 minutes)

This is the primary outcome data. Maui County publishes the Real Property Assessment Roll publicly
but not as a bulk download — you must request it.

**Source:** Maui County Real Property Assessment Division
**URL:** https://www.mauicounty.gov/294/Real-Property-Assessment

**Steps:**
1. Navigate to the page above
2. Look for "Assessment Data Downloads" or "Public Data Exports"
3. Request or download the CSV export of the full assessment roll
4. Alternatively, contact the Assessment Division directly:
   - Phone: (808) 270-7297
   - Email: rpa@mauicounty.gov
   - Request: "Full assessment roll export with sales history, 2018–2024, CSV format"

**Expected file:** `maui_assessor.csv` with columns including parcel ID, sale date, sale price,
square footage, year built, zoning code, TMK (Tax Map Key), and GPS coordinates.

**Placement:**
```bash
cp /path/to/maui_assessor.csv data/raw/parcels/maui_assessor.csv
```

**Verification:**
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('data/raw/parcels/maui_assessor.csv')
print('Rows:', len(df))
print('Columns:', list(df.columns)[:10])
print('Date range:', df['sale_date'].min(), '--', df['sale_date'].max())
"
# Expected: >50,000 rows, sale_date spanning 2018–2024
```

**Fallback:** If the county does not respond within 5 business days, the Redfin neighborhood
tracker (Step 5) provides ZIP-level price indices that can substitute for parcel-level analysis
in Phase 2 (SCM). Phase 1 (hedonic + DiD) requires parcel-level data.

---

## Step 3 — Fire Perimeter (2 minutes, auto-downloaded)

The 2023 Lahaina fire perimeter is automatically downloaded by `src/ingest/fire.py` from the
National Interagency Fire Center (NIFC).

**Auto-download:**
```bash
python3 -c "from src.ingest.fire import fetch_fire_perimeter; fetch_fire_perimeter()"
```

**Source URL:** https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_YTD/FeatureServer/0

**Expected output:** `data/raw/fire/lahaina_perimeter.geojson` (~50 KB)

**Verification:**
```bash
python3 -c "
import geopandas as gpd
gdf = gpd.read_file('data/raw/fire/lahaina_perimeter.geojson')
print('Perimeter area (km2):', round(gdf.to_crs(32604).area.sum() / 1e6, 2))
print('Bounding box:', gdf.total_bounds)
"
# Expected: area ~11 km2, bounding box near [-156.7, 20.8, -156.6, 20.9]
```

**Fallback:** If the ArcGIS REST endpoint is down, the Maui County Emergency Management Agency
also hosts the perimeter at https://www.mauicounty.gov/2190/Maui-Fires. Download the KML and
convert: `ogr2ogr -f GeoJSON data/raw/fire/lahaina_perimeter.geojson lahaina_fire.kml`

---

## Step 4 — WUI Classification (5 minutes, manual)

The Wildland-Urban Interface shapefile classifies every U.S. parcel as WUI or non-WUI. This
is required to identify which Maui properties face elevated wildfire exposure.

**Source:** USFS Research Data Archive — Dataset RDS-2015-0047-3
**URL:** https://www.fs.usda.gov/rds/archive/catalog/RDS-2015-0047-3

**Steps:**
1. Navigate to the URL above
2. Click **Download** — select the national-level shapefile (~2 GB compressed)
3. Extract and locate `wui_conus.shp` (the conterminous-US WUI classification layer)

**Placement:**
```bash
cp -r /path/to/extracted/wui/ data/raw/wui/
# Required: data/raw/wui/wui_conus.shp (and associated .dbf, .shx, .prj files)
```

**Verification:**
```bash
python3 -c "
import geopandas as gpd
gdf = gpd.read_file('data/raw/wui/wui_conus.shp', bbox=(-157.0, 20.5, -155.9, 21.1))
print('WUI records in Maui bounding box:', len(gdf))
print('WUI classes present:', sorted(gdf['WUI_Class'].unique()))
"
# Expected: >1000 records, WUI classes include 'Wildland-Urban Interface' and 'Wildland-Urban Intermix'
```

**Alternative:** The Silvis Lab at University of Wisconsin maintains a more recent (2020) WUI
layer: https://silvis.forest.wisc.edu/data/wui-change/. Contact them for research access.

---

## Step 5 — Price Indices (15 minutes, auto-downloaded)

### Zillow ZHVI by ZIP

Zillow publishes monthly house price indices by ZIP code as a public bulk CSV.

**Auto-download:**
```bash
python3 -c "from src.ingest.zillow_zip import fetch_zhvi; fetch_zhvi()"
```

**Expected output:** `data/raw/zillow/zhvi_zip.csv` (~30 MB, ~30,000 rows for Hawaii ZIPs)

**Verification:**
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('data/raw/zillow/zhvi_zip.csv')
hi = df[df['State'] == 'HI']
print('Hawaii ZIPs:', len(hi))
print('Date range:', df.columns[-1], '(most recent column)')
"
# Expected: ~30 Hawaii ZIPs, columns through present year
```

### FHFA House Price Index by ZIP

The Federal Housing Finance Agency publishes quarterly repeat-sales HPI by ZIP.

**Auto-download:**
```bash
python3 -c "from src.ingest.fred import fetch_fhfa_zip_hpi; fetch_fhfa_zip_hpi()"
```

**Source URL:** https://www.fhfa.gov/data/hpi/datasets?tab=additional-data
(file: HPI_AT_BDL_ZIP5.xlsx — All-Transactions HPI at the 5-Digit ZIP Code Level)

**Expected output:** `data/raw/fhfa/hpi_zip.parquet` (~5 MB)

**Verification:**
```bash
python3 -c "
import pandas as pd
df = pd.read_parquet('data/raw/fhfa/hpi_zip.parquet')
hi = df[df['zip'].str.startswith('967')]
print('Hawaii ZIP-quarters:', len(hi))
print('Year range:', hi['year'].min(), '--', hi['year'].max())
"
# Expected: >500 Hawaii ZIP-quarters, spanning 1996–present
```

---

## Step 6 — FRED Macro Series (5 minutes, auto-downloaded)

FRED macro controls (30-year mortgage rate, unemployment, median income) are auto-fetched when
`FRED_API_KEY` is in your `.env`.

**Auto-download:**
```bash
python3 -c "from src.ingest.fred import fetch_fred_series; fetch_fred_series()"
```

**Expected output:** `data/raw/fred/series.parquet`

**Series fetched:**
| FRED ID | Description |
|---------|-------------|
| `MORTGAGE30US` | 30-year fixed mortgage rate (weekly) |
| `UNRATE` | U.S. unemployment rate (monthly) |
| `MEHOINUSHA672N` | Real median household income (annual) |
| `DFF` | Federal funds effective rate (daily) |
| `CSUSHPISA` | Case-Shiller national HPI (monthly) |

---

## Step 7 — Census ACS (10 minutes, auto-downloaded)

ACS 5-year demographic estimates (income, housing tenure, education) are auto-fetched when
`CENSUS_API_KEY` is in your `.env`.

**Auto-download:**
```bash
python3 -c "from src.ingest.census_acs import fetch_census_acs; fetch_census_acs(state='15')"
```

**Expected output:** `data/raw/census/acs_zip.parquet`

---

## Verification Checklist

After completing all steps, run the automated data check:

```bash
make data-check
```

This script verifies that every required file is present, readable, and has the expected
shape. Expected output:

```
OK: data/raw/parcels/maui_assessor.csv         (58,341 rows)
OK: data/raw/fire/lahaina_perimeter.geojson    (1 polygon)
OK: data/raw/wui/wui_conus.shp                 (present + Maui records found)
OK: data/raw/zillow/zhvi_zip.csv               (Hawaii ZIPs: 31)
OK: data/raw/fhfa/hpi_zip.parquet              (Hawaii ZIP-quarters: 732)
OK: data/raw/fred/series.parquet               (5 series)
OK: data/raw/census/acs_zip.parquet            (Hawaii ZIPs: 31)
ALL REQUIRED DATA PRESENT
```

---

## Common Issues

**`ConnectionError` when downloading FHFA or Zillow:**
Both files are large (~30–100 MB). If your connection drops, re-run the download command —
the ingest modules use chunked streaming and will resume where they left off.

**`KeyError` on parcel CSV columns:**
The column names in the Maui Assessment Roll may vary between export vintages. Check
`data/raw/parcels/maui_assessor.csv` and compare column names to those expected in
`src/ingest/parcel.py`. Open a GitHub issue with `df.columns.tolist()` if they differ.

**WUI shapefile is too large to load:**
`src/ingest/wui.py` automatically clips to a Maui bounding box before loading. If memory
is still an issue, install `pyogrio` (`uv add pyogrio`) which uses lazy spatial reads.

**NIFC ArcGIS endpoint returns empty FeatureCollection:**
The WFIGS endpoint occasionally returns no features if query parameters change. Try the
alternative download from NASA FIRMS: https://firms.modaps.eosdis.nasa.gov/active_fire/
Filter by date range 2023-08-08 to 2023-08-15 and VIIRS instrument for Maui.
