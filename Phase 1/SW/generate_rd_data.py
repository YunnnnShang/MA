# -*- coding: utf-8 -*-
import subprocess
import re
import csv
from pathlib import Path
from tqdm import tqdm
import json
import pandas as pd # <-- Make sure pandas is installed (pip install pandas)

# ==============================================================================
# 1. CONFIGURATION SECTION
# ==============================================================================
X265_EXECUTABLE = Path.home() / "x265_git/source/x265"
FFMPEG_EXECUTABLE = Path.home() / "x265_git/source/ffmpeg-7.0.2-amd64-static/ffmpeg"
VMAF_EXECUTABLE = Path.home() / "vmaf/libvmaf/build/tools/vmaf"
VMAF_MODEL_PATH = Path.home() / "vmaf/model/vmaf_v0.6.1.json" # Needed for VMAF calculation

VIDEO_SOURCE_DIR = Path.home() / "thesis_videos/aom_8bit"
RESULTS_DIR = Path.home() / "thesis_results_ci"

QPS = [22, 27, 32, 37]
PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"]
FRAMES = 130 

VIDEOS = {
    # --- 4K Sequences (a1_4k) ---
    "BoxingPractice_4k": {"path": VIDEO_SOURCE_DIR / "a1_4k/BoxingPractice_3840x2160_5994fps_8bit_420.yuv", "w": 3840, "h": 2160, "fps": "60000/1001", "frames": FRAMES},
    "Crosswalk_4k": {"path": VIDEO_SOURCE_DIR / "a1_4k/Crosswalk_3840x2160_5994fps_8bit_420.yuv", "w": 3840, "h": 2160, "fps": "60000/1001", "frames": FRAMES},
    "FoodMarket2_4k": {"path": VIDEO_SOURCE_DIR / "a1_4k/FoodMarket2_3840x2160_5994fps_8bit_420.yuv", "w": 3840, "h": 2160, "fps": "60000/1001", "frames": FRAMES},
    "Neon1224_4k": {"path": VIDEO_SOURCE_DIR / "a1_4k/Neon1224_3840x2160_2997fps.yuv", "w": 3840, "h": 2160, "fps": "29.97", "frames": FRAMES},
    "NocturneDance_4k": {"path": VIDEO_SOURCE_DIR / "a1_4k/NocturneDance_3840x2160p_8bit_60fps.yuv", "w": 3840, "h": 2160, "fps": "60", "frames": FRAMES},
    "PierSeaSide_4k": {"path": VIDEO_SOURCE_DIR / "a1_4k/PierSeaSide_3840x2160_2997fps_8bit_420.yuv", "w": 3840, "h": 2160, "fps": "29.97", "frames": FRAMES},
    "Tango_4k": {"path": VIDEO_SOURCE_DIR / "a1_4k/Tango_3840x2160_5994fps_8bit_420.yuv", "w": 3840, "h": 2160, "fps": "60000/1001", "frames": FRAMES},
    "TimeLapse_4k": {"path": VIDEO_SOURCE_DIR / "a1_4k/TimeLapse_3840x2160_5994fps_8bit_420.yuv", "w": 3840, "h": 2160, "fps": "60000/1001", "frames": FRAMES},
    
    # --- 2K / 1080p Sequences (a2_2k) ---
    "Boat_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/Boat_1920x1080_5994_8bit_420.yuv", "w": 1920, "h": 1080, "fps": "60000/1001", "frames": FRAMES},
    "FoodMarket_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/FoodMarket_1920x1080_5994_8bit_420.yuv", "w": 1920, "h": 1080, "fps": "60000/1001", "frames": FRAMES},
    "MeridianTalk_sdr_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/MeridianTalk_sdr_1920x1080p_5994_8bit.yuv", "w": 1920, "h": 1080, "fps": "60000/1001", "frames": FRAMES},
    "RushFieldCuts_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/RushFieldCuts_1920x1080_2997.yuv", "w": 1920, "h": 1080, "fps": "29.97", "frames": FRAMES},
    "ToddlerFountain_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/ToddlerFountain_1920x1080_2997fps_8bit_420.yuv", "w": 1920, "h": 1080, "fps": "29.97", "frames": FRAMES},
    "TreesAndGrass_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/TreesAndGrass_1920_1080_30fps_8bit.yuv", "w": 1920, "h": 1080, "fps": "30", "frames": FRAMES},
    "Aerial3200_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/Aerial3200_1920x1080_5994_8bit_420.yuv", "w": 1920, "h": 1080, "fps": "60000/1001", "frames": FRAMES},
    "CrowdRun_1080p50": {"path": VIDEO_SOURCE_DIR / "a2_2k/CrowdRun_1920x1080p50.yuv", "w": 1920, "h": 1080, "fps": "50", "frames": FRAMES},
    "DinnerSceneCropped_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/DinnerSceneCropped_1920x1080_2997fps_8bit_420.yuv", "w": 1920, "h": 1080, "fps": "29.97", "frames": FRAMES},
    "Motorcycle_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/Motorcycle_1920x1080_30fps_8bit.yuv", "w": 1920, "h": 1080, "fps": "30", "frames": FRAMES},
    "MountainBike_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/MountainBike_1920x1080_30fps_8bit.yuv", "w": 1920, "h": 1080, "fps": "30", "frames": FRAMES},
    "OldTownCross_1080p50": {"path": VIDEO_SOURCE_DIR / "a2_2k/OldTownCross_1920x1080p50.yuv", "w": 1920, "h": 1080, "fps": "50", "frames": FRAMES},
    "PedestrianArea_1080p25": {"path": VIDEO_SOURCE_DIR / "a2_2k/PedestrianArea_1920x1080p25.yuv", "w": 1920, "h": 1080, "fps": "25", "frames": FRAMES},
    "RitualDance_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/RitualDance_1920x1080_5994_8bit_420.yuv", "w": 1920, "h": 1080, "fps": "60000/1001", "frames": FRAMES},
    "Riverbed_1080p25": {"path": VIDEO_SOURCE_DIR / "a2_2k/Riverbed_1920x1080p25.yuv", "w": 1920, "h": 1080, "fps": "25", "frames": FRAMES},
    "Skater227_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/Skater227_1920x1080_30fps.yuv", "w": 1920, "h": 1080, "fps": "30", "frames": FRAMES},
    "TunnelFlag_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/TunnelFlag_1920x1080_5994_8bit_420.yuv", "w": 1920, "h": 1080, "fps": "60000/1001", "frames": FRAMES},
    "Vertical_bees_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/Vertical_bees_1080x1920_2997.yuv", "w": 1080, "h": 1920, "fps": "29.97", "frames": FRAMES},
    "Vertical_Carnaby_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/Vertical_Carnaby_1080x1920_5994.yuv", "w": 1080, "h": 1920, "fps": "60000/1001", "frames": FRAMES},
    "WalkingInStreet_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/WalkingInStreet_1920x1080_30fps.yuv", "w": 1920, "h": 1080, "fps": "30", "frames": FRAMES},
    "WorldCup_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/WorldCup_1920x1080_30p.yuv", "w": 1920, "h": 1080, "fps": "30", "frames": FRAMES},
    "WorldCup_far_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/WorldCup_far_1920x1080_30p.yuv", "w": 1920, "h": 1080, "fps": "30", "frames": FRAMES},

    # --- 720p Sequences (a3_720p) ---
    "ControlledBurn_720p": {"path": VIDEO_SOURCE_DIR / "a3_720p/ControlledBurn_1280x720p30_420.yuv", "w": 1280, "h": 720, "fps": "30", "frames": FRAMES},
    "DrivingPOV_720p": {"path": VIDEO_SOURCE_DIR / "a3_720p/DrivingPOV_1280x720p_5994_8bit_420.yuv", "w": 1280, "h": 720, "fps": "60000/1001", "frames": FRAMES},
    "Johnny_720p": {"path": VIDEO_SOURCE_DIR / "a3_720p/Johnny_1280x720_60.yuv", "w": 1280, "h": 720, "fps": "60", "frames": FRAMES},
    "KristenAndSara_720p": {"path": VIDEO_SOURCE_DIR / "a3_720p/KristenAndSara_1280x720_60.yuv", "w": 1280, "h": 720, "fps": "60", "frames": FRAMES},
    "RollerCoaster_720p": {"path": VIDEO_SOURCE_DIR / "a3_720p/RollerCoaster_1280x720p_5994_8bit_420.yuv", "w": 1280, "h": 720, "fps": "60000/1001", "frames": FRAMES},
    "Vidyo3_720p": {"path": VIDEO_SOURCE_DIR / "a3_720p/Vidyo3_1280x720p_60fps.yuv", "w": 1280, "h": 720, "fps": "60", "frames": FRAMES},
    "Vidyo4_720p": {"path": VIDEO_SOURCE_DIR / "a3_720p/Vidyo4_1280x720p_60fps.yuv", "w": 1280, "h": 720, "fps": "60", "frames": FRAMES},
    "WestWindEasy_720p": {"path": VIDEO_SOURCE_DIR / "a3_720p/WestWindEasy_1280x720p30_420.yuv", "w": 1280, "h": 720, "fps": "30", "frames": FRAMES},

    # --- 360p Sequences (a4_360p) ---
    "BlueSky_360p": {"path": VIDEO_SOURCE_DIR / "a4_360p/BlueSky_360p25.yuv", "w": 640, "h": 360, "fps": "25", "frames": FRAMES},
    "RedKayak_360p": {"path": VIDEO_SOURCE_DIR / "a4_360p/RedKayak_360_2997.yuv", "w": 640, "h": 360, "fps": "29.97", "frames": FRAMES},
    "SnowMountain_360p": {"path": VIDEO_SOURCE_DIR / "a4_360p/SnowMountain_640x360_2997.yuv", "w": 640, "h": 360, "fps": "29.97", "frames": FRAMES},
    "SpeedBag_360p": {"path": VIDEO_SOURCE_DIR / "a4_360p/SpeedBag_640x360_2997.yuv", "w": 640, "h": 360, "fps": "29.97", "frames": FRAMES},
    "Stockholm_360p": {"path": VIDEO_SOURCE_DIR / "a4_360p/Stockholm_640x360_5994.yuv", "w": 640, "h": 360, "fps": "60000/1001", "frames": FRAMES},
    "TouchdownPass_360p": {"path": VIDEO_SOURCE_DIR / "a4_360p/TouchdownPass_640x360_2997.yuv", "w": 640, "h": 360, "fps": "29.97", "frames": FRAMES},

    # --- 270p Sequences (a5_270p) ---
    "FourPeople_270p": {"path": VIDEO_SOURCE_DIR / "a5_270p/FourPeople_480x270_60.yuv", "w": 480, "h": 270, "fps": "60", "frames": FRAMES},
    "ParkJoy_270p": {"path": VIDEO_SOURCE_DIR / "a5_270p/ParkJoy_480x270_50.yuv", "w": 480, "h": 270, "fps": "50", "frames": FRAMES},
    "SparksElevator_270p": {"path": VIDEO_SOURCE_DIR / "a5_270p/SparksElevator_480x270p_5994_8bit.yuv", "w": 480, "h": 270, "fps": "60000/1001", "frames": FRAMES},
    "Vertical_Bayshore_270p": {"path": VIDEO_SOURCE_DIR / "a5_270p/Vertical_Bayshore_270x480_2997.yuv", "w": 270, "h": 480, "fps": "29.97", "frames": FRAMES},
}
# ==============================================================================

