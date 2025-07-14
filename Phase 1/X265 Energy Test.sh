#!/bin/bash

# ----------------------
# Pilot Study: x265 Energy Measurement Script (RAPL-based)
# ----------------------

# === INPUT VIDEO ===
INPUT_YUV="$HOME/thesis_videos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv"
WIDTH=1280
HEIGHT=720
FRAMES=130
FPS=30

# === PILOT CONFIGURATIONS ===
QPS=(22 32 37)
PRESETS=(ultrafast medium veryslow)
REPEAT=10  # Number of repetitions for confidence testing

# === OUTPUT FOLDERS ===
mkdir -p encoded_outputs
mkdir -p energy_logs
mkdir -p psnr_logs

# === RAPL Energy Reading Functions ===
read_rapl_energy() {
    local domain_path=$1
    cat "$domain_path/energy_uj" 2>/dev/null || echo 0
}

get_rapl_energy_domains() {
    for d in /sys/class/powercap/intel-rapl:*/; do
        echo "$d"
    done
}

# === Main Loop ===
for QP in "${QPS[@]}"; do
  for PRESET in "${PRESETS[@]}"; do
    CONFIG_TAG="qp${QP}_${PRESET}"
    ENERGY_CSV="energy_logs/${CONFIG_TAG}_energy.csv"
    echo "Run,Package_J,PP0_J,DRAM_J" > "$ENERGY_CSV"

    for ((i=1; i<=REPEAT; i++)); do
      echo -e "\n[INFO] Encoding QP=${QP} Preset=${PRESET} Run=${i}"

      # === RAPL domain paths ===
      PKG_PATH="/sys/class/powercap/intel-rapl:0"
      PP0_PATH="/sys/class/powercap/intel-rapl:0:0"
      DRAM_PATH="/sys/class/powercap/intel-rapl:0:2"  # optional, if exists

      # === Energy before ===
      PKG_BEFORE=$(read_rapl_energy "$PKG_PATH")
      PP0_BEFORE=$(read_rapl_energy "$PP0_PATH")
      DRAM_BEFORE=$(read_rapl_energy "$DRAM_PATH")

      # === Run encoder ===
      OUT_BIN="encoded_outputs/${CONFIG_TAG}_run${i}.265"
      LOG_TXT="psnr_logs/${CONFIG_TAG}_run${i}.log"
      LOG_CSV="psnr_logs/${CONFIG_TAG}_run${i}_frame.csv"

      x265 \
        --input "$INPUT_YUV" \
        --input-res ${WIDTH}x${HEIGHT} \
        --fps ${FPS} \
        --frames ${FRAMES} \
        --intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 \
        --aq-mode 0 \
        --qp ${QP} --no-opt-qp-pps --ipratio 1.0 \
        --preset ${PRESET} \
        --tune psnr \
        --psnr \
        --recon /dev/null \
        --csv "$LOG_CSV" --csv-log-level 2 \
        -o "$OUT_BIN" 2> "$LOG_TXT"

      # === Energy after ===
      PKG_AFTER=$(read_rapl_energy "$PKG_PATH")
      PP0_AFTER=$(read_rapl_energy "$PP0_PATH")
      DRAM_AFTER=$(read_rapl_energy "$DRAM_PATH")

      # === Compute energy in Joules ===
      PKG_ENERGY=$(echo "scale=6; ($PKG_AFTER - $PKG_BEFORE)/1000000" | bc)
      PP0_ENERGY=$(echo "scale=6; ($PP0_AFTER - $PP0_BEFORE)/1000000" | bc)
      DRAM_ENERGY=$(echo "scale=6; ($DRAM_AFTER - $DRAM_BEFORE)/1000000" | bc)

      echo "$i,$PKG_ENERGY,$PP0_ENERGY,$DRAM_ENERGY" >> "$ENERGY_CSV"
      echo -e "\033[1;36m[INFO] Energy Run ${i}: Package=${PKG_ENERGY}J, PP0=${PP0_ENERGY}J, DRAM=${DRAM_ENERGY}J\033[0m"
    done
  done
done

# === Summary ===
echo -e "\n[INFO] Pilot Study Completed. Results stored in ./energy_logs and ./psnr_logs"
