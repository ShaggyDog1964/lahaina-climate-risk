# Literature Guide: Spatial Econometrics
## Sections: Spatial weights · Moran's I · LISA · SAR · SEM · SDM · LeSage-Pace effects · GWR
## Purpose: ground every spatial estimator in this codebase to its published paper and equation

---

## 1. Spatial Weights Matrix

### What the code does

`SpatialWeightsFactory` in `src/spatial/weights_phase3.py` implements three weight types:

- **KNN** (`build_knn`): k-nearest neighbors with default k=8, projected to EPSG:32604 (UTM Zone 4N, appropriate for Maui). Row-standardized via `w.transform = "r"`.
- **IDW** (`build_idw`): inverse-distance-squared weights within a bandwidth (default 10 km). For each unit i, raw weight to neighbor j is 1/d², then row-normalized so weights sum to 1. Row-standardized.
- **Queen** (`build_queen`): queen contiguity for polygon geometry. Falls back to KNN(k=6) with a warning when geometry is Point type (the typical case for parcel centroids). Row-standardized.

All three weight types are built by `build_all()` and returned as `libpysal.weights.W` objects. Conversion to `scipy.sparse.csr_matrix` is handled by `to_sparse()`, which explicitly forces `sp.csr_matrix` (not `csr_array`) to maintain scipy compatibility.

Eigenvalues are computed and cached by `eigenvalues()`. The method uses `scipy.sparse.linalg.eigs` with `k = min(n-2, n)` eigenvalues requested, extracting real parts of complex results. If `eigs` fails (e.g., very small n), it falls back to dense `np.linalg.eigvals`. Eigenvalues are sorted ascending and saved to a `.npy` cache file (e.g., `data/interim/spatial/eigenvalues_knn.npy`). They are used to evaluate the log-determinant in SAR, SEM, and SDM concentrated likelihoods and to compute the feasible range of the spatial parameter.

### The math (verified against code)

**KNN weight definition** (before row-standardization):

```
w_ij^(raw) = 1  if j is among the k nearest neighbors of i
           = 0  otherwise
```

**Row-standardization** (applied to all three weight types):

```
w_ij = w_ij^(raw) / sum_l w_il^(raw)
```

After row-standardization, each row sums to 1 and Wy is a simple average of neighbors' y values.

**IDW raw weight** (before row-standardization):

```
w_ij^(raw) = 1 / max(d_ij, 1)^2   for d_ij <= bandwidth_m
           = 0                      otherwise
```

where d_ij is Euclidean distance in metres between projected centroids i and j.

### Papers

1. **Anselin, L. (1988). *Spatial Econometrics: Methods and Models.* Kluwer Academic.**
   ISBN: 978-90-247-3735-2
   **Code connection:** Foundational reference for weight matrix construction in `SpatialWeightsFactory`
   **Key insight:** The choice of spatial weights W is the "first, crucial decision in spatial econometrics." Row-standardization (w_ij → w_ij / sum_j w_ij) ensures the spatial lag Wy is a local average of neighbors, but it changes the interpretation of the spatial parameter rho — it no longer has a natural distance-decay interpretation.
   **Read:** Chapter 2 (spatial weights). 2 hours.

2. **Getis, A. and Aldstadt, J. (2004). "Constructing the Spatial Weights Matrix Using a Local Statistic." *Geographical Analysis* 36(2): 90–104.**
   DOI: 10.1111/j.1538-4632.2004.tb01127.x
   **Key insight:** KNN weights are preferred when density of observations varies spatially — each unit always has exactly k neighbors regardless of geographic clustering. This is appropriate for the parcel dataset where parcels cluster near the fire perimeter.
   **Read:** Sections 1–2. 1 hour.

---

## 2. Global Moran's I

### What the code does

`GlobalMoransI.fit()` in `src/esda/morans.py` accepts a raw array `y` and a `sp.csr_matrix` W. It standardizes y to z-scores (subtract mean, divide by std), then computes:

```python
z = (y - y.mean()) / y.std()
Wz = W @ z
S0 = W.sum()
I = (z @ Wz) / (z @ z) * (n / S0)
```

**Analytical variance:** The code uses the Cliff-Ord kurtosis-corrected ("randomization") form, not the simpler normality form. Specifically:

```python
S1 = 0.5 * (W + W.T).power(2).sum()
S2 = sum((row_sums + col_sums)**2)
A = n * ((n^2 - 3n + 3)*S1 - n*S2 + 3*S0^2)
B = mean(z^4) / mean(z^2)^2     # kurtosis factor
C = B * ((n^2 - n)*S1 - 2n*S2 + 6*S0^2)
D = (n-1)(n-2)(n-3)*S0^2
Var_I = (A - C) / D - E[I]^2
```

