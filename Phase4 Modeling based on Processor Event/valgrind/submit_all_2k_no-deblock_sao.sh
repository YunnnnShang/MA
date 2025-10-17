#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/pe_energy_exp"
VIDEOS_DIR="$BASE/videos/a2_2k"            # 先只跑 2K
SBATCH_SCRIPT="$BASE/run_valgrind_dis_deblock_en_sao.sbatch"


# 预设与QP
PRESETS=(faster fast veryfast superfast)
QPS=(22 27 32 37)

# 检查 sbatch 脚本
if [[ ! -x "$SBATCH_SCRIPT" ]]; then
  echo "[ERR] 找不到可执行的 sbatch 脚本：$SBATCH_SCRIPT" >&2
  exit 1
fi

# 统计 2K 视频
mapfile -t YUVS < <(find "$VIDEOS_DIR" -maxdepth 1 -type f -name "*.yuv" | sort)
echo "[INFO] 2K 视频共找到 ${#YUVS[@]} 个。"

# 提取 WxH（严格匹配 1920x1080 这种段，避免 Aerial3200 干扰）
extract_wh() {
  local fname="$1"
  local wh
  wh="$(grep -Eo '[0-9]{3,4}x[0-9]{3,4}' <<<"$(basename "$fname")" | head -n1 || true)"
  if [[ -z "$wh" ]]; then
    echo ""
    return 1
  fi
  echo "$wh"
}

# 提取 FPS：常见命名转 60/30/50/25 等
extract_fps() {
  local fname="$1"
  local base="$(basename "$fname")"

  # 优先识别 5994/2997/30fps/60fps/50/25/p50/30p 等
  if   grep -qiE '5994|60fps|_60p(_|\.|$)' <<<"$base"; then echo 60
  elif grep -qiE '2997|30fps|_30p(_|\.|$)' <<<"$base"; then echo 30
  elif grep -qiE '50fps|_50p(_|\.|$)|p50'  <<<"$base"; then echo 50
  elif grep -qiE '25fps|_25p(_|\.|$)|p25'  <<<"$base"; then echo 25
  elif grep -qiE '24fps|_24p(_|\.|$)|p24'  <<<"$base"; then echo 24
  else
    # 默认 30
    echo 30
  fi
}



for yuv in "${YUVS[@]}"; do
  base="$(basename "$yuv")"
  # 分辨率
  if ! WH="$(extract_wh "$yuv")"; then
    echo "[SKIP] 无法解析分辨率：$base"
    continue
  fi
  WIDTH="${WH%x*}"
  HEIGHT="${WH#*x}"

  # FPS
  FPS="$(extract_fps "$yuv")"

  echo " → sbatch 2k | $base | ${WIDTH}x${HEIGHT} | fps=${FPS}"

  for preset in "${PRESETS[@]}"; do
    for qp in "${QPS[@]}"; do

      OUT=$(sbatch --parsable --export=ALL,\
YUV_PATH="$yuv",\
WIDTH="$WIDTH",\
HEIGHT="$HEIGHT",\
FPS="$FPS",\
FRAMES=130,\
PRESET="$preset",\
QP="$qp",\
CACHE_SIM=yes,\
BRANCH_SIM=yes \
"$SBATCH_SCRIPT")

      echo "   Submitted: preset=${preset} | qp=${qp} | JOBID=${OUT}"
    done
  done
done

echo "[DONE] 已提交 2K 全量（preset × qp × 所有 2K 视频）。用：squeue -u $USER 查看队列。"
