# Methodology Notes — Lahaina Climate-Risk Econometrics

This document provides a self-contained econometric reference for all estimation methods used across the four phases of the project. It is intended as a companion to the working paper (`paper/main.tex`) and to the source code in `src/`.

---

## 1. Identification Strategy

### 1.1 Treatment Definition

The treatment variable is defined at the parcel level. A parcel is "treated" if it falls within a specified distance band of the 2023 Lahaina fire perimeter as measured by minimum geodesic distance from the parcel centroid to the perimeter polygon. The primary treatment band is 0–2 km; secondary bands at 2–5 km and 5–10 km are used for heterogeneity analysis and spatial gradient estimation.

Treatment timing is determined by the fire ignition date of August 8, 2023. All sales on or after this date for treated parcels are "post-treatment" observations.

### 1.2 Control Group

The control group consists of Maui County residential parcels beyond 10 km from the fire perimeter. The 10 km exclusion zone avoids contamination from indirect amenity or insurance-market spillovers in the near-neighbor zone. Within the control group, the Callaway-Sant'Anna estimator further restricts to "not-yet-treated" units in each calendar period, exploiting the staggered roll-out of information about risk reclassification and insurance repricing across ZIP codes.

### 1.3 Treatment Bands

Distance bands are assigned using the `src/spatial/distance_bands.py` module, which computes minimum Haversine distance from each parcel centroid to the fire perimeter polygon vertices using a vectorized nearest-neighbor query against the H3-indexed perimeter representation.

| Band | Distance | Interpretation |
|------|----------|----------------|
| T0 | 0 km (inside perimeter) | Physical destruction zone |
| T1 | 0–2 km | Direct risk exposure |
| T2 | 2–5 km | Near-neighbor spillover |
| T3 | 5–10 km | Intermediate spillover |
| Control | > 10 km | Unaffected comparison group |

### 1.4 Parallel Trends Assumption

The identifying assumption is that, absent the Lahaina fire, treated and control parcels would have followed parallel price trends. This is evaluated using:

1. A pre-trend WLS regression of price changes on treatment indicators for all pre-August-2023 calendar periods (`src/models/parallel_trends.py`). A statistically significant pre-trend coefficient constitutes evidence against the parallel trends assumption.
2. An event-study plot with 95% confidence bands from the Callaway-Sant'Anna ATT(g,t) estimates at each calendar period relative to treatment cohort.

---

## 2. Hedonic Model Specification

### 2.1 Estimating Equation

The baseline hedonic model is:

$$\log P_{it} = \alpha + \beta X_{it} + \gamma_b + \tau_t + \varepsilon_{it}$$

where:
- $P_{it}$ is the transaction price (in nominal USD) of parcel $i$ sold at time $t$
- $X_{it}$ is a vector of structural and locational attributes: log square footage, age (years since construction), number of bedrooms, number of bathrooms, lot size (log acres), zoning category indicators, and waterfront indicator
- $\gamma_b$ are census-block fixed effects absorbing all time-invariant neighborhood-level unobservables
- $\tau_t$ are year-month fixed effects absorbing common macroeconomic fluctuations (interest rates, aggregate demand shocks)
- $\varepsilon_{it}$ is the idiosyncratic error term

### 2.2 Standard Errors

Standard errors are HC3 heteroskedasticity-robust (MacKinnon-White 1985), computed via the sandwich estimator. HC3 weights each squared residual by $(1 - h_{ii})^{-2}$ where $h_{ii}$ is the leverage of observation $i$, providing better finite-sample coverage than HC1.

### 2.3 Treatment Effect Augmentation

The baseline hedonic is augmented with:

$$\log P_{it} = \alpha + \beta X_{it} + \gamma_b + \tau_t + \sum_{k} \delta_k D^k_{it} + \varepsilon_{it}$$

where $D^k_{it}$ is an indicator for parcel $i$ being in treatment band $k$ in the post-treatment period. The coefficients $\delta_k$ recover the average log-price impact at each distance band.

---

## 3. Callaway-Sant'Anna ATT(g,t) Estimator

### 3.1 Setup