This is the randomization variance formula from Cliff and Ord (1981), which uses the sample kurtosis B to correct for non-normality. The z-statistic uses this variance. A two-tailed analytical p-value is computed via `scipy.stats.norm`.

**Permutation inference:** 999 permutations (default). Each permutation shuffles z globally (not conditionally), recomputes I, and the empirical p-value is `(count(I_perm >= I_obs) + 1) / (999 + 1)` — a one-sided upper-tail test.

The input `y` is whatever the caller passes in. In the Snakefile `global_morans` rule, `y_raw` (raw price change) is passed, not hedonic residuals.

### The math (verified against code)

**Moran's I statistic:**

```
I = (n / S0) * (z'Wz / z'z)
```

where z_i = (y_i - y_bar) / s_y and S0 = sum_i sum_j w_ij.

**Analytical expectation:**

```
E[I] = -1 / (n - 1)
```

**Cliff-Ord randomization variance (as implemented):**

```
S0 = sum_{ij} w_ij
S1 = (1/2) * sum_{ij} (w_ij + w_ji)^2
S2 = sum_i (sum_j w_ij + sum_j w_ji)^2

A = n * [(n^2 - 3n + 3)*S1 - n*S2 + 3*S0^2]
B = [n^{-1} sum_i z_i^4] / [n^{-1} sum_i z_i^2]^2    (kurtosis)
C = B * [(n^2 - n)*S1 - 2n*S2 + 6*S0^2]
D = (n-1)(n-2)(n-3)*S0^2

Var[I] = (A - C) / D - [E[I]]^2
```

**z-statistic:**

```
z = (I - E[I]) / sqrt(max(Var[I], 1e-12))
```

### Known issue with current implementation

The `global_morans` Snakefile rule feeds `y_raw` (raw price change) to Moran's I, not hedonic residuals. The published Moran's I on residuals requires that the hedonic model be estimated first and residuals passed through. This is documented in `docs/RESEARCH_ASSESSMENT.md` §4.

### Papers

1. **Moran, P.A.P. (1950). "Notes on Continuous Stochastic Phenomena." *Biometrika* 37(1/2): 17–23.**
   DOI: 10.2307/2332142
   **Code connection:** The statistic I = (n/S0) * (z'Wz / z'z) in `GlobalMoransI.fit()`
   **Key insight:** The spatial correlation statistic is analogous to Pearson's r — it measures whether neighbors have similar values. The normalization by S0 = sum_ij w_ij ensures I is scale-invariant with respect to the weight matrix.
   **Read:** The entire 7-page paper. 45 minutes.

2. **Cliff, A. and Ord, J.K. (1981). *Spatial Processes: Models and Applications.* Pion Limited.**
   ISBN: 0-85086-085-6
   **Code connection:** The kurtosis-corrected randomization variance in `GlobalMoransI.fit()` — the code implements the Cliff-Ord moments using the B factor (sample kurtosis), not the simpler normality-assumption formula.
   **Key insight:** Under the randomization assumption (observed values are a random permutation of the fixed set {y_1,...,y_n}), Var[I] includes a kurtosis correction term B that adjusts for heavy-tailed distributions. The code's use of `mean(z^4) / mean(z^2)^2` as B is exactly this correction. When y is normally distributed, B = 3 and the randomization and normality forms coincide.
   **Read:** Chapter 1 (the statistic) and Chapter 2 (moments). 3 hours.

3. **Anselin, L. (1996). "The Moran Scatterplot as an ESDA Tool to Assess Local Instability in Spatial Association." In *Spatial Analytical Perspectives on GIS.* Taylor & Francis.**
   **Key insight:** The Moran scatterplot (z vs Wz) partitions space into four quadrants that correspond exactly to the LISA HH/HL/LH/LL classification. The slope of the Moran scatterplot regression line is Moran's I. This geometric interpretation connects global and local statistics.

---

## 3. Local Indicators of Spatial Association (LISA)

### What the code does

`LocalMoransI.fit()` in `src/esda/lisa.py` standardizes y to z-scores, computes `Wz = W @ z`, then assigns local statistics:

```python
z = (y - y.mean()) / y.std()
Wz = np.asarray(W @ z).ravel()
I_local = z * Wz   # element-wise product, shape (n,)
```

