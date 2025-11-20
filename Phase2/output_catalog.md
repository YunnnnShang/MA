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

## **4. Folder: `04_modeling_hw/`**

*(NVIDIA Hardware-Only Energy Modeling)*

This folder contains all modeling results derived **exclusively from NVIDIA hardware encoder samples**
(`encoder == "NVIDIA"`, 768 rows in the dataset).

All features used in this section are physically interpretable properties of the encoding task.

---

### **4.1 `hw_linear_model_summary.csv`**

**What it contains**
A performance comparison of 5 linear regression models, each using a different subset of features.

**Columns**

* `Model` — feature set used
* `R2` — coefficient of determination
* `MAPE(%)` — Mean Absolute Percentage Error (%)
* `RMSE` — Root Mean Squared Error (J)

**Actual results**

| Model                  |         R2 |   MAPE(%) |  RMSE (J) |
| ---------------------- | ---------: | --------: | --------: |
| Time_only              |     0.7917 |     51.99 |     1.592 |
| BPP_only               |     0.0590 |    121.55 |     3.384 |
| QP_only                |     0.0006 |    127.55 |     3.488 |
| **Resolution_px_only** | **0.7763** | **52.93** | **1.650** |
| **Multi_feature**      | **0.8788** | **41.43** | **1.215** |

**Usage**

* This file is the **main results table** for hardware energy modeling in the thesis.
* It directly supports analytical claims such as:

  > “Time and resolution strongly influence NVENC energy, while QP and bpp show minimal predictive power.”

---

### **4.2 `pred_Time_only.csv`**

**Purpose**
Quantifies the prediction error when **encoding time** (`t_process_single_s`) is the only feature.

**Content**

* `True_Energy(J)`
* `Pred_Energy(J)`

**Interpretation**

* Captures general trend, but high error → strong **unmodeled complexity variance**.

---

### **4.3 `pred_BPP_only.csv`**

**Purpose**
Evaluates **bitrate density (bpp)** as a predictor.

**Content**

* `True_Energy(J)`
* `Pred_Energy(J)`

**Interpretation**

* Very low R² & very high MAPE
  → bpp **is not useful** for hardware energy prediction.

---

### **4.4 `pred_QP_only.csv`**

**Purpose**
Quantifies energy predictability using **QP alone**.

**Content**

* `True_Energy(J)`
* `Pred_Energy(J)`

**Interpretation**

> “QP has negligible impact on NVENC energy.”
> (R² ≈ 0 → essentially random with respect to energy.)

---

### **4.5 `pred_Resolution_px_only.csv`**

*(Replaces former “Resolution_only” entry)*

**Feature definition**

```
resolution_pixels = width × height
```

Example mapping:

| Resolution | resolution_pixels |
| ---------- | ----------------: |
| 270p       |           129,600 |
| 720p       |           921,600 |
| 1080p      |         2,073,600 |
| 4K         |         8,294,400 |

**Interpretation**

* Resolution is a **primary factor**, but
* Linear scaling with pixel count **does not fully capture** real NVENC energy behavior
  (non-linear efficiency, pipeline utilization, power gating effects)

---

### **4.6 `pred_Multi_feature.csv`**

**Feature set**

```
[
  t_process_single_s,
  bpp,
  qp,
  resolution_pixels
]
```

**Usage**

* Best model among tested linear setups
* Used for scatter plots of predicted vs. actual energy
* Supports concluding statements:

> “Pixel-based multi-feature linear modeling achieves noticeably lower error than any single-feature baseline.”

---

## **Section 4 Summary Statement (can be copied into thesis)**

> All regression results consistently indicate that NVENC energy is primarily determined by processing time and the amount of pixel data being processed, while quantization and bitrate parameters play only a minor role. The multi-feature linear model yields the best performance (R²≈0.88, MAPE≈41%), showing that a small, interpretable feature set can capture most but not all of the variability in hardware energy consumption.
