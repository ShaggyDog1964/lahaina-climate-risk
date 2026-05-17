# Literature Guide: Economic Theory and Empirical Context
## Sections: Disaster risk theory · Climate risk pricing · Natural disasters + real estate · Hawaii economics
## Purpose: ground the paper's contribution in the theoretical and empirical literature

---

## 1. Why This Paper Is Interesting: The Economic Mechanism

The Lahaina fire constitutes a natural experiment in climate-risk capitalization. The central claim is that:
1. The fire revealed information about wildfire risk in West Maui that was previously under-priced
2. Rational buyers updated their beliefs about future fire risk (Bayesian updating)
3. This belief update caused a persistent price discount on WUI-classified parcels beyond the physical destruction zone
4. The spatial extent of this discount identifies the geographic reach of climate risk repricing

The triple-difference β₁ − β₂ is designed to identify mechanism (3): controlling for the base price impact (mechanism 2) on all treated parcels, the additional WUI discount (β₁ − β₂) captures the forward-looking risk premium update.

### Why this particular event matters

The 2023 Lahaina fire is the deadliest U.S. wildfire in more than a century (112 confirmed deaths) and destroyed approximately 2,170 structures — a scale comparable to the 2018 Camp Fire in Paradise, California. Unlike most California wildfire events, it struck a dense, historically significant urban neighborhood in a geographically isolated market with no easy substitutes. These features make it an unusually clean setting for studying belief updating: the shock was sudden, visually salient, nationally covered, and struck a market where buyers cannot simply relocate to a comparable West Maui neighborhood at a lower price. Geographic isolation amplifies the belief-update and supply-shock channels simultaneously.

---

## 2. Disaster Risk and Rare Events in Asset Pricing (Theory)

### Why this matters for the project

The "belief update" framing requires a theoretical model where agents update disaster probability after a salient event. Barro and Gabaix provide the calibrated macro-finance version; Bayesian updating provides the micro-foundation. Without this theoretical grounding, the triple-difference β₁ − β₂ is just an interaction term — with it, the coefficient has a structural interpretation as the market price of a probability revision.

### Papers

---

**1. Barro, R. (2006). "Rare Disasters and Asset Markets in the Twentieth Century." *Quarterly Journal of Economics* 121(3): 823–866.**
DOI: 10.1162/qjec.2006.121.3.823

**Connection to project:** Establishes that even small disaster probabilities generate large risk premia when risk aversion is non-trivial. With annual disaster probability p ≈ 0.017 and coefficient of relative risk aversion γ = 3.5, the implied equity premium is approximately 3.5 percentage points. The same mechanism drives a wildfire risk premium in Maui real estate: even if the probability of a Lahaina-scale fire at any given parcel in any given year is very small, the expected utility loss from a house fire is catastrophic (the asset is fully destroyed), so even a small upward revision in p generates a large price discount.

**Key insight:** E[risk premium] ≈ p × E[(1−b)^{−γ} − 1] where b is fractional consumption loss. Even rare disasters with p < 0.02 generate large premia when γ > 2. For housing, b ≈ 1 (total loss), so the expression inside the expectation is extremely large — the formula predicts larger discounts from wildfire risk than from comparable financial disaster risk.

**What to read:** Sections I–III (the model calibration). Section IV (comparing to data) is useful for understanding the parameter space. Budget 3 hours.

---

**2. Gabaix, X. (2012). "Variable Rare Disasters: An Exactly Solved Framework for Ten Puzzles in Macro-Finance." *American Economic Review* 102(5): 2669–2702.**
DOI: 10.1257/aer.102.5.2669

**Connection to project:** Time-varying disaster risk probability p_t explains time-variation in asset prices without requiring time-varying risk aversion. This motivates why properties beyond the fire perimeter should reprice after the Lahaina event: the fire is a realization that updates p_t upward for all of Hawaii, not just for the burned parcels. If disaster probability follows an AR(1) — p_{t+1} = δp_t + ε_t — then a single realization causes persistent upward revision of p_t for all future periods.

**Key insight:** When disaster probability is mean-reverting and time-varying, asset prices move with p_t before any disaster occurs. A visible disaster realization shifts the mean of the conditional distribution of p_t persistently if p follows an AR(1) with δ close to 1. The post-Lahaina price discount on WUI parcels is a market update of the local level of p, not just a response to the specific fire damage.

**Implication for the paper's event study:** The belief-update channel should appear at t=0 (August 2023) and persist — it should not decay toward zero in the event study if the probability update is permanent. If event-study estimates decline in the post-period, that is evidence consistent with Kousky (2010; see Section 4) rather than the Gabaix permanent-update model.

**What to read:** Introduction and Section I (the core model). 2 hours.

---

**3. Weitzman, M. (2009). "On Modeling and Interpreting the Economics of Catastrophic Climate Change." *Review of Economics and Statistics* 91(1): 1–19.**
DOI: 10.1162/rest.91.1.1

