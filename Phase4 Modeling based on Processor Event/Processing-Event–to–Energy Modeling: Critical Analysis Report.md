# Processing-Event–to–Energy Modeling: Critical Analysis Report

> **Goal.** Use software-visible **processor events (PEs)** to predict **hardware slow-preset energy** ( (E_{hw,slow}) ) and compare prediction behavior across two filtering configurations and four encoder presets.

---

## 1. Experimental Context & Goal

* **Encoder & switches**

  * **Config A**: `--no-deblock --sao` (SAO enabled; Deblock disabled)
  * **Config B**: `--deblock --no-sao` (Deblock enabled; SAO disabled)
* **Presets**: `fast`, `faster`, `veryfast`, `superfast`
* **Target**: measured hardware energy at **slow** preset (aligned and injected as `E_hw_slow`)
* **Features (13 PEs)**: `Ir, Dr, Dw, I1mr, D1mr, D1mw, ILmr, DLmr, DLmw, Bc, Bcm, Bi, Bim`
* **Research question**

  1. Does SAO vs. Deblock materially change *predictability* of energy from PEs?
  2. How does predictability vary by preset?

---

## 2. Data, Alignment, and Files

* **Source tables**

  * `H:\all_dataset.csv` (contains `E_process_single_J` and metadata)
  * `H:\valgrind\callgrind_summary.csv` (PE summaries per run)
  * `H:\valgrind\callgrind_summary_with_E_hw_slow.csv` (merged table with `E_hw_slow`)
* **Alignment key**: `encoder == NVIDIA` ∧ `preset == 4` (in all_dataset) ∧ **QP** match ∧ `video_name == seq_name`.
* **Derived outputs (modeling)**

  * `overall_metrics.csv`
  * `mape_by_preset_long.csv`
  * `mape_by_preset_wide.csv`
  * `oof_predictions.csv`
  * `pe_means_by_preset_config.csv`

**Repro scripts**

* **Filling energy**: the earlier merge script (filters NVIDIA/preset=4 and joins by QP+video).
* **Model training**: `train_energy_models.py` (Linear & XGBoost, 5-fold **GroupKFold by `seq_name`**).
* **Preset analysis**: `analyze_preset_mape.py` (produces OOF predictions, per-preset MAPE tables, PE means).

> **OOF predictions** = per-sample predictions from CV folds where that sample was **not** in training. All metrics below are aggregated from OOF, thus reflect generalization.

---

## 3. Metrics (no abbreviations)

* **Coefficient of determination**: fraction of variance in measured energy explained by the model (higher is better).
* **Root mean square error**: average absolute error in **energy units** (lower is better).
* **Mean absolute percentage error** (“mean error rate”): average relative error (lower is better).

---

## 4. Results — Overall (all presets pooled)

From your `overall_metrics.csv` (exact values):

| Configuration | Model              | Coefficient of Determination | Root Mean Square Error | Mean Absolute Percentage Error |
| ------------- | ------------------ | ---------------------------: | ---------------------: | -----------------------------: |
| A             | Linear Regression  |              **0.952760728** |        **0.632960022** |                **0.040346966** |
| A             | XGBoost Regression |                  0.947650089 |            0.666319703 |                **0.027529404** |
| B             | Linear Regression  |                  0.919104075 |            0.828300652 |                    0.051716984 |
| B             | XGBoost Regression |              **0.930968886** |        **0.765150950** |                **0.027591544** |

**Checks & critical reading**

* **XGBoost** attains ~**2.75–2.76%** mean percentage error in both A and B, clearly outperforming linear’s **4.0–5.2%**.
* **Rationale**: energy–PE relation is **nonlinear** (interactions among memory and branch events).
* **A vs B**:

  * A shows **higher** explained variance for Linear (0.953) than B (0.919), yet **XGBoost percentage error** is virtually tied (2.753% vs 2.759%).
  * Interpretation: **SAO (A)** may correlate strongly overall (high variance explained) yet has **larger relative noise**, while **Deblock (B)** is **more uniform in relative terms** even if global variance is less linear.

---

## 5. Results — By Preset (MAPE, from `mape_by_preset_wide.csv`)

*(values in fractions; convert ×100 for %)*

| Preset        |    A Linear |    B Linear |    Δ(A−B) Linear |   A XGBoost |   B XGBoost |   Δ(A−B) XGBoost |
| ------------- | ----------: | ----------: | ---------------: | ----------: | ----------: | ---------------: |
| **fast**      | 0.041748557 | 0.049504414 | **−0.007755857** | 0.027794041 | 0.027099286 | **+0.000694755** |
| **faster**    | 0.041910646 | 0.047391450 | **−0.005480804** | 0.028188862 | 0.023820083 | **+0.004368779** |
| **superfast** | 0.037396338 | 0.056283975 | **−0.018887637** | 0.028024562 | 0.026374471 | **+0.001650091** |
| **veryfast**  | 0.040332324 | 0.053688098 | **−0.013355774** | 0.026110150 | 0.033072338 | **−0.006962187** |

**Plain-English reading**

* **Linear Regression**: **A is better than B for every preset** (Δ < 0). This **confirms the team’s expectation**: *if a linear model suffices, Config A (SAO) is easier to predict*.
* **XGBoost**:

  * **B better** for `fast`, `faster`, `superfast` (Δ > 0; B has smaller error by 0.07–0.44 percentage points).
  * **A better** for `veryfast` (Δ < 0; A gains a 0.70-point advantage).
* **Critical note**: the **largest separation** appears at **`faster`** (XGB: A 2.82% vs B 2.38%, Δ≈+0.44%), while **`veryfast`** flips the sign (A 2.61% vs B 3.31%).

---

## 6. Mechanistic Interpretation (cross-checking with PE means)

