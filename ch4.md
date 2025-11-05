# Chapter 4: Methodology

## 4.1. Experimental Setup and Test Conditions

This chapter details the experimental environments, measurement tools, and test conditions to ensure reproducibility.

### 4.1.1. Software Encoder Testbeds

Two software platforms are used, serving different purposes across stages:

#### 4.1.1.1. Lab Testbed for Initial Characterization

**Platform description:**

* **Hardware:** Intel(R) Core(TM) i5-10505 CPU @ 3.20GHz (6 cores)
* **Purpose:** For `Phase 1` and `Phase 2`—initial RD performance tests, energy–time analysis, and software-side baseline data collection
* **OS:** Linux (specific distribution)

**Tasks:**

* RD performance tests of the x265 software encoder (130-frame encodes)
* Software encoder energy measurement using Intel RAPL
* Analysis of the relationship between encoding time and energy
* BD-Metrics computation and performance comparison

**Rationale:** This platform provides a stable local environment for rapid iteration/debugging—suitable for baseline testing and early-stage data analysis.

#### 4.1.1.2. HPC Cluster for Deep Profiling

**Platform description:**

* **Cluster:** FAU LNT Intel HPC Cluster [cite: `Phase4 Modeling based on Processor Event/Phase 4 – Valgrind-Based Software Encoder Energy Modeling .md`, Line 22]
* **Scheduler:** SLURM (Simple Linux Utility for Resource Management) [cite: `Phase4 Modeling based on Processor Event/Roadmap.md`, Line 48]
* **CPU architectures:** Multi-node, multi-core; supports both Intel and AMD
* **Parallel execution:** `OMP_NUM_THREADS=8`, `--cpus-per-task=8` (example settings; not enforced, do not constrain concurrency)

**Purpose:** Used only for **compute-intensive** processor-event profiling in `Step 5` (Phase 4) (`Valgrind` and `perf`).

**Scale:**

* Valgrind: 960+ runs (48 sequences × 10 presets × 4 QPs × 2 configs)
* Perf: 1,920 CSVs (2 CPU architectures × 2 feature sets × 480 configs) [cite: `Phase4 Modeling based on Processor Event/Valgrind-Based Energy Modeling and Cross-Validation with Perf.md`, Line 58]

**Rationale:** Processor-event profiling—especially Valgrind—incurs very high runtime overhead (10×–100×), requiring parallelization to complete at scale in realistic time. HPC + SLURM make these workloads feasible.

### 4.1.2. Hardware Encoder Testbed

**Platform:** NVIDIA Jetson Orin NX 8GB module on reComputer J401 carrier board [cite: `Phase 1/HW/NVIDIA Jetson HEVC Hardware Encoder_ Rate-Distortion Test Workflow & Findings.md`, Line 17]

**Hardware:**

* **SoC:** NVIDIA Orin NX (8GB)
* **Carrier:** reComputer J401
* **Network:** Gigabit Ethernet (RJ-45), static IP: 192.168.178.1 [cite: `Phase 1/HW/NVIDIA Jetson HEVC Hardware Encoder_ Rate-Distortion Test Workflow & Findings.md`, Line 28]
* **Power:** Standard DC adapter

**Energy instrumentation:**

* **ZES ZIMMER LMG611 power analyzer:** System-level energy measurement for the hardware encoder
* **Connection:** LMG611 in series with Jetson’s main power rail; serial (`/dev/ttyUSB0`, 115200 baud) [cite: `Phase 1/HW/HW_energy_measurement.py`, Line 24]
* **Accuracy:** High-precision energy integration and power measurement; Wh↔J conversion supported

**Remote control:**

* **SSH:** Remote experiment control via `or16ixuv@192.168.178.1` [cite: `Phase 1/HW/NVIDIA Jetson HEVC Hardware Encoder_ Rate-Distortion Test Workflow & Findings.md`, Line 57]
* **Networking:** Static IP to ensure stable, reliable connectivity

### 4.1.3. Measurement and Profiling Instrumentation

A full toolchain is used, covering energy measurement, (en/de)coding, quality analysis, performance profiling, and data analysis:

#### Energy measurement

* **Intel RAPL (Running Average Power Limit):**

  * **Use:** On 4.1.1.1 (i5-10505 lab platform) for CPU/DRAM energy of x265
  * **Interface:** Read `/sys/class/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:0/energy_uj` [cite: `Phase 1/SW/energy/raw_energy.sh`, Line 16]
  * **Traits:** Software-level power telemetry, adequate precision for software encoder energy analysis

* **ZES ZIMMER LMG611:**

  * **Use:** On 4.1.2 (Jetson), serial SCPI (115200) to measure system-level energy
  * **Traits:** High-precision integration; paired load/idle measurement to remove platform baseline power

#### Encoding/decoding

* **x265 (v4.1):**

  * **Use:** All software-side runs to generate RD data and statistics
  * **Key args:** `--intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 --no-opt-qp-pps --ipratio 1.0`
  * **Output:** Per-frame PSNR and bitrate via `--psnr --csv --csv-log-level 2`

* **NVIDIA Jetson Multimedia API:**

  * **Executables:** `video_encode`, `video_decode` [cite: `Phase 1/HW/generate_rd_data_hw.py`, Line 9-10]
  * **Path:** `/usr/src/jetson_multimedia_api/samples/01_video_encode/video_encode`
  * **Use:** RD tests, producing HEVC bitstreams and decoding back to YUV

* **FFmpeg:**

  * **Use:** PSNR computation for hardware-coded streams
  * **Cmd:** `ffmpeg -lavfi "[0:v][1:v]psnr"` for per-frame PSNR [cite: `Phase 1/HW/generate_rd_data_hw.py`]

#### Video quality analysis

* **VQA (Video Quality Analyzer):**

  * **Use:** Step 4 (Phase 3) algorithm matching
  * **Extracts:** CU/PU/TU splits; intra modes; transform types/sizes; in-loop filters (Deblocking, SAO)
  * **Output:** Technical profile of hardware encoder for x265 parameter mapping

* **x265 built-in PSNR:**

  * **Method:** `--psnr --csv`
  * **Output:** PSNR for Y/U/V and weighted PSNR-YUV

#### Performance profiling

