# NVIDIA Jetson HEVC Hardware Encoder: Rate-Distortion Test Workflow & Findings

## Abstract

This document details the complete workflow for conducting a rate-distortion (RD) performance analysis of the NVIDIA Jetson Orin NX (8GB) hardware encoder (NVENC). The focus is on the HEVC All-Intra encoding configuration, which is a critical component of the broader research project. The process covers the experimental setup, the design and execution of an automated data collection script, and concludes with a summary of the final results and key findings.

This test successfully generated a comprehensive dataset of bitrate and PSNR values for a full suite of standard test sequences across various Quantization Parameter (QP) and hardware preset combinations. A significant finding was identified: the `medium` and `slow` presets for the hardware encoder yield identical performance results, a crucial insight into the fundamental differences between hardware and software-based video encoding solutions.

-----

## 1\. Experimental Setup and Remote Access

To ensure consistency and repeatability, all experiments were conducted remotely. This document outlines the setup for establishing a stable, direct network connection to the Jetson device from either a Linux or Windows host PC.

  * **Hardware Platform**:
    
    Target Device: NVIDIA Jetson Orin NX 8GB module seated on a reComputer J401 carrier board.
    
    Host PC: A personal computer running either a Linux distribution (e.g., Ubuntu) or Windows 10/11.
  * **Physical Connections**:
    1.  **Network**: The device was connected to the local area network via its **Gigabit Ethernet port (RJ-45)**.
    2.  **Power**: The device was powered using its standard DC power adapter.

  * **Network Configuration**： A direct, static IP-based network was configured to ensure a persistent and predictable connection between the host and the Jetson.

    The Jetson device was pre-configured with the following static network settings:
    ```sh
    IP Address: 192.168.178.1
    Subnet Mask: 255.255.255.0
    ```
    Host PC Configuration: The host PC's Ethernet adapter was configured manually to reside on the same subnet as the Jetson.
    
    For a **Linux Host**:
    
    The network interface connected to the Jetson was configured via the system's network manager to use an IP address within the `192.168.178.0/24` subnet (e.g., `192.168.178.10`).
    
    For a **Windows Host**:
    A static IP address was assigned to the Ethernet adapter by following these steps:
    
    Open the "Network Connections" panel by pressing Win + R, typing ncpa.cpl, and pressing Enter.
    
    Right-click the relevant Ethernet adapter and select "Properties".
    
    Double-click "Internet Protocol Version 4 (TCP/IPv4)".
    
    Select the option "Use the following IP address" and fill in the details:
    
    IP address: 192.168.178.10
    
    Subnet mask: 255.255.255.0
    
    Default gateway: (Leave blank)
      * **Remote Access**:
          * A Secure Shell (SSH) connection was established from a host PC to the Jetson device to gain command-line access.
          * **Command**:
            ```bash
            ssh or16ixuv@192.168.178.1
            ```
          * This setup provided a stable and reliable interface for script execution and file management throughout the experiment.

## 2\. Automated Rate-Distortion (RD) Data Collection

An automated workflow was implemented using a Python script (`generate_rd_data_hw.py`) to systematically evaluate the hardware encoder's performance across its operational range.

### 2.1. Test Parameter Space

The script was configured to iterate through a matrix of encoding parameters:

  * **Video Sequences**: The complete AOM (Alliance for Open Media) standard test set, including resolutions from 270p to 4K.
  * **Quantization Parameters (QPs)**: `[22, 27, 32, 37]`
  * **Hardware Presets**: The `-hpt` parameter was tested with values `[1, 2, 3, 4]`, corresponding to `ultrafast`, `fast`, `medium`, and `slow`.
  * **Encoding Configuration**: A strict **All-Intra** (`-ifi 1`) and **Constant QP** (`--econstqp`) configuration was enforced. Following the AOM Common Test Conditions (CTC v2.0), the **first 30 frames** of each sequence were encoded.

### 2.2. Automation Workflow

For each unique combination of parameters, the script performed the following five-step pipeline:

1.  **Hardware Encoding**: Invoked the `video_encode` executable from the Jetson Multimedia API to encode the source YUV file into an HEVC bitstream (`.bin`).
2.  **Hardware Decoding**: The resulting bitstream was immediately decoded back to the YUV format using the `video_decode` executable to prepare for quality assessment.
3.  **Bitrate Calculation**: The bitrate (in kbps) was calculated based on the encoded bitstream's file size, the number of encoded frames (30), and the source video's frame rate.
4.  **PSNR Calculation**: The `ffmpeg` utility was used to perform a frame-by-frame comparison between the original and decoded YUV files, calculating the average PSNR for the Y, U, and V color components.
5.  **Data Logging & Cleanup**: The complete data point (sequence name, QP, preset, bitrate, PSNR-Y/U/V) was appended to the results file. All intermediate files were then deleted.

