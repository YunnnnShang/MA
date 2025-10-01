### Transform Usage Statistics of HEVC Intra Coding

Table X reports the transform usage statistics derived from the VQ Analyzer exports for the software encoder (x265) and the NVIDIA hardware encoder (NVENC). The rows correspond to transform tools, and the columns correspond to different presets. For each configuration, the total number of Transform Units (TUs) utilizing a given tool is aggregated over all test sequences.

**Table X.** Transform usage by preset (x265 vs. NVENC, intra coding, 30-frame segments).
(a) x265 software encoder

| Transform / Preset | fast       | faster     | medium     | superfast  | ultrafast  | veryfast   |
| ------------------ | ---------- | ---------- | ---------- | ---------- | ---------- | ---------- |
| **DCT**            | 42,905,036 | 42,904,964 | 43,069,219 | 42,596,926 | 27,389,148 | 42,905,019 |
| **DST (Y4×4)**     | 53,412,363 | 53,412,345 | 54,897,222 | 50,695,758 | 0          | 53,412,418 |
| **PCM**            | 0          | 0          | 0          | 0          | 0          | 0          |
| **Transform Skip** | 0          | 0          | 0          | 0          | 0          | 0          |

(b) NVIDIA hardware encoder

| Transform / Preset | fast       | medium     | slow       | ultrafast  |
| ------------------ | ---------- | ---------- | ---------- | ---------- |
| **DCT**            | 48,274,920 | 33,392,742 | 33,392,747 | 54,260,693 |
| **DST (Y4×4)**     | 0          | 57,132,988 | 57,132,966 | 0          |
| **PCM**            | 0          | 0          | 0          | 0          |
| **Transform Skip** | 0          | 7,358,927  | 7,358,921  | 0          |

---

### Result Analysis

Several clear patterns emerge from these statistics:

1. **x265 Software Encoder.**
   Across all presets except *ultrafast*, a very large number of intra luma 4×4 TUs are processed using the DST-VII transform, in line with the HEVC standard restriction that DST applies exclusively to 4×4 intra luma TUs. The *ultrafast* preset shows **no usage of 4×4 luma TUs** (and hence no DST), reflecting its configuration choice to disable small TUs for maximum speed. Transform Skip is absent across all presets, consistent with x265’s default behavior where `--tskip` is disabled for lossy coding.

2. **NVENC Hardware Encoder.**
   For *fast* and *ultrafast* presets, no luma 4×4 TUs are observed, thus DST is not applied. In contrast, *medium* and *slow* presets exhibit very frequent usage of 4×4 luma TUs, with **DST counts around 57 million** and additional **transform skip flags (≈7.36 million)**. This shows that NVENC, when operated in slower presets, allocates significant resources to finer partitioning and to selectively bypassing transforms, potentially to preserve sharp edges and textural details.

3. **Consistency Checks.**
   The aggregate luma TU counts are on the order of 10^7–10^8, which is consistent with expectations. A discrepancy of approximately 1.5 million was observed in NVENC medium/slow configurations when comparing *LumaTU_total* with the sum of DCT+DST+TS+PCM. This difference corresponds closely to the transform skip counts in the chroma channels (Cb/Cr), which were not included in the luma budget. Thus, the statistics are internally consistent and the discrepancy is attributable to chroma-side skips rather than measurement error.

---

### Research Implications

These results highlight **systematic differences** between the software and hardware encoder implementations:

* **TU and transform selection policy.**
  Both encoders aggressively exploit DST for intra 4×4 luma blocks in non-ultrafast presets, but x265 consistently uses it whenever small TUs are enabled, while NVENC selectively disables 4×4/DST in faster presets.

* **Speed–quality trade-offs.**
  The absence of DST and transform skip in ultrafast/fast modes of both encoders indicates a deliberate design to minimize computational complexity at the expense of coding efficiency. Conversely, slower modes re-enable these tools, suggesting a configurable balance between throughput and efficiency.

* **Energy modeling relevance.**
  Since DST and Transform Skip affect not only compression efficiency but also hardware datapath utilization (e.g., bypassing transform blocks or invoking specialized DST logic), their usage frequencies provide a direct explanation for some of the observed **energy consumption differences** between x265 and NVENC across presets. Specifically, NVENC’s reliance on transform skip in medium/slow modes could partially explain its distinct power–quality trade-off profile.

2. x265 编码器行为分析

核心发现: x265 的预设在变换类型的选择上体现了平滑的、渐进式的复杂度权衡。

关键洞察:

