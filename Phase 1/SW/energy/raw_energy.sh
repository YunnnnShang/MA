#!/bin/bash
# ==============================================================================
# CONFIGURATION SECTION
# ==============================================================================

START_TIME_SECONDS=$(date +%s)
echo "脚本开始运行..."
echo "开始时间: $(date)"

RAW_OUTPUT_CSV="core_energy_ci_measurements2.csv"

SLEEP_TIME=2                 # 每次测量后的休眠时间（秒）
CONF_PROB=0.99               # 置信度
INTERVAL_PART=0.02           # 置信区间相对均值阈值
MAX_MEASURE=15               # 最大测量次数
MIN_MEASURE=5                # 最少测量次数触发置信度判断
OUTLIER_THRESHOLD_MEAS=9     # 超过此次数时进行离群值剔除

# 基础目录与可执行文件
VIDEO_SOURCE_DIR="$HOME/thesis_videos/aom_8bit"
X265_EXECUTABLE="$HOME/x265_git/source/x265"
RAPL_CORE_FILE="/sys/class/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:0/energy_uj"
PRESETS=(ultrafast superfast veryfast faster fast medium)
QPS=(22 27 32 37)
FRAMES=130

declare -A VIDEOS

# --- 4K Sequences (a1_4k) ---
VIDEOS["BoxingPractice_4k"]="a1_4k/BoxingPractice_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"
VIDEOS["Crosswalk_4k"]="a1_4k/Crosswalk_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"
VIDEOS["FoodMarket2_4k"]="a1_4k/FoodMarket2_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"
VIDEOS["Neon1224_4k"]="a1_4k/Neon1224_3840x2160_2997fps.yuv 3840 2160 29.97 $FRAMES"
VIDEOS["NocturneDance_4k"]="a1_4k/NocturneDance_3840x2160p_8bit_60fps.yuv 3840 2160 60 $FRAMES"
VIDEOS["PierSeaSide_4k"]="a1_4k/PierSeaSide_3840x2160_2997fps_8bit_420.yuv 3840 2160 29.97 $FRAMES"
VIDEOS["Tango_4k"]="a1_4k/Tango_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"
VIDEOS["TimeLapse_4k"]="a1_4k/TimeLapse_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"

# --- 2K / 1080p Sequences (a2_2k) ---
VIDEOS["Boat_2k"]="a2_2k/Boat_1920x1080_5994_8bit_420.yuv 1920 1080 60000/1001 $FRAMES"
VIDEOS["FoodMarket_2k"]="a2_2k/FoodMarket_1920x1080_5994_8bit_420.yuv 1920 1080 60000/1001 $FRAMES"
VIDEOS["MeridianTalk_sdr_2k"]="a2_2k/MeridianTalk_sdr_1920x1080p_5994_8bit.yuv 1920 1080 60000/1001 $FRAMES"
VIDEOS["RushFieldCuts_2k"]="a2_2k/RushFieldCuts_1920x1080_2997.yuv 1920 1080 29.97 $FRAMES"
VIDEOS["ToddlerFountain_2k"]="a2_2k/ToddlerFountain_1920x1080_2997fps_8bit_420.yuv 1920 1080 29.97 $FRAMES"
VIDEOS["TreesAndGrass_2k"]="a2_2k/TreesAndGrass_1920_1080_30fps_8bit.yuv 1920 1080 30 $FRAMES"
VIDEOS["Aerial3200_2k"]="a2_2k/Aerial3200_1920x1080_5994_8bit_420.yuv 1920 1080 60000/1001 $FRAMES"
VIDEOS["CrowdRun_1080p50"]="a2_2k/CrowdRun_1920x1080p50.yuv 1920 1080 50 $FRAMES"
VIDEOS["DinnerSceneCropped_2k"]="a2_2k/DinnerSceneCropped_1920x1080_2997fps_8bit_420.yuv 1920 1080 29.97 $FRAMES"
VIDEOS["Motorcycle_2k"]="a2_2k/Motorcycle_1920x1080_30fps_8bit.yuv 1920 1080 30 $FRAMES"
VIDEOS["MountainBike_2k"]="a2_2k/MountainBike_1920x1080_30fps_8bit.yuv 1920 1080 30 $FRAMES"
VIDEOS["OldTownCross_1080p50"]="a2_2k/OldTownCross_1920x1080p50.yuv 1920 1080 50 $FRAMES"
VIDEOS["PedestrianArea_1080p25"]="a2_2k/PedestrianArea_1920x1080p25.yuv 1920 1080 25 $FRAMES"
VIDEOS["RitualDance_2k"]="a2_2k/RitualDance_1920x1080_5994_8bit_420.yuv 1920 1080 60000/1001 $FRAMES"
VIDEOS["Riverbed_1080p25"]="a2_2k/Riverbed_1920x1080p25.yuv 1920 1080 25 $FRAMES"
VIDEOS["Skater227_2k"]="a2_2k/Skater227_1920x1080_30fps.yuv 1920 1080 30 $FRAMES"
VIDEOS["TunnelFlag_2k"]="a2_2k/TunnelFlag_1920x1080_5994_8bit_420.yuv 1920 1080 60000/1001 $FRAMES"
VIDEOS["Vertical_bees_2k"]="a2_2k/Vertical_bees_1080x1920_2997.yuv 1080 1920 29.97 $FRAMES"
VIDEOS["Vertical_Carnaby_2k"]="a2_2k/Vertical_Carnaby_1080x1920_5994.yuv 1080 1920 60000/1001 $FRAMES"
VIDEOS["WalkingInStreet_2k"]="a2_2k/WalkingInStreet_1920x1080_30fps.yuv 1920 1080 30 $FRAMES"
VIDEOS["WorldCup_2k"]="a2_2k/WorldCup_1920x1080_30p.yuv 1920 1080 30 $FRAMES"
VIDEOS["WorldCup_far_2k"]="a2_2k/WorldCup_far_1920x1080_30p.yuv 1920 1080 30 $FRAMES"

