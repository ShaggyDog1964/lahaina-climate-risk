# Data Sources

## Property Transactions (Phase 1)

### Maui County Assessment Roll (primary)
- **Type**: Parcel-level property transactions and attributes
- **URL**: https://www.mauicounty.gov/452/Real-Property-Assessment
- **Access**: Direct CSV download. No account required.
- **Coverage**: All taxable parcels in Maui County; includes historical sale prices and dates.
- **Limitations**: Updated annually; may lag recent transactions by 6–12 months.
- **Local path**: `data/raw/parcels/maui_assessment_roll.csv`
- **Ingest**: `src/ingest/parcel.py::fetch_maui_assessment_roll()`

### Honolulu Real Property Assessment (supplemental)
- **Type**: Parcel-level assessment data for comparison
- **URL**: https://opendata.hawaii.gov (search: "Real Property Assessment")
- **Access**: Socrata open data portal. No account required.
- **Local path**: `data/raw/parcels/honolulu_assessment.csv`
- **Ingest**: `src/ingest/parcel.py::fetch_honolulu_assessment_roll()` (stub)

## Aggregate Price Indices (Phase 2)

### Zillow Home Value Index (ZHVI) by ZIP
- **URL**: https://files.zillowstatic.com/research/public_csvs/zhvi/
- **Access**: Free public bulk download. No account required.
- **Coverage**: Monthly median home values by ZIP code.
- **Ingest**: `src/ingest/zillow_zip.py::fetch_zhvi_by_zip()`

### FHFA House Price Index by ZIP Code
- **URL**: https://www.fhfa.gov/DataTools/Downloads/Documents/HPI/HPI_AT_BDL_ZIP5.xlsx
- **Access**: Free direct download. No account required.
- **Coverage**: Quarterly repeat-sales HPI by 5-digit ZIP, all transactions.
- **Ingest**: `src/ingest/fred.py::fetch_fhfa_zip_hpi()`

### Redfin Research Data — Neighborhood Market Tracker
- **URL**: https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/neighborhood_market_tracker.tsv000.gz
- **Access**: Free S3 bulk download. No account required.
- **Coverage**: Monthly neighborhood-level price and inventory metrics.
- **Ingest**: `src/ingest/redfin.py::fetch_redfin_neighborhood()`

## Macroeconomic Controls

### FRED (Federal Reserve Economic Data)
- **URL**: https://fred.stlouisfed.org/docs/api/api_key.html
- **Access**: Free API. API key required (set `FRED_API_KEY` in `.env`).
- **Series used**: MEHOINUSHAWIA672N, HISTHPI, CSUSHPINSA, UNRATE, FEDFUNDS, MORTGAGE30US
- **Ingest**: `src/ingest/fred.py::fetch_series()`

### Census American Community Survey (ACS) 5-Year
- **URL**: https://api.census.gov/data/key_signup.html
- **Access**: Free API. API key required (set `CENSUS_API_KEY` in `.env`).
- **Ingest**: `src/ingest/census_acs.py::fetch_acs_zip()`

### Hawaii Tourism Authority (HTA) / DBEDT
- **URL**: https://www.hawaiitourismauthority.org/research/
- **Access**: Manual download required. See `src/ingest/hta_tourism.py` for expected format.
- **Ingest**: `src/ingest/hta_tourism.py::fetch_hta_visitors()` (stub)

## Spatial / Climate Data

### NIFC Interagency Fire Perimeters
- **URL**: ArcGIS REST API (see `src/ingest/fire.py`)
- **Access**: Free. No account required.
- **Ingest**: `src/ingest/fire.py::load_fire_perimeter()`

### USDA Forest Service Wildland-Urban Interface (WUI)
- **URL**: https://silvis.forest.wisc.edu/data/wui-change/
- **Access**: Free bulk shapefile download.
- **Local path**: `data/raw/wui/wui_conus.shp`
- **Ingest**: `src/ingest/wui.py::load_wui()`
