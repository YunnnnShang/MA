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

### 总体评价

通过VQ Analyzer工具提取并对比了在相同QP（量化参数）下，不同软件预设（presets）和硬件预设的编码决策统计数据。这些数据非常清晰地表明：**硬件编码器并非简单地等同于软件编码器的某个“快速”版本，而是在算法层面有着自己独特的、有时甚至是截然不同的决策机制。** 这正是论文核心价值的体现。

---

下面是对上传的毕业论文第三阶段 PPT（`praesentation16zu9_en.pptx`）中数据的分析和结论。该 PPT 汇总了对 每序列前1帧的编码统计，比较了软件编码器（x265）和硬件编码器（NVIDIA Jetson Orin NX NVENC）在不同预设下的行为。为便于理解，分析按照 HEVC 编码流程的主要阶段进行归纳，外部文献引用用来说明指标的设计初衷。

### 1. 块划分与分区方案

* **预测单元 (PU) 尺寸分布**：在所有预设下，小尺寸 PU（4×4 和 8×8）占比最高，符合 HEVC 将大 CTU 按四叉树细分为小 CU 并允许最小 4×4 PU 的设计。软件编码器在 `medium` 至 `superfast` 预设使用大量 4×4 PU（约 210～212 万个），8×8 PU 次之，而 16×16 与 32×32 PU 较少；到了 `ultrafast` 预设，4×4 和 8×8 PU 几乎消失，16×16 和 32×32 PU 明显增加，表明编码器为提升速度而选择更大的预测块。硬件编码器在低速预设也大量使用 4×4 和 8×8 PU，但随预设提速，会逐渐增加 8×8 和 16×16 的比例，并减少 4×4，说明硬件端同样倾向用大块减少计算。

* **分区模式**：统计仅出现了两种对称分区模式 2Nx2N 与 NxN，其他不对称或矩形模式均为 0。2Nx2N 块数量在软件端由约 167 万逐步降到 96 万（ultrafast），NxN 块数在 `medium`～`superfast` 约 53 万，在 `ultrafast` 为 0；硬件端 2Nx2N 块数从 141 万降到 69 万，NxN 块数从 53 万降至 31 万。说明针对本数据集，编码器主要使用全块或四分块，随着预设加速减少分区次数。

### 2. 预测阶段

* **帧内亮度模式**：HEVC 定义 35 种帧内亮度模式（33 个方向加 DC、平面）。软件编码器在中低速预设中广泛使用多种模式：模式 0（DC）次数最多（约 115～119 万），模式 1（45°）、模式 3 等也有数十万；模式分布相对均衡。到了 `ultrafast` 预设，大多数模式的次数骤减，很多模式为零，这意味着编码器仅使用少数简单模式加速处理。硬件编码器更倾向于使用少数模式，并在高速预设下将许多模式完全禁用。例如，硬件在 `fast`、`ultrafast` 时模式 0 为 46 万和 68 万，而其他多数模式为零或几万，显示其预测策略更简单。

* **帧内色度模式**：衍生模式 DM 占绝对主导，软件在慢速预设中约 174 万次，`ultrafast` 减至 69 万次；DC、平面、水平、垂直模式各有 6～14 万次。硬件编码器 DM 次数约 117 万（慢速）降至 53 万（fast），同时显著增加了平面、DC、水平和垂直模式的使用，这些模式次数大多比软件高一倍以上。线性模型 LM 未使用。

### 3. 变换与量化

* **变换单元 (TU) 尺寸**：HEVC 支持 4×4 至 32×32 离散余弦/正弦变换。在软件端，中低速预设 4×4 TU 约 248～242 万，8×8 TU 约 102 万，16×16 TU 约 55 万；在 `ultrafast` 预设，4×4 TU 变为 0，8×8 TU 降至 54 万，16×16 TU 升至 85 万，32×32 TU 也从 18 万增至 22 万。硬件端在 `slow`、`medium` 预设 4×4 TU 约 247 万，但在 `fast`、`ultrafast` 预设分别降至 57 万和 74 万，同时 8×8 和 16×16 TU 增长。说明随着编码速度提升，两种编码器都偏向较大 TU 以降低变换开销。

