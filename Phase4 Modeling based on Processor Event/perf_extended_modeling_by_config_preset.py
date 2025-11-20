# -*- coding: utf-8 -*-
"""
perf_v3.1_modeling_linear_raw_en.py

Final Modeling Script (Raw PEs Version - English):
1. Input: 'perf_abc_summary_with_E_hw_slow.csv'.
2. Features: Raw 18 HPC counts (No ratio normalization).
3. Model: LinearRegression only.
4. Experiments:
   - Experiment A: All Resolutions (All-Res).
   - Experiment 1 (Supplementary): 1080p Only (Robust total pixel check).
   - Experiment 2 (Supplementary): Feature Ablation Study.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import sys 

# Configuration
SUMMARY_CSV = Path("perf_abc_summary_with_E_hw_slow.csv")
OUTDIR = Path("v3.1_modeling_output_linear_raw_en")
OUTDIR.mkdir(exist_ok=True)

print("[INFO] Script configured for LinearRegression only.")
print("[INFO] Using 'Raw 18 HPC Counts' as features.")

# -----------------------------------------------------------------
# 1. Define Feature Columns (Raw 18 PEs)
# -----------------------------------------------------------------
FEATURE_COLS_18PE = [
    'instructions:u', 'cycles:u', 'branch_instructions:u', 'branch_misses:u',
    'cache_references:u', 'cache_misses:u', 'L1_dcache_loads:u', 
    'L1_dcache_load_misses:u', 'L1_dcache_stores:u', 'L1_icache_load_misses:u',
    'LLC_loads:u', 'LLC_load_misses:u', 'LLC_stores:u', 'LLC_store_misses:u',
    'dTLB_loads:u', 'dTLB_load_misses:u', 'dTLB_stores:u', 'dTLB_store_misses:u'
]

TARGET_COL = 'E_hw_slow'
GROUP_COL = 'video_name'


def clean_df(df, feature_cols_to_check):
    """
    Clean DataFrame:
    1. Drop rows with NaNs in Target or Feature columns.
    2. Ensure features are numeric.
    """
    print(f"Original data size: {len(df)}")
    
    # 1. Drop NaNs (Checking Target + Features + Width/Height for filtering)
    cols_to_check = [TARGET_COL] + feature_cols_to_check + ['width', 'height']
    
    missing_cols = [col for col in cols_to_check if col not in df.columns]
    if missing_cols:
        print(f"[ERROR] Missing required columns: {missing_cols}", file=sys.stderr)
        return pd.DataFrame() 
        
    df.dropna(subset=cols_to_check, inplace=True)
    print(f"Size after dropping NaNs: {len(df)}")
    
    # 2. Convert to numeric
    for col in feature_cols_to_check:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df.dropna(subset=cols_to_check, inplace=True)
    print(f"Final size after numeric conversion: {len(df)}")
    
    return df


def train_model(X_train, y_train):
    """
    Train a single LinearRegression model.
    """
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model


def train_eval_overall(df, feature_cols, target_col, group_col, n_splits=5, random_state=42, verbose=True):
    """
    Perform GroupKFold Cross-Validation (LinearRegression).
    Returns a dictionary of statistics.
    """
    
    missing_features = [col for col in feature_cols if col not in df.columns]
    if missing_features:
        print(f"[ERROR] train_eval_overall missing features: {missing_features}", file=sys.stderr)
        return {"Linear_MAPE": np.nan, "n": 0, "groups": 0, "cv": "0/0"}

    X = df[feature_cols]
    y = df[target_col]
    groups = df[group_col]
    
    # Standardization (Crucial even for raw counts)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    gkf = GroupKFold(n_splits=n_splits)
    
    linear_scores = []
    
    # Shuffle groups manually as GroupKFold doesn't support shuffle
    unique_groups = groups.unique()
    np.random.RandomState(random_state).shuffle(unique_groups)
    group_map = {group: i for i, group in enumerate(unique_groups)}
    shuffled_groups_indices = groups.map(group_map)

    for train_idx, test_idx in gkf.split(X_scaled, y, groups=shuffled_groups_indices):
        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train Linear Model
        model_lin = train_model(X_train, y_train)
        y_pred_lin = model_lin.predict(X_test)
        linear_scores.append(mean_absolute_percentage_error(y_test, y_pred_lin))

    n_samples = len(X)
    n_groups = len(groups.unique())
    cv_str = f"{len(linear_scores)}/{n_splits}"
    
    if not linear_scores:
        if verbose:
            print(f"[WARNING] CV generated no scores (Samples: {n_samples})", file=sys.stderr)
        return {"Linear_MAPE": np.nan, "n": n_samples, "groups": n_groups, "cv": cv_str}

    stats = {
        "Linear_MAPE": np.mean(linear_scores) * 100,
        "n": n_samples,
        "groups": n_groups,
        "cv": cv_str
    }
    return stats


def train_eval_by_preset(df, feature_cols, target_col, group_col, n_splits=5, random_state=42, verbose=True):
    """
    Perform evaluation grouped by 'preset'.
    """
    presets = sorted(df['preset'].unique())
    preset_results = []
    
    for preset in presets:
        if verbose:
            print(f"    ... Evaluating preset: {preset}")
        df_preset = df[df['preset'] == preset]
        
        n_groups_preset = df_preset[group_col].nunique()
        min_splits = min(n_splits, n_groups_preset)
        
        if min_splits < 2:
            if verbose:
                print(f"    [WARNING] Preset '{preset}' has only {n_groups_preset} groups. Skipping.")
            stats = {"Linear_MAPE": np.nan, "n": len(df_preset), "groups": n_groups_preset, "cv": f"0/{min_splits}"}
        else:
            stats = train_eval_overall(df_preset, feature_cols, target_col, group_col, n_splits=min_splits, random_state=random_state, verbose=verbose)
        
        stats['preset'] = preset
        preset_results.append(stats)
        
    return pd.DataFrame(preset_results)


# -----------------------------------------------------------------
# Experiment A & 1: Reusable Full Analysis Function
# -----------------------------------------------------------------
def run_full_analysis(df_clean, feature_cols, output_suffix, outdir):
    """
    Runs 'Overall' and 'By Preset' analysis for all configs in the dataframe.
    """
    
    configs = sorted(df_clean['config'].unique())
    print(f"\n--- Found {len(configs)} configs: {configs} ---")
    
    overall_results = []
    preset_results_list = []

    for config_name in configs:
        print(f"\n--- [Processing Config: '{config_name}'] ---")
        df_config_data = df_clean[df_clean['config'] == config_name].copy()
        
        if df_config_data.empty:
            print(f"  [WARNING] No data for '{config_name}', skipping.")
            continue
            
        print(f"  ... Running 'Overall' Evaluation (n={len(df_config_data)})")
        stats_overall = train_eval_overall(
            df_config_data,
            feature_cols,
            TARGET_COL,
            GROUP_COL,
            n_splits=5,
            random_state=42,
            verbose=True
        )
        stats_overall['config'] = config_name
        overall_results.append(stats_overall)
        print(f"  ... 'Overall' Result: {stats_overall}")

        print(f"  ... Running 'By Preset' Evaluation")
        df_preset = train_eval_by_preset(
            df_config_data,
            feature_cols,
            TARGET_COL,
            GROUP_COL,
            n_splits=5,
            random_state=42,
            verbose=True
        )
        df_preset['config'] = config_name
        preset_results_list.append(df_preset)
        print(f"  ... 'By Preset' Result:\n{df_preset}")

    # Save 'Overall' Results
    if not overall_results:
        print(f"[ERROR] Failed to generate 'Overall' results (Suffix: {output_suffix}).", file=sys.stderr)
        return
        
    df_overall_cmp = pd.DataFrame(overall_results)
    cols_overall = ['config'] + [col for col in df_overall_cmp.columns if col != 'config']
    df_overall_cmp = df_overall_cmp[cols_overall]
    
    overall_cmp_path = outdir / f"Linear_Overall_Performance{output_suffix}.csv"
    df_overall_cmp.to_csv(overall_cmp_path, index=False)
    print(f"\n[OK] Overall Model Performance saved to: {overall_cmp_path}")
    print(df_overall_cmp)

    # Save 'By Preset' Results
    if not preset_results_list:
        print(f"[ERROR] Failed to generate 'By Preset' results (Suffix: {output_suffix}).", file=sys.stderr)
        return
        
    df_preset_cmp = pd.concat(preset_results_list, ignore_index=True)
    cols_preset = ['config', 'preset'] + [col for col in df_preset_cmp.columns if col not in ['config', 'preset']]
    df_preset_cmp = df_preset_cmp[cols_preset]

    preset_cmp_path = outdir / f"Linear_MAPE_by_preset{output_suffix}.csv"
    df_preset_cmp.to_csv(preset_cmp_path, index=False)
    print(f"\n[OK] Model Performance by Preset saved to: {preset_cmp_path}")
    print(df_preset_cmp)


# -----------------------------------------------------------------
# Experiment 2: Feature Ablation Study
# -----------------------------------------------------------------
def run_ablation_study(df_all_configs, feature_cols, target_col, group_col, outdir):
    """
    Runs Feature Ablation Study for each config (LinearRegression Only).
    """
    print("\n\n--- [Experiment 2 (Supplementary): Running Feature Ablation Study] ---")
    results = []
    configs = sorted(df_all_configs['config'].unique())

    for config in configs:
        print(f"  ... Processing Ablation for: config = {config}")
        df_config = df_all_configs[df_all_configs['config'] == config].copy()
        if df_config.empty:
            continue
            
        n_groups_config = df_config[group_col].nunique()
        min_splits = min(5, n_groups_config) 
        
        if min_splits < 2:
            print(f"    [WARNING] Config '{config}' has too few groups, skipping ablation.")
            continue

        # 1. "All Features" (Standard Model)
        print("    - Evaluation (All Features) ...")
        stats_all = train_eval_overall(
            df_config, feature_cols, target_col, group_col, 
            n_splits=min_splits, verbose=False
        )
        results.append({"config": config, "feature_ablated": "None (All Features)", 
                        "Linear_MAPE": stats_all["Linear_MAPE"]})

        # 2. "Baseline" (All Features Disabled)
        print("    - Evaluation (Baseline - All Disabled) ...")
        df_baseline = df_config.copy()
        # Set all features to constant 1.0
        df_baseline[feature_cols] = 1.0
        
        stats_baseline = train_eval_overall(
            df_baseline, feature_cols, target_col, group_col, 
            n_splits=min_splits, verbose=False
        )
        results.append({"config": config, "feature_ablated": "All (Baseline)", 
                        "Linear_MAPE": stats_baseline["Linear_MAPE"]})

        # 3. Individual Ablation (Disable one feature at a time)
        for feature in feature_cols:
            print(f"    - Ablating: {feature}")
            df_ablated = df_config.copy()
            # Disable only this feature
            df_ablated[feature] = 1.0
            
            stats_ablated = train_eval_overall(
                df_ablated, feature_cols, target_col, group_col, 
                n_splits=min_splits, verbose=False
            )
            results.append({"config": config, "feature_ablated": feature, 
                            "Linear_MAPE": stats_ablated["Linear_MAPE"]})

    # Save Results
    df_results = pd.DataFrame(results)
    out_path = outdir / "Linear_Ablation_Study_Performance_Raw.csv"
    df_results.to_csv(out_path, index=False)
    print(f"\n[OK] Feature Ablation Study results saved to: {out_path}")
    print(df_results.head())


# -----------------------------------------------------------------
# Main: Experiment Controller
# -----------------------------------------------------------------
def main():
    # 1. Define Input and Output
    
    # Check Input
    if not SUMMARY_CSV.is_file():
        print(f"[FATAL ERROR] Input file not found: {SUMMARY_CSV}", file=sys.stderr)
        return 1
        
    print(f"--- Loading v3 Dataset: {SUMMARY_CSV} ---")
    df = pd.read_csv(SUMMARY_CSV)

    # 2. Clean Data (Only Keep non-NaNs)
    print("--- Cleaning Data (Checking Raw PE Columns) ---")
    df_clean = clean_df(df, FEATURE_COLS_18PE) 
    
    if df_clean.empty:
        print("[FATAL ERROR] No data remaining after cleaning.", file=sys.stderr)
        return 1
        
    # Note: No feature engineering function called here (Using Raw PEs)
    
    # -------------------------------------------------
    # Experiment A: Run on ALL data
    # -------------------------------------------------
    print("\n--- [Experiment A: Run on (ALL) Resolution Data, using Raw PEs] ---")
    run_full_analysis(df_clean, FEATURE_COLS_18PE, output_suffix="_all_res_raw", outdir=OUTDIR)
    
    # -------------------------------------------------
    # Experiment 1 (Supplementary): 1080p Only (Robust Pixel Check)
    # -------------------------------------------------
    print("\n\n--- [Experiment 1 (Supplementary): Run on (1080p Only) Data, using Raw PEs] ---")
    
    FULLHD_PIXELS = 1920 * 1080
    # Use total pixel count matching to support 1920x1080 and 1080x1920
    df_1080p = df_clean[
        (df_clean['width'] * df_clean['height']) == FULLHD_PIXELS
    ].copy()
    
    print(f"Filtering 1080p Data (Pixels={FULLHD_PIXELS}): {len(df_1080p)} / {len(df_clean)} records")
    
    if df_1080p.empty:
        print("[WARNING] No 1080p data found, skipping Experiment 1.")
    elif df_1080p[GROUP_COL].nunique() < 2: 
         print(f"[WARNING] Not enough independent groups ({df_1080p[GROUP_COL].nunique()} groups) in 1080p data for CV, skipping.")
    else:
        run_full_analysis(df_1080p, FEATURE_COLS_18PE, output_suffix="_1080p_only_raw", outdir=OUTDIR)

    # -------------------------------------------------
    # Experiment 2 (Supplementary): Feature Ablation Study
    # -------------------------------------------------
    # Run ablation on all data
    run_ablation_study(df_clean, FEATURE_COLS_18PE, TARGET_COL, GROUP_COL, OUTDIR)

    print("\n\n--- Completed All Tasks (Raw PE Version) ---")
    return 0

if __name__ == "__main__":
    main()