# --- 720p Sequences (a3_720p) ---
VIDEOS["ControlledBurn_720p"]="a3_720p/ControlledBurn_1280x720p30_420.yuv 1280 720 30 $FRAMES"
VIDEOS["DrivingPOV_720p"]="a3_720p/DrivingPOV_1280x720p_5994_8bit_420.yuv 1280 720 60000/1001 $FRAMES"
VIDEOS["Johnny_720p"]="a3_720p/Johnny_1280x720_60.yuv 1280 720 60 $FRAMES"
VIDEOS["KristenAndSara_720p"]="a3_720p/KristenAndSara_1280x720_60.yuv 1280 720 60 $FRAMES"
VIDEOS["RollerCoaster_720p"]="a3_720p/RollerCoaster_1280x720p_5994_8bit_420.yuv 1280 720 60000/1001 $FRAMES"
VIDEOS["Vidyo3_720p"]="a3_720p/Vidyo3_1280x720p_60fps.yuv 1280 720 60 $FRAMES"
VIDEOS["Vidyo4_720p"]="a3_720p/Vidyo4_1280x720p_60fps.yuv 1280 720 60 $FRAMES"
VIDEOS["WestWindEasy_720p"]="a3_720p/WestWindEasy_1280x720p30_420.yuv 1280 720 30 $FRAMES"

# --- 360p Sequences (a4_360p) ---
VIDEOS["BlueSky_360p"]="a4_360p/BlueSky_360p25.yuv 640 360 25 $FRAMES"
VIDEOS["RedKayak_360p"]="a4_360p/RedKayak_360_2997.yuv 640 360 29.97 $FRAMES"
VIDEOS["SnowMountain_360p"]="a4_360p/SnowMountain_640x360_2997.yuv 640 360 29.97 $FRAMES"
VIDEOS["SpeedBag_360p"]="a4_360p/SpeedBag_640x360_2997.yuv 640 360 29.97 $FRAMES"
VIDEOS["Stockholm_360p"]="a4_360p/Stockholm_640x360_5994.yuv 640 360 60000/1001 $FRAMES"
VIDEOS["TouchdownPass_360p"]="a4_360p/TouchdownPass_640x360_2997.yuv 640 360 29.97 $FRAMES"

# --- 270p Sequences (a5_270p) ---
VIDEOS["FourPeople_270p"]="a5_270p/FourPeople_480x270_60.yuv 480 270 60 $FRAMES"
VIDEOS["ParkJoy_270p"]="a5_270p/ParkJoy_480x270_50.yuv 480 270 50 $FRAMES"
VIDEOS["SparksElevator_270p"]="a5_270p/SparksElevator_480x270p_5994_8bit.yuv 480 270 60000/1001 $FRAMES"
VIDEOS["Vertical_Bayshore_270p"]="a5_270p/Vertical_Bayshore_270x480_2997.yuv 270 480 29.97 $FRAMES"
# 初始化 CSV 文件头
echo "VideoName,QP,Preset,MeasureNo,E_before_uJ,E_after_uJ,Delta_uJ" > "$RAW_OUTPUT_CSV"

