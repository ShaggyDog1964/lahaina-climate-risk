# Literature Guide: Econometric Identification

## Sections: Hedonic pricing · Callaway-Sant'Anna DiD · Triple difference · Synthetic control methods
## Purpose: ground every estimator in this codebase to its published paper and equation

---

## 1. Hedonic Pricing Model

### What the code does

`HedonicModel.fit()` in `src/models/hedonic.py` fits OLS on a long-panel DataFrame where the
outcome is `log_price` (log of transaction price). The right-hand side includes three continuous
covariates — `structure_sqft`, `land_area_sqft`, `year_built` — plus categorical dummies for
`zoning`, `fe_block` (census-block fixed effect), and `fe_yearmonth` (year-month fixed effect).
All fixed effects are absorbed via dummy variables passed directly to `statsmodels.formula.api.ols`
using the `C()` patsy notation; no within-transformation is applied. Standard errors use HC3
heteroskedasticity-robust covariance via `model.fit(cov_type="HC3")`.

### The math (verified against code)

The regression equation as implemented is:

```
log_price_it = α
             + β₁ structure_sqft_i
             + β₂ land_area_sqft_i
             + β₃ year_built_i
             + Σ_z δ_z · 𝟏[zoning_i = z]
             + Σ_b γ_b · 𝟏[fe_block_i = b]
             + Σ_τ λ_τ · 𝟏[fe_yearmonth_it = τ]
             + ε_it
```

**Within-transformation:** The code does NOT apply a Mundlak or Frisch-Waugh within-transform.
Block and time fixed effects are included as saturated dummy sets via `C(fe_block)` and
`C(fe_yearmonth)` in the patsy formula, so OLS absorbs them as explicit parameters. This is
numerically equivalent to within-demeaning but retains the FE coefficients in the parameter
vector.

**HC3 standard errors:** The code calls `model.fit(cov_type="HC3")`, which instructs statsmodels
to use the MacKinnon-White HC3 sandwich estimator:

```
V̂_HC3(β̂) = (X'X)⁻¹ [ Σᵢ ê²ᵢ / (1 − hᵢᵢ)² · xᵢxᵢ' ] (X'X)⁻¹
```

where `ê_i = y_i − x_i'β̂` is the OLS residual for observation i, and `h_ii = x_i'(X'X)⁻¹x_i`
is the leverage of observation i. Squaring `(1 − h_ii)` in the denominator (rather than the
single power used in HC2) gives larger inflation for high-leverage points and better finite-sample
coverage.

### Papers

1. **Rosen, S. (1974). "Hedonic Prices and Implicit Markets: Product Differentiation in Pure Competition." *Journal of Political Economy* 82(1): 34–55.**
   DOI: 10.1086/260169
   **Code connection:** `HedonicModel.fit()` in `src/models/hedonic.py`
   **Key insight:** In competitive equilibrium, the marginal implicit price of any attribute equals the consumer's marginal willingness to pay and the producer's marginal cost. The hedonic price function P(z) is the envelope of consumer bid functions — it identifies the market-clearing price gradient, not structural demand.
   **Read:** Sections I–III (the theory); Section IV (the regression). Budget 2 hours.
   **Why the project uses it:** Establishes the log-linear price gradient used to control for structural attributes before computing the fire-proximity treatment effect. The residuals from the hedonic feed Phase 3 spatial autocorrelation tests.

2. **Palmquist, R.B. (1984). "Estimating the Demand for the Characteristics of Housing." *Review of Economics and Statistics* 66(3): 394–404.**
   DOI: 10.2307/1925928
   **Code connection:** Theoretical motivation for including structural and locational covariates (`structure_sqft`, `land_area_sqft`, `year_built`, `zoning`) to isolate the fire-proximity price gradient.
   **Key insight:** Environmental disamenities are identified by comparing similar homes that differ only in exposure — the key identification assumption underlying fire-proximity price gradients.
   **Read:** Sections I–III. 45 minutes.