**Connection to project:** With thick-tailed climate damage distributions, standard expected utility cannot price catastrophic risks correctly. The "dismal theorem" states that if the tail of the damage distribution is fat enough (e.g., Pareto with tail exponent less than 1/γ), the expected utility integral diverges — infinite willingness to pay for any risk reduction. The practical implication for the Lahaina paper is that rational buyers may impose very large discounts on WUI-classified properties even if the assessed probability of fire is low, because the full conditional distribution of outcomes — including catastrophic loss — dominates the risk calculation.

**Key insight:** The dismal theorem predicts that WUI property discounts could be disproportionately large relative to the actuarially fair discount implied by fire frequency data. If the empirical ATT for WUI parcels substantially exceeds the actuarial value, Weitzman's mechanism is one explanation. This is particularly relevant for Lahaina, where the observed fire consumed an unexpectedly large urban area — a realization from the fat right tail of the damage distribution.

**What to read:** Sections I–III. 2 hours. Note: this paper is widely debated; be prepared to discuss whether the dismal theorem is literally applicable or merely provides qualitative motivation.

---

**4. Epstein, L. and Zin, S. (1989). "Substitution, Risk Aversion, and the Temporal Behavior of Consumption and Asset Returns: A Theoretical Framework." *Econometrica* 57(4): 937–969.**
DOI: 10.2307/1913778

**Connection to project:** Epstein-Zin preferences decouple the elasticity of intertemporal substitution from risk aversion. This matters for the Lahaina paper because the "discount rate channel" interpretation of price discounts (Giglio et al. 2021; see Section 3) requires separating how buyers trade off present vs. future consumption from how they feel about risk. Under Epstein-Zin, a buyer can have high risk aversion (which amplifies the fire risk discount) without being unwilling to invest in long-duration assets (which would independently reduce housing demand). Distinguishing these mechanisms matters for interpreting whether the price discount reflects pure risk repricing or also a shift in effective discount rates.

**What to read:** Sections 1–2. 1.5 hours. Not strictly required but useful for the Giglio et al. comparison.

---

## 3. Climate Risk and Housing Markets (Empirical)

### Why this matters

These are the papers this project's results will be compared against in any submission. A reviewer will ask: "Is your ATT estimate consistent with the established literature?" Know their methods, data, sample sizes, and result magnitudes precisely.

### Papers

---

**1. Bernstein, A., Gustafson, M., Lewis, R. (2019). "Disaster on the Horizon: The Price Effect of Sea Level Rise." *Journal of Financial Economics* 134(2): 253–272.**
DOI: 10.1016/j.jfineco.2019.03.013

**Status in project:** ALREADY IN references.bib as `Bernstein2019`. Cited in the abstract.

**Method:** Property-level hedonic regression using zip-code-level sea level rise exposure maps (NOAA 1-foot, 6-foot, 10-foot flood scenarios) as the treatment variable. The identification assumption is that two otherwise identical properties — one exposed to eventual sea level rise and one not — should sell at the same price absent climate risk capitalization. Sample: approximately 250,000 residential transactions in the continental U.S. coastal zone from 1993 to 2017.

**Key result:** Properties exposed to 6-foot sea level rise sell at a 7% discount relative to comparable unexposed properties, conditional on distance to water, elevation, and a full set of zip-year fixed effects. The discount has grown since 2013 and is larger in counties with higher climate awareness (consistent with the Baldauf et al. 2020 belief mechanism).

**What to compare:** When you report the ATT for 0–2 km parcels, compare it to Bernstein's 7%. If your estimate is 10–30%, that is consistent with wildfire (physical destruction, irreversible loss of the structure) being a more severe outcome than sea level rise (gradual inundation, some time to adapt and sell). If your estimate is less than 7%, consider whether the thinness of the Lahaina transaction sample is attenuating the estimate.

**What to read:** Entire paper. 3 hours.

---

**2. Baldauf, M., Garlappi, L., Yannelis, C. (2020). "Does Climate Change Affect Real Estate Prices? Only if You Believe in It." *Review of Financial Studies* 33(3): 1256–1295.**
DOI: 10.1093/rfs/hhz073

**Status in project:** ALREADY IN references.bib as `Baldauf2020`. Cited in the abstract.

**Method:** Uses county-level climate change belief data from the Yale Climate Opinion Maps interacted with FEMA Special Flood Hazard Area (100-year flood zone) exposure. The key variation is cross-sectional: within the same FEMA flood zone, do properties sell at different discounts in high-belief vs. low-belief counties? Identification exploits the geographic discontinuity in beliefs at county boundaries combined with the FEMA flood zone boundary.

**Key result:** Flood-zone properties in high-climate-belief counties (top quartile) sell at a 7–11% discount relative to non-flood-zone properties; in low-belief counties (bottom quartile), the discount is near zero and statistically indistinguishable from zero. The belief mechanism is the dominant channel for risk capitalization.

