# **Section 7 – Conclusion and Future Work**

This work established a unified two-phase framework for **energy modeling of HEVC intra-coding** by bridging *software-level simulation* and *hardware-level measurement*.  
The study combined deterministic insights from **Valgrind (Callgrind)** with real microarchitectural data from **Perf (HPC)**, thereby linking algorithmic behavior with physical energy consumption.

---

## **7.1 Conclusions**

### **(1) Phase 4 – Valgrind: Platform-Independent Simulation**

In **Phase 4**, the x265 encoder was profiled under two filter configurations—**Default-like** (Deblock on, SAO off) and **Hardware-like** (SAO on, Deblock off)—using *Callgrind* to record 13 processor-event counters that characterize instruction flow, cache activity, and branch behavior.  
Each software experiment was precisely matched to the corresponding **hardware-measured energy (Eₕw, slow)** by sequence name, QP, and preset, ensuring one-to-one energy labeling without missing data.

Linear regression models were trained to estimate hardware energy from these processor events.  
Despite the inherent abstraction of DBI-based simulation, the models achieved **MAPE < 5 %** across most presets, confirming that Valgrind’s deterministic instruction-level traces capture sufficient structural information to approximate real energy behavior.  
The analysis revealed that the **Hardware-like configuration** exhibits smoother and more predictable micro-architectural patterns—lower branch mispredictions and better data locality—while the **Default-like configuration** introduces higher irregularity due to Deblocking, which increases branch divergence and cache-miss variance.

---

### **(2) Phase 5 – Perf: Hardware-Level Cross-Validation**

In **Phase 5**, the methodology was extended from simulation to real hardware measurement through **Linux Perf**, capturing the *18-event Perf Extended* set consistent with *Kränzler et al. (2023)*.  
This phase validated whether Valgrind-derived trends persist under real PMU observations on Intel and AMD architectures.

The results confirmed cross-phase consistency:  
- Deblocking (Default-like) increased **branch-misses** and **L1-dcache-load-misses**, raising energy variance and nonlinearity.  
- SAO on (Hardware-like) maintained more regular execution and stronger linear correlation with energy.  

Linear regression achieved **MAPE ≈ 12 %** for Hardware-like and **≈ 30 %** for Default-like configurations.  
Although XGBoost further reduced error in high-variance cases, the linear models were preferred for interpretability and methodological clarity.  
Collectively, Phases 4 and 5 demonstrate that **processor-event-based energy estimation is both conceptually sound and empirically transferable** from deterministic software simulation to physical hardware execution.

---

### **(3) Cross-Phase Insights**

| Aspect | Phase 4 (Callgrind) | Phase 5 (Perf HPC) | Consistency |
|:--|:--|:--|:--|
| Measurement Layer | Software Simulation | Hardware Counters | Complementary |
| Observed Effect | Deblocking ↑ Branch-Miss / Cache-Miss | Same Trend Observed on CPU PMU | ✓ |
| Modeling Error (MAPE) | < 5 % | 12 % – 30 % | Order-of-Magnitude Preserved |
| Interpretability | Deterministic, Algorithmic | Realistic, Micro-architectural | ✓ |

The two phases together form a closed analytical loop: *algorithmic complexity → micro-architectural behavior → energy response*.  
This dual-layer validation strengthens the reliability and reproducibility of processor-event-based energy modeling.

---

## **7.2 Future Work – Toward Phase 6 (Closed-Loop Hardware Validation)**

While the present study concludes at Phase 5, a natural next step—**Phase 6**—is envisaged as *closed-loop validation* via **direct hardware power measurement**.  
Future efforts may integrate instruments such as **Intel RAPL** or **ZES LMG611** to capture real-time power traces from CPU and NVENC pipelines, thereby establishing a tri-level correspondence among:

1. **Instruction-Level Simulation** (Valgrind – Phase 4);  
2. **Microarchitectural Measurement** (Perf – Phase 5); and  
3. **Physical Power Observation** (Prospective Phase 6).

This integration would quantify residual bias between software proxies and physical energy, improve cross-hardware generalization (CPU ↔ GPU ↔ ASIC), and enable ratio-based feature engineering (e.g., IPC, Cache-Miss Rate) for dynamic energy modeling.  
Additionally, fine-grained temporal profiling could reveal transient power dynamics across encoder stages (intra prediction, transform, loop filters).

---

## **7.3 Final Remarks**

The presented two-phase framework provides a rigorous, reproducible foundation for **energy-aware video encoder analysis**.  
It unifies deterministic simulation with empirical measurement, demonstrating that *software-visible processor events* can reliably approximate *hardware energy behavior*.  
The proposed Phase 6 remains a prospective extension—not a missing piece—but a strategic path toward full hardware-validated, architecture-independent energy modeling.

---
