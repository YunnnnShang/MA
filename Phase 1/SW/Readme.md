#### 1.1 Experimental Setup

The x265 software encoder (version 4.1) was utilized for all encoding experiments. All encodes were strictly configured for **all-intra coding** (`--keyint 1`), ensuring that each frame is independently encoded without inter-frame prediction dependencies. **Adaptive Quantization (AQ) was explicitly disabled** (`--aq-mode 0`) to maintain a consistent quantization process across all frames and avoid dynamic QP adjustments that could obscure the direct impact of the set QP value.

```sh
x265 --input ~/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv   --input-res 1280x720   --fps 30   --frames 130   --intra --keyint 1 --min-keyint 1  --bframes 0 --scenecut 0 --qp 27  --no-opt-qp-pps   --ipratio 1.0  -o ControlledBurn_test_output.265
```

5 distinct video sequences were used as input sources to cover different resolutions and content complexities:
* **4K Sequence:** `BoxingPractice_3840x2160_5994fps_8bit_420.yuv`
    * Resolution: 3840x2160
    * Frame Rate: 59.94 fps
    * Total Frames: 130 frames
    * Path:/home/or16ixuv/thesis_videos/aom_8bit/a1_4k/BoxingPractice_3840x2160_5994fps_8bit_420.yuv
* **2K Sequence:** `Aerial3200_1920x1080_5994_8bit_420.yuv`
    * Resolution: 1920x1080
    * Frame Rate: 59.94 fps
    * Total Frames: 130 frames
    * Path:/home/or16ixuv/thesis_videos/aom_8bit/a2_2k/Aerial3200_1920x1080_5994_8bit_420.yuv
* **720p Sequence:** `ControlledBurn_1280x720p30_420.yuv`
    * Resolution: 1280x720
    * Frame Rate: 30 fps
    * Total Frames: 130 frames
    * Path:/home/or16ixuv/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv
* **360p Sequence:** `SnowMountain_640x360_2997.yuv`
    * Resolution: 640x360
    * Frame Rate: 29.97 fps
    * Total Frames: 130 frames
    * Path:/home/or16ixuv/thesis_videos/aom_8bit/a4_360p/SnowMountain_640x360_2997.yuv
* **270p Sequence:** `SparksElevator_480x270p_5994_8bit.yuv`
    * Resolution: 480x270
    * Frame Rate: 59.94 fps
    * Total Frames: 130 frames
    * Path:/home/or16ixuv/thesis_videos/aom_8bit/a5_270p/SparksElevator_480x270p_5994_8bit.yuv
For each video sequence, a matrix of encoding configurations was tested:
* **Quantization Parameters (QP):** 22, 27, 32, 37
* **Presets:** `ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`, `placebo`

For every encoding run, detailed frame-level statistics were collected using x265's `--csv-log-level 2` option, capturing metrics such as PSNR (Y, U, V components) and bits consumed per frame.


#### 1.2 Data Processing and Analysis

A series of Python scripts were developed to automate the data collection and analysis process, ensuring consistency and repeatability across all 48 video sequences. The workflow was designed to first gather the fundamental rate-distortion data and then perform a quantitative efficiency comparison.


##### 1.2.1 Rate-Distortion and Performance Data Collection

The primary data on video quality and encoding performance was collected using a dedicated Python script, designed for robust and comprehensive metric extraction.

1. `generate_rd_data.py` (Comprehensive R-D Data Collection Script):This script automates the process of encoding each of the 48 video sequences across all 10 presets and 4 QP values.
   *  **Strict R-D Conditions:** To ensure accurate and comparable results for the subsequent BD-Metrics analysis, a rigorous set of x265 parameters was used to maintain a constant QP and disable adaptive optimizations that could influence the rate-distortion characteristics. The core command structure is as follows:
      ```sh
      x265 ... --preset [preset] --qp [QP] --tune psnr --psnr --csv [log_file.csv] --csv-log-level 2 --no-opt-qp-pps --ipratio 1.0
      ```
   
   *  **Integrated Multi-Metric Collection:** For each encoding configuration, the script systematically and efficiently gathers a comprehensive set of metrics:
        1. **PSNR (Y, U, V):** The script calls the `x265` executable with the `--psnr` and `--csv` flags enabled. This allows the encoder to calculate the PSNR for all three color components (Y, U, and V) internally during the encoding process. The detailed frame-by-frame results are saved to a temporary CSV file. The script then reads this file and computes the average PSNR for each component, providing a reliable source for the complete objective quality score.
        2. **Bitrate:** The final `bitrate_kbps` is parsed directly from the summary output of the x265 process.