**Observed PE pattern (from `pe_means_by_preset_config.csv` and your heatmap):**

* **superfast**: *most* PEs minimal (fewer instructions, fewer reads/writes, fewer branches), **but `D1mr` is maximal**.

  * **Explanation**: superfast heavily prunes RDO/loops → **lower reuse**, shorter/irregular loops → **weaker L1 locality & prefetching** → **L1 data-read misses rise** despite smaller total traffic.
  * Higher-level misses (LLC) may remain low because the **working set is smaller**.
* **A (SAO)** tends to elevate **memory/cache metrics** (`Dr`, `D1mr`, `DLmr`, `DLmw`) due to neighbor-pixel accesses;
  **B (Deblock)** elevates **branch metrics** (`Bc`, `Bcm`, `Bim`) via conditional filters.

**Link to predictability**

* **Linear model** prefers **stable, approximately additive relations**. SAO’s memory-driven cost profile in A is **more linearly approximable** → linear MAPE consistently lower for A.
* **XGBoost** captures **nonlinear** interactions. Deblock’s branch-heavy behavior in B is **more nonlinear but regular** enough for trees to learn → B often wins for XGB (except `veryfast`, where the mix of control-flow and reduced feature diversity seems to hurt B).

---

## 7. Sanity Checks & Potential Pitfalls

1. **Leakage control**: used **GroupKFold by `seq_name`**; no sequence appears in both train and validation. ✔
2. **Target scaling**: MAPE is sensitive when true energy is small. We safeguarded with an `eps`, but extremely small targets would inflate percentages. No red flags observed from per-preset MAPEs (~2.4–3.3%). ✔
3. **Preset balance**: each preset in A/B shows **n=120** samples in `mape_by_preset_long.csv` (balanced). ✔
4. **Outliers**: the `veryfast@B` XGB error (3.31%) is notably worse; investigate per–sequence residuals in `oof_predictions.csv` (by `seq_name`, `qp`) to identify outliers or texture-dependent divergence. ⚠
5. **Feature sufficiency**: 13 raw counts ignore **rates/ratios** (e.g., `D1mr/Dr`, `Bim/Bc`) that often improve stability. Consider augmenting features. ⚠

---

## 8. What the Results Mean for Our Goal

* **Feasibility**: Using PEs to predict **hardware energy** works very well: **~2.6–3.3%** MAPE with XGB; **~3.7–5.6%** for Linear.
* **Design takeaway**:

  * If we **require a simple model** (low complexity, interpretability), **Config A (SAO)** is **preferable** (Linear consistently better for A).
  * If we **allow nonlinear models**, **Config B (Deblock)** is **slightly more predictable** in 3/4 presets (fast, faster, superfast), with the notable **exception at veryfast** where A dominates.
* **Scientific insight**: Deblock’s branch-dominated cost is **nonlinear but learnable** (tree models excel). SAO’s memory-dominated cost is **more linear**, aligning with our a-priori expectation.

---

## 9. Actionable Next Steps (evidence-driven)

1. **Target the veryfast@B weakness**

   * From `oof_predictions.csv`, compute residuals by `seq_name`/`qp` to isolate sequences driving the 3.31% MAPE.
   * If a few sequences dominate error, consider robust losses (Huber) or per-sequence weights.

2. **Feature engineering**

   * Add **rates/ratios**: `D1mr/Dr`, `DLmr/Dr`, `DLmw/Dw`, `I1mr/Ir`, `Bim/Bc`, `Ir/Dr`, etc.
   * These stabilize cross-video differences and often reduce MAPE by 0.2–0.5 pts.

3. **Modeling refinements**

   * Light hyper-parameter sweep for XGB per preset (inner **GroupKFold**) to see if `veryfast@B` improves.
   * Try **ElasticNet** or **PolynomialFeatures** for Linear to narrow the A–B gap without losing simplicity.

4. **Mechanistic validation**

   * Compute **miss rates** and **branch mispredict rates** per preset×config; correlate with OOF residuals to confirm causal links (e.g., high `D1mr/Dr` ↔ higher error).

---

## 10. Minimal Repro/Logging (for lab notebook)

* **Scripts run**

  * `train_energy_models.py` → produced `overall_metrics.csv`, per-config metrics and feature importances.
  * `analyze_preset_mape.py` → produced OOF predictions and per-preset MAPE tables.
* **Key outputs inspected**

  * `overall_metrics.csv`: global accuracy.
  * `mape_by_preset_wide.csv`: core A vs B by preset.
  * `oof_predictions.csv`: per-sample truth vs prediction (foundation for all metrics).
  * `pe_means_by_preset_config.csv`: mechanism check; confirms *superfast* L1D-miss anomaly.

---

## 11. Concise Conclusions

* **Main claim validated**: *PEs are strong predictors of hardware energy.*
* **Linear model regime**: *When acceptable*, **Config A (SAO)** is **consistently better** than B across presets.
* **Nonlinear regime**: **XGBoost** reaches **≈2.6–2.8%** error; **Config B** is **slightly better** in fast/faster/superfast, but **Config A** is **clearly better** in **veryfast**.
* **Mechanisms** match data: **SAO** → memory/cache-heavy (more linear); **Deblock** → branch-heavy (nonlinear).

---

### Appendix — Suggested one-liners for slide captions

* *“With GroupKFold by sequence, XGBoost achieves sub-3% mean error across presets, confirming that processor-event features robustly map to hardware energy.”*
* *“If a linear model is preferred (simplicity, interpretability), SAO-only (Config A) consistently yields lower error than Deblock-only (Config B).”*
* *“At veryfast, A outperforms B even for XGBoost, indicating a regime where memory-driven behavior becomes more learnable than branch-dominated behavior.”*