Let $G_i$ denote the calendar period in which unit $i$ first receives treatment (the "cohort"), with $G_i = \infty$ for never-treated units. Define $ATT(g,t)$ as the average treatment effect on units first treated in cohort $g$ at calendar period $t$:

$$ATT(g,t) = \mathbb{E}[Y_t(g) - Y_t(0) \mid G_i = g]$$

where $Y_t(g)$ is the potential outcome at time $t$ under treatment cohort $g$ and $Y_t(0)$ is the never-treated potential outcome.

### 3.2 Doubly-Robust IPW Estimator

Callaway and Sant'Anna (2021) estimate $ATT(g,t)$ using a doubly-robust inverse probability weighting estimator that combines an outcome regression with a propensity score model. The estimator is consistent if either (but not necessarily both) of the two nuisance models is correctly specified.

The propensity score $p_g(X_i) = P(G_i = g \mid X_i, G_i \in \{g, \infty\})$ is estimated by logistic regression. The outcome regression $\mu_{0,t}(X_i) = \mathbb{E}[Y_t \mid X_i, G_i = \infty]$ is estimated by OLS on the never-treated sample.

### 3.3 Aggregation

Cohort-period estimates $ATT(g,t)$ are aggregated to:

1. **Simple ATT**: $\theta^{simple} = \sum_{g,t} w_{g,t} \cdot ATT(g,t)$ where $w_{g,t}$ are cohort-size weights
2. **Event-study ATT**: $\theta^{es}(\ell) = \sum_g w_g \cdot ATT(g, g+\ell)$ for event-time $\ell = t - g$

Inference uses the multiplier bootstrap with 999 draws.

### 3.4 Control Group

This project uses the "not-yet-treated" control group, which restricts comparisons to units not yet treated by period $t$. This is more efficient than using only never-treated units when staggered adoption creates many cohorts.

---

## 4. Triple-Difference Decomposition

### 4.1 Estimating Equation

The triple-difference (DDD) model extends the baseline DiD by adding a third dimension — WUI classification — to separate the belief-update channel from physical destruction and displacement:

$$\log P_{it} = \alpha + \beta_1 (\text{Post}_t \times \text{Treated}_i \times \text{WUI}_i) + \beta_2 (\text{Post}_t \times \text{Treated}_i) + \beta_3 (\text{Post}_t \times \text{WUI}_i) + \beta_4 \text{WUI}_i + \gamma_b + \tau_t + \varepsilon_{it}$$

### 4.2 Channel Interpretation

| Coefficient | Interpretation |
|-------------|---------------|
| $\beta_2$ | Average DiD effect for non-WUI treated parcels (displacement + physical damage) |
| $\beta_1$ | Additional effect for WUI-classified parcels conditional on treatment and post |
| $\beta_1 - \beta_2$ | Pure belief-update channel: the additional discount accruing to WUI parcels |

The logic is that WUI classification is a forward-looking risk signal. A parcel classified as WUI but not physically destroyed still faces elevated perceived wildfire risk. The differential $\beta_1 - \beta_2$ captures the market's revision of long-run risk expectations for WUI-adjacent properties, holding distance fixed.

---

## 5. Synthetic Control Methods

### 5.1 ADH Synthetic Control

The Abadie-Diamond-Hainmueller (2010) synthetic control constructs a weighted combination of donor units (non-treated ZIP codes / market areas) that best matches the treated unit's pre-treatment outcome trajectory and covariate values.

**Inner optimization** (unit weights $w$): Given a positive semi-definite importance matrix $V$, find weights $w^* \in \Delta^{J-1}$ (the unit simplex) that minimize pre-treatment RMSPE:

$$w^*(V) = \arg\min_{w \in \Delta^{J-1}} \sum_{t=1}^{T_0} \left( Y_{1t} - \sum_{j=2}^{J+1} w_j Y_{jt} \right)^2 V_{tt}$$

**Outer optimization** (importance matrix $V$): Find $V^*$ such that the synthetic control also minimizes out-of-sample prediction error on a validation subsample of the pre-period, or by minimizing the objective over the space of diagonal positive semi-definite $V$ matrices.

Implementation: `src/scm/adh_scm.py` uses `cvxpy` for the inner QP and `scipy.optimize.minimize` with BFGS for the outer V-matrix search.