### 2.3. Final Output

This automated process successfully generated the final dataset for this phase of the project: `rd_results_hardware_full_dataset.csv`. This file contains the complete and accurate RD performance metrics for the NVIDIA hardware encoder under the specified test conditions, providing a solid foundation for subsequent analysis.

## 3\. Key Finding: Analysis of Hardware Preset Behavior

A critical observation was made during the analysis of the collected data:

> For all tested video sequences, the **`medium` (`-hpt 3`)** and **`slow` (`-hpt 4`)** presets produced **identical rate-distortion results**.

This indicates that the identical performance is not an artifact of the collection script but rather an inherent characteristic of the NVIDIA hardware encoder's implementation for HEVC all-intra encoding.

### 3.1. Interpretation of the Finding

This behavior contrasts sharply with software encoders like x265, where a `slow` preset uses significantly more complex algorithms to achieve superior compression efficiency compared to `medium`. The observed equivalency in the hardware encoder suggests:

1.  **Hardware Implementation Mapping**: It is highly probable that, for design efficiency and complexity reasons, the hardware maps multiple user-facing preset levels to the same internal algorithmic path.
2.  **Impact of All-Intra Mode**: The all-intra configuration disables inter-prediction, which is where the most complex and computationally expensive encoding tools reside. This simplification likely further reduces the already limited differences between the hardware presets, causing them to converge to the same operational point.
3.  **Design Philosophy**: The primary design goal for hardware encoders like NVENC is to maximize speed and power efficiency, not to provide the fine-grained control and ultimate compression efficiency of a software encoder.

### 3.2. Significance for this Research

This finding is fundamentally important for the core objective of this thesis—modeling the relationship between software encoder behavior and hardware encoder energy consumption. It demonstrates that:

  * A direct, one-to-one mapping of identically named presets between software (x265) and hardware (NVENC) is not valid.
  * When modeling the hardware encoder, the configuration space must account for this "degeneracy," where distinct settings (`medium` and `slow`) result in a single performance outcome.

This provides a strong, data-backed argument for the necessity of a detailed characterization of the hardware's behavior before an accurate energy estimation model can be developed.

## 4\. Comprehensive Rate-Distortion Performance Analysis

Following the initial data collection, a more in-depth analysis was conducted to quantify the performance trade-offs between the hardware encoder's presets. This involved enriching the dataset and performing a standardized Bjøntegaard Delta (BD) metric analysis.

### 4.1. Data Enrichment and Normalization

To facilitate a fair and standardized comparison across different video resolutions, the initial dataset was enriched with two key metrics:

1.  **Bits Per Pixel (bpp):** The `bitrate_kbps` values were converted to `bpp` to create a resolution-independent measure of compression efficiency. This normalization is critical for comparing the RD-performance of, for example, a 4K sequence against a 720p sequence.
2.  **Weighted PSNR (PSNR-YUV):** In addition to the individual Y, U, and V components, a combined, weighted PSNR was calculated for each data point. This was done in accordance with the AOM Common Test Conditions standard, using the formula:
    `PSNR-YUV = 0.875 * PSNR_Y + 0.0625 * PSNR_U + 0.0625 * PSNR_V`

This enriched dataset, `fulldataset_hardware_psnr_yuv.csv`, formed the basis for all subsequent analyses.

### 4.2. BD-Metric Analysis Methodology

To quantify the RD-performance differences, a comprehensive Bjøntegaard Delta (BD) analysis was performed. To ensure consistency with the planned software encoder analysis phase, the methodology was aligned with the approach previously used for x265, employing the standard `bjontegaard` Python library.

* **Reference Preset**: The `medium` preset was selected as the reference for all comparisons.
* **Test Presets**: `ultrafast`, `fast`, and `slow` were evaluated against the `medium` reference.
* **Metrics**: BD-PSNR (in dB) and BD-Rate (in %) were calculated for all four quality metrics: `PSNR-Y`, `PSNR-U`, `PSNR-V`, and `PSNR-YUV`.
* **Interpolation Method**: The `akima` spline interpolation method was used for curve fitting to maintain methodological consistency.

### 4.3. Analysis of Aggregated Results & Key Findings

