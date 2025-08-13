import os
import pandas as pd
import matplotlib.pyplot as plt

# === Configure paths ===
csv_dir = "psnr_logs"
output_dir = "psnr_plots"
os.makedirs(output_dir, exist_ok=True)

# === Get all *_frame.csv files ===
csv_files = [f for f in os.listdir(csv_dir) if f.endswith("_frame.csv")]

# === Extract all QP and Preset mappings ===
qp_map = {}
for fname in csv_files:
    try:
        name = fname.replace("_frame.csv", "")  # e.g. qp22_fast
        qp, preset = name.split("_", 1)
        qp_map.setdefault(qp, []).append(preset)
    except ValueError:
        print(f"[WARNING] Unexpected file format: {fname}")

# === Main plotting loop ===
for qp, presets in sorted(qp_map.items(), key=lambda x: int(x[0][2:])):  # Sort by qp in ascending order
    n = len(presets)
    n = len(presets)
    fig, axes = plt.subplots(n, 3, figsize=(15, n * 2.8))
    fig.suptitle(f"Frame-wise PSNR Curves (QP={qp})", fontsize=18)

    for i, preset in enumerate(sorted(presets)):
        fname = f"{qp}_{preset}_frame.csv"
        fpath = os.path.join(csv_dir, fname)

        try:
            df = pd.read_csv(fpath)
            df.columns = df.columns.str.strip()

            # Additional debug information
            print(f"[INFO] Reading: {fname} -> shape: {df.shape}")

            if not all(col in df.columns for col in ["Y PSNR", "U PSNR", "V PSNR"]):
                raise ValueError("Missing PSNR columns")

            frames = df.index
            y_psnr = pd.to_numeric(df["Y PSNR"], errors="coerce")
            u_psnr = pd.to_numeric(df["U PSNR"], errors="coerce")
            v_psnr = pd.to_numeric(df["V PSNR"], errors="coerce")

            psnr_data = [y_psnr, u_psnr, v_psnr]
            colors = ["blue", "orange", "green"]
            labels = ["Y PSNR", "U PSNR", "V PSNR"]

            for j in range(3):
                ax = axes[i][j] if n > 1 else axes[j]
                ax.plot(frames, psnr_data[j], color=colors[j])
                ax.set_title(f"{preset} - {labels[j]}", fontsize=10)
                ax.set_ylabel("PSNR (dB)")
                ax.set_xlabel("Frame Index")
                ax.grid(True)

                # === Force y-axis to start from 0 ===
                ax.set_ylim(0, 60)  # Adjust upper limit as needed based on data distribution

        except Exception as e:
            print(f"[ERROR] Failed to process {fname}: {e}")
            for j in range(3):
                ax = axes[i][j] if n > 1 else axes[j]
                ax.axis("off")
                ax.set_title(f"{preset} - Error", fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_file = os.path.join(output_dir, f"{qp}_psnr_curves.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"[OK] Saved: {out_file}")
