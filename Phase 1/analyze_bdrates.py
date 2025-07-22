# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import bjontegaard as bd

# ==============================================================================
# 1. 配置区域 (CONFIGURATION SECTION)
# ==============================================================================
# 输入文件: 由 generate_rd_data.py 生成的比特率和PSNR数据文件
DATA_CSV_PATH = Path.home() / "thesis_results_ci/bitrate_psnr_results.csv"

# 输出的BD-metrics结果文件
RESULTS_CSV_PATH = Path.home() / "thesis_results_ci/bd_metrics_results.csv"

# 定义用于比较的基准预设 (Reference)
REFERENCE_PRESET = "medium"

# 定义需要进行比较的测试预设 (Test)
PRESETS_TO_TEST = ["ultrafast", "superfast", "veryfast", "faster", "fast", "slow", "slower", "veryslow", "placebo"]
# ==============================================================================

# ... [calculate_bd_metrics_for_video 函数与之前版本相同，此处省略以保持简洁] ...
def calculate_bd_metrics_for_video(video_df, ref_preset, test_presets):
    video_results = []
    ref_data = video_df[video_df['preset'] == ref_preset].sort_values(by='qp')
    if len(ref_data) < 4:
        tqdm.write(f"警告: 视频 '{video_df['video_name'].iloc[0]}' 的基准预设 '{ref_preset}' 数据点不足 ({len(ref_data)}个)，跳过。")
        return []
    ref_rates, ref_psnrs = ref_data['bitrate_kbps'].values, ref_data['psnr_y'].values
    for test_preset in test_presets:
        if test_preset == ref_preset: continue
        test_data = video_df[video_df['preset'] == test_preset].sort_values(by='qp')
        if len(test_data) < 4:
            tqdm.write(f"警告: 视频 '{video_df['video_name'].iloc[0]}' 的测试预设 '{test_preset}' 数据点不足 ({len(test_data)}个)，跳过。")
            continue
        test_rates, test_psnrs = test_data['bitrate_kbps'].values, test_data['psnr_y'].values
        try:
            bd_rate_value = bd.bd_rate(ref_rates, ref_psnrs, test_rates, test_psnrs, method='akima')
            bd_psnr_value = bd.bd_psnr(ref_rates, ref_psnrs, test_rates, test_psnrs, method='akima')
            video_results.append({
                "video_name": video_df['video_name'].iloc[0],
                "comparison": f"{test_preset}_vs_{ref_preset}",
                "bd_rate_change_perc": bd_rate_value,
                "bd_psnr_change_db": bd_psnr_value
            })
        except Exception as e:
            tqdm.write(f"错误: 在计算 '{test_preset}' vs '{ref_preset}' 时出错: {e}")
    return video_results

if __name__ == "__main__":
    if not DATA_CSV_PATH.exists():
        print(f"错误: 数据文件未找到: {DATA_CSV_PATH}。请先运行 'generate_rd_data.py'。")
        exit()

    df = pd.read_csv(DATA_CSV_PATH)
    all_bd_results = []
    video_names = df['video_name'].unique()

    for video_name in tqdm(video_names, desc="计算BD-Metrics"):
        video_df = df[df['video_name'] == video_name].copy()
        video_df['bitrate_kbps'] = pd.to_numeric(video_df['bitrate_kbps'], errors='coerce')
        video_df['psnr_y'] = pd.to_numeric(video_df['psnr_y'], errors='coerce')
        video_df.dropna(subset=['bitrate_kbps', 'psnr_y'], inplace=True)
        results_for_video = calculate_bd_metrics_for_video(video_df, REFERENCE_PRESET, PRESETS_TO_TEST)
        all_bd_results.extend(results_for_video)

    if all_bd_results:
        results_df = pd.DataFrame(all_bd_results)
        RESULTS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(RESULTS_CSV_PATH, index=False, float_format='%.4f')
        print(f"\nBD-metrics 计算完成！结果已保存至: {RESULTS_CSV_PATH}")
        print("\n--- BD-rate 结果概览 (码率变化百分比) ---")
        print(results_df.pivot_table(index='video_name', columns='comparison', values='bd_rate_change_perc').to_markdown(floatfmt=".2f"))
    else:
        print("\n计算未产生任何结果。请检查输入数据文件。")