**Permutation p-values:** 999 permutations (default). For each permutation k, the full z vector is shuffled globally. The per-observation count is `sum_k (I_perm_k[i] >= I_local[i])`, accumulated over all permutations. The pseudo p-value is `(count + 1) / (999 + 1)`. Note: this is a global shuffle, not the conditional permutation (hold z_i fixed, shuffle only the neighbors) described in Anselin (1995). The unconditional shuffle is computationally simpler but slightly less conservative.

**Significance threshold:** alpha = 0.05 (default, passed as parameter). Observations with `p_value >= 0.05` receive the "NS" label.

**Quadrant classification** (as implemented, applied only to significant observations):

- **HH:** z_i > 0 and (Wz)_i > 0
- **LL:** z_i < 0 and (Wz)_i < 0
- **HL:** z_i > 0 and (Wz)_i < 0 (spatial outlier: high value surrounded by low values)
- **LH:** z_i < 0 and (Wz)_i > 0 (spatial outlier: low value surrounded by high values)
- **NS:** p_value >= alpha

### The math (verified against code)

**Local Moran's I for observation i:**

```
I_i = z_i * (Wz)_i
```

where:

```
z_i = (y_i - y_bar) / s_y
(Wz)_i = sum_j w_ij * z_j
```

Note that z is the full-sample standardization, not a local one. The product z_i * (Wz)_i measures whether unit i's deviation from the mean is reinforced by its neighbors' deviations.

**Relationship to global I** (Anselin 1995):

```
I = (1/(n-1)) * sum_i I_i     (approximately, up to a scaling constant)
```

**Pseudo p-value:**

```
p_i = (#{k : I_perm_k[i] >= I_obs[i]} + 1) / (n_perm + 1)
```

### Papers

1. **Anselin, L. (1995). "Local Indicators of Spatial Association—LISA." *Geographical Analysis* 27(2): 93–115.**
   DOI: 10.1111/j.1538-4632.1995.tb00338.x
   **Code connection:** Equations (1)–(6) are directly implemented in `LocalMoransI.fit()`. The quadrant labels (HH/LL/HL/LH) match the paper's Figure 1. The alpha = 0.05 NS threshold is the paper's recommended default.
   **Key insight:** LISA decomposes the global Moran's I into local contributions: I ~ (1/(n-1)) * sum_i I_i. The pseudo p-value for each I_i uses permutation inference — randomly permute all values to generate the null distribution of (Wz)_i. The paper recommends conditional permutation (hold z_i fixed), which is slightly more conservative than the global shuffle used here.
   **Read:** Sections 2–3 (the statistic and quadrant map). 2 hours. This paper IS the implementation.

---

## 4. Spatial Autoregressive Model (SAR)

### What the code does

`SpatialLagModel.fit()` in `src/spatial_models/sar.py` estimates SAR via concentrated maximum likelihood over rho.

**Log-determinant:** The code uses the eigenvalue trick (Ord 1975). Eigenvalues of W are passed in as a precomputed array. The concentrated LL evaluates `sum(log(abs(1 - rho * eigenvalues)))` on every function call — O(n) after eigenvalue precomputation.

**Optimizer:** `scipy.optimize.minimize_scalar` with `method="bounded"`. Bounds are `[1/lambda_min + 1e-4, 1/lambda_max - 1e-4]` derived from the eigenvalues, clamped to (-0.9999, 0.9999).

**Standard errors:** Numerical Hessian of the full (unconcentrated) log-likelihood in the parameter vector `[rho, beta_1, ..., beta_k]` using a centered finite-difference scheme with step `eps = 1e-5`. The covariance matrix is `-H^{-1}`. SEs are `sqrt(abs(diag(cov)))`. If `H` is singular, SEs are NaN.

**Inputs:** The method accepts whatever y array the caller passes. The caller is responsible for passing raw or transformed y.

### The math (verified against code)

**Model:**

```
y = rho*Wy + X*beta + eps,   eps ~ N(0, sigma^2 * I)
```

**Full log-likelihood:**

```
L(rho, beta, sigma^2) = log|I - rho*W| - (n/2)*log(2*pi*sigma^2) - (1/(2*sigma^2)) * ||(I-rho*W)y - X*beta||^2
```

**For fixed rho, MLE solutions (via lstsq):**

```
beta_hat(rho) = (X'X)^{-1} X' (I-rho*W)y
sigma^2_hat(rho) = ||(I-rho*W)y - X*beta_hat(rho)||^2 / n
```

**Concentrated log-likelihood (as implemented — note: negated for minimization):**

```
L*(rho) = log|I-rho*W| - (n/2)*log(sigma^2_hat(rho))
```

The code minimizes `-L*(rho)`.

**Log-determinant via eigenvalues (Ord 1975):**

```
log|I - rho*W| = sum_i log(1 - rho*lambda_i)
```