* **Valgrind (Callgrind) v3.24.0:**

  * **Use:** On 4.1.1.2 (HPC) in Step 5 (Phase 4) for processor-event profiling
  * **Type:** Platform-agnostic dynamic binary instrumentation (DBI)
  * **Output:** 13 PEs: `Ir, Dr, Dw, I1mr, D1mr, D1mw, ILmr, DLmr, DLmw, Bc, Bcm, Bi, Bim` [cite: `Phase4 Modeling based on Processor Event/Roadmap.md`, Line 74]
  * **Traits:** High-precision, repeatable, architecture-neutral algorithm simulation; very high overhead (10×–100×) [cite: `Phase4 Modeling based on Processor Event/Phase 4 – Valgrind-Based Software Encoder Energy Modeling .md`, Line 27]

* **Linux perf (perf stat):**

  * **Use:** On 4.1.1.2 (HPC) in Step 5 (Phase 4) for hardware performance counters
  * **Events:** 18-event Perf Extended set (per Kränzler et al., 2023) [cite: `Phase4 Modeling based on Processor Event/Perf实验报告及结果分析.md`, Line 155]
  * **Architectures:** Intel and AMD
  * **Traits:** <1% overhead; true microarchitectural events
  * **Limits:** Some events unsupported on AMD (return `<not supported>`), confirming microarchitecture dependence [cite: ibid., Line 30]

#### Data analysis

* **Python stack:** pandas / numpy / matplotlib / scipy
* **BD-Metrics:**

  * **Tool:** `bjontegaard` Python lib
  * **Use:** BD-Rate, BD-PSNR
  * **Interpolation:** `akima` [cite: `Phase 1/HW/NVIDIA Jetson HEVC Hardware Encoder_ Rate-Distortion Test Workflow & Findings.md`, Line 134]

#### Machine learning

* **Linear Regression:**

  * **Use:** **Primary** model for energy prediction [cite: `Phase4 Modeling based on Processor Event/Phase 4 – Valgrind-Based Software Encoder Energy Modeling .md`, Line 93]
  * **Rationale:** Interpretability; consistent with Kränzler et al. (2023), aiding comparison and physical meaning [cite: ibid., Line 100]
  * **Performance:** Phase 4 (Valgrind) hardware-like config R²≈0.953, MAPE≈4.03% (<5% target) [cite: ibid., Line 119]
  * **Form:** $\hat{E}*{hw} = \beta_0 + \sum*{i=1}^{n} \beta_i \cdot PE_i$ [cite: `Phase4 Modeling based on Processor Event/Roadmap.md`, Line 120]

* **XGBoost:**

  * **Use:** **Supporting** model to test linear sufficiency and potential nonlinearities [cite: `Phase4 Modeling based on Processor Event/Phase 4 – Valgrind-Based Software Encoder Energy Modeling .md`, Line 94]
  * **Perf:** Phase 2 multivariate R²≈0.9998, MAPE≈1.28%; Phase 4 R²≈0.948, MAPE≈2.75% [cite: `Phase2/Analysis Summary.md`, Line 408; `Phase4 ... .md`, Line 120]

* **scikit-learn:**

  * **Models:** Linear, ElasticNet, RF, GBR
  * **CV:** 5-fold GroupKFold grouped by `seq_name` to avoid leakage [cite: `Phase4 ... .md`, Line 95]

#### Cluster scheduling

* **SLURM:**

  * **Use:** Job scheduling on FAU LNT Intel HPC
  * **Function:** Automate batch runs for Valgrind and perf
  * **Config:** `--cpus-per-task=8`, `OMP_NUM_THREADS=8` [cite: `Phase4 Modeling based on Processor Event/Roadmap.md`, Line 51]

### 4.1.4. Test Video Sequences

A set of **48** sequences covering broad resolutions/content, aligned with AOM CTC practices.

#### Distribution

* **a1_4k (8):** 3840×2160 — `BoxingPractice_4k`, `Crosswalk_4k`, `FoodMarket2_4k`, `Neon1224_4k`, `NocturneDance_4k`, `PierSeaSide_4k`, `Tango_4k`, `TimeLapse_4k` [cite: `Phase 1/SW/generate_rd_data.py`, Line 27-34]

* **a2_2k (21):** 1920×1080 or 1080×1920 — `Aerial3200_2k`, `Boat_2k`, `CrowdRun_1080p50`, `FoodMarket_2k`, `MeridianTalk_sdr_2k`, `Motorcycle_2k`, `MountainBike_2k`, `OldTownCross_1080p50`, `RitualDance_2k`, `Riverbed_1080p25`, `RushFieldCuts_2k`, `Skater227_2k`, `TunnelFlag_2k`, `Vertical_bees_2k`, `Vertical_Carnaby_2k`, `WalkingInStreet_2k`, `WorldCup_2k`, `WorldCup_far_2k`, `DinnerSceneCropped_2k`, `PedestrianArea_1080p25`, `ToddlerFountain_2k`, `TreesAndGrass_2k` [cite: ibid., Line 37-58]

* **a3_720p (8):** 1280×720 — `ControlledBurn_720p`, `DrivingPOV_720p`, `Johnny_720p`, `KristenAndSara_720p`, `RollerCoaster_720p`, `Vidyo3_720p`, `Vidyo4_720p`, `WestWindEasy_720p` [cite: ibid., Line 61-68]

* **a4_360p (6):** 640×360 — `BlueSky_360p`, `RedKayak_360p`, `SnowMountain_360p`, `SpeedBag_360p`, `Stockholm_360p`, `TouchdownPass_360p` [cite: ibid., Line 71-76]

* **a5_270p (4):** 480×270 or 270×480 — `FourPeople_270p`, `ParkJoy_270p`, `SparksElevator_270p`, `Vertical_Bayshore_270p` [cite: ibid., Line 79-82]

#### Traits

* **Format:** YUV420, 8-bit
* **Frame rates:** 25, 29.97, 30, 50, 59.94, 60 fps
* **Content diversity:** static/dynamic/dialogue/motion scenes
* **Orientation:** Includes 3 portrait videos (`Vertical_bees_2k`, `Vertical_Carnaby_2k`, `Vertical_Bayshore_270p`)

### 4.1.5. Common Encoding Configurations

To ensure reproducibility and consistency, strict configurations are enforced.

#### Strict intra-coding

All x265 experiments use strict intra-only and constant QP:

