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
        "data/raw/redfin/hawaii_neighborhoods.parquet",
        "data/raw/fhfa/hpi_zip.parquet",
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
        python3 -c "
from dotenv import load_dotenv; load_dotenv()
from src.ingest.fred import fetch_series
import pandas as pd
df = fetch_series(
    ['MEHOINUSHIA672N','HISTHPI','CSUSHPINSA','UNRATE','FEDFUNDS','MORTGAGE30US'],
    start='2019-01-01', end='2024-12-31'
)
df.to_parquet('{output}', engine='pyarrow')
"
        """

rule fetch_redfin:
    output:
        "data/raw/redfin/hawaii_neighborhoods.parquet",
    log:
        "logs/fetch_redfin.log",
    shell:
        """
        python3 -c "
from src.ingest.redfin import fetch_redfin_neighborhood
fetch_redfin_neighborhood()
" 2>&1 | tee {log}
        """

rule fetch_fhfa_zip:
    output:
        "data/raw/fhfa/hpi_zip.parquet",
    log:
        "logs/fetch_fhfa_zip.log",
    shell:
        """
        python3 -c "
from src.ingest.fred import fetch_fhfa_zip_hpi
fetch_fhfa_zip_hpi()
" 2>&1 | tee {log}
        """

rule fetch_fire:
    output:
        "data/raw/fire/lahaina_perimeter.geojson",
    shell:
        """
        python3 -c "
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
        python3 -c "
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
        python3 -c "
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
        python3 -c "
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
        python3 -c "
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
        python3 -c "
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
        python3 -c "
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
        python3 -c "
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
        python3 -c "
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
        python3 -c "
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
        python3 -c "
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
    log:
        "logs/phase2/fetch_zhvi.log",
    benchmark:
        "benchmarks/phase2/fetch_zhvi.benchmark.txt",
    shell:
        """
        python3 -c "
from src.ingest.zillow_zip import fetch_zhvi_by_zip
df = fetch_zhvi_by_zip('HI')
df.to_csv('{output}', index=False)
"
        """

rule fetch_acs:
    output:
        "data/raw/census/acs_zip_2022.parquet",
    log:
        "logs/phase2/fetch_acs.log",
    benchmark:
        "benchmarks/phase2/fetch_acs.benchmark.txt",
    shell:
        """
        python3 -c "
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
    log:
        "logs/phase2/build_zip_panel.log",
    benchmark:
        "benchmarks/phase2/build_zip_panel.benchmark.txt",
    shell:
        """
        python3 -c "
import pandas as pd
from src.ingest.zip_panel_builder import build_zip_panel
zhvi = pd.read_csv('{input.zhvi}')
acs = pd.read_parquet('{input.acs}')
hta = None
panel = build_zip_panel(zhvi, acs, hta)
panel.to_parquet('{output}', engine='pyarrow')
print(f'Panel shape: {{panel.shape}}, zip_code dtype: {{panel[\"zip_code\"].dtype}}')
" 2>&1 | tee {log}
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
    log:
        "logs/phase2/build_donor_pool.log",
    benchmark:
        "benchmarks/phase2/build_donor_pool.benchmark.txt",
    shell:
        """
        python3 -c "
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
    log:
        "logs/phase2/fit_adh_scm.log",
    benchmark:
        "benchmarks/phase2/fit_adh_scm.benchmark.txt",
    shell:
        """
        python3 -c "
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
pivot = pool.pivot(index='year_month', columns='zip_code', values='log_zhvi').sort_index()
donor_cols = [c for c in pivot.columns if c != '96761']
Y0_all = pivot[donor_cols].values
Y1_all = pivot['96761'].values
model = ADHSyntheticControl()
model.fit(X0, X1, Y0_pre, Y1_pre, Y0_all=Y0_all, Y1_all=Y1_all)
with open('{output.pkl}', 'wb') as f: pickle.dump(model, f)
gap = pd.DataFrame({{'gap': model.treatment_effect(Y1_all, Y0_all)}})
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
    log:
        "logs/phase2/fit_gsynth.log",
    benchmark:
        "benchmarks/phase2/fit_gsynth.benchmark.txt",
    shell:
        """
        python3 -c "
import pandas as pd, numpy as np, pickle
from src.scm.gsynth import GeneralizedSyntheticControl
data = np.load('{input.cov}', allow_pickle=True)
Y0_pre, Y1_pre = data['Y0_pre'], data['Y1_pre']
model = GeneralizedSyntheticControl()
model.fit(Y0_pre, Y1_pre, Y0_pre, Y1_pre, r=2)
with open('{output.pkl}', 'wb') as f: pickle.dump(model, f)
gap = pd.DataFrame({{'gap': model.treatment_effect(Y1_pre)}})
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
    log:
        "logs/phase2/fit_augsynth.log",
    benchmark:
        "benchmarks/phase2/fit_augsynth.benchmark.txt",
    shell:
        """
        python3 -c "