where lambda_i are eigenvalues of W, precomputed and cached. The code takes `log(abs(...))` to handle any residual imaginary parts after taking real parts.

**Feasible range of rho:**

```
1/lambda_min < rho < 1/lambda_max
```

where lambda_min and lambda_max are the minimum and maximum eigenvalues of W.

**Full log-likelihood (for Hessian-based SEs):**

```
L(rho, beta) = log|I-rho*W| - (n/2)*log(2*pi*sigma^2_hat) - n/2
```

where sigma^2 is re-estimated from the residual e = (I-rho*W)y - X*beta.

### Papers

1. **Ord, J.K. (1975). "Estimation Methods for Models of Spatial Interaction." *JASA* 70(349): 120–126.**
   DOI: 10.1080/01621459.1975.10480272
   **Code connection:** The eigenvalue log-determinant used in `SpatialLagModel.fit()`: `sum(log(abs(1 - rho * eigenvalues)))`. This is exactly what Ord derived. The precomputed eigenvalues are stored via `SpatialWeightsFactory.eigenvalues()` and cached at `data/interim/spatial/eigenvalues_knn.npy`.
   **Key insight:** `log|I-rho*W| = sum_i log(1-rho*lambda_i)` reduces an O(n^3) determinant to O(n) after precomputing W's eigenvalues once. This makes concentrated ML tractable for n up to ~10,000. The O(n^3) eigendecomposition is paid once; each likelihood evaluation thereafter is O(n).
   **Read:** Three pages. 30 minutes. Essential.

2. **Anselin, L. (1988).** [Already listed — Chapter 6 (SAR) and Chapter 7 (ML estimation)]
   **Code connection:** Full likelihood derivation; the concentrated LL formula L*(rho) = log|I-rho*W| - (n/2)*log(sigma^2_hat(rho))
   **Read:** Chapters 6–8. 4 hours.

3. **LeSage, J. and Pace, R.K. (2009). *Introduction to Spatial Econometrics.* CRC Press.**
   ISBN: 978-1-4200-6424-7
   **Code connection:** The definitive reference for every spatial model in Phase 3. Chapter 3 (SAR/SEM), Chapter 5 (SDM), Chapter 6 (direct/indirect/total effects).
   **Key insight:** The SAR model implies that a change in x_i for unit i changes y for ALL units via the feedback loop (I-rho*W)^{-1}. The "total effect" on the system of changing x_i by one unit exceeds the direct "own effect" — the spatial multiplier is (I-rho*W)^{-1}, not the identity.
   **Read:** Chapters 2–3 first (3 hours), then Chapter 6 (4 hours). The most important reference in this section.

---

## 5. Spatial Error Model (SEM)

### What the code does

`SpatialErrorModel.fit()` in `src/spatial_models/sem.py` is structurally identical to the SAR estimator but optimizes over lambda (the error autoregression parameter) rather than rho.

**Concentrated LL for SEM:** Let B = I - lambda*W. The pre-filtered model is By = BX*beta + eps. The code solves for beta via `lstsq(BX, By)` for each candidate lambda, then evaluates:

```python
log_det = sum(log(abs(1 - lam * eigenvalues)))
sigma2 = ||By - BX @ beta_hat||^2 / n
conc_ll = -(log_det - (n/2)*log(sigma2))    # negated for minimization
```

**Same eigenvalue trick as SAR.** The eigenvalues of W are reused for SEM — valid because log|I-lambda*W| = sum_i log(1 - lambda*lambda_i).

**Optimizer:** `minimize_scalar` with `method="bounded"`, same bounds logic as SAR.

**Standard errors:** Numerical Hessian of the full (unconcentrated) log-likelihood in `[lambda, beta_1, ..., beta_k]`, same finite-difference scheme as SAR.

**Additional diagnostic:** `breusch_pagan()` implements a heteroskedasticity test using statsmodels OLS on the squared residuals.

### The math (verified against code)

**Model:**

```
y = X*beta + u,    u = lambda*W*u + eps,    eps ~ N(0, sigma^2 * I)
```

**Reduced form:**

```
y = X*beta + (I - lambda*W)^{-1} * eps
```

**Pre-filtered form (as used in code):**

```
(I - lambda*W)y = (I - lambda*W)X*beta + eps
By = BX*beta + eps      where B = I - lambda*W
```

**Concentrated log-likelihood:**

```
L*(lambda) = log|I - lambda*W| - (n/2) * log(sigma^2_hat(lambda))
```

where:

```
beta_hat(lambda) = (X'B'BX)^{-1} X'B'By    [solved via lstsq(BX, By)]
sigma^2_hat(lambda) = ||By - BX*beta_hat||^2 / n
```

