# 分析编码器参数调整

## Analysis of hardware vs. software encoder behaviour and x265 parameter mapping

### 1 Overview and objectives

The user compared the output of an NVENC hardware H.265 encoder (running on an NVIDIA Jetson
device) with the reference x265 software encoder using multiple presets. They compiled their findings
into a presentation which shows the frequency of different prediction– and transform-unit sizes,
prediction modes, transform types, partition schemes and post-processing filters. The goal is to adjust
x265’s parameters so that its encoder behaves like the hardware encoder.

This report extracts the relevant data from the slides and cross-references it against authoritative
documentation:

- **NVENC behaviour:** NVENC is an HEVC encoder integrated in NVIDIA GPUs. The official
programming guide indicates that the hardware offers a set of predefined presets and limited
control over advanced coding tools. The guides do not explicitly list coding-unit sizes, transform
types or partition modes, but the user’s data provides those details.

- **HEVC background:** The HEVC standard uses integer DCT and DST transforms for transform sizes
from 4 × 4 up to 32 × 32. DST is used only for 4×4 luma transform units, while larger TUs use
DCT.

- **x265 documentation:** The open-source x265 encoder exposes many CLI options. Relevant
options include:

  - `--ctu` and `--min-cu-size` set the maximum and minimum coding-unit (CU) sizes. Larger CUs
  improve compression efficiency but reduce parallelism; the default maximum is 64 and the
  default minimum is 8 .

  - `--rect` and `--amp` enable rectangular (Nx2N/2NxN) and asymmetric partitions; both are
  disabled by default .

  - `--tu-intra-depth` and `--tu-inter-depth` control the depth of the transform-unit (TU)
  quad-tree. The default depth is 1, meaning the residual quad-tree is not split beyond the CU depth.

  - `--tskip` enables transform-skip mode for 4×4 TUs; it is disabled by default .

  - `--max-tu-size` sets the maximum TU size (default 32) .

  - `--fast-intra` limits the number of intra luma modes analysed (10 instead of 33) .

  - `--sao` toggles the sample-adaptive-offset filter; it is enabled by default . `--selective-sao`
  allows SAO to be enabled only for certain slice types .

  - `--deblock` controls the deblocking filter. It is enabled by default; offsets can be specified, and
  `--no-deblock` disables the filter completely .

Below, each slide’s findings are summarised and mapped to x265 parameters. Where appropriate,
multiple x265 presets are offered to match different hardware presets.

---

### 2 Prediction-unit (PU) sizes and coding-unit (CU) sizes

#### Observations from the slides

Hardware encoder uses only 32×32, 16×16, and 8×8 PUs across all presets. For **ultrafast and fast hardware presets**, the usage of 4×4 PUs is completely **zero**. In contrast, **medium and slow** hardware presets make heavy use of 4×4 blocks, with counts exceeding 2.1 million.

x265 software presets always allow 4×4 PUs, even in **ultrafast mode**, which differs significantly from NVENC’s restrictive behavior. 

To align with the hardware encoder, presets intended to mimic **fast/ultrafast** modes must explicitly prevent 4×4 PU generation, while **slow/medium** clones should retain them. The smallest allowed **CU size** influences PU usage, and `--min-cu-size` should be adapted accordingly.


#### Parameter mapping and recommendations

| Hardware preset | Observed PU usage pattern | Suggested x265 parameters | Rationale |
|-----------------|---------------------------|---------------------------|-----------|
| Slow or medium  | Extensive use of 4×4, 8×8, 16×16, and 32×32 PUs. | `--ctu 32` and default `--min-cu-size` (i.e. 8). Allow 4×4 by not restricting TU depth. | Mirrors the NVENC encoder’s rich partitioning behavior at slower presets. `--ctu 32` caps CU size to match 32×32 maximum PU. |
| Fast or ultrafast | Uses only 8×8, 16×16, 32×32 PUs; **no 4×4 PUs**. | `--min-cu-size 8 --ctu 32 --tu-intra-depth 1 --tu-inter-depth 1` | Prevents creation of 4×4 PUs and TUs. This mimics hardware constraints and simplifies block tree complexity, matching NVENC behavior. |

