#!/bin/bash
# ==============================================================================
# CONFIGURATION SECTION
# ==============================================================================

START_TIME_SECONDS=$(date +%s)
echo "脚本开始运行 (采用 '负载-空闲' 差分测量逻辑)..."
echo "开始时间: $(date)"

# 修改：新的输出文件名以反映新的测量方法
RAW_OUTPUT_CSV="core_energy_net_measurements.csv"

SLEEP_TIME=2                 # 每次完整测量（负载+空闲）后的休眠时间
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
# --- 4K Sequences (a1_4k)8 ---
VIDEOS["BoxingPractice_4k"]="a1_4k/BoxingPractice_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"
VIDEOS["Crosswalk_4k"]="a1_4k/Crosswalk_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"
VIDEOS["FoodMarket2_4k"]="a1_4k/FoodMarket2_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"
VIDEOS["Neon1224_4k"]="a1_4k/Neon1224_3840x2160_2997fps.yuv 3840 2160 29.97 $FRAMES"
VIDEOS["NocturneDance_4k"]="a1_4k/NocturneDance_3840x2160p_8bit_60fps.yuv 3840 2160 60 $FRAMES"
VIDEOS["PierSeaSide_4k"]="a1_4k/PierSeaSide_3840x2160_2997fps_8bit_420.yuv 3840 2160 29.97 $FRAMES"
VIDEOS["Tango_4k"]="a1_4k/Tango_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"
VIDEOS["TimeLapse_4k"]="a1_4k/TimeLapse_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 $FRAMES"

# --- 2K / 1080p Sequences (a2_2k)22 ---
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

# --- 720p Sequences (a3_720p) 8---
VIDEOS["ControlledBurn_720p"]="a3_720p/ControlledBurn_1280x720p30_420.yuv 1280 720 30 $FRAMES"
VIDEOS["DrivingPOV_720p"]="a3_720p/DrivingPOV_1280x720p_5994_8bit_420.yuv 1280 720 60000/1001 $FRAMES"
VIDEOS["Johnny_720p"]="a3_720p/Johnny_1280x720_60.yuv 1280 720 60 $FRAMES"
VIDEOS["KristenAndSara_720p"]="a3_720p/KristenAndSara_1280x720_60.yuv 1280 720 60 $FRAMES"
VIDEOS["RollerCoaster_720p"]="a3_720p/RollerCoaster_1280x720p_5994_8bit_420.yuv 1280 720 60000/1001 $FRAMES"
VIDEOS["Vidyo3_720p"]="a3_720p/Vidyo3_1280x720p_60fps.yuv 1280 720 60 $FRAMES"
VIDEOS["Vidyo4_720p"]="a3_720p/Vidyo4_1280x720p_60fps.yuv 1280 720 60 $FRAMES"
VIDEOS["WestWindEasy_720p"]="a3_720p/WestWindEasy_1280x720p30_420.yuv 1280 720 30 $FRAMES"

# --- 360p Sequences (a4_360p) 6---
VIDEOS["BlueSky_360p"]="a4_360p/BlueSky_360p25.yuv 640 360 25 $FRAMES"
VIDEOS["RedKayak_360p"]="a4_360p/RedKayak_360_2997.yuv 640 360 29.97 $FRAMES"
VIDEOS["SnowMountain_360p"]="a4_360p/SnowMountain_640x360_2997.yuv 640 360 29.97 $FRAMES"
VIDEOS["SpeedBag_360p"]="a4_360p/SpeedBag_640x360_2997.yuv 640 360 29.97 $FRAMES"
VIDEOS["Stockholm_360p"]="a4_360p/Stockholm_640x360_5994.yuv 640 360 60000/1001 $FRAMES"
VIDEOS["TouchdownPass_360p"]="a4_360p/TouchdownPass_640x360_2997.yuv 640 360 29.97 $FRAMES"

# --- 270p Sequences (a5_270p) 4---
VIDEOS["FourPeople_270p"]="a5_270p/FourPeople_480x270_60.yuv 480 270 60 $FRAMES"
VIDEOS["ParkJoy_270p"]="a5_270p/ParkJoy_480x270_50.yuv 480 270 50 $FRAMES"
VIDEOS["SparksElevator_270p"]="a5_270p/SparksElevator_480x270p_5994_8bit.yuv 480 270 60000/1001 $FRAMES"
VIDEOS["Vertical_Bayshore_270p"]="a5_270p/Vertical_Bayshore_270x480_2997.yuv 270 480 29.97 $FRAMES"

