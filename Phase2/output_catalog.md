## 1. Folder: `01_time_energy/`

This folder contains the **global Energy–Time correlation results**.

### 1.1 `x265_energy_time.png`

* **Type:** Scatter plot (PNG)
* **Data source:** All rows where `encoder == "x265"`.
* **X-axis:** `t_process_single_s` (encoding time in seconds).
* **Y-axis:** `E_process_single_J` (energy in Joules).
* **Legend:** A single entry: `x265`.
* **Title:** `x265 Energy vs Time (r=...)`, where `r` is the Pearson correlation coefficient.
* **Purpose / usage:**

  * Visualizes how tightly software energy is linearly coupled to encoding time.
  * Used to support statements like “for x265, energy and time exhibit an almost perfect linear relationship”.

---

### 1.2 `NVIDIA_energy_time.png`

* **Type:** Scatter plot (PNG)
* **Data source:** All rows where `encoder` contains `"NVIDIA"` / `"nvenc"` / `"hw"` (hardware encoder).
* **X-axis:** `t_process_single_s`.
* **Y-axis:** `E_process_single_J`.
* **Legend:** A single entry: `NVIDIA`.
* **Title:** `NVIDIA Energy vs Time (r=...)`.
* **Purpose / usage:**

  * Shows the Energy–Time relationship for the hardware encoder alone.
  * Used to discuss deviations from a perfectly linear trend due to idle power, scheduling effects, or measurement noise.

---

### 1.3 `Combined_energy_time.png`

* **Type:** Scatter plot (PNG)
* **Data source:** All rows in the dataset (both `x265` and `NVIDIA`).
* **X-axis:** `t_process_single_s`.
* **Y-axis:** `E_process_single_J`.
* **Legend:**

  * `x265` – software encoder points.
  * `NVIDIA` – hardware encoder points.
* **Title:** `Combined Energy vs Time (r=...)`.
* **Purpose / usage:**

  * Gives a global view of the Energy–Time relationship across all encoders.
  * The combined Pearson `r` is used to argue that the **overall measurement pipeline** is stable and consistent, even though hardware has more variance.

---

## 2. Folder: `02_config_impact/`

This folder contains all outputs for **configuration impact analysis**, i.e., how **resolution** and **QP** affect energy.

### 2.1 `resolution_trend_x265.png`

* **Type:** Line plot (PNG)
* **Data source:** All rows where `encoder == "x265"`.
* **X-axis:** Discrete resolutions in order: `270p`, `360p`, `720p`, `1080p`, `4K`.
* **Y-axis:** Median `E_process_single_J` per `(resolution, preset)` bin.
* **Lines / legend:**

  * One line per x265 preset present in the data (`ultrafast`, `superfast`, `faster`, `veryfast`, `fast`, `medium`).
  * Legend entries: preset names.
* **Purpose / usage:**

  * Shows how software energy increases with resolution under different presets.
  * Used to support observations such as “slower presets (e.g., medium) have significantly steeper energy growth with resolution than faster presets”.

---

### 2.2 `resolution_trend_NVIDIA.png`

* **Type:** Line plot (PNG)
* **Data source:** All rows where `encoder` is NVIDIA/hardware.
* **X-axis:** `270p`, `360p`, `720p`, `1080p`, `4K`.
* **Y-axis:** Median `E_process_single_J` per `(resolution, preset)` bin.
* **Lines / legend:**

  * One line per hardware preset (`1`, `2`, `3`, `4`), if present.
* **Purpose / usage:**

  * Compares energy scaling with resolution across different hardware presets.
  * Typically shows much **flatter slopes** than the x265 plot, supporting statements like “hardware energy grows more gently with resolution due to fixed pipeline power”.

---

### 2.3 `qp_trend_x265_<preset>.png`

* **File name pattern:** `qp_trend_x265_ultrafast.png`, `qp_trend_x265_medium.png`, etc.
* **Type:** Line plot (PNG)
* **Data source:** Rows where `encoder == "x265"` and `preset == <that preset>`.
* **X-axis:** QP values `[22, 27, 32, 37]`.
* **Y-axis:** Median `E_process_single_J` per `(QP, resolution)` bin.
* **Lines / legend:**

  * One line per resolution (e.g., `270p`, `360p`, `720p`, `1080p`, `4K`).
  * Legend entries: resolution labels.
