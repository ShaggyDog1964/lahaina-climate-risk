# Complete Reading List — Lahaina Climate-Risk Project
## Purpose: everything you must read to understand what the code is doing and why
## Total papers/books: 35
## Estimated reading time: 9 weeks at 2 items/day (selective reading of assigned sections only)

---

## HOW TO USE THIS LIST

Read in the order given within each tier. Tier 1 is a prerequisite for everything else.
For each item, the entry states:
- **Code connection** — exact function or file in the codebase
- **Key insight** — the single most important thing to extract
- **Read** — specific sections and estimated time (not the full paper unless noted)
- **Find it** — DOI or stable URL

Do not skip to advanced papers before finishing your tier. The math in Tier 2 will not
make sense without the intuition from Tier 1.

---

## TIER 1 — Foundations (read these first, ~2 weeks)
### These five give you the conceptual foundation for everything else.

**1. Angrist, J. and Pischke, J.S. (2009). *Mostly Harmless Econometrics.* Princeton UP.**
ISBN: 978-0-691-12034-8
**Code connection:** Conceptual grounding for all of Phase 1 (hedonic, DiD, parallel trends)
**Key insight:** The fundamental challenge of causal inference is the missing counterfactual. Regression, DiD, and IV are all strategies for constructing a credible counterfactual. Parallel trends is the specific assumption DiD makes.
**Read:** Chapter 2 (regression anatomy), Chapter 5 §5.1–5.3 (DiD and parallel trends). 6 hours total.

---

**2. Rosen, S. (1974). "Hedonic Prices and Implicit Markets." *Journal of Political Economy* 82(1): 34–55.**
DOI: 10.1086/260169
**Code connection:** `HedonicModel.fit()` in `src/models/hedonic.py`
**Key insight:** In competitive equilibrium, the marginal implicit price of any attribute equals the buyer's marginal willingness to pay. The hedonic regression identifies the market-clearing price gradient — not structural demand — which is why we can use it to estimate the fire-proximity price impact without a structural model.
**Read:** Sections I–III (theory), Section IV (the regression). 2 hours.

---

**3. Goodman-Bacon, A. (2021). "Difference-in-Differences with Variation in Treatment Timing." *Journal of Econometrics* 225(2): 254–277.**
DOI: 10.1016/j.jeconom.2021.03.014
**Code connection:** Justification for NOT using TWFE (`linearmodels.PanelOLS`); why `did_cs.py` uses C&S instead
**Key insight:** β_TWFE = weighted average of all pairwise 2×2 DiDs, where some weights are NEGATIVE. Already-treated units act as controls for later-treated units. With heterogeneous treatment effects (which fire-proximity effects surely are), TWFE is biased and can have the wrong sign.
**Read:** Section 2 (Theorem 1 — the decomposition). 2 hours. Read this BEFORE Callaway-Sant'Anna.

---

**4. Abadie, A., Diamond, A., Hainmueller, J. (2015). "Comparative Politics and the Synthetic Control Method." *AJPS* 59(2): 495–510.**
DOI: 10.1111/ajps.12116
**Code connection:** Intuition behind `ADHSyntheticControl` in `src/scm/adh_scm.py`
**Key insight:** The synthetic control "speaks for itself" — a well-fitting pre-period trajectory is more convincing than a significance test. Read this short, accessible paper BEFORE the 2010 JASA paper.
**Read:** Entire paper. 1 hour.

---

**5. Moran, P.A.P. (1950). "Notes on Continuous Stochastic Phenomena." *Biometrika* 37(1/2): 17–23.**
DOI: 10.2307/2332142
**Code connection:** `GlobalMoransI.compute()` in `src/esda/morans.py`
**Key insight:** Spatial autocorrelation is analogous to Pearson's r — it measures whether neighbors are more similar than expected by chance. E[I] = −1/(n−1) under spatial randomness; values above zero indicate clustering.
**Read:** The entire 7-page paper. 45 minutes.

---

## TIER 2 — Core methodology (~3 weeks)
### The papers the main estimators implement directly. Derive the code equations from these.

