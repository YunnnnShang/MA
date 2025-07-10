import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# --- Configuration ---
# Set the base directory where 'thesis_results' is located
# For example, if your structure is /home/or16ixuv/thesis_results/..., then BASE_DIR = '/home/or16ixuv/'
BASE_DIR = '/home/or16ixuv/' 

# List of video sequences to process
# Ensure these names exactly match your folder names under thesis_results
VIDEO_SEQUENCES = [
    'BoxingPractice_3840x2160_5994fps_8bit_420.yuv',
    'ControlledBurn_1280x720p30_420.yuv'
]

# List of QPs and Presets to analyze from your file structure
QPS = [22, 27, 32, 37]
PRESETS = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow', 'placebo']

# --- Functions ---

def load_and_process_csv(filepath):
    """Loads a CSV file, cleans column names, and calculates average PSNRs."""
    try:
        df = pd.read_csv(filepath)
        # Clean column names by stripping whitespace
        df.columns = df.columns.str.strip()

        # Ensure PSNR columns are numeric
        for col in ['Y PSNR', 'U PSNR', 'V PSNR']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                print(f"Warning: Column '{col}' not found in {filepath}. Skipping PSNR calculation for this column.")
                return None

        # Calculate average PSNRs
        avg_psnr_y = df['Y PSNR'].mean()
        avg_psnr_u = df['U PSNR'].mean()
        avg_psnr_v = df['V PSNR'].mean()

        return avg_psnr_y, avg_psnr_u, avg_psnr_v
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def plot_psnr_vs_qp(data_by_preset, video_sequence_name, output_dir):
    """
    Plots PSNR (Y, U, V) vs. QP for each preset.
    data_by_preset: Dictionary where keys are preset names and values are DataFrames
                    containing 'QP', 'Avg_Y_PSNR', 'Avg_U_PSNR', 'Avg_V_PSNR'.
    """
    if not data_by_preset:
        print(f"No data to plot for {video_sequence_name}.")
        return

    # Create output directory for plots if it doesn't exist
    plots_output_dir = os.path.join(output_dir, 'psnr_plots')
    os.makedirs(plots_output_dir, exist_ok=True)

    for preset_name, preset_df in data_by_preset.items():
        if preset_df.empty:
            print(f"No data for preset {preset_name} in {video_sequence_name}. Skipping plot.")
            continue

        # Sort by QP for correct plotting order
        preset_df = preset_df.sort_values(by='QP')

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(preset_df['QP'], preset_df['Avg_Y_PSNR'], marker='o', linestyle='--', label='PSNR_Y')
        ax.plot(preset_df['QP'], preset_df['Avg_U_PSNR'], marker='o', linestyle='--', label='PSNR_U')
        ax.plot(preset_df['QP'], preset_df['Avg_V_PSNR'], marker='o', linestyle='--', label='PSNR_V')

        ax.set_title(f'Average PSNR vs. QP for {video_sequence_name}\nPreset: {preset_name}')
        ax.set_xlabel('Quantization Parameter (QP)')
        ax.set_ylabel('Average PSNR (dB)')
        ax.set_xticks(QPS) # Ensure only the specified QPs are shown on the x-axis
        ax.grid(True, linestyle=':', alpha=0.7)
        ax.legend()
        plt.tight_layout()

        plot_filename = os.path.join(plots_output_dir, f'{video_sequence_name}_preset_{preset_name}_psnr_vs_qp.png')
        plt.savefig(plot_filename)
        plt.close(fig)
        print(f"Plot saved: {plot_filename}")

# --- Main Processing Loop ---

if __name__ == "__main__":
    print(f"Starting PSNR analysis from base directory: {BASE_DIR}")

    for video_seq in VIDEO_SEQUENCES:
        print(f"\nProcessing video sequence: {video_seq}")
        video_logs_dir = os.path.join(BASE_DIR, 'thesis_results', video_seq, 'psnr_logs')
        
        # Dictionary to store data for plotting per preset
        # { 'preset_name': pd.DataFrame({'QP':[], 'Avg_Y_PSNR':[], ...}) }
        all_data_for_plotting = {preset: pd.DataFrame(columns=['QP', 'Avg_Y_PSNR', 'Avg_U_PSNR', 'Avg_V_PSNR']) for preset in PRESETS}

        for qp in QPS:
            for preset in PRESETS:
                csv_filename = f'qp{qp}_{preset}_frame.csv'
                csv_filepath = os.path.join(video_logs_dir, csv_filename)

                psnr_data = load_and_process_csv(csv_filepath)
                if psnr_data:
                    avg_y, avg_u, avg_v = psnr_data
                    
                    # Append new row to the DataFrame for the current preset
                    new_row_df = pd.DataFrame([{
                        'QP': qp,
                        'Avg_Y_PSNR': avg_y,
                        'Avg_U_PSNR': avg_u,
                        'Avg_V_PSNR': avg_v
                    }])
                    all_data_for_plotting[preset] = pd.concat([all_data_for_plotting[preset], new_row_df], ignore_index=True)
                else:
                    print(f"Could not process {csv_filepath}. Skipping data for this combination.")
        
        # Plot results for the current video sequence
        print(f"\nGenerating plots for {video_seq}...")
        plot_psnr_vs_qp(all_data_for_plotting, video_seq, video_logs_dir)
    
    print("\nAnalysis complete.")