```sh
x265 --intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 \
  --no-opt-qp-pps --ipratio 1.0 \
  --qp [22|27|32|37] \
  --preset [preset_name] \
  --tune psnr --psnr \
  --csv [log_file.csv] --csv-log-level 2
```

**Key notes:**

* `--intra --keyint 1 --min-keyint 1`: force I-only, disable inter prediction
* `--bframes 0`: disable B-frames
* `--scenecut 0`: disable scene-cut detection
* `--no-opt-qp-pps`: keep constant QP
* `--ipratio 1.0`: fix I/P ratio
* `--tune psnr`: PSNR-oriented
* `--psnr`: compute PSNR
* `--csv --csv-log-level 2`: per-frame stats logging

#### QP settings

Exhaustively test **QP = {22, 27, 32, 37}**

* **QP 22:** high quality (low compression)
* **QP 27:** medium
* **QP 32:** medium–low
* **QP 37:** low quality (high compression)

#### Frame count evolution

A key methodological detail—different frame counts by purpose:

* **Phase 1 RD (cross-encoder comparison):** **30 frames** for both software and hardware (AOM CTC v2.0) [cite: `Phase 1/HW/generate_rd_data_hw.py`, Line 20; `... Findings.md`, Line 72]

  * **Purpose:** Fair, standard-conformant software vs hardware RD comparison
  * **Use:** BD-Metrics, RD curves, cross-encoder performance comparison

* **Phase 1 energy and all later stages:** **130 frames** for stability and larger sample size [cite: `Phase 1/SW/generate_rd_data.py`, Line 23]

  * **Purpose:** Improve stability of energy and decision statistics
  * **Use:** Software energy, processor-event profiling (Valgrind/perf), etc.

**Rationale:**

* **30 frames:** AOM-conformant cross-encoder RD comparability
* **130 frames:** Statistical stability for energy and algorithmic decisions

---

## 4.2. Methodological Workflow

## 4.2.1. Step 1: Initial Baseline Characterization & Problem Identification (Phase 1)

### Objective

Run initial RD/energy baselines on default presets for both software and hardware encoders to quantify gaps and set baseline for later modeling.

### Procedure

#### Software-side (x265)

**Platform:** 4.1.1.1 (i5-10505)

**Automation:** `generate_rd_data.py` [cite: `Phase 1/SW/generate_rd_data.py`]

**Matrix:** 48 sequences (a1_4k–a5_270p) × 10 presets × 4 QPs = 1,920 configs [cite: `Phase 1/SW/generate_rd_data.py`, Line 22-23]

**Strict intra configuration:**

* `--intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0`
* `--no-opt-qp-pps --ipratio 1.0`
* `--psnr --csv --csv-log-level 2`

**Command example:** [cite: `Phase 1/SW/Readme.md`, Line 5-6]

```sh
x265 --input ~/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv \
  --input-res 1280x720 --fps 30 --frames 130 \
  --intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 \
  --qp 27 --no-opt-qp-pps --ipratio 1.0 \
  --preset medium --tune psnr --psnr \
  --csv log_file.csv --csv-log-level 2 \
  -o output.265
```

**Data collection:**

* Per-frame PSNR (Y/U/V) and bitrate with `--csv-log-level 2`
* Parse `bitrate_kbps` and average PSNR from x265 output
* Output dataset: `bitrate_psnr_results_130frame.csv` [cite: `Phase 1/SW/generate_rd_data.py`]

**Energy measurement:** `raw_energy.sh` + `CI_process_and_analyze.py`

* **Method:** Intel RAPL (`/sys/class/.../energy_uj`) [cite: `Phase 1/SW/energy/raw_energy.sh`, Line 16]
* **Paired measurement:**

  1. Load run: record energy delta during encoding
  2. Idle run: wait same duration; record idle energy delta
  3. Net energy: `Net_Delta = Delta_Load - Delta_Idle` [cite: `Phase 1/SW/energy/raw_energy.sh`, Line 124-134]
* **Stat. validation:** 15 repeats per config; CI-based convergence [cite: `Phase 1/SW/CI_process_and_analyze.py`]
* **Convergence:** CI width < 2% mean (99% confidence) [cite: `Phase 1/SW/CI_process_and_analyze.py`]
* **Outliers:** Iteratively removed until convergence
* **Output:** `stable_core_energy_measurements_final.csv` [cite: `Phase 1/SW/Readme.md`, Line 91]

#### Hardware-side (NVENC)

**Platform:** 4.1.2 (Jetson)

**RD collection:** `generate_rd_data_hw.py` [cite: `Phase 1/HW/generate_rd_data_hw.py`]

**Pipeline:** For each (sequence, QP, preset) run 5 steps [cite: `... Findings.md`, Section 2.2]:

1. **Encode:** `video_encode` YUV → HEVC `.bin`

   ```bash
   video_encode [input.yuv] [width] [height] H265 [output.bin] \
     -hpt [preset_id] -sf 0 -ef [frames-1] \
     -ifi 1 --econstqp -qpi [qp] [qp] [qp]
   ```

   [cite: `Phase 1/HW/generate_rd_data_hw.py`, Line 285]

2. **Decode:** `video_decode` to YUV

   ```bash
   video_decode [input.bin] [output.yuv] H265
   ```

   [cite: `Phase 1/HW/generate_rd_data_hw.py`, Line 286]

3. **Bitrate:** from file size, 30 frames, frame rate

4. **PSNR:** FFmpeg per-frame PSNR

   ```bash
   ffmpeg -f rawvideo -pix_fmt yuv420p -s [width]x[height] -r [fps] -i [original.yuv] \
     -f rawvideo -pix_fmt yuv420p -s [width]x[height] -r [fps] -i [decoded.yuv] \
     -lavfi "[0:v][1:v]psnr" -f null -
   ```

   [cite: `Phase 1/HW/generate_rd_data_hw.py`]

5. **Record & clean:** Append (sequence, QP, preset, bitrate, PSNR-Y/U/V), then remove intermediates

**Matrix:** 48 sequences × 4 presets (-hpt 1–4) × 4 QPs [cite: `Phase 1/HW/generate_rd_data_hw.py`, Line 18-19]

**Frames:** First 30 frames (AOM CTC v2.0) [cite: `Phase 1/HW/generate_rd_data_hw.py`, Line 20]

**Output:** `rd_results_hardware_full_dataset.csv` [cite: `... Findings.md`, Section 2.3]