def get_rd_point(video_name, video_info, qp, preset):
    """ Collects R-D point data for a given video, QP, and preset, including Y, U, V PSNR """
    base_name = f"{video_name}_qp{qp}_{preset}"
    temp_dir = RESULTS_DIR / "temp_files"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    hevc_file = temp_dir / f"{base_name}.hevc"
    psnr_csv_file = temp_dir / f"{base_name}_psnr.csv"
    decoded_yuv_file = temp_dir / f"{base_name}_decoded.yuv"
    
    result = {
        "bitrate_kbps": None, 
        "psnr_y": None, 
        "psnr_u": None, 
        "psnr_v": None
    }

    try:
        # 1. Encoding with built-in PSNR calculation
        x265_command = [
            str(X265_EXECUTABLE),
            "--input", str(video_info["path"]),
            "--input-res", f'{video_info["w"]}x{video_info["h"]}',
            "--fps", str(video_info["fps"]),
            "--frames", str(video_info["frames"]),
            "--intra", "--keyint", "1", "--min-keyint", "1",
            "--bframes", "0", "--scenecut", "0",
            "--qp", str(qp),
            "--no-opt-qp-pps", "--ipratio", "1.0",
            "--preset", preset,
            "--tune", "psnr",
            "--psnr",  # <-- Enable PSNR calculation
            "--csv", str(psnr_csv_file), "--csv-log-level", "2", # <-- Output detailed CSV
            "-o", str(hevc_file)
        ]

        process = subprocess.run(x265_command, capture_output=True, text=True, check=True, encoding='utf-8')
        bitrate_match = re.search(r",\s*([\d\.]+)\s*kb/s", process.stderr)
        if bitrate_match:
            result["bitrate_kbps"] = float(bitrate_match.group(1))

        # 2. Calculate average PSNR from the generated CSV
        if psnr_csv_file.exists():
            df_psnr = pd.read_csv(psnr_csv_file)
            df_psnr.columns = df_psnr.columns.str.strip() # Clean column names
            result["psnr_y"] = pd.to_numeric(df_psnr["Y PSNR"], errors='coerce').mean()
            result["psnr_u"] = pd.to_numeric(df_psnr["U PSNR"], errors='coerce').mean()
            result["psnr_v"] = pd.to_numeric(df_psnr["V PSNR"], errors='coerce').mean()

    except Exception as e:
        tqdm.write(f"Failed: {video_name} QP={qp} Preset={preset}. Error: {e}")
        return None
    finally:
        # Cleanup
        for f in [hevc_file, psnr_csv_file, decoded_yuv_file]:
            if f.exists():
                f.unlink()
            
    return result