**Implication for the Lahaina paper:** Hawaii consistently scores as a high-climate-belief state in the Yale Climate Opinion data — it is a heavily Democratic state with a population that is acutely aware of climate vulnerability. This implies that the belief-update channel (β₁ − β₂ in the triple-difference) should be larger in Lahaina than in comparable wildfire markets in lower-belief states (e.g., rural California, Texas). The Baldauf et al. finding provides a testable benchmark: the WUI belief-update channel should be non-trivial if Hawaii buyers are in the top-belief quartile.

**What to read:** Entire paper. 3 hours.

---

**3. Giglio, S., Maggiori, M., Stroebel, J., Tan, Z., Utkus, S., Xu, X. (2021). "Climate Change and Long-Run Discount Rates: Evidence from Real Estate." *Review of Financial Studies* 34(8): 3527–3571.**
DOI: 10.1093/rfs/hhab032

**Method:** Exploits the institutional difference between freehold (perpetual ownership) and leasehold (fixed-term, typically 99-year) property rights in the UK and Singapore to measure very long-run discount rates. Climate-exposed properties have shorter effective economic lives (they will eventually be flooded or destroyed) so the freehold-leasehold price spread is informative about how markets price very-long-horizon climate risk.

**Key result:** Climate-exposed properties have higher long-run discount rates — investors demand higher expected returns, implying lower prices today even for risks that materialize 50–100 years in the future. The implied risk premium for long-run climate exposure is economically significant.

**Implication for the Lahaina paper:** The price discount on WUI-classified parcels can be interpreted as reflecting a higher effective discount rate applied to future cash flows from those properties. A buyer who assigns higher probability to the property being destroyed in a future wildfire will require a lower purchase price today, even if the risk materializes only probabilistically over 20–30 years. The Giglio et al. framework gives this interpretation formal content.

**Connection to Hawaii's leasehold market:** Hawaii has an unusually large leasehold residential market (a legacy of the Bishop Estate and other land trusts). If any WUI parcels in the sample are on leasehold titles, the Giglio et al. framework applies directly and provides an alternative estimate of the implied discount rate for fire risk.

**What to read:** Sections 1–3. 2 hours.

---

**4. Hong, H., Li, F., Xu, J. (2019). "Climate Risks and Market Efficiency." *Journal of Econometrics* 208(1): 265–281.**
DOI: 10.1016/j.jeconom.2018.09.015

**Method:** Uses county-level sea level rise exposure data interacted with stock market valuations of coastal real estate firms. Finds that equity markets underreact to rising sea level exposure over time — the exposure coefficient in the pricing regression becomes more negative over the sample period as the physical risk increases, suggesting markets are slow to update.

**Key result:** Stock markets appear to underreact to climate risk. The efficiency correction — when prices finally incorporate the risk — is rapid and generates large returns for short sellers. The Lahaina fire, as a single extremely salient event, may trigger the market efficiency correction that normally takes years to diffuse.

**Key insight:** The "availability heuristic" in behavioral economics (Kahneman and Tversky) predicts that experienced events are weighted more heavily than probabilistically equivalent non-experienced events. The Lahaina fire converts implicit wildfire risk (a probability) into experienced risk (a memory). This behavioral mechanism predicts larger price discounts post-fire than a purely rational model would, particularly in the short run (2023–2025 in the data window).

**Implication for the paper:** If the event study shows a large immediate price jump followed by partial recovery, that is consistent with Hong et al.'s "overreaction then correction" pattern. If the discount is persistent, it is consistent with a rational risk premium update. The shape of the event-study coefficients distinguishes these mechanisms.

**What to read:** Sections I–III. 2 hours.

---

**5. Keys, B. and Mulder, P. (2020). "Neglected No More: Housing Markets, Mortgage Lending, and Sea Level Rise." NBER Working Paper 27930.**
DOI: 10.3386/w27930

**Method:** Examines whether mortgage lenders have begun pricing sea level rise risk into mortgage rates, origination decisions, and securitization rates. Finds that GSE securitization rates for flood-exposed properties have declined — lenders are increasingly pricing out of flood-zone exposure by refusing to hold or securitize loans on high-risk properties.

**Key result:** By 2019, flood-zone properties in high-exposure zip codes faced 20–30 basis point higher mortgage rates and lower GSE purchase probabilities. The channel runs through lender risk assessment, not just buyer preferences.

**Implication for the Lahaina paper:** The price discount on WUI parcels may be amplified by tightening mortgage credit availability for fire-exposed properties. If lenders or insurance companies have repriced West Maui fire risk post-2023, the effective financing cost for WUI parcels is higher — which translates directly into lower sale prices. This is a distinct mechanism from buyer belief updating but produces the same observable outcome. The paper should acknowledge this channel in the discussion even if it cannot be separately identified with the current data.