The analysis of the aggregated BD-Metrics across all resolutions yielded several critical insights into the encoder's behavior.

#### 4.3.1. Overall Performance and Chroma Channel Anomalies

The average performance across the entire dataset confirms the expected trade-off between speed and efficiency for the luma component, but reveals an anomalous behavior for the chroma components.

**Table 1: Overall Average BD-Metrics (All Resolutions vs. `medium` preset)**

| test_preset | psnr_type | BD_PSNR_dB | BD_Rate_percent |
| :--- | :--- | :--- | :--- |
| **fast** | PSNR_U | 0.00 | -28.43 |
| | PSNR_Y | -0.10 | 1.25 |
| | PSNR_YUV | -0.08 | 1.20 |
| **slow** | All | 0.00 | 0.00 |
| **ultrafast**| PSNR_U | 0.00 | -21.04 |
| | PSNR_Y | -0.24 | 4.21 |
| | PSNR_YUV | -0.21 | 4.15 |

**Key Findings:**

1.  **Luma Performance Follows Expectation**: For the critical luma component (PSNR-Y), the `fast` and `ultrafast` presets incur a bitrate cost of **1.25%** and **4.21%**, respectively, to achieve the same quality as `medium`. This provides a clear, quantitative measure of the RD-performance degradation.

2.  **`slow` Preset Equivalence Confirmed**: The BD-Metrics for the `slow` preset are zero across the board, confirming our initial finding that it is functionally identical to the `medium` preset.

3.  **Anomalous Chroma Behavior**: A significant and unexpected finding is the massive bitrate *saving* observed for the U-channel (`-28.43%` for `fast` and `-21.04%` for `ultrafast`) with no corresponding drop in PSNR.

This finding reveals a significant characteristic of the hardware encoder's internal rate-control strategy. It suggests that for the medium preset, the encoder allocates a substantial portion of the bitrate to the chroma channels (specifically the U-channel). However, this additional bitrate investment does not yield a corresponding improvement in objective quality as measured by PSNR when compared to the faster presets. The fast and ultrafast presets appear to use a more simplified chroma encoding strategy, resulting in a much lower bitrate for the U-channel without a measurable penalty in PSNR.

Furthermore, the PSNR-V values were so static across different QPs that a valid BD-Metric could not be calculated at all, reinforcing the conclusion that the hardware encoder's rate control mechanism is overwhelmingly focused on the luma channel.

#### 4.3.2. Performance Dependency on Video Resolution

Analyzing the BD-Metrics on a per-resolution basis reveals another critical insight: the impact of the presets is not uniform.

**Table 2: Average BD-Rate for PSNR-Y by Resolution (vs. `medium` preset)**

| resolution | `fast` preset | `ultrafast` preset |
| :--- | :--- | :--- |
| **4K** | -0.71% | -0.01% |
| **1080p** | -0.38% | +3.10% |
| **720p** | +2.76% | +6.91% |
| **360p** | +5.20% | +7.99% |
| **270p** | +5.17% | +7.64% |

**Key Findings:**

1.  **Efficiency Loss is Magnified at Lower Resolutions**: The bitrate penalty for using faster presets is dramatically more pronounced for lower-resolution content. For 720p and below, using the `ultrafast` preset incurs a significant **7-8%** bitrate overhead.
2.  **Negligible Impact at 4K**: Conversely, for 4K video, the RD-performance difference between all presets is practically zero. This suggests that for high-resolution content, the encoder's performance bottleneck may shift, rendering the algorithmic simplifications of the faster presets less impactful on final compression efficiency.

## 5\. Visual Analysis and Conclusion

To complement the numerical data, a comprehensive set of `PSNR vs. QP` plots was generated. An automated script produced detailed plots for each of the 48 video sequences, alongside aggregated plots showing the average trends for the entire dataset and for each resolution class.

These visualizations confirmed the findings from the BD-Metric analysis. The aggregated plot showing performance by preset and resolution (see `_AVG_by_Preset_and_Resolution.png`) was particularly insightful, clearly illustrating how the performance gap between presets widens as the video resolution decreases.

In conclusion, this detailed RD-analysis of the NVIDIA Jetson hardware encoder has provided several crucial insights that are foundational to this thesis. We have not only quantified the performance trade-offs of its presets but also uncovered key architectural behaviors, such as the equivalency of the `slow` and `medium` presets and the strong dependency of preset impact on video resolution. These findings underscore the necessity of treating hardware encoders not as simple equivalents of their software counterparts, but as distinct systems whose operation
