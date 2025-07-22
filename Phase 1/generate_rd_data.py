# -*- coding: utf-8 -*-
import subprocess
import re
import csv
from pathlib import Path
from tqdm import tqdm
import json
# ==============================================================================
# 1. CONFIGURATION SECTION
# ==============================================================================
X265_EXECUTABLE = Path.home() / "x265_git/source/x265"
FFMPEG_EXECUTABLE = Path.home() / "x265_git/source/ffmpeg-7.0.2-amd64-static/ffmpeg"
VMAF_EXECUTABLE = Path.home() / "vmaf/libvmaf/build/tools/vmaf"
VIDEO_SOURCE_DIR = Path.home() / "thesis_videos/aom_8bit"
RESULTS_DIR = Path.home() / "thesis_results_ci"

QPS = [22, 27, 32, 37]
PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"]

VIDEOS = {
    "ControlledBurn_720p": {"path": VIDEO_SOURCE_DIR / "a3_720p/ControlledBurn_1280x720p30_420.yuv", "w": 1280, "h": 720, "fps": 30, "frames": 130},
    "Aerial_2k": {"path": VIDEO_SOURCE_DIR / "a2_2k/Aerial3200_1920x1080_5994_8bit_420.yuv", "w": 1920, "h": 1080, "fps": "60000/1001", "frames": 130},
    "BoxingPractice_4k": {"path": VIDEO_SOURCE_DIR / "a1_4k/BoxingPractice_3840x2160_5994fps_8bit_420.yuv", "w": 3840, "h": 2160, "fps": "60000/1001", "frames": 130},
    "SnowMountain_360p": {"path": VIDEO_SOURCE_DIR / "a4_360p/SnowMountain_640x360_2997.yuv", "w": 640, "h": 360, "fps": 29.97, "frames": 130},
    "SparksElevator_270p": {"path": VIDEO_SOURCE_DIR / "a5_270p/SparksElevator_480x270p_5994_8bit.yuv", "w": 480, "h": 270, "fps": "60000/1001", "frames": 130}
}
# ==============================================================================

def get_rd_point(video_name, video_info, qp, preset):
    """ Collects R-D point data for a given video, QP, and preset"""
    base_name = f"{video_name}_qp{qp}_{preset}"
    hevc_file = RESULTS_DIR / f"{base_name}.hevc"
    decoded_yuv_file = RESULTS_DIR / f"{base_name}_decoded.yuv"
    metrics_file = RESULTS_DIR / f"{base_name}_metrics.json"

    result = {"bitrate_kbps": None, "psnr_y": None}

    try:
        # 1.encoding

        x265_command = [
            str(X265_EXECUTABLE),
            "--input", str(video_info["path"]),
            "--input-res", f'{video_info["w"]}x{video_info["h"]}',
            "--fps", str(video_info["fps"]),
            "--frames", str(video_info["frames"]),
            "--intra", 
            "--keyint", "1",
            "--min-keyint", "1",
            "--bframes", "0",
            "--scenecut", "0",
            "--qp", str(qp),
            "--no-opt-qp-pps",
            "--ipratio", "1.0",
            "--preset", preset,
            "--tune", "psnr",
            "-o", str(hevc_file)
        ]

        process = subprocess.run(x265_command, capture_output=True, text=True, check=True)
        bitrate_match = re.search(r", (\d+\.\d+) kb/s,", process.stderr)
        if bitrate_match: result["bitrate_kbps"] = float(bitrate_match.group(1))

        # 2. decoding
        ffmpeg_command = [str(FFMPEG_EXECUTABLE), "-y", "-i", str(hevc_file), "-c:v", "rawvideo", "-f", "rawvideo", str(decoded_yuv_file)]
        subprocess.run(ffmpeg_command, capture_output=True, check=True)

        # 3. VMAF 
        vmaf_command = [
            str(VMAF_EXECUTABLE), "-r", str(video_info["path"]), "-d", str(decoded_yuv_file),
            "-w", str(video_info["w"]), "-h", str(video_info["h"]), "-p", "420", "-b", "8", "--json",
            "--threads", "4", "--output", str(metrics_file), "--feature", "psnr"
        ]
        subprocess.run(vmaf_command, capture_output=True, check=True)
        
        with open(metrics_file, 'r') as f:
            vmaf_data = json.load(f)
            result["psnr_y"] = vmaf_data.get("pooled_metrics", {}).get("psnr_y", {}).get("mean")

    except Exception as e:
        tqdm.write(f"fail: {video_name} QP={qp} Preset={preset}. error: {e}")
        return None
    finally:
        # cleanup
        for f in [hevc_file, decoded_yuv_file, metrics_file]:
            if f.exists(): f.unlink()
            
    return result

if __name__ == "__main__":
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_csv_path = RESULTS_DIR / "bitrate_psnr_results.csv"
    
    header = ["video_name", "qp", "preset", "bitrate_kbps", "psnr_y"]
    with open(output_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

    total_tasks = len(VIDEOS) * len(QPS) * len(PRESETS)
    with tqdm(total=total_tasks, desc="采集R-D数据") as pbar:
        for video_name, video_info in VIDEOS.items():
            for preset in PRESETS:
                for qp in QPS:
                    pbar.set_description(f"{video_name} @ {preset}, QP={qp}")
                    
                    rd_point = get_rd_point(video_name, video_info, qp, preset)
                    
                    if rd_point:
                        with open(output_csv_path, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([video_name, qp, preset, 
                                             f'{rd_point["bitrate_kbps"]:.2f}',
                                             f'{rd_point["psnr_y"]:.4f}'])
                    pbar.update(1)

    print(f"\n Saved: {output_csv_path}")