**6. Callaway, B. and Sant'Anna, P. (2021). "Difference-in-Differences with Multiple Time Periods." *Journal of Econometrics* 225(2): 200–230.**
DOI: 10.1016/j.jeconom.2020.12.001
**Code connection:** Direct implementation in `src/models/did_cs.py`. This IS the estimator.
**Key insight:** ATT(g,t) = E[Y_t(g) − Y_t(0) | G = g] where G = g means "first treated at time g." The doubly-robust estimator with `control_group="notyettreated"` is consistent if either the propensity score OR the outcome regression model is correctly specified.
**Read:** Sections 2–4 (ATT definition, DR estimator, aggregation). 4 hours.
**Math to derive:** Equations (2.1)–(2.4) for ATT(g,t); Equations (4.1)–(4.3) for aggregation to event study and simple average.
**Implementation note:** `src/models/did_cs.py` uses `est_method="dr"` and `control_group="notyettreated"` (verified in source).

---

**7. Abadie, A., Diamond, A., Hainmueller, J. (2010). "Synthetic Control Methods for Comparative Case Studies." *JASA* 105(490): 493–505.**
DOI: 10.1198/jasa.2009.ap08746
**Code connection:** Equations (1)–(4) implemented in `ADHSyntheticControl._inner_qp()` and `._outer_mspe()`
**Key insight:** Two-level optimization: inner QP finds w* given V; outer L-BFGS-B finds V* by minimizing pre-period outcome RMSPE. The outer objective uses `Y₀_pre/Y₁_pre` (outcome series), not covariate fit (verified in source).
**Read:** Equations (1)–(4), Section 4 (permutation inference). 3 hours.

---

**8. Anselin, L. (1988). *Spatial Econometrics: Methods and Models.* Kluwer Academic.**
ISBN: 978-90-247-3735-2
**Code connection:** Foundational reference for `SpatialWeightsFactory`, `SpatialLagModel`, `SpatialErrorModel`
**Key insight:** The choice of spatial weights W is the "first, crucial decision in spatial econometrics." Row-standardization makes Wy a local average of neighbors. The ML concentrated likelihood for SAR isolates ρ as the sole optimization variable.
**Read:** Chapter 2 (weights, 2 hours), Chapters 6–8 (SAR/SEM ML estimation, 4 hours). 6 hours total.

---

**9. LeSage, J. and Pace, R.K. (2009). *Introduction to Spatial Econometrics.* CRC Press.**
ISBN: 978-1-4200-6424-7
**Code connection:** Primary reference for `SpatialLagModel`, `SpatialErrorModel`, `SpatialDurbinModel`, and `LeSagePaceEffects`
**Key insight:** In SAR/SDM, OLS coefficients β are NOT the marginal effects of X on y. The correct effects are averages of the impact matrix S_r = (I−ρW)⁻¹(β_r I + θ_r W). The indirect (spillover) effect can exceed the direct effect when ρ is large.
**Read:** Chapter 2 (weights), Chapter 3 (SAR/SEM), Chapter 5 (SDM), Chapter 6 (effects equations 6.14–6.22). 10 hours. This is the most important reference for Phase 3.

---

**10. Anselin, L. (1995). "Local Indicators of Spatial Association—LISA." *Geographical Analysis* 27(2): 93–115.**
DOI: 10.1111/j.1538-4632.1995.tb00338.x
**Code connection:** Equations (1)–(6) in `LocalMoransI.compute()` in `src/esda/lisa.py`
**Key insight:** LISA decomposes global Moran's I into local contributions: I = Σᵢ Iᵢ/(n−1) where Iᵢ = zᵢ(Wz)ᵢ. Quadrant classification (HH/LL/HL/LH) uses the sign of zᵢ and (Wz)ᵢ. Pseudo p-values use permutation.
**Read:** Sections 2–3. 2 hours.
**Implementation note:** `src/esda/lisa.py` uses a GLOBAL shuffle for permutation, not Anselin's recommended conditional permutation with zᵢ held fixed. This is a conservative approximation — document when reporting.

---

