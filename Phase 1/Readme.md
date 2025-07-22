#### 1.1 Experimental Setup

The x265 software encoder (version 5.1.4) was utilized for all encoding experiments. All encodes were strictly configured for **all-intra coding** (`--keyint 1`), ensuring that each frame is independently encoded without inter-frame prediction dependencies. **Adaptive Quantization (AQ) was explicitly disabled** (`--aq-mode 0`) to maintain a consistent quantization process across all frames and avoid dynamic QP adjustments that could obscure the direct impact of the set QP value.

```sh
x265 --input ~/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv   --input-res 1280x720   --fps 30   --frames 129   --intra --keyint 1 --min-keyint 1  --bframes 0 --scenecut 0 --qp 27  --no-opt-qp-pps   --ipratio 1.0  -o ControlledBurn_test_output.265
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

Python scripts were developed to automate the data processing and visualization, including:
1.  **CSV Parsing and Cleaning:** Reading CSV files, stripping whitespace from column headers, and converting relevant columns (e.g., PSNR, Bits, Encode Order) to numeric types. 
2.  **Visualize PSNR data:**  `plot_psnr_curves.py` script, which displays the PSNR (y,u,v) value of each frame at different QPs of each preset in the form of a visual curve over time, and generates a PSNR curve for each frame
3.  **Average PSNR Calculation:** `analyze_psnr.py` script,For each QP-Preset combination, the average PSNR for Y, U, and V components across all frames in the video sequence was calculated.

#### 1.3 High-Precision Energy Measurement: Confidence Interval Testing

To ensure the statistical validity of the energy data, we introduced Confidence Interval (CI) testing and separated the energy data collection from any other processing tasks.

1. `measure_raw_energy.sh` (Purified Data Collection Script):

   * A streamlined Bash script whose sole purpose is to perform multiple measurements (up to 50) for each encoding configuration in a quiescent system environment.
   * To minimize measurement overhead, the script uses parameters like `--log-level none` and `-o /dev/null` to suppress all logging and file output from x265.
   * It records only the raw Core domain RAPL energy readings (before and after encoding) into `raw_core_energy_measurements.csv`.

2. `process_and_analyze.py`(Post-Processing Script):

   * This Python script reads the raw data file generated above.
   * It implements the confidence interval test algorithm: for each set of measurements, it iteratively calculates the confidence interval width until it is less than 2% of the mean, or a maximum number of iterations is reached.
   * The algorithm includes outlier removal logic to further enhance the stability of the results.
   * It also integrates RAPL counter overflow handling to ensure accurate energy calculation for long-running encoding tasks.
   * The final output is a clean dataset named `stable_core_energy_measurements_final.csv`, containing a single, statistically validated, stable average energy value for each configuration.
#### 1.4  BD-Metrics Analysis

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