### 5.2 Generalized Synthetic Control (GSynth)

GSynth (Xu 2017) extends ADH to allow time-varying treatment effects and heterogeneous factor loadings. It estimates an interactive fixed-effects model on the control units:

$$Y_{it} = \lambda_i' F_t + \varepsilon_{it} \quad \text{for } i \in \text{Controls}$$

where $\lambda_i$ are unit-specific factor loadings and $F_t$ are latent common factors estimated by nuclear norm minimization. The counterfactual for the treated unit is $\hat{Y}_{1t}(0) = \hat{\lambda}_1' \hat{F}_t$ where $\hat{\lambda}_1$ is estimated from the treated unit's pre-treatment outcomes.

Implementation: `src/scm/gsynth.py` uses `cvxpy` for nuclear norm minimization and `sklearn` for factor extraction.

### 5.3 Augmented Synthetic Control (AugSynth)

AugSynth (Ben-Michael et al. 2021) augments the ADH weights with an outcome model ridge regression to reduce bias from imperfect pre-treatment fit:

$$\hat{\tau}^{AugSynth} = \hat{\tau}^{SC} + (\hat{\mu}_{1,post} - \hat{\mu}^{SC}_{post})$$

where $\hat{\mu}$ is a regularized outcome model fit on the donor pool. This provides double robustness: the estimator is consistent if either the synthetic control weights or the outcome model is correctly specified.

Implementation: `src/scm/augsynth.py` combines the ADH weights from `adh_scm.py` with a ridge-augmented bias correction.

### 5.4 In-Space Placebo Inference

For each donor unit $j$, re-run the synthetic control as if $j$ were the treated unit, using the remaining donors as the control pool. The treatment effect for each placebo is the post-treatment gap $\hat{Y}_{jt} - Y_{jt}$. The permutation p-value is:

$$p = \frac{\text{rank}(RMSPE_1^{post} / RMSPE_1^{pre})}{\text{number of placebos} + 1}$$

where the rank is computed among all placebo RMSPE ratios. Implementation: `src/inference/placebo.py` and `src/inference/rmspe.py`.

### 5.5 Leave-One-Out Donor Robustness

LOO analysis iteratively removes each donor unit and re-estimates the synthetic control weights, checking whether any single donor drives the result. A robust finding is one where the treatment effect gap is qualitatively similar across all LOO estimates. Implementation: `src/inference/loo.py`.

---

## 6. Spatial Weights

The `SpatialWeightsFactory` in `src/spatial/weights_phase3.py` constructs spatial weights matrices in three modes:

- **KNN**: K-nearest neighbors (default $k=8$) based on parcel centroid distances
- **IDW**: Inverse distance weighting with a power parameter (default $p=1$)
- **Queen contiguity**: Shared-boundary contiguity for polygon data

All weights matrices are row-standardized and returned as `scipy.sparse.csr_matrix` objects. Row-standardization ensures that the spatial lag of a constant vector equals that constant, a prerequisite for valid Moran's I computation.

---

## 7. Global Moran's I

### 7.1 Statistic

The global Moran's I statistic measures the degree of spatial autocorrelation in a variable $y$:

$$I = \frac{N}{\sum_i \sum_j w_{ij}} \cdot \frac{\sum_i \sum_j w_{ij} (y_i - \bar{y})(y_j - \bar{y})}{\sum_i (y_i - \bar{y})^2}$$

Implementation: `src/esda/morans.py` computes $I$ via sparse matrix operations, avoiding the $O(N^2)$ double loop.

### 7.2 Inference

Two inference approaches are implemented:

1. **Cliff-Ord asymptotic moments**: Analytical mean $E[I]$ and variance $V[I]$ under the randomization hypothesis, yielding a z-statistic and normal p-value.
2. **Permutation test**: 999 random permutations of $y$ (holding $W$ fixed) generate an empirical null distribution; the permutation p-value is the fraction of permuted $I^{(r)}$ exceeding the observed $I$.

**Important implementation note**: The $S_2$ term in the Cliff-Ord variance formula involves squaring the row and column sums of $W$. These sums must be raveled to 1-D arrays before squaring; applying `**2` to a sparse matrix triggers `scipy.sparse.linalg.matrix_power`, which is incorrect.