3. **MacKinnon, J. and White, H. (1985). "Some Heteroskedasticity-Consistent Covariance Matrix Estimators with Improved Finite Sample Properties." *Journal of Econometrics* 29(3): 305–325.**
   DOI: 10.1016/0304-4076(85)90158-7
   **Code connection:** HC3 standard errors via `model.fit(cov_type="HC3")` in `HedonicModel.fit()`
   **Key insight:** HC3 inflates each squared residual by `1/(1−h_ii)²` where `h_ii` is the leverage of observation i; high-leverage observations receive more inflation, providing better finite-sample coverage than White's HC0/HC1.
   **Read:** Section 3 (the HC3 estimator). 30 minutes.

---

## 2. Callaway-Sant'Anna Difference-in-Differences

### What the code does

`CallawayAntaCSiD.fit()` in `src/models/did_cs.py` wraps the `csdid` library. The outcome
variable is `log_price` (configurable). Treatment groups are identified by the `treatment_band`
column; units where `treatment_band == "control"` form the comparison group. When `csdid` is
available, the code calls `ATTgt(..., control_group="notyettreated")`, which uses the
**not-yet-treated** comparison group (units that have not yet received treatment as of each
calendar period). The estimator is invoked with `cs.fit(est_method="dr")`, selecting the
**doubly-robust** IPW-regression estimator. All treated groups (`treatment_band != "control"`)
are assigned the same first-treatment time integer (the first `post == 1` period), making this
effectively a sharp single-event staggered design.

ATT(g,t) estimates are returned in a DataFrame; `agg_simple` averages ATT across all (g,t) pairs
with equal weight; `agg_dynamic` groups by calendar time and averages ATT within each period,
producing a simple event study indexed by calendar time (not event time). A fallback TWFE OLS
with `treated * post` interaction is used if `csdid` import fails.

### The math (verified against code)

**ATT(g,t) definition:**
```
ATT(g,t) = E[Y_t(g) − Y_t(0) | G = g]
```
where `G = g` means "first treated at calendar time g" and `Y_t(0)` is the counterfactual
never-treated potential outcome.