if __name__ == "__main__":
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_csv_path = RESULTS_DIR / "bitrate_psnr_results_full.csv" # New output file name
    
    # Updated header for the new columns
    header = ["video_name", "qp", "preset", "bitrate_kbps", "psnr_y", "psnr_u", "psnr_v"]
    with open(output_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

    total_tasks = len(VIDEOS) * len(QPS) * len(PRESETS)
    with tqdm(total=total_tasks, desc="Collecting R-D Data") as pbar:
        for video_name, video_info in VIDEOS.items():
            for preset in PRESETS:
                for qp in QPS:
                    pbar.set_description(f"{video_name} @ {preset}, QP={qp}")
                    
                    rd_point = get_rd_point(video_name, video_info, qp, preset)
                    
                    if rd_point:
                        with open(output_csv_path, 'a', newline='') as f:
                            writer = csv.writer(f)
                            # Write all PSNR values
                            writer.writerow([
                                video_name, qp, preset, 
                                f'{rd_point["bitrate_kbps"]:.2f}' if rd_point["bitrate_kbps"] is not None else 'N/A',
                                f'{rd_point["psnr_y"]:.4f}' if rd_point["psnr_y"] is not None else 'N/A',
                                f'{rd_point["psnr_u"]:.4f}' if rd_point["psnr_u"] is not None else 'N/A',
                                f'{rd_point["psnr_v"]:.4f}' if rd_point["psnr_v"] is not None else 'N/A'
                            ])
                    pbar.update(1)

    print(f"\nAll R-D data collection complete. Results saved to: {output_csv_path}")
