"""Reproducible corrected synchronization ablation and evidence extraction.
Single-worker, resumable training with per-round atomic model-state checkpoints.
All communication figures are modeled bytes, not observed packets.
"""
import csv
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
os.chdir(BASE)
ROOT = Path("reproducibility/sync_corrected")
RAW = Path("results")
CONFIGS = Path("configs/generated")
SEEDS = (11, 23, 42)
GAPS = (1, 2, 3, 5)
ROOT.mkdir(parents=True, exist_ok=True)
CONFIGS.mkdir(exist_ok=True)
RAW.mkdir(exist_ok=True)
base = json.loads(Path("configs/manuscript_cifar10.json").read_text())


def valid(path):
    if not path.exists():
        return False
    try:
        with path.open(newline="") as h:
            rows = list(csv.DictReader(h))
        return len(rows) == 100 and int(rows[-1]["round"]) == 100
    except (ValueError, OSError, KeyError):
        return False


def refresh():
    summary = []
    for gap in GAPS:
        for seed in SEEDS:
            prefix = f"cifar10_sync_corrected_gap_{gap}_cifar10_ahce-fl_seed{seed}_tau0.01"
            file = RAW / f"{prefix}.csv"
            if not valid(file):
                continue
            with file.open(newline="") as h:
                rows = list(csv.DictReader(h))
            for metric in ("sync_triggered", "total_bytes", "accuracy", "divergence_l2"):
                if metric not in rows[-1]:
                    raise RuntimeError("Missing required telemetry field " + metric)
            summary.append({
                "gap": gap, "seed": seed, "accuracy": float(rows[-1]["accuracy"]),
                "modeled_total_bytes": sum(int(r["total_bytes"]) for r in rows),
                "sync_count": sum(int(r["sync_triggered"]) for r in rows),
                "sync_reasons": {reason: sum(r["sync_reason"] == reason for r in rows)
                                 for reason in ("both", "max_gap", "divergence", "held")},
                "divergence_min": min(float(r["divergence_l2"]) for r in rows),
                "divergence_max": max(float(r["divergence_l2"]) for r in rows),
                "csv": file.name,
            })
            (ROOT / file.name).write_bytes(file.read_bytes())
            j = file.with_suffix(".json")
            if j.exists():
                (ROOT / j.name).write_bytes(j.read_bytes())
    (ROOT / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n")
    (ROOT / "progress.json").write_text(json.dumps({
        "completed": len(summary), "planned": 12,
        "checkpoint_type": "atomic torch model state per round",
        "threshold_used": 1e9,
        "objective": "isolate maximum synchronization gap independently of divergence trigger",
        "execution_note": "No real networking is measured",
    }, indent=2) + "\n")
    # Detect whether the configured gap actually affects the controlled experiment.
    grouped = defaultdict(list)
    for row in summary:
        grouped[row["gap"]].append(row)
    if len(grouped) == 4 and all(len(v) == 3 for v in grouped.values()):
        by_gap = {str(gap): {
            "mean_accuracy": sum(x["accuracy"] for x in rows) / len(rows),
            "mean_sync_count": sum(x["sync_count"] for x in rows) / len(rows),
            "mean_modeled_total_bytes": sum(x["modeled_total_bytes"] for x in rows) / len(rows),
        } for gap, rows in sorted(grouped.items())}
        (ROOT / "gap_summary.json").write_text(json.dumps(by_gap, indent=2) + "\n")
        syncs = [v["mean_sync_count"] for v in by_gap.values()]
        if len(set(syncs)) == 1:
            raise RuntimeError("FAILED: corrected synchronization gaps still produce identical counts")
    return len(summary)


def run():
    print("START", time.strftime("%Y-%m-%d %H:%M:%S"), flush=True)
    print("CODE", subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip(), flush=True)
    for gap in GAPS:
        for seed in SEEDS:
            name = f"cifar10_sync_corrected_gap_{gap}"
            filename = CONFIGS / f"{name}.json"
            checkpoint = RAW / "checkpoints" / f"{name}_seed{seed}_tau0.01.pt"
            cfg = dict(base)
            cfg["sync_max_gap"] = gap
            cfg["sync_threshold"] = 1e9
            cfg["checkpoint_every"] = 1
            cfg["checkpoint_path"] = str(checkpoint)
            filename.write_text(json.dumps(cfg, indent=2) + "\n")
            prefix = f"{name}_cifar10_ahce-fl_seed{seed}_tau0.01"
            output = RAW / f"{prefix}.csv"
            if valid(output):
                print("SKIP_COMPLETE", gap, seed, flush=True)
                refresh()
                continue
            for attempt in range(1, 4):
                print("RUN", gap, seed, "attempt", attempt, flush=True)
                p = subprocess.run([sys.executable, "-u", "-m", "ahce.train",
                                    "--config", str(filename), "--method", "ahce-fl",
                                    "--seed", str(seed), "--tau", "0.01"])
                if p.returncode == 0 and valid(output):
                    break
                print("RETRY", gap, seed, "exit", p.returncode, flush=True)
                time.sleep(10)
            else:
                raise RuntimeError(f"Run failed after three attempts: gap {gap}, seed {seed}")
            print("COMPLETE", gap, seed, "count", refresh(), flush=True)
            # An immediate snapshot helps if shutdown occurs before the next timer tick.
            s = subprocess.run(["/bin/zsh", "scripts/sync_every_30min.sh"])
            print("SNAPSHOT_RETURN_CODE", s.returncode, flush=True)
    print("FINISHED_ALL", refresh(), flush=True)
    p = subprocess.run(["/bin/zsh", "scripts/sync_every_30min.sh"])
    if p.returncode:
        raise RuntimeError("Final snapshot upload failed")
    print("ALL_CORRECTED_RUNS_DONE", flush=True)


if __name__ == "__main__":
    run()