---

## 8. LISA Quadrant Classification

Local Indicators of Spatial Association (Anselin 1995) decompose the global Moran's I into local contributions:

$$I_i = \frac{(y_i - \bar{y})}{m_2} \sum_j w_{ij} (y_j - \bar{y})$$

where $m_2 = \sum_i (y_i - \bar{y})^2 / N$.

Observations are classified into four quadrants in the Moran scatter plot (standardized $y_i$ vs. standardized spatial lag $Wy_i$):

| Quadrant | Label | Interpretation |
|----------|-------|---------------|
| HH | High-High | Hot spot: high value surrounded by high values |
| LL | Low-Low | Cold spot: low value surrounded by low values |
| HL | High-Low | Spatial outlier: high value surrounded by low values |
| LH | Low-High | Spatial outlier: low value surrounded by high values |

Pseudo p-values for each $I_i$ are computed by permuting the values of all other units while holding $y_i$ fixed, with 999 permutations. Observations with pseudo p-value above 0.05 are labeled NS (not significant).

Implementation: `src/esda/lisa.py`.

---

## 9. SAR, SEM, and SDM Estimation

### 9.1 Spatial Autoregressive Model (SAR)

The SAR (spatial lag) model is:

$$y = \rho W y + X \beta + \varepsilon, \quad \varepsilon \sim N(0, \sigma^2 I)$$

The log-likelihood is:

$$\ell(\rho, \beta, \sigma^2) = -\frac{N}{2}\log(2\pi\sigma^2) + \log|I - \rho W| - \frac{1}{2\sigma^2}(y - \rho Wy - X\beta)'(y - \rho Wy - X\beta)$$

Estimation uses **concentrated ML**: for fixed $\rho$, the optimal $\beta^*(\rho)$ and $\sigma^{2*}(\rho)$ have closed-form expressions via OLS. Substituting back yields a concentrated log-likelihood $\ell^c(\rho)$ that is maximized by scalar golden-section search over $\rho \in (-1, 1)$.

The log-determinant $\log|I - \rho W|$ is computed via the eigenvalues of $W$: $\log|I - \rho W| = \sum_k \log(1 - \rho \omega_k)$ where $\omega_k$ are the eigenvalues of $W$.

Implementation: `src/spatial_models/sar.py`. Sparse eigenvalues via `scipy.sparse.linalg.eigs`.

### 9.2 Spatial Error Model (SEM)

The SEM models spatial dependence in the error term:

$$y = X \beta + u, \quad u = \lambda W u + \varepsilon, \quad \varepsilon \sim N(0, \sigma^2 I)$$

which implies $y = X\beta + (I - \lambda W)^{-1}\varepsilon$. Estimation follows the same concentrated ML approach as SAR, with scalar search over $\lambda \in (-1, 1)$.

Implementation: `src/spatial_models/sem.py`.

### 9.3 Spatial Durbin Model (SDM)

The SDM includes both a spatial lag of $y$ and spatial lags of the regressors $X$:

$$y = \rho W y + X \beta + WX \theta + \varepsilon$$

The SDM nests both SAR (when $\theta = 0$) and SEM (when the common-factor restriction $\theta = -\rho \beta$ holds). Likelihood ratio tests for these nested restrictions are implemented in `src/spatial_models/sdm.py`.

Implementation: `src/spatial_models/sdm.py`. Wald tests of the common-factor restriction $\theta + \rho\beta = 0$ use a delta-method covariance.

### 9.4 Model Selection

`src/spatial_models/model_registry.py` compares SAR, SEM, and SDM by AIC, BIC, and likelihood ratio tests. The preferred model minimizes AIC subject to passing a spatial dependence test (Lagrange Multiplier test from `spreg`).

---

## 10. LeSage-Pace Direct, Indirect, and Total Effects

In the SAR model, a unit change in covariate $k$ for unit $j$ affects not only unit $j$'s outcome but also the outcomes of all units connected to $j$ through $W$. The total effect on unit $i$ from a change to unit $j$'s covariate is element $(i,j)$ of the matrix:

$$S_k = (I - \rho W)^{-1} I_k \beta_k$$