**What to read:** Sections I–III. 2 hours.

---

## 4. Natural Disasters and Real Estate Prices (Direct Comparators)

### Why this matters

These are the papers reviewers will specifically cite when evaluating whether the estimated ATT magnitude is plausible. You need to know the "reasonable range" for your results and the methodological precedents for identifying disaster effects on property values.

### Papers

---

**1. Coffman, M. and Noy, I. (2012). "Hurricane Iniki: Measuring the Long-Term Economic Impact of a Natural Disaster Using Synthetic Control." *Environment and Development Economics* 17(2): 187–205.**
DOI: 10.1017/S1355770X11000350

**Connection to project:** The MOST DIRECTLY COMPARABLE published paper. Uses the synthetic control method for a Hawaii natural disaster (Hurricane Iniki, September 1992, Kauai). The donor pool is the other Hawaiian counties. The treatment unit is Kauai County. This is nearly identical to Phase 2 of the current project — Maui County ZIP codes as treated units, other Hawaii ZIP codes as donors.

**Key result:** Hurricane Iniki reduced Kauai County's per-capita personal income by approximately 18% permanently (no convergence observed over the 10-year post-period). The synthetic control's pre-period fit is excellent: pre-period RMSPE is very small and the visual match between Kauai and synthetic Kauai is tight for the 20-year pre-period.

**What to compare directly to your Phase 2 results:**
- Their pre-period RMSPE (very small, visually tight) vs. this project's pre-RMSPE = 0.0154
- The permanence of their treatment effect vs. the RMSPE ratio = 3.06 observed here
- Their donor pool (other Hawaii counties — 3 units) vs. this project's donor pool (58 ZIP codes)
- Their permutation inference (small number of placebos — 3) vs. this project's p = 0.155 with 58 placebos

**Note on comparison:** Coffman-Noy have fewer donors but stronger pre-period fit and a clearly significant result. The current project has more donors but a non-significant permutation p-value (0.155). The difference may be explained by: (a) income is more persistent than house prices; (b) Iniki was larger relative to the Kauai economy than the Lahaina fire relative to Maui County; (c) the current project's donor pool may include ZIPs that are poor matches for Maui.

**What to read:** Entire paper. 2 hours.

---

**2. Hallstrom, D. and Smith, V.K. (2005). "Market Responses to Hurricanes." *Journal of Environmental Economics and Management* 50(3): 541–561.**
DOI: 10.1016/j.jeem.2005.02.002

**Connection to project:** The closest methodological precedent for identifying pure belief updates vs. physical damage. Uses a NEAR-MISS hurricane (Hurricane Andrew, 1992 — which nearly hit southwest Florida before shifting trajectory) as a quasi-experiment. Properties in the near-miss zone received the information shock (heightened hurricane awareness) without physical destruction.

**Key result:** A near-miss hurricane reduced property prices in the near-miss zone by 6–10% — purely a risk perception effect with no physical destruction channel. This is the "pure belief update" benchmark in the literature.

**What to compare:** Your WUI interaction β₁ − β₂ is designed to isolate exactly this mechanism. If β₁ − β₂ is in the 6–10% range, that is consistent with the Hallstrom-Smith near-miss benchmark. If it is larger, the Lahaina fire provided a more severe information shock than a near-miss (consistent with "availability heuristic" amplification). If it is smaller or zero, either the belief-update channel is not operating or the WUI indicator is a poor proxy for forward-looking risk.

**What to read:** Entire paper. 2 hours.

---

**3. Bakkensen, L. and Barrage, L. (2022). "Going Underwater? Flood Risk Belief Heterogeneity and Implications for Housing Markets, Surveys, and Optimal Policy." *Journal of Political Economy* 130(5): 1290–1357.**
DOI: 10.1086/718982

**Connection to project:** Provides the most rigorous decomposition of physical risk from perceived risk in disaster-affected housing markets. Uses survey data on flood risk beliefs combined with property transaction data in Rhode Island to separately identify buyers who accurately vs. inaccurately perceive flood risk.

**Key result:** Buyers with accurate flood risk beliefs impose 8–10% price discounts on flood-zone properties; buyers with underestimated risk impose near-zero discounts. Moral hazard from the National Flood Insurance Program (NFIP) substantially reduces the capitalization of flood risk — subsidized insurance reduces the effective perceived cost of flood risk, driving discounts toward zero.

**Implication for the Lahaina paper:** The analogous question is whether Hawaii homeowners' insurance adequately prices wildfire risk. If fire insurance for WUI properties in Hawaii is repriced upward post-2023 (higher premiums or reduced availability), the effective risk burden on WUI buyers increases — and the observed price discount reflects both a belief update and an insurance pricing shock. These channels cannot be separated without insurance premium data, but the paper should acknowledge them. The Bakkensen-Barrage framework predicts that the belief-update channel (β₁ − β₂) is larger when insurance is less available, consistent with the post-Lahaina insurance market disruption in Hawaii.