* **Purpose / usage:**

  * Characterizes how QP affects x265 energy at different resolutions under a fixed preset.
  * Used to show negative slopes (energy decreases with QP) and that this effect becomes stronger at higher resolutions.

---

### 2.4 `qp_trend_NVIDIA_<preset>.png`

* **File name pattern:** `qp_trend_NVIDIA_1.png`, `qp_trend_NVIDIA_2.png`, etc.
* **Type:** Line plot (PNG)
* **Data source:** Rows where `encoder` is NVIDIA and `preset == <that preset>`.
* **X-axis:** QP `[22, 27, 32, 37]`.
* **Y-axis:** Median `E_process_single_J` per `(QP, resolution)` bin.
* **Lines / legend:**

  * One line per resolution.
* **Purpose / usage:**

  * Shows that hardware energy is largely **insensitive to QP** (slopes close to zero).
  * Useful to highlight differences between software and hardware behavior: QP is an important factor for software energy but not for hardware.

---

### 2.5 `resolution_slopes.csv`

* **Type:** CSV table
* **Columns:**

  * `Config` – string identifier of the form:

    * `x265_<preset>` for software presets.
    * `NVIDIA_<preset>` for hardware presets.
  * `Slope` – numeric slope of energy vs. resolution index
    (*resolution index* = 0,1,2,3,4 corresponding to `270p`→`4K`).
* **Data meaning:**

  * For each `(encoder, preset)`, the script fits a **linear model** of the form
    `Energy ≈ a * resolution_index + b` and stores `a` in `Slope`.
* **Purpose / usage:**

  * Quantifies how strongly energy increases with resolution for each preset.
  * Used to derive numeric statements like “for x265-medium, the energy slope is much larger than for hardware preset 3”.

---

### 2.6 `qp_slopes.csv`

* **Type:** CSV table
* **Columns:**

  * `Config` – string identifier of the form:

    * `x265_<preset>_<resolution>`
    * `NVIDIA_<preset>_<resolution>`
  * `Slope` – numeric slope of energy vs. QP.
* **Data meaning:**

  * For each `(encoder, preset, resolution)` combination, the script fits a line:
    `Energy ≈ a * QP + b` and stores `a` as `Slope`.
* **Purpose / usage:**

  * Measures how energy changes when QP increases.
  * Negative slopes for x265 confirm the QP–energy trade-off; near-zero slopes for NVIDIA show QP has almost no influence on hardware energy.

---

## 3. Folder: `03_rd_re/`

This folder contains all **Rate–Distortion (R-D)** and **Rate–Energy (R-E)** curves, both combined and per encoder.

For each resolution `R` in `["270p", "360p", "720p", "1080p", "4K"]` **that actually exists in the data**, the following files may be present.

### 3.1 `RD_combined_<R>.png`

* **Example:** `RD_combined_1080p.png`
* **Type:** Scatter plot (PNG)
* **Data source:** All rows with `resolution == R`.
* **X-axis:** `bpp` (bits per pixel).
* **Y-axis:** `psnr_yuv` (overall YUV PSNR).
* **Legend:**

  * `x265` – software encoder points.
  * `NVIDIA` – hardware encoder points.
* **Purpose / usage:**

  * Direct R-D comparison at a fixed resolution.
  * Used to show which encoder achieves higher quality at the same bitrate (or lower bitrate at the same quality).

---

### 3.2 `RE_combined_<R>.png`

* **Example:** `RE_combined_4K.png`
* **Type:** Scatter plot (PNG)
* **Data source:** All rows with `resolution == R`.
* **X-axis:** `E_process_single_J` (energy).
* **Y-axis:** `psnr_yuv`.
* **Legend:**

  * `x265`, `NVIDIA`.
* **Purpose / usage:**

  * Shows how energy and quality trade off at a fixed resolution across encoders.
  * Supports statements about hardware being more energy-stable, or about software offering better R-D at potentially higher energy.

---

### 3.3 `RD_x265_<R>.png`

