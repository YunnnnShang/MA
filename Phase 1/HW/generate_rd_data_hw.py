#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import re
import csv
from pathlib import Path

VIDEO_ENCODE_EXEC = Path("/usr/src/jetson_multimedia_api/samples/01_video_encode/video_encode")
VIDEO_DECODE_EXEC = Path("/usr/src/jetson_multimedia_api/samples/00_video_decode/video_decode")
FFMPEG_EXEC = Path("/usr/bin/ffmpeg")

VIDEO_SOURCE_ROOT = Path("/OriginalVideos/aom_8bit")
RESULTS_DIR = Path.home() / "TestFiles/rd_results_hw_full"

KEEP_INTERMEDIATES = False

QPS = [22, 27, 32, 37]
PRESETS = {1: "ultrafast", 2: "fast", 3: "medium", 4: "slow"}
FRAMES_TO_ENCODE = 30

# --- VIDEO DATASET ---
VIDEOS = {
    # --- 4K Sequences (a1_4k) ---
    "BoxingPractice_4k": {
        "path": VIDEO_SOURCE_ROOT / "a1_4k/BoxingPractice_3840x2160_5994fps_8bit_420.yuv",
        "w": 3840, "h": 2160, "fps": "60000/1001"
    },
    "Crosswalk_4k": {
        "path": VIDEO_SOURCE_ROOT / "a1_4k/Crosswalk_3840x2160_5994fps_8bit_420.yuv",
        "w": 3840, "h": 2160, "fps": "60000/1001"
    },
    "FoodMarket2_4k": {
        "path": VIDEO_SOURCE_ROOT / "a1_4k/FoodMarket2_3840x2160_5994fps_8bit_420.yuv",
        "w": 3840, "h": 2160, "fps": "60000/1001"
    },
    "Neon1224_4k": {
        "path": VIDEO_SOURCE_ROOT / "a1_4k/Neon1224_3840x2160_2997fps.yuv",
        "w": 3840, "h": 2160, "fps": "29.97"
    },
    "NocturneDance_4k": {
        "path": VIDEO_SOURCE_ROOT / "a1_4k/NocturneDance_3840x2160p_8bit_60fps.yuv",
        "w": 3840, "h": 2160, "fps": "60"
    },
    "PierSeaSide_4k": {
        "path": VIDEO_SOURCE_ROOT / "a1_4k/PierSeaSide_3840x2160_2997fps_8bit_420.yuv",
        "w": 3840, "h": 2160, "fps": "29.97"
    },
    "Tango_4k": {
        "path": VIDEO_SOURCE_ROOT / "a1_4k/Tango_3840x2160_5994fps_8bit_420.yuv",
        "w": 3840, "h": 2160, "fps": "60000/1001"
    },
    "TimeLapse_4k": {
        "path": VIDEO_SOURCE_ROOT / "a1_4k/TimeLapse_3840x2160_5994fps_8bit_420.yuv",
        "w": 3840, "h": 2160, "fps": "60000/1001"
    },

    # --- 2K / 1080p Sequences (a2_2k) ---
    "Boat_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/Boat_1920x1080_5994_8bit_420.yuv",
        "w": 1920, "h": 1080, "fps": "60000/1001"
    },
    "FoodMarket_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/FoodMarket_1920x1080_5994_8bit_420.yuv",
        "w": 1920, "h": 1080, "fps": "60000/1001"
    },
    "MeridianTalk_sdr_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/MeridianTalk_sdr_1920x1080p_5994_8bit.yuv",
        "w": 1920, "h": 1080, "fps": "60000/1001"
    },
    "RushFieldCuts_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/RushFieldCuts_1920x1080_2997.yuv",
        "w": 1920, "h": 1080, "fps": "29.97"
    },
    "ToddlerFountain_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/ToddlerFountain_1920x1080_2997fps_8bit_420.yuv",
        "w": 1920, "h": 1080, "fps": "29.97"
    },
    "TreesAndGrass_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/TreesAndGrass_1920_1080_30fps_8bit.yuv",
        "w": 1920, "h": 1080, "fps": "30"
    },
    "Aerial3200_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/Aerial3200_1920x1080_5994_8bit_420.yuv",
        "w": 1920, "h": 1080, "fps": "60000/1001"
    },
    "CrowdRun_1080p50": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/CrowdRun_1920x1080p50.yuv",
        "w": 1920, "h": 1080, "fps": "50"
    },
    "DinnerSceneCropped_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/DinnerSceneCropped_1920x1080_2997fps_8bit_420.yuv",
        "w": 1920, "h": 1080, "fps": "29.97"
    },
    "Motorcycle_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/Motorcycle_1920x1080_30fps_8bit.yuv",
        "w": 1920, "h": 1080, "fps": "30"
    },
    "MountainBike_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/MountainBike_1920x1080_30fps_8bit.yuv",
        "w": 1920, "h": 1080, "fps": "30"
    },
    "OldTownCross_1080p50": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/OldTownCross_1920x1080p50.yuv",
        "w": 1920, "h": 1080, "fps": "50"
    },
    "PedestrianArea_1080p25": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/PedestrianArea_1920x1080p25.yuv",
        "w": 1920, "h": 1080, "fps": "25"
    },
    "RitualDance_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/RitualDance_1920x1080_5994_8bit_420.yuv",
        "w": 1920, "h": 1080, "fps": "60000/1001"
    },
    "Riverbed_1080p25": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/Riverbed_1920x1080p25.yuv",
        "w": 1920, "h": 1080, "fps": "25"
    },
    "Skater227_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/Skater227_1920x1080_30fps.yuv",
        "w": 1920, "h": 1080, "fps": "30"
    },
    "TunnelFlag_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/TunnelFlag_1920x1080_5994_8bit_420.yuv",
        "w": 1920, "h": 1080, "fps": "60000/1001"
    },
    "Vertical_bees_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/Vertical_bees_1080x1920_2997.yuv",
        "w": 1080, "h": 1920, "fps": "29.97"
    },
    "Vertical_Carnaby_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/Vertical_Carnaby_1080x1920_5994.yuv",
        "w": 1080, "h": 1920, "fps": "60000/1001"
    },
    "WalkingInStreet_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/WalkingInStreet_1920x1080_30fps.yuv",
        "w": 1920, "h": 1080, "fps": "30"
    },
    "WorldCup_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/WorldCup_1920x1080_30p.yuv",
        "w": 1920, "h": 1080, "fps": "30"
    },
    "WorldCup_far_2k": {
        "path": VIDEO_SOURCE_ROOT / "a2_2k/WorldCup_far_1920x1080_30p.yuv",
        "w": 1920, "h": 1080, "fps": "30"
    },

    # --- 720p Sequences (a3_720p) ---
    "ControlledBurn_720p": {
        "path": VIDEO_SOURCE_ROOT / "a3_720p/ControlledBurn_1280x720p30_420.yuv",
        "w": 1280, "h": 720, "fps": "30"
    },
    "DrivingPOV_720p": {
        "path": VIDEO_SOURCE_ROOT / "a3_720p/DrivingPOV_1280x720p_5994_8bit_420.yuv",
        "w": 1280, "h": 720, "fps": "60000/1001"
    },
    "Johnny_720p": {
        "path": VIDEO_SOURCE_ROOT / "a3_720p/Johnny_1280x720_60.yuv",
        "w": 1280, "h": 720, "fps": "60"
    },
    "KristenAndSara_720p": {
        "path": VIDEO_SOURCE_ROOT / "a3_720p/KristenAndSara_1280x720_60.yuv",
        "w": 1280, "h": 720, "fps": "60"
    },
    "RollerCoaster_720p": {
        "path": VIDEO_SOURCE_ROOT / "a3_720p/RollerCoaster_1280x720p_5994_8bit_420.yuv",
        "w": 1280, "h": 720, "fps": "60000/1001"
    },
    "Vidyo3_720p": {
        "path": VIDEO_SOURCE_ROOT / "a3_720p/Vidyo3_1280x720p_60fps.yuv",
        "w": 1280, "h": 720, "fps": "60"
    },
    "Vidyo4_720p": {
        "path": VIDEO_SOURCE_ROOT / "a3_720p/Vidyo4_1280x720p_60fps.yuv",
        "w": 1280, "h": 720, "fps": "60"
    },
    "WestWindEasy_720p": {
        "path": VIDEO_SOURCE_ROOT / "a3_720p/WestWindEasy_1280x720p30_420.yuv",
        "w": 1280, "h": 720, "fps": "30"
    },

    # --- 360p Sequences (a4_360p) ---
    "BlueSky_360p": {
        "path": VIDEO_SOURCE_ROOT / "a4_360p/BlueSky_360p25.yuv",
        "w": 640, "h": 360, "fps": "25"
    },
    "RedKayak_360p": {
        "path": VIDEO_SOURCE_ROOT / "a4_360p/RedKayak_360_2997.yuv",
        "w": 640, "h": 360, "fps": "29.97"
    },
    "SnowMountain_360p": {
        "path": VIDEO_SOURCE_ROOT / "a4_360p/SnowMountain_640x360_2997.yuv",
        "w": 640, "h": 360, "fps": "29.97"
    },
    "SpeedBag_360p": {
        "path": VIDEO_SOURCE_ROOT / "a4_360p/SpeedBag_640x360_2997.yuv",
        "w": 640, "h": 360, "fps": "29.97"
    },
    "Stockholm_360p": {
        "path": VIDEO_SOURCE_ROOT / "a4_360p/Stockholm_640x360_5994.yuv",
        "w": 640, "h": 360, "fps": "60000/1001"
    },
    "TouchdownPass_360p": {
        "path": VIDEO_SOURCE_ROOT / "a4_360p/TouchdownPass_640x360_2997.yuv",
        "w": 640, "h": 360, "fps": "29.97"
    },

    # --- 270p Sequences (a5_270p) ---
    "FourPeople_270p": {
        "path": VIDEO_SOURCE_ROOT / "a5_270p/FourPeople_480x270_60.yuv",
        "w": 480, "h": 270, "fps": "60"
    },
    "ParkJoy_270p": {
        "path": VIDEO_SOURCE_ROOT / "a5_270p/ParkJoy_480x270_50.yuv",
        "w": 480, "h": 270, "fps": "50"
    },
    "SparksElevator_270p": {
        "path": VIDEO_SOURCE_ROOT / "a5_270p/SparksElevator_480x270p_5994_8bit.yuv",
        "w": 480, "h": 270, "fps": "60000/1001"
    },
    "Vertical_Bayshore_270p": {
        "path": VIDEO_SOURCE_ROOT / "a5_270p/Vertical_Bayshore_270x480_2997.yuv",
        "w": 270, "h": 480, "fps": "29.97"
    },
}

