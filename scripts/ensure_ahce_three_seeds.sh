#!/bin/zsh
set -u
cd "$HOME/research/AHCE-FL" || exit 1
export PYTHONUNBUFFERED=1
echo "START $(date -u '+%FT%TZ') watchdog=$$"
while kill -0 44080 2>/dev/null; do
  echo "WAIT $(date -u '+%FT%TZ') existing 15-run runner active"
  sleep 120
done
echo "BATCH EXITED $(date -u '+%FT%TZ')"
for seed in 11 23 42; do
  echo "RUN_OR_SKIP seed=$seed $(date -u '+%FT%TZ')"
  .venv/bin/python -m ahce.full_validation --seeds "$seed" --methods ahce-fl || exit 2
done
echo "ANALYSIS $(date -u '+%FT%TZ')"
.venv/bin/python -m ahce.statistics --output results/analysis_summary.json || exit 3
echo "COMPLETE $(date -u '+%FT%TZ')"