echo "开始收集能耗数据..."

for VIDEO_KEY in "${!VIDEOS[@]}"; do
  IFS=' ' read -r YUV_REL_PATH WIDTH HEIGHT FPS FRAMES_TO_ENCODE <<< "${VIDEOS[$VIDEO_KEY]}"
  YUV_PATH="$VIDEO_SOURCE_DIR/$YUV_REL_PATH"

  [ ! -f "$YUV_PATH" ] && echo "警告: 未找到 '$YUV_PATH'，跳过 $VIDEO_KEY" && continue

  echo -e "\n处理: $VIDEO_KEY (${WIDTH}x${HEIGHT} @ $FPS fps)"

  for QP in "${QPS[@]}"; do
    for PRESET in "${PRESETS[@]}"; do

      measurements=()

      for (( m=1; m<=MAX_MEASURE; m++ )); do
        E_BEFORE=$(cat "$RAPL_CORE_FILE")
        "$X265_EXECUTABLE" \
          --input "$YUV_PATH" \
          --input-res "${WIDTH}x${HEIGHT}" \
          --fps "$FPS" \
          --frames "$FRAMES_TO_ENCODE" \
          --preset "$PRESET" \
          --intra --keyint 1 \
          --qp "$QP" \
          --log-level none \
          -o /dev/null 2>/dev/null
        E_AFTER=$(cat "$RAPL_CORE_FILE")
        DELTA=$(( E_AFTER - E_BEFORE ))
        (( DELTA < 0 )) && DELTA=0
        measurements+=("$DELTA")

        echo "$VIDEO_KEY,$QP,$PRESET,$m,$E_BEFORE,$E_AFTER,$DELTA" >> "$RAW_OUTPUT_CSV"
        sleep $SLEEP_TIME

        N=${#measurements[@]}
        if (( N >= MIN_MEASURE )); then
          MEAS_LINE=$(IFS=','; echo "${measurements[*]}")
          mapfile -t stats < <(python3 <<EOF
import statistics, math
from scipy.stats import t
raw = "$MEAS_LINE"
parts = raw.split(',') if raw else []
data = [float(p) for p in parts]
if not data:
    print("0")
    print("0")
else:
    conf_prob = $CONF_PROB
    alpha = 1 - conf_prob
    n = len(data)
    mean = statistics.mean(data)
    if n < 2:
        conf = float('inf')
    else:
        std = statistics.stdev(data)
        conf = 0.0 if std == 0 else std/math.sqrt(n)*t.ppf(1-alpha/2, n-1)
    threshold = $INTERVAL_PART * mean
    print(f"{conf:.6f}")
    print(f"{threshold:.6f}")
EOF
)

          CONF="${stats[0]}"
          THRESHOLD="${stats[1]}"
          echo "测量次数: $N | CI margin: $CONF | 阈值: $THRESHOLD"

          if (( $(echo "$CONF < $THRESHOLD" | bc -l) )); then
            avg=$(python3 <<EOF
import statistics
raw = "$MEAS_LINE"
parts = raw.split(',') if raw else []
data = [float(p) for p in parts]
print(f"{statistics.mean(data):.6f}" if data else "0")
EOF
)
            echo "最终平均能耗: $avg uJ (满足置信度要求)"
            break
          fi

          if (( N > OUTLIER_THRESHOLD_MEAS )); then
            filtered=$(python3 <<EOF
import statistics
raw = "$MEAS_LINE"
data = [float(p) for p in raw.split(',')]
if len(data) < 2:
    out = data
else:
    med = statistics.median(data)
    low, high = 0.75*med, 1.25*med
    out = [d for d in data if low < d < high]
print(','.join(str(int(d)) for d in out))
EOF
)
            IFS=',' read -ra measurements <<< "$filtered"
          fi
        fi
      done
    done
  done
done

END_TIME_SECONDS=$(date +%s)
DURATION=$((END_TIME_SECONDS - START_TIME_SECONDS))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))
SECONDS=$((DURATION % 60))

echo "=============================================================================="
echo "脚本执行完毕。"
echo "结束时间: $(date)"
echo "总耗时: ${HOURS} 小时 ${MINUTES} 分钟 ${SECONDS} 秒"
