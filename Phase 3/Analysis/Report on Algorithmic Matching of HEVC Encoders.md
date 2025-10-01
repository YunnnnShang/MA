# Report on Algorithmic Matching of HEVC Encoders
**Phase II: Technical Profiling and Configuration Cloning**

## 1. Objective

Following the successful completion of the VQA (Video Quality Analyzer) data acquisition phase, the next critical step is to establish a fair and scientifically valid basis for comparing the x265 software encoder and the NVIDIA NVENC hardware encoder. This objective is driven by the core challenge that encoder presets (e.g., "medium") are not directly comparable across different implementations, as they represent vendor-specific trade-offs between speed and quality.

As directed, the goal of this phase is to:
1.  **Compare the coding tools** used by the x265 software encoder and the NVENC hardware encoder at a micro-behavioral level.
2.  **Make necessary changes to x265** by creating a custom configuration that mimics the algorithmic behavior of a target hardware preset.

This process, termed "Configuration Cloning," ensures that subsequent energy modeling is based on comparing the two platforms as they perform computationally similar tasks, thereby isolating the impact of the hardware architecture itself. This report details the methodology and results for cloning the NVIDIA NVENC `medium` preset.

## 2. Methodology

The process was divided into three main stages: profiling the target hardware encoder, mapping its behavior to software encoder parameters, and verifying the match.

### 2.1. Stage 1: Technical Profile Generation of the Target Encoder

The primary target for this analysis was the **NVIDIA NVENC `medium` preset**. This preset was chosen as it represents a balance between encoding speed and quality, making it a representative case for many practical applications.

Using the consolidated VQA statistics from `hardware_stats_full.csv`, a Python script was executed to compute the average values of key micro-behavioral metrics across all videos and QPs for this preset. This generated a quantitative "Technical Profile" of the target preset's algorithmic behavior.

### 2.2. Stage 2: Mapping the Technical Profile to x265 Parameters

The quantitative profile from Stage 1 was then translated into a specific set of x265 command-line parameters. This was achieved by referencing the x265 documentation and selecting parameters that force x265 to adopt the behavior observed in the hardware encoder. The goal was to build a command from the ground up, without relying on a standard x265 preset, to ensure maximum fidelity to the hardware's profile.

### 2.3. Stage 3: Verification of the Cloned Configuration

A "clone" HEVC bitstream (e.g., `ControlledBurn_720p_x265_clone_qp27.hevc`) was generated using the custom x265 parameter set derived in Stage 2. This bitstream was then subjected to the exact same VQA analysis pipeline as the original hardware streams. The resulting data was analyzed to generate a technical profile for the "clone" configuration, which was then compared directly against the target hardware profile to assess the accuracy of the match.

## 3. Results and Analysis

### 3.1. Technical Profile of NVIDIA NVENC 'medium' Preset

The analysis of the hardware encoder's `medium` preset revealed a distinct and complex encoding strategy. The table below summarizes the average usage of key HEVC coding tools.

**Table 1: Quantitative Technical Profile of NVIDIA NVENC `medium` Preset**

| Metric Category | Specific Metric | Average Value (%) |
| :--- | :--- | :--- |
| **CU Partitioning** | 64x64 CU Usage | 0.0 % |
| | 32x32 CU Usage | 12.9 % |
| | 16x16 CU Usage | 25.0 % |
| | 8x8 CU Usage | 62.0 % |
| **Intra Prediction** | Planar Mode Usage | 17.2 % |
| | DC Mode Usage | 9.2 % |
| | Angular Mode Usage | 73.6 % |
| **TU Partitioning** | 32x32 TU Usage | 11.3 % |
| | 16x16 TU Usage | 20.0 % |
| | 8x8 TU Usage | 18.9 % |
| | 4x4 TU Usage | 49.9 % |
| **Transform Types** | DST Usage Rate | 59.3 % |
| | Transform Skip Usage Rate | 7.6 % |
| **Loop Filters** | SAO (Luma) Active Rate | 36.6 % |
| | SAO (Chroma) Active Rate | 1.6 % |
| | Deblocking Filter | **Enabled** |

#### 3.1.1. Analysis of Key Findings

* **CU Partitioning Strategy**: The most significant finding is the **complete absence of 64x64 Coding Units (CUs)**. [cite_start]The HEVC standard introduced larger CUs to efficiently compress flat image areas[cite: 9944, 9945]. The NVENC hardware, however, forgoes this tool entirely in its `medium` preset, instead relying heavily on the smallest **8x8 CUs (62.0% usage)**. This suggests a hardware architecture optimized for processing smaller, more numerous blocks, possibly to enhance parallelism.