* **TU 深度**：软件编码器主要在 32×32 CU 深度 0 和 16×16 CU 深度 0 上产生 TUs；8×8 CU 深度 1 的计数高达 157 万，说明对 8×8 CU 经常继续细分。硬件在 `fast`、`ultrafast` 时则对 16×16 CU 进行深度 1 分割（约 73～101 万次），而 8×8 CU 深度 1 次数为零。这表明硬件编码器在高预设下倾向于对 16×16 CU 做额外变换划分，以补偿较少的 4×4 TU。

* **变换类型**：HEVC 推荐 4×4 块使用 DST 变换。数据中，软件在 `medium`～`superfast` 完全使用 DST（120 次），在 `ultrafast` 改用 DCT（120 次）；硬件在 `slow`、`medium` 也使用 DST（约 117 次），在 `fast`、`ultrafast` 完全使用 DCT（5760 次）。这说明高速度模式中双方都用 DCT 来降低复杂度。

### 4. 环路滤波

* **去块滤波（DBF）**：多数边界采用弱滤波，软件在 `medium` 预设有 385 万次弱滤波，到了 `ultrafast` 降至 285 万；强滤波和不滤波的次数也随预设升高而减少。硬件在 `slow`、`medium` 预设的统计缺失（可能未记录），但在 `fast`、`ultrafast` 时弱滤波约 343～379 万次，强滤波约 126～138 万次，比例与软件相近。总体看，弱滤波是主要模式，且高预设时滤波量减少。

* **采样自适应偏移（SAO）**：软件仅在 `medium` 到 `veryfast` 预设启用 SAO，涉及 No‑op、Band、0°、45°、90°、135° 边缘等六种类型，平均每类几千到一万七千次；在 `superfast`、`ultrafast` 完全禁用。硬件则在所有预设启用 SAO，但大部分 CTU（约 30 万）选择不进行操作，启用 Band 或 Edge 类 SAO 的 CTU 数随预设提升而略有增长（如 45° SAO 从 38k 增至 47k）。因此硬件编码器即便在快速模式也保留 SAO，软件则通过关闭 SAO 来加速。

* **SCC 工具**：无论软件还是硬件，块内复制（IBC）和 Palette 模式的计数均为 0，符合这些工具主要针对屏幕内容；因此对自然视频序列不会启用。

### 5. 其它指标

* **Slices**：对每帧统计的切片数显示均为 1，意味着两个编码器在所有预设下都将整帧编码为一个切片。这简化了并行处理，但缺乏错包容能力。

### 总体结论

1. **块大小与分区策略**：小块（4×4、8×8）广泛用于捕捉纹理细节，随预设提速逐渐让位于 16×16 和 32×32。软件端在 `ultrafast` 彻底禁用 4×4 和 8×8 块，而硬件端在高预设仍然保留一定 8×8 块但减少 4×4。

2. **帧内预测模式**：软件中低速预设下充分利用 HEVC 33 个方向模式，硬件在快速模式下简化为少数模式。色度预测以衍生模式 DM 为主，但硬件显著增加了平面、DC、水平和垂直模式的比例，显示其内部实现与 x265 有差异。

3. **变换与量化**：双方都偏好小尺寸 TU、DST 变换和浅层深度，在高预设时逐渐转向大尺寸 TU、DCT 变换和在较大 CU 上进行深层分割。

4. **环路滤波**：弱去块滤波是主流，强滤波和无滤波次之；软件在高速预设关闭 SAO，硬件则始终启用 SAO 但以大量 No‑op 为主。

5. **编码器差异**：整体趋势表明，两种编码器在遵循 HEVC 基本规范的同时，采用不同的折衷策略：x265 通过减少小块和关闭 SAO 来换取速度，而 NVIDIA 硬件在高速模式下依然执行 SAO 和部分小块分割；硬件在色度模式选择上更加多样，说明其内置算法与 x265 不同。

这些分析有助于理解不同预设下编码器的行为，为后续的编码优化、视频质量评估或算法改进提供依据。