* **Example:** `RD_x265_720p.png`
* **Type:** Scatter plot (PNG)
* **Data source:** Rows where `encoder == "x265"` and `resolution == R`.
* **X-axis:** `bpp`.
* **Y-axis:** `psnr_yuv`.
* **Legend:**

  * Single entry: `x265 @ <R>`.
* **Purpose / usage:**

  * R-D behavior for the software encoder alone at a given resolution.
  * Useful when you want a clean R-D plot without hardware points, e.g., to illustrate internal preset differences or to overlay BD-curves in later processing.

---

### 3.4 `RE_x265_<R>.png`

* **Example:** `RE_x265_1080p.png`
* **Type:** Scatter plot (PNG)
* **Data source:** `encoder == "x265"`, `resolution == R`.
* **X-axis:** `E_process_single_J`.
* **Y-axis:** `psnr_yuv`.
* **Legend:**

  * `x265 @ <R>`.
* **Purpose / usage:**

  * Energy vs. quality behavior for software only.
  * Useful for illustrating how energy-efficient different presets are if you post-process or annotate the points.

---

### 3.5 `RD_NVIDIA_<R>.png`

* **Example:** `RD_NVIDIA_4K.png`
* **Type:** Scatter plot (PNG)
* **Data source:** `encoder` is NVIDIA / hardware, `resolution == R`.
* **X-axis:** `bpp`.
* **Y-axis:** `psnr_yuv`.
* **Legend:**

  * `NVIDIA @ <R>`.
* **Purpose / usage:**

  * Hardware-only R-D curves for a given resolution.
  * Useful to show limited preset differentiation in R-D space, or to compare with x265 in textual discussion.

---

### 3.6 `RE_NVIDIA_<R>.png`

* **Example:** `RE_NVIDIA_270p.png`
* **Type:** Scatter plot (PNG)
* **Data source:** NVIDIA-only rows, `resolution == R`.
* **X-axis:** `E_process_single_J`.
* **Y-axis:** `psnr_yuv`.
* **Legend:**

  * `NVIDIA @ <R>`.
* **Purpose / usage:**

  * Hardware-only R-E behavior at one resolution.
  * Often used to demonstrate that energy consumption is relatively stable with QP, while PSNR changes.

---

## 4. Folder: `04_modeling_hw/`

All results in this folder are for **NVIDIA hardware only**
(i.e., rows where `encoder` is the hardware encoder, 768 samples in your dataset).

### 4.1 `hw_linear_model_summary.csv`

**What it is:**
A CSV table summarizing the performance of all linear models tested on the NVIDIA-only subset.

**Columns:**

* `Model` – name of the feature set used:

  * `Time_only`
  * `BPP_only`
  * `QP_only`
  * `Resolution_only`
  * `Multi_feature`
* `R2` – coefficient of determination on all NVIDIA samples (n = 768)
* `MAPE(%)` – Mean Absolute Percentage Error in percent
* `RMSE` – Root Mean Squared Error in Joules

**Actual content (rounded):**

| Model           | R2     | MAPE(%) | RMSE (J) |
| --------------- | ------ | ------- | -------- |
| Time_only       | 0.7917 | 51.99   | 1.592    |
| BPP_only        | 0.0590 | 121.55  | 3.384    |
| QP_only         | 0.0006 | 127.55  | 3.488    |
| Resolution_only | 0.8863 | 18.51   | 1.176    |
| Multi_feature   | 0.9551 | 12.81   | 0.740    |

**How to use it in analysis:**

* Shows that:

  * **Time-only model** captures the main trend but is still quite inaccurate (MAPE ≈ 52%).
  * **BPP-only** and **QP-only** are very weak predictors for hardware energy (very low R², very high MAPE).
  * **Resolution-only** already provides a strong signal (R² ≈ 0.89, MAPE ≈ 18.5%).
  * **Multi-feature** (time + bpp + QP + resolution) is the best linear model here (R² ≈ 0.96, MAPE ≈ 12.8%, RMSE ≈ 0.74 J).
* This table is your primary quantitative evidence for:

  * “Time is important but not sufficient alone”
  * “Resolution is a dominant structural factor”
  * “Simple linear models with a small number of features already achieve reasonably accurate prediction for NVIDIA hardware energy.”

