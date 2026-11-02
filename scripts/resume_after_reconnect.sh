#!/bin/zsh
set -eu
cd "$HOME/research/AHCE-FL"
while kill -0 16611 2>/dev/null; do
 echo "WAIT compression $(date -u '+%FT%TZ')"
 sleep 120
done
grep -q 'Sensitivity complete' logs/sensitivity_compression_resume.log || { echo 'COMPRESSION FAILED'; exit 2; }
echo "START synchronization $(date -u '+%FT%TZ')"
.venv/bin/python -m ahce.sensitivity --mode synchronization --seeds 11 23 42
echo "SENSITIVITY_DONE $(date -u '+%FT%TZ')"