---

### 3 Intra luma prediction modes

#### Observations

- The **hardware encoder (NVENC)** demonstrates a selective use of intra prediction modes depending on the preset:
  - For `ultrafast`, it avoids **all odd-numbered angular modes** (e.g., modes 3, 5, 7, 9, ..., 33) while still using **even-numbered angular modes** along with **DC (mode 1)** and **Planar (mode 0)**.
  - For `fast` `medium` `slow` presets, nearly **all angular modes** (both odd and even) are used to varying degrees.
- This suggests that **ultrafast hardware encoding minimizes directional complexity**, likely for energy or latency efficiency.
- **x265**, by default, uses all 35 intra luma modes regardless of preset. This results in higher complexity but more accurate predictions. This discrepancy highlights a key simplification in hardware-based intra coding.


#### Parameter mapping

| Hardware preset | Observed intra mode usage | Suggested x265 parameters | Rationale |
|-----------------|---------------------------|---------------------------|-----------|
| Slow or medium  | Uses most or all 35 intra luma modes. | Default x265 configuration is sufficient. Optionally enable `--tskip` and disable `--fast-intra`. | Software's full-mode search mirrors NVENC slow/medium behavior. |
| Fast or ultrafast | Uses Planar, DC, and a small number of angular modes (e.g., 8, 10, 26); many modes unused. | Enable `--fast-intra` to reduce angular mode search to ~10. Optionally disable `--tskip` to match hardware constraints. | `--fast-intra` performs a sparse search (every 5th angular mode + local refinement), closely aligning with NVENC fast presets. Disabling transform skip also matches hardware limitations. |

---

### 4 Intra chroma modes

#### Observations 

The NVENC hardware encoder exhibits a strong preference for **chroma mode simplification**. In all presets, **Derived Mode (DM)** dominates chroma prediction, followed by moderate usage of DC and Planar modes. Directional modes like Horizontal, Vertical, and Diagonal are sparsely used, and **Linear Model (LM)** mode is completely unused in both software and hardware encoders.

The usage patterns remain fairly stable across slow and medium presets. However, in fast and ultrafast presets, overall chroma mode diversity decreases: DM and Planar dominate, while directionals and DC drop in frequency. This suggests that hardware encoders aggressively prune chroma prediction modes at higher speed presets to reduce complexity.

In contrast, the x265 software encoder uses nearly all chroma modes across all presets—including Diagonal, Horizontal, Vertical, and Planar—even in ultrafast mode. LM is disabled across all presets, indicating that both encoders avoid this mode due to its complexity or unsuitability for natural content.


#### Parameter suggestions

| Hardware preset   | Observed chroma mode usage                        | Suggested x265 parameters                                                                 | Rationale                                                                 |
|-------------------|---------------------------------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| Slow or medium    | DM dominant; Planar > DC > Directionals; no LM   | Use default settings; optionally set `--no-intra-refresh`, and avoid LM tools.              | x265 defaults already match this mode diversity well; no tuning needed.   |
| Fast or ultrafast | Mostly DM and Planar; lower DC/directionals      | Reduce TU depth via `--tu-intra-depth 1`, keep Planar and DM; optionally disable Diagonals and `--no-rect` and `--no-strong-intra-smoothing` to simplify chroma intra behavior. | Simplifies chroma prediction while retaining essential high-use modes.    |

---

### 5 Transform-unit sizes and transform types

#### Observations (Corrected and Augmented)

The **hardware slow and medium presets** utilize the full range of transform unit (TU) sizes—4×4, 8×8, 16×16, and 32×32—with approximately **2.48 million 4×4 TUs** each. These small TUs are primarily derived from **CU=8 blocks split at TU depth=1**, as seen from the **TU depth stats** (`CU8:1 ≈ 1.67M`) and `CU8:0 ≈ 545k` indicating 8×8 TUs. This TU structure allows **fine-grained residual coding**, supporting **high coding efficiency** especially for detailed textures.

