"""
Snakemake DAG for Lahaina Climate-Risk Phase 1 Pipeline.

Run: snakemake --cores 4 all
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FIRE_DATE = "2023-08-08"
H3_RESOLUTION = 8
KNN_K = 8

# ---------------------------------------------------------------------------
# Terminal rule
# ---------------------------------------------------------------------------
rule all:
    input:
        # Ingest outputs
        "data/raw/fred/series.parquet",
        "data/raw/fire/lahaina_perimeter.geojson",
        "data/interim/parcels_clean.parquet",
        "data/interim/parcels_wui.parquet",
        # Spatial outputs
        "data/interim/parcels_h3.parquet",
        "data/interim/parcels_bands.parquet",
        "data/interim/weights_knn.gal",
        "data/interim/weights_idw.gal",
        "data/final/panel.parquet",
        # Model outputs
        "results/hedonic_results.pkl",
        "results/hedonic_table.csv",
        "results/att_gt.pkl",
        "results/event_study.csv",
        "results/triple_diff_results.pkl",
        "results/decomposition.csv",
        "results/parallel_trends_test.json",
        "figures/event_study.pdf",

# ---------------------------------------------------------------------------
# Ingest rules
# ---------------------------------------------------------------------------
rule fetch_fred:
    input:
        ".env",
    output:
        "data/raw/fred/series.parquet",
    shell:
        """
        python -c "
from dotenv import load_dotenv; load_dotenv()
from src.ingest.fred import fetch_series
import pandas as pd
df = fetch_series(
    ['MEHOINUSHAWIA672N','HISTHPI','CSUSHPINSA','UNRATE','FEDFUNDS','MORTGAGE30US'],
    start='2019-01-01', end='2024-12-31'
)
df.to_parquet('{output}', engine='pyarrow')
"
        """

rule fetch_fire:
    output:
        "data/raw/fire/lahaina_perimeter.geojson",
    shell:
        """
        python -c "
from src.ingest.fire import load_fire_perimeter
gdf = load_fire_perimeter()
gdf.to_file('{output}', driver='GeoJSON')
"
        """

rule load_parcels:
    input:
        "data/raw/parcels/maui_assessor.csv",
    output:
        "data/interim/parcels_clean.parquet",
    shell:
        """
        python -c "
from src.ingest.parcel import load_maui_parcels
gdf = load_maui_parcels('{input}')
gdf.drop(columns='geometry').to_parquet('{output}', engine='pyarrow')
"
        """

rule join_wui:
    input:
        parcels="data/interim/parcels_clean.parquet",
        wui="data/raw/wui/wui_conus.shp",
    output:
        "data/interim/parcels_wui.parquet",
    shell:
        """
        python -c "
import geopandas as gpd, pandas as pd
from src.ingest.wui import load_wui
parcels = pd.read_parquet('{input.parcels}')
wui = load_wui('{input.wui}')
merged = parcels.merge(wui[['parcel_id','wui_class']], on='parcel_id', how='left')
merged['wui_class'] = merged['wui_class'].fillna('None')
merged.to_parquet('{output}', engine='pyarrow')
"
        """

# ---------------------------------------------------------------------------
# Spatial rules
# ---------------------------------------------------------------------------
rule build_h3:
    input:
        "data/interim/parcels_wui.parquet",
    output:
        "data/interim/parcels_h3.parquet",
    shell:
        """
        python -c "
import geopandas as gpd, pandas as pd
from src.spatial.h3_grid import assign_h3
df = pd.read_parquet('{input}')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs='EPSG:4326')
parcel_h3, _ = assign_h3(gdf, resolution={H3_RESOLUTION})
parcel_h3.drop(columns='geometry').to_parquet('{output}', engine='pyarrow')
"
        """

rule assign_bands:
    input:
        parcels="data/interim/parcels_h3.parquet",
        fire="data/raw/fire/lahaina_perimeter.geojson",
    output:
        "data/interim/parcels_bands.parquet",
    shell:
        """
        python -c "
