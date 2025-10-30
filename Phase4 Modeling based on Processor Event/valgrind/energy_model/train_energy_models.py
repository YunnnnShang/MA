#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_preset_mape.py

目标：以“软件侧处理器事件（PEs）→ 预测硬件 slow 能耗 E_hw_slow”为中心，
严格对比两种滤波配置（Config A: --no-deblock --sao；Config B: --deblock --no-sao）
在不同 preset 下的预测误差（MAPE），并给出支撑机理观察的 PEs 统计。

步骤：
1) 读取 H:\valgrind\callgrind_summary_with_E_hw_slow.csv
2) 对 A/B 各自做 5-fold GroupKFold(seq_name)：
   - 线性回归（标准化）
   - XGBoost（默认参数，可后续调优）
   生成全量 OOF 预测（不会泄漏）
3) 按 preset 分组，分别计算 MAPE（Mean Error Rate）：
   MER = mean(|(y_pred - y_true) / y_true|)
4) 输出以下文件到 H:\valgrind\model_outputs：
   - mape_by_preset.csv               （主表：A/B × Linear/XGB 的每个 preset 的 MAPE）
   - overall_metrics.csv              （A/B × Linear/XGB 的整体 R² / RMSE / MAPE）
   - pe_means_by_preset_config.csv    （支撑：各 preset、各 config 的 PEs 均值）
   - oof_predictions.csv              （OOF 逐样本：便于你做散点/误差分布图）

