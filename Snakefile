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

# ---------------------------------------------------------------------------
# Phase 2 terminal rule
# ---------------------------------------------------------------------------
rule phase2:
    input:
        "data/raw/zillow/zhvi_zip.csv",
        "data/raw/census/acs_zip_2022.parquet",
        "data/interim/zip_panel.parquet",
        "data/interim/donor_pool.parquet",
        "data/interim/covariate_matrix.npz",
        "results/scm/adh_results.pkl",
        "results/scm/adh_gap_series.parquet",
        "results/scm/gsynth_results.pkl",
        "results/scm/gsynth_gap_series.parquet",
        "results/scm/augsynth_results.pkl",
        "results/scm/augsynth_gap_series.parquet",
        "results/scm/model_comparison.csv",
        "results/inference/placebo_distribution.parquet",
        "results/inference/p_values.json",
        "results/inference/loo_gaps.parquet",
        "results/inference/stability_score.json",

# ---------------------------------------------------------------------------
# Phase 2 ingest rules
# ---------------------------------------------------------------------------
rule fetch_zhvi:
    output:
        "data/raw/zillow/zhvi_zip.csv",
    shell:
        """
        python -c "
from src.ingest.zillow_zip import fetch_zhvi_by_zip
df = fetch_zhvi_by_zip('HI')
df.to_csv('{output}', index=False)
"
        """

rule fetch_acs:
    output:
        "data/raw/census/acs_zip_2022.parquet",
    shell:
        """
        python -c "
from src.ingest.census_acs import fetch_acs_zip
df = fetch_acs_zip(year=2022)
df.to_parquet('{output}', engine='pyarrow')
"
        """

rule build_zip_panel:
    input:
        zhvi="data/raw/zillow/zhvi_zip.csv",
        acs="data/raw/census/acs_zip_2022.parquet",
    output:
        "data/interim/zip_panel.parquet",
    shell:
        """
        python -c "
import pandas as pd
from src.ingest.zip_panel_builder import build_zip_panel
zhvi = pd.read_csv('{input.zhvi}')
acs = pd.read_parquet('{input.acs}')
hta = None
panel = build_zip_panel(zhvi, acs, hta)
panel.to_parquet('{output}', engine='pyarrow')
"
        """

# ---------------------------------------------------------------------------
# Phase 2 SCM rules
# ---------------------------------------------------------------------------
rule build_donor_pool:
    input:
        zip_panel="data/interim/zip_panel.parquet",
        acs="data/raw/census/acs_zip_2022.parquet",
    output:
        pool="data/interim/donor_pool.parquet",
        cov="data/interim/covariate_matrix.npz",
    shell:
        """
        python -c "
import pandas as pd, numpy as np
from src.scm.donor_pool import DonorPool
from src.scm.covariate_matrix import build_covariate_matrix, build_outcome_matrices
panel = pd.read_parquet('{input.zip_panel}')
acs = pd.read_parquet('{input.acs}')
dp = DonorPool(panel)
dp.build()
dp.donor_panel.to_parquet('{output.pool}', engine='pyarrow')
X0, X1, cov_names = build_covariate_matrix(dp, acs)
Y0_pre, Y1_pre, times = build_outcome_matrices(dp)
np.savez('{output.cov}', X0=X0, X1=X1, Y0_pre=Y0_pre, Y1_pre=Y1_pre, covariate_names=cov_names, time_periods=times)
"
        """

rule fit_adh_scm:
    input:
        pool="data/interim/donor_pool.parquet",
        cov="data/interim/covariate_matrix.npz",
    output:
        pkl="results/scm/adh_results.pkl",
        gap="results/scm/adh_gap_series.parquet",
    shell:
        """
        python -c "
import pandas as pd, numpy as np, pickle
from src.scm.adh_scm import ADHSyntheticControl
from src.scm.donor_pool import DonorPool
data = np.load('{input.cov}', allow_pickle=True)
X0, X1, Y0_pre, Y1_pre = data['X0'], data['X1'], data['Y0_pre'], data['Y1_pre']
pool = pd.read_parquet('{input.pool}')
dp = DonorPool.__new__(DonorPool)
dp._donor_panel = pool
dp.treated_zip = '96761'
dp.pre_end = '2023-07'
model = ADHSyntheticControl()
model.fit(X0, X1, Y0_pre, Y1_pre)
with open('{output.pkl}', 'wb') as f: pickle.dump(model, f)
gap = pd.DataFrame({'gap': model.treatment_effect(Y1_pre, Y0_pre)})
gap.to_parquet('{output.gap}', engine='pyarrow')
"
        """

rule fit_gsynth:
    input:
        pool="data/interim/donor_pool.parquet",
        cov="data/interim/covariate_matrix.npz",
    output:
        pkl="results/scm/gsynth_results.pkl",
        gap="results/scm/gsynth_gap_series.parquet",
    shell:
        """
        python -c "
import pandas as pd, numpy as np, pickle
from src.scm.gsynth import GeneralizedSyntheticControl
data = np.load('{input.cov}', allow_pickle=True)
Y0_pre, Y1_pre = data['Y0_pre'], data['Y1_pre']
model = GeneralizedSyntheticControl()
model.fit(Y0_pre, Y1_pre, Y0_pre, Y1_pre, r=2)
with open('{output.pkl}', 'wb') as f: pickle.dump(model, f)
gap = pd.DataFrame({'gap': model.treatment_effect(Y1_pre)})
gap.to_parquet('{output.gap}', engine='pyarrow')
"
        """

