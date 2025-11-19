#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HEVC Energy Full Analysis - v2 (with proper legends)

Features:
1) Energy-Time Correlation: SW vs HW separate + combined (with legends)
2) Resolution & QP Impact: trend plots + slope CSV
3) R-D & R-E curves:
    A) combined encoder comparison (with legends)
    B) per-encoder separate plots (with legends)
4) Linear Regression Modeling (NVIDIA-only hardware energy):
    - Time-only / BPP-only / QP-only / Resolution-only / Multi-feature
    - Metrics: R2 / MAPE / RMSE
"""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_absolute_percentage_error, mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder

plt.rcParams["figure.dpi"] = 130
plt.rcParams["font.size"] = 11
plt.rcParams["savefig.bbox"] = "tight"

RES_ORDER = ["270p", "360p", "720p", "1080p", "4K"]
QP_ORDER = [22, 27, 32, 37]


def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)


def slope(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 2:
        return np.nan
    return np.polyfit(x[m], y[m], 1)[0]


# ===================== Part 1 =====================
def part1_corr(df, outdir):
    print(">>> Part1: Energy-Time Correlation")
    sub = Path(outdir) / "01_time_energy"
    ensure_dir(sub)

    enc_sw = df[df["encoder"].str.contains("x265", case=False)]
    enc_hw = df[df["encoder"].str.contains("nvenc|nvidia|hw", case=False)]

    def corr_and_plot(df_, label, filename):
        r = np.corrcoef(df_["t_process_single_s"], df_["E_process_single_J"])[0, 1]
        print(f"  {label}: n={len(df_)} r={r:.4f}")
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(df_["t_process_single_s"], df_["E_process_single_J"],
                   alpha=0.5, label=label)
        ax.set_title(f"{label} Energy vs Time (r={r:.3f})")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Energy (J)")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(frameon=False)
        fig.savefig(sub / filename)
        plt.close(fig)

    # x265-only & NVIDIA-only
    if not enc_sw.empty:
        corr_and_plot(enc_sw, "x265", "x265_energy_time.png")
    if not enc_hw.empty:
        corr_and_plot(enc_hw, "NVIDIA", "NVIDIA_energy_time.png")

    # Combined
    r_all = np.corrcoef(df["t_process_single_s"], df["E_process_single_J"])[0, 1]
    print(f"  Combined: n={len(df)} r={r_all:.4f}")

    fig, ax = plt.subplots(figsize=(7, 5))
    if not enc_sw.empty:
        ax.scatter(enc_sw["t_process_single_s"], enc_sw["E_process_single_J"],
                   alpha=0.5, label="x265")
    if not enc_hw.empty:
        ax.scatter(enc_hw["t_process_single_s"], enc_hw["E_process_single_J"],
                   alpha=0.5, label="NVIDIA")

    ax.set_title(f"Combined Energy vs Time (r={r_all:.3f})")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Energy (J)")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(frameon=False)
    fig.savefig(sub / "Combined_energy_time.png")
    plt.close(fig)


# ===================== Part 2 =====================
def part2_trends(df, outdir):
    print(">>> Part2: Resolution & QP Impact")
    sub = Path(outdir) / "02_config_impact"
    ensure_dir(sub)

    enc_sw = df[df["encoder"].str.contains("x265", case=False)]
    enc_hw = df[df["encoder"].str.contains("nvenc|nvidia|hw", case=False)]

    def plot_resolution(df_, label):
        fig, ax = plt.subplots(figsize=(7, 5))
        slopes = {}
        for preset in sorted(df_["preset"].unique()):
            d = df_[df_["preset"] == preset]
            means = [
                d[d["resolution"] == r]["E_process_single_J"].median()
                if len(d[d["resolution"] == r]) > 0 else np.nan
                for r in RES_ORDER
            ]
            ax.plot(RES_ORDER, means, marker="o", label=preset)
            slopes[f"{label}_{preset}"] = slope(range(len(RES_ORDER)), means)
        ax.set_title(f"Resolution Impact - {label}")
        ax.set_ylabel("Energy (J)")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(frameon=False)
        fig.savefig(sub / f"resolution_trend_{label}.png")
        plt.close(fig)
        return slopes

    def plot_qp(df_, label):
        slopes = {}
        for preset in sorted(df_["preset"].unique()):
            dp = df_[df_["preset"] == preset]
            fig, ax = plt.subplots(figsize=(7, 5))
            for r in RES_ORDER:
                dr = dp[dp["resolution"] == r]
                means = [
                    dr[dr["qp"] == q]["E_process_single_J"].median()
                    if len(dr[dr["qp"] == q]) > 0 else np.nan
                    for q in QP_ORDER
                ]
                if np.all(np.isnan(means)):
                    continue
                ax.plot(QP_ORDER, means, marker="o", label=r)
                slopes[f"{label}_{preset}_{r}"] = slope(QP_ORDER, means)
            ax.set_title(f"QP Impact - {label}, preset={preset}")
            ax.set_xlabel("QP")
            ax.set_ylabel("Energy (J)")
            ax.grid(True, linestyle="--", alpha=0.3)
            ax.legend(frameon=False)
            fig.savefig(sub / f"qp_trend_{label}_{preset}.png")
            plt.close(fig)
        return slopes

    slope_res = {}
    if not enc_sw.empty:
        slope_res.update(plot_resolution(enc_sw, "x265"))
    if not enc_hw.empty:
        slope_res.update(plot_resolution(enc_hw, "NVIDIA"))
    pd.DataFrame(slope_res.items(), columns=["Config", "Slope"]).to_csv(
        sub / "resolution_slopes.csv", index=False
    )

    slope_qp = {}
    if not enc_sw.empty:
        slope_qp.update(plot_qp(enc_sw, "x265"))
    if not enc_hw.empty:
        slope_qp.update(plot_qp(enc_hw, "NVIDIA"))
    pd.DataFrame(slope_qp.items(), columns=["Config", "Slope"]).to_csv(
        sub / "qp_slopes.csv", index=False
    )


# ===================== Part 3 =====================
def part3_rd_re(df, outdir):
    print(">>> Part3: R-D & R-E (A+B)")
    sub = Path(outdir) / "03_rd_re"
    ensure_dir(sub)

    enc_sw = df[df["encoder"].str.contains("x265", case=False)]
    enc_hw = df[df["encoder"].str.contains("nvenc|nvidia|hw", case=False)]

    for r in RES_ORDER:
        dr = df[df["resolution"] == r]
        if dr.empty:
            continue

        # A: combined encoder comparison
        fig, ax = plt.subplots(figsize=(7, 5))
        for enc_df, label in [(enc_sw, "x265"), (enc_hw, "NVIDIA")]:
            de = enc_df[enc_df["resolution"] == r]
            if de.empty:
                continue
            ax.scatter(de["bpp"], de["psnr_yuv"], alpha=0.4, label=label)
        ax.set_title(f"R-D @ {r} (combined)")
        ax.set_xlabel("bpp")
        ax.set_ylabel("PSNR-YUV")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(frameon=False)
        fig.savefig(sub / f"RD_combined_{r}.png")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(7, 5))
        for enc_df, label in [(enc_sw, "x265"), (enc_hw, "NVIDIA")]:
            de = enc_df[enc_df["resolution"] == r]
            if de.empty:
                continue
            ax.scatter(de["E_process_single_J"], de["psnr_yuv"], alpha=0.4, label=label)
        ax.set_title(f"R-E @ {r} (combined)")
        ax.set_xlabel("Energy (J)")
        ax.set_ylabel("PSNR-YUV")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(frameon=False)
        fig.savefig(sub / f"RE_combined_{r}.png")
        plt.close(fig)

        # B: per-encoder separate plots (with legends)
        for enc_df, label in [(enc_sw, "x265"), (enc_hw, "NVIDIA")]:
            d = enc_df[enc_df["resolution"] == r]
            if d.empty:
                continue

            # R-D single encoder
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.scatter(d["bpp"], d["psnr_yuv"], alpha=0.5,
                       label=f"{label} @ {r}")
            ax.set_title(f"R-D @ {r} ({label})")
            ax.set_xlabel("bpp")
            ax.set_ylabel("PSNR-YUV")
            ax.grid(True, linestyle="--", alpha=0.3)
            ax.legend(frameon=False)
            fig.savefig(sub / f"RD_{label}_{r}.png")
            plt.close(fig)

            # R-E single encoder
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.scatter(d["E_process_single_J"], d["psnr_yuv"], alpha=0.5,
                       label=f"{label} @ {r}")
            ax.set_title(f"R-E @ {r} ({label})")
            ax.set_xlabel("Energy (J)")
            ax.set_ylabel("PSNR-YUV")
            ax.grid(True, linestyle="--", alpha=0.3)
            ax.legend(frameon=False)
            fig.savefig(sub / f"RE_{label}_{r}.png")
            plt.close(fig)


# ===================== Part 4 =====================
def part4_model_hw(df, outdir):
    print(">>> Part4: NVIDIA Hardware Linear Modeling")
    sub = Path(outdir) / "04_modeling_hw"
    ensure_dir(sub)

    df_hw = df[df["encoder"].str.contains("nvenc|nvidia|hw", case=False)]
    y = df_hw["E_process_single_J"].values

    enc = OneHotEncoder(sparse_output=False).fit(df_hw[["resolution"]])
    res_enc = enc.transform(df_hw[["resolution"]])

    feature_sets = {
        "Time_only": df_hw[["t_process_single_s"]].values,
        "BPP_only": df_hw[["bpp"]].values,
        "QP_only": df_hw[["qp"]].values,
        "Resolution_only": res_enc,
        "Multi_feature": np.hstack([
            df_hw[["t_process_single_s", "bpp", "qp"]].values,
            res_enc,
        ]),
    }

    results = []
    for name, X in feature_sets.items():
        model = LinearRegression().fit(X, y)
        pred = model.predict(X)
        R2 = r2_score(y, pred)
        MAPE = mean_absolute_percentage_error(y, pred) * 100
        RMSE = np.sqrt(mean_squared_error(y, pred))
        results.append([name, R2, MAPE, RMSE])

        pd.DataFrame(
            {"True_Energy(J)": y, "Pred_Energy(J)": pred}
        ).to_csv(sub / f"pred_{name}.csv", index=False)

        print(f"  {name}: R2={R2:.4f}, MAPE={MAPE:.2f}%, RMSE={RMSE:.3f}")

    pd.DataFrame(
        results, columns=["Model", "R2", "MAPE(%)", "RMSE"]
    ).to_csv(sub / "hw_linear_model_summary.csv", index=False)


# ===================== Main =====================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--outdir", default="./hevc_analysis_output_v2")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    ensure_dir(args.outdir)

    print("===== Starting v2 Analysis =====")
    part1_corr(df, args.outdir)
    part2_trends(df, args.outdir)
    part3_rd_re(df, args.outdir)
    part4_model_hw(df, args.outdir)
    print("🎉 DONE - Results under:", Path(args.outdir).resolve())


if __name__ == "__main__":
    main()
