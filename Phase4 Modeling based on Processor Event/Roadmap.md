# 🧭 Experimental Roadmap (Final Integrated Version – Phase 4 & Phase 5)

## 1. Objective

This research aims to establish a **processor-event-based energy modeling framework** for HEVC intra-coding by systematically bridging two complementary analysis layers:

1. **Phase 4 – Valgrind (Callgrind Simulation):**  
   A deterministic, platform-independent simulation of instruction-level and cache behavior to capture algorithmic complexity.

2. **Phase 5 – Perf (Hardware Performance Counters):**  
   A hardware-validated measurement of real microarchitectural events to verify whether Valgrind-observed trends persist in physical CPUs.

Together, these phases address two core scientific questions:

1. How do Deblocking and SAO filters influence processor-level behavior and energy efficiency?  
2. Can software-visible processor events (PEs) reliably predict hardware energy consumption across simulation and real measurement domains?

---

## 2. Experimental Design Overview

### 2.1 Independent Variables

| Category | Parameter | Range / Levels | Description |
|-----------|------------|----------------|--------------|
| Encoding preset | `preset` | fast, faster, veryfast, superfast | Controls algorithmic complexity and speed |
| Filter configuration | `config` | Default-like, Hardware-like | See § 2.2 |
| Quantization parameter | `qp` | 22, 27, 32, 37 | Controls compression strength |
| Resolution | `res` | 2K, 4K | Balanced visual content |
| Frames per run | `frames` | 130 | Fixed for fair comparison |

### 2.2 Filter Configurations

| Label | Parameters | Description |
|--------|-------------|-------------|
| **Default-like** | `--deblock --no-sao` | x265 default behavior (Deblocking ON, SAO OFF) |
| **Hardware-like** | `--no-deblock --sao` | Hardware-mimicking behavior (Deblocking OFF, SAO ON) |

Both configurations were executed on identical videos, QPs, and presets, ensuring controlled isolation of filter effects.

---

## 3. Experimental Environment

| Item | Description |
|------|--------------|
| Platform | FAU LNT Intel CPU Cluster |
| OS & Scheduler | Linux + Slurm |
| Core tools | x265, Valgrind 3.24.0, Perf, CMake, NASM |
| Target energy | Hardware encoder (NVENC, preset = slow) measured via power meter |
| Parallel setup | `--cpus-per-task = 8`, `OMP_NUM_THREADS = 8` |

---

## 4. Procedure Overview

### Phase 4 – Valgrind (Callgrind Simulation)

**Goal:** Capture deterministic instruction and cache behavior at the software level.

1. Build x265 with OpenMP support and run under Callgrind.
2. Sweep across all (preset, QP, resolution) combinations.
3. Generate `.out` files for both configurations.

```bash
# Example (Hardware-like)
valgrind --tool=callgrind \
  --callgrind-out-file=callgrind_HWlike_${preset}_${qp}_${seq}.out \
  ./x265 --input ${seq_path} --input-res ${WxH} \
         --frames 130 --preset ${preset} --qp ${qp} \
         --keyint 1 --no-deblock --sao -o /dev/null
```
4. Parse outputs via custom scripts to extract 13 key processor events (PEs):
`Ir, Dr, Dw, I1mr, D1mr, D1mw, ILmr, DLmr, DLmw, Bc, Bcm, Bi, Bim.`
5. Align each run with its corresponding hardware energy label
`E_hw_slow` from the NVENC dataset using `(video_name, qp)` matching.

### Phase 5 – Perf (HPC Measurement)

**Goal:**  
Measure real microarchitectural behavior and validate the Valgrind-derived conclusions under actual hardware execution.

1. Use perf stat to record the 18-event “Perf Extended” set consistent with Kränzler et al., 2023:

```bash
cache-misses, cache-references, instructions,
L1-dcache-loads/misses, L1-icache-load-misses,
LLC-loads/misses, LLC-stores/misses,
branch-instructions, branch-misses, branch-loads/misses,
dTLB-loads/misses, dTLB-stores/misses
```
2. Collect data on both Intel and AMD architectures.
3. Merge hardware counters with the same energy label E_hw_slow.
4. Compute averages by preset and configuration for microarchitectural comparison.


## 5. Data Structure

| Column          | Description                                  |
|-----------------|----------------------------------------------|
| `preset`, `qp`, `seq_name` | Experimental identifiers                  |
| `Ir` – `Bim` or 18 Perf PEs | Processor events (Valgrind 13 / Perf 18) |
| `E_hw_slow`     | Hardware energy (target label, J)            |
| `config`        | Default-like / Hardware-like                 |

