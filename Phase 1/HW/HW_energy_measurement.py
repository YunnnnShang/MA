#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import subprocess
import statistics
import numpy as np
import serial
import copy
import csv

try:
    from scipy.stats import t as student_t
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False
    print("[WARN] scipy not installed, using fallback for CI calculation.")

# ========================= User config =========================
# For the full run, expand the VIDEOS, QPS, and PRESETS lists.
CLIENT = "or16ixuv@192.168.178.1"
SSH_BATCH_MODE = True
SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200

# --- VIDEO DATASET ---
VIDEOS = [
    # --- 4K Sequences (a1_4k) ---
    # {
    #     "name": "BoxingPractice_4k",
    #     "path": "/OriginalVideos/aom_8bit/a1_4k/BoxingPractice_3840x2160_5994fps_8bit_420.yuv",
    #     "w": 3840, "h": 2160, "fps": "60000/1001"
    # },
    # {
    #     "name": "Crosswalk_4k",
    #     "path": "/OriginalVideos/aom_8bit/a1_4k/Crosswalk_3840x2160_5994fps_8bit_420.yuv",
    #     "w": 3840, "h": 2160, "fps": "60000/1001"
    # },
    # {
    #     "name": "FoodMarket2_4k",
    #     "path": "/OriginalVideos/aom_8bit/a1_4k/FoodMarket2_3840x2160_5994fps_8bit_420.yuv",
    #     "w": 3840, "h": 2160, "fps": "60000/1001"
    # },
    # {
    #     "name": "Neon1224_4k",
    #     "path": "/OriginalVideos/aom_8bit/a1_4k/Neon1224_3840x2160_2997fps.yuv",
    #     "w": 3840, "h": 2160, "fps": "29.97"
    # },
    # {
    #     "name": "NocturneDance_4k",
    #     "path": "/OriginalVideos/aom_8bit/a1_4k/NocturneDance_3840x2160p_8bit_60fps.yuv",
    #     "w": 3840, "h": 2160, "fps": "60"
    # },
    # {
    #     "name": "PierSeaSide_4k",
    #     "path": "/OriginalVideos/aom_8bit/a1_4k/PierSeaSide_3840x2160_2997fps_8bit_420.yuv",
    #     "w": 3840, "h": 2160, "fps": "29.97"
    # },
    # {
    #     "name": "Tango_4k",
    #     "path": "/OriginalVideos/aom_8bit/a1_4k/Tango_3840x2160_5994fps_8bit_420.yuv",
    #     "w": 3840, "h": 2160, "fps": "60000/1001"
    # },
    # {
    #     "name": "TimeLapse_4k",
    #     "path": "/OriginalVideos/aom_8bit/a1_4k/TimeLapse_3840x2160_5994fps_8bit_420.yuv",
    #     "w": 3840, "h": 2160, "fps": "60000/1001"
    # },

    # # --- 2K / 1080p Sequences (a2_2k) ---
    # {
    #     "name": "Boat_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/Boat_1920x1080_5994_8bit_420.yuv",
    #     "w": 1920, "h": 1080, "fps": "60000/1001"
    # },
    # {
    #     "name": "FoodMarket_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/FoodMarket_1920x1080_5994_8bit_420.yuv",
    #     "w": 1920, "h": 1080, "fps": "60000/1001"
    # },
    # {
    #     "name": "MeridianTalk_sdr_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/MeridianTalk_sdr_1920x1080p_5994_8bit.yuv",
    #     "w": 1920, "h": 1080, "fps": "60000/1001"
    # },
    # {
    #     "name": "RushFieldCuts_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/RushFieldCuts_1920x1080_2997.yuv",
    #     "w": 1920, "h": 1080, "fps": "29.97"
    # },
    # {
    #     "name": "ToddlerFountain_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/ToddlerFountain_1920x1080_2997fps_8bit_420.yuv",
    #     "w": 1920, "h": 1080, "fps": "29.97"
    # },
    # {
    #     "name": "TreesAndGrass_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/TreesAndGrass_1920_1080_30fps_8bit.yuv",
    #     "w": 1920, "h": 1080, "fps": "30"
    # },
    # {
    #     "name": "Aerial3200_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/Aerial3200_1920x1080_5994_8bit_420.yuv",
    #     "w": 1920, "h": 1080, "fps": "60000/1001"
    # },
    # {
    #     "name": "CrowdRun_1080p50",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/CrowdRun_1920x1080p50.yuv",
    #     "w": 1920, "h": 1080, "fps": "50"
    # },
    # {
    #     "name": "DinnerSceneCropped_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/DinnerSceneCropped_1920x1080_2997fps_8bit_420.yuv",
    #     "w": 1920, "h": 1080, "fps": "29.97"
    # },
    # {
    #     "name": "Motorcycle_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/Motorcycle_1920x1080_30fps_8bit.yuv",
    #     "w": 1920, "h": 1080, "fps": "30"
    # },
    # {
    #     "name": "MountainBike_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/MountainBike_1920x1080_30fps_8bit.yuv",
    #     "w": 1920, "h": 1080, "fps": "30"
    # },
    # {
    #     "name": "OldTownCross_1080p50",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/OldTownCross_1920x1080p50.yuv",
    #     "w": 1920, "h": 1080, "fps": "50"
    # },
    # {
    #     "name": "PedestrianArea_1080p25",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/PedestrianArea_1920x1080p25.yuv",
    #     "w": 1920, "h": 1080, "fps": "25"
    # },
    # {
    #     "name": "RitualDance_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/RitualDance_1920x1080_5994_8bit_420.yuv",
    #     "w": 1920, "h": 1080, "fps": "60000/1001"
    # },
    # {
    #     "name": "Riverbed_1080p25",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/Riverbed_1920x1080p25.yuv",
    #     "w": 1920, "h": 1080, "fps": "25"
    # },
    # {
    #     "name": "Skater227_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/Skater227_1920x1080_30fps.yuv",
    #     "w": 1920, "h": 1080, "fps": "30"
    # },
    # {
    #     "name": "TunnelFlag_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/TunnelFlag_1920x1080_5994_8bit_420.yuv",
    #     "w": 1920, "h": 1080, "fps": "60000/1001"
    # },
    # {
    #     "name": "Vertical_bees_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/Vertical_bees_1080x1920_2997.yuv",
    #     "w": 1080, "h": 1920, "fps": "29.97"
    # },
    # {
    #     "name": "Vertical_Carnaby_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/Vertical_Carnaby_1080x1920_5994.yuv",
    #     "w": 1080, "h": 1920, "fps": "60000/1001"
    # },
    # {
    #     "name": "WalkingInStreet_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/WalkingInStreet_1920x1080_30fps.yuv",
    #     "w": 1920, "h": 1080, "fps": "30"
    # },
    # {
    #     "name": "WorldCup_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/WorldCup_1920x1080_30p.yuv",
    #     "w": 1920, "h": 1080, "fps": "30"
    # },
    # {
    #     "name": "WorldCup_far_2k",
    #     "path": "/OriginalVideos/aom_8bit/a2_2k/WorldCup_far_1920x1080_30p.yuv",
    #     "w": 1920, "h": 1080, "fps": "30"
    # },

    # --- 720p Sequences (a3_720p) ---
    {
        "name": "ControlledBurn_720p",
        "path": "/OriginalVideos/aom_8bit/a3_720p/ControlledBurn_1280x720p30_420.yuv",
        "w": 1280, "h": 720, "fps": "30"
    },
    {
        "name": "DrivingPOV_720p",
        "path": "/OriginalVideos/aom_8bit/a3_720p/DrivingPOV_1280x720p_5994_8bit_420.yuv",
        "w": 1280, "h": 720, "fps": "60000/1001"
    },
    {
        "name": "Johnny_720p",
        "path": "/OriginalVideos/aom_8bit/a3_720p/Johnny_1280x720_60.yuv",
        "w": 1280, "h": 720, "fps": "60"
    },
    {
        "name": "KristenAndSara_720p",
        "path": "/OriginalVideos/aom_8bit/a3_720p/KristenAndSara_1280x720_60.yuv",
        "w": 1280, "h": 720, "fps": "60"
    },
    {
        "name": "RollerCoaster_720p",
        "path": "/OriginalVideos/aom_8bit/a3_720p/RollerCoaster_1280x720p_5994_8bit_420.yuv",
        "w": 1280, "h": 720, "fps": "60000/1001"
    },
    {
        "name": "Vidyo3_720p",
        "path": "/OriginalVideos/aom_8bit/a3_720p/Vidyo3_1280x720p_60fps.yuv",
        "w": 1280, "h": 720, "fps": "60"
    },
    {
        "name": "Vidyo4_720p",
        "path": "/OriginalVideos/aom_8bit/a3_720p/Vidyo4_1280x720p_60fps.yuv",
        "w": 1280, "h": 720, "fps": "60"
    },
    {
        "name": "WestWindEasy_720p",
        "path": "/OriginalVideos/aom_8bit/a3_720p/WestWindEasy_1280x720p30_420.yuv",
        "w": 1280, "h": 720, "fps": "30"
    },

    # # --- 360p Sequences (a4_360p) ---
    # {
    #     "name": "BlueSky_360p",
    #     "path": "/OriginalVideos/aom_8bit/a4_360p/BlueSky_360p25.yuv",
    #     "w": 640, "h": 360, "fps": "25"
    # },
    # {
    #     "name": "RedKayak_360p",
    #     "path": "/OriginalVideos/aom_8bit/a4_360p/RedKayak_360_2997.yuv",
    #     "w": 640, "h": 360, "fps": "29.97"
    # },
    # {
    #     "name": "SnowMountain_360p",
    #     "path": "/OriginalVideos/aom_8bit/a4_360p/SnowMountain_640x360_2997.yuv",
    #     "w": 640, "h": 360, "fps": "29.97"
    # },
    # {
    #     "name": "SpeedBag_360p",
    #     "path": "/OriginalVideos/aom_8bit/a4_360p/SpeedBag_640x360_2997.yuv",
    #     "w": 640, "h": 360, "fps": "29.97"
    # },
    # {
    #     "name": "Stockholm_360p",
    #     "path": "/OriginalVideos/aom_8bit/a4_360p/Stockholm_640x360_5994.yuv",
    #     "w": 640, "h": 360, "fps": "60000/1001"
    # },
    # {
    #     "name": "TouchdownPass_360p",
    #     "path": "/OriginalVideos/aom_8bit/a4_360p/TouchdownPass_640x360_2997.yuv",
    #     "w": 640, "h": 360, "fps": "29.97"
    # },

    # # --- 270p Sequences (a5_270p) ---
    # {
    #     "name": "FourPeople_270p",
    #     "path": "/OriginalVideos/aom_8bit/a5_270p/FourPeople_480x270_60.yuv",
    #     "w": 480, "h": 270, "fps": "60"
    # },
    # {
    #     "name": "ParkJoy_270p",
    #     "path": "/OriginalVideos/aom_8bit/a5_270p/ParkJoy_480x270_50.yuv",
    #     "w": 480, "h": 270, "fps": "50"
    # },
    # {
    #     "name": "SparksElevator_270p",
    #     "path": "/OriginalVideos/aom_8bit/a5_270p/SparksElevator_480x270p_5994_8bit.yuv",
    #     "w": 480, "h": 270, "fps": "60000/1001"
    # },
    # {
    #     "name": "Vertical_Bayshore_270p",
    #     "path": "/OriginalVideos/aom_8bit/a5_270p/Vertical_Bayshore_270x480_2997.yuv",
    #     "w": 270, "h": 480, "fps": "29.97"
    # }
]

