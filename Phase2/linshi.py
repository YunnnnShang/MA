#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HEVC Intra-Coding: Energy (J) vs Time (s) scatter plots
Professional version (NO cleaning). Draws with preset-level coloring within each encoder.

Data assumptions (NO cleaning/normalization):
- CSV columns (already validated/cleaned by user):
  ['encoder','resolution','video_name','qp','preset','bpp','bitrate_kbps',
   'psnr_y','psnr_u','psnr_v','psnr_yuv','E_process_single_J','P_process_W','t_process_single_s']

What this script produces:
1) Overall:
   - overall/overall_x265.(png|pdf)   # x265-only, preset-colored
   - overall/overall_hw.(png|pdf)     # HW-only, preset-colored
   - overall/overall_combined.(png|pdf)  # x265 + HW overlapped; encoder-shape; preset-colored within encoder
2) Per-Resolution (for present ones among: 270p, 360p, 720p, 1080p, 2k, 4K):
   - per_resolution/res_{RES}_x265.(png|pdf)
   - per_resolution/res_{RES}_hw.(png|pdf)
   - per_resolution/res_{RES}_combined.(png|pdf)
3) Per-Preset (independent):
   - per_preset/preset_x265_{preset}.(png|pdf)
   - per_preset/preset_hw_{preset}.(png|pdf)

Usage:
  python plot_energy_time_professional.py --csv /path/to/all_dataset.csv --outdir ./figures
  python plot_energy_time_professional.py --csv /path/to/all_dataset.csv --outdir ./figures --logx --logy
