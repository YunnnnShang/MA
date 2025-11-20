#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_energy_models_ABC.py

目标：
1. (新) 执行 A/B/C 差分分析 (Mean, CV, Ratios) 来对比 'default', 'hw-like', 'dis_filter'。
2. (原) 以 PEs 预测 E_hw_slow 为中心, 对所有三个配置进行建模并计算 MAPE。

步骤：
1) 读取 abc.xlsx (包含 default, hw-like, dis_filter)。
2) 补齐 dis_filter 缺失的 E_hw_slow 值 (为建模做准备)。
3) (新) 运行差分分析：
   - 计算并*保存* Mean / CV / Ratios 对比表。
4) (原) 运行建模分析：
   - 对 *每个* 配置 (default, hw-like, dis_filter) 单独进行 5-fold 交叉验证。
   - 训练线性回归和 XGBoost 模型。
   - 计算并*保存* MAPE / R² / RMSE 结果。

"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor
import sys
import warnings

# --- 核心配置 ---
# 确保 abc.xlsx 与此脚本在同一目录, 或者提供完整路径
DATA_PATH = "abc.xlsx" 
# (修正) Excel 文件中数据表头的起始行 (第1行, 0-indexed)
HEADER_ROW = 0 
OUTPUT_DIR = Path("./model_outputs_abc") # 保存到新的输出目录

# --- 列定义 (必须与 abc.xlsx 中的列名完全一致) ---
CONFIG_COL = 'config'      # 配置 (default, hw-like, dis_filter)
PRESET_COL = 'preset'      # 预设 (fast, faster, ...)
# (修正) 你的 CSV/Excel 中列名为 'seq_name'
GROUP_COL = 'seq_name'     # 分组键 (例如 Aerial3200_2k) 
TARGET_COL = 'E_hw_slow' # 预测目标

# 处理器事件 (PEs) 特征列
FEATURE_COLS = [
    'Ir', 'Dr', 'Dw', 'I1mr', 'D1mr', 'D1mw', 
    'ILmr', 'DLmr', 'DLmw', 'Bc', 'Bcm', 'Bi', 'Bim'
]

def load_and_prep_data(data_path: str) -> pd.DataFrame | None:
    """加载并准备 A/B/C 数据。"""
    print(f"--- 正在加载数据: {data_path} ---")
    try:
        # header=HEADER_ROW (0) 表示数据从第1行开始
        df = pd.read_excel(data_path, header=HEADER_ROW)
        print(f"成功加载 {len(df)} 行数据。")
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{data_path}'", file=sys.stderr)
        return None
    except Exception as e:
        print(f"加载 Excel 时出错: {e}", file=sys.stderr)
        return None

    # 确保所有必需列都存在
    required_cols = [CONFIG_COL, PRESET_COL, GROUP_COL, TARGET_COL] + FEATURE_COLS
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"错误: 数据中缺少以下列: {missing_cols}", file=sys.stderr)
        return None

    # 1. 补齐 E_hw_slow (为建模做准备)
    #    (这假设 'default' 或 'hw-like' 行的 E_hw_slow 值是有效的)
    print(f"--- 正在补齐 '{TARGET_COL}' ... ---")
    nan_before = df[TARGET_COL].isna().sum()
    if nan_before > 0:
        fill_keys = [GROUP_COL, 'qp'] # 假设 'qp' 列存在
        if 'qp' not in df.columns:
            print("警告: 'qp' 列不存在, 仅使用 '{GROUP_COL}' 填充, 结果可能不准确。", file=sys.stderr)
            fill_keys = [GROUP_COL]
            
        df[TARGET_COL] = df.groupby(fill_keys)[TARGET_COL].transform('first')
        nan_after = df[TARGET_COL].isna().sum()
        print(f"补齐前: {nan_before} 个空值。补齐后: {nan_after} 个空值。")
    else:
        print("E_hw_slow 值完整, 无需补齐。")

    # 2. 转换数据类型以进行计算
    for col in FEATURE_COLS + [TARGET_COL]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 丢弃任何仍然无法计算的行
    df.dropna(subset=FEATURE_COLS + [TARGET_COL], inplace=True)
    
    print(f"数据准备完毕。剩余有效数据 {len(df)} 行。")
    return df

