# -*- coding: utf-8 -*-
"""
perf_extended_modeling_by_config_preset_v2.py

修复点
------
1) 修复绘图时报错：表格里既有字符串（preset）又有浮点数，np.round 不能直接作用于混合类型。
   -> 新的 plot_table_png() 会分别格式化数值与字符串。
2) 其余逻辑与上一版一致：仅 Intel、18个PEs特征、A/B分别建模（Linear + XGB/GBR备选）、GroupKFold按seqname分组、
   输出 Overall 与 “MAPE by preset”的对比表 + PNG。

用法
------
python perf_extended_modeling_by_config_preset_v2.py ^
  --summary_csv "H:\\perf_out_ext\\perf_extended_summary_with_E_hw_slow.csv" ^
  --outdir "H:\\perf_out_ext\\model_perf"

"""

import argparse
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LinearRegression

# xgboost 不可用则退回到 GBR
try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except Exception:
    from sklearn.ensemble import GradientBoostingRegressor
    HAS_XGB = False


# —— 18 个 PEs ——（如你的列名有轻微差异，在这里修正）
EXPECTED_18_EVENTS: List[str] = [
    "instructions",
    "cycles",
    "branches",                 # 若你的表里是 branch-instructions，请在下面 ALIASES 中映射
    "branch-misses",
    "cache-references",
    "cache-misses",
    "l1-dcache-loads",
    "l1-dcache-load-misses",
    "l1-dcache-stores",
    "l1-icache-load-misses",
    "llc-loads",
    "llc-load-misses",
    "llc-stores",
    "llc-store-misses",
    "dtlb-loads",
    "dtlb-load-misses",
    "dtlb-stores",
    "dtlb-store-misses",
]

ALIASES = {
    "branch-instructions": "branches",
}


def normalize_event_columns(df: pd.DataFrame) -> pd.DataFrame:
    """将别名列合并到标准列名（避免丢列）"""
    for src, dst in ALIASES.items():
        if src in df.columns:
            if dst not in df.columns:
                df[dst] = df[src]
            else:
                df[dst] = df[dst].where(~df[dst].isna(), df[src])
    return df


def load_summary(summary_csv: str) -> pd.DataFrame:
    df = pd.read_csv(summary_csv)
    need_cols = {"index", "qp", "preset", "seqname", "config", "E_hw_slow"}
    missing = need_cols - set(df.columns)
    if missing:
        raise ValueError(f"缺少必要列：{missing}")

    df["preset"] = df["preset"].astype(str).str.lower()
    df["config"] = df["config"].astype(str).str.upper()

    df = normalize_event_columns(df)
    for ev in EXPECTED_18_EVENTS:
        if ev not in df.columns:
            df[ev] = np.nan

    df = df[df["config"].isin(["A", "B"])].copy()
    df = df[~df["E_hw_slow"].isna()].copy()
    return df


def evaluate_one_split(X, y, model_type: str, random_state: int = 42):
    if model_type == "linear":
        mdl = LinearRegression()
    else:
        if HAS_XGB:
            mdl = XGBRegressor(
                n_estimators=600, max_depth=5, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, random_state=random_state,
                n_jobs=0,
            )
        else:
            from sklearn.ensemble import GradientBoostingRegressor
            mdl = GradientBoostingRegressor(random_state=random_state)

    mdl.fit(X, y)
    yhat = mdl.predict(X)
    return mean_absolute_percentage_error(y, yhat)