QPS = [22, 27, 32, 37]
PRESETS = [1, 2, 3, 4] # 1:ultrafast, 2:fast, 3:medium, 4:slow
FRAMES_TO_ENCODE = 130 # For All-Intra test

# --- Binaries on Jetson ---
VIDEO_ENCODE_EXEC = "/usr/src/jetson_multimedia_api/samples/01_video_encode/video_encode"

# --- CI & Timing Policy ---
CONF_PROB = 0.99
INTERVAL_PART = 0.02
MIN_MEASUREMENTS = 5
MAX_MEASUREMENTS = 15
STABILIZATION_SEC = 30.0
MIN_ENCODE_DURATION_SEC = 2.0
IDLE_GAP_SEC = 2.0
#COOLDOWN_SEC = 0.0

# --- LMG611 Instrument Policy ---
LMG_RETURNS_WH = True
VOLT_RANGE_UPPER = 250.0
CURR_RANGE_FIXED = 0.6 

# ========================= Helper Functions =========================

def _w(lmg: serial.Serial, cmd: str):
    """Sends a command to the LMG611."""
    if not cmd.endswith("\r"): cmd += "\r"
    lmg.write(cmd.encode("ascii"))
    time.sleep(0.05)

def _qf(lmg: serial.Serial, cmd: str) -> float:
    _w(lmg, cmd)
    line = lmg.readline().decode("utf-8", errors="ignore").strip()
    while not line: line = lmg.readline().decode("utf-8", errors="ignore").strip()
    return float(line)

