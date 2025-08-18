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