def run_ablation_analysis(df: pd.DataFrame, output_dir: Path):
    """
    (新功能) 执行 A/B/C 差分分析 (Mean, CV, Ratios)。
    """
    print("\n" + "="*80)
    print("               (新) 1. A/B/C 差分分析 (逻辑对比)")
    print("="*80)
    
    # 确保所有特征都存在
    valid_features = [col for col in FEATURE_COLS if col in df.columns]
    
    # --- a) 均值 (Mean) ---
    df_mean = df.groupby(CONFIG_COL)[valid_features].mean()
    
    # --- b) 变异系数 (CV) ---
    df_std = df.groupby(CONFIG_COL)[valid_features].std()
    df_cv = df_std / df_mean
    
    # --- c) 归一化比率 (Ratios) ---
    df_ratios = pd.DataFrame(index=df_mean.index)
    try:
        df_ratios['MPI (D1m_total / Ir)'] = (df_mean['D1mr'] + df_mean['D1mw']) / df_mean['Ir']
        df_ratios['Branch_Density (Bc / Ir)'] = df_mean['Bc'] / df_mean['Ir']
        df_ratios['Branch_Miss_Rate (Bcm / Bc)'] = df_mean['Bcm'] / df_mean['Bc']
    except KeyError as e:
        print(f"警告: 计算 Ratios 时缺少列: {e}", file=sys.stderr)

    # --- 保存文件 ---
    (output_dir / "ablation").mkdir(parents=True, exist_ok=True)
    path_mean = output_dir / "ablation" / "ablation_study_mean.csv"
    path_cv = output_dir / "ablation" / "ablation_study_cv.csv"
    path_ratios = output_dir / "ablation" / "ablation_study_ratios.csv"
    
    df_mean.to_csv(path_mean)
    df_cv.to_csv(path_cv)
    df_ratios.to_csv(path_ratios)
    
    # --- (修改) 移除打印到终端的大型表格 ---
    # print("\n--- [差分分析 1/3] 均值 (Mean) 对比 (平均逻辑开销) ---")
    # print(df_mean[['Ir', 'Dr', 'Bc', 'D1mr', 'Bcm']].to_markdown(floatfmt=",.2e"))
    
    # print("\n--- [差分分析 2/3] 变异系数 (CV) 对比 (逻辑波动性) ---")
    # print(df_cv[['Ir', 'Dr', 'Bc', 'D1mr', 'Bcm']].to_markdown(floatfmt=".4f"))

    # print("\n--- [差分分析 3/3] 归一化比率 (Ratios) 对比 (归一化效率) ---")
    # print(df_ratios.to_markdown(floatfmt=".6f"))
    
    print(f"\n[差分分析] 结果已保存到 {output_dir / 'ablation'}")