import pandas as pd, numpy as np, pickle
from src.scm.augsynth import AugmentedSyntheticControl
data = np.load('{input.cov}', allow_pickle=True)
Y0_pre, Y1_pre = data['Y0_pre'], data['Y1_pre']
with open('{input.adh}', 'rb') as f: adh = pickle.load(f)
model = AugmentedSyntheticControl()
model.fit(adh.w_, Y0_pre, Y1_pre, Y0_pre, Y1_pre)
with open('{output.pkl}', 'wb') as f: pickle.dump(model, f)
gap = pd.DataFrame({{'gap': model.treatment_effect()}})
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
        python3 -c "
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
        python3 -c "
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
if not adh.is_post_fitted:
    raise RuntimeError('Stale pickle: post_rmspe_ is None. Delete results/scm/adh_results.pkl and re-run fit_adh_scm.')
ratio = adh.rmspe_ratio()
p = placebo.p_value(ratio)
with open('{output.pvals}', 'w') as f:
    json.dump({{'p_value': p, 'rmspe_ratio': ratio, 'pre_rmspe': adh.pre_rmspe_, 'post_rmspe': adh.post_rmspe_}}, f, indent=2)
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
        python3 -c "
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

# ---------------------------------------------------------------------------
# Phase 3 terminal rule
# ---------------------------------------------------------------------------
rule phase3:
    input:
        "data/interim/spatial/price_change.parquet",
        "data/interim/spatial/weights_knn.pkl",
        "data/interim/spatial/weights_idw.pkl",
        "data/interim/spatial/eigenvalues_knn.npy",
        "results/esda/global_morans.json",
        "results/esda/lisa_stats.parquet",
        "results/esda/cluster_labels.parquet",
        "results/spatial/sar_results.pkl",
        "results/spatial/sem_results.pkl",
        "results/spatial/sdm_results.pkl",
        "results/spatial/lesage_pace_effects.parquet",
        "results/spatial/nesting_tests.json",
        "results/gwr/optimal_bandwidth.json",
        "results/gwr/gwr_surface.parquet",

# ---------------------------------------------------------------------------
# Phase 3 spatial outcome
# ---------------------------------------------------------------------------
rule build_spatial_outcome:
    input:
        panel="data/final/panel.parquet",
    output:
        "data/interim/spatial/price_change.parquet",
    shell:
        """
        python3 -c "
import pandas as pd
from src.spatial_models.outcome import build_price_change
panel = pd.read_parquet('{input.panel}')
gdf = build_price_change(panel)
gdf.drop(columns='geometry').to_parquet('{output}', engine='pyarrow')
"
        """

# ---------------------------------------------------------------------------
# Phase 3 weights
# ---------------------------------------------------------------------------
rule build_weights_phase3:
    input:
        "data/interim/spatial/price_change.parquet",
    output:
        knn="data/interim/spatial/weights_knn.pkl",
        idw="data/interim/spatial/weights_idw.pkl",
        eigs="data/interim/spatial/eigenvalues_knn.npy",
    shell:
        """
        python3 -c "
import pandas as pd, geopandas as gpd, pickle, numpy as np
from src.spatial.weights_phase3 import SpatialWeightsFactory
df = pd.read_parquet('{input}')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs='EPSG:4326')
factory = SpatialWeightsFactory()
weights = factory.build_all(gdf)
with open('{output.knn}', 'wb') as f: pickle.dump(weights['knn'], f)
with open('{output.idw}', 'wb') as f: pickle.dump(weights['idw'], f)
W_sparse = factory.to_sparse(weights['knn'])
eigs = factory.eigenvalues(W_sparse)
np.save('{output.eigs}', eigs)
"
        """

# ---------------------------------------------------------------------------
# Phase 3 ESDA
# ---------------------------------------------------------------------------
rule global_morans:
    input:
        price="data/interim/spatial/price_change.parquet",
        weights="data/interim/spatial/weights_knn.pkl",
    output:
        "results/esda/global_morans.json",
    shell:
        """
        python3 -c "
import pandas as pd, geopandas as gpd, pickle, json, numpy as np
from src.esda.morans import GlobalMoransI
from src.spatial.weights_phase3 import SpatialWeightsFactory
df = pd.read_parquet('{input.price}')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs='EPSG:4326')
with open('{input.weights}', 'rb') as f: w = pickle.load(f)
factory = SpatialWeightsFactory()
W_sparse = factory.to_sparse(w)
y = df['y_raw'].fillna(0).values
model = GlobalMoransI().fit(y, W_sparse)
with open('{output}', 'w') as f: json.dump(model.summary(), f, indent=2)
"
        """