rule fit_augsynth:
    input:
        adh="results/scm/adh_results.pkl",
        cov="data/interim/covariate_matrix.npz",
    output:
        pkl="results/scm/augsynth_results.pkl",
        gap="results/scm/augsynth_gap_series.parquet",
    shell:
        """
        python -c "
import pandas as pd, numpy as np, pickle
from src.scm.augsynth import AugmentedSyntheticControl
data = np.load('{input.cov}', allow_pickle=True)
Y0_pre, Y1_pre = data['Y0_pre'], data['Y1_pre']
with open('{input.adh}', 'rb') as f: adh = pickle.load(f)
model = AugmentedSyntheticControl()
model.fit(adh.w_, Y0_pre, Y1_pre, Y0_pre, Y1_pre)
with open('{output.pkl}', 'wb') as f: pickle.dump(model, f)
gap = pd.DataFrame({'gap': model.treatment_effect()})
gap.to_parquet('{output.gap}', engine='pyarrow')
"
        """

rule compare_scms:
    input:
        adh="results/scm/adh_results.pkl",
        gsynth="results/scm/gsynth_results.pkl",
        augsynth="results/scm/augsynth_results.pkl",
    output:
        "results/scm/model_comparison.csv",
    shell:
        """
        python -c "
import pickle
from src.scm.model_registry import ModelRegistry
reg = ModelRegistry()
with open('{input.adh}', 'rb') as f: adh = pickle.load(f)
with open('{input.gsynth}', 'rb') as f: gsynth = pickle.load(f)
with open('{input.augsynth}', 'rb') as f: augsynth = pickle.load(f)
reg.register('ADH', adh, {{}})
reg.register('GSynth', gsynth, {{}})
reg.register('ASCM', augsynth, {{}})
reg.compare_rmspe().to_csv('{output}', index=False)
"
        """

# ---------------------------------------------------------------------------
# Phase 2 inference rules
# ---------------------------------------------------------------------------
rule run_placebos:
    input:
        adh="results/scm/adh_results.pkl",
        pool="data/interim/donor_pool.parquet",
        cov="data/interim/covariate_matrix.npz",
    output:
        dist="results/inference/placebo_distribution.parquet",
        pvals="results/inference/p_values.json",
    shell:
        """
        python -c "
import pandas as pd, numpy as np, pickle, json
from src.scm.donor_pool import DonorPool
from src.scm.adh_scm import ADHSyntheticControl
from src.inference.placebo import InSpacePlacebo
from src.scm.covariate_matrix import build_covariate_matrix, build_outcome_matrices
pool = pd.read_parquet('{input.pool}')
data = np.load('{input.cov}', allow_pickle=True)
with open('{input.adh}', 'rb') as f: adh = pickle.load(f)
dp = DonorPool.__new__(DonorPool)
dp._donor_panel = pool
dp.treated_zip = '96761'
dp.pre_end = '2023-07'
placebo = InSpacePlacebo(ADHSyntheticControl, dp, build_covariate_matrix)
result_df = placebo.run(n_jobs=1)
result_df.to_parquet('{output.dist}', engine='pyarrow')
p = placebo.p_value(adh.rmspe_ratio())
with open('{output.pvals}', 'w') as f: json.dump({{'p_value': p, 'rmspe_ratio': adh.rmspe_ratio()}}, f, indent=2)
"
        """

rule run_loo:
    input:
        adh="results/scm/adh_results.pkl",
        cov="data/interim/covariate_matrix.npz",
        pool="data/interim/donor_pool.parquet",
    output:
        gaps="results/inference/loo_gaps.parquet",
        score="results/inference/stability_score.json",
    shell:
        """
        python -c "
import pandas as pd, numpy as np, pickle, json
from src.inference.loo import LeaveOneOutDiagnostic
from src.scm.donor_pool import DonorPool
data = np.load('{input.cov}', allow_pickle=True)
X0, X1, Y0_pre, Y1_pre = data['X0'], data['X1'], data['Y0_pre'], data['Y1_pre']
with open('{input.adh}', 'rb') as f: adh = pickle.load(f)
pool = pd.read_parquet('{input.pool}')
donors = [z for z in pool['zip_code'].unique() if z != '96761']
loo = LeaveOneOutDiagnostic()
result = loo.run(adh, X0, X1, Y0_pre, Y1_pre, Y0_pre, Y1_pre, donors)
pd.DataFrame(result['loo_gaps']).to_parquet('{output.gaps}', engine='pyarrow')
with open('{output.score}', 'w') as f: json.dump({{'stability_score': loo.stability_score()}}, f, indent=2)
"
        """
