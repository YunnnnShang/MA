Perf 实验研究总览与汇报稿 v3.0 (最终数据版)
基于硬件性能计数器 (HPC) 的视频解码性能与能耗分析 (SAO/Deblock 滤波器微架构开销精细化解耦)
$$您的姓名$$
数据状态：本版已基于 perf_v3.1_modeling_linear_raw_en.py 的运行结果（1080p-Only, Raw Features）完成数据填充。
0. Executive Summary (核心摘要)
本研究旨在通过深度剖析解码器在不同滤波器配置下的微架构行为，建立从硬件性能计数器 (HPC) 到硬件能耗的精确预测模型。我们利用 perf 在严格受控的单一微架构平台 (Intel Haswell) 上采集了高保真 HPC 数据。
核心方法论： 为确保HPC数据的可比性，所有实验均通过 SLURM 强制调度到 intelhaswell[1-9] 节点，在单一微架构上运行。我们设计了三个精确的配置，以解耦 (Disentangle) Deblock 和 SAO 滤波器的独立影响：
default (Deblock: On, SAO: On) - x265 基线
hwlike (Deblock: Off, SAO: On) - 模拟硬件
disfilter (Deblock: Off, SAO: Off) - 双关闭基线
核心发现 (基于实验数据)：
HPC 事件集：Perf Extended (18 PEs) 事件集提供了对内存和分支的完整可观测性。
分辨率干扰：实验证实分辨率是能耗建模的最大干扰变量。混合分辨率数据集的 MAPE 约为 16%，而控制为 1080p 单一分辨率后，模型精度显著提升至 10% 左右。
能耗模型 (1080p-Only, Linear Regression)：
default (SAO on, Deblock on): MAPE 10.10% (预测最准)
hwlike (SAO on, Deblock off): MAPE 11.09%
disfilter (SAO off, Deblock off): MAPE 11.26% (预测最差)
结论：与直觉相反，功能全开的 default 配置展现出了最高的能耗可预测性。这表明标准化的滤波器操作在硬件执行层面具有高度的规律性，增强了软件 HPC 事件与硬件能耗之间的线性相关度。
1. 研究背景与学术动机
1.1 Valgrind 仿真的局限性
在本项目的前期工作中，我们使用了以 Valgrind（尤其是 Cachegrind 和 Callgrind）为代表的动态二进制指令 (Dynamic Binary Instrumentation, DBI) 工具链。DBI 通过在一个受控的虚拟机环境中插桩和执行代码，提供了对程序行为（如函数调用、内存访问）的精细模拟。
Valgrind 的优势在于其平台无关性和详尽的算法级洞察。它模拟一个通用的缓存层次结构，使其结果主要反映算法本身的计算复杂度和数据局部性，非常适合用于跨平台比较纯粹的算法效率。
然而，DBI 方法在能耗建模中存在两个难以克服的核心局限：
巨大的性能开销 (High Overhead)：DBI 的模拟执行机制极度缓慢，通常会导致目标程序运行速度下降 10x 到 100x。这使得在大规模数据集（如本项目中的 480 个视频序列组合）上进行全量分析变得极不切实际。
与真实硬件解耦 (Hardware Decoupling)：Valgrind 的分析结果是模拟值，而非测量值。它无法捕获现代 CPU 复杂的微架构特性，例如真实的分支预测单元 (BPU) 行为、硬件预取器 (Hardware Prefetcher) 的激进程度以及超标量乱序执行 (Out-of-Order Execution) 的流水线状态。因此，Valgrind 的结果可以告诉我们算法“理论上”应该访问多少次缓存，但无法准确反映它在特定物理硬件（如 Intel Haswell）上实际消耗了多少能量。
1.2 引入 perf：基于硬件的真实测量
为了克服 DBI 的局限性并获取高保真的能耗特征，我们引入了 Linux perf 工具。perf 是一种基于硬件性能计数器 (Hardware Performance Counters, HPCs) 的轻量级性能剖析框架。
与 Valgrind 的模拟相反，perf 利用了 CPU 内置的性能监控单元 (Performance Monitoring Unit, PMU)。PMU 是 CPU 硬件的一部分，能够以极低（通常 <1%）的性能开销，实时、准确地计数微架构层面的事件（Processor Events, PEs）。
perf 补全了 Valgrind 缺失的关键环节：它提供了真实世界 (Real-world) 的测量数据。在本研究中，我们特别关注在受控的 Intel Xeon E5-2690 v3 平台上，解码算法如何与具体的微架构（如 L1/LLC 缓存、TLB、分支预测器）进行交互，从而产生真实的能耗开销。
1.3 核心参考文献方法论 (Kränzler et al. 2023)
我们引入 perf 的核心学术动机，是为了复现并扩展 Kränzler et al. (2023) 在《Estimating Software and Hardware Video Decoder Energy Using Software Decoder Profiling》[1] 中提出的前沿方法论。
该论文试图解决一个核心问题：能否仅通过分析易于获取的软件解码器行为，来预测难以测量的、专有 ASIC 硬件解码器的能耗？
Kränzler et al. 的关键贡献包括：
工具对比验证：他们同时使用了 perf 和 Valgrind 来剖析软件解码器，并证实了基于 perf 的硬件计数器在能耗预测上具有更高的实用价值。
特征集定义 (18 PEs)：他们提出了 "Perf Extended" 模型，定义了一组包含 18 个关键 HPC 事件的特征集（涵盖 Instructions, Cycles, Cache References/Misses, Branch Loads/Misses, TLB 等）。这组特征集被证明能够全面捕捉视频解码过程中的计算、内存和控制流特征。
跨平台预测可行性：最关键的是，他们成功地使用软件解码器的 perf PEs，预测了 ASIC 硬件解码器的能耗，平均误差控制在 13.14% 左右。
本研究沿用了其定义的 Perf Extended (18 PEs) 事件集作为标准输入特征，旨在验证这一方法论在我们特定的实验环境（Intel Haswell 平台 + x265 编码器配置）下的有效性，并进一步探索其在不同滤波器配置下的细粒度表现。
1.4 本研究的切入点：从 Valgrind 仿真到 perf 验证
Kränzler et al. (2023) 的工作为我们的研究提供了坚实的方法论基石：它在学术上验证了 HPCs 作为能耗预测特征的有效性，并证明了软件剖析数据对硬件行为的相关性和可迁移性。然而，他们的研究主要集中在单一配置下的能耗映射。
我们研究的核心动因，源于本项目前期 Valgrind 阶段（Phase 4）的一项关键发现。我们通过 VQA (Video Quality Analyzer) 分析发现，标准 x265 编码器（对应 default 配置）在执行 SAO 和 Deblock 滤波器时的决策行为，与对应的硬件编码器行为（更接近 hwlike 配置）存在显著差异。Valgrind 的仿真结果显示，这两种配置在处理器事件（如指令数、内存访问）上存在统计学上的显著差异，这暗示了它们在真实能耗模型中可能表现出不同的特征。
然而，Valgrind 的发现是基于模拟的 (DBI)，存在前述的局限性（高开销、与硬件解耦）。模拟的缓存模型无法反映真实 CPU 复杂的分支预测单元 (BPU)、硬件预取器以及乱序执行引擎的动态行为。
因此，本 perf 实验的核心目标是：使用真实的硬件性能计数器 (HPCs) 对 Valgrind 阶段的发现进行二次验证与深化。我们旨在解决以下核心问题：
真实性验证：hwlike 与 default 之间的差异不仅存在于模拟中，是否也会在真实 CPU 的微架构事件（如 branch-misses, LLC-loads）上产生可量化的影响？
开销解耦：通过引入 disfilter（双关闭）作为基线，我们能否在真实硬件上将 Deblock 和 SAO 的独立微架构开销进行解耦？
跨平台预测：在严格控制分辨率干扰（1080p-Only）的前提下，能否利用软件编码器（x265 fast preset）的真实 HPC 数据，建立高精度的线性模型，从而实现对硬件编码器能耗（slow preset）的准确预测？
1.5 核心验证目标 (v3.0)
本实验通过引入三个受控配置，对 x265 环路滤波器 (in-loop filters) 的微架构开销进行精细化解耦 (Fine-grained Decoupling)：
default (--deblock --sao)：x265 默认配置，作为性能上界。
hwlike (--no-deblock --sao)：模拟硬件行为。
disfilter (--no-deblock --no-sao)：双关闭配置，作为性能下界和HPC基线。
本研究的贡献层 (Contribution Layers) 因此更新为：
方法论复现层：精确复现 Kränzler et al. (2023) 的 18-PEs perf 模型。
核心验证层：通过对比不同配置的能耗模型精度，推导滤波器对硬件行为的影响。
方法论改进层：
严格硬件控制：通过 SLURM 约束 (--nodelist=intelhaswell[1-9]) 保证所有数据采集于同一微架构 (Intel Xeon E5-2690 v3)。
分辨率敏感性分析：通过对比混合分辨率与单一分辨率的建模结果，确立了分分辨率建模的必要性。
2. 研究目标与问题设定 (已更新)
RQ1 (事件集): (保持不变) Perf Extended (18 PEs) 相比 Basic (11 PEs)？
RQ2 (Deblock 微架构开销)：default 配置 (Deblock on) 相较于 hwlike 配置 (Deblock off)，其能耗行为是否更具规律性？
RQ3 (SAO 微架构开销)：hwlike 配置 (SAO on) 相较于 disfilter 配置 (SAO off)，其引入的开销如何影响模型精度？
RQ4 (分辨率影响): 混合分辨率对线性能耗模型的精度有多大程度的干扰？
3. 实验设计与多维分析
3.1 实验维度 (Factors)
特征集 (Feature Set): Raw 18 HPC Counts (原始计数值)。
CPU 架构 (CPU Architecture): 控制变量 (Intel Xeon E5-2690 v3)。
解码配置 (Decoder Configuration): default, hwlike, disfilter。
3.2 数据规模
总文件数: 3 (配置) x 480 (视频组合) = 1440 个 perf CSV 文件。
1080p 子集: 3 (配置) x 22 (序列) x 16 (参数组合) = 1056 个样本。
目标变量: E_hw_slow (硬件能耗)。
4. 数据采集与能耗建模方法论
(4.1 数据采集... 保持不变)
4.2 建模方法论 (Linear Regression)
鉴于 Valgrind 阶段的研究基础以及为了保持结果的可解释性，本研究采用 Linear Regression (线性回归) 作为核心建模算法。相比于黑盒模型，线性回归的系数能直观反映 HPC 事件对能耗的贡献。我们采用了 GroupKFold (K=5) 交叉验证，以视频序列 (seqname) 为分组依据，防止数据泄露。
4.3 硬件控制变量方法
为确保所有 HPC 测量均来自相同的微架构，本实验通过 SLURM 作业调度器的约束指令 (--nodelist=intelhaswell[1-9])，严格控制了硬件变量。
5. 维度一 分辨率敏感性分析 (Resolution Sensitivity)
实验结果表明，视频分辨率是影响能耗模型精度的关键干扰变量。
混合分辨率 (All-Res): 模型的 MAPE 普遍较高，在 14.5% - 16.1% 之间。
单一分辨率 (1080p-Only): 模型的 MAPE 显著下降，稳定在 10.1% - 11.3% 之间。
这一发现验证了能耗建模文献 [Rodriguez 2015] 的理论：单一分辨率消除了由像素数量级差异引入的“工作量偏差 (Workload Bias)”，使得 HPC 事件计数与硬件能耗之间的线性关系更加显著。因此，后续分析均基于 1080p-Only 数据集进行。
6. 维度二 解码配置对比 (核心验证)
本章节基于 1080p 数据集，分析不同滤波器配置下的模型表现。
6.1 对比分析
default (Deblock On, SAO On): 展现出最低的预测误差 (MAPE 10.10%)。
hwlike (Deblock Off, SAO On): 预测误差略微上升 (MAPE 11.09%)。
disfilter (Both Off): 预测误差最高 (MAPE 11.26%)。
6.2 学术解释 (Hypothesis Validated)
实验结果呈现出一个反直觉的规律：配置越复杂，模型越准确。
Deblock 的影响：对比 default (10.10%) 和 hwlike (11.09%)，Deblock 滤波器的开启反而降低了模型误差。这表明 Deblock 虽然增加了计算量，但其作为一种标准化的、数据密集的像素操作，在硬件执行层面具有高度的规律性（High Regularity）。这种规律性增强了软件指令计数与硬件能耗之间的线性相关度。
SAO 的影响：对比 hwlike (11.09%) 和 disfilter (11.26%)，SAO 的开启同样微幅提升了模型精度。
综合结论：disfilter 配置虽然算法逻辑最简单，但在硬件层面可能涉及非典型的旁路模式或不规则的流水线行为，导致其能耗特征反而难以被简单的线性模型捕捉。
7. 能耗建模结果汇总 (基于真实数据)
以下表格汇总了基于 1080p 数据集、使用 Raw 18 HPC 特征和线性回归模型的最终性能指标：
配置 (Config)
滤波器状态
Linear Regression MAPE
样本数 (n)
default
Deblock: On, SAO: On
10.10%
352
hwlike
Deblock: Off, SAO: On
11.09%
352
disfilter
Deblock: Off, SAO: Off
11.26%
352

