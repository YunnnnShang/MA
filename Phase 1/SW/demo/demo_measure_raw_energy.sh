#!/bin/bash
# 1. CONFIGURATION SECTION
RAW_OUTPUT_CSV="raw_core_energy_measurements.csv"
MAX_REPEATS=15 

QPS=(22 27 32 37)
PRESETS=(ultrafast superfast veryfast faster fast medium slow slower veryslow placebo)

declare -A VIDEOS
VIDEOS["ControlledBurn_720p"]="/home/or16ixuv/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv 1280 720 30 130"
VIDEOS["Aerial_2k"]="/home/or16ixuv/thesis_videos/aom_8bit/a2_2k/Aerial3200_1920x1080_5994_8bit_420.yuv 1920 1080 60000/1001 130"
VIDEOS["BoxingPractice_4k"]="/home/or16ixuv/thesis_videos/aom_8bit/a1_4k/BoxingPractice_3840x2160_5994fps_8bit_420.yuv 3840 2160 60000/1001 130"
VIDEOS["SnowMountain_360p"]="/home/or16ixuv/thesis_videos/aom_8bit/a4_360p/SnowMountain_640x360_2997.yuv 640 360 29.97 130"
VIDEOS["SparksElevator_270p"]="/home/or16ixuv/thesis_videos/aom_8bit/a5_270p/SparksElevator_480x270p_5994_8bit.yuv 480 270 60000/1001 130"

RAPL_CORE_FILE="/sys/class/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:0/energy_uj"
# Initialize a new CSV header
echo "VideoName,QP,Preset,Repeat,RAPL_Core_Before_uJ,RAPL_Core_After_uJ" > "$RAW_OUTPUT_CSV"

echo "Start collecting raw data on Core energy consumption..."

# --- Loop ---
for VIDEO_NAME in "${!VIDEOS[@]}"; do
  IFS=' ' read -r YUV_PATH WIDTH HEIGHT FPS FRAMES <<< "${VIDEOS[$VIDEO_NAME]}"

  for QP in "${QPS[@]}"; do
    for PRESET in "${PRESETS[@]}"; do
      for ((i = 1; i <= MAX_REPEATS; i++)); do
        
        echo -ne "Processing: $VIDEO_NAME | QP=$QP | Preset=$PRESET |  $i th measurement...\r"

        E_BEFORE=$(cat "$RAPL_CORE_FILE")

        x265 \
          --input "$YUV_PATH" \
          --input-res "${WIDTH}x${HEIGHT}" \
          --fps "$FPS" \
          --frames "$FRAMES" \
          --preset "$PRESET" \
          --intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 \
          --qp $QP --no-opt-qp-pps --ipratio 1.0 \
          --log-level none \
          -o /dev/null 2>/dev/null

        E_AFTER=$(cat "$RAPL_CORE_FILE")

        # Records the raw readings of the Core domain
        echo "$VIDEO_NAME,$QP,$PRESET,$i,$E_BEFORE,$E_AFTER" >> "$RAW_OUTPUT_CSV"
      done
    done
  done
done

echo -e "Results saved: $RAW_OUTPUT_CSV"