**11. Ord, J.K. (1975). "Estimation Methods for Models of Spatial Interaction." *JASA* 70(349): 120–126.**
DOI: 10.1080/01621459.1975.10480272
**Code connection:** The eigenvalue log-determinant trick in `SpatialLagModel.fit()`, `SpatialErrorModel.fit()`, `SpatialDurbinModel.fit()`
**Key insight:** log|I−ρW| = Σᵢ log(1−ρλᵢ) where λᵢ are eigenvalues of W, precomputed once. This reduces an O(n³) determinant to O(n) per likelihood evaluation. Without this trick, spatial ML is infeasible for n > 500.
**Read:** Three pages. 30 minutes. Essential.

---

**12. Fotheringham, A.S., Brunsdon, C., Charlton, M. (2002). *Geographically Weighted Regression.* Wiley.**
ISBN: 978-0-471-49616-8
**Code connection:** AICc formula in `BandwidthSelector._aic_c()` and golden-section algorithm in `BandwidthSelector.golden_section_search()`
**Key insight:** AICc(h) = 2n ln(σ̂²) + n ln(2π) + n(n + tr(H)) / (n − 2 − tr(H)) where tr(H) is the sum of local hat values. NOTE: `src/gwr/bandwidth.py` uses `log(σ̂²)` which differs from the published formula by a factor of 2 — document this divergence. Golden-section works because AICc(h) is unimodal in h.
**Read:** Chapters 1–3. 4 hours.

---