**Log-determinant:** Same eigenvalue trick as SAR:

```
log|I - lambda*W| = sum_i log(1 - lambda*lambda_i)
```

### Papers

1. **Anselin, L. (1988).** [Chapter 7 — SEM ML estimation]
   **Code connection:** `SpatialErrorModel.fit()` in `src/spatial_models/sem.py`
   **Key insight:** SEM corrects for spatial correlation in errors (omitted variables with spatial structure) but does NOT generate spillover effects. If a neighbor's fire proximity affects your price beyond the correlation in unobservables, SEM misses it — that's why SDM is preferred when spillovers are expected.

2. **LeSage, J. and Pace, R.K. (2009).** [Chapter 3 — SEM ML estimation and comparison with SAR]
   **Code connection:** Model selection via AIC/BIC in `src/spatial_models/model_registry.py` — the registry computes AIC and BIC from `log_likelihood_` for all three models (SAR, SEM, SDM) using the same formula `-2*LL + 2*k` and `-2*LL + log(n)*k`.

---

## 6. Spatial Durbin Model (SDM)

### What the code does

`SpatialDurbinModel.fit()` in `src/spatial_models/sdm.py` augments the design matrix with spatially lagged covariates WX, then applies the same concentrated ML machinery as SAR.

**WX construction:** The code detects the intercept column (the constant column where `np.allclose(X[:, c], 1.0)`), excludes it from spatial lagging, and computes `W @ X[:, c]` for every non-intercept column c. The augmented design matrix is `X_aug = [X | WX]`. Attributes `x_names_` and `wx_names_` (prefixed "W_") track the covariate names.

**Concentrated LL:** Identical to SAR but with X_aug replacing X:

```python
A = I_n - rho * W
Ay = A @ y
beta_aug, _, _, _ = lstsq(X_aug, Ay)
sigma2 = ||Ay - X_aug @ beta_aug||^2 / n
conc_ll = -(log_det - (n/2)*log(sigma2))
```

**Parameter split:** After optimization, `beta_ = beta_aug_hat[:k]` (coefficients on original X) and `theta_ = beta_aug_hat[k:]` (coefficients on WX, excluding intercept lag).

**Standard errors:** Numerical Hessian of `[rho, beta_aug_1, ..., beta_aug_{k+k_wx}]`, same scheme as SAR/SEM. The full covariance `_cov_` is stored for use in the SEM common-factor Wald test.

**Nesting tests implemented:**

- `test_sar_restriction(sar_model)`: **LR test** of H0: theta = 0 (SDM vs SAR). `LR = 2*(LL_SDM - LL_SAR)`, df = len(theta_). Uses `scipy.stats.chi2`.
- `test_sem_cf_restriction(sem_model, beta_sem)`: **Wald test** of common-factor restriction H0: theta + rho*beta = 0 (SDM restricts to SEM). The Jacobian matrix J is constructed analytically and the variance of the restriction vector R = theta + rho*beta is computed via the delta method using `_cov_`.

### The math (verified against code)

**Model:**

```
y = rho*Wy + X*beta + W*X*theta + eps
```

where WX excludes the spatial lag of the intercept column.

**Augmented design (as implemented):**

```
X_aug = [X | WX]    (n x (k + k_wx) matrix)
```

The concentrated LL is then identical to SAR with X_aug substituting for X.

**Nesting structure:**

- SDM restricts to SAR when theta = 0. LR test: `LR = 2*(LL_SDM - LL_SAR)`, chi^2(k_wx).
- SDM restricts to SEM when theta + rho*beta = 0 (common-factor restriction). Wald test via delta method, chi^2(k_wx).
- SDM restricts to OLS when rho = 0 AND theta = 0.

**Concentrated log-likelihood:**

```
L*(rho) = log|I-rho*W| - (n/2)*log(sigma^2_hat(rho))
```

where `sigma^2_hat(rho) = ||(I-rho*W)y - X_aug*beta_aug_hat(rho)||^2 / n`.

### Papers

1. **LeSage, J. and Pace, R.K. (2009).** [Chapter 5 — SDM]
   **Code connection:** `SpatialDurbinModel.fit()` in `src/spatial_models/sdm.py`
   **Key insight:** SDM is the "do no harm" spatial model — it nests both SAR and SEM. Use SDM as the baseline; test restrictions to simplify. If neither the common-factor restriction (→ SEM) nor theta = 0 (→ SAR) is rejected, SDM is the preferred model. The spatial multiplier in SDM includes both WX (contemporaneous spillovers in X) and (I-rho*W)^{-1} (feedback in y).