def init_lmg611(lmg: serial.Serial, v_upper: float, i_upper: float):
    lmg.reset_input_buffer(); lmg.reset_output_buffer()
    print("Initializing LMG611...")
    _w(lmg, "*RST"); time.sleep(1)
    _w(lmg, "LANG 0")
    _w(lmg, ":SENS:ENER:ENAB 1")
    _w(lmg, f":SENS:VOLT:RANG:AUTO 0; :SENS:VOLT:RANG:UPP {v_upper}")
    _w(lmg, f":SENS:CURR:RANG:AUTO 0; :SENS:CURR:RANG:UPP {i_upper}")
    _w(lmg, ":TRIG:INT:ENER:STOP 1; :TRIG:INT:ENER:RES 1")
    print(f"LMG611 Initialized. V_range={v_upper}V, I_range(fixed)={i_upper}A")

def ssh_command(client: str, remote_cmd: str):
    wrapped = f"bash -lc '{remote_cmd}'"
    ssh_opts = ["ssh"]
    if SSH_BATCH_MODE: ssh_opts += ["-o", "BatchMode=yes"]
    ssh_opts += [client, wrapped]
    
    res = subprocess.run(ssh_opts, capture_output=True, text=True)
    
    if res.returncode != 0:
        raise RuntimeError(
            f"Remote command failed (ssh return {res.returncode}).\n"
            f"COMMAND:\n  {remote_cmd}\n"
            f"STDOUT:\n{res.stdout}\n"
            f"STDERR:\n{res.stderr}"
        )