where $I_k\beta_k$ is the $k$-th column of $(I - \rho W)^{-1}\beta_k$ after selecting the covariate. Effects are summarized as:

- **Direct effect**: Average diagonal element of $S_k$ — own-unit impact
- **Indirect (spillover) effect**: Average off-diagonal row sum of $S_k$ — cross-unit impact
- **Total effect**: Direct + Indirect

**Implementation note**: Dense inversion of $(I - \rho W)^{-1}$ is never computed directly; all implementations use the eigenvalue trace approximation:

$$\frac{1}{N}\text{tr}(S_k) \approx \frac{\beta_k}{N} \sum_{r=0}^{R} \rho^r \text{tr}(W^r)$$

where $\text{tr}(W^r)$ is computed iteratively using sparse matrix powers, truncated at order $R=10$. Implementation: `src/spatial_models/effects.py`.

---

## 11. Geographically Weighted Regression

### 11.1 Model

GWR estimates a spatially varying coefficient model:

$$y_i = X_i \beta(u_i, v_i) + \varepsilon_i$$

where $\beta(u_i, v_i)$ is a vector of locally estimated coefficients at the geographic coordinates $(u_i, v_i)$ of observation $i$. Each $\beta_i$ is estimated by weighted least squares using a kernel function $K_h(d_{ij})$ to downweight observations far from location $i$:

$$\hat{\beta}(u_i, v_i) = (X' W_i X)^{-1} X' W_i y$$

where $W_i = \text{diag}(K_h(d_{i1}), \ldots, K_h(d_{iN}))$.

### 11.2 Kernel Functions

Two kernel types are implemented in `src/gwr/gwr_model.py`:

- **Bisquare (adaptive)**: $K_h(d) = (1 - (d/h)^2)^2 \cdot \mathbf{1}[d < h]$ — hard truncation at bandwidth $h$, suitable for irregular point distributions
- **Gaussian (fixed)**: $K_h(d) = \exp(-d^2 / 2h^2)$ — smooth decay without hard truncation

### 11.3 Bandwidth Selection

The optimal bandwidth $h^*$ minimizes leave-one-out cross-validated sum of squared errors:

$$CV(h) = \sum_i \left( y_i - \hat{y}_{-i}(h) \right)^2$$

where $\hat{y}_{-i}(h)$ is the GWR prediction at location $i$ using all observations except $i$. The hat matrix shortcut avoids refitting the model for each held-out observation.

The `BandwidthSelector` in `src/gwr/bandwidth.py` uses golden-section search over a bounded interval of candidate bandwidths, with optional pickle checkpointing to `data/interim/spatial/bw_checkpoint.pkl` for long-running CV.

---

## 12. Inference Methods Summary

| Method | Where Used | Reference |
|--------|-----------|-----------|
| HC3 heteroskedasticity-robust SE | Hedonic OLS, triple-diff | MacKinnon-White (1985) |
| Multiplier bootstrap (999 draws) | Callaway-Sant'Anna ATT | Callaway-Sant'Anna (2021) |
| Permutation test (999 perms) | Global Moran's I | Cliff-Ord (1981) |
| Permutation test (999 perms) | LISA pseudo p-values | Anselin (1995) |
| In-space placebo + RMSPE rank | ADH / GSynth / AugSynth | Abadie et al. (2010) |
| Leave-one-out donor robustness | ADH / GSynth / AugSynth | Abadie et al. (2015) |
| Likelihood ratio test | SAR vs SEM vs SDM nesting | LeSage-Pace (2009) |
| Delta-method Wald test | SDM common-factor restriction | LeSage-Pace (2009) |

---

## 13. Software and Reproducibility

All estimation code is in `src/`. The full pipeline is orchestrated by the Snakemake DAG in `Snakefile` and can be run with `make phase1`, `make phase2`, `make phase3`. Test coverage is maintained at or above 80% across all modules (158 tests, 0 failures as of Phase 3). Numerical precision tests in `tests/numerical_validation/` validate key estimators against closed-form solutions and published benchmark results.

Random seeds: all test fixtures use `np.random.seed(42)` or `np.random.default_rng(42)`. GWR checkpoint files ensure bandwidth selection can be resumed without recomputation.
