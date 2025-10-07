# 🧭 实验路线图（最终版）

## 1. 实验目标（Objective）

本实验旨在：

> 通过 Valgrind 工具分析 HEVC 软件编码器（x265）在不同滤波配置下（deblock/SAO）及不同编码预设下（fast–superfast）的处理器事件行为，并结合硬件实测能耗数据，建立基于处理器事件的能耗预测模型，比较两种滤波配置下的能耗与特征差异。

本实验主要回答两个问题：

1. 滤波配置（Deblock/SAO）是否显著影响处理器级行为和能耗？
2. 是否可以用处理器事件（PEs）准确预测不同配置下的能耗？

---

## 2. 实验设计（Design Overview）

### 2.1 实验变量（Independent Variables）

| 类别 | 项目 | 值 / 范围 | 说明 |
|------|------|-----------|------|
| 编码预设 | Preset | fast, faster, veryfast, superfast | 控制编码复杂度与速度 |
| 滤波配置 | Config | 两种模式 | 见下 |
| 量化参数 | QP | 22, 27, 32, 37 | 控制压缩强度 |
| 分辨率 | Resolution | 2K, 4K | 保持一致场景对比 |
| 帧数 | Frames | 130 | 固定帧数以便公平比较 |

### 2.2 两种滤波配置（Configuration Modes）

| 配置编号 | 参数设置 | 说明 |
|-----------|----------|------|
| **Config A** | `--no-deblock --sao` | 禁用 Deblocking 滤波，启用 SAO |
| **Config B** | `--deblock --no-sao` | 启用 Deblocking 滤波，禁用 SAO |

> 两组配置将在相同的视频、预设、QP 下分别运行各一次，以分析滤波器开关对 CPU 事件及能耗分布的影响。

---

## 3. 实验环境（Experimental Environment）

| 项目 | 内容 |
|------|------|
| 计算平台 | FAU LNT Intel CPU Cluster |
| 操作系统 | Linux（Slurm 作业调度系统） |
| 主要工具 | x265, Valgrind 3.24.0, CMake, NASM |
| 能耗数据 | 已有硬件能耗测量（slow preset 下）作为回归目标 |
| 并行设置 | `--cpus-per-task=8`, `OMP_NUM_THREADS=8` 固定 |

---

## 4. 实验流程（Procedure）

### 阶段 1：环境准备

1. 安装 NASM（x265 优化）
2. 编译 Valgrind（3.24.0）
3. 构建 x265 编码器（开启 OpenMP，多线程）
4. 验证单点运行（确保输出 callgrind 文件）

---

### 阶段 2：编码 Profiling 采集（两轮）

每轮实验遍历以下参数：

- `preset ∈ {fast, faster, veryfast, superfast}`
- `QP ∈ {22, 27, 32, 37}`
- `Resolution ∈ {2K, 4K}`
- `Frames = 130`

每个组合生成一个独立的 Valgrind 输出文件。

#### 轮次 1：Config A（no-deblock + sao）

```bash
valgrind --tool=callgrind \
  --callgrind-out-file=callgrind_A_${preset}_${qp}_${seq}.out \
  ./x265 --input ${seq_path} \
         --input-res ${W}x${H} --frames 130 \
         --preset ${preset} --qp ${qp} \
         --keyint 1 --no-deblock --sao \
         --output NUL
```
#### 轮次 2：Config B（deblock + no-sao）

```bash
valgrind --tool=callgrind \
  --callgrind-out-file=callgrind_B_${preset}_${qp}_${seq}.out \
  ./x265 --input ${seq_path} \
         --input-res ${W}x${H} --frames 130 \
         --preset ${preset} --qp ${qp} \
         --keyint 1 --deblock --no-sao \
         --output NUL
```
### 阶段 3：数据提取与整理

使用 callgrind_annotate 或脚本自动解析输出：

```bash
callgrind_annotate callgrind_A_fast_qp27_4k.out > A_fast_qp27_4k.txt

```

提取以下 13 个关键处理器事件（PEs）：
| 缩写               | 含义         | 对应硬件行为   |
| ---------------- | ---------- | -------- |
| Ir               | 已执行指令数     | CPU 工作量  |
| Dr, Dw           | 数据读/写次数    | 内存带宽     |
| I1mr, D1mr, D1mw | L1 缓存 miss | 一级缓存效率   |
| ILmr, DLmr, DLmw | LL 缓存 miss | 末级缓存效率   |
| Bc, Bi           | 分支指令/执行次数  | 程序控制流复杂度 |
| Bcm, Bim         | 分支预测失败次数   | 分支预测效率   |

## 5. 数据结构（Data Structure）

最终整理后的数据表（DataFrame / CSV）结构如下：
| 列名          | 含义                          |
| ----------- | --------------------------- |
| `index`     | 样本编号                        |
| `preset`    | 编码预设（fast–superfast）        |
| `qp`        | 量化参数                        |
| `seq_name`  | 视频序列名                       |
| `Ir`–`Bim`  | 13 项处理器事件                   |
| `E_hw_slow` | 对应 slow preset 下的硬件能耗（目标变量） |
| `config`    | 滤波配置编号（A/B）                 |