*  **Generated Dataset:** `bitrate_psnr_results.csv`
     This file contains the foundational rate-distortion data for all sequences. As shown in the provided screenshot, each row represents a unique encoding run and includes the `video_name`, `qp`, `preset`, `bitrate_kbps`, and the corresponding PSNR values for all three components: `psnr_y, psnr_u, and psnr_v`.

      This dataset is the primary source for plotting complete Rate-Distortion (R-D) curves and serves as the direct input for the subsequent BD-Metrics analysis across all color channels.
   
##### 1.2.2 High-Precision Energy Measurement: Confidence Interval Testing

To ensure the statistical validity of the energy data, a separate and purified measurement process was implemented.

1. `measure_raw_energy.sh` (Purified Data Collection Script): A streamlined Bash script whose sole purpose is to perform multiple measurements (15 repetitions) for each encoding configuration in a quiescent system environment. To minimize measurement overhead and isolate the encoding task, all logging and file output from x265 are suppressed（`--log-level none` and `-o /dev/null` ).It records only the raw Intel RAPL energy counter values before and after each encode into `raw_core_energy_measurements.csv`.

2. `process_and_analyze.py`(Post-Processing Script): This Python script processes the raw energy data by implementing a confidence interval (CI) test algorithm. For each set of 15 measurements, it iteratively calculates the mean and confidence interval, removing outliers until the interval width is less than 2% of the mean. This process yields a single, statistically stable average energy value for each configuration. The script also handles potential RAPL counter overflow to ensure accuracy.

##### 1.2.3 BD-Metrics Analysis for Efficiency Comparison

To perform a quantitative evaluation of the compression efficiency of the different x265 presets, a Bjontegaard-Delta (BD) analysis was conducted.

1.  `bitrate_psnr_results.csv`
   * For a standard comparison of encoding efficiency (BD-Metrics analysis), a separate and precise set of Rate-Distortion (R-D) data is required. The `generate_rd_data.py` script was developed for this purpose.
   * To ensure the QP value is strictly constant (disabling adaptive quantization and other optimizations), the script uses a more rigorous set of parameters when calling `x265`, which is crucial for the accuracy of the subsequent BD-rate calculations:
   ```
   x265 ... --qp ${QP} --no-opt-qp-pps --ipratio 1.0 --tune psnr ...
   ```
2. `analyze_bdrates.py`
   * As a final quantitative evaluation of the performance of different x265 presets, a Bjontegaard-Delta (BD) analysis was performed.
   * The script reads the data from `bitrate_psnr_results.csv`, uses the `medium` preset as a reference, and calculates the BD-rate (%) and BD-PSNR (dB) for the other nine presets.
   * The analysis results are saved in `bd_metrics_results.csv`, providing highly convincing data for the thesis on the encoding efficiency differences.

Through the entire workflow, we have produced three core, clean datasets for different analysis purposes:

1. `stable_core_energy_measurements_final.csv`:
   * Content: Stable average energy data, validated with confidence interval tests.
   * Purpose: Primary input for energy modeling.

2. `bitrate_psnr_results.csv`:
   * Content: Bitrate and PSNR data collected in a strictly constant-QP mode.
   * Purpose: Plotting R-D curves and for BD-Metrics analysis.

3. `bd_metrics_results.csv`:
   * Content: Quantitative comparison results (BD-rate and BD-PSNR) between different x265 presets.
   * Purpose: To be used directly in the results chapter of the thesis to demonstrate differences in encoding efficiency.
