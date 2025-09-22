# Part 1: Data Analysis Summary

This section aims to complete the **energy consumption and encoding time relationship analysis** for **HEVC Intra-Coding software (x265) and hardware (NVIDIA Jetson platform)** encoders under different configurations. The analysis is based on cleaned and verified data.

---

## Data Analysis Content

According to the established research plan, the first part of the data analysis is divided into three subtasks:

1. **Overall Analysis**

   * Plot scatterplots of energy consumption vs. encoding time for all data points.
   * Plot separately: x265-only, HW-only, and combined.
   * Distinguish point shapes by encoder type, and color by preset within each type.

2. **Per-Resolution Analysis**

   * Resolution set: `270p, 360p, 720p, 1080p, 2k, 4K`.
   * For each resolution, plot: x265-only, HW-only, and combined.
   * The aim is to visually observe how the relationship between time and energy changes as video size increases.

3. **Per-Preset Analysis**

   * **x265 presets**: `ultrafast, superfast, faster, veryfast, fast, medium`.
   * **HW presets**: `1, 2, 3, 4`.
   * For each preset, plot scatterplots of energy consumption vs. time.
   * Examine correlations under different optimization levels/hardware gears.

All plots support both **linear and logarithmic axes (--logx, --logy)** to facilitate trend presentation across different magnitudes.

---

## Example Usage

Run in Windows PowerShell:

```powershell
# Linear axes
python linshi.py --csv all_dataset.csv --outdir ./figures

# Logarithmic X axis
python analyze_energy_time_relations.py --csv all_dataset.csv --outdir ./figures --logx

# Logarithmic Y axis
python analyze_energy_time_relations.py --csv all_dataset.csv --outdir ./figures --logy

# Log-log axes (both X and Y)
python analyze_energy_time_relations.py --csv all_dataset.csv --outdir ./figures --logx --logy
```

---

## Generated Folder Structure

After running, images are saved to the `./figures/` directory, organized by analysis category:

```
figures/
├── overall/
│   ├── overall_x265.png / .pdf
│   ├── overall_hw.png / .pdf
│   └── overall_combined.png / .pdf
├── per_resolution/
│   ├── res_270p_x265.png / .pdf
│   ├── res_270p_hw.png / .pdf
│   ├── res_270p_combined.png / .pdf
│   ├── res_360p_*.png / .pdf
│   ├── res_720p_*.png / .pdf
│   ├── res_1080p_*.png / .pdf
│   └── res_4K_*.png / .pdf
└── per_preset/
    ├── preset_x265_ultrafast.png / .pdf
    ├── preset_x265_superfast.png / .pdf
    ├── preset_x265_faster.png / .pdf
    ├── preset_x265_veryfast.png / .pdf
    ├── preset_x265_fast.png / .pdf
    ├── preset_x265_medium.png / .pdf
    ├── preset_hw_1.png / .pdf
    ├── preset_hw_2.png / .pdf
    ├── preset_hw_3.png / .pdf
    └── preset_hw_4.png / .pdf
```

---

## Results

### Overall

* **x265**: n=1152, r≈0.9994 → nearly perfect linear relationship.
* **HW**: n=768, r≈0.8898 → strong correlation but with fluctuations.
* **Combined**: n=1920, r≈0.9978 → overall stable, proving the reliability of the measurement system.

### Per-Resolution (HW section)

* **270p**: r≈0.20 → no correlation, data needs to be retested.
* **360p**: r≈0.89 → decent, but with minor outliers.
* **720p**: r≈0.99 → very stable.
* **1080p**: r≈0.62 → large deviation, data needs to be retested.
* **4K**: r≈0.92 → strong correlation, but slightly weaker than software.
* **x265**: for all resolutions r>0.95, very stable.

### Per-Preset

* **All x265 presets**: all r≈0.9993–0.9995 → optimization level does not affect the linearity of the energy-time relationship.
* **HW presets**:

  * Preset 1: r≈0.94 → good
  * Preset 2: r≈0.86 → weakest, with anomalies
  * Preset 3: r≈0.94 → good
  * Preset 4: r≈0.94 → good

---

## Analysis Summary

1. **Software side (x265)**: For all resolutions and presets, energy consumption and encoding time show an almost perfect linear correlation; linear modeling can be directly adopted.
2. **Hardware side (HW)**: Overall correlation is high, but performance is poor at low (270p) and mid (1080p) resolutions and with Preset=2, indicating significant effects from idle power and hardware scheduling mechanisms.
3. **Academic insights**:

   * Software energy prediction can be directly regressed from time;
   * Hardware energy modeling requires incorporating resolution, preset, and idle power compensation, and, if necessary, more complex regression or machine learning models;
   * Logarithmic axis analysis verifies consistency across scales, suitable for paper figures.