All data were merged into master CSVs:  
- `callgrind_summary_with_E_hw_slow.csv` (Phase 4)  
- `perf_extended_summary_with_E_hw_slow.csv` (Phase 5)

---

## 6. Modeling and Evaluation

### 6.1 Model Choice

The **baseline model** is **linear regression** (for interpretability and parity with prior work).  
Non-linear models (XGBoost) are used only for auxiliary checks.

\[
\hat{E}_{hw} = \beta_0 + \sum_{i=1}^{n} \beta_i \cdot PE_i
\]

### 6.2 Training Strategy

- Train **separately per configuration** (Default-like vs Hardware-like).
- **5-fold GroupKFold** (grouped by `seq_name`) to avoid leakage across frames of the same sequence.
- Report:
  - Mean Absolute Percentage Error (MAPE)
  - Coefficient of determination (R²)
  - Root Mean Squared Error (RMSE)

### 6.3 Metrics and Thresholds

| Metric | Target Value                                  | Interpretation        |
|--------|-----------------------------------------------|-----------------------|
| MAPE   | ≤ 5% (Valgrind) / ≤ 12% (Perf Hardware-like)  | Prediction accuracy   |
| R²     | ≥ 0.90                                         | Model goodness-of-fit |
| RMSE   | Reported in Joules                             | Scale-aware error     |

---

## 7. Analysis Dimensions

1. **Filter Configuration Effect**  
   - Deblocking (Default-like) introduces control-flow irregularity (↑ `branch-misses`) and worsens locality (↑ `L1/LLC` misses).  
   - SAO (Hardware-like) increases regular memory access but preserves **linear** energy scaling.

2. **Preset Sensitivity**  
   - Faster presets reduce total instructions yet often increase **miss ratios**, exposing memory bottlenecks.  
   - *Superfast* shows the smallest PE counts overall **except** `D1mr`, which peaks—consistent with L1 pressure.

3. **Cross-Phase Validation**  
   - Valgrind and Perf align on direction and relative magnitude of filter-induced effects.  
   - Deblock-driven **nonlinearity** emerges more strongly in Perf due to real pipeline effects (flushes, refills).

---

## 8. Key Findings

| Configuration                              | Source     | MAPE (Linear) | R²     | Trend                                      |
|--------------------------------------------|------------|---------------|--------|--------------------------------------------|
| Hardware-like (SAO on, Deblock off)        | Valgrind   | < 5%          | > 0.95 | Smooth, linear energy–PE relationship      |
| Default-like (Deblock on, SAO off)         | Valgrind   | ≈ 6–8%        | 0.90–0.94 | More irregular branch/memory behavior    |
| Hardware-like                               | Perf       | ≈ 12%         | ≈ 0.95 | Higher predictability on real hardware     |
| Default-like                                | Perf       | ≈ 30%         | ≈ 0.92 | Nonlinearity amplified by hardware effects |

**Interpretation:**  
Deblocking dominates energy variance via data-dependent branching and cache disruptions, while SAO remains computationally regular and thus more predictable.

---

## 9. Visualization Plan

| Figure                    | Description                                                    |
|---------------------------|----------------------------------------------------------------|
| *Error Rate vs Preset*    | MAPE across presets for both configurations                   |
| *Predicted vs Measured*   | Scatter plots with y = x reference lines                      |
| *Feature Importance*      | Relative weights (linear coefficients / XGB gain)             |
| *ΔPE Heatmaps*            | Event-level differences (Hardware-like – Default-like)        |
| *Energy Bar Charts*       | Mean `E_hw_slow` per preset and configuration                 |

---

## 10. Conclusion and Future Work (Phase 6 Perspective)

### 10.1 Conclusions

- The two-phase framework robustly links **algorithmic-level simulation** (Valgrind) with **microarchitectural-level measurement** (Perf).  
- Processor events—especially `branch-misses` and `L1/LLC` misses—consistently explain the energy gap between filters.  
- Linear regression achieves **interpretable** and **competitive** accuracy; non-linear effects are primarily tied to Deblocking.  
- The **Hardware-like** configuration exhibits more stable, energy-proportional behavior, enabling stronger software→hardware mapping.

### 10.2 Future Work – Potential Phase 6

A natural continuation is **closed-loop validation** via **direct power measurement** (e.g., Intel RAPL, ZES LMG611), integrating:

1. Valgrind instruction-level simulation →  
2. Perf microarchitectural measurement →  
3. Real power trace correlation.

This would quantify residual bias, enable CPU–GPU–ASIC cross-validation, and support ratio-based features (IPC, miss-rate).  
Fine-grained temporal profiling could further reveal transient power dynamics across encoder stages.

---