* **TU Partitioning Strategy**: The encoder demonstrates a strong preference for **deep Transform Unit (TU) recursion**, with **49.9% of all TUs being the minimum 4x4 size**. This indicates a quality-oriented approach where the encoder performs extensive Rate-Distortion Optimization (RDO) to find the optimal transform size for the prediction residual, a computationally expensive process.

* **Transform Type Strategy**: The encoder actively utilizes advanced transform tools.
    * **Discrete Sine Transform (DST)**: A **59.3% usage rate** for DST on eligible 4x4 luma blocks is remarkably high. [cite_start]In HEVC, a DST can be used for 4x4 luma transform blocks in intra-coded regions[cite: 10151]. As this decision requires extra computation (evaluating both DCT and DST), this indicates that the RDO engine is aggressively seeking quality improvements for blocks with specific directional textures.
    * **Transform Skip (TS)**: A **7.6% usage rate** confirms that this tool is enabled and effectively used to preserve sharp details by bypassing the transform stage, a behavior consistent with a quality-focused encoder.

* **Loop Filter Strategy**:
    * **Sample Adaptive Offset (SAO)**: The filter is confirmed to be active. The data reveals an intelligent, adaptive application: it is enabled on 36.6% of luma blocks, where its impact on perceived quality is highest, but only on 1.6% of chroma blocks, likely to conserve computational resources. [cite_start]The SAO filter is designed to reduce artifacts like banding and ringing by applying offsets to reconstructed pixels[cite: 10218, 10219].
    * **Deblocking Filter (DBF)**: Its operation is confirmed. [cite_start]The DBF is a fundamental component of HEVC for reducing blocking artifacts and is expected to be enabled in any quality-oriented preset[cite: 10210].

### 3.2. Mapping to x265 Parameters and "Clone" Configuration

Based on the technical profile above, the following custom x265 parameter set was constructed to "clone" the NVENC `medium` preset's behavior.

**Table 2: Mapping of Hardware Profile to x265 Parameters**

| Hardware Profile Feature | Quantitative Data | Mapped x265 Parameter | Justification |
| :--- | :--- | :--- | :--- |
| No 64x64 CUs | 0.0% Usage | `--ctu 32` | [cite_start]Restricts the maximum CU size to match the hardware's observed limit. x265 presets faster than `veryfast` also use a 32x32 CTU to improve parallelism[cite: 9666]. |
| Extensive 8x8 CU Usage | 62.0% Usage | `--min-cu-size 8` | [cite_start]Allows the encoder to partition down to the smallest CU size (8x8) as defined by the HEVC standard and observed in the hardware output[cite: 8194]. |
| Deep TU Recursion | 49.9% 4x4 TU Usage | `--tu-intra-depth 3` | Simulates the hardware's preference for small TUs by allowing deep recursion. [cite_start]This setting limits the extra recursion depth for intra CUs[cite: 8323, 8324, 8325, 8326]. |
| Transform Skip Enabled | 7.6% Usage | `--tskip` | [cite_start]Explicitly enables the Transform Skip tool, which is effective at RDO levels 3 and above[cite: 8850]. |
| SAO Filter Enabled | Confirmed Active | `--sao` | [cite_start]Explicitly enables the SAO loop filter, which is on by default in most x265 presets[cite: 8845, 9667]. |
| Deblocking Filter Enabled | Confirmed Active | *(Default enabled)* | [cite_start]The deblocking filter is enabled by default in x265 and did not require a specific flag[cite: 8837, 9698]. |
| Complex RDO Decisions | High DST/TS Usage | `--rd 4` | [cite_start]Sets the Rate-Distortion Optimization (RDO) level to a higher value to encourage more exhaustive analysis, including the evaluation of DST[cite: 8181, 8184]. |
| All-Intra Configuration | Research Scope | `--keyint 1` | [cite_start]Enforces an All-Intra encoding configuration, consistent with the project scope[cite: 8488, 8489]. |

#### 3.2.1. Resulting "Clone" Command Configuration

For clarity and reproducibility, the final command template used for the verification encodes is provided below. This command is constructed by overriding the `medium` preset defaults with the specific parameters derived from our analysis.

```bash
x265 --input <input_file.yuv> --input-res <width>x<height> --fps <fps> \
--output <output_file.hevc> --qp <QP_VALUE> \
--preset medium \
--ctu 32 \
--min-cu-size 8 \
--tu-intra-depth 3 \
--tskip \
--sao \
--rd 4 \
--keyint 1