**What to read:** Sections I–IV. 3 hours.

---

**4. Bin, O. and Polasky, S. (2004). "Effects of Flood Hazards on Property Values: Evidence before and after Hurricane Floyd." *Land Economics* 80(4): 490–500.**
DOI: 10.3368/le.80.4.490

**Connection to project:** A foundational pre-post hedonic study using Hurricane Floyd (1999, North Carolina) as a natural experiment. The methodology — compare flood-zone to non-flood-zone property prices before and after a major flood — is a direct predecessor of the Lahaina DiD design.

**Key result:** Flood zone discount increased from approximately 5% pre-hurricane to approximately 8% post-hurricane. The 3-percentage-point increase represents the belief update attributable to experiencing the flood. Properties outside the 100-year flood zone but near flooded areas also showed price declines, consistent with belief updating beyond the formal risk designation boundary.

**What to compare:** The Bin-Polasky result (3 pp increase in discount after the flood) is directly analogous to the difference between β₂ (baseline treated discount) and β₁ (WUI-treated discount). If β₁ − β₂ is in the 3–5% range, that is consistent with Bin-Polasky. If the total treated discount (β₂) is comparable to Bernstein's 7% sea-level-rise result, the combined picture is internally consistent.

**What to read:** Sections I–III. 1.5 hours.

---

**5. Kousky, C. (2018). "Financing Flood Losses: A Discussion of the National Flood Insurance Program." *Risk Management and Insurance Review* 21(1): 11–32.**
DOI: 10.1111/rmir.12090

**Status in project:** IN references.bib as `Kousky2018`. NOTE: This is a different paper than the "Learning from Extreme Events" paper often attributed to Kousky. The bib entry cites a 2018 NFIP financing paper, not the belief-updating paper. For the belief-decay mechanism described in the project's framing, the correct citation is:

**Kousky, C. (2010). "Learning from Extreme Events: Risk Perceptions After the Flood." *Land Economics* 86(3): 395–422.** DOI: 10.3368/le.86.3.395 [citation to be verified — check whether this is the correct journal, volume, and pages]

**Connection to the 2018 paper actually in the bib:** The NFIP financing paper discusses how subsidized flood insurance creates moral hazard that suppresses the capitalization of flood risk into property prices. This is directly relevant to the Lahaina paper: if Hawaii homeowners' insurance for WUI properties is subsidized or unavailable, the observed price discount understates the actuarial fire risk premium, just as Kousky argues the NFIP suppresses flood risk capitalization.

**Connection to the belief-decay mechanism (Kousky 2010):** If the data window extends to 2025–2026, the event study may show declining post-fire discounts. This "fading memory" pattern — price discounts are highest 1–2 years post-disaster and decay toward pre-disaster levels over 5–7 years — is documented in the flood risk literature. The Lahaina data (April 2024–September 2025) covers only the first 1–2 years post-fire, which is the period when discounts should be at their maximum under the fading-memory model. If results show no discount, that is evidence against both the risk-repricing and the fading-memory channels.

**What to read:** Entire 2018 paper. 2 hours. Locate and read the 2010 paper separately.

---

**6. Issler, P., Stanton, R., Vergara-Alert, C., Wallace, N. [citation to be verified]. "Mortgage Markets with Climate-Change Risk: Evidence from Wildfires in California."**

**Connection to project:** The most directly comparable wildfire-specific paper in the real estate finance literature. Uses California residential wildfire data with a DiD strategy similar to Phase 1 of this project. As of the knowledge cutoff, a working paper version existed at SSRN; a journal publication may exist by 2026.

**What to find:** Search SSRN, NBER, or Google Scholar for "Issler Stanton Vergara-Alert Wallace wildfire mortgage" to find the current version and its publication venue, DOI, and ATT estimate.

**Expected result range:** California wildfire DiD papers typically report property value declines of 10–30% within the fire perimeter and 3–10% in the near-perimeter zone (0–2 km), with effects decaying to near-zero beyond 5–10 km. If the current paper's ATT falls in this range, the results are consistent with the California wildfire literature.

**What to compare:** Issler et al.'s ATT for near-perimeter properties vs. the Lahaina ATT for the 0–2 km band. Note that the California study likely has a much larger sample (thousands of transactions vs. the current project's 2,636), which means their standard errors will be much smaller — any comparison should acknowledge the Lahaina sample is at the low end for credible hedonic identification.

---

**7. Anenberg, S. and Kung, E. [citation to be verified — search for Camp Fire + property values]. "The Lahaina paper's closest structural comparator: the 2018 Camp Fire."**

**Connection to project:** The 2018 Camp Fire destroyed approximately 18,800 structures in Paradise, California — the largest structure-loss wildfire in U.S. history and the closest comparator to Lahaina's 2,170 structures. Several working papers and at least one published paper use the Camp Fire as a natural experiment for property value effects.