示例行：

| index | preset | qp | seq_name     | Ir     | Dr     | Dw     | … | Bim   | E_hw_slow | config |
| ----- | ------ | -- | ------------ | ------ | ------ | ------ | - | ----- | --------- | ------ |
| 1     | fast   | 27 | Crosswalk_4k | 5.3e11 | 1.2e11 | 8.6e10 | … | 2.1e7 | 24.3      | A      |
| 2     | fast   | 27 | Crosswalk_4k | 5.5e11 | 1.3e11 | 8.5e10 | … | 2.2e7 | 24.3      | B      |

## 6. 建模与分析（Modeling and Analysis）

### 6.1 模型选择

采用 **XGBoost 回归模型** 建立能耗预测关系：

\[
\hat{E} = f_{\text{XGB}}(Ir, Dr, Dw, I1mr, D1mr, D1mw, ILmr, DLmr, DLmw, Bc, Bcm, Bi, Bim)
\]

- **输入特征**：13 项 PEs  
- **输出目标**：对应 slow 预设下的能耗数据 \(E_{hw, slow}\)  
- **模型类型**：非线性梯度提升树（XGBoostRegressor）

**示例参数：**

```python
xgb.XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0
)
```
### 6.2 模型训练策略

- 按 **配置 (A/B)** 分组分别建模，比较两种滤波配置下的模型性能。  
- 采用 **5 折交叉验证** 评估泛化能力。  
- 计算平均误差率（Error Rate, 类似 MAPE）：  

\[
\text{Error Rate} = \frac{1}{N} \sum_i \left| \frac{\hat{E}_i - E_i}{E_i} \right|
\]

- 对比指标：  
  - 平均误差率（Mean Error Rate）  
  - R²（拟合优度）  
  - 特征重要性（Feature Importance）

---

### 6.3 分析方向

1. **模型预测性能**  
   - 比较 Config A 与 Config B 的平均误差率；  
   - 分析 fast–superfast 不同预设下的预测误差差异。  

2. **事件特征贡献度**  
   - 提取 XGBoost 的 `feature_importances_`；  
   - 观察哪些事件在不同滤波配置下影响最显著（如 cache miss 或 branch misprediction）。  

3. **滤波配置差异**  
   - 对比两组配置下的平均事件计数变化；  
   - 判断 SAO 与 Deblock 的开启/关闭是否带来更高的内存访问或分支行为。  

---

## 7. 实验结果预期（Expected Findings）

- SAO 开启（Config A）预计增加 **内存读写量 (Dr/Dw)** 与 **缓存 miss**，因其像素邻域滤波需要更多数据访问；  
- Deblock 开启（Config B）可能增加 **分支预测失败 (Bim)**，因其条件判断更多；  
- 两组模型的总体预测误差率（Error Rate）预期在 **5%–8%**；  
- XGBoost 模型能有效捕捉非线性特征交互（如 Dr × DLmw、Bc × Bim），显著优于线性回归；  
- 特征重要性排序揭示能耗关键来源：  
  - 高频特征：`Dr`, `DLmr`, `DLmw`, `Bcm`  
  - 低频但高能耗特征：`Bim`, `ILmr`  

---

## 8. 实验时间计划（Time Plan）

| 阶段 | 内容 | 预计时间 |
|------|------|----------|
| 环境搭建 | x265 + Valgrind 安装验证 | 0.5 天 |
| Config A Profiling | 第一轮数据采集 | 1 天 |
| Config B Profiling | 第二轮数据采集 | 1 天 |
| 数据提取与整合 | callgrind → CSV 转换 + 能耗对齐 | 0.5 天 |
| 建模与验证 | XGBoost 训练与误差分析 | 0.5 天 |
| 报告与图表 | 可视化 + 结论总结 | 0.5 天 |

---

## 9. 结果展示建议（Visualization Plan）

| 图表 | 内容 |
|------|------|
| **Error Rate vs Preset (A/B)** | 两组滤波配置的预测误差对比 |
| **Predicted vs Measured** | 模型拟合散点对角图 |
| **Feature Importance (XGBoost)** | 不同配置下事件贡献度排序 |
| **Event Change (ΔPEs)** | 两组配置的平均事件增减热力图 |
| **Energy Difference Bar** | Config A vs B 在 slow preset 下的能耗差异 |

---

## 10. 实验结论（Expected Conclusion）

- SAO 与 Deblocking 的启用/禁用会显著改变 CPU 微结构行为；  
- 处理器事件（PEs）与硬件能耗存在稳定的可学习关系；  
- 树型模型（XGBoost）能有效捕捉非线性耦合，预测误差低；  
- 基于 PEs 的能耗建模为编码器能耗优化提供了可解释路径；  
- 可量化评估 SAO 与 Deblock 模块在能耗层面的相对代价。  