import geopandas as gpd, pandas as pd
from src.spatial.distance_bands import assign_distance_bands
df = pd.read_parquet('{input.parcels}')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs='EPSG:4326')
fire_gdf = gpd.read_file('{input.fire}')
fire_geom = fire_gdf.to_crs('EPSG:32604').union_all()
result = assign_distance_bands(gdf, fire_geom)
result.drop(columns='geometry').to_parquet('{output}', engine='pyarrow')
"
        """

rule build_weights:
    input:
        "data/interim/parcels_bands.parquet",
    output:
        knn="data/interim/weights_knn.gal",
        idw="data/interim/weights_idw.gal",
    shell:
        """
        python -c "
import geopandas as gpd, pandas as pd
from src.spatial.weights import build_weights, build_inverse_distance_weights
df = pd.read_parquet('{input}')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs='EPSG:4326')
build_weights(gdf, k={KNN_K}, output_path='{output.knn}')
build_inverse_distance_weights(gdf, threshold_km=10.0, output_path='{output.idw}')
"
        """

rule build_panel:
    input:
        parcels="data/interim/parcels_bands.parquet",
        fred="data/raw/fred/series.parquet",
    output:
        "data/final/panel.parquet",
    shell:
        """
        python -c "
import geopandas as gpd, pandas as pd
from src.spatial.panel_builder import build_panel
parcels = pd.read_parquet('{input.parcels}')
gdf = gpd.GeoDataFrame(parcels, geometry=gpd.points_from_xy(parcels.lon, parcels.lat), crs='EPSG:4326')
fred = pd.read_parquet('{input.fred}')
panel = build_panel(gdf, fred, fire_date='{FIRE_DATE}')
panel.to_parquet('{output}', engine='pyarrow')
"
        """

# ---------------------------------------------------------------------------
# Model rules
# ---------------------------------------------------------------------------
rule run_hedonic:
    input:
        "data/final/panel.parquet",
    output:
        pkl="results/hedonic_results.pkl",
        csv="results/hedonic_table.csv",
    shell:
        """
        python -c "
import pandas as pd, pickle
from src.models.hedonic import HedonicModel
panel = pd.read_parquet('{input}')
model = HedonicModel()
results = model.fit(panel)
with open('{output.pkl}', 'wb') as f: pickle.dump(results, f)
model.summary_table().to_csv('{output.csv}')
"
        """

rule run_did_cs:
    input:
        "data/final/panel.parquet",
    output:
        att="results/att_gt.pkl",
        csv="results/event_study.csv",
    shell:
        """
        python -c "
import pandas as pd, pickle
from src.models.did_cs import CallawayAntaCSiD
panel = pd.read_parquet('{input}')
model = CallawayAntaCSiD()
model.fit(panel)
with open('{output.att}', 'wb') as f: pickle.dump(model._results, f)
model.event_study_df().to_csv('{output.csv}', index=False)
"
        """

rule run_triple_diff:
    input:
        "data/final/panel.parquet",
    output:
        pkl="results/triple_diff_results.pkl",
        csv="results/decomposition.csv",
    shell:
        """
        python -c "
import pandas as pd, pickle
from src.models.triple_diff import TripleDifference
panel = pd.read_parquet('{input}')
model = TripleDifference()
results = model.fit(panel)
with open('{output.pkl}', 'wb') as f: pickle.dump(results, f)
model.decompose().to_csv('{output.csv}', index=False)
"
        """

rule test_parallel:
    input:
        "results/event_study.csv",
    output:
        json="results/parallel_trends_test.json",
        pdf="figures/event_study.pdf",
    shell:
        """
        python -c "
import pandas as pd, json
from src.models.parallel_trends import test_parallel_trends, plot_event_study
es = pd.read_csv('{input}')
result = test_parallel_trends(es)
with open('{output.json}', 'w') as f: json.dump(result, f, indent=2)
plot_event_study(es, '{output.pdf}')
"
        """