In contrast, **fast and ultrafast hardware presets** show a **drastic reduction** in 4×4 TU usage (**567k and 741k**, respectively), and a corresponding **rise in 8×8 and 16×16 TUs**, consistent with the increase in `TU depth(CU 16)=1` (**727k for fast**, **1M+ for ultrafast**), which produces 8×8 TUs from CU=16 blocks. Notably, **CU=8 is unused** in fast/ultrafast (`CU 8:0/1 = 0`), which confirms the near-elimination of 4×4 TU generation. The continued presence of **~200k 32×32 TUs** across all presets suggests that **32×32 is not disabled**, but used selectively.

On the transform type side, **NVENC hardware** uses **DCT exclusively** in **fast and ultrafast presets**, where **DST counts are 0**, and uses DST **only sparingly** in slow/medium (**117 instances**). This matches HEVC reference behavior, where **DST is used only for 4×4 luma TUs**. The strong reduction of 4×4 TUs in fast/ultrafast presets naturally results in zero DST usage.

These observations are further corroborated by **TU Depth** statistics:

* CU=64 is never used.
* All 32×32 TUs stem from CU=32 at TU depth=0.
* All 4×4 TUs arise from CU=8 at TU depth=1.
* All 8×8 TUs in fast/ultrafast arise from CU=16 at TU depth=1.

---

### Parameter mapping (Revised and Verified)