"""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -------------------- CONFIG (NO cleaning) --------------------
X_COL = "t_process_single_s"
Y_COL = "E_process_single_J"

# exact resolution labels to check (no normalization)
RES_SET = ["270p", "360p", "720p", "1080p", "2k", "4K"]

# x265 preset space (we will only plot those actually present)
X265_PRESETS = ["ultrafast", "superfast", "faster", "veryfast", "fast", "medium"]

# HW preset space (treat as strings for matching)
HW_PRESETS_STR = ["1", "2", "3", "4"]

# Encoder marker shapes
ENCODER_MARKER = {
    "x265": "o",   # circle
    "HW":   "^",   # triangle
}

# Colormaps for presets (distinct & consistent order)
# Chosen to be clear in grayscale printing as well (varying luminance).
X265_PRESET_COLORS = {
    "ultrafast":  "#1f77b4",
    "superfast":  "#17becf",
    "faster":     "#ff7f0e",
    "veryfast":   "#bcbd22",
    "fast":       "#2ca02c",
    "medium":     "#9467bd",
}
HW_PRESET_COLORS = {
    "1": "#d62728",
    "2": "#e377c2",
    "3": "#7f7f7f",
    "4": "#8c564b",
}

# Matplotlib styling
plt.rcParams["figure.dpi"] = 130
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["font.size"] = 11


# -------------------- Utilities --------------------
def encoder_group_value(enc):
    """
    Split encoder into two groups WITHOUT modifying your data:
    - EXACT 'x265' => 'x265'
    - everything else => 'HW'
    """
    return "x265" if str(enc) == "x265" else "HW"

def pearson_r_safe(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if x.size < 3:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def save_figure(fig, path_png: Path):
    ensure_dir(path_png.parent)
    fig.savefig(path_png)
    fig.savefig(path_png.with_suffix(".pdf"))
    plt.close(fig)

def finalize_axes(ax, title, logx=False, logy=False):
    if logx:
        ax.set_xscale("log")
        ax.grid(True, which="both", axis="x", linestyle="--", alpha=0.3)
    if logy:
        ax.set_yscale("log")
        ax.grid(True, which="both", axis="y", linestyle="--", alpha=0.3)
    ax.set_xlabel("Encoding Time (s)")
    ax.set_ylabel("Energy (J)")
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.3)
    # legend placed outside if too long will fallback to best
    ax.legend(loc="best", frameon=False)

def scatter_by_preset(ax, df_subset, encoder_key, alpha=0.55, s=20.0):
    """
    Within one encoder group, split points by preset and color by preset.
    - encoder_key: 'x265' or 'HW'
    """
    marker = ENCODER_MARKER[encoder_key]
    if encoder_key == "x265":
        cmap = X265_PRESET_COLORS
        ordered = [p for p in X265_PRESETS if p in set(df_subset["preset"])]
    else:
        cmap = HW_PRESET_COLORS
        # cast preset to str for matching 1..4
        preset_as_str = df_subset["preset"].astype(str)
        ordered = [p for p in HW_PRESETS_STR if p in set(preset_as_str)]

    # draw per-preset
    handles = []
    labels = []
    if encoder_key == "x265":
        for p in ordered:
            dp = df_subset[df_subset["preset"] == p]
            if dp.empty:
                continue
            h = ax.scatter(dp[X_COL], dp[Y_COL], c=cmap[p], marker=marker, s=s, alpha=alpha, label=f"{encoder_key} | {p}")
            handles.append(h); labels.append(f"{encoder_key} | {p}")
    else:
        for p in ordered:
            mask = (df_subset["preset"].astype(str) == p)
            dp = df_subset[mask]
            if dp.empty:
                continue
            h = ax.scatter(dp[X_COL], dp[Y_COL], c=cmap[p], marker=marker, s=s, alpha=alpha, label=f"{encoder_key} | {p}")
            handles.append(h); labels.append(f"{encoder_key} | {p}")

    return handles, labels


# -------------------- Plotting blocks --------------------
def overall_plots(df, outdir: Path, logx=False, logy=False):
    sub = outdir / "overall"

    dx = df[df["encoder"].apply(lambda e: encoder_group_value(e) == "x265")]
    dh = df[df["encoder"].apply(lambda e: encoder_group_value(e) == "HW")]

    # x265-only (preset-colored)
    if not dx.empty:
        r = pearson_r_safe(dx[X_COL], dx[Y_COL])
        print(f"[Overall] x265: n={len(dx)} | r={r:.4f}")
        fig, ax = plt.subplots(figsize=(7.2, 5.2))
        scatter_by_preset(ax, dx, "x265")
        finalize_axes(ax, f"Energy vs Time (Overall, x265) | r={r:.3f}", logx, logy)
        save_figure(fig, sub / "overall_x265.png")

    # HW-only (preset-colored)
    if not dh.empty:
        r = pearson_r_safe(dh[X_COL], dh[Y_COL])
        print(f"[Overall] HW  : n={len(dh)} | r={r:.4f}")
        fig, ax = plt.subplots(figsize=(7.2, 5.2))
        scatter_by_preset(ax, dh, "HW")
        finalize_axes(ax, f"Energy vs Time (Overall, HW) | r={r:.3f}", logx, logy)
        save_figure(fig, sub / "overall_hw.png")

    # combined (both encoders; each encoder preset-colored)
    if not dx.empty or not dh.empty:
        r_all = pearson_r_safe(df[X_COL], df[Y_COL])
        print(f"[Overall] Combined: n={len(df)} | r={r_all:.4f}")
        fig, ax = plt.subplots(figsize=(7.6, 5.4))
        handles = []; labels = []
        if not dx.empty:
            h, l = scatter_by_preset(ax, dx, "x265")
            handles += h; labels += l
        if not dh.empty:
            h, l = scatter_by_preset(ax, dh, "HW")
            handles += h; labels += l
        # Larger legend if many presets show up
        ax.legend(handles, labels, loc="best", frameon=False, ncols=2 if len(labels) > 8 else 1)
        finalize_axes(ax, f"Energy vs Time (Overall, combined) | r={r_all:.3f}", logx, logy)
        save_figure(fig, sub / "overall_combined.png")


def per_resolution_plots(df, outdir: Path, logx=False, logy=False):
    sub = outdir / "per_resolution"

    for res in RES_SET:
        dres = df[df["resolution"] == res]
        if dres.empty:
            continue

        dx = dres[dres["encoder"].apply(lambda e: encoder_group_value(e) == "x265")]
        dh = dres[dres["encoder"].apply(lambda e: encoder_group_value(e) == "HW")]

        # x265-only
        if not dx.empty:
            r = pearson_r_safe(dx[X_COL], dx[Y_COL])
            print(f"[Per-Resolution] {res} | x265: n={len(dx)} | r={r:.4f}")
            fig, ax = plt.subplots(figsize=(7.2, 5.2))
            scatter_by_preset(ax, dx, "x265")
            finalize_axes(ax, f"Energy vs Time ({res}, x265) | r={r:.3f}", logx, logy)
            save_figure(fig, sub / f"res_{res}_x265.png")

        # HW-only
        if not dh.empty:
            r = pearson_r_safe(dh[X_COL], dh[Y_COL])
            print(f"[Per-Resolution] {res} | HW  : n={len(dh)} | r={r:.4f}")
            fig, ax = plt.subplots(figsize=(7.2, 5.2))
            scatter_by_preset(ax, dh, "HW")
            finalize_axes(ax, f"Energy vs Time ({res}, HW) | r={r:.3f}", logx, logy)
            save_figure(fig, sub / f"res_{res}_hw.png")

        # combined
        r_all = pearson_r_safe(dres[X_COL], dres[Y_COL])
        print(f"[Per-Resolution] {res} | Combined: n={len(dres)} | r={r_all:.4f}")
        fig, ax = plt.subplots(figsize=(7.4, 5.3))
        handles = []; labels = []
        if not dx.empty:
            h, l = scatter_by_preset(ax, dx, "x265"); handles += h; labels += l
        if not dh.empty:
            h, l = scatter_by_preset(ax, dh, "HW");   handles += h; labels += l
        ax.legend(handles, labels, loc="best", frameon=False, ncols=2 if len(labels) > 8 else 1)
        finalize_axes(ax, f"Energy vs Time ({res}, combined) | r={r_all:.3f}", logx, logy)
        save_figure(fig, sub / f"res_{res}_combined.png")


def per_preset_independent_plots(df, outdir: Path, logx=False, logy=False):
    sub = outdir / "per_preset"

    # x265 presets (independent)
    dx = df[df["encoder"].apply(lambda e: encoder_group_value(e) == "x265")]
    if not dx.empty:
        present_x265 = [p for p in X265_PRESETS if p in set(dx["preset"])]
        for p in present_x265:
            dpx = dx[dx["preset"] == p]
            if dpx.empty:
                continue
            r = pearson_r_safe(dpx[X_COL], dpx[Y_COL])
            print(f"[Per-Preset x265] {p}: n={len(dpx)} | r={r:.4f}")
            fig, ax = plt.subplots(figsize=(7.2, 5.2))
            ax.scatter(dpx[X_COL], dpx[Y_COL], c=X265_PRESET_COLORS[p],
                       marker=ENCODER_MARKER["x265"], s=22.0, alpha=0.6, label=f"x265 | {p}")
            finalize_axes(ax, f"Energy vs Time (x265, preset={p}) | r={r:.3f}", logx, logy)
            save_figure(fig, sub / f"preset_x265_{p}.png")

    # HW presets (independent)
    dh = df[df["encoder"].apply(lambda e: encoder_group_value(e) == "HW")]
    if not dh.empty:
        # match by string equality
        pstr = dh["preset"].astype(str)
        present_hw = [p for p in HW_PRESETS_STR if p in set(pstr)]
        for p in present_hw:
            dph = dh[pstr == p]
            if dph.empty:
                continue
            r = pearson_r_safe(dph[X_COL], dph[Y_COL])
            print(f"[Per-Preset HW] {p}: n={len(dph)} | r={r:.4f}")
            fig, ax = plt.subplots(figsize=(7.2, 5.2))
            ax.scatter(dph[X_COL], dph[Y_COL], c=HW_PRESET_COLORS[p],
                       marker=ENCODER_MARKER["HW"], s=22.0, alpha=0.6, label=f"HW | {p}")
            finalize_axes(ax, f"Energy vs Time (HW, preset={p}) | r={r:.3f}", logx, logy)
            save_figure(fig, sub / f"preset_hw_{p}.png")


# -------------------- Main --------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to all_dataset.csv")
    parser.add_argument("--outdir", default="./figures", help="Output directory")
    parser.add_argument("--logx", action="store_true", help="Use log scale on X (time)")
    parser.add_argument("--logy", action="store_true", help="Use log scale on Y (energy)")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    ensure_dir(outdir)

    # NO cleaning/normalization: just load as-is
    df = pd.read_csv(args.csv)

    # Assert required columns exist (do NOT alter values)
    required_cols = {
        "encoder","resolution","video_name","qp","preset","bpp","bitrate_kbps",
        "psnr_y","psnr_u","psnr_v","psnr_yuv","E_process_single_J","P_process_W","t_process_single_s"
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # 1) Overall
    overall_plots(df, outdir, logx=args.logx, logy=args.logy)

    # 2) Per-Resolution
    per_resolution_plots(df, outdir, logx=args.logx, logy=args.logy)

    # 3) Per-Preset (independent)
    per_preset_independent_plots(df, outdir, logx=args.logx, logy=args.logy)

    print(f"[Done] Figures saved under: {outdir.resolve()}")


if __name__ == "__main__":
    main()
