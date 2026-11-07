# AHCE-FL priority-gated execution workflow

**Source of truth:** Archived CIFAR-10 CSVs and experiment JSONs remain immutable. Every new run is assigned its own configuration, seed, output prefix and evidence record.

## Gate P1 — Provenance (mandatory)

Run: `python scripts/priority_workflow.py --stage audit`.

- Checks 15 baseline run identifiers and 100-round CSV coverage.
- Produces `reports/priority_workflow/P1_PROVENANCE_SIDECAR.json` identifying the 12 original comparator metadata inconsistencies, with source SHA-256 hashes.
- The legacy experiment JSONs are **not rewritten**. The verified top-level comparator name and raw CSV provide the analytical assignment.
- A provenance **sidecar is an accounting correction**, not a retroactive re-execution.

## Gate P2 — Selection weights (planned, not run)

Run `python scripts/priority_workflow.py --stage plan` to create 18 independent configurations: six resource-weight policies (equal, bandwidth-, energy-, accuracy-, latency- and compute-heavy), each with seeds 11, 23 and 42. Fixed: CIFAR-10, 100 rounds, 50 clients, five edges, 10 participants per round, five local epochs, and tau 0.01.

Each generated file can be executed deliberately from the repository root:

```bash
python -m ahce.train --config configs/priority_generated/weights_bandwidth_seed11.json --method ahce-fl --seed 11 --tau 0.01
```

Repeat for all planned cases with resource monitoring, verify 100 sequential rounds per CSV, and archive outputs under distinct paths. Do not combine seedwise differences until all paired settings are valid. Weight sensitivity is not yet established.

## Gate P3 — Joint synchronization (planned, not run)

The generated 27 configurations cross maximum gaps `{1,3,5}`, divergence thresholds `{0.05,0.5,1e9}`, and three paired seeds. The `1e9` threshold is a timer-isolation control, not an adaptive threshold. Record `sync_reason` at every round and verify divergence events separately.

Example:

```bash
python -m ahce.train --config configs/priority_generated/gap3_delta0.5_seed11.json --method ahce-fl --seed 11 --tau 0.01
```

No superiority, causality or hardware performance claims follow until the new results are inspected.

## Gate P4 — Communication and statistics (mandatory)

The priority audit recalculates flat-baseline transfers (308,560,000 modeled bytes) from client upload/download columns and explicitly isolates the duplicated cloud entries (another 308,560,000). The older report's 617,120,000-byte flat total is historical and **must not** silently replace the manuscript ledger. The independent manuscript audit compares all 51 archived runs and Tables 4–9, including paired confidence intervals and p-values.

## Gate P5 — Figure audit (human review pending)

The automated preflight hashes manuscript and numerical source files, but **does not claim a visual figure verification**. Each of nine figures needs a panel-by-panel check of axes, error bars, plotted values, caption alignment, and image resolution.

## Gate P6 — External robustness (future, separately budgeted)

Broader datasets/architectures/seeds, real hardware, packet traces, measured power, and implementation-level privacy/security are additional experiments. Do not treat simulated modeled bytes or critical-path estimates as physical observations.

## Automated GitHub workflow

`.github/workflows/research-priority-gates.yml` runs audit gates on changes to analysis/implementation and permits explicit `workflow_dispatch` execution of `audit`, `plan`, or `all-preflight`. Artifacts include a status manifest; no expensive training starts automatically, and the workflow never commits raw experiment changes.

**Acceptance criteria:** P1/P4 audit tests pass, provenance inconsistencies stay disclosed, P2/P3 are labelled *planned* until executed, P5/P6 remain pending until independently validated. The baseline result (FedAvg > AHCE-FL accuracy; lower modeled FedAvg payload) is retained.