def evaluate_by_preset(df_cfg: pd.DataFrame, features: List[str], seed: int = 42) -> Tuple[pd.DataFrame, Dict[str, float]]:
    rows = []
    for preset in sorted(df_cfg["preset"].unique()):
        sub = df_cfg[df_cfg["preset"] == preset].copy()
        X = sub[features].astype(float).fillna(0.0)
        y = sub["E_hw_slow"].astype(float)
        groups = sub["seqname"].astype(str)

        unique_groups = groups.nunique()
        do_cv = unique_groups >= 5 and len(sub) >= 20

        if do_cv:
            gkf = GroupKFold(n_splits=5)
            m_lin, m_boost = [], []
            for tr, te in gkf.split(X, y, groups):
                Xtr, Xte = X.iloc[tr], X.iloc[te]
                ytr, yte = y.iloc[tr], y.iloc[te]

                # Linear
                mdl_lin = LinearRegression()
                mdl_lin.fit(Xtr, ytr)
                yhat = mdl_lin.predict(Xte)
                m_lin.append(mean_absolute_percentage_error(yte, yhat))

                # Boost
                if HAS_XGB:
                    mdl_b = XGBRegressor(
                        n_estimators=600, max_depth=5, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, random_state=seed, n_jobs=0
                    )
                else:
                    from sklearn.ensemble import GradientBoostingRegressor
                    mdl_b = GradientBoostingRegressor(random_state=seed)
                mdl_b.fit(Xtr, ytr)
                yhat2 = mdl_b.predict(Xte)
                m_boost.append(mean_absolute_percentage_error(yte, yhat2))

            mape_lin = float(np.mean(m_lin))
            mape_boost = float(np.mean(m_boost))
        else:
            # in-sample 兜底
            mape_lin = float(evaluate_one_split(X, y, "linear", seed))
            mape_boost = float(evaluate_one_split(X, y, "boost", seed))

        rows.append({
            "preset": preset,
            "Linear_MAPE": mape_lin,
            "Boost_MAPE": mape_boost,
            "n": int(len(sub)),
            "groups": int(unique_groups),
            "cv": "GroupKFold(5)" if do_cv else "in-sample",
        })

    per_preset_df = pd.DataFrame(rows).sort_values("preset")

    # overall
    X_all = df_cfg[features].astype(float).fillna(0.0)
    y_all = df_cfg["E_hw_slow"].astype(float)
    groups_all = df_cfg["seqname"].astype(str)

    unique_groups_all = groups_all.nunique()
    do_cv_all = unique_groups_all >= 5 and len(df_cfg) >= 20

    if do_cv_all:
        gkf = GroupKFold(n_splits=5)
        m_lin, m_boost = [], []
        for tr, te in gkf.split(X_all, y_all, groups_all):
            Xtr, Xte = X_all.iloc[tr], X_all.iloc[te]
            ytr, yte = y_all.iloc[tr], y_all.iloc[te]

            mdl_lin = LinearRegression()
            mdl_lin.fit(Xtr, ytr)
            yhat = mdl_lin.predict(Xte)
            m_lin.append(mean_absolute_percentage_error(yte, yhat))

            if HAS_XGB:
                mdl_b = XGBRegressor(
                    n_estimators=800, max_depth=6, learning_rate=0.05,
                    subsample=0.8, colsample_bytree=0.8, random_state=seed, n_jobs=0
                )
            else:
                from sklearn.ensemble import GradientBoostingRegressor
                mdl_b = GradientBoostingRegressor(random_state=seed)
            mdl_b.fit(Xtr, ytr)
            yhat2 = mdl_b.predict(Xte)
            m_boost.append(mean_absolute_percentage_error(yte, yhat2))

        overall = {
            "Linear_MAPE": float(np.mean(m_lin)),
            "Boost_MAPE": float(np.mean(m_boost)),
            "n": int(len(df_cfg)),
            "groups": int(unique_groups_all),
            "cv": "GroupKFold(5)",
        }
    else:
        overall = {
            "Linear_MAPE": float(evaluate_one_split(X_all, y_all, "linear", seed)),
            "Boost_MAPE": float(evaluate_one_split(X_all, y_all, "boost", seed)),
            "n": int(len(df_cfg)),
            "groups": int(unique_groups_all),
            "cv": "in-sample",
        }

    return per_preset_df, overall


def make_preset_comparison_table(presets: List[str],
                                 A_df: pd.DataFrame,
                                 B_df: pd.DataFrame) -> pd.DataFrame:
    A = A_df.set_index("preset")[["Linear_MAPE", "Boost_MAPE"]].rename(
        columns={"Linear_MAPE": "A_linear", "Boost_MAPE": "A_xgb"}
    )
    B = B_df.set_index("preset")[["Linear_MAPE", "Boost_MAPE"]].rename(
        columns={"Linear_MAPE": "B_linear", "Boost_MAPE": "B_xgb"}
    )
    idx = presets
    merged = pd.concat([A.reindex(idx), B.reindex(idx)], axis=1)
    merged["AminusB_xgb"] = merged["A_xgb"] - merged["B_xgb"]
    merged["AminusB_linear"] = merged["A_linear"] - merged["B_linear"]
    merged = merged.reset_index().rename(columns={"index": "preset"})
    return merged