---

### 4.2 `pred_Time_only.csv`

**What it is:**

* A CSV containing **per-sample predictions** of the NVIDIA hardware energy using a linear regression with only **time** as input.

**Shape and columns:**

* Rows: 768 (all NVIDIA samples)
* Columns:

  * `True_Energy(J)` – ground truth energy (`E_process_single_J`)
  * `Pred_Energy(J)` – predicted energy from the `Time_only` model

**Usage:**

* To create scatter plots of `True_Energy` vs `Pred_Energy` for the Time-only model.
* To analyze residuals (prediction error vs. time, vs. resolution, etc.).
* To visually support the statement based on the summary:

  * R² = 0.7917, MAPE ≈ 51.99%, RMSE ≈ 1.592 J
    → “Time captures the trend but leaves large relative errors for many samples.”

---

### 4.3 `pred_BPP_only.csv`

**What it is:**

* Predictions from a linear model that uses only **bpp** as the input feature.

**Shape and columns:**

* Rows: 768
* Columns:

  * `True_Energy(J)`
  * `Pred_Energy(J)` – from the `BPP_only` model

**Global performance (from summary):**

* R² = 0.0590
* MAPE ≈ 121.55%
* RMSE ≈ 3.384 J

**Usage:**

* To explicitly show that bpp alone has almost no predictive power for hardware energy:

  * Very low R².
  * Extremely high MAPE.
* Useful for supporting a negative result:

  > “Bitrate per pixel (bpp) is not a suitable single-feature predictor for NVENC energy consumption.”

---

### 4.4 `pred_QP_only.csv`

**What it is:**

* Predictions from a linear model that uses only **QP** as the input.

**Shape and columns:**

* Rows: 768
* Columns:

  * `True_Energy(J)`
  * `Pred_Energy(J)` – from the `QP_only` model

**Global performance:**

* R² = 0.0006
* MAPE ≈ 127.55%
* RMSE ≈ 3.488 J

**Usage:**

* Strong evidence that **QP alone is almost useless** for predicting NVIDIA hardware energy:

  * R² essentially zero.
  * Huge MAPE.
* This matches your qualitative conclusion that NVENC energy is **almost independent of QP** and instead dominated by pipeline and resolution-related factors.

---

### 4.5 `pred_Resolution_only.csv`

**What it is:**

* Predictions from a linear model that uses only **resolution** (one-hot encoded) as input.

**Shape and columns:**

* Rows: 768
* Columns:

  * `True_Energy(J)`
  * `Pred_Energy(J)` – from the `Resolution_only` model

**Global performance:**

* R² = 0.8863
* MAPE ≈ 18.51%
* RMSE ≈ 1.176 J

**Usage:**

* Shows that resolution by itself explains a **large proportion of the variance** in hardware energy.

* Good for supporting statements like:

  > “Resolution is a primary determinant of NVENC energy consumption, even without time or QP features.”

* In figures, this file can be used to:

  * Plot residuals vs. resolution to see if some resolutions are systematically under/over-estimated.
  * Build a bar chart of mean prediction error per resolution.

---

### 4.6 `pred_Multi_feature.csv`

**What it is:**

* Predictions from the **best linear model** tested here:
  features = `[time, bpp, QP, resolution(one-hot)]`.

**Shape and columns:**

* Rows: 768
* Columns:

  * `True_Energy(J)`
  * `Pred_Energy(J)` – from the `Multi_feature` model

**Global performance:**

* R² = 0.9551
* MAPE ≈ 12.81%
* RMSE ≈ 0.740 J

**Usage:**

* This is the **main result** for your linear hardware energy model:

  * It shows that even a simple linear regression with a small number of physically interpretable features can predict NVENC energy with low error.
* Suitable for:

  * Final “prediction vs. ground truth” scatter plot (points near the diagonal).
  * Quantitative claims in your thesis, e.g.:

    > “The multi-feature linear model achieves R² ≈ 0.96 and MAPE ≈ 12.8% on all NVIDIA samples, significantly improving over single-feature baselines such as Time-only or Resolution-only.”






eference these filenames and metrics directly.
