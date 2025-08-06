#!/bin/bash
# ==============================================================================
# CONFIGURATION SECTION
# ==============================================================================

RAW_OUTPUT_CSV="core_energy_ci_measurements.csv"

# 初始参数，可按需调整
SLEEP_TIME=5                 # 每次测量后的休眠时间（秒）
CONF_PROB=0.99               # 置信度
INTERVAL_PART=0.02           # 置信区间相对均值阈值
MAX_MEASURE=50               # 最大测量次数
MIN_MEASURE=5                # 最少测量次数触发置信度判断
OUTLIER_THRESHOLD_MEAS=9     # 超过此次数时进行离群值剔除

# 基础目录与可执行文件
VIDEO_SOURCE_DIR="$HOME/thesis_videos/aom_8bit"
X265_EXECUTABLE="$HOME/x265_git/source/x265"
RAPL_CORE_FILE="/sys/class/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:0/energy_uj"

# 保留 medium 及以上更快的预设
PRESETS=(ultrafast superfast veryfast faster fast medium)

# QP 不变
QPS=(22 27 32 37)

# 测试帧数
FRAMES=130

# 视频列表省略，保持原脚本中 declare -A VIDEOS[...] 定义

# 初始化 CSV 文件头
echo "VideoName,QP,Preset,MeasureNo,E_before_uJ,E_after_uJ,Delta_uJ" > "$RAW_OUTPUT_CSV"

echo "开始收集能耗数据（含置信度判断）..."

# ------------------------------------------------------------------------------
# 主循环：遍历所有视频、QP、Preset
# ------------------------------------------------------------------------------
for VIDEO_KEY in "${!VIDEOS[@]}"; do
  IFS=' ' read -r YUV_REL_PATH WIDTH HEIGHT FPS FRAMES_TO_ENCODE <<< "${VIDEOS[$VIDEO_KEY]}"
  YUV_PATH="$VIDEO_SOURCE_DIR/$YUV_REL_PATH"

  if [ ! -f "$YUV_PATH" ]; then
      echo "警告: 未找到 '$YUV_PATH'，跳过 $VIDEO_KEY"
      continue
  fi

  echo -e "\n处理: $VIDEO_KEY (${WIDTH}x${HEIGHT} @ $FPS fps)"

  for QP in "${QPS[@]}"; do
    for PRESET in "${PRESETS[@]}"; do

      # 每组参数测量数组重置
      measurements=()

      # 测量循环
      for (( m=1; m<=MAX_MEASURE; m++ )); do
        # 1. 读取测前电量
        E_BEFORE=$(cat "$RAPL_CORE_FILE")

        # 2. 编码执行
        "$X265_EXECUTABLE" \
          --input "$YUV_PATH" \
          --input-res "${WIDTH}x${HEIGHT}" \
          --fps "$FPS" \
          --frames "$FRAMES_TO_ENCODE" \
          --preset "$PRESET" \
          --intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 \
          --qp "$QP" --no-opt-qp-pps --ipratio 1.0 \
          --log-level none \
          -o /dev/null 2>/dev/null

        # 3. 读取测后电量，并计算差值
        E_AFTER=$(cat "$RAPL_CORE_FILE")
        DELTA=$(( E_AFTER - E_BEFORE ))
        measurements+=("$DELTA")

        # 4. 写入 CSV
        echo "$VIDEO_KEY,$QP,$PRESET,$m,$E_BEFORE,$E_AFTER,$DELTA" \
          >> "$RAW_OUTPUT_CSV"

        # 5. 睡眠，减少长时间连续测量带来的额外功耗
        sleep $SLEEP_TIME

        # 6. 置信度判断（至少测量 MIN_MEASURE 次后触发）
        N=${#measurements[@]}
        if (( N >= MIN_MEASURE )); then

          # 使用 Python 计算当前置信区间和阈值
          read CONF THRESHOLD <<< "$(python3 - <<EOF
import sys, statistics, math
from scipy.stats import t
data = list(map(float, sys.argv[1].split(',')))
conf_prob = $CONF_PROB
alpha = 1 - conf_prob
n = len(data)
mean = statistics.mean(data)
std = statistics.stdev(data)
conf = std/math.sqrt(n) * t.ppf(1-alpha/2, n-1)
threshold = $INTERVAL_PART * mean
print(conf, threshold)
EOF
)" <<< "${measurements[*]// /,}"

          echo "  测量次数: $N | CI margin: $CONF | 阈值: $THRESHOLD"

          # 6.1 如果满足置信度要求，则结束本组测量
          if (( $(echo "$CONF < $THRESHOLD" | bc -l) )); then
            avg=$(python3 - <<EOF
import sys, statistics
data = list(map(float, sys.argv[1].split(',')))
print(statistics.mean(data))
EOF
)" <<< "${measurements[*]// /,}"
            echo "  最终平均能耗: $avg uJ (满足置信度要求)"
            break
          fi

          # 6.2 如果置信度仍不够、且测量超过 OUTLIER_THRESHOLD_MEAS 次，则剔除离群值
          if (( N > OUTLIER_THRESHOLD_MEAS )); then
            filtered=$(python3 - <<EOF
import sys, statistics
data = list(map(float, sys.argv[1].split(',')))
med = statistics.median(data)
low, high = 0.75*med, 1.25*med
filtered = [d for d in data if low < d < high]
print(','.join(map(str, filtered)))
EOF
)" <<< "${measurements[*]// /,}"
            IFS=',' read -ra measurements <<< "$filtered"
            echo "  已剔除离群值，剩余测量次数: ${#measurements[@]}"
          fi

        fi
      done  # End measurements loop

    done  # End presets
  done    # End QPs
done      # End videos

echo -e "\n所有测量完成，结果保存在: $RAW_OUTPUT_CSV"
