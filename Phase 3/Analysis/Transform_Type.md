
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