---

✅ The above completes the first part of the data analysis summary, laying the foundation for subsequent **analysis of coding configuration impact on energy (resolution trends, QP analysis)** and **software-hardware comparison (R-D, R-E, BD analysis)**.

# Part 2: Analysis of the Impact of Coding Configuration on Energy Consumption

The goal of this section is to study how **coding configuration parameters (Resolution, QP, Preset)** affect the energy performance of the encoder. Through trend plots and slope statistics, the variation patterns of energy consumption under different parameters are revealed.

---

## Resolution Impact

### Method

* With QP and preset fixed, the x-axis is resolution (270p → 360p → 720p → 1080p → 4K), and the y-axis is energy consumption (J).
* Software and hardware are plotted separately, with different colors for presets inside each.

### Results

* **x265**:

  * All presets show positive slopes—energy increases significantly with resolution.
  * Slower presets (e.g., medium) have the largest slope (≈629), fastest presets (ultrafast) the smallest (≈156).
  * Indicates that resolution impacts energy more for complex presets.

* **HW**:

  * All presets have small slopes (≈2–3), energy increases with resolution but the magnitude is limited.
  * Differences between presets exist but are not significant (preset 1≈2.0 vs preset 3≈2.95).
  * Indicates that fixed power in the hardware pipeline is dominant, showing energy efficiency advantages at high resolution.

### Conclusion

* Software energy is highly sensitive to resolution; hardware energy increases more gently.
* This matches expectations: software algorithm complexity is exponentially affected by resolution, hardware is closer to linear throughput.

---

## QP Impact

### Method

* With resolution and preset fixed, the x-axis is QP (22, 27, 32, 37), and the y-axis is energy consumption (J).
* Each preset is plotted separately, with different lines for each resolution.

### Results

* **x265**:

  * All curves have negative slopes, indicating that energy decreases as QP increases.
  * The decrease correlates positively with resolution:

    * At 270p, slope≈-2 ~ -9
    * At 1080p, slope≈-36 ~ -154
    * At 4K, slope≈-98 ~ -507
  * Slower presets decrease faster (medium at 4K, slope≈-507, nearly 5x that of ultrafast).

* **HW**:

  * All slopes are near zero (≈-0.3 ~ +0.02), QP has almost no effect on energy.
  * Some cases even show positive slopes (e.g., preset=2 @270p slope≈+0.018), possibly due to measurement noise or pipeline fixed power being dominant.

### Conclusion

* Software energy is significantly dependent on QP, reflecting a quality–energy trade-off.
* Hardware energy is nearly independent of QP, indicating energy is mainly determined by fixed pipeline, not encoding complexity.

---

## Folder Structure

```
figures/
├── resolution_impact/
│   ├── x265_resolution_trends.png / .pdf
│   └── HW_resolution_trends.png / .pdf
└── qp_impact/
    ├── x265_qp_trends_preset_ultrafast.png / .pdf
    ├── x265_qp_trends_preset_superfast.png / .pdf
    ├── x265_qp_trends_preset_faster.png / .pdf
    ├── x265_qp_trends_preset_veryfast.png / .pdf
    ├── x265_qp_trends_preset_fast.png / .pdf
    ├── x265_qp_trends_preset_medium.png / .pdf
    ├── HW_qp_trends_preset_1.png / .pdf
    ├── HW_qp_trends_preset_2.png / .pdf
    ├── HW_qp_trends_preset_3.png / .pdf
    └── HW_qp_trends_preset_4.png / .pdf
```

---

## Comprehensive Summary

1. **Resolution impact**:

   * x265 → energy increases significantly with resolution, slower presets have larger slopes.
   * HW → energy increases slowly with resolution, much less than on the software side.
2. **QP impact**:

   * x265 → increasing QP significantly reduces energy, especially at high resolutions and complex presets.
   * HW → energy hardly changes with QP, QP is not a significant factor.
3. **Research implications**:

   * Software modeling can use QP and resolution as key variables.
   * Hardware modeling needs to emphasize resolution, preset, and idle power compensation, not QP.
   * Results clearly reflect software-hardware architectural differences: software energy is complexity-driven, hardware energy is pipeline-dominated.

---
# Part 3: Software vs. Hardware Encoder Performance Comparison

This section is the core of the paper, focusing on quantitatively comparing the performance differences between the **x265 software encoder** and the **NVIDIA Jetson hardware encoder**, with standardized results based on the **BD analysis method**.

---

## Data Standardization and BD Analysis Preparation