def _format_table_cells(df: pd.DataFrame, decimals: int = 6) -> List[List[str]]:
    """把 DataFrame 转成字符串表格，数值保留 decimals 位，小数；非数值保持原样。"""
    out = []
    for _, row in df.iterrows():
        cells = []
        for val in row:
            if pd.api.types.is_number(val):
                if pd.isna(val):
                    cells.append("")
                else:
                    cells.append(f"{val:.{decimals}f}")
            else:
                cells.append(str(val))
        out.append(cells)
    return out


def plot_table_png(df: pd.DataFrame, title: str, out_png: Path):
    """绘制表格PNG（兼容字符串+数值混合列）"""
    import matplotlib.pyplot as plt

    cell_text = _format_table_cells(df, decimals=6)
    col_labels = list(df.columns)

    fig_h = 0.8 + 0.5 * (len(df) + 1)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    ax.axis("off")
    tbl = ax.table(cellText=cell_text, colLabels=col_labels, loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.3)
    ax.set_title(title, pad=12)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary_csv", type=str, required=True,
                    help="perf_extended_summary_with_E_hw_slow.csv 路径（仅 Intel）")
    ap.add_argument("--outdir", type=str, required=True,
                    help="输出目录")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_summary(args.summary_csv)

    # 允许固定顺序（如果你的数据包含这四类，将按此顺序展示）
    preset_order = ["fast", "faster", "veryfast", "superfast"]
    presets = [p for p in preset_order if p in set(df["preset"].unique())]
    # 如有其他 preset 也包含进来
    extras = [p for p in sorted(df["preset"].unique()) if p not in presets]
    presets = presets + extras

    feature_cols = [ev for ev in EXPECTED_18_EVENTS if ev in df.columns]

    dfA = df[df["config"] == "A"].copy()
    dfB = df[df["config"] == "B"].copy()

    A_preset_df, A_overall = evaluate_by_preset(dfA, feature_cols, seed=args.seed)
    B_preset_df, B_overall = evaluate_by_preset(dfB, feature_cols, seed=args.seed)

    A_preset_path = outdir / "A_mape_by_preset.csv"
    B_preset_path = outdir / "B_mape_by_preset.csv"
    A_preset_df.to_csv(A_preset_path, index=False)
    B_preset_df.to_csv(B_preset_path, index=False)

    preset_cmp = make_preset_comparison_table(presets, A_preset_df, B_preset_df)
    preset_cmp_path = outdir / "MAPE_by_preset_Model_Performance_Comparison.csv"
    preset_cmp.to_csv(preset_cmp_path, index=False)

    overall_cmp = pd.DataFrame([
        {"config": "A", **A_overall},
        {"config": "B", **B_overall},
        {"config": "AminusB",
         "Linear_MAPE": A_overall["Linear_MAPE"] - B_overall["Linear_MAPE"],
         "Boost_MAPE": A_overall["Boost_MAPE"] - B_overall["Boost_MAPE"],
         "n": np.nan, "groups": np.nan, "cv": f"{A_overall.get('cv','')}/{B_overall.get('cv','')}"}
    ])
    overall_cmp_path = outdir / "Overall_Model_Performance_Comparison.csv"
    overall_cmp.to_csv(overall_cmp_path, index=False)

    png_path = outdir / "MAPE_by_preset_Model_Performance_Comparison.png"
    plot_table_png(
        preset_cmp[["preset", "A_linear", "A_xgb", "B_linear", "B_xgb", "AminusB_xgb", "AminusB_linear"]],
        title="MAPE by preset — Model Performance Comparison",
        out_png=png_path
    )

    print(f"[OK] 写出：{A_preset_path}")
    print(f"[OK] 写出：{B_preset_path}")
    print(f"[OK] 写出：{preset_cmp_path}")
    print(f"[OK] 写出：{overall_cmp_path}")
    print(f"[OK] 表格图片：{png_path}")
    print(f"[INFO] A overall: Linear={A_overall['Linear_MAPE']:.6f}, Boost={A_overall['Boost_MAPE']:.6f}")
    print(f"[INFO] B overall: Linear={B_overall['Linear_MAPE']:.6f}, Boost={B_overall['Boost_MAPE']:.6f}")


if __name__ == "__main__":
    main()