def determine_loop_count(client: str, video_info: dict, qp: int, preset_id: int, frames: int, out_path: str) -> int:
    """
    Performs a two-probe measurement to accurately determine the required loop count
    to meet MIN_ENCODE_DURATION_SEC, separating SSH overhead from payload.
    This function does NOT perform the final measurement.
    """
    one_cmd = (
        f"{VIDEO_ENCODE_EXEC} {video_info['path']} {video_info['w']} {video_info['h']} H265 {out_path} "
        f"-hpt {preset_id} -sf 0 -ef {frames-1} -ifi 1 --econstqp -qpi {qp} {qp} {qp}"
    )

    # Probe 1: Time a single execution
    t_start_1 = time.time()
    ssh_command(client, one_cmd)
    t_end_1 = time.time()
    duration_1 = t_end_1 - t_start_1

    if duration_1 >= MIN_ENCODE_DURATION_SEC:
        return 1

    # Probe 2: Time a double execution
    two_cmd = f"for i in {{1..2}}; do {one_cmd}; done"
    t_start_2 = time.time()
    ssh_command(client, two_cmd)
    t_end_2 = time.time()
    duration_2 = t_end_2 - t_start_2

    t_payload = max(0.001, duration_2 - duration_1)
    t_overhead = max(0.001, duration_1 - t_payload)

    loops = int(np.ceil((MIN_ENCODE_DURATION_SEC - t_overhead) / t_payload))
    
    return loops if loops > 0 else 1
def run_final_encode(client: str, video_info: dict, qp: int, preset_id: int, frames: int, out_path: str, loops: int) -> float:
    """
    Runs the final, looped encoding command for a specific number of loops.
    This is the function that will be timed and measured by the power meter.
    """
    one_cmd = (
        f"{VIDEO_ENCODE_EXEC} {video_info['path']} {video_info['w']} {video_info['h']} H265 {out_path} "
        f"-hpt {preset_id} -sf 0 -ef {frames-1} -ifi 1 --econstqp -qpi {qp} {qp} {qp}"
    )

    if loops <= 1:
        final_cmd = one_cmd
    else:
        final_cmd = f"for i in {{1..{loops}}}; do {one_cmd}; done"

    t_start = time.time()
    ssh_command(client, final_cmd)
    t_end = time.time()

    return t_end - t_start