**Energy measurement:** Initial paired load/idle with LMG611. This directly ran encode jobs and logged energy; it did **not** yet handle DVFS, thermal throttling, etc.

### Analysis

#### RD analysis

**Software (x265):** `analyze_bdrates.py` [cite: `Phase 1/SW/analyze_bdrates.py`]

* Reference `medium`; compute BD-Rate (%) and BD-PSNR (dB) for the other 9 presets
* Output: `bd_metrics_results.csv` [cite: `Phase 1/SW/Readme.md`, Line 99]

**Hardware (NVENC):**

* Normalize: bpp and weighted PSNR-YUV (`PSNR-YUV = 0.875 × PSNR_Y + 0.0625 × PSNR_U + 0.0625 × PSNR_V`) [cite: `... Findings.md`, Line 123]
* BD-Metrics: reference `medium`; compute for `ultrafast`, `fast`, `slow`
* Interpolation: `akima` [cite: `... Findings.md`, Line 134]

#### Key RD finding: preset equivalence

**Finding:** For all sequences, NVENC `medium` (`-hpt 3`) and `slow` (`-hpt 4`) produce identical RD results.

**Evidence:** BD-Metrics show 0.00% / 0.00 dB between `slow` and `medium` (see Table 1 in `... Findings.md`) [cite: Section 3].

**Implications:**

* Hardware maps multiple user presets to identical internal algorithm paths
* Intra-only mode further compresses preset differences
* Hardware design optimizes for speed/efficiency over fine-grained control
* Direct preset-name mapping between software and hardware is invalid

### Critical finding: non-reproducible hardware energy (Phase 1)

Contrary to stable RAPL data on x265, Phase 1 hardware energy measurements were non-reproducible.

**Evidence:** The final report on precise hardware video-encoder energy measurement [cite: 高精度硬件视频编码器能耗测量实验方案最终报告] shows large run-to-run variance (20–30% or more) under identical configs → fundamental flaws in the preliminary method.

**Symptoms:**

* Back-to-back runs differ substantially
* Results vary across time (even within the same day)
* Highly random; no stable energy–config mapping

**Conclusion:** Phase 1 hardware energy method is fundamentally flawed and must be discarded before modeling. A rigorous, scientific measurement methodology is required.

**Transition:** Leads directly to Step 2—diagnose and overhaul measurement methodology.

---

## 4.2.2. Step 2: Rigorous Hardware Energy Measurement Methodology (Phase 2 core)

### Objective

Resolve Step 1’s crisis by developing a rigorous methodology that mitigates hardware uncertainties to obtain reliable, reproducible hardware-energy “Ground Truth.”

### Root cause analysis

From NVIDIA Jetson TDG [cite: 高精度硬件视频编码器能耗测量实验方案最终报告, NVIDIA_TDG_2025], two main causes:

#### 1. DVFS (Dynamic Voltage and Frequency Scaling)

Fast, millisecond-scale frequency changes under varying load/temperature cause power volatility for short tasks.

* **Mechanism:** Hardware encoding is fast (sub-1s for low-res/fast presets). Multiple frequency jumps within short windows create unstable measured energy.
* **Impact:** Identical tasks can yield very different energy due to DVFS state.

#### 2. Thermal throttling

Sustained load raises temperature; throttling then biases measurements.

* **Mechanism:** Long series of encodes push SoC beyond thresholds; auto down-clocking reduces later measured energy
* **Impact:** Non-reproducibility and sequence/history dependence

#### 3. Measurement interference

* **SSH latency:** Remote triggering adds timing noise
* **OS jitter:** Background services on Jetson perturb idle/load states

### Solution: three-level nested measurement

This is the core methodological contribution, implemented in `HW_energy_measurement.py` [cite: file] and the final measurement report [cite: 高精度...].

#### Inner loop (measurement amplification)

**Goal:** Smooth DVFS fluctuations

**Method:** Repeatedly execute N encodes (e.g., 100×) to extend total duration to `MIN_ENCODE_DURATION_SEC` (e.g., 2.0s) [cite: `HW_energy_measurement.py`, Line 293]

**Implementation:** `determine_loop_count()` two-probe timing [cite: Line 343-375]:

1. **Probe 1:** single encode time

   ```python
   t_start_1 = time.time()
   ssh_command(client, one_cmd)
   t_end_1 = time.time()
   duration_1 = t_end_1 - t_start_1
   ```

2. **Probe 2:** double encode time

   ```python
   two_cmd = f"for i in {{1..2}}; do {one_cmd}; done"
   t_start_2 = time.time()
   ssh_command(client, two_cmd)
   t_end_2 = time.time()
   duration_2 = t_end_2 - t_start_2
   ```

3. **Compute:** separate SSH overhead from payload

   ```python
   t_payload = max(0.001, duration_2 - duration_1)
   t_overhead = max(0.001, duration_1 - t_payload)
   loops = int(np.ceil((MIN_ENCODE_DURATION_SEC - t_overhead) / t_payload))
   ```

   [cite: Line 370-373]

**Effect:** Longer windows average out frequency jumps → stable mean power.

#### Middle loop (normalization)

**Goal:** Stable **per-encode** energy

**Paired measurement:** `measure_once_paired()` [cite: Line 397-439]:

1. **Load:**

   ```python
   _w(lmg, ":TRIG:INT:ENER:RES 1")
   _w(lmg, ":TRIG:INT:ENER:STAR 1")
   run_fn()
   _w(lmg, ":TRIG:INT:ENER:STOP 1")
   e_load_raw = _qf(lmg, ":READ:SCAL:ENER?")
   t_load_measured = _qf(lmg, ":READ:SCALAR:SLOTS:ENERGY:DURATION?")
   ```

2. **Idle:** same duration `t_load_measured`

   ```python
   time.sleep(IDLE_GAP_SEC)
   _w(lmg, ":TRIG:INT:ENER:RES 1")
   _w(lmg, ":TRIG:INT:ENER:STAR 1")
   time.sleep(t_load_measured)
   _w(lmg, ":TRIG:INT:ENER:STOP 1")
   e_idle_raw = _qf(lmg, ":READ:SCAL:ENER?")
   ```

3. **Net energy:**

   ```python
   toJ = (lambda x: x * 3600.0) if LMG_RETURNS_WH else (lambda x: x)
   e_load_J = toJ(e_load_raw)
   e_idle_J = toJ(e_idle_raw)
   e_process_J = e_load_J - e_idle_J
   ```

   [cite: Line 420-427]