def run_modeling_analysis(df: pd.DataFrame, output_dir: Path):
    """
    (原功能) 执行 A/B/C 建模分析 (MAPE, R^2)。
    """
    print("\n" + "="*80)
    print("               (原) 2. A/B/C 建模分析 (模型精度)")
    print("="*80)
    
    (output_dir / "modeling").mkdir(parents=True, exist_ok=True)
    
    # 获取所有有效的配置
    valid_configs = df[CONFIG_COL].unique()
    print(f"将为以下 {len(valid_configs)} 个配置分别建模: {valid_configs}")

    all_oof_preds = []
    overall_metrics = []

    for config in valid_configs:
        print(f"\n--- 正在处理配置: {config} ---")
        
        group_df = df[df[CONFIG_COL] == config].copy()
        if group_df.empty:
            print(f"配置 {config} 没有数据, 已跳过。")
            continue
            
        X = group_df[FEATURE_COLS]
        y = group_df[TARGET_COL]
        groups = group_df[GROUP_COL]

        # 确保 OOF 数组有空间
        oof_preds_linear = np.zeros_like(y)
        oof_preds_xgb = np.zeros_like(y)

        # 按 seqname 分组的 5 折交叉验证
        gkf = GroupKFold(n_splits=5)
        
        for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
            # print(f"  ... Fold {fold+1}/5")
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # --- 1. 线性回归 (带标准化) ---
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            lr = LinearRegression()
            lr.fit(X_train_scaled, y_train)
            oof_preds_linear[test_idx] = lr.predict(X_test_scaled)
            
            # --- 2. XGBoost ---
            xgb = XGBRegressor(random_state=42, n_jobs=-1)
            xgb.fit(X_train, y_train) # XGB 不需要标准化
            oof_preds_xgb[test_idx] = xgb.predict(X_test)

        # 保存 OOF 预测结果
        group_df['pred_linear'] = oof_preds_linear
        group_df['pred_xgb'] = oof_preds_xgb
        all_oof_preds.append(group_df)
        
        # 计算整体指标
        for model_name, preds in [('Linear', oof_preds_linear), ('XGBoost', oof_preds_xgb)]:
            r2 = r2_score(y, preds)
            rmse = np.sqrt(mean_squared_error(y, preds))
            # MAPE-like (原脚本的 MER)
            mape_like = np.mean(np.abs((preds - y) / y))
            
            overall_metrics.append({
                'config': config,
                'model': model_name,
                'r2': r2,
                'rmse': rmse,
                'mape_like': mape_like
            })
            # (修改) 移除循环内的打印
            # print(f"  [{config} / {model_name}] R²: {r2:.4f}, MAPE: {mape_like:.6f}")

    # --- 保存所有建模结果 ---
    if not all_oof_preds:
        print("未生成任何模型, 脚本终止。", file=sys.stderr)
        return

    # 1. 整体指标
    df_overall = pd.DataFrame(overall_metrics)
    overall_path = output_dir / "modeling" / "overall_metrics.csv"
    df_overall.to_csv(overall_path, index=False)
    print(f"\n[建模] 整体指标已保存到: {overall_path.name}")

    # 2. OOF 预测
    df_oof = pd.concat(all_oof_preds)
    oof_path = output_dir / "modeling" / "oof_predictions.csv"
    df_oof.to_csv(oof_path, index=False)
    print(f"[建模] OOF 预测已保存到: {oof_path.name}")
    
    # 3. 按 Preset 拆分的 MAPE
    #    (这里我们只使用 OOF 表来计算)
    df_oof['err_linear'] = np.abs((df_oof['pred_linear'] - df_oof[TARGET_COL]) / df_oof[TARGET_COL])
    df_oof['err_xgb'] = np.abs((df_oof['pred_xgb'] - df_oof[TARGET_COL]) / df_oof[TARGET_COL])
    
    mape_tbl = df_oof.groupby([CONFIG_COL, PRESET_COL])[['err_linear', 'err_xgb']].mean().reset_index()
    mape_tbl.rename(columns={'err_linear': 'mape_linear', 'err_xgb': 'mape_xgb'}, inplace=True)
    
    mape_tbl_path = output_dir / "modeling" / "mape_by_preset_long.csv"
    mape_tbl.to_csv(mape_tbl_path, index=False)
    print(f"[建模] 按 Preset 拆分的 MAPE (长表) 已保存到: {mape_tbl_path.name}")
    
    # 4. 按 Preset 拆分的 MAPE (宽表, 用于对比)
    #    (更新了这里的逻辑, 使其能自动处理3个或更多配置)
    pivot_linear = mape_tbl.pivot(index=PRESET_COL, columns=CONFIG_COL, values='mape_linear')
    pivot_xgb = mape_tbl.pivot(index=PRESET_COL, columns=CONFIG_COL, values='mape_xgb')
    
    out_compare = pd.DataFrame(index=pivot_linear.index)
    valid_configs = df[CONFIG_COL].unique() # 再次获取配置列表
    for cfg in valid_configs:
        if cfg in pivot_linear.columns:
            out_compare[f"{cfg}_linear"] = pivot_linear[cfg]
        if cfg in pivot_xgb.columns:
            out_compare[f"{cfg}_xgb"] = pivot_xgb[cfg]

    mape_compare_path = output_dir / "modeling" / "mape_by_preset_wide.csv"
    out_compare.to_csv(mape_compare_path, index=True)
    print(f"[建模] 按 Preset 拆分的 MAPE (宽表) 已保存到: {mape_compare_path.name}")


def main():
    # 创建主输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载并准备数据 (包括补齐)
    df = load_and_prep_data(DATA_PATH)
    
    if df is None:
        print("数据加载失败, 脚本终止。", file=sys.stderr)
        sys.exit(1)
        
    # --- 1. (新) 运行 A/B/C 差分分析 ---
    run_ablation_analysis(df, OUTPUT_DIR)
    
    # --- 2. (原) 运行 A/B/C 建模 ---
    run_modeling_analysis(df, OUTPUT_DIR)
    
    print("\n--- 脚本执行完毕 ---")

if __name__ == "__main__":
    # 抑制 pandas 中关于 groupby.transform 可能产生的性能警告
    warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
    main()