def measure_once_paired(lmg: serial.Serial, run_fn):
    """Performs one paired load/idle measurement cycle."""
    # ---- Load Phase ----
    _w(lmg, ":TRIG:INT:ENER:RES 1")
    _w(lmg, ":TRIG:INT:ENER:STAR 1")
    
    run_fn()

    _w(lmg, ":TRIG:INT:ENER:STOP 1")
    e_load_raw = _qf(lmg, ":READ:SCAL:ENER?")
    t_load_measured = _qf(lmg, ":READ:SCALAR:SLOTS:ENERGY:DURATION?")

    time.sleep(IDLE_GAP_SEC)

    # ---- Idle Phase ----
    _w(lmg, ":TRIG:INT:ENER:RES 1")
    _w(lmg, ":TRIG:INT:ENER:STAR 1")
    time.sleep(t_load_measured)
    _w(lmg, ":TRIG:INT:ENER:STOP 1")
    e_idle_raw = _qf(lmg, ":READ:SCAL:ENER?")
    t_idle_measured = t_load_measured

    # --- Calculations ---
    toJ = (lambda x: x * 3600.0) if LMG_RETURNS_WH else (lambda x: x)
    e_load_J = toJ(e_load_raw)
    e_idle_J = toJ(e_idle_raw)

    if t_load_measured <= 0 or t_idle_measured <= 0:
        return None

    e_process_J = e_load_J - e_idle_J
    p_load_W = e_load_J / t_load_measured
    p_idle_W = e_idle_J / t_idle_measured
    p_process_W = p_load_W - p_idle_W

    print(f"  [raw] E_load={e_load_J:.3f}J, t_load={t_load_measured:.3f}s, P_load~{p_load_W:.2f}W")
    print(f"  [raw] E_idle={e_idle_J:.3f}J, t_idle={t_idle_measured:.3f}s, P_idle~{p_idle_W:.2f}W")

    return {
        "E_process": e_process_J, "P_process": p_process_W, "t_process": t_load_measured,
        "E_load": e_load_J, "t_load": t_load_measured, "P_load": p_load_W,
        "E_idle": e_idle_J, "t_idle": t_idle_measured, "P_idle": p_idle_W,
    }

def t_half_width(samples: list, conf_prob: float) -> float:
    n = len(samples)
    if n < 2: return float("inf")
    s = statistics.stdev(samples)
    if SCIPY_OK: tcrit = student_t.ppf((1 + conf_prob) / 2, n - 1)
    else: tcrit = 2.576 if conf_prob >= 0.99 else 1.96
    return (s / np.sqrt(n)) * tcrit