def parse_fps(fps_str):
    if isinstance(fps_str, str) and "/" in fps_str:
        num, den = map(int, fps_str.split('/'))
        return num / den
    return float(fps_str)

def run_cmd(args):
    return subprocess.run(args, capture_output=True, text=True)

def parse_psnr(stderr: str):
    def _grab(m):
        return float("inf") if m == "inf" else float(m)
    m_y = re.search(r"\by:([0-9.]+|inf)\b", stderr)
    m_u = re.search(r"\bu:([0-9.]+|inf)\b", stderr)
    m_v = re.search(r"\bv:([0-9.]+|inf)\b", stderr)
    if not (m_y and m_u and m_v):
        raise ValueError("PSNR fields missing")
    return _grab(m_y.group(1)), _grab(m_u.group(1)), _grab(m_v.group(1))

def get_rd_point(video_info, qp, preset_id, preset_name):
    video_name = video_info["name"]
    original_yuv = video_info["path"]
    width, height = video_info["w"], video_info["h"]
    fps = parse_fps(video_info["fps"])

    hevc_file = RESULTS_DIR / f"{video_name}_qp{qp}_preset{preset_name}.bin"
    decoded_yuv_file = RESULTS_DIR / f"{video_name}_qp{qp}_preset{preset_name}_decoded.yuv"

    try:
        encode_cmd = [
            str(VIDEO_ENCODE_EXEC), str(original_yuv), str(width), str(height), "H265", str(hevc_file),
            "-hpt", str(preset_id), "-sf", "0", "-ef", str(FRAMES_TO_ENCODE - 1),
            "-ifi", "1", "--econstqp", "-qpi", str(qp), str(qp), str(qp)
        ]
        proc_enc = run_cmd(encode_cmd)
        if proc_enc.returncode != 0:
            return None

        decode_cmd = [
            str(VIDEO_DECODE_EXEC), "H265", "--disable-rendering",
            "-o", str(decoded_yuv_file), str(hevc_file)
        ]
        proc_dec = run_cmd(decode_cmd)
        if proc_dec.returncode != 0 or not decoded_yuv_file.exists():
            return None

        file_size_bytes = hevc_file.stat().st_size
        bitrate_kbps = (file_size_bytes * 8 * fps) / (FRAMES_TO_ENCODE * 1000)

        base_args = [
            str(FFMPEG_EXEC),
            "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{width}x{height}", "-i", str(original_yuv),
            "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{width}x{height}", "-i", str(decoded_yuv_file),
            "-frames:v", str(FRAMES_TO_ENCODE), "-lavfi", "[0:v][1:v]psnr", "-f", "null", "-"
        ]
        proc_psnr = run_cmd(base_args)
        try:
            psnr_y, psnr_u, psnr_v = parse_psnr(proc_psnr.stderr)
        except Exception:
            fb_args = [
                str(FFMPEG_EXEC),
                "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{width}x{height}", "-i", str(original_yuv),
                "-f", "rawvideo", "-pix_fmt", "nv12", "-s", f"{width}x{height}", "-i", str(decoded_yuv_file),
                "-frames:v", str(FRAMES_TO_ENCODE),
                "-lavfi", "[1:v]format=yuv420p[dec];[0:v][dec]psnr", "-f", "null", "-"
            ]
            proc_fb = run_cmd(fb_args)
            psnr_y, psnr_u, psnr_v = parse_psnr(proc_fb.stderr)

        return {
            "video_name": video_name, "qp": qp, "preset": preset_name,
            "bitrate_kbps": round(bitrate_kbps, 2),
            "psnr_y": psnr_y if psnr_y != float("inf") else "inf",
            "psnr_u": psnr_u if psnr_u != float("inf") else "inf",
            "psnr_v": psnr_v if psnr_v != float("inf") else "inf",
        }
    except Exception:
        return None
    finally:
        if not KEEP_INTERMEDIATES:
            try:
                if hevc_file.exists(): hevc_file.unlink()
                if decoded_yuv_file.exists(): decoded_yuv_file.unlink()
            except Exception:
                pass

if __name__ == "__main__":
    for exe in [VIDEO_ENCODE_EXEC, VIDEO_DECODE_EXEC, FFMPEG_EXEC]:
        if not exe.exists():
            exit(1)
    for v_info in VIDEOS.values():
        if not v_info["path"].exists():
            exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_csv_path = RESULTS_DIR / "rd_results_hardware_full_dataset.csv"
    header = ["video_name", "qp", "preset", "bitrate_kbps", "psnr_y", "psnr_u", "psnr_v"]

    with open(output_csv_path, 'w', newline='') as f:
        csv.writer(f).writerow(header)

    for video_name, video_data in VIDEOS.items():
        video_data['name'] = video_name
        for preset_id, preset_name in PRESETS.items():
            for qp in QPS:
                rd_point = get_rd_point(video_data, qp, preset_id, preset_name)
                if rd_point:
                    with open(output_csv_path, 'a', newline='') as f:
                        csv.writer(f).writerow([rd_point[k] for k in header])