**What to find:** Search Google Scholar, SSRN, or NBER for "Camp Fire property values difference-in-differences" or "Paradise California housing prices 2018." Multiple papers may exist. Find the version with the largest sample and most credible identification, and record:
- ATT estimate for within-perimeter properties
- ATT estimate for 0–2 km near-perimeter properties
- Method (hedonic DiD, synthetic control, or event study)
- Sample size and time window

**Expected result:** Camp Fire studies likely show 20–40% property value declines within the perimeter (physical destruction) and 5–15% declines in the 0–5 km near-perimeter zone. Lahaina estimates should be in a similar range given comparable scale.

---

**8. Bakkensen, L. and Ma, L. (2020). "Sorting Over Flood Risk and Implications for Policy Reform." NBER Working Paper 28077.**
DOI: 10.3386/w28077 [citation to be verified — check year and working paper number]

**Connection to project:** Documents that buyers who move into flood-risk areas have heterogeneous beliefs about flood risk — some systematically underestimate it. This sorting dynamic means that the buyer pool in fire-risk WUI areas may not be representative of the general population in terms of risk perception. Lahaina buyers, post-fire, are selecting into a market where the risk has been vividly demonstrated — the post-fire buyer pool is almost certainly drawn from a different part of the belief distribution than the pre-fire buyer pool.

**Implication:** If post-fire buyers are more risk-tolerant (or have access to better fire mitigation resources), the observed price discount understates the average buyer's willingness-to-pay reduction. Conversely, if post-fire buyers are disproportionately investors purchasing at a discount with the expectation of price recovery, the observed prices reflect speculative holding rather than long-run capitalization. The paper should acknowledge this sorting caveat.

---

## 5. Hawaii-Specific Economics

### Why this matters

Hawaii's real estate market is unusual in several dimensions that affect how the Lahaina results should be interpreted and how broadly they generalize. Reviewers will raise these as external validity questions. These papers and data sources provide the context.

### Hawaii market characteristics relevant to the Lahaina paper

