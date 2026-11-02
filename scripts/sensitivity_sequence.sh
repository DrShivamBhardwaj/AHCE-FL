#!/bin/zsh
set -eu
cd "$HOME/research/AHCE-FL"
while pgrep -f 'python -m ahce.sensitivity --mode compression' >/dev/null; do
 echo "WAIT_COMPRESSION $(date -u '+%FT%TZ')"
 sleep 120
done
if ! grep -q 'Sensitivity complete' logs/sensitivity_compression.log; then
 echo 'COMPRESSION_NOT_COMPLETE'; exit 2
fi
.venv/bin/python -m ahce.sensitivity --mode synchronization --seeds 11 23 42