* **Extract core metrics**: PSNR (psnr\_yuv), bitrate (bpp), energy consumption (E\_process\_single\_J).
* **Ensure fairness**: unified QP settings (22, 27, 32, 37), consistent resolution.
* **Data aggregation**: use the median value of each (encoder, preset, resolution, qp) as the analysis point.

---

## Rate-Distortion (R-D) and Rate-Energy (R-E) Analysis

* **R-D curve (PSNR vs bpp)**: shows bitrate differences between different encoders/presets at the same quality.
* **R-E curve (PSNR vs Energy)**: shows energy consumption differences between different encoders/presets at the same quality.

**Analysis results**:

* **R-D**: x265 significantly outperforms HW at medium and high resolutions, with clear preset differences; HW shows little difference between presets.
* **R-E**: HW is more stable in energy efficiency, energy does not change with QP, showing throughput optimization characteristics.

---

## BD Analysis Method

* **Anchor**: hardware preset **HW-4 (slow)**.
* **Comparison targets**: all x265 presets (ultrafast → medium) + other HW presets (1, 2, 3).
* **Output metrics**:

  * **BD-Rate (%)**: bitrate difference at the same PSNR; negative values are better.
  * **BD-PSNR (dB)**: quality difference at the same bitrate; positive values are better.

---

## BD Analysis Results

### Cross-Resolution Overall Mean

* **x265-medium/faster/fast/veryfast**: BD-Rate ≈ −38.7% ~ −38.9%, BD-PSNR ≈ +2.47 ~ +2.49 dB.
* **x265-superfast**: BD-Rate ≈ −37.80%, BD-PSNR ≈ +2.40 dB.
* **x265-ultrafast**: BD-Rate ≈ −25.33%, BD-PSNR ≈ +1.43 dB.
* **HW-3**: identical to HW-4 (0%, 0 dB).
* **HW-2**: BD-Rate ≈ +3.45%, BD-PSNR ≈ −0.19 dB.
* **HW-1**: BD-Rate ≈ +6.52%, BD-PSNR ≈ −0.33 dB.

### Resolution Trends (using x265-medium as an example)

* 270p: BD-Rate −10.44%, BD-PSNR +0.87 dB.
* 360p: BD-Rate −29.94%, BD-PSNR +2.37 dB.
* 720p: BD-Rate −44.90%, BD-PSNR +2.96 dB.
* 1080p: BD-Rate −47.15%, BD-PSNR +2.91 dB.
* 4K: BD-Rate −62.05%, BD-PSNR +3.33 dB.

### Anomalies

* **x265-ultrafast @ 270p**: BD-Rate +11.32%, BD-PSNR −0.66 dB, indicating that at low resolution and ultra-fast preset, performance is worse than HW slow.
* As resolution increases to 4K, this preset becomes significantly superior (BD-Rate −56.97%, BD-PSNR +3.00 dB).

---

## Folder Structure

```
figures/
├── rd_curves/
│   ├── rd_curve_x265_vs_hw_270p.png / .pdf
│   ├── rd_curve_x265_vs_hw_360p.png / .pdf
│   ├── rd_curve_x265_vs_hw_720p.png / .pdf
│   ├── rd_curve_x265_vs_hw_1080p.png / .pdf
│   └── rd_curve_x265_vs_hw_4k.png / .pdf
├── re_curves/
│   ├── re_curve_x265_vs_hw_270p.png / .pdf
│   ├── re_curve_x265_vs_hw_360p.png / .pdf
│   ├── re_curve_x265_vs_hw_720p.png / .pdf
│   ├── re_curve_x265_vs_hw_1080p.png / .pdf
│   └── re_curve_x265_vs_hw_4k.png / .pdf
└── bd_summary/
    ├── bd_summary_overall.csv
    └── bd_per_resolution.csv
```

---

## Comprehensive Analysis Conclusions

1. **Software side (x265)**:

   * Significant advantages in R-D, especially at medium and high resolutions, with bitrate savings up to 40–60% and quality improvement of 2–3 dB.
   * Energy consumption is highly sensitive to resolution and preset.

2. **Hardware side (HW)**:

   * R-D efficiency is inferior to x265; HW-3 is fully equivalent to HW-4, HW-1/2 are slightly worse.
   * Energy consumption is very stable and not affected by QP.

3. **Comparison insights**:

   * If the goal is **compression efficiency (R-D)** → recommend x265 (medium/faster/fast/veryfast).
   * If the goal is **energy efficiency/throughput (R-E)** → recommend HW, and HW-3 and HW-4 are interchangeable.
   * Avoid x265-ultrafast in low-resolution scenarios to avoid losing efficiency advantages.