2. **Elhorst, J.P. (2010). "Applied Spatial Econometrics: Raising the Bar." *Spatial Economic Analysis* 5(1): 9–28.**
   DOI: 10.1080/17421770903541772
   **Code connection:** LR nesting tests in `SpatialDurbinModel.test_sar_restriction()` and Wald common-factor test in `test_sem_cf_restriction()`, plus AIC/BIC comparison in `src/spatial_models/model_registry.py`
   **Key insight:** Table 1 of Elhorst (2010) gives the full nesting structure of spatial models. The common-factor restriction theta = -rho*beta implies that the spatial error model is the correct DGP. The LR test of SDM vs. SAR has df = k_wx (one restriction per non-intercept covariate). Read this paper alongside LeSage-Pace Chapter 5.
   **Read:** Sections 1–2. 1 hour.

---

## 7. LeSage-Pace Direct, Indirect, and Total Effects

### What the code does

`LeSagePaceEffects.compute()` in `src/spatial_models/effects.py` computes direct, indirect, and total effects for SDM using the eigenvalue trace approximation. It does NOT form the dense matrix (I-rho*W)^{-1}.

**Eigenvalue acquisition:** The method first checks for `sdm._eigenvalues_` attribute; if absent, calls `_compute_eigs_approx(W)` which uses `spla.eigs` (up to 50 eigenvalues) or dense fallback.

**Point estimates via trace trick:**

```python
denom = 1.0 - rho * eigs
trace_Ainv  = sum(1.0 / denom)              # tr((I-rhoW)^{-1})
trace_WAinv = sum(eigs / denom)             # tr(W @ (I-rhoW)^{-1})
```

**Effects formulas (as implemented, for covariate r with coefficient b_r in X and t_r in WX):**

```python
direct_r   = (b_r * trace_Ainv  + t_r * trace_WAinv) / n
total_r    = (b_r + t_r) * trace_Ainv / n
indirect_r = total_r - direct_r
```

**Standard errors:** Simulation-based (Monte Carlo). The code draws `n_simulations = 1000` parameter vectors from `N(params0, cov_psd)` where `params0 = [rho, beta..., theta...]` and `cov_psd` is the positive-semidefinite projection of `sdm._cov_` (computed by clipping negative eigenvalues of the covariance matrix to 1e-12). For each draw, the trace trick is re-evaluated with the simulated rho and coefficients. SEs are the standard deviation of the simulated effects distribution.

**p-values:** Two-tailed normal approximation: `2 * norm.sf(|effect / se|)` using simulation SEs.

### The math (verified against code)

**Impact matrix for covariate r (SDM):**

```
S_r(W) = (I - rho*W)^{-1} * (beta_r * I + theta_r * W)
```

For SAR (theta_r = 0):

```
S_r(W) = beta_r * (I - rho*W)^{-1}
```

**Direct effect** (average own-parcel response):

```
ADI_r = (1/n) * tr(S_r)
      = (1/n) * [beta_r * tr((I-rho*W)^{-1}) + theta_r * tr(W*(I-rho*W)^{-1})]
```

**Total effect** (average of row sums; as implemented):

```
ATI_r = (1/n) * iota' * S_r * iota
      = (b_r + t_r) * tr((I-rho*W)^{-1}) / n
```

Note: this formula assumes W is row-stochastic (row sums = 1), so iota'*W*(I-rho*W)^{-1}*iota = iota'*(I-rho*W)^{-1}*iota = tr((I-rho*W)^{-1}).

**Indirect/spillover effect:**

```
AII_r = ATI_r - ADI_r
      = (1/n) * [t_r * tr((I-rho*W)^{-1}) - t_r * tr(W*(I-rho*W)^{-1})]
```

**Eigenvalue trace approximation** (exact for symmetric W; used here for row-standardized W which is generally asymmetric):

```
tr((I-rho*W)^{-1})     = sum_i 1/(1 - rho*lambda_i)
tr(W*(I-rho*W)^{-1})   = sum_i lambda_i/(1 - rho*lambda_i)
```

**SE computation:** Monte Carlo simulation. Draw theta_sim ~ N(theta_hat, Sigma_hat), recompute trace quantities, accumulate distribution of direct/indirect/total. SE = std of simulated distribution. This is the approach in LeSage and Pace (2009) Section 6.2.

### Papers

