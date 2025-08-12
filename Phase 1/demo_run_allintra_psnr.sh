#!/bin/bash

# Basic parameter settings
INPUT_YUV="$HOME/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv"
WIDTH=1280
HEIGHT=720
FRAMES=130
FPS=30

QPS=(22 27 32 37)
PRESETS=(ultrafast superfast veryfast faster fast medium slow slower veryslow placebo)

mkdir -p encoded_outputs
mkdir -p psnr_logs

for QP in "${QPS[@]}"; do
  for PRESET in "${PRESETS[@]}"; do
    OUT_NAME="qp${QP}_${PRESET}"
    OUT_BIN="encoded_outputs/${OUT_NAME}.265"
    LOG_TXT="psnr_logs/${OUT_NAME}.log"
    LOG_CSV="psnr_logs/${OUT_NAME}_frame.csv"

    echo -e "\n[INFO] Encoding QP=${QP} Preset=${PRESET}"

    # Encoding execution
    x265 \
      --input "$INPUT_YUV" \
      --input-res ${WIDTH}x${HEIGHT} \
      --fps ${FPS} \
      --frames ${FRAMES} \
      --intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 \
      --qp ${QP} --no-opt-qp-pps --ipratio 1.0 \
      --preset ${PRESET} \
      --tune psnr \
      --psnr \
      --recon /dev/null \
      --csv "${LOG_CSV}" --csv-log-level 2 \
      -o "${OUT_BIN}" 2> "${LOG_TXT}"

    # Average QP verification
    ACTUAL_QP=$(grep "frame I:" "${LOG_TXT}" | grep -o "Avg QP:[0-9.]*" | cut -d ':' -f2 | cut -d '.' -f1)

    if [ "$ACTUAL_QP" != "$QP" ]; then
      echo -e "\033[1;31m[WARNING] Avg QP MISMATCH: QP=${QP} but got Avg QP=${ACTUAL_QP} (Preset: ${PRESET})\033[0m"
    else
      echo -e "\033[1;32m[OK] Avg QP=${ACTUAL_QP} matches QP=${QP}\033[0m"
    fi
  done
done