DST 的作用: 从 superfast 到 medium，编码器都大量使用了 DST (DST (Y4x4))，其使用次数甚至超过了 DCT。这表明在这些预设下，x265 的 RDO 引擎认为，花费额外的计算去检查 DST 是否更优是值得的。

ultrafast 的极致简化: ultrafast 预设完全禁用了 DST (DST (Y4x4) 为 0)。这是一个典型的为了追求极致速度而做出的算法牺牲。RDO 过程被大大简化，编码器不再为 4x4 块进行 DCT vs DST 的决策，直接全部使用 DCT。

Transform Skip 的缺失: 在所有预设下，TransformSkip 的使用次数都为 0。这对于你使用的自然视频测试序列是正常的。Transform Skip 主要在屏幕内容或残差极小的区域有优势，在复杂纹理的自然视频中，RDO 计算后通常认为它不是最优选择。

3. NVIDIA 硬件编码器 (NVENC) 行为分析

核心发现: 与 x265 不同，NVIDIA 硬件编码器的预设在变换工具的选择上呈现出**“开关式”的、非连续的**行为模式。

关键洞察:

预设的“阶梯式”功能开启:

ultrafast 和 fast 预设: 完全不使用 DST 和 Transform Skip。它们的变换模块工作在一个非常基础的“纯 DCT”模式下，这极大地简化了硬件处理流程，从而实现高速编码。

medium 和 slow 预设: 同时开启了 DCT, DST, 和 Transform Skip。这表明从 medium 预设开始，硬件 RDO 引擎进入了一个更复杂的模式，会综合评估这三种变换工具的优劣。

medium vs slow 的相似性: 在变换类型的选择上，medium 和 slow 预设的统计数据几乎完全相同。这强烈暗示，这两个预设之间的性能和能耗差异并非源于变换阶段，而是源于其他编码环节，例如：

Intra 预测模式的搜索范围 (slow 可能搜索更多角度模式)。

CU 划分的搜索深度 (slow 可能进行更穷举的 RDO 决策)。
### Transform Skip 在 HEVC 里到底是什么？

* 正常情况下，HEVC 的残差会做 **整数 DCT-II**（大多数块尺寸）或 **DST-VII**（仅限 **帧内 luma 的 4×4**）。
* **Transform Skip** 的含义是：**对某个 TU 直接跳过变换阶段**（可理解为恒等变换/IDTX），随后仍进行量化与熵编（除非另外启用了“变换-量化旁路”，也叫 transquant-bypass，用于真正的无损）。这一点在标准与参考资料中都有明确描述。([ITU][1])

> 标准层面有明确的 **`transform_skip_flag`** 语法元素；很多资料也会把它作为屏幕内容等“锐利边缘”场景的利器（跳过变换能避免把锐利边缘“扩散”到许多系数）。([维基百科][3])
明白 ✅

你想要的效果是：

* 用我们刚才写的 **推导流程**重新算出来的 `Transform_Type`（区分 DCT / DST / TS / PCM），**直接写回到原始的 VQ Analyzer 导出 CSV 里**。
* 即：保留所有原始列，只是把现有的 `Transform_Type` 列（现在全是 `DCT`）**替换成推导后的结果**。

---

### 核心思路

1. **逐 TU 行推导**（因为你原始 CSV 是帧/块级别，每行有 TU 尺寸 / skip 标志 / PCM 标志）。

   * 如果 `Intra PU type: PCM` → `Transform_Type="PCM"`
   * elif `Y transform skip: Skipped` 或 `Cb/Cr transform skip: Skipped` → `Transform_Type="TransformSkip"`
   * elif `TU sizes (luma only): 4x4`（且为 Y，非 skip/PCM） → `Transform_Type="DST"`
   * else → `Transform_Type="DCT"`
2. 将得到的新列直接覆盖掉旧的 `Transform_Type`。
3. 保存为新的 `*_with_transformtype.csv`，避免覆盖原始文件。

---

### 示例代码