1. **LeSage, J. and Pace, R.K. (2009).** [Chapter 6 — direct/indirect/total effects, equations (6.14)–(6.22)]
   **Code connection:** `LeSagePaceEffects.compute()` in `src/spatial_models/effects.py`. The eigenvalue trace trick for ADI and ATI is their Equation (6.19). The Monte Carlo simulation for SEs is their Algorithm 6.1.
   **Key insight:** In SAR/SDM, OLS coefficients beta are NOT the marginal effects of X on y. The correct effects are the row (or column) averages of S_r(W). The indirect effect can exceed the direct effect when rho is large — this is the "spatial multiplier" phenomenon. For housing markets, a fire risk discount at one parcel reduces prices of all neighbors.
   **Read:** Chapter 6 entirely. Budget 4 hours.

2. **LeSage, J. and Pace, R.K. (2014). "The Biggest Myth in Spatial Econometrics." *Econometrics* 2(4): 217–249.**
   DOI: 10.3390/econometrics2040217
   **Code connection:** Justification for computing indirect effects rather than reporting beta directly from the coefficient table
   **Key insight:** The "biggest myth" is that spatial models are just about correcting nuisance autocorrelation. In fact, the spatial parameter rho determines the magnitude of spillovers — ignoring indirect effects systematically understates the aggregate impact of any intervention.
   **Read:** Sections 1–3. 2 hours.

---

## 8. Geographically Weighted Regression (GWR)

### What the code does

**Kernel:** Both bisquare and Gaussian are implemented in `GeographicallyWeightedRegression._kernel_weights()`. The default in `BandwidthSelector.__init__()` is `kernel="bisquare"`.

**Bandwidth type:** Fixed (not adaptive). The bandwidth is a single scalar `bandwidth_km` converted to metres. Every observation uses the same bandwidth regardless of local data density.

**Core fit loop** (`_fit_internal()`): For each observation i, compute the kernel weight vector `w_i` (shape n) from the precomputed distance matrix row `dists[i]`. Build `W_diag = diag(w_i)` and solve local WLS:

```python
XtW = X.T @ W_diag
XtWX = XtW @ X
XtWy = XtW @ y
XtWX_inv = inv(XtWX + eye(k)*1e-10)   # ridge for numerical stability
beta_i = XtWX_inv @ XtWy
```

The ridge term `1e-10 * I` is added for numerical stability. Local SE uses the locally weighted residual variance:

```python
sigma2_i = sum(w_i * (y - X @ beta_i)^2) / max(sum(w_i) - k, 1)
se_i = sqrt(sigma2_i * diag(XtWX_inv))
```

**AICc computation** (from Fotheringham et al. 2002, eq. 2.33, as implemented):

```python
sigma2_hat = mean((y - y_hat)^2)
tr_H = sum(hat_diag)                       # effective_df_ = sum of h_ii
denom_aicc = n - 2 - tr_H
aicc = 2*n*log(sigma2_hat) + n*log(2*pi) + n*(n + tr_H) / denom_aicc
```

The hat diagonal is `h_ii = x_i' * (X'W(i)X)^{-1} * x_i`.

**Bandwidth selection** (`BandwidthSelector.golden_section_search()`): Golden-section search on the interval `[lower_km, upper_km]` with default `[1.0, 50.0]` km and tolerance `tol=1.0` km. The golden ratio conjugate `phi = (sqrt(5)-1)/2 ≈ 0.618` is precomputed as `_PHI`. At each iteration: `d = phi * (upper - lower)`, probe points `x1 = upper - d` and `x2 = lower + d`, evaluate AICc at both, shrink the bracket. Checkpoints (lower, upper, evaluations list) are saved to `data/interim/spatial/bw_checkpoint.pkl` every 5 iterations and on completion.

**Output:** `local_params_` is an (n, k) array of local beta estimates — one coefficient vector per parcel. These are exported to the GeoDataFrame by `to_geodataframe()` as columns `beta_{name}` and `t_{name}`.

### The math (verified against code)

**Local WLS at location i:**

```
beta_hat(u_i, v_i) = (X' W(i) X + 1e-10*I)^{-1} X' W(i) y
```

where `W(i) = diag(K(d_ij / bandwidth_m))` and d_ij is the distance from parcel i to parcel j.

**Bisquare kernel** (as implemented):

```
K(u) = (1 - u^2)^2   for |u| < 1
     = 0              otherwise
```

where u = d_ij / bandwidth_m.

**Gaussian kernel** (as implemented):

```
K(u) = exp(-0.5 * u^2)
```

where u = d_ij / bandwidth_m.

**AICc for bandwidth selection** (Fotheringham et al. 2002, eq. 2.33):

```
AICc(h) = 2n * ln(sigma_hat) + n*ln(2*pi) + n*(n + tr(H)) / (n - 2 - tr(H))
```

