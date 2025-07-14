#!/bin/bash

# ---------- 参数定义 ----------
N_REPEATS=10
OUTPUT_CSV="energy_measurements.csv"

QPS=(22 27 32 37)
PRESETS=(ultrafast superfast veryfast faster fast medium slow slower veryslow placebo)

# 视频配置：名称=路径 分辨率 宽 高 帧率 帧数
declare -A VIDEOS
VIDEOS["ControlledBurn_720p"]="/home/or16ixuv/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv 1280 720 30 130"
VIDEOS["Aerial3200_2k"]="/home/or16ixuv/thesis_videos/aom_8bit/a2_2k/Aerial3200_1920x1080_5994_8bit_420.yuv 1920 1080 59.94 130"
VIDEOS["BoxingPractice_4k"]="/home/or16ixuv/thesis_videos/aom_8bit/a1_4k/BoxingPractice_3840x2160_5994fps_8bit_420.yuv 3840 2160 59.94 130"
VIDEOS["SnowMountain_360p"]="/home/or16ixuv/thesis_videos/aom_8bit/a4_360p/SnowMountain_640x360_2997.yuv 640 360 29.97 130"
VIDEOS["SparksElevator_270p"]="/home/or16ixuv/thesis_videos/aom_8bit/a5_270p/SparksElevator_480x270p_5994_8bit.yuv 480 270 59.94 130"

mkdir -p encoded_outputs logs

# 初始化 CSV 表头
echo "Video,QP,Preset,Repeat,Energy_Core_J,Energy_Uncore_J,Energy_DRAM_J" > "$OUTPUT_CSV"

# ---------- 主循环 ----------
for VIDEO_NAME in "${!VIDEOS[@]}"; do
  IFS=' ' read -r YUV_PATH WIDTH HEIGHT FPS FRAMES <<< "${VIDEOS[$VIDEO_NAME]}"

  for QP in "${QPS[@]}"; do
    for PRESET in "${PRESETS[@]}"; do
      for ((i = 1; i <= N_REPEATS; i++)); do
        echo -e "\n[INFO] $VIDEO_NAME | QP=$QP | Preset=$PRESET | Iteration=$i"

        # --- RAPL 读取函数 ---
        read_energy() {
          local domain=$1
          cat "/sys/class/powercap/intel-rapl:0:$domain/energy_uj"
        }

        E_CORE_BEFORE=$(read_energy 0)
        E_UNCORE_BEFORE=$(read_energy 1)
        E_DRAM_BEFORE=$(read_energy 2)

        OUT_BIN="encoded_outputs/${VIDEO_NAME}_qp${QP}_${PRESET}_run${i}.265"
        LOG_TXT="logs/${VIDEO_NAME}_qp${QP}_${PRESET}_run${i}.log"

        # --- x265 编码 ---
        x265 \
          --input "$YUV_PATH" \
          --input-res ${WIDTH}x${HEIGHT} \
          --fps $FPS \
          --frames $FRAMES \
          --intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 \
          --qp $QP --no-opt-qp-pps --ipratio 1.0 \
          --preset $PRESET \
          --tune psnr \
          --psnr \
          --recon /dev/null \
          -o "$OUT_BIN" 2> "$LOG_TXT"

        # --- RAPL 读取后 ---
        E_CORE_AFTER=$(read_energy 0)
        E_UNCORE_AFTER=$(read_energy 1)
        E_DRAM_AFTER=$(read_energy 2)

        # --- 计算能耗 ---
        CORE_J=$(awk "BEGIN {print ($E_CORE_AFTER - $E_CORE_BEFORE)/1000000}")
        UNCORE_J=$(awk "BEGIN {print ($E_UNCORE_AFTER - $E_UNCORE_BEFORE)/1000000}")
        DRAM_J=$(awk "BEGIN {print ($E_DRAM_AFTER - $E_DRAM_BEFORE)/1000000}")

        # --- 记录结果 ---
        echo "$VIDEO_NAME,$QP,$PRESET,$i,$CORE_J,$UNCORE_J,$DRAM_J" >> "$OUTPUT_CSV"
      done
    done
  done
done