# Part 4: Establishment and Validation of Hardware Energy Consumption Prediction Model

This section is the final goal of the study, aiming to establish a prediction model for **hardware encoder (NVIDIA Jetson platform NVENC) energy consumption** based on observable features of the **software encoder (x265)**, and to verify its accuracy.

---

## Model Input Features

Model input features come from software encoder behavior, mainly including:

* **Encoding time (sw\_time\_s)**: time taken by the software side to encode a video segment.
* **Bitrate feature (sw\_bpp)**: bits per pixel output by the software side.
* **Encoding configuration parameters**: Resolution (270p, 360p, 720p, 1080p, 4K), QP (22, 27, 32, 37), preset (x265: ultrafast–medium, HW: 1–4).

The target variable is **hardware energy consumption (E\_hw\_J)**.

---

## Modeling Methods

The modeling process is divided into three categories:

1. **Univariate modeling**

   * **Time→Energy**: fit the relationship between hardware energy and software time.
   * **bpp→Energy**: fit the relationship between hardware energy and software output bitrate.

2. **Polynomial Regression**

   * Apply quadratic and polynomial extensions to univariate models to explore nonlinear improvements.

3. **Multivariate modeling**

   * Combine multiple features: `sw_time_s + sw_bpp + resolution + QP + Preset`.
   * Test various algorithms: linear regression, ElasticNet, random forest (RF), gradient boosting regression (GBR), XGBoost (XGB).

Model validation metrics:

* **R²** (coefficient of determination)
* **MAPE** (mean absolute percentage error)
* **RMSE** (root mean square error)

---

## Modeling Results

### Univariate Models

* **Time→Energy**:

  * Linear regression: R²≈0.74, MAPE≈53% → insufficient accuracy.
  * Polynomial (2nd/3rd order): R²≈0.84, MAPE≈25% → some improvement but still not ideal.
  * Tree models (GBR/RF/XGB): R²≈0.89, MAPE≈18% → significant improvement, but still higher than the paper's target (<5%).

* **bpp→Energy**:

  * Linear/polynomial: R² <0.15, MAPE>100% → almost useless.
  * GBR: R²≈0.77, MAPE≈49%.
  * RF/XGB: R²≈0.89, MAPE≈22–23% → some improvement, but far inferior to the Time feature.

👉 Conclusion: **Time is the most critical feature for univariate prediction**; bpp alone cannot effectively predict energy.

---

### Multivariate Models

After introducing resolution, QP, and preset, model performance improves greatly:

* MV-Linear / MV-ElasticNet: R²≈0.94, MAPE≈20%.
* MV-GBR: R²≈0.997, MAPE≈3.16%.
* MV-RF: R²≈0.986, MAPE≈2.89%.
* **MV-XGB: R²≈0.9998, MAPE≈1.28% → Best model**.

👉 Multivariate XGBoost outperforms all other candidates, achieving almost perfect prediction with an average error of only 1.3%, far below the paper's 5% accuracy target.

---

## Visualization Results

### Scatterplots

* **HW Energy vs SW Time**: energy increases with software encoding time; the higher the resolution, the more energy consumed. Each HW preset shows a parallel distribution, indicating time is the dominant factor.
* **HW Energy vs SW bpp**: scatter is more dispersed; the univariate relationship is weak, but as an auxiliary feature in multivariate models, it improves overall accuracy.

### Fitting Performance

* GBR/RF/XGB fit curves closely match actual data.
* MV-XGB can stably predict across different resolutions and presets, exhibiting excellent generalization.

---

## Analysis Summary

1. **Univariate results**: time feature reflects energy trend well, but error remains high; bpp alone is ineffective.
2. **Multivariate results**: time + resolution + QP + Preset combination greatly improves model accuracy.
3. **Best model**: XGBoost multivariate model, R²≈0.9998, MAPE≈1.28%, meeting the paper’s target of <5% error.
4. **Academic significance**:

   * There is a highly modelable relationship between software encoding behavior and hardware energy consumption;
   * Time dominates energy, with resolution/configuration as correction factors;
   * Although bpp is not a main factor, its combination in multivariate models can further optimize performance.

---

✅ At this point, the fourth part: **establishment and validation of the hardware energy consumption prediction model** is complete. The study successfully demonstrates the feasibility and high accuracy of predicting hardware energy consumption using software features, contributing a core modeling result to the paper.

---

✅ At this point, the third part—software vs. hardware encoder performance comparison—is complete, forming a full analysis loop from **R-D curve → R-E curve → BD table → comprehensive conclusions**, laying the groundwork for subsequent chapters on energy modeling and more.