def iqr_filter(xs: list) -> list:
    if len(xs) < 4: return xs
    q1, q3 = np.percentile(xs, [25, 75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [x for x in xs if lo <= x <= hi]

def median_25_filter(xs: list) -> list:
    if len(xs) < 3: return xs
    med = float(np.median(xs))
    lo, hi = 0.75 * med, 1.25 * med
    return [x for x in xs if lo <= x <= hi]

# ========================= Main =========================
def main():
    try:
        lmg = serial.Serial(SERIAL_PORT, baudrate=BAUD, timeout=20)
    except serial.SerialException as e:
        print(f"FATAL: Could not open {SERIAL_PORT}. Error: {e}"); return

    init_lmg611(lmg, VOLT_RANGE_UPPER, CURR_RANGE_FIXED)
    
    print(f"\n--- System Stabilization ({STABILIZATION_SEC}s) ---")
    time.sleep(STABILIZATION_SEC)

    output_csv = 'energy_results_hardware_batch_normalized.csv' # 建议使用新文件名
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        # 更新CSV表头以反映归一化后的数据
        writer.writerow(['video_name', 'qp', 'preset', 
                         'E_process_single_J', 'P_process_W', 't_process_single_s',
                         'E_load_total_J', 't_load_total_s', 'P_load_W',
                         'E_idle_total_J', 't_idle_total_s', 'P_idle_W'])

        # *** BATCH PROCESSING LOOPS ***
        for video in VIDEOS:
            for qp in QPS:
                for preset in PRESETS:
                    remote_out_path = f"/tmp/{video['name']}_qp{qp}_p{preset}.h265"
                    print(f"\n--- Processing: {video['name']} | QP={qp} | Preset={preset} ---")
                    
                    # --- 1. PROBE PHASE (No power measurement) ---
                    # 先执行探测，确定本次测试点需要的循环次数
                    try:
                        print(" -> Probing for optimal loop count...")
                        _loops = determine_loop_count(CLIENT, video, qp, preset, FRAMES_TO_ENCODE, remote_out_path)
                        print(f" -> Probe complete. Using {_loops} loops for this test point.")
                    except RuntimeError as e:
                        print(f"  [FATAL_PROBE] Probe failed for this test point. Aborting.")
                        print(e)
                        # 清理可能的残留文件并跳到下一个测试点
                        try: ssh_command(CLIENT, f"rm -f {remote_out_path}")
                        except RuntimeError: pass
                        continue # Skip to the next test point in the preset loop
        
                    all_results = []
                    
                    # --- 2. MEASUREMENT PHASE ---
                    for rep in range(1, MAX_MEASUREMENTS + 1):
                        print(f"\n--- Repetition {rep}/{MAX_MEASUREMENTS} ---")
                        try:
                            # 定义一个简单的lambda函数，它只调用最终的执行函数
                            # 这个函数将被 measure_once_paired 精确地计时和积分
                            final_run_fn = lambda: run_final_encode(CLIENT, video, qp, preset, FRAMES_TO_ENCODE, remote_out_path, _loops)
                            
                            # measure_once_paired 现在测量的就是纯粹的、最终的N次循环
                            result = measure_once_paired(lmg, final_run_fn)
                            
                            if result and result["E_process"] > 0:
                                # --- 3. NORMALIZATION ---
                                original_total_energy = result['E_process']
                                result['E_process'] /= _loops
                                result['t_process'] /= _loops
                                if result['t_process'] > 0:
                                    result['P_process'] = result['E_process'] / result['t_process']
                                else:
                                    result['P_process'] = 0
                                
                                all_results.append(result)
                                print(f"  [info] Loops={_loops}, E_total={original_total_energy:.3f} J -> E_single={result['E_process']:.3f} J, t_single={result['t_process']:.3f} s")
                            else:
                                print("  [skip] Invalid sample.")
        
                        except RuntimeError as e:
                            print(f"  [ERROR] A command failed during repetition {rep}. Aborting this test point.")
                            print(e)
                            all_results = []
                            break

                         # --- 后续的统计分析将自动使用归一化后的 'E_process' 值 ---
                        current_energies = [r['E_process'] for r in all_results]
                        if len(current_energies) >= MIN_MEASUREMENTS:
                            energies_filtered = iqr_filter(current_energies)

                            if len(energies_filtered) >= MIN_MEASUREMENTS:
                                mean_e = np.mean(energies_filtered)
                                ci_half_width = t_half_width(energies_filtered, CONF_PROB)
                                threshold = INTERVAL_PART * mean_e

                                print(f"-> Stats (n={len(energies_filtered)}): "
                                      f"Mean_single={mean_e:.3f} J, CI half-width={ci_half_width:.3f} J, Threshold={threshold:.3f} J")

                                if ci_half_width < threshold:
                                    print("-> Confidence Interval target met. Stopping early.")
                                    # 过滤掉不在最终统计范围内的结果
                                    all_results = [r for r in all_results if r['E_process'] in energies_filtered]
                                    break
                                else:
                                    if len(energies_filtered) > 9:
                                        before = len(energies_filtered)
                                        energies_filtered = median_25_filter(energies_filtered)
                                        after = len(energies_filtered)
                                        if after != before:
                                            print(f"-> median±25% filtered: {before} -> {after} samples")
                    
                    if all_results:
                        # --- 最终结果现在是基于“单次编码平均值”计算的 ---
                        final_energy_mean = np.mean([r['E_process'] for r in all_results])
                        final_power_mean = np.mean([r['P_process'] for r in all_results])
                        final_duration_mean = np.mean([r['t_process'] for r in all_results])
                        
                        # 注意: 原始的load/idle值仍然是循环的总值，这里我们主要关心归一化后的净值
                        final_load_energy = np.mean([r['E_load'] for r in all_results])
                        final_load_time = np.mean([r['t_load'] for r in all_results])
                        final_load_power = np.mean([r['P_load'] for r in all_results])
                        final_idle_energy = np.mean([r['E_idle'] for r in all_results])
                        final_idle_time = np.mean([r['t_idle'] for r in all_results])
                        final_idle_power = np.mean([r['P_idle'] for r in all_results])

                        writer.writerow([
                            video['name'], qp, preset, 
                            f"{final_energy_mean:.4f}", f"{final_power_mean:.2f}", f"{final_duration_mean:.3f}",
                            f"{final_load_energy:.4f}", f"{final_load_time:.3f}", f"{final_load_power:.2f}",
                            f"{final_idle_energy:.4f}", f"{final_idle_time:.3f}", f"{final_idle_power:.2f}"
                        ])
                        f.flush()
                    
                    try:
                        ssh_command(CLIENT, f"rm -f {remote_out_path}")
                    except RuntimeError as e:
                        print(f"  [WARN] Could not clean up remote file {remote_out_path}. Error: {e}")

    print(f"\n--- Batch measurement complete. Results saved to {output_csv} ---")
    lmg.close()

if __name__ == "__main__":
    main()