**13. Abadie, A. (2021). "Using Synthetic Controls: Feasibility, Data Requirements, and Methodological Aspects." *JEL* 59(2): 391–425.**
DOI: 10.1257/jel.20191450
**Code connection:** Complete design reference for all SCM implementation choices
**Key insight:** SCM requires (a) many pre-treatment periods (T₀ ≥ 15 recommended), (b) convex hull condition (treated unit's outcomes lie in span of donors), (c) no interference between units. With 58 Hawaii ZIPs and T₀ < 24 months, this project is at the boundary of feasibility.
**Read:** Sections I–V. 4 hours. The definitive reference.

---

## TIER 3 — Extensions and robustness (~2 weeks)
### Papers behind extended estimators, robustness checks, and inference procedures.

**14. de Chaisemartin, C. and D'Haultfœuille, X. (2020). "Two-Way Fixed Effects Estimators with Heterogeneous Treatment Effects." *AER* 110(9): 2964–2996.**
DOI: 10.1257/aer.20181169
**Code connection:** Further justification for C&S over TWFE; robustness check if TWFE is reported
**Key insight:** Alternative proof of TWFE bias via "contamination bias" formula. Complements Goodman-Bacon.
**Read:** Sections I–II. 1.5 hours.

---

**15. Sun, L. and Abraham, S. (2021). "Estimating Dynamic Treatment Effects in Event Studies with Heterogeneous Treatment Effects." *Journal of Econometrics* 225(2): 175–199.**
DOI: 10.1016/j.jeconom.2020.09.006
**Code connection:** Alternative estimator referenced in robustness checks
**Key insight:** The interaction-weighted (IW) estimator is numerically equivalent to C&S under the same assumptions but implementable via saturated OLS.
**Read:** Sections 2–3. 2 hours.

---

**16. Roth, J., Sant'Anna, P., Bilinski, A., Poe, J. (2023). "What's Trending in Difference-in-Differences?" *Journal of Econometrics* 235(2): 2218–2244.**
DOI: 10.1016/j.jeconom.2023.03.008
**Code connection:** Survey paper — the map of the modern DiD field
**Key insight:** Under the same parallel trends assumption, all modern DiD estimators (C&S, Sun-Abraham, Borusyak et al.) converge. Differences arise only when assumptions differ.
**Read:** Entire paper — it is a survey. 2 hours.

---

**17. Xu, Y. (2017). "Generalized Synthetic Control Method." *Political Analysis* 25(1): 57–76.**
DOI: 10.1017/pan.2016.2
**Code connection:** `GeneralizedSyntheticControl.fit()` in `src/scm/gsynth.py`
**Key insight:** IFE model Y_it = δ_it D_it + λᵢ'Fₜ + ε_it estimated by alternating LS over r latent factors. Does NOT require convex hull condition. The EM alternates between estimating Fₜ from control units and λᵢ for all units.
**Read:** Sections 2–3. 2 hours.

---

**18. Ben-Michael, E., Feller, A., Rothstein, J. (2021). "The Augmented Synthetic Control Method." *JASA* 116(536): 1789–1803.**
DOI: 10.1080/01621459.2021.1929245
**Code connection:** `AugmentedSyntheticControl.fit()` in `src/scm/augsynth.py`
**Key insight:** When pre-RMSPE > 0.02, ADH gap is biased. Ridge augmentation corrects: τ̂_t^ASCM = (Y₁ₜ − Y₀ₜ'w*) − (m̂₁ₜ − m̂₀ₜ'w*). Implementation note: ridge is fit per time step with LOOCV λ grid [0.01, 0.1, 1, 10, 100, 1000] (verified in source).
**Read:** Sections 1–3. 3 hours.

---

**19. Ferman, B. and Pinto, C. (2021). "Synthetic Controls with Imperfect Pretreatment Fit." *Quantitative Economics* 12(4): 1197–1221.**
DOI: 10.3982/QE1596
**Code connection:** Explains why Hawaii setting (58 donors, short pre-period) limits inference reliability
**Key insight:** Pre-period RMSPE is not a sufficient statistic for SCM quality. With J < 20 donors and T₀ < 20, the permutation distribution has low power and inference is unreliable.
**Read:** Section 2. 1.5 hours.

---

**20. Cliff, A. and Ord, J.K. (1981). *Spatial Processes: Models and Applications.* Pion Limited.**
ISBN: 0-85086-085-6
**Code connection:** Kurtosis-corrected analytical variance in `GlobalMoransI.compute()`. NOTE: the code uses the randomization variance with B = mean(z⁴)/mean(z²)² kurtosis correction (verified in source) — cite this book for the formula.
**Key insight:** Under the randomization assumption, Var[I] involves the 4th moment of the data (B factor), not just second moments as in the normality version. The randomization form is more robust when data is non-normal.
**Read:** Chapter 1 and Chapter 2 (moments, pp. 42–46). 3 hours.

---

**21. Elhorst, J.P. (2010). "Applied Spatial Econometrics: Raising the Bar." *Spatial Economic Analysis* 5(1): 9–28.**
DOI: 10.1080/17421770903541772
**Code connection:** LR nesting tests in `SpatialDurbinModel.fit()` and `src/spatial_models/model_registry.py`
**Key insight:** Table 1 maps the full nesting structure of spatial models. Common-factor restriction θ + ρβ = 0 implies SEM is the DGP; if rejected, use SDM. SDM's LR test vs. SAR has df = k (one restriction per covariate).
**Read:** Sections 1–2. 1 hour.

---

**22. LeSage, J. and Pace, R.K. (2014). "The Biggest Myth in Spatial Econometrics." *Econometrics* 2(4): 217–249.**
DOI: 10.3390/econometrics2040217
**Code connection:** Justification for `LeSagePaceEffects.compute()` — why β is not the marginal effect
**Key insight:** Ignoring indirect effects systematically understates the aggregate impact of any intervention. The spatial multiplier means aggregate effects exceed parcel-level effects by a factor of 1/(1−ρ) in the simplest case.
**Read:** Sections 1–3. 2 hours.

---

**23. Brunsdon, C., Fotheringham, A.S., Charlton, M. (1996). "Geographically Weighted Regression: A Method for Exploring Spatial Nonstationarity." *Geographical Analysis* 28(4): 281–298.**
DOI: 10.1111/j.1538-4632.1996.tb00936.x
**Code connection:** `GeographicallyWeightedRegression.fit()` in `src/gwr/gwr_model.py`
**Key insight:** The original GWR paper. β̂(uᵢ,vᵢ) = (X'W(i)X)⁻¹X'W(i)y where W(i) = diag(K(dᵢⱼ/h)). The bisquare kernel K(u) = (1−u²)² for |u| < 1 has compact support — a computational advantage over Gaussian.
**Read:** Entire paper. 1.5 hours.

---

**24. Wheeler, D. and Tiefelsdorf, M. (2005). "Multicollinearity and Correlation among Local Regression Coefficients in Geographically Weighted Regression." *Journal of Geographical Systems* 7(2): 161–187.**
DOI: 10.1007/s10109-005-0155-z
**Code connection:** Caveat to include when reporting GWR results
**Key insight:** Local GWR coefficients can appear spatially non-stationary even when the true DGP has constant coefficients — purely due to multicollinearity between local estimates. The current 0.034% variation in local betas (on current synthetic data) is consistent with this artifact.
**Read:** Sections 1–3. 1.5 hours.

---

## TIER 4 — Empirical context (~1 week)
### Comparable papers. Read to calibrate your results and situate the contribution.

**25. Bernstein, A., Gustafson, M., Lewis, R. (2019). "Disaster on the Horizon: The Price Effect of Sea Level Rise." *JFE* 134(2): 253–272.**
DOI: 10.1016/j.jfineco.2019.03.013
**Already in references.bib as `Bernstein2019`**
**Key result:** 7% discount for sea-level-exposed properties. Discount has grown since 2013.
**Comparison:** Your ATT for 0–2 km parcels should exceed 7% (wildfire destroys structures; sea level rise is gradual). If ATT < 7%, the result is surprising and needs explanation.

---

**26. Baldauf, M., Garlappi, L., Yannelis, C. (2020). "Does Climate Change Affect Real Estate Prices? Only If You Believe In It." *RFS* 33(3): 1256–1295.**
DOI: 10.1093/rfs/hhz073
**Already in references.bib as `Baldauf2020`**
**Key result:** Flood-zone discount is 7–11% in high-belief counties, near zero in low-belief counties.
**Comparison:** Hawaii is a high-belief state → your belief-update channel (β₁ − β₂) should be on the larger end of the range. If β₁ − β₂ < 5%, the belief-update channel is weak despite high baseline climate awareness.

---

**27. Coffman, M. and Noy, I. (2012). "Hurricane Iniki: Measuring the Long-Term Economic Impact of a Natural Disaster Using Synthetic Control." *Environment and Development Economics* 17(2): 187–205.**
DOI: 10.1017/S1355770X11000350
**Key result:** Hurricane Iniki reduced Kauai County GDP by ~18% permanently. Pre-period RMSPE < 0.01.
**Comparison:** Most comparable paper — Hawaii natural disaster + synthetic control. Their pre-period RMSPE (< 0.01) vs. this project's 0.0154. Their donor pool is Hawaii counties; this project uses ZIPs.

---

**28. Hallstrom, D. and Smith, V.K. (2005). "Market Responses to Hurricanes." *JEEM* 50(3): 541–561.**
DOI: 10.1016/j.jeem.2005.02.002
**Key result:** Near-miss hurricane (no physical damage) reduced property prices 6–10% — purely a risk perception update.
**Comparison:** Your WUI triple-difference coefficient β₁ − β₂ is the "pure belief update" estimate. Compare to Hallstrom-Smith's 6–10%.

---

**29. Bakkensen, L. and Barrage, L. (2022). "Going Underwater? Flood Risk Belief Heterogeneity and Implications for Housing Markets, Surveys, and Optimal Policy." *JPE* 130(5): 1290–1357.**
DOI: 10.1086/718982
**Key result:** Buyers with accurate flood risk beliefs impose 8–10% discounts; those with underestimated risk impose near-zero discounts.
**Comparison:** The project's belief-update channel (β₁ − β₂) tests whether Hawaii WUI buyers impose a forward-looking risk discount. Expected positive and significant.

---

**30. Bin, O. and Polasky, S. (2004). "Effects of Flood Hazards on Property Values: Evidence before and after Hurricane Floyd." *Land Economics* 80(4): 490–500.**
DOI: 10.3368/le.80.4.490
**Key result:** Flood zone discount increased from 5% pre-hurricane to 8% post-hurricane — the belief update.
**Comparison:** Early pre-post hedonic study documenting belief updating from a natural disaster. Your design is the DiD generalization of this approach.

---

**31. Giglio, S. et al. (2021). "Climate Change and Long-Run Discount Rates: Evidence from Real Estate." *RFS* 34(8): 3527–3571.**
DOI: 10.1093/rfs/hhab032
**Key result:** Climate-exposed properties have higher long-run discount rates — investors demand higher expected returns.
**Comparison:** Your price discount can be interpreted as a higher discount rate applied to fire-risk parcels. The level shift in rates is the capitalized belief-update.

---

**32. Kousky, C. (2010). "Learning from Extreme Events: Risk Perceptions After the Flood." *Land Economics* 86(3): 395–422.**
DOI: 10.3368/le.86.3.395
**Note:** references.bib has a `Kousky2018` entry that cites a different paper (NFIP financing). The "Learning from Extreme Events" paper is from 2010. Verify and fix the bib entry.
**Key result:** Flood zone discounts are highest 1–2 years post-disaster and decay over 5–7 years ("fading salience" effect).
**Comparison:** Redfin data covers April 2024–September 2025 (1–2 years post-fire). If the Lahaina discount is large in this window and later data shows decay, this is consistent with Kousky's fading salience mechanism.

---

## TIER 5 — Theory (optional but valuable, ~2 weeks)
### Economic theory motivating why this is interesting and what the expected magnitudes should be.

**33. Barro, R. (2006). "Rare Disasters and Asset Markets in the Twentieth Century." *QJE* 121(3): 823–866.**
DOI: 10.1162/qjec.2006.121.3.823
**Connection:** Theoretical foundation for the wildfire risk premium. E[premium] ≈ p × E[(1−b)^{−γ} − 1]. Even p = 0.017 with γ = 3.5 generates a large premium. Motivates why the Lahaina fire (which raised perceived p) causes a persistent price discount.
**Read:** Sections I–III. 3 hours.

---

**34. Weitzman, M. (2009). "On Modeling and Interpreting the Economics of Catastrophic Climate Change." *Review of Economics and Statistics* 91(1): 1–19.**
DOI: 10.1162/rest.91.1.1
**Connection:** With thick-tailed climate risks, standard expected utility gives infinite risk aversion — markets may impose very large discounts on properties with non-trivial wildfire exposure, even far from the perimeter.
**Read:** Sections I–III. 2 hours.

---

**35. Fotheringham, A.S., Yang, W., Kang, W. (2017). "Multiscale Geographically Weighted Regression (MGWR)." *AAAG* 107(6): 1247–1265.**
DOI: 10.1080/24694452.2017.1352480
**Code connection:** Optional extension if GWR bandwidth remains too large on real data
**Key insight:** MGWR allows different bandwidths for different covariates — the fire-distance effect may operate at a finer scale (2–5 km) than structural attribute effects (county-wide). If standard GWR produces a too-large bandwidth, MGWR is the next step.
**Read:** Sections 1–3. 2 hours.

---

## THE MATH BEHIND EACH MODEL

### Hedonic regression

```
Estimating equation:
  log P_it = α + β X_it + Σ_b γ_b Block_b + Σ_t τ_t YearMonth_t + ε_it

Implementation: OLS with C() patsy dummy variables for block and year-month FE
(NOT within-transformation — explicit dummies retained in the design matrix)

HC3 standard errors:
  V̂(β̂) = (X'X)⁻¹ Σ_i [ê_i²/(1-h_ii)²] x_i x_i' (X'X)⁻¹
  where h_ii is the diagonal of the hat matrix H = X(X'X)⁻¹X'
  HC3 inflates high-leverage observations more than HC1 — better finite-sample coverage
```

### Callaway-Sant'Anna DiD

```
ATT(g,t) = E[Y_t(g) − Y_t(0) | G = g]
where G = g is first-treatment cohort, Y_t(0) is counterfactual outcome.

Doubly-robust estimator (est_method="dr", control_group="notyettreated"):
  ATT_DR(g,t) = E[ (Y_t − Y_{g-1})(G_g/P(G_g))
                 − (Y_t − Y_{g-1})(1−D_t) p̂(G_g|X)/(P̂(C|X) × p̂(G=C)) ]

Aggregation to event study:
  θ^es(ℓ) = Σ_g ATT(g, g+ℓ) × P(G = g | G+ℓ ≤ T) / Σ_g P(G = g | G+ℓ ≤ T)

agg_dynamic groups by calendar time with equal weight (not cohort-size-weighted).
```

### Triple-difference decomposition

```
log P_it = α + β₁(Post_t × Treated_i × WUI_i)  [triple interaction]
         + β₂(Post_t × Treated_i)               [double interaction]
         + β₃(Post_t × WUI_i)                   [WUI-post interaction]
         + β₄ WUI_i + γ_b + τ_t + ε_it

Belief-update channel: β_wui − β_nowui (from decompose())
SE of channel: sqrt(se_wui² + se_nowui²)

Estimated by PanelOLS with clustered standard errors (cluster_entity=True)
NOT HC3 — clustering is at the parcel level.
```

### ADH synthetic control

```
Inner QP (cvxpy):
  w* = argmin_w (X₁ − X₀w)'V(X₁ − X₀w)  s.t.  w ≥ 0, Σw = 1

Outer loop (L-BFGS-B over v_diag):
  V* = argmin_v ||Y₁_pre − Y₀_pre w*(v)||²  [OUTCOME RMSPE, not covariate fit]
  v_diag normalized: v* ← |v*| / ||v*||₁

Post-period gap: α̂_t = Y₁_t − Y₀_t' w*  for t > T₀

Permutation p-value (inclusive):
  p = Σ_j 𝟏[rmspe_ratio_j ≥ rmspe_ratio_treated] / J   [one-sided, inclusive]
```

### SAR concentrated log-likelihood

```
Model: y = ρWy + Xβ + ε,  ε ~ N(0, σ²I)

For fixed ρ:
  β̂(ρ) = (X'X)⁻¹ X'(I−ρW)y
  σ̂²(ρ) = ||(I−ρW)y − Xβ̂(ρ)||² / n

Concentrated log-likelihood:
  L*(ρ) = log|I−ρW| − n/2 log(σ̂²(ρ))

Log-determinant (Ord 1975):
  log|I−ρW| = Σᵢ log(1 − ρλᵢ)   [eigenvalues λᵢ precomputed, saved to .npy]

Optimizer: minimize_scalar(method="bounded")  bounds = (1/λ_min, 1/λ_max)
Standard errors: numerical Hessian via centered finite differences (eps=1e-5)
```

### LeSage-Pace direct/indirect/total effects

```
Impact matrix for covariate r (SDM):
  S_r(W) = (I−ρW)⁻¹(β_r I + θ_r W)

Direct effect (average diagonal):    ADI_r = (1/n) tr(S_r)
Total effect (average row sum):       ATI_r = (1/n) ι'S_r ι
Indirect/spillover effect:            AII_r = ATI_r − ADI_r

Eigenvalue trace approximation (NEVER forms dense (I−ρW)⁻¹):
  tr(S_r) ≈ β_r Σᵢ 1/(1−ρλᵢ) + θ_r Σᵢ λᵢ/(1−ρλᵢ)

SE computation: Monte Carlo simulation — draw 1000 samples from N(θ̂, Σ̂),
compute S_r for each draw, take standard deviation of resulting ADI/AII/ATI.
(Known issue: SEs are degenerate at ~4×10⁻⁷ on current 122-observation dataset)
```

### GWR local WLS

```
For parcel i at location (uᵢ, vᵢ):
  β̂(uᵢ,vᵢ) = (X'W_iX)⁻¹ X'W_iy
  W_i = diag(K(dᵢⱼ/h))   where dᵢⱼ = geodesic distance i→j

Bisquare kernel (default): K(u) = (1−u²)²   for |u| < 1,  else 0
Gaussian kernel:            K(u) = exp(−u²/2)

Bandwidth selection by AICc (golden-section over [1, 50] km, tolerance 1 km):
  AICc(h) = 2n log(σ̂²) + n log(2π) + n(n+tr(H)) / (n−2−tr(H))
  [Note: code uses log(σ̂²) — differs from Fotheringham et al. 2002 eq. 2.33
   which uses log(σ̂). Document this as an implementation divergence.]
```

---

## QUICK REFERENCE: Code function → Paper → Equation

| Function | File | Paper | Key equation/section |
|---|---|---|---|
| `HedonicModel.fit()` | `src/models/hedonic.py` | Rosen (1974) | P = f(z₁,…,zₙ), Sections I–III |
| `HedonicModel.fit()` [HC3 SEs] | `src/models/hedonic.py` | MacKinnon & White (1985) | HC3 formula, Section 3 |
| `CallawayAntaCSiD.fit()` | `src/models/did_cs.py` | Callaway & Sant'Anna (2021) | Eq. (2.1)–(2.4), DR estimator |
| `CallawayAntaCSiD.aggregate()` | `src/models/did_cs.py` | Callaway & Sant'Anna (2021) | Eq. (4.1)–(4.3) |
| `TripleDifference.fit()` | `src/models/triple_diff.py` | Gruber (1994) | Triple-diff design, Section II |
| `TripleDifference.decompose()` | `src/models/triple_diff.py` | Callaway & Sant'Anna (2021) | Channel decomposition |
| `ADHSyntheticControl._inner_qp()` | `src/scm/adh_scm.py` | ADH (2010) | Eq. (1)–(3) |
| `ADHSyntheticControl._outer_mspe()` | `src/scm/adh_scm.py` | ADH (2010) | Eq. (4), outcome RMSPE |
| `GeneralizedSyntheticControl.fit()` | `src/scm/gsynth.py` | Xu (2017) | Eq. (3)–(7), EM algorithm |
| `AugmentedSyntheticControl.fit()` | `src/scm/augsynth.py` | Ben-Michael et al. (2021) | Eq. (2.3)–(2.5), ridge correction |
| `InSpacePlacebo.p_value()` | `src/inference/placebo.py` | ADH (2010) | Section 4, RMSPE ratio rank |
| `SpatialWeightsFactory.build_knn()` | `src/spatial/weights_phase3.py` | Anselin (1988) | Chapter 2 |
| `GlobalMoransI.compute()` | `src/esda/morans.py` | Moran (1950) + Cliff & Ord (1981) | Statistic + pp. 42–46 (kurtosis variance) |
| `LocalMoransI.compute()` | `src/esda/lisa.py` | Anselin (1995) | Eq. (1)–(6) |
| `SpatialLagModel.fit()` [log-det] | `src/spatial_models/sar.py` | Ord (1975) | Eigenvalue trick |
| `SpatialLagModel.fit()` [LL] | `src/spatial_models/sar.py` | Anselin (1988) | Chapters 6–8 |
| `SpatialErrorModel.fit()` | `src/spatial_models/sem.py` | Anselin (1988) | Chapter 7 |
| `SpatialDurbinModel.fit()` | `src/spatial_models/sdm.py` | LeSage & Pace (2009) | Chapter 5 |
| `SpatialDurbinModel._lrt_sar()` | `src/spatial_models/sdm.py` | Elhorst (2010) | Table 1, nesting structure |
| `SpatialDurbinModel._wald_sem()` | `src/spatial_models/sdm.py` | Elhorst (2010) | Common-factor restriction |
| `LeSagePaceEffects.compute()` | `src/spatial_models/effects.py` | LeSage & Pace (2009) | Eq. (6.14)–(6.22) |
| `BandwidthSelector.golden_section_search()` | `src/gwr/bandwidth.py` | Fotheringham et al. (2002) | Eq. (2.33), AICc |
| `GeographicallyWeightedRegression.fit()` | `src/gwr/gwr_model.py` | Brunsdon et al. (1996) | Eq. (1)–(4) |

---

## IMPLEMENTATION DIVERGENCES FROM PUBLISHED FORMULAS

These divergences were identified by reading the source code against the cited papers.
Document each one explicitly when writing the paper's methods section.

| Location | Published formula | Code implementation | Impact |
|---|---|---|---|
| `morans.py` variance | Normality assumption | Kurtosis-corrected randomization form (B factor) | More robust; no impact on z-stat |
| `lisa.py` permutation | Conditional permutation (z_i held fixed) | Global shuffle of all z values | Conservative approximation; p-values may be slightly anti-conservative |
| `gwr/bandwidth.py` AICc | 2n ln(σ̂) [Fotheringham eq. 2.33] | 2n ln(σ̂²) [factor-of-2 difference] | Bandwidth selected may differ from the published formula's optimum; document as divergence |
| `effects.py` SEs | Analytical Hessian | Monte Carlo simulation (1000 draws) | Correct approach; degenerate SEs on current 122-obs dataset are a data/sample problem, not a formula error |