rule local_morans:
    input:
        price="data/interim/spatial/price_change.parquet",
        weights="data/interim/spatial/weights_knn.pkl",
    output:
        stats="results/esda/lisa_stats.parquet",
        labels="results/esda/cluster_labels.parquet",
    shell:
        """
        python3 -c "
import pandas as pd, geopandas as gpd, pickle, numpy as np
from src.esda.lisa import LocalMoransI
from src.spatial.weights_phase3 import SpatialWeightsFactory
df = pd.read_parquet('{input.price}')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs='EPSG:4326')
with open('{input.weights}', 'rb') as f: w = pickle.load(f)
factory = SpatialWeightsFactory()
W_sparse = factory.to_sparse(w)
y = df['y_raw'].fillna(0).values
model = LocalMoransI().fit(y, W_sparse)
result_gdf = model.to_geodataframe(gdf)
result_gdf.drop(columns='geometry').to_parquet('{output.stats}', engine='pyarrow')
pd.DataFrame({{'parcel_id': df['parcel_id'] if 'parcel_id' in df.columns else range(len(df)), 'cluster_label': model.cluster_labels_}}).to_parquet('{output.labels}', engine='pyarrow')
"
        """

# ---------------------------------------------------------------------------
# Phase 3 spatial models
# ---------------------------------------------------------------------------
rule fit_sar:
    input:
        price="data/interim/spatial/price_change.parquet",
        weights="data/interim/spatial/weights_knn.pkl",
        eigs="data/interim/spatial/eigenvalues_knn.npy",
    output:
        "results/spatial/sar_results.pkl",
    shell:
        """
        python3 -c "
import pandas as pd, numpy as np, pickle
from src.spatial_models.sar import SpatialLagModel
from src.spatial.weights_phase3 import SpatialWeightsFactory
df = pd.read_parquet('{input.price}')
with open('{input.weights}', 'rb') as f: w = pickle.load(f)
factory = SpatialWeightsFactory()
W_sparse = factory.to_sparse(w)
eigs = np.load('{input.eigs}', allow_pickle=True)
y = df['y_raw'].fillna(0).values
X_cols = [c for c in ['dist_to_fire_km'] if c in df.columns]
X = np.column_stack([np.ones(len(df))] + [df[c].fillna(0).values for c in X_cols])
model = SpatialLagModel().fit(y, X, W_sparse, eigs)
with open('{output}', 'wb') as f: pickle.dump(model, f)
"
        """

rule fit_sem:
    input:
        price="data/interim/spatial/price_change.parquet",
        weights="data/interim/spatial/weights_knn.pkl",
        eigs="data/interim/spatial/eigenvalues_knn.npy",
    output:
        "results/spatial/sem_results.pkl",
    shell:
        """
        python3 -c "
import pandas as pd, numpy as np, pickle
from src.spatial_models.sem import SpatialErrorModel
from src.spatial.weights_phase3 import SpatialWeightsFactory
df = pd.read_parquet('{input.price}')
with open('{input.weights}', 'rb') as f: w = pickle.load(f)
factory = SpatialWeightsFactory()
W_sparse = factory.to_sparse(w)
eigs = np.load('{input.eigs}', allow_pickle=True)
y = df['y_raw'].fillna(0).values
X_cols = [c for c in ['dist_to_fire_km'] if c in df.columns]
X = np.column_stack([np.ones(len(df))] + [df[c].fillna(0).values for c in X_cols])
model = SpatialErrorModel().fit(y, X, W_sparse, eigs)
with open('{output}', 'wb') as f: pickle.dump(model, f)
"
        """

