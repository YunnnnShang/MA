#### 1.1 Experimental Setup

The x265 software encoder (version 5.1.4) was utilized for all encoding experiments. All encodes were strictly configured for **all-intra coding** (`--keyint 1`), ensuring that each frame is independently encoded without inter-frame prediction dependencies. **Adaptive Quantization (AQ) was explicitly disabled** (`--aq-mode 0`) to maintain a consistent quantization process across all frames and avoid dynamic QP adjustments that could obscure the direct impact of the set QP value.

```sh
x265 --input ~/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv   --input-res 1280x720   --fps 30   --frames 129   --intra --keyint 1 --min-keyint 1  --bframes 0 --scenecut 0 --qp 27  --no-opt-qp-pps   --ipratio 1.0  -o ControlledBurn_test_output.265
```

Two distinct video sequences were used as input sources to cover different resolutions and content complexities:
* **4K Sequence:** `BoxingPractice_3840x2160_5994fps_8bit_420.yuv`
    * Resolution: 3840x2160
    * Frame Rate: 59.94 fps
    * Total Frames: 130 frames
* **HD Sequence:** `ControlledBurn_1280x720p30_420.yuv`
    * Resolution: 1280x720
    * Frame Rate: 30 fps
    * Total Frames: 130 frames

For each video sequence, a matrix of encoding configurations was tested:
* **Quantization Parameters (QP):** 22, 27, 32, 37
* **Presets:** `ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`, `placebo`

For every encoding run, detailed frame-level statistics were collected using x265's `--csv-log-level 2` option, capturing metrics such as PSNR (Y, U, V components) and bits consumed per frame.


#### 1.2 Data Processing and Analysis

Python scripts were developed to automate the data processing and visualization, including:
1.  **CSV Parsing and Cleaning:** Reading CSV files, stripping whitespace from column headers, and converting relevant columns (e.g., PSNR, Bits, Encode Order) to numeric types. 
2.  **Visualize PSNR data:**  `plot_psnr_curves.py` script, which displays the PSNR (y,u,v) value of each frame at different QPs of each preset in the form of a visual curve over time, and generates a PSNR curve for each frame
3.  **Average PSNR Calculation:** `analyze_psnr.py` script,For each QP-Preset combination, the average PSNR for Y, U, and V components across all frames in the video sequence was calculated.
   