4. **Normalize per encode:**

   ```python
   result['E_process'] /= _loops
   result['t_process'] /= _loops
   ```

   [cite: Line 520-521]

**Effect:** `E_single` removes loop-count scaling → stable per-job energy.

#### Outer loop (statistical convergence)

**Goal:** Statistical reliability

**Method:** Repeat the middle loop M times (M≥5, ≤15) [cite: Line 290-291]; collect `E_single` samples.

**Stats pipeline:**

1. **Outliers:**

   * **IQR (1.5×):** [cite: Line 449-454]

   ```python
   def iqr_filter(xs: list) -> list:
       if len(xs) < 4: return xs
       q1, q3 = np.percentile(xs, [25, 75])
       iqr = q3 - q1
       lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
       return [x for x in xs if lo <= x <= hi]
   ```

   * **median±25%:** if n>9 [cite: Line 456-460]

   ```python
   def median_25_filter(xs: list) -> list:
       if len(xs) < 3: return xs
       med = float(np.median(xs))
       lo, hi = 0.75 * med, 1.25 * med
       return [x for x in xs if lo <= x <= hi]
   ```

2. **CI test (99%):** [cite: Line 288, 441-447]

   ```python
   def t_half_width(samples: list, conf_prob: float) -> float:
       n = len(samples)
       if n < 2: return float("inf")
       s = statistics.stdev(samples)
       if SCIPY_OK:
           tcrit = student_t.ppf((1 + conf_prob) / 2, n - 1)
       else:
           tcrit = 2.576 if conf_prob >= 0.99 else 1.96
       return (s / np.sqrt(n)) * tcrit
   ```

   * **Criterion:** half-width < 2% of mean

   ```python
   ci_half_width = t_half_width(energies_filtered, CONF_PROB)
   threshold = INTERVAL_PART * mean_e  # 0.02
   if ci_half_width < threshold:
       print("-> Confidence Interval target met. Stopping early.")
       break
   ```

   [cite: Line 545-555]

   * **Early stop:** once converged (≤15 reps)

### Environmental controls

1. **CPU temperature:** keep <55 °C to avoid throttling
2. **Power mode calibration:** unify CPU frequency state before each run
3. **System stabilization:** 30 s pre-run stabilization (`STABILIZATION_SEC = 30.0`) [cite: `HW_energy_measurement.py`, Line 292, 472]

### Outcome

**`Phase2/all_dataset.csv`** [cite: `Phase2/all_dataset.csv`]

A high-reliability, statistically converged hardware-energy **Ground Truth** dataset containing:

* Software (x265) RD and energy
* Hardware (NVENC) RD and energy (statistically validated)
* All points pass 99% confidence, 2% error CI convergence

**Quality assurance:**

* Each hardware energy datum is a statistically validated stable mean
* Three-level nested design removes DVFS and thermal effects
* Environmental controls unify conditions

**Output file:** `energy_results_hardware_batch_normalized.csv` [cite: `HW_energy_measurement.py`, Line 474]

* Fields: `video_name, qp, preset, E_process_single_J, P_process_W, t_process_single_s, E_load_total_J, t_load_total_s, P_load_W, E_idle_total_J, t_idle_total_s, P_idle_W`
* Energies normalized per single encode

### Transition

With reliable Ground Truth, we proceed to meaningful analysis and modeling. First (Step 3): high-level characterization.

---

## 4.2.3. Step 3: High-Level Feature Modeling Attempt (Phase 2 analysis)

### Objective

Before complex PE modeling, attempt to predict hardware energy from simple, high-level features observable on the software side (software energy/time/configs).

### Data

Use `Phase2/all_dataset.csv` [cite: file], containing:

* Software (x265) energy, time, bitrate, PSNR, etc.
* Hardware (NVENC) energy (Step 2 Ground Truth)
* Aligned by `(video_name, qp, preset)`

### Modeling attempts

#### 1. Energy–time relationship

**Method:** Scatter energy vs time for software/hardware; compute Pearson r [cite: `Phase2/Analysis Summary.md`, Part 1]

**Results:**

* **x265:** n=1152, r≈0.9994 → near-perfect linearity
* **Hardware:** n=768, r≈0.8898 → strong but noisy [cite: `Phase2/Analysis Summary.md`, Line 92]

**Finding:** Time alone (r≈0.89) is insufficient for accurate hardware prediction.

#### 2. QP impact

**Method:** Fix resolution/preset; analyze QP effect (slopes) [cite: Part 2]

**Results:**

* **x265:** negative slopes; energy decreases with QP

  * 270p: ≈−2 ~ −9
  * 1080p: ≈−36 ~ −154
  * 4K: ≈−98 ~ −507
* **Hardware:** slopes ≈ 0 (≈−0.3 ~ +0.02) [cite: Line 185]

**Finding:** QP barely affects hardware energy → dominated by fixed pipeline power rather than coding complexity.

#### 3. Univariate models

**Method:** Predict `E_hw_J` from `sw_time_s` or `sw_bpp` [cite: Part 4]

**Results:**

**Time→Energy:**

* Linear: R²≈0.74, MAPE≈53%
* Poly(2/3): R²≈0.84, MAPE≈25%
* Tree (GBR/RF/XGB): R²≈0.89, MAPE≈18% [cite: Line 387-389]

**bpp→Energy:**

* Linear/Poly: R²<0.15, MAPE>100%
* GBR: R²≈0.77, MAPE≈49%
* RF/XGB: R²≈0.89, MAPE≈22–23% [cite: Line 393-395]

**Conclusion:** Time is the best single feature but still inadequate (MAPE>18%). bpp is nearly useless alone.

#### 4. Multivariate models

**Method:** Combine `sw_time_s + sw_bpp + resolution + QP + preset` [cite: Part 4]

**Results:**

* MV-Linear / MV-ElasticNet: R²≈0.94, MAPE≈20%
* MV-GBR: R²≈0.997, MAPE≈3.16%
* MV-RF: R²≈0.986, MAPE≈2.89%
* **MV-XGB: R²≈0.9998, MAPE≈1.28% (best)** [cite: Line 405-408]

**Note:** These rely on **config** features, not **algorithm-behavior** features; limited explanatory power across platforms.

---