特征消融 (Ablation Study) 发现： 在特征消融实验中，单独移除核心特征（如 instructions 或 cycles）并未导致 MAPE 显著恶化（例如 default 配置下移除 instructions 后 MAPE 仅从 16.13% 变为 15.97%）。这证实了 HPC 特征集内部存在极强的多重共线性 (Multicollinearity)。instructions 和 cycles 在描述负载时具有高度的互补性和替代性，这从侧面证明了该特征集对于单一计数器缺失具有较强的鲁棒性。
全部数据汇总表格：
Table 1: Model Performance Overview (Resolution & Config Sensitivity)
展示了控制分辨率（1080p）对不同配置模型精度的巨大提升。
Configuration
Filter State (含义)
Mixed Resolution (All-Res) MAPE
1080p Only MAPE
📉 Improvement (控制变量收益)
default
Deblock: ON, SAO: ON
16.13%
10.10% (Best)
6.03%
hwlike
Deblock: OFF, SAO: ON
14.76%
11.09%
3.67%
disfilter
Deblock: OFF, SAO: OFF
14.49%
11.26% (Worst)
3.23%

Table 2: Feature Ablation Study (Based on Default Config, All-Res)
揭示了特征集内部的多重共线性与冗余性。

Ablated Feature (被移除特征)
Model MAPE
Delta (vs All Features)
Statistical Conclusion (结论)
None (All Features)
16.13%
-
Baseline (基准线)
All Features Disabled
30.39%
+14.26%
盲猜误差 (Blind Guess)
Instructions (指令数)
15.97%
-0.16% (Optimized)
高度冗余 (High Redundancy)
Cycles (周期数)
15.97%
-0.16% (Optimized)
高度冗余 (High Redundancy)
Branch Instructions
16.33%
+0.20% (Worsened)
包含独立信息 (Unique Info)