echo "VideoName,QP,Preset,MeasureNo,Delta_Load_uJ,EncodingTime_s,Delta_Idle_uJ,Net_Delta_uJ" > "$RAW_OUTPUT_CSV"

echo "开始收集能耗数据..."

for VIDEO_KEY in "${!VIDEOS[@]}"; do
  IFS=' ' read -r YUV_REL_PATH WIDTH HEIGHT FPS FRAMES_TO_ENCODE <<< "${VIDEOS[$VIDEO_KEY]}"
  YUV_PATH="$VIDEO_SOURCE_DIR/$YUV_REL_PATH"

  [ ! -f "$YUV_PATH" ] && echo "警告: 未找到 '$YUV_PATH'，跳过 $VIDEO_KEY" && continue

  echo -e "\n处理: $VIDEO_KEY (${WIDTH}x${HEIGHT} @ $FPS fps)"

  for QP in "${QPS[@]}"; do
    for PRESET in "${PRESETS[@]}"; do

      measurements=() # 这个数组现在将存储净能耗 (Net_Delta)

      for (( m=1; m<=MAX_MEASURE; m++ )); do
        # --- 步骤 1: 负载测量 (Load Measurement) ---
        TIME_START=$(date +%s.%N)
        E_BEFORE_LOAD=$(cat "$RAPL_CORE_FILE")
        

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
               
        E_AFTER_LOAD=$(cat "$RAPL_CORE_FILE")
        TIME_END=$(date +%s.%N)

        DELTA_LOAD=$(( E_AFTER_LOAD - E_BEFORE_LOAD ))
        ENCODING_TIME=$(echo "$TIME_END - $TIME_START" | bc)

        # --- 步骤 2: 空闲测量 (Idle Measurement) ---
        # 让系统有极短的喘息时间，避免测量误差
        sleep 0.2 
        E_BEFORE_IDLE=$(cat "$RAPL_CORE_FILE")
        sleep "$ENCODING_TIME" # 等待与编码完全相同的时间
        E_AFTER_IDLE=$(cat "$RAPL_CORE_FILE")

        DELTA_IDLE=$(( E_AFTER_IDLE - E_BEFORE_IDLE ))
        
        # --- 步骤 3: 计算净能耗 (Net Energy) ---
        NET_DELTA=$(( DELTA_LOAD - DELTA_IDLE ))
        
        # 纠正潜在的负值（如果由于系统噪音，空闲测量值偶然高于负载测量值）
        (( NET_DELTA < 0 )) && NET_DELTA=0
        
        measurements+=("$NET_DELTA")

        # 将所有相关数据写入 CSV
        echo "$VIDEO_KEY,$QP,$PRESET,$m,$DELTA_LOAD,$ENCODING_TIME,$DELTA_IDLE,$NET_DELTA" >> "$RAW_OUTPUT_CSV"
        sleep $SLEEP_TIME

        # --- 置信区间判断逻辑 (基于净能耗) ---
        N=${#measurements[@]}
        if (( N >= MIN_MEASURE )); then
          # 传递给 python 的是净能耗的测量值
          MEAS_LINE=$(IFS=','; echo "${measurements[*]}")
          mapfile -t stats < <(python3 <<EOF
import statistics, math
from scipy.stats import t
raw = "$MEAS_LINE"
parts = raw.split(',') if raw else []
data = [float(p) for p in parts]
if not data or statistics.mean(data) == 0:
    print("0")
    print("inf")
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
    threshold = ($INTERVAL_PART/2) * mean
    print(f"{conf:.6f}")
    print(f"{threshold:.6f}")
EOF
)

          CONF="${stats[0]}"
          THRESHOLD="${stats[1]}"
          echo "[$VIDEO_KEY, QP=$QP, Preset=$PRESET] 测量次数: $N | 置信区间余量: $CONF | 阈值: $THRESHOLD"

          if (( $(echo "$CONF < $THRESHOLD" | bc -l) )); then
            avg=$(python3 <<EOF
import statistics
raw = "$MEAS_LINE"
parts = raw.split(',') if raw else []
data = [float(p) for p in parts]
print(f"{statistics.mean(data):.6f}" if data else "0")
EOF
)
            echo "最终平均 **净** 能耗: $avg uJ (满足置信度要求)"
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
    # 过滤离群值
    low, high = 0.75*med, 1.25*med
    out = [d for d in data if low <= d <= high] # 使用闭区间可能更稳健
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