**Doubly-robust estimator (Callaway-Sant'Anna, eq. 3.1):**
The `dr` method combines inverse-probability weighting (propensity score model for group
membership) with outcome regression (linear model for the control group trend), yielding
consistency if either the propensity model or the outcome model is correctly specified:

```
ATT̂_DR(g,t) = E̊[ (Y_t − Y_{g−1}) · [G=g / P(G=g)]
              − p̂(X) / (1 − p̂(X)) · (1 − G=g) · (Y_t − Y_{g−1})
              − (m̂_{g,t}(X) − m̂_{g,g−1}(X)) · [G=g / P(G=g) − p̂(X)/(1−p̂(X))] ]
```
where `p̂(X)` is the estimated propensity score for being in cohort g and `m̂` is the outcome
regression on the not-yet-treated comparison group.

**Aggregation to event study (as implemented):**
```
θ̂^es(τ) = mean_g ATT̂(g, τ)
```
The code groups by `time` and averages ATT with equal weight across all cohorts at each calendar
period (not by cohort-size weights). This is a simplification of the C&S weighted aggregation.

**Parallel trends assumption (conditional on X):**
```
E[Y_t(0) − Y_{g−1}(0) | X, G = g] = E[Y_t(0) − Y_{g−1}(0) | X, G ∈ not-yet-treated]
```

### Papers

1. **Goodman-Bacon, A. (2021). "Difference-in-Differences with Variation in Treatment Timing." *Journal of Econometrics* 225(2): 254–277.**
   DOI: 10.1016/j.jeconom.2021.03.014
   **Code connection:** Justification for not using TWFE (`linearmodels` PanelOLS) as the primary estimator — the project uses C&S instead; the TWFE fallback in `_fit_twfe_fallback()` is explicitly labelled an approximation.
   **Key insight:** β_TWFE decomposes into a weighted average of all pairwise 2×2 DiD comparisons; some weights are negative because late-treated units act as controls for early-treated units, and with heterogeneous treatment effects TWFE can have the wrong sign.
   **Read:** Section 2 (Theorem 1 — the decomposition). 2 hours. Read this before Callaway-Sant'Anna.

2. **de Chaisemartin, C. and D'Haultfœuille, X. (2020). "Two-Way Fixed Effects Estimators with Heterogeneous Treatment Effects." *American Economic Review* 110(9): 2964–2996.**
   DOI: 10.1257/aer.20181169
   **Code connection:** Further justification for C&S over TWFE.
   **Key insight:** Provides the "contamination bias" formula: TWFE equals a weighted sum of ATTs where weights can be negative, with contamination bias arising when already-treated units serve as the control in the DiD comparison.
   **Read:** Sections I–II. 1.5 hours.

3. **Callaway, B. and Sant'Anna, P. (2021). "Difference-in-Differences with Multiple Time Periods." *Journal of Econometrics* 225(2): 200–230.**
   DOI: 10.1016/j.jeconom.2020.12.001
   **Code connection:** Direct implementation in `src/models/did_cs.py` via `csdid.att_gt.ATTgt` with `control_group="notyettreated"` and `est_method="dr"`. This IS the estimator.
   **Key insight:** Proposes ATT(g,t) — cohort-time-specific average treatment effects — and shows how to aggregate them into event studies and simple average ATTs without negative weights, as long as identification uses "clean" controls (never-treated or not-yet-treated).
   **Read:** Sections 2–4 (ATT definition, estimator, aggregation). Section 5 (inference via bootstrap) is secondary. Budget 4 hours.
   **Math to derive:** Equations (2.1)–(2.4) define ATT(g,t). Equations (4.1)–(4.3) define the three aggregations (simple, dynamic, group-specific). Table 1 summarises the estimator variants including the DR version used here.

4. **Sun, L. and Abraham, S. (2021). "Estimating Dynamic Treatment Effects in Event Studies with Heterogeneous Treatment Effects." *Journal of Econometrics* 225(2): 175–199.**
   DOI: 10.1016/j.jeconom.2020.09.006
   **Code connection:** Alternative to C&S considered in robustness; uses the interaction-weighted estimator.
   **Key insight:** The interaction-weighted (IW) estimator is a saturated regression that includes all treatment-cohort-time interactions; it is numerically equivalent to C&S under the same assumptions but is easier to implement in standard regression software.
   **Read:** Sections 2–3. 2 hours.

5. **Roth, J., Sant'Anna, P., Bilinski, A., Poe, J. (2023). "What's Trending in Difference-in-Differences? A Synthesis of the Recent Econometrics Literature." *Journal of Econometrics* 235(2): 2218–2244.**
   DOI: 10.1016/j.jeconom.2023.03.008
   **Code connection:** Survey of the entire DiD literature — the map of the field.
   **Key insight:** Organises C&S, Sun-Abraham, de Chaisemartin-D'Haultfœuille, Borusyak et al., and others into a unified framework; shows when they agree and when they diverge. Under the same parallel trends assumption, all modern DiD estimators converge.
   **Read:** Entire paper — it is a survey and accessible. 2 hours.

6. **Angrist, J. and Pischke, J.S. (2009). *Mostly Harmless Econometrics.* Princeton University Press.**
   ISBN: 978-0-691-12034-8
   **Code connection:** Conceptual grounding for the parallel trends assumption.
   **Read:** Chapter 5, Section 5.3 (parallel trends). 1 hour. Prerequisite before Goodman-Bacon.

---

## 3. Triple-Difference Decomposition

### What the code does

`TripleDifference.fit()` in `src/models/triple_diff.py` constructs three binary indicator columns
from the panel: `is_treated` (`treatment_band != "control"`), `is_wui` (`wui_class` in
`["Intermix", "Interface"]`), and their interactions `post_x_treated`, `post_x_wui`, and
`triple` (`post * is_treated * is_wui`). The primary path uses `linearmodels.panel.PanelOLS`
with `entity_effects=True` and `time_effects=True` and clustered standard errors
(`cov_type="clustered", cluster_entity=True`). When the panel is a pure cross-section (≤1
observation per entity) or `linearmodels` fails, it falls back to
`statsmodels.formula.api.ols` with the formula
`log_price ~ post * is_treated * is_wui + C(fe_yearmonth) + C(parcel_id)` and HC3 errors.

`decompose()` extracts three quantities from the fitted parameters:
- `beta_post_treated_wui` — the coefficient on the `triple` term (post × treated × WUI),
  interpreted as "direct damage plus belief update"
- `beta_post_treated_nowui` — the coefficient on `post_x_treated` (post × treated, non-WUI),
  interpreted as "displacement / market friction"
- `belief_update_channel` — the difference `beta_post_treated_wui − beta_post_treated_nowui`,
  with standard error `sqrt(se_wui² + se_nowui²)`, interpreted as "pure belief update estimate"

Optional macro controls (`UNRATE`, `FEDFUNDS`, `MORTGAGE30US`, `CSUSHPINSA`) are included if
present in the panel.

### The math (verified against code)

For the PanelOLS path (entity + time effects absorbed):

```
log_price_it = α
             + β₁ (post_t × treated_i × WUI_i)     [triple]
             + β₂ (post_t × treated_i)               [post_x_treated]
             + β₃ (post_t × WUI_i)                   [post_x_wui]
             + β₄ treated_i
             + β₅ WUI_i
             + β₆ post_t
             + Σ_c δ_c · macro_controls_ct           [if present]
             + μ_i                                    [entity FE, absorbed]
             + λ_t                                    [time FE, absorbed]
             + ε_it
```

**Belief-update channel:** `β₁ − β₂`
(the incremental discount on WUI-treated parcels relative to non-WUI-treated parcels, conditional
on being post-fire and treated)

**Physical displacement / market friction channel:** `β₂`
(the base post-fire discount for all treated parcels regardless of WUI classification)

**Standard error of belief-update channel:** `sqrt(se_β₁² + se_β₂²)`
(treating β₁ and β₂ as independent — conservative if they are positively correlated)

**Identification assumption:** WUI classification is exogenous to post-fire price movements. WUI
is determined by 2010 vegetation density and structure density (USFS Silvis Lab) and predates
the 2023 fire; selection into WUI is not driven by endogenous fire-risk exposure at the time of
treatment.

### Papers

1. **Gruber, J. (1994). "The Incidence of Mandated Maternity Benefits." *American Economic Review* 84(3): 622–641.**
   **Code connection:** Conceptual foundation for the triple-difference estimator design in `TripleDifference`.
   **Key insight:** The triple-difference β₁ − β₂ identifies the differential effect on one subgroup (WUI) versus another (non-WUI) within the treated group, removing confounders that affect all treated parcels equally. This is the "difference out the confounders" interpretation of DiD³.
   **Read:** Section II (the triple-difference design). 45 minutes.

2. **Angrist, J. and Pischke, J.S. (2009).** [Already listed above — re-read Section 5.1 on DD³ interpretation.]

---

## 4. Synthetic Control Methods

### What the code does

**ADH (`src/scm/adh_scm.py`):** `ADHSyntheticControl._inner_qp()` solves a convex QP using
`cvxpy` with solvers tried in order (CLARABEL, SCS, ECOS). The outer V-matrix loop is in
`_outer_mspe()`, which normalises the diagonal so it sums to 1 before calling the inner QP.
`fit()` runs `scipy.optimize.minimize` with `method="L-BFGS-B"` over the raw (unnormalised)
v_diag; the final V is set to `diag(abs(v*) / sum(abs(v*)))`. Pre-RMSPE is stored as
`pre_rmspe_`; post-RMSPE and `rmspe_ratio_` are computed by `_compute_post_rmspe()` when
`Y0_all` and `Y1_all` are passed to `fit()`, or lazily via `post_rmspe()`.

**Placebo inference (`src/inference/placebo.py`):** `InSpacePlacebo.run()` designates each
donor ZIP as a pseudo-treated unit in turn (parallel via `joblib`), fits the same SCM class
with the remaining donors as the new donor pool, and computes `pre_rmspe`, `post_rmspe`, and
`rmspe_ratio` for each. `p_value(treated_ratio)` returns
`count(rmspe_ratio_j ≥ treated_ratio) / J` (inclusive rank). `discard_poor_fit()` removes
placebos with `pre_rmspe > multiple × treated_pre_rmspe` before re-ranking.

**GSynth (`src/scm/gsynth.py`):** `GeneralizedSyntheticControl.fit()` initialises factors via
SVD of the donor pre-period matrix, then runs alternating least-squares (EM-like) for up to 200
iterations: E-step estimates loadings `Lambda0` and `lambda_1` by OLS given current `F`; M-step
updates `F` by OLS given `Lambda0`. Post-period factors are estimated from donor post-period
data using the converged `Lambda0`. `r` is a hyperparameter; `select_r()` uses leave-one-out
CV over donors to choose the optimal value.

**AugSCM (`src/scm/augsynth.py`):** `AugmentedSyntheticControl.fit()` takes pre-computed ADH
weights `w_adh`. For each time period t it fits a Ridge regression with pre-period donor
outcomes as features to predict each donor's outcome at t; the treated unit's prediction at t
uses the treated pre-period series as features. The bias correction is the weighted donor ridge
prediction subtracted from the treated ridge prediction. Ridge `lambda` is tuned by LOOCV over
donors across a grid `[0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]` if not supplied.

### The math — ADH (verified against code)

**Inner QP (`_inner_qp()`, solved by cvxpy):**
```
w* = argmin_w  (X₁ − X₀ w)' V (X₁ − X₀ w)
     s.t.  w ≥ 0,  Σⱼ wⱼ = 1
```
where `X₁` is the treated unit's covariate vector (k,), `X₀` is the donor covariate matrix
(k, J), and `V = diag(v_diag / sum(v_diag))` is the importance diagonal.

**Outer V-matrix optimisation (`_outer_mspe()`, minimised by L-BFGS-B):**
```
V* = argmin_{v ≥ 0}  MSPE_pre(w*(V(v)))

MSPE_pre = (1/T₀) ‖ Y₁_pre − Y₀_pre w*(V) ‖²
```
Note: the outer objective uses pre-period *outcome* fit (Y₀_pre, Y₁_pre), not covariate fit,
consistent with the ADH (2010) outer-loop specification.

**Post-treatment gap:**
```
α̂_t = Y₁_t − Y₀_t' w*,   for t > T₀
```

**Pre-RMSPE and post-RMSPE:**
```
pre_RMSPE  = sqrt( (1/T₀) ‖ Y₁_pre  − Y₀_pre  w* ‖² )
post_RMSPE = sqrt( (1/T₁) ‖ Y₁_post − Y₀_post w* ‖² )
```

**Permutation p-value (`InSpacePlacebo.p_value()`):**
```
p = Σⱼ 𝟏[ rmspe_ratio_j ≥ rmspe_ratio_treated ] / J
```
where `rmspe_ratio = post_RMSPE / pre_RMSPE` and J is the number of donor placebos that passed
the `discard_poor_fit` filter (if applied).

### The math — GSynth (verified against code)

**IFE model:**
```
Y_it = δ_it D_it + λ_i' F_t + ε_it
```
where `F_t` is a (r,) latent factor vector at time t and `λ_i` is the (r,) unit loading.

**Alternating LS algorithm (as implemented — not standard EM over a latent variable model,
but equivalent in estimation):**
1. Initialise F (T₀ × r) via SVD of Y₀_pre: `U[:, :r] * S[:r]`
2. E-step: `Lambda0 = lstsq(F, Y₀_pre)` → (r, J);  `lambda_1 = lstsq(F, Y₁_pre)` → (r,)
3. M-step: `F = lstsq(Lambda0', Y₀_pre')'.T` → (T₀, r)
4. Repeat until `‖F_new − F_old‖_F < 1e-6` or 200 iterations.
5. Extend to post period: `F_post = lstsq(Lambda0', Y₀_post')'.T`

**Counterfactual:**
```
Ŷ₁_t(0) = F_t' λ̂₁,   for all t
```

**Treatment effect:**
```
τ̂_t^GSynth = Y₁_t − F̂_t' λ̂₁
```

### The math — AugSCM (verified against code)

**Ridge outcome model:** For each time period t, fit Ridge regression:
```
m̂_t: Y₀_pre.T (J × T₀) → Y₀_all[t, :] (J,)
```
treating each donor as a training sample with its own pre-period series as features.

**Treated counterfactual at t:**
```
m̂₁_t = Ridge_t.predict(Y₁_pre.reshape(1, -1))
```

**Weighted donor counterfactual at t:**
```
m̂₀_t^w = Σⱼ wⱼ* · Ridge_t.predict(Y₀_pre[:, j])
         = (Ridge_t.predict(Y₀_pre.T)) @ w_adh
```

**Bias correction:**
```
bias_t = m̂₁_t − m̂₀_t^w
```

**Augmented gap:**
```
τ̂_t^ASCM = (Y₁_t − Y₀_t' w*) − bias_t
           = τ̂_t^raw  −  (m̂₁_t − Σⱼ wⱼ* m̂ⱼ_t)
```

### Papers

1. **Abadie, A., Diamond, A., Hainmueller, J. (2015). "Comparative Politics and the Synthetic Control Method." *American Journal of Political Science* 59(2): 495–510.**
   DOI: 10.1111/ajps.12116
   **Code connection:** Intuition behind `ADHSyntheticControl` — read before the 2010 paper.
   **Key insight:** The synthetic control "speaks for itself" — a well-fitting pre-period trajectory convinces readers that the post-period gap is causal without requiring a significance test; the weight-based transparency is the method's key advantage over a black-box regression.
   **Read:** Entire paper — it is short and accessible. 1 hour.

2. **Abadie, A., Diamond, A., Hainmueller, J. (2010). "Synthetic Control Methods for Comparative Case Studies: Estimating the Effect of California's Tobacco Control Program." *JASA* 105(490): 493–505.**
   DOI: 10.1198/jasa.2009.ap08746
   **Code connection:** Equations (1)–(4) are implemented directly in `ADHSyntheticControl._inner_qp()` (inner QP) and `._outer_mspe()` (outer MSPE minimisation).
   **Key insight:** The outer V-matrix optimisation makes the synthetic control differ from simple matching — it down-weights predictors that do not help pre-period outcome fit, which is crucial when X₁ has more variables than donors.
   **Read:** Equations (1)–(4). Section 4 (inference via placebo). 3 hours.

3. **Abadie, A. (2021). "Using Synthetic Controls: Feasibility, Data Requirements, and Methodological Aspects." *Journal of Economic Literature* 59(2): 391–425.**
   DOI: 10.1257/jel.20191450
   **Code connection:** Complete reference for all design choices in the SCM implementation — donor pool construction, covariate selection, V-matrix, inference.
   **Key insight:** SCM requires (a) many pre-treatment periods (T₀ ≥ 15 recommended), (b) the convex hull condition (treated unit's outcomes lie in span of donors), and (c) no interference; with only ~8 Hawaii ZIP codes and a pre-period of < 24 months, this project is at the lower boundary of SCM feasibility.
   **Read:** Sections I–V. 4 hours. The definitive reference.

4. **Xu, Y. (2017). "Generalized Synthetic Control Method: Causal Inference with Interactive Fixed Effects Models." *Political Analysis* 25(1): 57–76.**
   DOI: 10.1017/pan.2016.2
   **Code connection:** `GeneralizedSyntheticControl.fit()` in `src/scm/gsynth.py`.
   **Key insight:** GSynth does not require the convex hull condition — the IFE model extrapolates outside the support of donor outcomes via factor structure, which is more powerful but less transparent than ADH; `select_r()` chooses the number of factors by leave-one-out CV over donors.
   **Read:** Sections 2–3 (model and alternating LS algorithm). 2 hours.

5. **Ben-Michael, E., Feller, A., Rothstein, J. (2021). "The Augmented Synthetic Control Method." *JASA* 116(536): 1789–1803.**
   DOI: 10.1080/01621459.2021.1929245
   **Code connection:** `AugmentedSyntheticControl.fit()` in `src/scm/augsynth.py`.
   **Key insight:** When pre-period fit is imperfect (pre-RMSPE > 0), the plain ADH gap is biased; the ridge bias-correction `bias_t = m̂₁_t − Σⱼ wⱼ m̂ⱼ_t` debiases the gap, and the estimator is doubly robust — consistent if either the SCM weights or the ridge outcome model is correctly specified.
   **Read:** Sections 1–3 (setup, bias correction, inference). 3 hours.

6. **Ferman, B. and Pinto, C. (2021). "Synthetic Controls with Imperfect Pretreatment Fit." *Quantitative Economics* 12(4): 1197–1221.**
   DOI: 10.3982/QE1596
   **Code connection:** Explains why the Hawaii setting (few donors, short pre-period) produces wide confidence intervals and why `discard_poor_fit()` in `InSpacePlacebo` matters.
   **Key insight:** Pre-period RMSPE is not a sufficient statistic for SCM quality — if pre-period fit is achieved by chance (few donors, many covariates), the post-period gap is uninformative; with J < 20 donors and T₀ < 20, inference is unreliable unless poor-fitting placebos are discarded.
   **Read:** Section 2 (the problem). 1.5 hours.