## 4.2.4. Step 4: Limits of High-Level Modeling & Need for Algorithmic Analysis

### Limits of simple models

Although multivariate XGBoost achieves R²≈0.9998/ MAPE≈1.28%, it has fundamental limits:

#### 1. Poor interpretability

* Features (time, resolution, QP, preset) are high-level knobs and don’t explain algorithmic differences.
* QP has near-zero effect on hardware energy but strong effect on software (slopes to −507), implying hardware is pipeline-power dominated.
* Time–energy (r≈0.89) alone cannot explain the discrepancy.

#### 2. Weak generalization

* Reliance on config-based features risks breakdown under new config combos or platforms.
* These features don’t reflect internal decisions (intra modes, TU sizes, filter choices).

#### 3. No root-cause explanation

* Cannot answer **why** hardware vs software energy differ under same video/QP.
* Observations: hardware `medium` ≡ `slow` (RD), hardware energy ≈ insensitive to QP, etc.—hinting different algorithmic strategies.

### Necessity of algorithm-level analysis

Given these limits, we must descend from config-level features to algorithmic behavior.

**Transition:**

1. Steps 1–2: establish Ground Truth
2. Step 3: show limits of high-level models
3. Step 4 (now): recognize need for algorithm-level analysis
4. Step 5 (Phase 3): VQA-based analysis of algorithmic traits (filters, decisions)
5. Step 6 (Phase 4): PE-based modeling to map software algorithmic behavior to hardware energy

**Evolution path:**

```
Config-level modeling (Phase 2)
    ↓ [limitations]
Algorithm-level analysis (Phase 3: VQA)
    ↓ [reveal differences]
Processor events modeling (Phase 4: PEs)
```

**Conclusion:** High-level models can fit but lack interpretability/generalization. For a scientific and explainable mapping from software to hardware energy, we must analyze algorithmic behavior (→ Phase 3 VQA and Phase 4 PEs).

---

## 4.2.5. Step 5: Algorithmic Behavior Matching (Phase 3)

### Objective

Driven by Step 4, identify similarities/differences in internal decisions to achieve **configuration cloning**. Translate hardware behavior into concrete x265 parameters so later modeling compares comparable computation.

### Procedure

#### VQA bitstream analysis

**Tool:** VQA [cite: `Phase 3/Analysis/Report on Algorithmic Matching of HEVC Encoders.md`, Section 1]

**Objects:** Hardware bitstreams from Step 2 (`generate_rd_data_hw.py`, 30-frame encodes)

**Metrics:** Extract micro-level decision statistics [cite: `Phase 3/Analysis/Summary of HEVC Coding Analysis Metrics/readme.md`]:

1. **CU/PU/TU splits:**

   * CU sizes (64/32/16/8)
   * PU sizes (32/16/8/4)
   * TU sizes/depth
   * Partition modes (2N×2N, N×N, rect, AMP)

2. **Intra prediction modes:**

   * Luma: 35 modes (Planar, DC, 33 angles)
   * Chroma: DM, DC, Planar, Horizontal, Vertical, Diagonal, etc.

3. **Transform types:**

   * DCT vs DST
   * Transform Skip usage
   * Transform type vs TU size

4. **In-loop filters:**

   * Deblocking (strength/direction/activation)
   * SAO (No-op, Band, Edge)

**Technical profiles:** For each hardware preset (slow/medium/fast/ultrafast) compute averages across sequences/QPs to form quantitative profiles [cite: `Report...`, Section 2.1]

### Matching process

#### Stage 1: hardware profile generation

**Target preset:** NVIDIA NVENC `slow` (final target for energy modeling)

**Method:** Compute key averages from `hardware_stats_full.csv` [cite: `Report...`, Section 2.1]

**Key findings (slow):**

* **CU:** 64×64 **disabled** (0.0%); heavy 8×8 (62.0%); 32×32=12.9%, 16×16=25.0% [cite: Table 1]
* **TU:** deep recursion; 49.9% TUs at 4×4 [cite: Table 1]
* **Transforms:** DST 59.3%; Transform Skip 7.6% [cite: Table 1]
* **Filters:** SAO enabled (luma 36.6%); Deblocking **disabled** [cite: Table 1]

#### Stage 2: map to x265 parameters

From VQA stats and x265 docs [cite: `Summary ... /Analyze encoder parameter .md`]:

| Hardware behavior | Quantitative data | x265 parameter       | Rationale                                |
| ----------------- | ----------------- | -------------------- | ---------------------------------------- |
| No 64×64 CU       | 0.0%              | `--ctu 32`           | Cap max CU to match observed upper bound |
| Heavy 8×8 CU      | 62.0%             | `--min-cu-size 8`    | Permit minimum CU 8×8                    |
| Deep TU recursion | 49.9% 4×4 TU      | `--tu-intra-depth 3` | Allow deep TU recursion                  |
| Transform Skip    | 7.6%              | `--tskip`            | Enable TSkip                             |
| SAO on            | confirmed         | `--sao`              | Match SAO usage                          |
| Deblocking off    | confirmed         | `--no-deblock`       | Match hardware slow/medium               |
| No rect/AMP       | 2N×2N/N×N only    | `--no-rect --no-amp` | Match absence of rect/AMP                |

[cite: `Report...`, Table 2; `Analyze encoder parameter .md`, Sections 2–7]

**Final “clone” command template:**

```bash
x265 --input <input_file.yuv> --input-res <width>x<height> --fps <fps> \
  --output <output_file.hevc> --qp <QP_VALUE> \
  --preset medium \
  --ctu 32 \
  --min-cu-size 8 \
  --tu-intra-depth 3 \
  --tskip \
  --sao \
  --no-deblock \
  --no-rect --no-amp \
  --rd 4 \
  --keyint 1
```

[cite: `Report...`, Section 3.2.1]

#### Stage 3: clone validation

**Method:** Generate HEVC with clone params; run the same VQA; compare profiles vs target hardware preset [cite: `Report...`, Section 2.3]

### Key findings & transition

#### Finding 1: algorithmic similarity between hardware preset and software preset

VQA shows **hardware `slow`** is closest to software **`superfast`**:

* **PU sizes:** Software `medium`→`superfast` use many 4×4 PUs (~2.10–2.12M); hardware `slow`/`medium` also heavy on 4×4/8×8 [cite: `Summary ... /readme.md`, Line 85]
* **TU sizes:** Both use ~2.47–2.48M 4×4 TUs in slow/superfast [cite: Line 97]
* **Transforms:** Software `medium`–`superfast` use DST (120×); hardware `slow`/`medium` also use DST (~117×) [cite: Line 101]