注：若 preset 的“组数（seq_name 数量）”< 折数，会退化到 KFold。
"""

import os
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import GroupKFold, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb

warnings.filterwarnings("ignore")
RND_SEED = 42

# -------- 配置 --------
INPUT_CSV  = r"H:\valgrind\callgrind_summary_with_E_hw_slow.csv"
OUTPUT_DIR = r"H:\valgrind\model_outputs"
N_SPLITS   = 5
TARGET_COL = "E_hw_slow"
GROUP_COL  = "seq_name"
CONFIG_COL = "config"   # A / B
PRESET_COL = "preset"

EXPECTED_FEATURES = [
    "Ir", "Dr", "Dw",
    "I1mr", "D1mr", "D1mw",
    "ILmr", "DLmr", "DLmw",
    "Bc", "Bcm", "Bi", "Bim"
]

XGB_PARAMS = dict(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=RND_SEED,
    verbosity=0,
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

def mean_error_rate(y_true, y_pred, eps=1e-8):
    denom = np.where(np.abs(y_true) < eps, eps, y_true)
    return np.mean(np.abs((y_pred - y_true) / denom))

def find_cols(df, candidates):
    cols_lower = {c.lower().strip(): c for c in df.columns}
    found = []
    for cand in candidates:
        key = cand.lower().strip()
        if key in cols_lower:
            found.append(cols_lower[key])
    return found

def prepare_X_y(df, feature_cols, target_col):
    X = df[feature_cols].astype(float).values
    y = df[target_col].astype(float).values
    return X, y

def get_cv_splits(X, y, groups, n_splits):
    uniq = np.unique(groups)
    if len(uniq) >= n_splits:
        cv = GroupKFold(n_splits=n_splits)
        return list(cv.split(X, y, groups)), "GroupKFold"
    else:
        k = min(n_splits, max(2, len(y)))
        cv = KFold(n_splits=k, shuffle=True, random_state=RND_SEED)
        return list(cv.split(X, y)), "KFold"

def oof_predictions_for_config(sub_df, feature_cols):
    """
    对单个 config 生成 OOF 预测（Linear + XGB），并返回包含以下列的 DataFrame：
    [config, preset, seq_name, y_true, y_pred_linear, y_pred_xgb]
    """
    X, y = prepare_X_y(sub_df, feature_cols, TARGET_COL)
    groups = sub_df[GROUP_COL].astype(str).values
    presets = sub_df[PRESET_COL].astype(str).values

    splits, cv_name = get_cv_splits(X, y, groups, N_SPLITS)

    # 容器
    y_pred_lin = np.zeros_like(y, dtype=float)
    y_pred_xgb = np.zeros_like(y, dtype=float)

    for tr_idx, te_idx in splits:
        X_tr, X_te = X[tr_idx], X[te_idx]
        y_tr, y_te = y[tr_idx], y[te_idx]

        # Linear (with scaling)
        scaler = StandardScaler().fit(X_tr)
        Xtr_s = scaler.transform(X_tr)
        Xte_s = scaler.transform(X_te)
        lin = LinearRegression().fit(Xtr_s, y_tr)
        y_pred_lin[te_idx] = lin.predict(Xte_s)

        # XGB
        xgb_model = xgb.XGBRegressor(**XGB_PARAMS)
        xgb_model.fit(X_tr, y_tr)
        y_pred_xgb[te_idx] = xgb_model.predict(X_te)

    out = pd.DataFrame({
        CONFIG_COL: sub_df[CONFIG_COL].values,
        PRESET_COL: presets,
        GROUP_COL:  sub_df[GROUP_COL].values,
        "y_true":   y,
        "y_pred_linear": y_pred_lin,
        "y_pred_xgb":    y_pred_xgb,
    })
    return out

def main():
    df = pd.read_csv(INPUT_CSV, low_memory=False)

    # 找到特征列
    feature_cols = find_cols(df, EXPECTED_FEATURES)
    if len(feature_cols) == 0:
        raise ValueError(f"未找到任何预期特征列，检查列名。文件列：{list(df.columns)}")
    missing_feats = [c for c in EXPECTED_FEATURES if c not in feature_cols]
    if missing_feats:
        print("警告：以下预期特征未在文件中找到，将被忽略：", missing_feats)

    # 必要列检查
    for c in [TARGET_COL, GROUP_COL, CONFIG_COL, PRESET_COL]:
        if c not in df.columns:
            raise ValueError(f"缺少必要列 '{c}'。当前列：{list(df.columns)}")

    # 清理数据（去缺失）
    df = df.dropna(subset=[TARGET_COL] + feature_cols + [PRESET_COL, CONFIG_COL, GROUP_COL]).copy()

    # 仅保留 A/B
    valid_configs = ["A", "B"]
    df = df[df[CONFIG_COL].isin(valid_configs)].copy()

    # 每个 config 生成 OOF 预测
    oof_all = []
    overall_rows = []
    for cfg in valid_configs:
        sub = df[df[CONFIG_COL] == cfg].copy()
        if sub.empty:
            continue

        oof = oof_predictions_for_config(sub, feature_cols)
        oof_all.append(oof)

        # 整体指标（不分 preset）
        y_true = oof["y_true"].values
        for mdl, col in [("Linear", "y_pred_linear"), ("XGBoost", "y_pred_xgb")]:
            y_pred = oof[col].values
            r2 = r2_score(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            mer = mean_error_rate(y_true, y_pred)
            overall_rows.append({
                "config": cfg,
                "model": mdl,
                "r2": r2,
                "rmse": rmse,
                "mape_like": mer
            })

    oof_all = pd.concat(oof_all, ignore_index=True)
    overall_df = pd.DataFrame(overall_rows)

    # 按 preset 统计 MAPE（A/B × Linear/XGB）
    g = oof_all.groupby([CONFIG_COL, PRESET_COL])
    mape_tbl = g.apply(lambda d: pd.Series({
        "mape_linear": mean_error_rate(d["y_true"].values, d["y_pred_linear"].values),
        "mape_xgb":    mean_error_rate(d["y_true"].values, d["y_pred_xgb"].values),
        "n_samples":   len(d)
    })).reset_index()

    # 透视成你更易读的对比表：行 = preset，列 = (A_linear, A_xgb, B_linear, B_xgb)
    pivot_linear = mape_tbl.pivot(index=PRESET_COL, columns=CONFIG_COL, values="mape_linear")
    pivot_xgb    = mape_tbl.pivot(index=PRESET_COL, columns=CONFIG_COL, values="mape_xgb")
    # 合并成一个对照表
    # 列名：A_linear, A_xgb, B_linear, B_xgb，以及差值列（A_xgb - B_xgb）
    out_compare = pd.DataFrame(index=sorted(mape_tbl[PRESET_COL].unique()))
    for cfg in valid_configs:
        out_compare[f"{cfg}_linear"] = pivot_linear.get(cfg)
        out_compare[f"{cfg}_xgb"]    = pivot_xgb.get(cfg)
    out_compare["AminusB_xgb"]    = out_compare["A_xgb"] - out_compare["B_xgb"]
    out_compare["AminusB_linear"] = out_compare["A_linear"] - out_compare["B_linear"]

    # 支撑机理：各 preset & config 的 PEs 均值（便于观察趋势）
    pe_means = df.groupby([CONFIG_COL, PRESET_COL])[feature_cols].mean().reset_index()

    # 保存文件
    mape_tbl_path      = Path(OUTPUT_DIR) / "mape_by_preset_long.csv"
    mape_compare_path  = Path(OUTPUT_DIR) / "mape_by_preset_wide.csv"
    overall_path       = Path(OUTPUT_DIR) / "overall_metrics.csv"
    oof_path           = Path(OUTPUT_DIR) / "oof_predictions.csv"
    pe_means_path      = Path(OUTPUT_DIR) / "pe_means_by_preset_config.csv"

    mape_tbl.to_csv(mape_tbl_path, index=False)
    out_compare.to_csv(mape_compare_path, index=True)
    overall_df.to_csv(overall_path, index=False)
    oof_all.to_csv(oof_path, index=False)
    pe_means.to_csv(pe_means_path, index=False)

    print("已保存：")
    print(" - (长表) per-preset MAPE:", mape_tbl_path)
    print(" - (宽表) per-preset MAPE 对比 A/B × Linear/XGB:", mape_compare_path)
    print(" - 整体指标（R²/RMSE/MAPE）:", overall_path)
    print(" - OOF 逐样本预测:", oof_path)
    print(" - PEs 均值（按 preset×config）:", pe_means_path)

if __name__ == "__main__":
    main()