rule fit_sdm:
    input:
        price="data/interim/spatial/price_change.parquet",
        weights="data/interim/spatial/weights_knn.pkl",
        eigs="data/interim/spatial/eigenvalues_knn.npy",
        sar="results/spatial/sar_results.pkl",
    output:
        "results/spatial/sdm_results.pkl",
    shell:
        """
        python3 -c "
import pandas as pd, numpy as np, pickle
from src.spatial_models.sdm import SpatialDurbinModel
from src.spatial.weights_phase3 import SpatialWeightsFactory
df = pd.read_parquet('{input.price}')
with open('{input.weights}', 'rb') as f: w = pickle.load(f)
factory = SpatialWeightsFactory()
W_sparse = factory.to_sparse(w)
eigs = np.load('{input.eigs}', allow_pickle=True)
y = df['y_raw'].fillna(0).values
X_cols = [c for c in ['dist_to_fire_km'] if c in df.columns]
X = np.column_stack([np.ones(len(df))] + [df[c].fillna(0).values for c in X_cols])
X_names = ['intercept'] + X_cols
model = SpatialDurbinModel().fit(y, X, W_sparse, eigs, X_names=X_names)
with open('{output}', 'wb') as f: pickle.dump(model, f)
"
        """

rule lesage_pace:
    input:
        sdm="results/spatial/sdm_results.pkl",
        weights="data/interim/spatial/weights_knn.pkl",
    output:
        "results/spatial/lesage_pace_effects.parquet",
    shell:
        """
        python3 -c "
import pickle
from src.spatial_models.effects import LeSagePaceEffects
from src.spatial.weights_phase3 import SpatialWeightsFactory
with open('{input.sdm}', 'rb') as f: sdm = pickle.load(f)
with open('{input.weights}', 'rb') as f: w = pickle.load(f)
factory = SpatialWeightsFactory()
W_sparse = factory.to_sparse(w)
effects = LeSagePaceEffects().compute(sdm, W_sparse)
effects.summary_table().to_parquet('{output}', engine='pyarrow')
"
        """

rule nesting_tests:
    input:
        sar="results/spatial/sar_results.pkl",
        sem="results/spatial/sem_results.pkl",
        sdm="results/spatial/sdm_results.pkl",
    output:
        "results/spatial/nesting_tests.json",
    shell:
        """
        python3 -c "
import pickle, json
from src.spatial_models.model_registry import SpatialModelRegistry
with open('{input.sar}', 'rb') as f: sar = pickle.load(f)
with open('{input.sem}', 'rb') as f: sem = pickle.load(f)
with open('{input.sdm}', 'rb') as f: sdm = pickle.load(f)
reg = SpatialModelRegistry()
reg.register('SAR', sar)
reg.register('SEM', sem)
reg.register('SDM', sdm)
results = {{
    'comparison': reg.compare().to_dict(),
    'lrt_sdm_vs_sar': reg.lrt('SDM', 'SAR'),
}}
with open('{output}', 'w') as f: json.dump(results, f, indent=2)
"
        """

# ---------------------------------------------------------------------------
# Phase 3 GWR
# ---------------------------------------------------------------------------
rule gwr_bandwidth:
    input:
        "data/interim/spatial/price_change.parquet",
    output:
        bw="results/gwr/optimal_bandwidth.json",
        checkpoint="data/interim/spatial/bw_checkpoint.pkl",
    shell:
        """
        python3 -c "
import pandas as pd, geopandas as gpd, json, numpy as np
from src.gwr.bandwidth import BandwidthSelector
df = pd.read_parquet('{input}')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs='EPSG:4326')
y = df['y_raw'].fillna(0).values
X_cols = [c for c in ['dist_to_fire_km'] if c in df.columns]
X = np.column_stack([np.ones(len(df))] + [df[c].fillna(0).values for c in X_cols])
sel = BandwidthSelector(gdf, y, X, checkpoint_path='{output.checkpoint}')
bw = sel.fit(lower_km=1.0, upper_km=50.0)
with open('{output.bw}', 'w') as f: json.dump({{'bandwidth_km': bw}}, f, indent=2)
"
        """

rule fit_gwr:
    input:
        price="data/interim/spatial/price_change.parquet",
        bw="results/gwr/optimal_bandwidth.json",
    output:
        "results/gwr/gwr_surface.parquet",
    shell:
        """
        python3 -c "
import pandas as pd, geopandas as gpd, json, numpy as np
from src.gwr.gwr_model import GeographicallyWeightedRegression
df = pd.read_parquet('{input.price}')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs='EPSG:4326')
with open('{input.bw}') as f: bw_info = json.load(f)
y = df['y_raw'].fillna(0).values
X_cols = [c for c in ['dist_to_fire_km'] if c in df.columns]
X = np.column_stack([np.ones(len(df))] + [df[c].fillna(0).values for c in X_cols])
X_names = ['intercept'] + X_cols
model = GeographicallyWeightedRegression().fit(gdf, y, X, bw_info['bandwidth_km'])
result_gdf = model.to_geodataframe(gdf, X_names)
result_gdf.drop(columns='geometry').to_parquet('{output}', engine='pyarrow')
"
        """
