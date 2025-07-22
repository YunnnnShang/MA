#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from scipy.stats import t
from pathlib import Path

RAW_DATA_CSV = Path("raw_core_energy_measurements.csv")
RAPL_MAX_ENERGY_FILE = Path("/sys/class/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:0/max_energy_range_uj")
ITERATION_LIMIT = 15   

# CI parameters
CONF_PROBABILITY = 0.99   # 99% confidence interval
INTERVAL_PART   = 0.02    # Convergence threshold: 2% mean
MIN_MEASUREMENTS = 5      # Minimum number of samples for convergence judgment
MAX_ITERATIONS   = 15     # Maximum iterations for convergence

def calculate_energy(prev_uJ: int, curr_uJ: int, max_range_uJ: int) -> float:
    """
    Handle RAPL overflow and convert microjoules to joules
    """
    if curr_uJ < prev_uJ:
        used = max_range_uJ - prev_uJ + curr_uJ
    else:
        used = curr_uJ - prev_uJ
    return used / 1e6

def find_stable_energy_fullset(energies,
                               conf_prob=CONF_PROBABILITY,
                               interval_part=INTERVAL_PART,
                               min_measurements=MIN_MEASUREMENTS,
                               max_iter=MAX_ITERATIONS):
    """
    Full sample CI convergence test + outlier removal
      1) Calculate mean/std of the current sample list
      2) Compute CI width = std/√n * t_{α}(n-1)
      3) If width < threshold (2%*mean), convergence is achieved
      4) Otherwise, if n > 9, remove outliers based on 0.75–1.25× median and repeat
    Returns: (mean after convergence, number of samples used for convergence)
    """
    current = list(energies)
    n = len(current)
    if n < min_measurements:
        return np.mean(current), n

    for _ in range(max_iter):
        n = len(current)
        mean_e = np.mean(current)
        std_e  = np.std(current, ddof=1)
        if std_e == 0:
            return mean_e, n

        t_val = t.ppf((1 + conf_prob) / 2, df=n-1)
        ci_width = (std_e / np.sqrt(n)) * t_val

        if ci_width < interval_part * mean_e:
            return mean_e, n

        if n > 9:
            med = np.median(current)
            lo, hi = 0.75 * med, 1.25 * med
            current = [e for e in current if lo < e < hi]
        else:
            break

    return np.mean(current), len(current)

def main():
    if not RAW_DATA_CSV.exists():
        print(f"Error: cannot find {RAW_DATA_CSV}")
        return
    try:
        max_range = int(RAPL_MAX_ENERGY_FILE.read_text())
    except Exception as e:
        print(f"Error reading max energy range: {e}")
        return

    # Read raw data and calculate energy consumption (J)
    df = pd.read_csv(RAW_DATA_CSV)
    df['Core_Energy_J'] = df.apply(
        lambda r: calculate_energy(r['RAPL_Core_Before_uJ'],
                                   r['RAPL_Core_After_uJ'],
                                   max_range),
        axis=1)

    results = []
    for (video, qp, preset), grp in df.groupby(['VideoName', 'QP', 'Preset']):
        energies = grp['Core_Energy_J'].tolist()
        stable_mean, iterations = find_stable_energy_fullset(energies)
        exceeded = iterations > ITERATION_LIMIT
        results.append({
            'VideoName': video,
            'QP': int(qp),
            'Preset': preset,
            'stable_energy_joules': stable_mean,
            'iterations_needed': iterations,
            'exceeded_limit': exceeded
        })

    out_df = pd.DataFrame(results)
    print("\nDetailed CI convergence results:")
    print(out_df.to_string(index=False))

    # Save to CSV
    out_df.to_csv('ci_iterations_detail.csv', index=False)
    print("\nResults saved to ci_iterations_detail.csv")

if __name__ == "__main__":
    main()