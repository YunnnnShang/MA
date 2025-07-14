#!/bin/bash

# === Pilot Energy Measurement Script (x265 All-Intra) ===

INPUT_YUV="$HOME/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv"
WIDTH=1280
HEIGHT=720
FRAMES=130
FPS=30

QPS=(22 32 37)
PRESETS=(ultrafast medium veryslow)
REPEAT=10

OUT_DIR="encoded_outputs"
PSNR_DIR="psnr_logs"
ENERGY_DIR="energy_logs"

mkdir -p "$OUT_DIR" "$PSNR_DIR" "$ENERGY_DIR"

# RAPL domains: core (PP0), uncore (pkg), dram
RAPL_PATH_BASE="/sys/class/powercap/intel-rapl:0"
RAPL_CORE="$RAPL_PATH_BASE:0/energy_uj"
RAPL_UNCORE="$RAPL_PATH_BASE:1/energy_uj"
RAPL_DRAM="$RAPL_PATH_BASE:2/energy_uj"

function read_energy() {
  cat "$1"
}

function to_joule() {
  echo "scale=6; $1 / 1000000.0" | bc
}

# Output CSV header
ENERGY_CSV="$ENERGY_DIR/energy_pilot_results.csv"
echo "Video,QP,Preset,Run,Energy_Core_J,Energy_Uncore_J,Energy_DRAM_J" > "$ENERGY_CSV"

for QP in "${QPS[@]}"; do
  for PRESET in "${PRESETS[@]}"; do
    for RUN in $(seq 1 $REPEAT); do
      OUT_NAME="qp${QP}_${PRESET}_run${RUN}"
      OUT_BIN="$OUT_DIR/${OUT_NAME}.265"
      LOG_TXT="$PSNR_DIR/${OUT_NAME}.log"
      LOG_CSV="$PSNR_DIR/${OUT_NAME}_frame.csv"

      echo -e "\n[INFO] Encoding QP=${QP} Preset=${PRESET} Run=${RUN}"

      # === RAPL start ===
      ENERGY_CORE_BEFORE=$(read_energy "$RAPL_CORE")
      ENERGY_UNCORE_BEFORE=$(read_energy "$RAPL_UNCORE")
      ENERGY_DRAM_BEFORE=$(read_energy "$RAPL_DRAM")

      # === Encode ===
      x265 \
        --input "$INPUT_YUV" \
        --input-res ${WIDTH}x${HEIGHT} \
        --fps ${FPS} \
        --frames ${FRAMES} \
        --intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 \
        --qp ${QP} --aq-mode 0 \
        --preset ${PRESET} \
        --tune psnr \
        --psnr \
        --recon /dev/null \
        --csv "$LOG_CSV" --csv-log-level 2 \
        -o "$OUT_BIN" 2> "$LOG_TXT"

      # === RAPL end ===
      ENERGY_CORE_AFTER=$(read_energy "$RAPL_CORE")
      ENERGY_UNCORE_AFTER=$(read_energy "$RAPL_UNCORE")
      ENERGY_DRAM_AFTER=$(read_energy "$RAPL_DRAM")

      # === Compute delta ===
      DELTA_CORE=$((ENERGY_CORE_AFTER - ENERGY_CORE_BEFORE))
      DELTA_UNCORE=$((ENERGY_UNCORE_AFTER - ENERGY_UNCORE_BEFORE))
      DELTA_DRAM=$((ENERGY_DRAM_AFTER - ENERGY_DRAM_BEFORE))

      # Convert to Joules
      CORE_J=$(to_joule $DELTA_CORE)
      UNCORE_J=$(to_joule $DELTA_UNCORE)
      DRAM_J=$(to_joule $DELTA_DRAM)

      echo "ControlledBurn_720p,${QP},${PRESET},${RUN},${CORE_J},${UNCORE_J},${DRAM_J}" >> "$ENERGY_CSV"
    done
  done

done

# === Summary ===
echo -e "\n[INFO] Pilot study complete. Energy data saved to: $ENERGY_CSV"
