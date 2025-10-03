### Summary of HEVC Coding Analysis Metrics

We categorize these metrics based on the core steps of the HEVC encoding process into four main categories: **Block Partitioning**, **Prediction**, **Transform and Quantization**, and **Loop Filtering**.

#### 1. Block Partitioning & Structure

These metrics determine how the encoder divides a frame into blocks of varying sizes for processing.

* **Partition Schemes (Partition Types)**
* **Purpose**: Describes how a coding unit (CU) is divided into smaller prediction units (PUs). This is a core feature of HEVC and directly impacts coding efficiency.
* **Specific Metrics**: `Partition types: 2Nx2N`, `NxN`, `2NxN`, `Nx2N`, etc.
* **Analysis Method**: Use our general `prepare_stats` function for processing, searching for `'Partition types: '`.

* **CU Size (Coding Unit Size)**
* **Purpose**: Counts the usage frequency of coding units (CUs) of different sizes. CUs are the basic unit for HEVC image division.
* **Specific indicators**: `CU sizes: 64x64`, `32x32`, `16x16`, `8x8`.
* **Analysis method**: Use a general function and search for the keyword `'CU sizes: '`.

* **PU Size (Prediction Unit Size)**
* **Purpose**: Counts the usage frequency of prediction units (PUs) of different sizes. PUs are the basic unit for intra-frame and inter-frame prediction.
* **Specific indicators**: `PU sizes: 64x64`, `32x32`, `16x16`, `4x4`, and other sizes.
* **Analysis method**: Use a general function and search for the keyword `'PU sizes: '`.

* **Slices**
* **Purpose**: Counts the number of slices each frame is divided into. Slices are the basic unit for parallel processing and error recovery.
* **Specific metric**: `#Slices`.
* **Analysis method**: Use a **dedicated analysis script** and the `describe()` function to calculate its statistical distribution (average, maximum, etc.).

#### 2. Prediction

This type of metric describes how the encoder uses previously encoded pixels to predict the pixel values ​​of the current block. It is mainly divided into intra-frame and inter-frame prediction. Your project will focus on **Intra Prediction**.

* **Intra Prediction Modes**
* **Purpose**: Counts the frequency of use of various prediction directions (angles) and modes during intra-frame prediction. * **Specific Metrics**:
* **Luma**: `Intra luma modes: 0`, `1`...`34` (representing DC, Planar, and various angular modes).
* **Chroma**: `Intra chroma modes: DM`, `DC`, `Planar`, `Vert`, `Horiz`.
* **Analysis Method**: Use a general function in two steps, searching for `Intra luma modes: ' and `Intra chroma modes: ' respectively.

* **Screen Content Coding Tool (SCC)**
* **Purpose**: Counts the usage of HEVC's special coding tools for screen content (such as computer desktops and documents). * **Specific Metrics**:
* `Inter PU type: IBC` (Intra Block Copy)
* `Pred mode: Palette` / `Intra PU type: Palette` (Palette mode)
* **Analysis Method**: Use a **specialized analysis script** to sum and calculate statistics for these specific columns.

#### 3. Transform & Quantization

After obtaining the prediction residual, the encoder further compresses the data through these two steps.

* **TU Size**
* **Purpose**: Counts the frequency of use of transform units (TUs) of different sizes. TUs are the basic unit for performing discrete cosine transforms (DCTs).
* **Specific Metrics**: `TU sizes: 32x32`, `16x16`, `8x8`, `4x4`.
* **Analysis Method**: Use a general function, searching for `TU sizes: '

**TU Depth**
**Purpose**: Describes the depth of the transform unit (TU) relative to the coding unit (CU).
**Specific indicators**: `TU depth (CU 64): 0`, `TU depth (CU 32): 1`, etc.
* **Analysis Method**: Use a general function, searching for the keyword `'TU depth \('` (note that the brackets must be escaped).

* **Transform Types**
* **Purpose**: Counts the types of transform kernels used during the transform phase (e.g., DCT-II, DST-VII).
* **Specific Metric**: The various values ​​in the `Transform_Type` column (e.g., `DCT_DCT`).
* **Analysis Method**: Use a **dedicated analysis script**, using the `value_counts()` function to count the occurrences of different values ​​in a single column.

#### 4. In-Loop Filtering

To improve the visual quality of reconstructed images, HEVC implements filters within the encoding loop.

* **Post-Processing Filters**
* **Purpose**: Counts the usage and patterns of the deblocking filter (deblocking) and sample adaptive offset (SAO) filters.
* **Specific Metric**:
* **Deblocking**: `Deblocking luma vertical: No deblocking`, Luma strong, etc.
* **SAO**: `SAO type luma: No Operation`, `Band`, `Edge`, etc.
* **Analysis method**: Use universal functions for each, searching for keywords such as `'Deblocking luma vertical: '` and `'SAO type luma: '`.