- **Geographic isolation**: West Maui has no nearby substitute. Buyers who want oceanfront Maui property cannot substitute to an equivalent market 50 miles away. This supply inelasticity amplifies price responses to both supply shocks (physical destruction) and demand shocks (risk repricing).
- **Tourism dependence**: A significant fraction of West Maui residential properties are vacation rentals or second homes. Displacement of tourism reduces rental income and holding values, which is a distinct channel from owner-occupant risk aversion.
- **High median home values**: The median home price in West Maui significantly exceeds the state median (~$1M+). Buyers in this price range are typically high-income and financially sophisticated — they are more likely to act on climate risk information (consistent with Baldauf et al.'s high-belief-county finding).
- **Insurance market disruption**: Following the August 2023 fire, several insurers reduced or cancelled homeowners' insurance coverage in West Maui. This amplifies the effective cost of WUI property ownership independently of buyer risk preferences.
- **Native Hawaiian land rights and displacement**: A significant fraction of Lahaina residents were Native Hawaiian families with long-term ties to the area. Their displacement is not captured by property transaction data but affects the social context in which market prices are determined.

### Papers and sources

---

**1. Coffman, M. and Noy, I. (2012).** [Full entry in Section 4 above]

The Hawaii-specific natural disaster paper. Use this as the primary reference for contextualizing the Lahaina study within the broader literature on Hawaii's economic history and vulnerability.

---

**2. UHERO — University of Hawaii Economic Research Organization.**
Website: uhero.hawaii.edu

Search for:
- UHERO Brief: "Economic Impact of the 2023 Lahaina Wildfire" (search the UHERO website for publications from August–December 2023)
- UHERO Report: "Hawaii Housing Market" (annual or semi-annual reports on statewide housing conditions)
- UHERO Tourism industry analysis post-2023

These are gray literature but are the primary source for Maui-specific macroeconomic context. UHERO researchers have published on Hawaii disaster economics and housing supply constraints; any published UHERO analysis of the Lahaina fire should be cited if it exists.

---

**3. Sutter, D. and Poitras, M. (2010). "Do People Respond to Low Probability Risks? Evidence from Tornado Risk and Manufactured Homes." *Journal of Risk and Uncertainty* 40(2): 181–196.**
DOI: 10.1007/s11166-010-9089-x

**Connection to project:** Documents that low-probability risks ARE capitalized into housing markets when the risk is salient and visually familiar. Uses a county-level cross-section of manufactured home prices and tornado occurrence data. Areas with higher historical tornado frequency have lower manufactured home prices, with the discount proportional to expected risk.

**Implication for Lahaina:** The Sutter-Poitras result provides evidence that even "rare" events are priced if they are salient to buyers. Wildfire is visually salient (smoke, orange skies, news coverage), personally proximate (neighbors' homes destroyed), and physically comprehensible in a way that sea level rise is not. This supports the prediction that the Lahaina fire generates larger belief updates than equivalent sea-level-rise information, consistent with Hong et al.'s availability heuristic mechanism.

**What to read:** Sections I–III. 1.5 hours.

---

**4. Hawaii Bureau of Conveyances — Maui County residential deed transfers.**
Website: https://boc.ehawaii.gov

This is not a paper but a primary data source. If the current project's `maui_assessor.csv` has uncertain provenance (as documented in `docs/RESEARCH_ASSESSMENT.md`), the Bureau of Conveyances is the authoritative source for pre-fire residential transaction data in Hawaii. Deed transfer extracts are available by county and year; the Maui County residential transfer file for 2018–2026 would provide the verified transaction data the project currently lacks.

**Relevance to the paper:** Any submission should describe the transaction data source precisely. "Maui County Real Property Assessment Roll" may refer to assessment (valuation) data rather than arm's-length transaction data. The distinction matters: assessment rolls record estimated values, not actual sales prices. Actual sales prices must come from deed transfer records or a compiled transaction database (CoreLogic, ATTOM, Redfin). Clarifying the data source and its provenance is necessary before any results can be relied upon.

---

## 6. Identification Assumptions — Threats and Defenses

For each key assumption in the paper, the specific threat and the defense are listed. This section serves as the "referee response" preparation: these are the objections a careful referee will raise, and the answers the paper should have ready.

---

### Parallel trends (Callaway-Sant'Anna DiD)

**Assumption:** Absent the Lahaina fire, treated and control parcels would have had parallel log-price trajectories.

**Main threat:** Selection on pre-trends. The Lahaina fire burned in WUI areas with specific vegetation, elevation, and terrain characteristics. These same characteristics may have independently driven pre-fire price trends — for example, WUI parcels may have appreciated faster than control parcels due to ocean view and scenic character, or slower due to pre-existing insurance risk awareness. If treated parcels were already on a different price trajectory before August 2023, the DiD estimate confounds the fire effect with a pre-existing trend.

**Defense:** Pre-trend regression (`src/models/parallel_trends.py`). Plot the event-study ATT(g,t) estimates for all pre-fire periods — they should scatter around zero with confidence intervals that exclude economically meaningful magnitudes. Add geographic controls (distance to ocean, elevation, census block FE) to absorb confounders correlated with both fire proximity and pre-trend. The current event study shows ATT = 0 for all pre-periods, but this reflects degenerate estimation (all zeros), not a genuine pre-trend test. A valid parallel trends test requires confirmed real transaction data.

**Threat 2:** SUTVA (Stable Unit Treatment Value Assumption). The Lahaina fire reduced housing supply in the Lahaina submarket by 2,170 units. This supply destruction increases prices for comparable non-burned properties elsewhere on Maui — i.e., the "control" properties benefit from a supply shock that has nothing to do with the fire risk channel. If this is true, the estimated ATT for treated parcels relative to control parcels is biased toward zero (attenuated), because the control group's prices are elevated by displaced demand.

**Defense:** The SUTVA violation due to supply displacement works in the direction of attenuation — the estimated ATT is a lower bound on the true effect. Documenting this as a limitation is the appropriate response. An ideal robustness check would use non-Maui Hawaii ZIP codes as the comparison group (similar income and climate profiles but no supply displacement), but this requires a different data source.

**Threat 3:** Insurance repricing as a confounding shock. Post-August 2023, several insurers reduced or cancelled homeowners' coverage in West Maui. If WUI parcels face more insurance non-renewal than non-WUI parcels in the same distance band, the post-fire WUI price discount conflates the belief-update channel with an insurance availability shock. These two channels have identical implications for observed prices but different policy implications.

**Defense:** Acknowledge in the paper that β₁ − β₂ captures the combined effect of belief updating and insurance-cost increases for WUI properties. Separating them requires insurance premium or cancellation data, which is not currently in the pipeline.

---

### No anticipation (Callaway-Sant'Anna DiD)

**Assumption:** Treated parcels did not begin adjusting prices before August 8, 2023.

**Threat:** If buyers anticipated the fire (e.g., from weather forecasts during the August 8 event, or from pre-existing awareness of WUI fire risk driven by 2023 drought conditions), pre-fire prices may have already started declining before the formal treatment date. This would cause the pre-period ATT estimates to be negative rather than zero, and the parallel trends test would reject even in the absence of a violation.

**Defense:** The Lahaina fire was a rapid-onset event. Ignition occurred at approximately 6:00 AM on August 8, 2023, from downed power lines during high-wind conditions. The fire reached the historic district by approximately 11:00 AM. No buyer could have priced this specific event into a property transaction signed in the days immediately before August 8. Anticipation within the pre-fire months (July 2023) is theoretically possible due to drought coverage, but the pre-trend test can assess this directly. Plot pre-fire monthly ATTs through July 2023; if they are uniformly near zero, anticipation is not a first-order concern.

---

### Exclusion restriction (triple-difference)

**Assumption:** WUI classification affects post-fire prices only through the forward-looking wildfire risk channel, not through other channels that are independently activated by the fire.

**Threat:** WUI parcels have specific physical characteristics (vegetation density, lot size, distance from urban core, building materials) that correlate with fire damage risk AND independently affect post-fire prices through distinct channels. For example: (a) WUI parcels may have higher vegetation management costs that become salient post-fire; (b) lenders may refuse to originate or refinance mortgages on WUI parcels post-fire regardless of actuarial risk; (c) WUI classification may proxy for lower neighborhood amenity values that become more visible post-fire (fewer trees, more scorched landscape).

**Defense:** Include WUI × structural attribute interactions to verify the WUI treatment effect is not driven by lot size or building characteristics. Test that WUI × post is zero in the pre-period within the treated zone — if WUI parcels were systematically different in price trend pre-fire, the exclusion restriction is violated. The key test is whether the WUI differential exists only post-fire and specifically in the treated (near-perimeter) zone, not in the control zone. If WUI parcels in the control zone (>10 km) also show post-fire discounts relative to non-WUI control parcels, that suggests the WUI effect is market-wide rather than local, which is itself interesting but different from the triple-difference interpretation.

---

### External validity

**Question:** Do Lahaina results generalize to other wildfire-affected markets?

**Constraints that limit generalization:**

1. **Supply inelasticity**: West Maui has no nearby substitutes. Buyers who want Maui waterfront real estate cannot substitute to an equivalent market at lower cost. Mainland wildfire markets (Paradise CA, parts of Colorado, Oregon) are near larger metro areas with more substitutable housing stock. Price discounts may be larger in Hawaii precisely because supply is more constrained.

2. **Tourism dependence**: A significant share of West Maui residential properties are vacation rentals or second homes. The demand shock from the fire includes both owner-occupant displacement and tourism disruption. This makes the Lahaina market structurally different from purely residential wildfire markets in California or Colorado.

3. **Climate awareness and political economy**: Hawaii is a high-climate-belief state. The belief-update channel (β₁ − β₂) is expected to be larger in high-belief markets (Baldauf et al. 2020). Results from Lahaina may overstate the belief-update channel for equivalent wildfire events in lower-belief markets.

4. **Insurance market structure**: Hawaii's homeowners' insurance market is smaller and less competitive than California's. Post-Lahaina insurance disruption in Hawaii may have been more severe than it would be in a market with more insurer competition, amplifying the effective cost shock for WUI buyers.

5. **Cultural and social characteristics**: Lahaina's historic status as a culturally significant community for Native Hawaiians, combined with the severity of displacement, may have generated unusual market dynamics (community pressure to sell, estate liquidations, investor entry) that do not generalize to standard wildfire markets.

**Implication for the paper:** State clearly in Section 6 (Conclusion) that results are specific to the Lahaina market context. Compare to the Camp Fire (Paradise, CA) as the closest comparable magnitude wildfire, and to Coffman-Noy (Hurricane Iniki) as the closest Hawaii disaster study. Do not claim the estimates establish a general law for wildfire price effects.

---

## 7. References Not Yet in references.bib — Additions to Consider

The following papers are mentioned in this guide and are not currently in `paper/references.bib`. Consider adding them when the paper reaches a draft stage with actual result values.

| Paper | Key use in paper |
|---|---|
| Barro (2006) QJE | Theory grounding for rare disaster risk premium |
| Gabaix (2012) AER | Time-varying disaster probability → post-fire repricing |
| Weitzman (2009) ReStud | Fat-tailed damage distributions → large discounts |
| Hallstrom and Smith (2005) JEEM | Benchmark for pure belief-update channel (6–10%) |
| Bakkensen and Barrage (2022) JPE | Decomposition of physical vs. perceived risk |
| Bin and Polasky (2004) Land Economics | Pre-post hedonic predecessor |
| Goodman-Bacon (2021) JE | Justification for C&S over TWFE |
| de Chaisemartin and D'Haultfoeuille (2020) AER | Additional TWFE contamination bias reference |
| Coffman and Noy (2012) EDE | Hawaii comparator (already important to cite) |
| Roth et al. (2023) JE | DiD synthesis survey |
| Palmquist (1984) ReStud | Hedonic theory for locational attributes |
| Keys and Mulder (2020) NBER | Mortgage credit channel for climate risk |
| Issler et al. [citation to be verified] | California wildfire ATT comparator |
| Camp Fire paper [citation to be verified] | Paradise CA magnitude comparator |

For papers marked [citation to be verified], search NBER, SSRN, and Google Scholar before adding to the bib. Do not add entries with invented DOIs or journal names.
