# API Reference

Auto-generated from module docstrings. Run `make docs` to regenerate.

---

## Navigation

- [Synthetic Control Methods](#synthetic-control-methods)
- [Causal Identification Models](#causal-identification-models)
- [Spatial Regression Models](#spatial-regression-models)
- [Exploratory Spatial Data Analysis](#exploratory-spatial-data-analysis)
- [Geographically Weighted Regression](#geographically-weighted-regression)
- [Inference](#inference)
- [Spatial Utilities](#spatial-utilities)
- [Data Ingest](#data-ingest)
- [REST API](#rest-api)
- [Output Generation](#output-generation)

---

## Synthetic Control Methods

### `src.scm.adh_scm` — [adh_scm.py](../src/scm/adh_scm.py)

Abadie-Diamond-Hainmueller (2010) Synthetic Control from scratch.

#### `ADHSyntheticControl`

Abadie, Diamond & Hainmueller (2010) Synthetic Control.

Solves:  min_w  (X1 - X0 @ w)' V (X1 - X0 @ w)
         s.t.   w >= 0, sum(w) == 1
V is found by outer loop: min_V  MSPE_pre(w*(V))
where w*(V) is the inner QP solution.

##### `__init__(self) -> 'None'`

Initialize an unfitted ADHSyntheticControl.

Attributes:
    w_: Donor weight vector (J,); None until fit.
    V_: Diagonal importance-weight matrix (k x k); None until fit.
    pre_rmspe_: Pre-period RMSPE of the synthetic control; None until fit.
    post_rmspe_: Post-period RMSPE; None until computed.
    _donor_names: Optional list of donor labels passed to fit().
    converged_: True if the outer L-BFGS-B optimization converged.
    _T0_: Number of pre-treatment time periods; None until fit.
    rmspe_ratio_: post_rmspe_ / pre_rmspe_; None until post period is computed.

##### `fit(self, X0: 'np.ndarray', X1: 'np.ndarray', Y0_pre: 'np.ndarray', Y1_pre: 'np.ndarray', donor_names: 'list[str] | None' = None, Y0_all: 'np.ndarray | None' = None, Y1_all: 'np.ndarray | None' = None) -> 'ADHSyntheticControl'`

Fit ADH synthetic control.

Args:
    X0: Donor covariate matrix (k, J).
    X1: Treated covariate vector (k,).
    Y0_pre: Donor pre-period outcomes (T0, J).
    Y1_pre: Treated pre-period outcomes (T0,).
    donor_names: Optional list of donor labels.

Returns:
    self

##### `post_rmspe(self, Y1_post: 'np.ndarray', Y0_post: 'np.ndarray') -> 'float'`

RMSPE over post-treatment period.

##### `predict(self, Y0_all: 'np.ndarray') -> 'np.ndarray'`

Synthetic control series: Y0_all @ w_.

##### `rmspe_ratio(self) -> 'float'`

Ratio of post-RMSPE to pre-RMSPE.

##### `summary(self) -> 'dict'`

Return model summary dict.

##### `treatment_effect(self, Y1_all: 'np.ndarray', Y0_all: 'np.ndarray') -> 'np.ndarray'`

Gap series: Y1_all - synthetic.

### `src.scm.gsynth` — [gsynth.py](../src/scm/gsynth.py)

Generalized Synthetic Control (Xu 2017) — interactive fixed effects.

#### `GeneralizedSyntheticControl`

Xu (2017) Generalized Synthetic Control via EM/IFE.

Model: Y_it = delta_it * D_it + lambda_i' F_t + eps_it
Estimate F (T x r) and Lambda (r x J) from donor panel via alternating LS.

##### `__init__(self) -> 'None'`

Initialize an unfitted GeneralizedSyntheticControl.

Attributes:
    F_: Pre-period factor matrix (T0 x r); None until fit.
    F_full_: Full-period factor matrix (T x r) extending F_ to post period; None until fit.
    lambda_1_: Treated unit factor loadings (r,); None until fit.
    lambda_0_: Donor factor loadings (r x J); None until fit.
    pre_rmspe_: Pre-period root mean squared prediction error; None until fit.
    r_: Number of latent factors used in the fitted model; None until fit.

##### `fit(self, Y0_pre: 'np.ndarray', Y1_pre: 'np.ndarray', Y0_all: 'np.ndarray', Y1_all: 'np.ndarray', r: 'int' = 2) -> 'GeneralizedSyntheticControl'`

Fit IFE model via alternating LS (EM-like).

Args:
    Y0_pre: Donor pre-period outcomes (T0, J).
    Y1_pre: Treated pre-period outcomes (T0,).
    Y0_all: Donor full-period outcomes (T, J).
    Y1_all: Treated full-period outcomes (T,).
    r: Number of latent factors.

Returns:
    self

##### `select_r(self, Y0_pre: 'np.ndarray', Y1_pre: 'np.ndarray', r_max: 'int' = 5) -> 'int'`

Select r via leave-one-out CV on donors.

Returns:
    Optimal r in {1, ..., r_max}.

##### `treatment_effect(self, Y1_all: 'np.ndarray') -> 'np.ndarray'`

Gap series: Y1_all - counterfactual.

### `src.scm.augsynth` — [augsynth.py](../src/scm/augsynth.py)

Augmented Synthetic Control Method (Ben-Michael et al. 2021).

#### `AugmentedSyntheticControl`

Ben-Michael, Feller & Rothstein (2021) ASCM.

Corrects ADH weights for pre-period imbalance via ridge regression:
tau_t^ASCM = (Y1t - sum_j w_j^SCM Y_jt) - (m̂_1t - sum_j w_j^SCM m̂_jt)
where m̂_it = ridge prediction using pre-period outcomes as features.

##### `__init__(self) -> 'None'`

Initialize an unfitted AugmentedSyntheticControl.

Attributes:
    tau_ascm_: Bias-corrected treatment effect series (None until fit).
    tau_raw_: Raw SCM gap Y1 - Y0@w_adh (None until fit).
    bias_correction_: Ridge bias term m̂_1t - sum_j w_j m̂_jt (None until fit).
    lambda_ridge_: Ridge regularization parameter used for bias correction.
    _ridge: Last fitted sklearn Ridge estimator (reference only).

##### `fit(self, w_adh: 'np.ndarray', Y0_pre: 'np.ndarray', Y1_pre: 'np.ndarray', Y0_all: 'np.ndarray', Y1_all: 'np.ndarray', lambda_ridge: 'float | None' = None) -> 'AugmentedSyntheticControl'`

Fit ASCM given ADH weights.

Args:
    w_adh: ADH donor weights (J,).
    Y0_pre: Donor pre-period outcomes (T0, J).
    Y1_pre: Treated pre-period outcomes (T0,).
    Y0_all: Donor all-period outcomes (T, J).
    Y1_all: Treated all-period outcomes (T,).
    lambda_ridge: Ridge regularization; tuned by LOOCV if None.

Returns:
    self

##### `treatment_effect(self) -> 'np.ndarray'`

Return ASCM treatment effect series.

### `src.scm.donor_pool` — [donor_pool.py](../src/scm/donor_pool.py)

Donor pool construction for synthetic control.

#### `DonorPool`

Screen and manage the donor pool for synthetic control.

Args:
    panel: Zip-level panel with [zip_code, year_month, log_zhvi, ...].
    treated_zip: Zip code of treated unit.
    pre_end: Last pre-treatment year_month (inclusive), e.g. "2023-07".

##### `__init__(self, panel: 'pd.DataFrame', treated_zip: 'str' = '96761', pre_end: 'str' = '2023-07') -> 'None'`

Initialize the DonorPool with a zip-level panel.

Args:
    panel: DataFrame with at least columns [zip_code, year_month, log_zhvi].
        zip_code will be coerced to zero-padded 5-character str if needed.
    treated_zip: Zip code of the treated unit (Lahaina, default "96761").
    pre_end: Last pre-treatment period as "YYYY-MM" (inclusive).

Attributes:
    panel: Copy of the input panel with zip_code coerced to str.
    treated_zip: Zero-padded treated zip code string.
    pre_end: Pre-treatment end period string.
    _donors: Cached list of donor zip codes after build(); None until then.
    _donor_panel: Subset of panel containing donors + treated; None until build().

##### `build(self, min_r2: 'float' = 0.6) -> 'list[str]'`

Run all screens and cache donor list.

Returns:
    List of donor zip codes.

##### `filter_hawaii_zips(self) -> 'list[str]'`

Return all zips except treated.

##### `screen_on_data_quality(self, max_missing_pct: 'float' = 0.1) -> 'list[str]'`

Drop zips with >max_missing_pct missing log_zhvi months.

##### `screen_on_pretrend(self, min_r2: 'float' = 0.6) -> 'list[str]'`

Keep donors with pre-period R² ≥ min_r2 AND correlation ≥ 0.5 with treated.

### `src.scm.model_registry` — [model_registry.py](../src/scm/model_registry.py)

Model registry for SCM variants.

#### `ModelRegistry`

Dict-like container mapping model name → fitted SCM + metadata.

##### `__init__(self) -> 'None'`

Initialize an empty ModelRegistry.

Attributes:
    _models: Internal dict mapping model name strings to
        {"model": fitted_object, "meta": metadata_dict} entries.

##### `compare_rmspe(self) -> 'pd.DataFrame'`

Return DataFrame comparing pre-RMSPE, post-RMSPE, ratio across models.

##### `get(self, name: 'str') -> 'dict'`

Return registered entry by name.

##### `register(self, name: 'str', model: 'object', meta: 'dict') -> 'None'`

Register a fitted model.

Args:
    name: Model identifier (e.g. "ADH", "GSynth", "ASCM").
    model: Fitted SCM object.
    meta: Arbitrary metadata dict.

---

## Causal Identification Models

### `src.models.hedonic` — [hedonic.py](../src/models/hedonic.py)

Hedonic pricing model for Lahaina parcel transactions.

#### `HedonicModel`

OLS hedonic price model with census-block and year-month fixed effects.

Specification:
    log_price ~ structure_sqft + land_area_sqft + year_built
              + C(zoning) + C(fe_block) + C(fe_yearmonth)

Uses HC3 heteroskedasticity-robust standard errors.

##### `__init__(self) -> 'None'`

Initialize HedonicModel.

##### `fit(self, panel: 'pd.DataFrame') -> 'sm_lm.RegressionResultsWrapper'`

Fit the hedonic OLS model with HC3 standard errors.

Args:
    panel: Long-panel DataFrame with columns [log_price, structure_sqft,
        land_area_sqft, year_built, zoning, fe_block, fe_yearmonth].

Returns:
    Fitted statsmodels RegressionResultsWrapper.

Raises:
    KeyError: If required columns are missing from panel.

##### `summary_table(self) -> 'pd.DataFrame'`

Return a tidy summary DataFrame of estimated coefficients.

Returns:
    DataFrame with columns [coef, se, t, p, ci_lower_95, ci_upper_95].

Raises:
    RuntimeError: If fit() has not been called.

### `src.models.did_cs` — [did_cs.py](../src/models/did_cs.py)

Callaway-Sant'Anna (2021) staggered DiD implementation.

#### `CallawayAntaCSiD`

Callaway-Sant'Anna (2021) heterogeneity-robust DiD estimator.

Wraps the csdid library with a clean interface. Falls back to a
two-way FE approximation when csdid is unavailable.

Reference:
    Callaway, B. & Sant'Anna, P. H. C. (2021). Difference-in-Differences
    with Multiple Time Periods. Journal of Econometrics, 225(2), 200-230.

##### `__init__(self) -> 'None'`

Initialize CallawayAntaCSiD.

##### `event_study_df(self) -> 'pd.DataFrame'`

Return event-study aggregated ATT estimates.

Returns:
    DataFrame with columns [event_time, att, se, ci_lower, ci_upper].

Raises:
    RuntimeError: If fit() has not been called.

##### `fit(self, panel: 'pd.DataFrame', outcome: 'str' = 'log_price', group_var: 'str' = 'treatment_band', time_var: 'str' = 'fe_yearmonth', id_var: 'str' = 'parcel_id') -> 'dict'`

Estimate group-time ATTs using Callaway-Sant'Anna.

Args:
    panel: Long-panel DataFrame.
    outcome: Name of the outcome variable column.
    group_var: Column identifying treatment group. Units with
        group_var == "control" are the comparison group.
    time_var: Column identifying calendar time periods.
    id_var: Column identifying unique units (parcels).

Returns:
    Dictionary with keys:
        - att_gt: DataFrame of ATT(g,t) estimates
        - agg_simple: Simple aggregated ATT (scalar dict)
        - agg_dynamic: Dynamic/event-study aggregated ATTs (DataFrame)

### `src.models.triple_diff` — [triple_diff.py](../src/models/triple_diff.py)

Triple-difference model: WUI x post x distance band.

#### `TripleDifference`

Triple-difference estimator: log_price ~ post x treatment_band x wui_class.

Uses linearmodels PanelOLS with entity and time effects where possible;
falls back to statsmodels OLS when panel indexing is not feasible.

##### `__init__(self) -> 'None'`

Initialize TripleDifference.

##### `decompose(self) -> 'pd.DataFrame'`

Extract and label triple-difference interaction terms.

Returns:
    DataFrame with columns [term, coef, se, interpretation] containing:
        - beta_post_treated_wui: post x treated x WUI effect
        - beta_post_treated_nowui: post x treated (non-WUI) effect
        - belief_update_channel: difference (WUI minus non-WUI)

Raises:
    RuntimeError: If fit() has not been called.

##### `fit(self, panel: 'pd.DataFrame')`

Fit the triple-difference model.

Args:
    panel: Long-panel DataFrame with columns [log_price, post,
        treatment_band, wui_class, parcel_id, fe_yearmonth, ...].

Returns:
    PanelResults or RegressionResultsWrapper from the fitted model.

Raises:
    KeyError: If required columns are missing from panel.

### `src.models.parallel_trends` — [parallel_trends.py](../src/models/parallel_trends.py)

Parallel trends testing and event-study visualization.

#### `plot_event_study(event_study_df: 'pd.DataFrame', output_path: 'str') -> 'None'`

Plot event-study ATT coefficients with 95% CI ribbon.

NBER working paper aesthetic: white background, minimal spines, 10pt font.

Args:
    event_study_df: DataFrame with columns [event_time, att, ci_lower, ci_upper].
    output_path: File path for the saved figure (PDF or PNG).

Returns:
    None. Saves figure to output_path.

#### `test_parallel_trends(event_study_df: 'pd.DataFrame') -> 'dict'`

Test for parallel pre-trends by regressing pre-period ATTs on event_time.

Args:
    event_study_df: DataFrame with columns [event_time, att, se, ci_lower, ci_upper].

Returns:
    Dictionary with keys:
        - slope: OLS slope of pre-period ATTs on event_time
        - p_value: p-value for the slope coefficient
        - passes: True if p_value > 0.10 (fail to reject flat pre-trends)

Raises:
    ValueError: If fewer than 2 pre-period observations are present.

---

## Spatial Regression Models

### `src.spatial_models.sar` — [sar.py](../src/spatial_models/sar.py)

Spatial Autoregressive (Lag) Model via concentrated log-likelihood.

#### `SpatialLagModel`

SAR: y = rho*Wy + X*beta + eps, eps ~ N(0, sigma^2*I).

Estimated by concentrated ML over rho.

##### `fit(self, y: 'np.ndarray', X: 'np.ndarray', W: 'sp.csr_matrix', eigenvalues: 'np.ndarray', x_names: 'list[str] | None' = None) -> 'SpatialLagModel'`

Fit the SAR model y = rho*Wy + X*beta + eps via concentrated ML.

The concentrated log-likelihood over rho is:
  L(rho) = log|I - rho*W| - (n/2) * log(sigma^2(rho))
where sigma^2(rho) = ||Ay - X*beta(rho)||^2 / n and A = I - rho*W.
beta(rho) is obtained by OLS on the filtered system Ay ~ X.

Standard errors are derived from the numerical Hessian of the full
log-likelihood evaluated at (rho_hat, beta_hat).

Args:
    y: Outcome vector of length n. Must have nonzero variance.
    X: Design matrix (n, k), including intercept if desired.
    W: Row-standardized spatial weights matrix (n x n, csr_matrix).
    eigenvalues: Real eigenvalues of W (length n); used to compute
        log|I - rho*W| = sum(log|1 - rho*lambda_i|) and to bound rho.
    x_names: Column labels for X; defaults to ["x0", "x1", ...].

Returns:
    self, with rho_, beta_, sigma2_, log_likelihood_, aic_, bic_,
    se_, t_stats_, p_values_ populated.

Raises:
    ValueError: If y has no variation.

References:
    Ord (1975), Estimation Methods for Models of Spatial Interaction,
    JASA 70(349), eq. 4-6.

##### `predict(self, X: 'np.ndarray', W: 'sp.csr_matrix', y: 'np.ndarray') -> 'np.ndarray'`

Compute fitted values solving (I - rho*W)*yhat = X*beta.

Args:
    X: Design matrix (n, k).
    W: Spatial weights matrix (n x n, csr_matrix).
    y: Outcome vector (unused; retained for API symmetry).

Returns:
    Predicted values of shape (n,) obtained via sparse direct solve.

Raises:
    AttributeError: If fit() has not been called yet.

##### `residuals(self, y: 'np.ndarray', X: 'np.ndarray', W: 'sp.csr_matrix') -> 'np.ndarray'`

Compute residuals y - yhat.

Args:
    y: Observed outcome vector (n,).
    X: Design matrix (n, k).
    W: Spatial weights matrix (n x n, csr_matrix).

Returns:
    Residual vector of shape (n,).

##### `summary(self) -> 'pd.DataFrame'`

Return a DataFrame of parameter estimates and inference statistics.

Returns:
    DataFrame indexed by ["rho"] + x_names with columns:
    coef, se, t_stat, p_value, ci_lo, ci_hi.

Raises:
    AttributeError: If fit() has not been called yet.

### `src.spatial_models.sem` — [sem.py](../src/spatial_models/sem.py)

Spatial Error Model (SEM) via concentrated log-likelihood.

#### `SpatialErrorModel`

SEM: y = X*beta + u, u = lambda*W*u + eps, eps ~ N(0, sigma^2*I).

##### `breusch_pagan(self, residuals: 'np.ndarray', X: 'np.ndarray') -> 'dict'`

Spatial Breusch-Pagan test for heteroskedasticity.

##### `fit(self, y: 'np.ndarray', X: 'np.ndarray', W: 'sp.csr_matrix', eigenvalues: 'np.ndarray', x_names: 'list[str] | None' = None) -> 'SpatialErrorModel'`

Fit the SEM y = X*beta + (I - lambda*W)^{-1}*eps via concentrated ML.

The Kelejian-Prucha (1998) concentrated log-likelihood over lambda is:
  L(lambda) = log|I - lambda*W| - (n/2) * log(sigma^2(lambda))
where the filtered system is B*y ~ B*X with B = I - lambda*W, and
beta(lambda) is obtained by GLS (OLS on filtered data).

Args:
    y: Outcome vector of length n.
    X: Design matrix (n, k), including intercept if desired.
    W: Row-standardized spatial weights matrix (n x n, csr_matrix).
    eigenvalues: Real eigenvalues of W; used for the log-determinant term
        and to bound lambda within stationarity constraints.
    x_names: Column labels for X; defaults to ["x0", "x1", ...].

Returns:
    self, with lambda_, beta_, sigma2_, log_likelihood_, aic_, bic_,
    se_, t_stats_, p_values_ populated.

References:
    Anselin (1988), Spatial Econometrics: Methods and Models, Kluwer, ch. 6.

##### `summary(self) -> 'pd.DataFrame'`

Return a DataFrame of parameter estimates and inference statistics.

Returns:
    DataFrame indexed by ["lambda"] + x_names with columns:
    coef, se, t_stat, p_value, ci_lo, ci_hi.

Raises:
    AttributeError: If fit() has not been called yet.

### `src.spatial_models.sdm` — [sdm.py](../src/spatial_models/sdm.py)

Spatial Durbin Model (SDM) via concentrated log-likelihood.

#### `SpatialDurbinModel`

SDM: y = rho*Wy + X*beta + W*X*theta + eps.

Augments the design matrix with spatially lagged covariates W@X
(excluding the spatial lag of the intercept column).

##### `fit(self, y: 'np.ndarray', X: 'np.ndarray', W: 'sp.csr_matrix', eigenvalues: 'np.ndarray', x_names: 'list[str] | None' = None) -> 'SpatialDurbinModel'`

Fit the Spatial Durbin Model via concentrated log-likelihood.

NOTE: The keyword argument is lowercase ``x_names``, not ``X_names``.

##### `summary(self) -> 'pd.DataFrame'`

Return a DataFrame of parameter estimates and inference statistics.

Returns:
    DataFrame indexed by ["rho"] + x_names + wx_names with columns:
    coef, se, t_stat, p_value.

Raises:
    AttributeError: If fit() has not been called yet.

##### `test_sar_restriction(self, sar_model: 'object') -> 'dict'`

LR test of theta=0 (SDM vs SAR); df = len(theta_).

##### `test_sem_cf_restriction(self, sem_model: 'object', beta_sem: 'np.ndarray') -> 'dict'`

Wald test of common-factor restriction: theta + rho*beta = 0.

### `src.spatial_models.effects` — [effects.py](../src/spatial_models/effects.py)

LeSage-Pace direct/indirect/total effects decomposition for SDM.

#### `LeSagePaceEffects`

Compute direct, indirect, and total effects for SDM via simulation.

##### `compute(self, sdm: 'SDMProtocol', W: 'sp.csr_matrix', n_simulations: 'int' = 1000, seed: 'int' = 42) -> 'LeSagePaceEffects'`

Compute direct, indirect, and total effects for a fitted SDM.

Uses the eigenvalue trace approximation (LeSage & Pace 2009, eq. 2.28–2.31):
  S_r = (I - rho*W)^{-1} * diag(beta_r + W*theta_r)
  direct   = n^{-1} * tr(S_r)
  total    = n^{-1} * 1'S_r*1
  indirect = total - direct

Standard errors are obtained by drawing (rho, beta, theta) from a multivariate
normal approximating the joint posterior and repeating the trace computation.

Args:
    sdm: Fitted SpatialDurbinModel (or any object satisfying SDMProtocol).
    W: Row-standardized spatial weights matrix (n x n, csr_matrix).
    n_simulations: Number of simulation draws for SE estimation.
    seed: Random seed for reproducibility.

Returns:
    self, with effects_df_ populated as a DataFrame with columns:
    variable, direct, indirect, total, direct_se, indirect_se, total_se,
    direct_p, indirect_p, total_p.

References:
    LeSage & Pace (2009), Introduction to Spatial Econometrics, CRC Press,
    ch. 2, eq. 2.28-2.31.

##### `summary_table(self) -> 'pd.DataFrame'`

Return effects_df_ sorted by absolute total effect (descending).

Returns:
    DataFrame with columns variable, direct, indirect, total and their
    standard errors and p-values, sorted by abs(total) descending.

Raises:
    AttributeError: If compute() has not been called yet.

#### `SDMProtocol`

Protocol describing the interface expected from a fitted SDM object.

##### `__init__(self, *args, **kwargs)`

*(no docstring)*

### `src.spatial_models.model_registry` — [model_registry.py](../src/spatial_models/model_registry.py)

Registry for comparing spatial models.

#### `SpatialModelRegistry`

Register and compare spatial models by AIC/BIC/LL.

##### `__init__(self) -> 'None'`

Initialize an empty model registry.

Attributes:
    _models: Internal dict mapping model name strings to fitted model objects.

##### `compare(self) -> 'pd.DataFrame'`

Build a comparison table of all registered models sorted by AIC.

Returns:
    DataFrame with columns: model, spatial_param (rho or lambda),
    log_likelihood, aic, bic. Sorted ascending by aic.

##### `lrt(self, model_a: 'str', model_b: 'str') -> 'dict'`

LR test: H0 = model_b is correctly specified (model_a is unrestricted).

##### `register(self, name: 'str', model: 'object') -> 'None'`

Store a fitted spatial model under the given name.

Args:
    name: Identifier string (e.g. "SAR", "SEM", "SDM").
    model: Any fitted model object exposing rho_/lambda_, log_likelihood_,
        aic_, bic_ attributes.

---

## Exploratory Spatial Data Analysis

### `src.esda.morans` — [morans.py](../src/esda/morans.py)

Global Moran's I with permutation inference (Anselin 1995).

#### `GlobalMoransI`

Global Moran's I statistic with analytical and permutation-based inference.

##### `fit(self, y: 'np.ndarray', W: 'sp.csr_matrix', n_permutations: 'int' = 999, seed: 'int' = 42) -> 'GlobalMoransI'`

Compute Global Moran's I with analytical and permutation inference.

Implements the Cliff-Ord (1981) statistic:
I = (n / S0) * (z'Wz / z'z)
where z = (y - ybar) / std(y) and S0 = sum of all weights.

Args:
    y: Outcome vector of length n.
    W: Row-standardized spatial weights matrix (n x n, csr_matrix).
    n_permutations: Number of random permutations for inference.
    seed: Random seed for reproducibility.

Returns:
    self, with fitted attributes I_, E_I_, Var_I_, z_score_,
    p_value_analytical_, p_value_permutation_, I_perm_distribution_.

References:
    Anselin (1995), eq. 1-4; Cliff & Ord (1981) ch. 1.

##### `summary(self) -> 'dict'`

Return a dict summary of all fitted statistics.

Returns:
    Dict with keys: I, E_I, Var_I, z_score, p_value_analytical,
    p_value_permutation.

Raises:
    AttributeError: If fit() has not been called yet.

### `src.esda.lisa` — [lisa.py](../src/esda/lisa.py)

Local Moran's I (LISA) with permutation inference (Anselin 1995).

#### `LocalMoransI`

Local Moran's I statistics with HH/LL/HL/LH/NS cluster labels.

##### `cluster_counts(self) -> 'dict[str, int]'`

Return counts of each LISA cluster label.

Returns:
    Dict mapping each label (HH, LL, HL, LH, NS) to its observation count.
    All five labels are always present (defaulting to 0).

Raises:
    AttributeError: If fit() has not been called yet.

##### `fit(self, y: 'np.ndarray', W: 'sp.csr_matrix', n_permutations: 'int' = 999, seed: 'int' = 42, alpha: 'float' = 0.05) -> 'LocalMoransI'`

Compute local Moran's I for each observation with permutation p-values.

For observation i: I_i = z_i * sum_j(w_ij * z_j)
where z = (y - ybar) / std(y).

Cluster labels follow the Anselin (1995) quadrant scheme:
HH (high-high), LL (low-low), HL (high-low), LH (low-high), NS (not significant).

Args:
    y: Outcome vector of length n.
    W: Row-standardized spatial weights matrix (n x n, csr_matrix).
    n_permutations: Number of random permutations per observation.
    seed: Random seed for reproducibility.
    alpha: Significance threshold for cluster label assignment.

Returns:
    self, with fitted attributes I_local_, p_values_, cluster_labels_.

References:
    Anselin (1995), Local Indicators of Spatial Association — LISA,
    Geographical Analysis 27(2), eq. 4-7.

##### `to_geodataframe(self, gdf: 'gpd.GeoDataFrame') -> 'gpd.GeoDataFrame'`

Attach LISA results as columns to a copy of the input GeoDataFrame.

Args:
    gdf: GeoDataFrame whose row order matches the y array passed to fit().

Returns:
    Copy of gdf with added columns: I_local, p_value, cluster_label.

Raises:
    AttributeError: If fit() has not been called yet.

---

## Geographically Weighted Regression

### `src.gwr.bandwidth` — [bandwidth.py](../src/gwr/bandwidth.py)

GWR bandwidth selection via golden-section search on AICc.

#### `BandwidthSelector`

Select optimal GWR bandwidth via golden-section AICc minimization.

##### `__init__(self, gdf: 'gpd.GeoDataFrame', y: 'np.ndarray', X: 'np.ndarray', kernel: 'str' = 'bisquare', criterion: 'str' = 'AICc', checkpoint_path: 'str' = 'data/interim/spatial/bw_checkpoint.pkl') -> 'None'`

Initialize the bandwidth selector and precompute pairwise distances.

Args:
    gdf: GeoDataFrame of observation locations (any CRS; reprojected to EPSG:32604).
    y: Outcome vector of length n.
    X: Design matrix of shape (n, k).
    kernel: Kernel type — "bisquare" or "gaussian".
    criterion: Information criterion to minimize — currently "AICc".
    checkpoint_path: Path for pickle-based search state checkpointing.

Attributes:
    _gdf: Reprojected GeoDataFrame (EPSG:32604, index reset).
    _y: Outcome array.
    _X: Design matrix.
    _kernel: Kernel function name.
    _criterion: Selection criterion name.
    _checkpoint_path: Checkpoint file path string.
    _evaluations: List of (bandwidth_km, criterion_value) pairs evaluated so far.
    _dists: Precomputed pairwise Euclidean distance matrix (n x n, metres).

##### `checkpoint(self, state: 'dict', path: 'str | None' = None) -> 'None'`

Pickle the current search state to disk.

Args:
    state: Dict to serialize (typically contains lower, upper, evaluations).
    path: Override checkpoint file path; uses self._checkpoint_path if None.

##### `fit(self, lower_km: 'float' = 1.0, upper_km: 'float' = 50.0) -> 'float'`

Select the optimal GWR bandwidth by minimizing AICc over [lower_km, upper_km].

Resumes from a checkpoint if one exists; persists the final state afterward.

Args:
    lower_km: Lower bound of the search interval in kilometres.
    upper_km: Upper bound of the search interval in kilometres.

Returns:
    Optimal bandwidth in kilometres (midpoint of converged golden-section interval).

##### `golden_section_search(self, lower: 'float', upper: 'float', tol: 'float' = 1.0) -> 'float'`

Run golden-section search with periodic checkpointing.

##### `resume_from_checkpoint(self, path: 'str | None' = None) -> 'dict | None'`

Load a previously saved search state from disk.

Args:
    path: Override checkpoint file path; uses self._checkpoint_path if None.

Returns:
    Unpickled state dict if the checkpoint file exists, else None.

### `src.gwr.gwr_model` — [gwr_model.py](../src/gwr/gwr_model.py)

Geographically Weighted Regression (GWR).

#### `GeographicallyWeightedRegression`

GWR with bisquare or gaussian kernel.

NEVER inverts (I-rhoW) as a dense matrix.
Uses local WLS at each observation.

##### `coefficient_surface(self, var_name: 'str', x_names: 'list[str]') -> 'np.ndarray'`

Return the local coefficient vector for a single predictor.

Args:
    var_name: Name of the predictor variable (must appear in x_names).
    x_names: Ordered list of all predictor names used in fit().

Returns:
    Array of shape (n,) containing the local beta for var_name at each location.

Raises:
    ValueError: If var_name is not in x_names.
    AttributeError: If fit() has not been called yet.

##### `fit(self, gdf: 'gpd.GeoDataFrame', y: 'np.ndarray', X: 'np.ndarray', bandwidth_km: 'float', kernel: 'str' = 'bisquare') -> 'GeographicallyWeightedRegression'`

Fit GWR by computing local WLS at every observation location.

Projects gdf to EPSG:32604, builds the pairwise distance matrix, then
calls _fit_internal. After fitting, AICc is available via self.aicc_.

Args:
    gdf: GeoDataFrame of observation locations (any CRS).
    y: Outcome vector of length n.
    X: Design matrix of shape (n, k), including intercept column if desired.
    bandwidth_km: Kernel bandwidth in kilometres.
    kernel: Kernel type — "bisquare" or "gaussian".

Returns:
    self, with all local_params_, local_se_, local_t_, y_hat_,
    residuals_, hat_diag_, sigma2_local_, effective_df_, aicc_ populated.

References:
    Fotheringham, Brunsdon & Charlton (2002), Geographically Weighted
    Regression, Wiley, ch. 2.

##### `to_geodataframe(self, gdf: 'gpd.GeoDataFrame', x_names: 'list[str]') -> 'gpd.GeoDataFrame'`

Attach local GWR coefficients and diagnostics to a GeoDataFrame.

Args:
    gdf: GeoDataFrame whose row order matches the y array passed to fit().
    x_names: Names for the k columns of X (e.g. ["intercept", "dist_to_fire"]).

Returns:
    Copy of gdf with columns: beta_<name>, t_<name> for each x_name,
    plus y_hat, residual, sigma2_local.

Raises:
    AttributeError: If fit() has not been called yet.

---

## Inference

### `src.inference.placebo` — [placebo.py](../src/inference/placebo.py)

In-space placebo inference for synthetic control.

#### `InSpacePlacebo`

In-space placebo test: designate each donor as pseudo-treated.

Args:
    scm_class: Class with .fit(X0, X1, Y0_pre, Y1_pre) interface.
    donor_pool: Fitted DonorPool object.
    covariate_matrix_fn: Callable returning (X0, X1, covariate_names).

##### `__init__(self, scm_class, donor_pool, covariate_matrix_fn) -> 'None'`

Initialize the in-space placebo runner.

Args:
    scm_class: SCM class with a .fit(X0, X1, Y0_pre, Y1_pre) interface
        (e.g. ADHSyntheticControl).
    donor_pool: Fitted DonorPool object providing the panel and metadata.
    covariate_matrix_fn: Callable returning (X0, X1, covariate_names) for
        a given DonorPool.

Attributes:
    scm_class: The SCM class to instantiate for each placebo run.
    donor_pool: The fitted DonorPool object.
    covariate_matrix_fn: Covariate builder callable.
    placebo_df: DataFrame of placebo results (None until run() is called).
    _treated_pre_rmspe: Pre-RMSPE of the actual treated unit (None until set).

##### `discard_poor_fit(self, max_pre_rmspe_multiple: 'float' = 2.0) -> 'InSpacePlacebo'`

Drop placebos with pre-RMSPE > multiple × treated pre-RMSPE.

##### `p_value(self, treated_ratio: 'float') -> 'float'`

Fraction of placebos with RMSPE ratio ≥ treated ratio.

##### `p_values(self) -> 'dict'`

Return dict with p_full and p_trimmed (if discard_poor_fit was called).

Returns:
    Dict with keys: p_full, p_trimmed, n_placebos_full, n_placebos_trimmed.

##### `run(self, n_jobs: 'int' = -1) -> 'pd.DataFrame'`

Run in-space placebo for each donor zip.

Args:
    n_jobs: Number of parallel jobs (-1 = all cores).

Returns:
    DataFrame with [zip_code, pre_rmspe, post_rmspe, rmspe_ratio, gap_*].

##### `set_treated_pre_rmspe(self, value: 'float') -> 'None'`

Set the treated unit's pre-RMSPE for discard_poor_fit.

### `src.inference.loo` — [loo.py](../src/inference/loo.py)

Leave-one-out robustness diagnostics for synthetic control.

#### `LeaveOneOutDiagnostic`

Leave-one-out robustness check for ADH SCM.

##### `__init__(self) -> 'None'`

Initialize an empty LeaveOneOutDiagnostic.

Attributes:
    _result: Cached result dict from the most recent run() call (None until run).
    _base_gap: Gap series for the full donor pool (None until run).

##### `run(self, scm, X0: 'np.ndarray', X1: 'np.ndarray', Y0_pre: 'np.ndarray', Y1_pre: 'np.ndarray', Y0_all: 'np.ndarray', Y1_all: 'np.ndarray', donor_names: 'list[str]') -> 'dict'`

Refit SCM dropping each high-weight donor.

Args:
    scm: Fitted ADHSyntheticControl (or compatible) object.
    X0: Donor covariate matrix (k, J).
    X1: Treated covariate vector (k,).
    Y0_pre: Donor pre-period outcomes (T0, J).
    Y1_pre: Treated pre-period outcomes (T0,).
    Y0_all: Donor all-period outcomes (T, J).
    Y1_all: Treated all-period outcomes (T,).
    donor_names: Donor zip labels.

Returns:
    Dict with keys loo_gaps, base_gap, pre_rmspes.

##### `stability_score(self) -> 'float'`

Max absolute deviation of any LOO gap from base gap (post-period).

### `src.inference.rmspe` — [rmspe.py](../src/inference/rmspe.py)

RMSPE utility functions for synthetic control inference.

#### `gap_series(Y1: 'np.ndarray', Y_synth: 'np.ndarray') -> 'np.ndarray'`

Element-wise gap: Y1 - synthetic.

#### `post_rmspe(Y1_post: 'np.ndarray', Y_synth_post: 'np.ndarray') -> 'float'`

Root mean squared prediction error over the post-treatment period.

#### `pre_rmspe(Y1_pre: 'np.ndarray', Y_synth_pre: 'np.ndarray') -> 'float'`

Root mean squared prediction error over the pre-treatment period.

#### `rmspe_ratio(pre: 'float', post: 'float') -> 'float'`

Ratio of post-RMSPE to pre-RMSPE.

---

## Spatial Utilities

### `src.spatial.weights_phase3` — [weights_phase3.py](../src/spatial/weights_phase3.py)

Phase 3 spatial weights factory: KNN, IDW, Queen contiguity.

#### `SpatialWeightsFactory`

Build and convert spatial weights matrices for Phase 3.

##### `build_all(self, gdf: 'gpd.GeoDataFrame', k: 'int' = 8, bandwidth_km: 'float' = 10.0) -> 'dict[str, lps_weights.W]'`

Build all three weight specifications and return them in a dict.

Args:
    gdf: GeoDataFrame of observation locations.
    k: Number of nearest neighbours for KNN weights.
    bandwidth_km: IDW distance threshold in kilometres.

Returns:
    Dict with keys "knn", "idw", "queen", each mapping to a
    row-standardized libpysal W object.

##### `build_idw(self, gdf: 'gpd.GeoDataFrame', bandwidth_km: 'float' = 10.0) -> 'lps_weights.W'`

Inverse-distance weights within bandwidth, row-standardized.

##### `build_knn(self, gdf: 'gpd.GeoDataFrame', k: 'int' = 8) -> 'lps_weights.W'`

KNN weights, row-standardized, projected EPSG:32604.

##### `build_queen(self, gdf: 'gpd.GeoDataFrame') -> 'lps_weights.W'`

Queen contiguity for polygon geometry; falls back to KNN(6) for points.

##### `eigenvalues(self, W_sparse: 'sp.csr_matrix', cache_path: 'str | None' = None) -> 'np.ndarray'`

Compute real eigenvalues of W; cache to .npy if path given.

##### `persist_weights_to_postgis(self, w: 'lps_weights.W', gdf: 'gpd.GeoDataFrame', table: 'str', dsn: 'str | None' = None) -> 'None'`

Write adjacency to PostGIS if POSTGRES_DSN is set.

##### `to_sparse(self, w: 'lps_weights.W') -> 'sp.csr_matrix'`

Convert libpysal W to CSR sparse matrix (n×n float64).

### `src.spatial.distance_bands` — [distance_bands.py](../src/spatial/distance_bands.py)

Distance band assignment relative to the Lahaina fire perimeter.

#### `assign_distance_bands(gdf: 'gpd.GeoDataFrame', fire_geom: 'BaseGeometry') -> 'gpd.GeoDataFrame'`

Assign distance-to-fire and treatment band to each parcel.

Args:
    gdf: GeoDataFrame with point geometry in any CRS.
    fire_geom: Shapely geometry of the fire perimeter, already projected
        to EPSG:32604 (UTM zone 4N, Hawaii).

Returns:
    GeoDataFrame with added columns [dist_to_fire_km, treatment_band],
    reprojected back to original CRS.

### `src.spatial.panel_builder` — [panel_builder.py](../src/spatial/panel_builder.py)

Long-panel construction merging parcel transactions with FRED macro data.

#### `build_panel(parcels: 'gpd.GeoDataFrame', fred: 'pd.DataFrame', fire_date: 'str' = '2023-08-08') -> 'pd.DataFrame'`

Build a long-format panel merging parcel sales with FRED controls.

Args:
    parcels: GeoDataFrame with parcel-level columns including sale_date,
        parcel_id, tract_geoid, and all spatial features.
    fred: Long-format FRED DataFrame with columns [date, series_id, value].
    fire_date: ISO date string for the Lahaina fire (2023-08-08).

Returns:
    Long-panel DataFrame sorted by (parcel_id, sale_date) with columns:
        - All parcel columns (minus geometry)
        - FRED macro controls pivoted wide (one column per series_id)
        - post: 1 if sale_date >= fire_date, else 0
        - event_time: integer months since fire (negative=pre, positive=post)
        - fe_block: census-block fixed effect identifier (= tract_geoid)
        - fe_yearmonth: year-month fixed effect string (YYYY-MM)
        - year_month: period string for merge key

Raises:
    KeyError: If required columns are absent from parcels or fred.

---

## Data Ingest

### `src.ingest.parcel` — [parcel.py](../src/ingest/parcel.py)

Maui County assessor parcel loader with pandera schema validation.

#### `fetch_maui_assessment_roll(output_dir: 'str' = 'data/raw/parcels/') -> 'gpd.GeoDataFrame'`

Load Maui County Assessment Roll from local file or raise stub error.

DATA SOURCE: Maui County Assessment Division Real Property Assessment Roll
URL: https://www.mauicounty.gov/452/Real-Property-Assessment
Download the CSV and place at data/raw/parcels/maui_assessment_roll.csv

Returns GeoDataFrame with columns: parcel_id, sale_price, sale_date, lat, lon,
land_area_sqft, structure_sqft, year_built, zoning, tax_class, assessed_total,
log_price, geometry

Args:
    output_dir: Directory containing the maui_assessment_roll.csv file.

Returns:
    GeoDataFrame with point geometry, validated schema, and log_price column.

Raises:
    NotImplementedError: If the CSV file is not present at the expected path.
    pandera.errors.SchemaError: If the data fails schema validation.

#### `load_maui_parcels(path: 'str' = 'data/raw/parcels/maui_assessor.csv') -> 'gpd.GeoDataFrame'`

Load and validate Maui County assessor parcel data.

Args:
    path: Path to the assessor CSV or shapefile.

Returns:
    GeoDataFrame with point geometry, validated schema, and log_price column.

Raises:
    pandera.errors.SchemaError: If the data fails schema validation.
    FileNotFoundError: If path does not exist.

### `src.ingest.fred` — [fred.py](../src/ingest/fred.py)

FRED API ingestion for Hawaii climate-risk macroeconomic controls.

#### `fetch_fhfa_zip_hpi(output_dir: 'str' = 'data/raw/fhfa/', force_download: 'bool' = False, url: 'str' = 'https://www.fhfa.gov/document/d/hpi/hpi_at_bdl_zip5.xlsx') -> 'pd.DataFrame'`

Fetch FHFA House Price Index at ZIP code level.

DATA SOURCE: Federal Housing Finance Agency All-Transactions HPI by ZIP
URL: https://www.fhfa.gov/document/d/hpi/hpi_at_bdl_zip5.xlsx

Args:
    output_dir: Directory for cached parquet.
    force_download: Re-download even if cache exists.
    url: Override FHFA download URL.

Returns:
    DataFrame with columns: ZIP5, yr, qtr, index_nsa, year_month.
    Filtered to Hawaii ZIP codes (prefix 967 or 968).

#### `fetch_series(series_ids: 'list[str]', start: 'str', end: 'str', cache_dir: 'Path' = PosixPath('data/raw/fred')) -> 'pd.DataFrame'`

Fetch FRED time series and return a tidy long DataFrame.

Args:
    series_ids: List of FRED series identifiers.
    start: Observation start date, ISO format (YYYY-MM-DD).
    end: Observation end date, ISO format (YYYY-MM-DD).
    cache_dir: Directory for caching raw JSON responses.

Returns:
    DataFrame with columns [date, series_id, value] sorted by (series_id, date).

Raises:
    EnvironmentError: If FRED_API_KEY is not set.
    requests.HTTPError: On non-2xx API responses.

### `src.ingest.zillow_zip` — [zillow_zip.py](../src/ingest/zillow_zip.py)

Zillow ZHVI zip-level data ingestion.

#### `fetch_zhvi_by_zip(state: 'str' = 'HI', cache_dir: 'Path | None' = None) -> 'pd.DataFrame'`

Download Zillow ZHVI single-family monthly CSV, melt to long format.

Args:
    state: Two-letter state abbreviation to filter (default "HI").
    cache_dir: Directory for raw CSV cache; defaults to data/raw/zillow/.

Returns:
    Long DataFrame with columns [zip_code, year_month, zhvi].

### `src.ingest.census_acs` — [census_acs.py](../src/ingest/census_acs.py)

Census ACS 5-year API ingestion for zip-level covariates.

#### `fetch_acs_zip(variables: 'list[str] | None' = None, state_fips: 'str' = '15', year: 'int' = 2022, cache_dir: 'Path | None' = None) -> 'pd.DataFrame'`

Fetch ACS 5-year estimates for zip code tabulation areas.

Fetches ALL ZCTAs nationally (the Census API does not support the `in=state`
filter for ZCTAs), then filters to Hawaii ZIP codes in Python using the
``_HI_ZIP_PREFIXES`` constant (967xx, 968xx).  The ``state_fips`` parameter
is retained for API compatibility but is not sent to the Census endpoint.

Args:
    variables: ACS variable codes; defaults to VARIABLE_MAP keys.
    state_fips: Unused by the Census request; kept for call-site compatibility.
    year: ACS release year.
    cache_dir: Cache directory; defaults to data/raw/census/.

Returns:
    DataFrame with columns [zip_code, median_hh_income, median_home_value,
    total_population, owner_occupied_units, renter_occupied_units, total_workers]
    filtered to Hawaii ZIP codes.

### `src.ingest.fire` — [fire.py](../src/ingest/fire.py)

NIFC fire perimeter loader for the 2023 Lahaina wildfire.

#### `load_fire_perimeter(source: 'str' = 'nifc') -> 'gpd.GeoDataFrame'`

Download or load the 2023 Lahaina fire perimeter.

Args:
    source: Data source identifier. Currently only "nifc" is supported.

Returns:
    GeoDataFrame with fire perimeter polygon(s) in EPSG:4326.

Raises:
    ValueError: If source is not "nifc".
    requests.HTTPError: On failed API requests.

### `src.ingest.redfin` — [redfin.py](../src/ingest/redfin.py)

Redfin Research Data ingest — neighborhood market tracker.

#### `fetch_redfin_neighborhood(state: 'str' = 'Hawaii', force_download: 'bool' = False, url: 'str' = 'https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/neighborhood_market_tracker.tsv000.gz') -> 'pd.DataFrame'`

Fetch Redfin neighborhood market tracker data for Hawaii.

Streams and decompresses the gzipped TSV in chunks.
Caches filtered result to data/raw/redfin/hawaii_neighborhoods.parquet.

Args:
    state: State name to filter (default "Hawaii").
    force_download: Re-download even if cache exists.
    url: Override download URL.

Returns:
    DataFrame with columns: region, period_begin, period_end,
    median_sale_price, median_ppsf, homes_sold, inventory,
    days_on_market, sale_to_list, year_month.

---

## REST API

### `src.api.app` — [app.py](../src/api/app.py)

FastAPI spatial results service.

#### `get_gwr_surface(variable: 'str' = Query(beta_dist_to_fire), limit: 'int' = Query(200)) -> 'list[GWRSurface]'`

Return GWR coefficient surface records.

Tries ClickHouse first; falls back to parquet at results/gwr/gwr_surface.parquet.

Args:
    variable: Name of the GWR coefficient variable to retrieve (informational;
        both beta_dist_to_fire and beta_wui are always included in the response).
    limit: Maximum number of records to return (capped at 5000).

Returns:
    List of GWRSurface objects.

#### `get_lisa_clusters(cluster_label: 'str | None' = Query(None), limit: 'int' = Query(100)) -> 'list[LISAResult]'`

Return LISA cluster observations, optionally filtered by label.

Tries ClickHouse first; falls back to parquet at results/esda/lisa_stats.parquet.

Args:
    cluster_label: One of HH, LL, HL, LH, NS, or None to return all labels.
    limit: Maximum number of records to return (capped at 5000).

Returns:
    List of LISAResult objects.

Raises:
    HTTPException 422: If cluster_label is not a valid label string.

#### `get_lisa_counts() -> 'ClusterCountResponse'`

Return aggregate counts of LISA cluster labels across all observations.

Tries ClickHouse first; falls back to parquet at results/esda/cluster_labels.parquet.

Returns:
    ClusterCountResponse with counts for HH, LL, HL, LH, NS, and total.

#### `get_model_comparison() -> 'list[SpatialModelSummary]'`

Return the spatial model comparison table (SAR vs SEM vs SDM).

Tries ClickHouse first; falls back to JSON at results/spatial/nesting_tests.json.

Returns:
    List of SpatialModelSummary objects sorted by AIC ascending.

#### `get_spatial_autocorrelation() -> 'dict[str, Any]'`

Return Global Moran's I summary from the precomputed JSON result.

Returns:
    Dict with keys I, E_I, Var_I, z_score, p_value_analytical,
    p_value_permutation if the file exists; otherwise a status message dict.

#### `health() -> 'dict[str, str]'`

Return API liveness status.

Returns:
    JSON object {"status": "ok"}.

#### `log_requests(request, call_next)`

Log HTTP method and URL for every incoming request.

Args:
    request: Starlette Request object.
    call_next: ASGI middleware chain callable.

Returns:
    The downstream Response object unchanged.

### `src.api.schemas` — [schemas.py](../src/api/schemas.py)

Pydantic v2 schemas for spatial results API.

#### `ClusterCountResponse`

Response schema for LISA cluster count summary.

Attributes:
    HH: Count of High-High (spatial cluster) observations.
    LL: Count of Low-Low (spatial cluster) observations.
    HL: Count of High-Low (spatial outlier) observations.
    LH: Count of Low-High (spatial outlier) observations.
    NS: Count of Not Significant observations.
    total: Total number of observations across all labels.

##### `__init__(self, /, **data: 'Any') -> 'None'`

Create a new model by parsing and validating input data from keyword arguments.

Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
validated to form a valid model.

`self` is explicitly positional-only to allow `self` as a field name.

##### `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'`

Returns a copy of the model.

!!! warning "Deprecated"
    This method is now deprecated; use `model_copy` instead.

If you need `include` or `exclude`, use:

```python {test="skip" lint="skip"}
data = self.model_dump(include=include, exclude=exclude, round_trip=True)
data = {**data, **(update or {})}
copied = self.model_validate(data)
```

Args:
    include: Optional set or mapping specifying which fields to include in the copied model.
    exclude: Optional set or mapping specifying which fields to exclude in the copied model.
    update: Optional dictionary of field-value pairs to override field values in the copied model.
    deep: If True, the values of fields that are Pydantic models will be deep-copied.

Returns:
    A copy of the model with included, excluded and updated fields as specified.

##### `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'`

*(no docstring)*

##### `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'`

*(no docstring)*

##### `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'`

!!! abstract "Usage Documentation"
    [`model_copy`](../concepts/models.md#model-copy)

Returns a copy of the model.

!!! note
    The underlying instance's [`__dict__`][object.__dict__] attribute is copied. This
    might have unexpected side effects if you store anything in it, on top of the model
    fields (e.g. the value of [cached properties][functools.cached_property]).

Args:
    update: Values to change/add in the new model. Note: the data is not validated
        before creating the new model. You should trust this data.
    deep: Set to `True` to make a deep copy of the model.

Returns:
    New model instance.

##### `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'`

!!! abstract "Usage Documentation"
    [`model_dump`](../concepts/serialization.md#python-mode)

Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

Args:
    mode: The mode in which `to_python` should run.
        If mode is 'json', the output will only contain JSON serializable types.
        If mode is 'python', the output may contain non-JSON-serializable Python objects.
    include: A set of fields to include in the output.
    exclude: A set of fields to exclude from the output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to use the field's alias in the dictionary key if defined.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

Returns:
    A dictionary representation of the model.

##### `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'`

!!! abstract "Usage Documentation"
    [`model_dump_json`](../concepts/serialization.md#json-mode)

Generates a JSON representation of the model using Pydantic's `to_json` method.

Args:
    indent: Indentation to use in the JSON output. If None is passed, the output will be compact.
    ensure_ascii: If `True`, the output is guaranteed to have all incoming non-ASCII characters escaped.
        If `False` (the default), these characters will be output as-is.
    include: Field(s) to include in the JSON output.
    exclude: Field(s) to exclude from the JSON output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to serialize using field aliases.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

Returns:
    A JSON string representation of the model.

##### `model_post_init(self, context: 'Any', /) -> 'None'`

Override this method to perform additional initialization after `__init__` and `model_construct`.
This is useful if you want to do some validation that requires the entire model to be initialized.

#### `GWRSurface`

Response schema for a single GWR coefficient surface observation.

Attributes:
    parcel_id: Unique parcel identifier string.
    lat: Latitude in decimal degrees (WGS 84).
    lon: Longitude in decimal degrees (WGS 84).
    beta_dist_to_fire: Local GWR coefficient for distance-to-fire predictor.
    beta_wui: Local GWR coefficient for the WUI class predictor.
    y_hat: GWR fitted value (log price or price change) at this location.

##### `__init__(self, /, **data: 'Any') -> 'None'`

Create a new model by parsing and validating input data from keyword arguments.

Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
validated to form a valid model.

`self` is explicitly positional-only to allow `self` as a field name.

##### `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'`

Returns a copy of the model.

!!! warning "Deprecated"
    This method is now deprecated; use `model_copy` instead.

If you need `include` or `exclude`, use:

```python {test="skip" lint="skip"}
data = self.model_dump(include=include, exclude=exclude, round_trip=True)
data = {**data, **(update or {})}
copied = self.model_validate(data)
```

Args:
    include: Optional set or mapping specifying which fields to include in the copied model.
    exclude: Optional set or mapping specifying which fields to exclude in the copied model.
    update: Optional dictionary of field-value pairs to override field values in the copied model.
    deep: If True, the values of fields that are Pydantic models will be deep-copied.

Returns:
    A copy of the model with included, excluded and updated fields as specified.

##### `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'`

*(no docstring)*

##### `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'`

*(no docstring)*

##### `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'`

!!! abstract "Usage Documentation"
    [`model_copy`](../concepts/models.md#model-copy)

Returns a copy of the model.

!!! note
    The underlying instance's [`__dict__`][object.__dict__] attribute is copied. This
    might have unexpected side effects if you store anything in it, on top of the model
    fields (e.g. the value of [cached properties][functools.cached_property]).

Args:
    update: Values to change/add in the new model. Note: the data is not validated
        before creating the new model. You should trust this data.
    deep: Set to `True` to make a deep copy of the model.

Returns:
    New model instance.

##### `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'`

!!! abstract "Usage Documentation"
    [`model_dump`](../concepts/serialization.md#python-mode)

Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

Args:
    mode: The mode in which `to_python` should run.
        If mode is 'json', the output will only contain JSON serializable types.
        If mode is 'python', the output may contain non-JSON-serializable Python objects.
    include: A set of fields to include in the output.
    exclude: A set of fields to exclude from the output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to use the field's alias in the dictionary key if defined.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

Returns:
    A dictionary representation of the model.

##### `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'`

!!! abstract "Usage Documentation"
    [`model_dump_json`](../concepts/serialization.md#json-mode)

Generates a JSON representation of the model using Pydantic's `to_json` method.

Args:
    indent: Indentation to use in the JSON output. If None is passed, the output will be compact.
    ensure_ascii: If `True`, the output is guaranteed to have all incoming non-ASCII characters escaped.
        If `False` (the default), these characters will be output as-is.
    include: Field(s) to include in the JSON output.
    exclude: Field(s) to exclude from the JSON output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to serialize using field aliases.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

Returns:
    A JSON string representation of the model.

##### `model_post_init(self, context: 'Any', /) -> 'None'`

Override this method to perform additional initialization after `__init__` and `model_construct`.
This is useful if you want to do some validation that requires the entire model to be initialized.

#### `LISAResult`

Response schema for a single LISA cluster observation.

Attributes:
    parcel_id: Unique parcel identifier string.
    lat: Latitude in decimal degrees (WGS 84).
    lon: Longitude in decimal degrees (WGS 84).
    I_local: Local Moran's I statistic for this observation.
    p_value: Permutation-based p-value for the local statistic.
    cluster_label: LISA quadrant label — one of HH, LL, HL, LH, NS.

##### `__init__(self, /, **data: 'Any') -> 'None'`

Create a new model by parsing and validating input data from keyword arguments.

Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
validated to form a valid model.

`self` is explicitly positional-only to allow `self` as a field name.

##### `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'`

Returns a copy of the model.

!!! warning "Deprecated"
    This method is now deprecated; use `model_copy` instead.

If you need `include` or `exclude`, use:

```python {test="skip" lint="skip"}
data = self.model_dump(include=include, exclude=exclude, round_trip=True)
data = {**data, **(update or {})}
copied = self.model_validate(data)
```

Args:
    include: Optional set or mapping specifying which fields to include in the copied model.
    exclude: Optional set or mapping specifying which fields to exclude in the copied model.
    update: Optional dictionary of field-value pairs to override field values in the copied model.
    deep: If True, the values of fields that are Pydantic models will be deep-copied.

Returns:
    A copy of the model with included, excluded and updated fields as specified.

##### `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'`

*(no docstring)*

##### `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'`

*(no docstring)*

##### `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'`

!!! abstract "Usage Documentation"
    [`model_copy`](../concepts/models.md#model-copy)

Returns a copy of the model.

!!! note
    The underlying instance's [`__dict__`][object.__dict__] attribute is copied. This
    might have unexpected side effects if you store anything in it, on top of the model
    fields (e.g. the value of [cached properties][functools.cached_property]).

Args:
    update: Values to change/add in the new model. Note: the data is not validated
        before creating the new model. You should trust this data.
    deep: Set to `True` to make a deep copy of the model.

Returns:
    New model instance.

##### `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'`

!!! abstract "Usage Documentation"
    [`model_dump`](../concepts/serialization.md#python-mode)

Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

Args:
    mode: The mode in which `to_python` should run.
        If mode is 'json', the output will only contain JSON serializable types.
        If mode is 'python', the output may contain non-JSON-serializable Python objects.
    include: A set of fields to include in the output.
    exclude: A set of fields to exclude from the output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to use the field's alias in the dictionary key if defined.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

Returns:
    A dictionary representation of the model.

##### `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'`

!!! abstract "Usage Documentation"
    [`model_dump_json`](../concepts/serialization.md#json-mode)

Generates a JSON representation of the model using Pydantic's `to_json` method.

Args:
    indent: Indentation to use in the JSON output. If None is passed, the output will be compact.
    ensure_ascii: If `True`, the output is guaranteed to have all incoming non-ASCII characters escaped.
        If `False` (the default), these characters will be output as-is.
    include: Field(s) to include in the JSON output.
    exclude: Field(s) to exclude from the JSON output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to serialize using field aliases.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

Returns:
    A JSON string representation of the model.

##### `model_post_init(self, context: 'Any', /) -> 'None'`

Override this method to perform additional initialization after `__init__` and `model_construct`.
This is useful if you want to do some validation that requires the entire model to be initialized.

#### `SpatialModelSummary`

Response schema for a single entry in the spatial model comparison table.

Attributes:
    model_name: Model identifier (e.g. "SAR", "SEM", "SDM").
    spatial_param: Estimated spatial parameter (rho for SAR/SDM, lambda for SEM).
    log_likelihood: Maximized log-likelihood value.
    aic: Akaike Information Criterion (-2*LL + 2*k).
    bic: Bayesian Information Criterion (-2*LL + k*log(n)).
    p_value: P-value for the spatial parameter (two-sided z-test).

##### `__init__(self, /, **data: 'Any') -> 'None'`

Create a new model by parsing and validating input data from keyword arguments.

Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
validated to form a valid model.

`self` is explicitly positional-only to allow `self` as a field name.

##### `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'`

Returns a copy of the model.

!!! warning "Deprecated"
    This method is now deprecated; use `model_copy` instead.

If you need `include` or `exclude`, use:

```python {test="skip" lint="skip"}
data = self.model_dump(include=include, exclude=exclude, round_trip=True)
data = {**data, **(update or {})}
copied = self.model_validate(data)
```

Args:
    include: Optional set or mapping specifying which fields to include in the copied model.
    exclude: Optional set or mapping specifying which fields to exclude in the copied model.
    update: Optional dictionary of field-value pairs to override field values in the copied model.
    deep: If True, the values of fields that are Pydantic models will be deep-copied.

Returns:
    A copy of the model with included, excluded and updated fields as specified.

##### `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'`

*(no docstring)*

##### `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'`

*(no docstring)*

##### `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'`

!!! abstract "Usage Documentation"
    [`model_copy`](../concepts/models.md#model-copy)

Returns a copy of the model.

!!! note
    The underlying instance's [`__dict__`][object.__dict__] attribute is copied. This
    might have unexpected side effects if you store anything in it, on top of the model
    fields (e.g. the value of [cached properties][functools.cached_property]).

Args:
    update: Values to change/add in the new model. Note: the data is not validated
        before creating the new model. You should trust this data.
    deep: Set to `True` to make a deep copy of the model.

Returns:
    New model instance.

##### `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'`

!!! abstract "Usage Documentation"
    [`model_dump`](../concepts/serialization.md#python-mode)

Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

Args:
    mode: The mode in which `to_python` should run.
        If mode is 'json', the output will only contain JSON serializable types.
        If mode is 'python', the output may contain non-JSON-serializable Python objects.
    include: A set of fields to include in the output.
    exclude: A set of fields to exclude from the output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to use the field's alias in the dictionary key if defined.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

Returns:
    A dictionary representation of the model.

##### `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'`

!!! abstract "Usage Documentation"
    [`model_dump_json`](../concepts/serialization.md#json-mode)

Generates a JSON representation of the model using Pydantic's `to_json` method.

Args:
    indent: Indentation to use in the JSON output. If None is passed, the output will be compact.
    ensure_ascii: If `True`, the output is guaranteed to have all incoming non-ASCII characters escaped.
        If `False` (the default), these characters will be output as-is.
    include: Field(s) to include in the JSON output.
    exclude: Field(s) to exclude from the JSON output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to serialize using field aliases.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

Returns:
    A JSON string representation of the model.

##### `model_post_init(self, context: 'Any', /) -> 'None'`

Override this method to perform additional initialization after `__init__` and `model_construct`.
This is useful if you want to do some validation that requires the entire model to be initialized.

### `src.api.db` — [db.py](../src/api/db.py)

ClickHouse client for spatial results.

#### `ClickHouseClient`

Thin wrapper around clickhouse-driver Client.

##### `__init__(self, host: 'str | None' = None, port: 'int | None' = None, database: 'str | None' = None) -> 'None'`

Initialize the ClickHouse client configuration.

Connection is lazy — no socket is opened until the first query.

Args:
    host: ClickHouse host; falls back to CH_HOST env var (empty = disabled).
    port: ClickHouse native protocol port; falls back to CH_PORT env var (default 9000).
    database: Database name; falls back to CH_DB env var (default "lahaina").

Attributes:
    _host: Resolved host string.
    _port: Resolved port integer.
    _database: Resolved database name.
    _client: Lazily initialized clickhouse_driver.Client instance (None until first use).

##### `connect(self) -> 'None'`

Eagerly initialize the ClickHouse connection.

Raises:
    RuntimeError: If CH_HOST is not set.

##### `create_tables(self) -> 'None'`

Create lisa_results, gwr_surfaces, and model_comparison tables if absent.

All tables use MergeTree with a run_date partition. Safe to call repeatedly
(CREATE TABLE IF NOT EXISTS semantics).

Raises:
    RuntimeError: If CH_HOST is not configured.

##### `insert_gwr(self, df: 'pd.DataFrame') -> 'None'`

Bulk-insert GWR surface rows into the gwr_surfaces table.

Args:
    df: DataFrame whose columns match the gwr_surfaces schema.

##### `insert_lisa(self, df: 'pd.DataFrame') -> 'None'`

Bulk-insert LISA results into the lisa_results table.

Args:
    df: DataFrame whose columns match the lisa_results schema.

##### `insert_model_comparison(self, df: 'pd.DataFrame') -> 'None'`

Bulk-insert model comparison rows into the model_comparison table.

Args:
    df: DataFrame whose columns match the model_comparison schema.

##### `query(self, sql: 'str', parameters: 'dict | None' = None) -> 'pd.DataFrame'`

Execute an arbitrary SQL query and return the results as a DataFrame.

Args:
    sql: SQL string; use %(name)s placeholders for parameters.
    parameters: Dict of bind parameters (optional).

Returns:
    DataFrame with column names derived from the query result metadata.

Raises:
    RuntimeError: If CH_HOST is not configured.

---

## Output Generation

### `src.outputs.tables` — [tables.py](../src/outputs/tables.py)

Publication-quality LaTeX table generation for Phase 1 results.

#### `did_to_latex(event_study_path: 'str', output_dir: 'str' = 'docs/tables') -> 'str'`

Format Callaway-Sant'Anna event-study ATTs as a LaTeX table.

Produces a threeparttable with Panel A (pre-treatment) and
Panel B (post-treatment) rows.

Args:
    event_study_path: Path to event_study.csv from CallawayAntaCSiD.event_study_df().
    output_dir: Directory to save the generated .tex file.

Returns:
    LaTeX string for the event-study table.

Raises:
    FileNotFoundError: If event_study_path does not exist.

#### `hedonic_to_latex(results_path: 'str', output_dir: 'str' = 'docs/tables') -> 'str'`

Format hedonic regression results as a publication-quality LaTeX table.

Produces a threeparttable with Panel A (structural controls) and
Panel B (treatment indicators / FE) with HC3 note.

Args:
    results_path: Path to hedonic_table.csv from HedonicModel.summary_table().
    output_dir: Directory to save the generated .tex file.

Returns:
    LaTeX string for the threeparttable.

Raises:
    FileNotFoundError: If results_path does not exist.

### `src.outputs.scm_tables` — [scm_tables.py](../src/outputs/scm_tables.py)

LaTeX table generation for SCM results.

#### `balance_table_latex(X0: 'np.ndarray', X1: 'np.ndarray', donor_names: 'list[str]', covariate_names: 'list[str]', w_adh: 'np.ndarray') -> 'str'`

Generate LaTeX balance table.

Args:
    X0: Donor covariate matrix (k, J).
    X1: Treated covariate vector (k,).
    donor_names: Donor zip code labels.
    covariate_names: Covariate labels.
    w_adh: ADH donor weights (J,).

Returns:
    LaTeX string.

#### `rmspe_table_latex(model_registry) -> 'str'`

Generate LaTeX RMSPE comparison table.

Args:
    model_registry: ModelRegistry with registered models.

Returns:
    LaTeX string.

#### `save_latex(content: 'str', filename: 'str') -> 'Path'`

Save LaTeX string to docs/tables/.

#### `weights_table_latex(model_registry) -> 'str'`

Generate LaTeX table of donor weights with characteristics.

Args:
    model_registry: ModelRegistry with registered models.

Returns:
    LaTeX string.

### `src.outputs.scm_plots` — [scm_plots.py](../src/outputs/scm_plots.py)

Publication-quality SCM visualizations.

#### `plot_loo(base_gap: 'np.ndarray', loo_gaps: 'dict[str, np.ndarray]', time_periods: 'list[str]', fire_date: 'str', output_path: 'str | Path', ax: 'plt.Axes | None' = None) -> 'None'`

Plot leave-one-out gap series vs base gap.

Args:
    base_gap: Base gap series (T,).
    loo_gaps: Dict mapping donor name → LOO gap series.
    time_periods: Year-month list.
    fire_date: Fire year-month string.
    output_path: Output file path.
    ax: Existing axes.

#### `plot_model_comparison(model_registry, time_periods: 'list[str]', fire_date: 'str', output_path: 'str | Path', ax: 'plt.Axes | None' = None) -> 'None'`

Plot gap series for ADH, GSynth, ASCM side-by-side.

Args:
    model_registry: ModelRegistry with registered models.
    time_periods: Year-month list.
    fire_date: Fire year-month string.
    output_path: Output file path.
    ax: Existing axes.

#### `plot_placebo_distribution(placebo_df: 'pd.DataFrame', treated_gap_series: 'np.ndarray', time_periods: 'list[str]', fire_date: 'str', output_path: 'str | Path', ax: 'plt.Axes | None' = None) -> 'None'`

Plot gap series for all placebos + treated unit.

Args:
    placebo_df: DataFrame from InSpacePlacebo.run().
    treated_gap_series: Treated unit gap (T,).
    time_periods: Year-month list length T.
    fire_date: Fire year-month string.
    output_path: Output file path.
    ax: Existing axes.

#### `plot_scm_path(Y1_all: 'np.ndarray', Y_synth_all: 'np.ndarray', time_periods: 'list[str]', fire_date: 'str', output_path: 'str | Path', title: 'str' = 'Lahaina vs. synthetic Lahaina', ax: 'plt.Axes | None' = None) -> 'None'`

Plot treated and synthetic paths with shaded gap.

Args:
    Y1_all: Treated unit outcome series (T,).
    Y_synth_all: Synthetic control series (T,).
    time_periods: List of year_month strings length T.
    fire_date: Year-month of fire (e.g. "2023-08").
    output_path: File path (PDF + PNG saved).
    title: Plot title.
    ax: Existing axes; created if None.

### `src.outputs.spatial_tables` — [spatial_tables.py](../src/outputs/spatial_tables.py)

LaTeX table generation for spatial econometrics results.

#### `effects_latex(effects_df: 'pd.DataFrame') -> 'str'`

Generate a LaTeX table of LeSage-Pace direct/indirect/total effects.

Writes the table to docs/tables/phase3_effects.tex as a side-effect.

Args:
    effects_df: DataFrame from LeSagePaceEffects.summary_table() with columns
        variable, direct, indirect, total, direct_se, indirect_se, total_se,
        direct_p, indirect_p, total_p.

Returns:
    LaTeX string for the complete table environment.

#### `moran_lisa_latex(global_morans_dict: 'dict', cluster_counts_dict: 'dict') -> 'str'`

Generate a two-panel LaTeX table for Global Moran's I and LISA cluster counts.

Writes the table to docs/tables/phase3_moran_lisa.tex as a side-effect.

Args:
    global_morans_dict: Dict from GlobalMoransI.summary() with keys I, E_I,
        Var_I, z_score, p_value_analytical, p_value_permutation.
    cluster_counts_dict: Dict from LocalMoransI.cluster_counts() with keys
        HH, LL, HL, LH, NS (and optionally total).

Returns:
    LaTeX string for the complete table environment.

#### `sar_sem_sdm_latex(model_registry, lrt_sdm_sar: 'dict | None' = None, wald_sdm_sem: 'dict | None' = None) -> 'str'`

Generate a LaTeX table comparing SAR, SEM, and SDM estimates.

Writes the table to docs/tables/phase3_spatial_models.tex as a side-effect.

Args:
    model_registry: Fitted SpatialModelRegistry with SAR, SEM, SDM registered.
    lrt_sdm_sar: Optional dict from SpatialDurbinModel.test_sar_restriction()
        containing keys lr_stat and p_value.
    wald_sdm_sem: Optional dict from SpatialDurbinModel.test_sem_cf_restriction()
        containing keys W_stat and p_value.

Returns:
    LaTeX string for the complete table environment.

### `src.outputs.spatial_plots` — [spatial_plots.py](../src/outputs/spatial_plots.py)

Interactive spatial visualizations (Folium choropleth + Matplotlib).

#### `plot_gwr_surface(gdf: 'gpd.GeoDataFrame', variable: 'str', output_path: 'str') -> 'str'`

Interactive Folium choropleth of a GWR local β surface.

#### `plot_lisa_map(gdf: 'gpd.GeoDataFrame', output_path: 'str') -> 'str'`

Interactive Folium LISA cluster map saved as self-contained HTML.

#### `plot_spatial_model_comparison(model_registry, output_path: 'str') -> 'str'`

Bar chart: AIC comparison across spatial models.

#### `plot_spillover_decay(effects_df: 'pd.DataFrame', output_path: 'str', dist_col: 'str' = 'dist_band_km', beta_col: 'str' = 'mean_beta', se_col: 'str' = 'se_beta') -> 'str'`

Spillover decay: mean local GWR β vs distance band, with fitted decay.

---
