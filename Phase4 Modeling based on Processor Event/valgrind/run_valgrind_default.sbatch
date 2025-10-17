#!/usr/bin/env bash
#SBATCH --job-name=vg_x265_default_1T
#SBATCH --cpus-per-task=1
#SBATCH --time=24:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

# 保留助教风格：先加载环境
source ~/.bashrc || true

# 二进制路径（按你的目录写死）——避免“不同节点找不到”
X265_EXECUTABLE="${X265_EXECUTABLE:-$HOME/pe_energy_exp/x265_build/x265}"
VALGRIND_BIN="${VALGRIND_BIN:-$HOME/.local/valgrind/bin/valgrind}"

# 必需参数（提交器传进来）
: "${YUV_PATH:?YUV_PATH is required}"
: "${WIDTH:?WIDTH is required}"
: "${HEIGHT:?HEIGHT is required}"
: "${FPS:?FPS is required}"
: "${FRAMES:?FRAMES is required}"
: "${PRESET:?PRESET is required}"
: "${QP:?QP is required}"
: "${CACHE_SIM:?CACHE_SIM is required}"      # yes/no
: "${BRANCH_SIM:?BRANCH_SIM is required}"    # yes/no

# 固定单线程
export OMP_NUM_THREADS=1
export X265_THREADS=1

OUTDIR="$HOME/pe_energy_exp/outs"
LOGDIR="$HOME/pe_energy_exp/logs"
mkdir -p "$OUTDIR" "$LOGDIR"

# 早期自检，定位 127 问题
echo "[NODE] $(hostname)  [DATE] $(date)"
echo "[BIN]  VALGRIND_BIN=$VALGRIND_BIN"
echo "[BIN]  X265_EXECUTABLE=$X265_EXECUTABLE"
"$VALGRIND_BIN" --version || { echo "[FATAL] valgrind 不可执行"; exit 127; }
"$X265_EXECUTABLE" --version >/dev/null 2>&1 || { echo "[FATAL] x265 不可执行"; exit 127; }

# 助教要求的 callgrind 参数（保持一致），其余沿用我们方案
VG_FLAGS=( --tool=callgrind --dump-instr=yes --collect-jumps=yes )
if [[ "$CACHE_SIM" == "yes" ]]; then
  VG_FLAGS+=( --simulate-cache=yes --I1=32768,8,64 --D1=32768,8,64 --LL=12582912,24,64 )
fi
if [[ "$BRANCH_SIM" == "yes" ]]; then
  VG_FLAGS+=( --branch-sim=yes )
fi

# 输出文件名（我们要存结果，不丢到 /dev/null）
BASENAME="callgrind_Default_1T_${PRESET}_qp${QP}_$(basename "${YUV_PATH%.*}")_${WIDTH}x${HEIGHT}_${FPS}fps_${FRAMES}f.out"
VG_FLAGS+=( --callgrind-out-file="$OUTDIR/$BASENAME" )

# 记录简单环境
printf 'HOST=%s\nJOBID=%s\nMEM=%s\n' "$(hostname)" "${SLURM_JOB_ID:-NA}" "${SLURM_MEM_PER_NODE:-NA}" \
  > "$LOGDIR/env_Default_1T_${PRESET}_qp${QP}_$(basename "${YUV_PATH%.*}")_${WIDTH}x${HEIGHT}_${FPS}fps_${FRAMES}f.log" || true

# 跑
exec "$VALGRIND_BIN" "${VG_FLAGS[@]}" \
  "$X265_EXECUTABLE" \
  --input "$YUV_PATH" \
  --input-res "${WIDTH}x${HEIGHT}" \
  --fps "$FPS" \
  --frames "$FRAMES" \
  --preset "$PRESET" \
  --intra --keyint 1 \
  --qp "$QP" \
  --aq-mode 0 \
  --log-level none \
  -o /dev/null
