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

📌 **hw_linear_model_summary.csv 数据如下（系统读取）**：

| Model              | R2     | MAPE(%) | RMSE (J) |
| ------------------ | ------ | ------- | -------- |
| Time_only          | 0.7917 | 51.99   | 1.592    |
| BPP_only           | 0.0590 | 121.55  | 3.384    |
| QP_only            | 0.0006 | 127.55  | 3.488    |
| Resolution_px_only | 0.7763 | 52.93   | 1.650    |
| Time_Resolution_px | 0.8786 | 41.29   | 1.216    |
| Multi_feature      | 0.8788 | 41.43   | 1.215    |


---

## ✅ Section 4 — Hardware Energy Modeling Output Catalog

📌 *All results here are generated exclusively from NVIDIA encoder samples (n = 768).*

---

### **4.1 `hw_linear_model_summary.csv`**

Performance statistics of all energy prediction models tested.

| Model                  | Input Features                       |         R² |  MAPE (%) |  RMSE (J) | Interpretation                          |
| ---------------------- | ------------------------------------ | ---------: | --------: | --------: | --------------------------------------- |
| **Time_only**          | Encoding time (`t_process_single_s`) | **0.7917** | **51.99** | **1.592** | Captures trend but large residual error |
| **BPP_only**           | Bitrate per pixel (`bpp`)            |     0.0590 |    121.55 |     3.384 | Very weak predictor                     |
| **QP_only**            | Quantization parameter (`qp`)        |     0.0006 |    127.55 |     3.488 | Essentially no correlation              |
| **Resolution_px_only** | Pixel count (`width × height`)       |     0.7763 |     52.93 |     1.650 | Resolution matters, but not linear      |
| **Time_Resolution_px** | Pixel count (`width × height`)+Encoding time (`t_process_single_s`) |     0.8786 |     41.29 |     1.216 | Resolution matters, but not linear      |
| **Multi_feature**      | Time + BPP + QP + Pixel count        | **0.8788** | **41.43** | **1.215** | Best linear model among tested          |

**Conclusion:**

> Time and resolution dominate hardware energy behavior.
> QP and BPP have little predictive value for NVENC energy.

---

### **4.2 `pred_Time_only.csv`**

| Column           | Meaning                             |
| ---------------- | ----------------------------------- |
| `True_Energy(J)` | Ground truth measured NVIDIA energy |
| `Pred_Energy(J)` | Prediction using only encoding time |

**Based on summary:**

* MAPE **51.99%** → large distribution gaps
* Used to show **time ≠ full predictor** for hardware

---

### **4.3 `pred_BPP_only.csv`**

| Statistic |   Value |
| --------- | ------: |
| R²        |  0.0590 |
| MAPE      | 121.55% |
| RMSE      | 3.384 J |

**Conclusion:**

> bpp is **not** meaningful for hardware energy estimation.

---

### **4.4 `pred_QP_only.csv`**

| Statistic |   Value |
| --------- | ------: |
| R²        |  0.0006 |
| MAPE      | 127.55% |
| RMSE      | 3.488 J |

**Conclusion:**

> QP has **almost zero** explanatory power for NVENC energy.

---

### **4.5 `pred_Resolution_px_only.csv`**

| Statistic |   Value |
| --------- | ------: |
| R²        |  0.7763 |
| MAPE      |  52.93% |
| RMSE      | 1.650 J |

**Interpretation:**

* Resolution matters, but **pixel count alone is still insufficient**
* Indicates **non-linear scaling** and **pipeline power efficiencies**

---

### **4.6 `pred_Multi_feature.csv`**

| Statistic |       Value |
| --------- | ----------: |
| R²        |  **0.8788** |
| MAPE      |  **41.43%** |
| RMSE      | **1.215 J** |

**Interpretation:**

> The multi-feature model performs best among linear models,
> but remaining error suggests the need for **non-linear modeling**
> (e.g., tree-based regression) for higher precision.