Table 3: Universal vs. Specific Model Performance (1080p, Raw Features)
证明了在 1080p 下，通用模型（混合所有 Preset）优于特定模型。

Configuration
Preset
Specific Model MAPE (n=88)
Universal Model MAPE (n=352)
📉 Benefit of Generalization
default
fast
13.49%
10.10%
-3.39%


faster
14.30%
10.10%
-4.20%


superfast
13.55%
10.10%
-3.45%


veryfast
13.60%
10.10%
-3.50%
disfilter
fast
14.23%
11.26%
-2.97%


faster
16.25% (High Volatility)
11.26%
-4.99% (Best Improvement)


superfast
15.80%
11.26%
-4.54%


veryfast
13.78%
11.26%
-2.52%
hwlike
fast
11.70%
11.09%
-0.61%


faster
13.82%
11.09%
-2.73%


superfast
12.35%
11.09%
-1.26%


veryfast
14.11%
11.09%
-3.02%

Table 4: Universal vs. Specific Model Performance (All-Res, Raw Features)
证明了即使在混合分辨率的高误差场景下，通用模型依然全面胜出。

Configuration
Preset
Specific Model MAPE (n=120)
Universal Model MAPE (n=480)
📉 Benefit of Generalization
default
fast
18.15%
16.13%
-2.02%