#### Finding 2: fundamental in-loop filter difference (“filter bottleneck”)

Despite CU/PU/TU/modes/transform similarities, **filters differ**:

* **Hardware:** SAO **on** across presets; Deblocking **off** at slow/medium [cite: `Analyze encoder parameter .md`, Section 7; `readme.md`, Line 107]
* **Software:** `superfast` has SAO **off** for speed but Deblocking **on** by default [cite: `Analyze encoder parameter .md`, Line 174]

**This is the final bottleneck:** hardware uses `SAO on, Deblock off`; software `superfast` uses `SAO off, Deblock on`. This cannot be bridged by trivial tuning—needs dedicated quantification.

### Transition

Having completed high-level (Step 3) and algorithm-level (Step 4/5) analyses, we must descend to the physical (processor) layer to quantify the real costs of this “filter bottleneck” and identify fundamental predictive features. This leads to Step 6: PE profiling to quantify Deblocking vs SAO microarchitectural costs and map software behavior to hardware energy.

---

## 4.2.6. Step 6: Processor-Level Profiling & Final Model Development (Phase 4)

### Objectives

1. **Resolve the filter bottleneck:** Quantify microarchitectural costs of Deblocking vs SAO and explain hardware (`SAO on, Deblock off`) vs software default (`Deblock on, SAO off`)
2. **Produce physically meaningful features:** Extract PEs for an interpretable energy model

### Experimental design

#### Platform migration

**Why:** Extremely compute-heavy (960+ Valgrind runs at 10×–100× overhead) [cite: `Phase 4 … .md`, Line 27]

**Plan:**

* **Source:** 4.1.1.1 (i5-10505 lab)
* **Target:** 4.1.1.2 (FAU LNT Intel HPC) [cite: Line 22]
* **Scheduler:** SLURM for automated batching

#### Base configuration

**Preset coverage:** faster/fast/veryfast/superfast as the base, with layered analyses as needed [cite: Section 4.3]

**Encode config:** Strict intra, 130 frames, QP = {22, 27, 32, 37} [cite: Section 4.3]

#### Controlled configs

Two configs to isolate filters:

**Config A (Hardware-like):** `--no-deblock --sao`

* **Goal:** Emulate hardware slow filter usage
* **Hypothesis:** SAO yields more regular access patterns → more predictable PEs

**Config B (Default):** `--deblock --no-sao`

* **Goal:** Emulate x265 defaults
* **Hypothesis:** Deblocking introduces data-dependent control flow → more branch misses/cache misses

[cite: Section 4.4]

**Scale:** Valgrind ≈ 30 sequences × 4 presets × 4 QPs × 2 configs = 960; perf repeated on Intel+AMD → 1,920 CSVs (Extended 18 events) [cite: Section 4.3]

### Dual-method profiling

#### 4.2.6.1. Valgrind (Callgrind)

**Goal:** High-precision, interpretable **simulated events** as **primary features**

**Tool:** Valgrind 3.24.0 (Callgrind) [cite: Line 20]

**Env:** HPC; `OMP_NUM_THREADS=1`, `X265_THREADS=1` to minimize concurrency effects

**Flow:**

1. **Batch:** SLURM jobs over all (seq, preset, QP, config)

   ```bash
   valgrind --tool=callgrind \
     --callgrind-out-file=callgrind_[A/B]_${preset}_${qp}_${seq}.out \
     ./x265 --input ${seq_path} --input-res ${WxH} \
            --frames 130 --preset ${preset} --qp ${qp} \
            --keyint 1 [--no-deblock --sao | --deblock --no-sao] \
            -o /dev/null
   ```

   [cite: `Roadmap.md`, Line 65-71]

2. **Events:** Parse 13 PEs:

   * `Ir; Dr, Dw; I1mr, D1mr, D1mw; ILmr, DLmr, DLmw; Bc, Bcm, Bi, Bim` [cite: Line 74]

3. **Alignment:** Match each software run to hardware energy label `E_hw_slow` by `(video_name, qp)` [cite: Section 4.5]

**Output:** `callgrind_summary_with_E_hw_slow.csv` (960 rows, 13 PEs + target)

**Traits:** Architecture-neutral, precise, deterministic; high overhead

#### 4.2.6.2. Linux perf

**Goal:** Low-overhead **hardware** counters for **real-world validation** and **cross-arch comparison**

**Tool:** `perf stat` [cite: `Valgrind-Based Energy Modeling and Cross-Validation with Perf.md`, Section 6.2.3]

**Env:** HPC; Intel + AMD [cite: Line 54]

**Flow:**

1. **Events:** Extended 18 set (Kränzler et al. 2023) [cite: `Perf实验报告及结果分析.md`, Line 155]

   ```bash
   perf stat -e cache-misses,cache-references,instructions,cycles, \
     L1-dcache-loads,L1-dcache-load-misses,L1-icache-load-misses, \
     LLC-loads,LLC-load-misses,LLC-stores,LLC-store-misses, \
     branch-instructions,branch-misses,branch-loads,branch-load-misses, \
     dTLB-loads,dTLB-load-misses,dTLB-stores,dTLB-store-misses \
     -x, ./x265 [params...]
   ```

2. **Cross-arch:**

   * **Intel:** all 18 collected
   * **AMD:** some unsupported (e.g., LLC) → `<not supported>` [cite: Line 30]

3. **Scale:** 1,920 CSVs (2 arch × 2 feature sets × 480 configs) [cite: Line 58]

**Output:** `perf_extended_summary_with_E_hw_slow.csv`

**Traits:** Low overhead; validates Valgrind findings; reveals architecture dependence

### Final modeling

#### Dataset

**X (features):** Valgrind **13 PEs** (`Ir, Dr, Dw, I1mr, D1mr, D1mw, ILmr, DLmr, DLmw, Bc, Bcm, Bi, Bim`) [cite: Section 4.6]

**Rationale:** Phase 4 shows the 13-PE set performs best (hardware-like MAPE≈4.03%, <5% target) [cite: Line 119]

**Y (target):** Step 2 hardware energy `E_hw_slow` (Jetson NVENC, `preset=slow`) [cite: Section 4.5]