| **Hardware preset**  | **TU usage & transform type**                                                                                              | **Suggested x265 parameters**                                                                                                                                                                                                                    | **Explanation**                                                                                                                                                                                                                                     |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Slow / Medium**    | High number of **4×4 TUs** (~2.48M); full TU size range used (up to 32×32); **DST used occasionally (117 instances)**      | - `--ctu 32` (to match CU size)<br> - Leave `--tu-intra-depth` and `--tu-inter-depth` at **default (1)**<br> - Keep `--tskip` **enabled (default)**<br> - Set `--max-tu-size 32`                                                                 | Allows the encoder to form 4×4 TUs (via CU=8 at depth=1) and access **DST** transforms when needed. The TU size cap of 32 aligns with hardware’s upper bound. TU depth 1 is sufficient to reach 4×4 from CU=8, no need to increase further.         |
| **Fast / Ultrafast** | Strong reduction or absence of 4×4 TUs; dominant use of **8×8 (from CU16@depth=1)** and **16×16**; **DCT-only** transforms | - `--ctu 32`<br> - Set `--tu-intra-depth 1` and `--tu-inter-depth 1`<br> - **Optional**: `--max-tu-size 16` (to disfavor 32×32)<br> - **Optional**: `--no-tskip` (to enforce DCT-only usage, as NVENC doesn't use transform-skip in these modes) | Setting TU depth to 1 prevents 4×4 TUs, since no CU=8 is used in hardware fast/ultrafast. The encoder then favors 8×8 and 16×16 transforms. Disabling `tskip` removes any residual 4×4 TU + DST combinations. Capping TU size to 16 aligns with HW. |

> 🔍 **Optional refinement:**
> If strict mimicry of fast/ultrafast hardware presets is desired, add `--rdpenalty 2` to **discourage 32×32 intra TUs**, though 32×32 is still allowed in NVENC.

---

### 6 Partition schemes

#### Observations

The block-partitioning slide shows that NVENC uses only 2Nx2N and NxN partitions; all
rectangular (2NxN/Nx2N) and asymmetric (AMP) partition types are unused.
x265 defaults to rectangular and asymmetric partitioning being disabled; however, certain presets
or RD levels may enable them.

#### Parameter mapping

| Parameter | Setting | Justification |
|------------|----------|----------------|
| `--no-rect` | Disable rectangular partitions (Nx2N and 2NxN). | NVENC never uses rectangular partitions, so x265 should avoid them. |
| `--no-amp` | Disable asymmetric partitions (AMP). | The hardware encoder does not use AMP; leaving AMP disabled matches the hardware behaviour. |

---

### 7 Post-processing filters: deblocking and SAO

#### Observations

The deblocking slide shows that NVENC slow/medium presets leave deblocking completely
disabled, while fast/ultrafast presets apply vertical deblocking with varying strengths. x265
enables the deblocking filter by default, with offsets set to 0; it can be disabled with `--no-deblock`.

The SAO slide shows that NVENC always uses the sample-adaptive-offset filter; different SAO
types (band and edge filters) occur frequently. x265 also enables SAO by default, but its
superfast and ultrafast presets disable it to gain speed.

#### Parameter mapping

| Aspect | Suggested x265 configuration | Rationale |
|---------|------------------------------|------------|
| Deblocking filter | For slow/medium hardware presets, disable deblocking completely with `--no-deblock` to match the absence of deblocking statistics. For fast/ultrafast hardware presets, leave deblocking enabled (`--deblock`) and fine-tune tC/Beta offsets if necessary. | NVENC’s deblocking strength varies by preset. Matching it in x265 may require experimentation with `--deblock` offsets; starting with defaults and adjusting based on visual output is recommended. |
| SAO filter | Enable SAO (`--sao`) and use `--selective-sao 4` to ensure SAO is applied to all slices. Avoid the fastest x265 presets that disable SAO internally. | NVENC always uses SAO; enabling it in x265 ensures similar post-processing. |

---

### 8 Screen-content coding (SCC) tools

The presentation’s SCC slide shows that neither the software nor the hardware encoder used intra
block copy (IntraBC) or palette modes (predominant in screen-content coding). x265 exposes SCC
tools only through a build-time option and command-line flags, so simply do not enable SCC to match
the hardware behaviour.

---

### 9 Additional considerations and workflow for tuning x265

1. **Select a base preset:**  
   Choose an x265 preset close to the target hardware speed (e.g., medium or fast). Presets determine RD levels and analysis complexity.  
   Use the `medium` preset for hardware slow/medium and `fast` or `faster` for hardware fast/ultrafast.

2. **Apply parameter overrides:**  
   After selecting the preset, append the overrides discussed above.

   Example (hardware fast preset):
   ```bash
   --ctu 32 --min-cu-size 8 --no-rect --no-amp \
   --tu-intra-depth 1 --tu-inter-depth 1 --max-tu-size 16 \
   --fast-intra --no-tskip --sao --selective-sao 4 --deblock
   ```
   
   Example (hardware slow preset):
   ```bash
   --preset medium --ctu 32 --min-cu-size 8 --no-rect --no-amp \
   --tu-intra-depth 1 --tu-inter-depth 1 --max-tu-size 32 \
   --sao --selective-sao 4 --no-deblock
   ```
   Adjust `--rdpenalty` , `--deblock` offsets and bitrate settings based on the desired bitrate and visual quality.
3. **Validate with VQ analysis:**  
   After encoding test sequences, perform the same VQ statistics analysis used in the presentation. Compare the distribution of PU/TU sizes, intra modes and transform types to the hardware counts. Iterate on the parameters until the distributions closely align.

4. **Energy considerations:** The energy-consumption paper notes that software HEVC encoding can be  very  energy-intensive.  Limiting  CU/TU  sizes,  reducing  the number  of  prediction  modes  and  disabling  complex  partitions  reduce  CPU  load  and  power
consumption.  Hardware  encoders  are  designed  around  such  restrictions,  so  the  proposed parameter sets not only mimic NVENC but also lower the energy footprint of x265.

### 10 Conclusion

NVENC’s H.265 encoder uses a carefully restricted subset of HEVC features: it limits coding-unit sizes to
32×32  and  8×8,  rarely  uses  4×4  blocks  for  fast  modes,  restricts  angular  intra  modes,  disables
rectangular and asymmetric partitions, and always employs SAO while selectively applying deblocking.
By consulting the x265 CLI documentation and applying the parameter mappings summarised above,
you can tune x265 to approximate the hardware encoder’s behaviour. Fine-tuning may still be required
to match exact distributions and visual quality, but the recommendations provide a solid starting point.
