# AHCE-FL P2/P3 execution runbook — 7 November 2026

45 independent 100-round CIFAR-10 experiments: 18 P2 selection-weight cases (six policies × three seeds), followed by 27 P3 synchronization cases (three G × three δ × three seeds).

Controller: `python -u scripts/execute_priority_ablations.py`. Runs sequentially, validates 100 rounds, writes SHA-256 manifests and archival copies to `reproducibility/priority_ablations_2026_11_07`, and pushes **only campaign artifacts** to branch `research/priority-ablations-2026-11`. The original 51-run archive and manuscript are never changed.

Control: `configs/priority_generated/weights_equal_seed11.json` is the default P2 equal-weight control. Each run has a dedicated 5-round checkpoint, enabling safe resume after interruption; a rerun skips previously verified outputs. Partial or invalid final CSV/JSON triggers a stop rather than overwriting evidence.

`status.json` is the source of truth. A run is complete only after a 100-record consecutively numbered CSV, matching method/seed/configuration, final accuracy and checksums pass verification. During execution, `results/` contains transient output and model checkpoints; completed results are explicitly committed with checksums.

Mac shutdown terminates local execution. Caffeinate prevents idle sleep but **does not keep a powered-off laptop working**. Re-execute the controller to resume interrupted work after reboot; only fully verified completed cases are skipped. Do not state that 45 experiments passed until their individual audit files exist.

Resource note: CIFAR-10 full dataset (50,000 training/10,000 test), 50 clients, five edges, 100 rounds, five local epochs; all outputs are modeled simulation results rather than measured hardware/network data.

## Unattended recovery (bounded)

`zsh scripts/install_ahce_priority_launchagent.sh` installs macOS LaunchAgent `org.ahce.priority-ablations`. It checks the campaign every five minutes and resumes if the controller is absent, respecting a strict **two launches per active case** limit. When a case fails twice, the watchdog halts and records `HALTED_RETRY_LIMIT`; no algorithm, seeds, inputs, or raw measurements are ever altered to make the run pass.

The controller still runs **one case at a time** with a 5-round checkpoint. Only verified full 100-round outputs are archived and synchronized to GitHub. Transient run errors can be retried from intact local checkpoints; missing or inconsistent final outputs halt for manual review. `watchdog_state.json`, `controller.log`, `status.json`, and per-case `run_logs` reveal actual progress.

The Mac must stay powered on and logged in for LaunchAgent execution. Caffeinate reduces idle sleep, **not shutdown**. The agent automatically starts when the user logs back in after a restart.

## Five-minute live dashboard

Run `zsh scripts/install_priority_dashboard.sh` once on the Mac. LaunchAgent `org.ahce.priority-live-dashboard` serves a **read-only** local webpage at `http://127.0.0.1:8765/`, bound exclusively to the Mac loopback interface. Open this URL in a browser on the same Mac and leave the tab open. It refreshes actual status, completed runs, live round number, watchdog health and checkpoint-branch commit every **300 seconds** and also has a manual refresh button. The underlying API endpoint `/api/status` always reads current status and log files; it never edits measurements or triggers training. This is a local dashboard, not a 5-minute ChatGPT notification service.
