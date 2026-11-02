#!/bin/zsh
set -eu
cd "$HOME/research/AHCE-FL"
while pgrep -f 'python -m ahce.sensitivity --mode compression' >/dev/null || pgrep -f 'python -m ahce.sensitivity --mode synchronization' >/dev/null || pgrep -f 'scripts/sensitivity_sequence.sh' >/dev/null; do
 echo "WAIT $(date -u '+%FT%TZ')"
 sleep 120
done
grep -q 'Sensitivity complete' logs/sensitivity_compression.log || { echo COMPRESSION_NOT_COMPLETE; exit 2; }
grep -q 'Sensitivity complete' logs/sensitivity_sequence.log || { echo SYNCHRONIZATION_NOT_COMPLETE; exit 3; }
mkdir -p reproducibility/cifar10_sensitivity
cp configs/generated/cifar10_*.json reproducibility/cifar10_sensitivity/
cp results/cifar10_*_cifar10_ahce-fl_seed*.csv reproducibility/cifar10_sensitivity/
cp results/cifar10_*_cifar10_ahce-fl_seed*.json reproducibility/cifar10_sensitivity/
python3 - <<'PY'
from pathlib import Path
import csv,hashlib,json
root=Path('reproducibility/cifar10_sensitivity')
csvs=list(root.glob('*.csv'))
assert len(csvs)==24, f'Expected 24 sensitivity runs, found {len(csvs)}'
rows=[]
for path in sorted(csvs):
 data=list(csv.DictReader(path.open()))
 assert len(data)==100 and int(data[-1]['round'])==100, path
 rows.append(dict(run=path.stem,final_accuracy=float(data[-1]['accuracy']),total_bytes=sum(int(x['total_bytes']) for x in data),sync_count=sum(int(x['sync_triggered']) for x in data)))
(root/'metrics.json').write_text(json.dumps(rows,indent=2)+'\n')
(root/'README.md').write_text('# CIFAR-10 sensitivity\n\nFull-data 100-round compression and synchronization ablations for seeds 11, 23 and 42. All 24 complete CSV files and companion provenance JSON are included. Accuracy and bytes are recorded in metrics.json. No fabricated or missing runs. Communication represents modeled payload bytes.\n')
(root/'SHA256SUMS.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file() and x.name!='SHA256SUMS.json'},indent=2)+'\n')
print('ARCHIVED',len(csvs))
PY
git add reproducibility/cifar10_sensitivity && git commit -m 'Archive 24 verified CIFAR-10 sensitivity runs and provenance'
git push origin main
echo "ARCHIVE_COMPLETE $(date -u '+%FT%TZ')"