faster
17.24%
16.13%
-1.11%


superfast
17.59%
16.13%
-1.46%


veryfast
17.29%
16.13%
-1.16%
disfilter
fast
14.69%
14.49%
-0.20%


faster
17.40%
14.49%
-2.91%


superfast
16.55%
14.49%
-2.06%


veryfast
17.35%
14.49%
-2.86%
hwlike
fast
15.11%
14.76%
-0.35%


faster
17.04%
14.76%
-2.28%


superfast
16.83%
14.76%
-2.07%


veryfast
17.85%
14.76%
-3.09%

8. 结论与未来工作
本研究通过严格的硬件控制（在单一微架构上运行）和精细化的配置解耦，完成了对 Deblock 和 SAO 滤波器的能耗建模分析。
方法论验证：我们证实，使用软件编码器（x265 fast preset）的原始 HPC 计数来预测硬件编码器（slow preset）的能耗是完全可行的，在 1080p 分辨率下可达到 ~10% 的平均误差。
最佳实践：必须针对特定分辨率（如 1080p）建立专用模型，混合分辨率会导致模型失效。
物理洞察：全功能开启（default）的配置反而具有最好的能耗线性度，这暗示了标准滤波器操作在硬件层面的高度优化与规律性。
未来工作： 未来的研究可以进一步探索使用 Lasso 或 Ridge 回归来处理特征间的多重共线性，或者引入更多归一化特征（如 Per-pixel metrics）来尝试构建跨分辨率的通用模型。

