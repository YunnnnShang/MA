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

Hardware presets use only 32×32, 16×16, 8×8 and occasionally 4×4 PUs; larger PUs (e.g.,
64×32, 64×48) are never used. For the slow and medium hardware presets the number of 4×4
PUs is very high (~2.15 million), while for fast/ultrafast the hardware encoder does not use 4×4
PUs at all . In contrast, x265’s medium preset also uses many 4×4 PUs, but its superfast and
ultrafast presets disable them entirely.
The smallest CU size determines the smallest PU/TU size possible. Because hardware fast/ultrafast
never go below 8×8, the minimum CU size should be at least 8 for those modes; hardware slow/
medium make heavy use of 4×4 blocks and therefore require a minimum CU size of 8 or smaller.

#### Parameter mapping and recommendations

| Hardware preset | Observed PU/CU usage | Suggested x265 parameters | Rationale |
|-----------------|----------------------|---------------------------|------------|
| Slow or medium | Heavy use of 4×4 PUs alongside 8×8–32×32 PUs. | Keep default `--min-cu-size 8` to allow 8×8 CUs and 4×4 PUs, and set `--ctu 32` to limit the maximum CU size to 32×32. Do not disable 4×4 transforms. | The hardware encoder accepts 4×4 PU/TU blocks for slow and medium presets; limiting the maximum CU size to 32 reduces the search space and matches the hardware’s largest PU of 32×32. |
| Fast or ultrafast | PUs are limited to 8×8–32×32; no 4×4 PUs. | Use `--min-cu-size 8` to prevent 4×4 CUs, combine with `--ctu 32` to match the 32×32 maximum CU, and set `--tu-intra-depth 1` and `--tu-inter-depth 1` so the TU depth never splits into 4×4. | This configuration removes 4×4 CUs/TUs and restricts the maximum CU size to 32, mirroring the hardware fast/ultrafast presets. |

---

### 3 Intra luma prediction modes

#### Observations

The HEVC standard supports 35 luma intra-prediction modes. x265 evaluates all 33 angular modes
by default (plus planar/DC) unless `--fast-intra` is used.
The slide shows that the hardware encoder only uses a limited subset of luma modes: the counts
for many modes are zero across all hardware presets. For example, modes 6, 7 and modes
above 12 are unused or rarely used; the hardware fast/ultrafast presets concentrate on a small set
of modes such as DC, planar and a few angular modes.

#### Parameter mapping

| Aspect | Suggested x265 parameters | Explanation |
|---------|---------------------------|-------------|
| Limit intra luma modes | Enable `--fast-intra`. This initial scan checks every fifth angular mode and then refines around the best candidate, reducing the number of modes to ~10. | The hardware encoder uses only a handful of intra modes; `--fast-intra` achieves a similar reduction in angular mode search. |
| Consider disabling rare modes completely | Optionally combine `--fast-intra` with `--no-tskip` to disable transform skip evaluation for 4×4 TUs, which the hardware does not use. | Transform-skip is useful mainly for screen-content coding and is not supported by NVENC; disabling it further aligns x265’s behaviour. |

---

### 4 Intra chroma modes

#### Observations

HEVC chroma prediction offers six modes: DC, planar, horizontal, vertical, diagonal and LM (Linear
Model). The slide shows that NVENC uses mostly DM (derived mode) and planar/horizontal/
vertical modes; LM is never used and diagonal modes are rarely chosen.

#### Parameter suggestions

x265 does not expose direct switches for individual chroma modes. However, restricting chroma mode
search implicitly follows from limiting the luma modes and CU sizes. Using `--fast-intra` (Section 3)
reduces the number of angular luma candidates and therefore the number of chroma mode evaluations.
Disabling 4×4 CUs also removes LM (which is only available on 4×4 blocks). Therefore, the CU-size
restrictions recommended earlier already steer x265 towards the hardware’s chroma-mode usage.

---

### 5 Transform-unit sizes and transform types

#### Observations

The hardware slow and medium presets use 4×4, 8×8, 16×16 and 32×32 TUs, with ~2.48 million
4×4 TUs. The fast and ultrafast presets, however, show a substantial reduction in 4×4 TUs
(567k and 741k, respectively) and increased use of 8×8 and 16×16 TUs.
The transform-type slide shows that NVENC uses DCT exclusively for fast/ultrafast presets (DST
counts are zero) and only a few DST transforms for slow/medium presets. HEVC uses DST only
for 4×4 luma TUs.

#### Parameter mapping

| Hardware preset | TU usage & transform type | Suggested x265 parameters | Explanation |
|------------------|---------------------------|---------------------------|-------------|
| Slow/medium | TUs include a large number of 4×4 blocks; a handful of DST transforms are used. | Leave `--tu-intra-depth` and `--tu-inter-depth` at 1 (default) so the residual quad-tree can split into 4×4 TUs. Allow transform-skip for 4×4 TUs (`--tskip` remains disabled by default). Set `--max-tu-size 32` to match the hardware’s largest TU size. | This configuration permits 4×4 TUs and thus allows x265 to use DST (when beneficial) similarly to hardware slow/medium. |
| Fast/ultrafast | 4×4 TUs are largely absent; DCT is used exclusively. | Use `--tu-intra-depth 1` and `--tu-inter-depth 1` to prevent splits beyond the CU depth, thereby avoiding 4×4 TUs. Set `--max-tu-size 16` if the hardware rarely uses 32×32 TUs. Disable transform skip (`--no-tskip`). | Preventing deeper TU splits eliminates 4×4 TUs and, by extension, DST transforms. Limiting the maximum TU size to 16 favours 8×8 and 16×16 TUs, matching the hardware fast/ultrafast profiles. Disabling transform skip ensures that DCT is always used for the remaining TU sizes. |

In addition, the `--rdpenalty` option can be used to discourage 32×32 TUs by applying a cost penalty or
forcing a split. Setting `--rdpenalty 2` forces x265 not to use 32×32 intra TUs, which is beneficial
when emulating NVENC fast/ultrafast.

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
