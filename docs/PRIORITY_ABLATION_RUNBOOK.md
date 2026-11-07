# AHCE-FL P2/P3 execution runbook — 7 November 2026

45 independent 100-round CIFAR-10 experiments: 18 P2 selection-weight cases (six policies × three seeds), followed by 27 P3 synchronization cases (three G × three δ × three seeds).

Controller: `python -u scripts/execute_priority_ablations.py`. Runs sequentially, validates 100 rounds, writes SHA-256 manifests and archival copies to `reproducibility/priority_ablations_2026_11_07`, and pushes **only campaign artifacts** to branch `research/priority-ablations-2026-11`. The original 51-run archive and manuscript are never changed.

Control: `configs/priority_generated/weights_equal_seed11.json` is the default P2 equal-weight control. Each run has a dedicated 5-round checkpoint, enabling safe resume after interruption; a rerun skips previously verified outputs. Partial or invalid final CSV/JSON triggers a stop rather than overwriting evidence.

`status.json` is the source of truth. A run is complete only after a 100-record consecutively numbered CSV, matching method/seed/configuration, final accuracy and checksums pass verification. During execution, `results/` contains transient output and model checkpoints; completed results are explicitly committed with checksums.

Mac shutdown terminates local execution. Caffeinate prevents idle sleep but **does not keep a powered-off laptop working**. Re-execute the controller to resume interrupted work after reboot; only fully verified completed cases are skipped. Do not state that 45 experiments passed until their individual audit files exist.

Resource note: CIFAR-10 full dataset (50,000 training/10,000 test), 50 clients, five edges, 100 rounds, five local epochs; all outputs are modeled simulation results rather than measured hardware/network data.