**Alignment:** One-to-one `(video_name, qp)` across software features and hardware labels [cite: Section 4.5]

#### Models

**Primary:** **Linear Regression**

* **Why:** Interpretability; aligns with prior work [cite: Line 100]
* **Form:** $\hat{E}*{hw} = \beta_0 + \sum*{i=1}^{13} \beta_i \cdot PE_i$ [cite: `Roadmap.md`, Line 120]

**Auxiliary:** **XGBoost Regressor**

* **Why:** Test for nonlinearities [cite: Line 94]

#### Training & validation

**CV:** **5-fold GroupKFold** by `seq_name` (avoid sequence-level leakage) [cite: Line 95]

**Grouping rationale:** Frames from the same sequence are correlated; grouping is a rigor reviewers value.

**Training:**

* **Separate models:** Train Config A and Config B independently to isolate filter effects
* **Scaling:** StandardScaler on PE features

#### Metrics

* **MAPE:** Primary; target <5% [cite: Line 101]
* **R²:** Goal >0.90
* **RMSE:** Absolute error in Joules

### Results

#### Valgrind-model performance

| Config                                  | Model   |        R² |  RMSE (J) |      MAPE |
| --------------------------------------- | ------- | --------: | --------: | --------: |
| **Default (Deblock on, SAO off)**       | Linear  |     0.919 |     0.828 |     5.17% |
| **Default**                             | XGBoost |     0.931 |     0.765 |     2.76% |
| **Hardware-like (SAO on, Deblock off)** | Linear  | **0.953** | **0.633** | **4.03%** |
| **Hardware-like**                       | XGBoost |     0.948 |     0.666 |     2.75% |

[cite: Section 4.8]

**Key points:**

* Linear already achieves **MAPE < 5%**, showing stable linear predictability.
* **Hardware-like** has lower RMSE/higher R² → more stable/linear energy–PE relationship.
* XGBoost only slightly improves accuracy → relationship largely linear.

#### Processor-event interpretation

**Coefficients (normalized):** Cache misses (DLmr, D1mr) and branch mispredictions (Bim) dominate; instruction count (Ir) secondary:
#[E_{pred} = 0.41 \cdot DLmr + 0.37 \cdot D1mr + 0.22 \cdot Bim + 0.08 \cdot Ir + \epsilon]
[cite: Section 4.10]

**Physical meaning:**

* **Energy is dominated by memory misses and branch mispredictions**, consistent with power models where stalls are costly.
* **Config A vs B:**

  * Config B shows higher `Bim` and `D1mr`
  * Explanation: Deblocking introduces data-dependent branches (control flow unpredictability); SAO operates on pixel groups with deterministic offsets (more regular access) [cite: Section 4.9]

#### Perf validation

**Cross-tool validation:** Perf confirms Valgrind findings on real hardware [cite: `Valgrind-Based Energy Modeling and Cross-Validation with Perf.md`, Section 6.8]:

| Aspect         | Valgrind                  | Perf                                      | Consistency |
| -------------- | ------------------------- | ----------------------------------------- | :---------: |
| Branching      | Deblock ↑ branch mispred  | `branch-misses` ↑                         |      ✅      |
| Caches         | Deblock ↑ L1/L2 misses    | `L1-dcache-load-misses` ↑                 |      ✅      |
| Predictability | Hardware-like more linear | MAPE: Hardware-like 12.0% < Default 30.0% |      ✅      |

[cite: Section 6.8]

**Cross-arch:** Some AMD counters unsupported (`<not supported>`), confirming microarchitecture dependence; subsequent analysis focuses on Intel for completeness/stability [cite: `Perf实验报告及结果分析.md`, Line 30, 265]

### Transition

Step 6 builds an interpretable, processor-event-based cross-platform energy estimator, completing the chain from diagnosis to final modeling.

---

## 4.3. Summary of Methodological Contributions

In sum, the methodology is a six-step, logic-driven pipeline from diagnosis to final modeling.

**First (Steps 1–2),** we overcame the measurement crisis with a rigorous scheme (temperature control, power-mode calibration, statistical convergence) to obtain reliable software/hardware baselines. The three-level nested method (inner amplification, middle normalization, outer convergence) is a core contribution that yields scientifically reliable, reproducible hardware-energy Ground Truth.

**Next (Step 3),** using these data we showed that simple proxy models (e.g., time, QP) cannot support cross-platform prediction. x265 shows near-perfect energy–time linearity (r≈0.999), whereas hardware is only strongly correlated (r≈0.89). Crucially, QP is nearly irrelevant for hardware (slope≈0) but strongly affects software (as low as −507), proving fundamentally different responses to configuration.

**Then (Steps 4–5),** after exposing high-level limits, we moved to algorithm-level analysis via VQA and achieved configuration cloning. We found hardware `slow` is closest to software `superfast`, and translated hardware behaviors (“never use 64×64 CU”, “deep TU recursion”) into x265 params (`--ctu 32`, `--tu-intra-depth 3`, etc.). However, a **filter bottleneck** remains: hardware uses `SAO on, Deblock off` while software defaults to `Deblock on, SAO off`.

**Afterward (Step 6),** we migrated compute-heavy profiling to HPC and, via Valgrind + perf, provided a physical explanation and extracted final modeling features. With controlled experiments (Config A vs B), we quantified Deblocking vs SAO microarchitectural costs. The 13-PE Valgrind features predict hardware energy with MAPE<5%. Perf confirms that Deblocking increases branch misses/cache misses and harms linearity.

**Finally (Step 6),** we built an interpretable, processor-event-based model. Linear regression ($\hat{E}*{hw} = \beta_0 + \sum*{i=1}^{13} \beta_i \cdot PE_i$) on the hardware-like config achieves R²≈0.953, MAPE≈4.03% (<5%). Coefficients show energy dominated by cache misses (`DLmr`, `D1mr`) and branch mispredictions (`Bim`), aligning with established power theories.

This multi-layer, multi-platform, progressively deepened process ensures each step stands on solid data and analysis. From diagnosis (Step 1) to measurement overhaul (Step 2), from high-level modeling (Step 3) to algorithmic cloning (Steps 4–5), and finally to physical-layer modeling (Step 6), the methodology forms a tightly coupled, rigorous chain that offers a reproducible, interpretable paradigm for cross-platform video-encoder energy modeling.
