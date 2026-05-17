# Next Steps: Data Acquisition
## Status: BLOCKED — pipeline cannot produce valid results without verified transaction data
## Priority order: (1) deed transfers → (2) fix pipeline → (3) expand donor pool → (4) optional adds

---

## Critical Path: Verified Parcel Transaction Data

The `maui_assessor.csv` has a fatal red flag: all 2,636 transactions share a single zoning
code (`zoning = 4`). Real Maui County residential data spans dozens of zoning codes. The
pre-April 2024 transaction records have unclear provenance. Every downstream result is
unreliable until this is resolved. **Do not run Phase 1–3 analyses on `maui_assessor.csv`
until provenance is confirmed or replaced.**

### Option A — Hawaii Bureau of Conveyances (Free, Slow)

The State of Hawaii Bureau of Conveyances (BOC) records all real property deed transfers.
They publish quarterly extract files under the Open Data initiative.

**Contact:**
- Website: https://boc.ehawaii.gov/
- Public portal: https://data.hawaii.gov/ → search "Bureau of Conveyances"
- Direct DBEDT request: https://dbedt.hawaii.gov/economic/databook/
- Phone: (808) 587-0147
- Email: BOC@hawaii.gov

**What to request:**
> "Maui County (Maui, Molokai, Lanai) residential deed transfer records, January 2018
> through June 2026. Fields: TMK (tax map key), grantor, grantee, instrument type,
> recording date, consideration amount (sale price), document type. Residential sales only
> (exclude foreclosures, family transfers at $0 consideration, quitclaim deeds at $10)."

**Expected format:** CSV or fixed-width text with TMK codes matching the format in
`data/raw/Maui Real Property Assessment Roll/pardat26.txt` (e.g., `2-4-008-001`).

**Join key:** TMK code links to `pardat26.txt` for structural attributes (sqft, year built,
bedrooms, bathrooms, zoning). The shapefile in `data/raw/Maui Parcel Shapefile.shp/`
provides centroid lat/lon.

**Verification after receipt:**
```python
import pandas as pd
df = pd.read_csv("boc_maui_transfers.csv")
# Must pass all of:
assert df["zoning"].nunique() > 5, "Single zoning code is synthetic"
assert df["sale_price"].between(50_000, 10_000_000).mean() > 0.8
assert (df["sale_date"] < "2023-08-08").any(), "Need pre-fire transactions"
assert (df["sale_date"] > "2023-08-08").any(), "Need post-fire transactions"
print(df.groupby(pd.to_datetime(df["sale_date"]).dt.year).size())
```

**Expected N:** 5,000–15,000 Maui residential deed transfers from 2018–2026
(ballpark: 1,000–2,000 per year for all of Maui County). Target ≥ 500 parcels with
at least one pre-fire AND one post-fire transaction for the spatial panel.

---

### Option B — ATTOM Data Solutions (Paid, Fast, ~$2–5K)

ATTOM is the standard academic/institutional source for U.S. deed and assessor data.

**Contact:**
- Website: https://www.attomdata.com/solutions/property-data/
- Academic licensing: solutions@attomdata.com
- Request: "Hawaii County deed transfer extract, Maui County, 2018–2026"
- Quote turnaround: 2–5 business days

**Fields to request:** APN (assessor parcel number), TMK, sale date, sale price, instrument
type, arms-length flag, building sq ft, year built, bedrooms, bathrooms, zoning code,
lat/lon centroid.

**Advantage:** ATTOM flags arms-length transactions, excludes non-market transfers
($0, $1 foreclosures, family deeds), and includes both buyer and seller names for
repeat-sales analysis. Faster than BOC extract.

---

### Option C — CoreLogic (Paid, Institutional License)

Similar to ATTOM. Used by the Federal Reserve, Fannie Mae, and most top econometrics
programs. University affiliation often qualifies for academic pricing (~$1–3K for a
county extract).

**Contact:** https://www.corelogic.com/data-analytics/ → "Academic Research"

---

### Option D — Redfin Extended Historical Pull (Free, Limited)

The current `data/raw/REDFIN/*.csv` covers only April 2024–September 2025 (1.5 years).
Redfin Research publishes neighborhood-level data through `src/ingest/redfin.py`, but
parcel-level historical transaction data requires the public listing search tool.

**Limitation:** Redfin only shows listed properties — not off-market or non-MLS sales.
Coverage is ~70–80% of transactions in West Maui (the rest are non-MLS). This will
bias the sample toward higher-value arm's-length sales. Not acceptable as the sole
source but useful as a supplementary check.

**Action:** Download the full Redfin neighborhood tracker history (monthly, all time):
```bash
# Current fetch is filtered to post-2023; extend start date:
python - <<'EOF'
from src.ingest.redfin import fetch_redfin_neighborhood
df = fetch_redfin_neighborhood(region="Hawaii", start_date="2018-01-01")
df.to_parquet("data/raw/redfin/redfin_full_2018_2026.parquet")
print(df.shape, df["period_begin"].min(), df["period_begin"].max())
EOF
```

---

## Data Assembly Order (Once BOC or ATTOM Data Arrives)