where sigma_hat^2 = mean(y - y_hat)^2 and tr(H) = sum_i h_ii = sum_i x_i'(X'W(i)X)^{-1}x_i.

Note: the code uses `log(sigma^2_hat)` (variance, not SD) in the first term:

```python
2.0 * n * np.log(sigma2_hat)   # = 2n * log(sigma^2) = 4n * log(sigma)
```

This is a factor-of-2 scaling difference from the Fotheringham et al. formula which uses `ln(sigma_hat)`. The AICc values are therefore not directly comparable to published implementations, but the minimum is at the same bandwidth since the scaling is constant across h.

**Golden-section search:**

```
d = phi * (upper - lower)     where phi = (sqrt(5)-1)/2 ≈ 0.618
x1 = upper - d
x2 = lower + d
if AICc(x1) < AICc(x2): upper = x2
else:                     lower = x1
```

Converges when `(upper - lower) <= tol = 1.0` km. The optimal bandwidth is `(lower + upper) / 2`.

### Papers

1. **Brunsdon, C., Fotheringham, A.S., Charlton, M. (1996). "Geographically Weighted Regression: A Method for Exploring Spatial Nonstationarity." *Geographical Analysis* 28(4): 281–298.**
   DOI: 10.1111/j.1538-4632.1996.tb00936.x
   **Code connection:** The foundational GWR paper — defines local WLS as implemented in `GeographicallyWeightedRegression._fit_internal()`
   **Key insight:** GWR reveals when coefficients are spatially non-stationary — the test is whether local beta_hat_i vary significantly more than expected under global beta. The key diagnostic is the ratio of GWR to OLS residual sum of squares.
   **Read:** Entire paper. 1.5 hours.

2. **Fotheringham, A.S., Brunsdon, C., Charlton, M. (2002). *Geographically Weighted Regression: The Analysis of Spatially Varying Relationships.* Wiley.**
   ISBN: 978-0-471-49616-8
   **Code connection:** AICc formula in `GeographicallyWeightedRegression._fit_internal()` (lines 91–95) and golden-section algorithm in `BandwidthSelector.golden_section_search()`. Note the factor-of-2 scaling in the AICc formula described above.
   **Key insight:** The AICc bandwidth selector is preferred over CV because it accounts for the effective degrees of freedom tr(H) — a smaller bandwidth increases tr(H), penalizing overfitting. The golden-section search is used because AICc(h) is unimodal — it has one minimum.
   **Read:** Chapters 1–3. 4 hours.

3. **Wheeler, D. and Tiefelsdorf, M. (2005). "Multicollinearity and Correlation among Local Regression Coefficients in Geographically Weighted Regression." *Journal of Geographical Systems* 7(2): 161–187.**
   DOI: 10.1007/s10109-005-0155-z
   **Code connection:** Limitation to disclose when interpreting `local_params_` variation across parcels
   **Key insight:** Local GWR coefficients can appear spatially non-stationary even when the true DGP has constant coefficients — purely due to collinearity between local estimates. Any apparent spatial variation in the estimated betas should be interpreted cautiously; the variation may reflect this artifact rather than true geographic heterogeneity in the fire-discount effect.
   **Read:** Sections 1–3. 1.5 hours.

4. **Fotheringham, A.S., Yang, W., Kang, W. (2017). "Multiscale Geographically Weighted Regression (MGWR)." *Annals of the American Association of Geographers* 107(6): 1247–1265.**
   DOI: 10.1080/24694452.2017.1352480
   **Key insight:** MGWR allows different bandwidths for different covariates — the distance-to-fire effect may operate at a finer scale than the structural (sqft, bedrooms) effects. If the GWR bandwidth optimized by AICc remains large (suggesting spatial stationarity in the data), MGWR is the appropriate next model to investigate.
   **Read:** Sections 1–3. 2 hours.

---

## Reading Priority

For a researcher new to this codebase, read in this order:

1. Anselin (1988) Chapters 2, 6, 7 — foundations for weights, SAR, SEM
2. LeSage & Pace (2009) Chapters 2–3, 5–6 — the implementation reference for SDM and effects
3. Ord (1975) — 3 pages, essential for understanding why eigenvalues appear everywhere
4. Anselin (1995) LISA — this paper IS the `LocalMoransI` implementation
5. Fotheringham et al. (2002) Chapters 1–3 — GWR AICc and bandwidth selection
6. LeSage & Pace (2014) — motivation for reporting indirect effects, not just beta
7. Elhorst (2010) — nesting tests reference table
8. Wheeler & Tiefelsdorf (2005) — read before reporting any GWR coefficient surface