```python
import pandas as pd
import re
from pathlib import Path

def update_transform_type(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 确认列名
    col_pcm   = [c for c in df.columns if re.match(r"^Intra\s*PU\s*type:\s*PCM$", c, flags=re.I)]
    col_ts_y  = [c for c in df.columns if re.match(r"^Y\s*transform\s*skip:\s*Skipped$", c, flags=re.I)]
    col_ts_cb = [c for c in df.columns if re.match(r"^Cb\s*transform\s*skip:\s*Skipped$", c, flags=re.I)]
    col_ts_cr = [c for c in df.columns if re.match(r"^Cr\s*transform\s*skip:\s*Skipped$", c, flags=re.I)]
    col_y_4x4 = [c for c in df.columns if re.match(r"^TU\s*sizes\s*\(luma only\):\s*4x4$", c, flags=re.I)]

    # 如果没有 Transform_Type 列，先建一个空的
    if "Transform_Type" not in df.columns:
        df["Transform_Type"] = "DCT"

    def classify_row(row):
        # PCM 优先
        if col_pcm and row[col_pcm[0]] > 0:
            return "PCM"
        # Transform Skip
        if (col_ts_y and row[col_ts_y[0]] > 0) or \
           (col_ts_cb and row[col_ts_cb[0]] > 0) or \
           (col_ts_cr and row[col_ts_cr[0]] > 0):
            return "TransformSkip"
        # DST (Luma 4x4, 非skip/PCM)
        if col_y_4x4 and row[col_y_4x4[0]] > 0:
            return "DST"
        # 其余都归为 DCT
        return "DCT"

    df["Transform_Type"] = df.apply(classify_row, axis=1)
    return df


# 用法示例
sw = pd.read_csv("software_stats_full.csv")
hw = pd.read_csv("hardware_stats_full.csv")

sw_new = update_transform_type(sw)
hw_new = update_transform_type(hw)

# 保存为新文件
sw_new.to_csv("software_stats_full_with_transformtype.csv", index=False)
hw_new.to_csv("hardware_stats_full_with_transformtype.csv", index=False)
```

---

### 注意事项

* 这里的逻辑是逐行判断 → 结果是 **逐块/逐帧的 Transform_Type 标签**，而不是聚合表。
* 如果你的 CSV 是**统计汇总**（每列已经是计数），那就不能逐行分类，只能像之前一样做“聚合推导”。你上传的表格看起来是**逐帧统计**，所以逐行更新没问题。
* 如果未来你导出更细分的列（例如 CBF=1 的 TU 直方图），可以进一步细化逻辑，比如 “非零系数的 Y 4x4 TU → DST”。


### 容易混淆的两个“Skip”

请一定区分：

1. **Transform Skip（变换跳过）**：针对 **变换阶段** 的工具，标志位是 `transform_skip_flag`。([ITU][1])
2. **Inter 的 Skip 模式**：运动补偿那边的 **merge/skip**（无残差），完全是另一回事。([IP Home][4])

---

### 在不同配置/扩展里的适用性

* 在 **HEVC 标准**中，变换跳过最早就作为工具存在（面向 4×4 小块最典型）。后续 **RExt / SCC** 扩展里还对 **变换跳过**做过增强（例如更大的块、与 RDPCM 的配合等），但这不改变“HEVC 支持 transform skip”的事实，只是**扩展了其适用范围/形态**。([维基百科][3])

---

### 为什么我的 x265 数据里 “TS_* = 0”，而 NVENC 某些档位有非零？

* **x265 默认并不会启用 transform skip**（需要 `--tskip`，且只在较高 RDO 等级才评估），所以你看到 **SW 端 `TS_*` 为 0** 是非常正常的。([x265.readthedocs.io][2])
* **NVENC** 在某些预设/固件策略下可能**会启用**，尤其是面对带有强边缘/文本的内容或者特定速度/质量平衡点，因此你在 **HW 的 medium/slow** 档位里看到了 **`Y transform skip: Skipped`** 数量级不为零，这也是合理现象。

  * **“变换类型”** 只用于 **DCT-II / DST-VII**（谁被真正应用）。
  * **“是否跳过变换”** 应该是**独立的开关/标签**（`transform_skip_flag`），它表示“没有做任何变换”。
* 换句话说：**Transform Skip ≠ 一种新的变换**；它是**不变换**。
  如果我们为了出一张合并表把“Transform Skip”也放在行上，那应当在图例/注释里明确：这行代表“未进行 DCT/DST 的块”，而不是“第三种变换”。

---

[1]: https://www.itu.int/rec/dologin_pub.asp?id=T-REC-H.265.1-201410-S%21%21PDF-E&lang=e&type=items&utm_source=chatgpt.com "H.265.1"
[2]: https://x265.readthedocs.io/en/stable/cli.html?utm_source=chatgpt.com "Command Line Options - x265 Documentation - Read the Docs"
[3]: https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding?utm_source=chatgpt.com "High Efficiency Video Coding"
[4]: https://iphome.hhi.de/wiegand/assets/pdfs/2012_12_IEEE-HEVC-Overview.pdf?utm_source=chatgpt.com "Overview of the High Efficiency Video Coding (HEVC) ..."