```
Step 1: Verify deed transfer file
   - Check zoning diversity (must be >5 unique codes for Maui residential)
   - Check date range coverage (pre-fire: 2018-08-08 to 2023-08-08 baseline)
   - Check N ≥ 5,000 transactions from ≥ 2,000 unique parcels

Step 2: Join to assessment roll
   pardat26.txt  →  deed_transfers.csv  (join on TMK)
   Output: parcels with structural attributes + sale prices + dates

Step 3: Join to fire perimeter and WUI
   fire/lahaina_perimeter.geojson  →  compute dist_to_fire_km for each TMK centroid
   wui/wui_conus.*  →  join WUI flag on census block GEOID

Step 4: Replace maui_assessor.csv
   cp data/raw/parcels/maui_assessor.csv data/raw/parcels/maui_assessor_ORIGINAL_SUSPICIOUS.csv
   # Write verified file to same path so Snakefile rules don't break:
   python scripts/assemble_parcels.py \
       --deed data/raw/boc_maui_transfers.csv \
       --assessor data/raw/Maui\ Real\ Property\ Assessment\ Roll/pardat26.txt \
       --shapefile "data/raw/Maui Parcel Shapefile.shp/" \
       --output data/raw/parcels/maui_assessor.csv

Step 5: Verify assembled file
   python - <<'EOF'
   import pandas as pd
   df = pd.read_csv("data/raw/parcels/maui_assessor.csv")
   assert df["zoning"].nunique() > 5
   assert len(df) >= 5000
   assert df["sale_date"].lt("2023-08-08").any()
   assert df["sale_date"].gt("2023-08-08").any()
   print("VERIFIED:", df.shape)
   print(df[["sale_price","sqft","year_built","zoning","dist_to_fire_km"]].describe())
   EOF
```

---

## Data Already Working — No Action Needed

| Source | File | Status | Notes |
|---|---|---|---|
| Fire perimeter | `data/raw/fire/lahaina_perimeter.geojson` | ✅ Real | NIFC IRWIN ID verified |
| FHFA ZIP HPI | `data/raw/fhfa/hpi_zip.parquet` | ✅ Real | Hawaii ZIPs, 1975–present |
| Zillow ZHVI | `data/raw/zillow/zhvi_zip.csv` | ✅ Real | 78 HI ZIPs × months |
| Census ACS | `data/raw/census/acs_zip_2022.parquet` | ✅ Real | 97 ZIP codes |
| FRED macros | `data/raw/fred/series.parquet` | ✅ Real | 5 series |
| WUI shapefile | `data/raw/wui/wui_conus.*` | ✅ Real | USFS Silvis Lab |
| TIGER tracts | `data/raw/tiger/` | ✅ Real | 2020 Census |
| Maui shapefile | `data/raw/Maui Parcel Shapefile.shp/` | ✅ Real | TMK geometry |
| Assessment roll | `data/raw/Maui Real Property Assessment Roll/pardat26.txt` | ✅ Real | Structural attributes, no prices |
| Redfin (post-fire) | `data/raw/REDFIN/*.csv` | ⚠️ Partial | Apr 2024–Sep 2025 only |

---

## Optional Additions (Secondary Priority)

### HTA Tourism Data

`src/ingest/hta_tourism.py` always raises `NotImplementedError`. Tourism volume
(visitor arrivals, hotel occupancy) is a plausible time-varying control for West Maui.

**Source:**
- Hawaii Tourism Authority Data Book: https://www.hawaiitourismauthority.org/research/databook/
- Direct download: Annual CSV exports available from 2000–present
- Fields: Monthly visitor arrivals by county, hotel occupancy rate by island

**If adding:** Place at `data/raw/hta/hta_visitor_arrivals.csv` and implement
`fetch_hta_tourism()` in `src/ingest/hta_tourism.py`. Add as time-varying control
in the hedonic model (`X_it`).

**Priority:** Low. Tourism shocks are already partially captured by FRED macro controls.
Skip unless a referee asks for it.

### FEMA Damage Assessment

FEMA's Individual Assistance registration data for the 2023 Lahaina fire is publicly
available via FEMA's OpenFEMA API.

```bash
curl "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?disaster=4724" \
  -o data/raw/fema/disaster_4724.json
# Individual Assistance data:
curl "https://www.fema.gov/api/open/v2/HousingAssistanceOwners?disasterNumber=4724" \
  -o data/raw/fema/housing_assistance.json
```

**Use:** Merge on ZIP or block group to separate "physically destroyed" from "risk-exposed
but undamaged" parcels — a cleaner damage channel than WUI classification alone.

### Donor Pool Expansion (Phase 2)

The current 58 donors are all Hawaii ZIPs. For a higher-powered placebo test (N_donors > 100),
add mainland U.S. resort/coastal markets:
- Malibu CA (90265), Santa Barbara CA (93101), Big Bear Lake CA (92315)
- Bend OR (97701), Sedona AZ (86336)

All have FHFA ZIP HPI series. Add them to `src/scm/donor_pool.py` under a new
`extended_donor_pool` flag. With 100+ donors, p = 0.05 is achievable (currently
minimum p = 1/59 = 0.017 with 59 units).
