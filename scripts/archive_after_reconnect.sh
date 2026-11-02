#!/bin/zsh
set -eu
cd "$HOME/research/AHCE-FL"
while kill -0 16709 2>/dev/null; do sleep 120; done
grep -q 'SENSITIVITY_DONE' logs/sensitivity_resume_sequence.log || exit 2
mkdir -p reproducibility/cifar10_sensitivity
cp configs/generated/cifar10_*.json reproducibility/cifar10_sensitivity/
cp results/cifar10_*_cifar10_ahce-fl_seed*.csv reproducibility/cifar10_sensitivity/
cp results/cifar10_*_cifar10_ahce-fl_seed*.json reproducibility/cifar10_sensitivity/
python3 - <<'PY'
from pathlib import Path
import csv,json,hashlib
p=Path('reproducibility/cifar10_sensitivity')
f=sorted(p.glob('*.csv'))
assert len(f)==24,len(f)
out=[]
for x in f:
 r=list(csv.DictReader(x.open()))
 assert len(r)==100 and int(r[-1]['round'])==100,x
 out.append(dict(run=x.stem,accuracy=float(r[-1]['accuracy']),total_bytes=sum(int(y['total_bytes']) for y in r),syncs=sum(int(y['sync_triggered']) for y in r)))
(p/'metrics.json').write_text(json.dumps(out,indent=2))
(p/'README.md').write_text('# Full 100-round CIFAR-10 compression and synchronization sensitivities\n24 runs, seeds 11, 23, 42. Communication is modeled payload bytes.\n')
(p/'SHA256SUMS.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in p.iterdir() if x.is_file() and x.name!='SHA256SUMS.json'},indent=2))
print('VERIFIED',len(f))
PY
git add reproducibility/cifar10_sensitivity
git commit -m 'Sync complete 24-run sensitivity study with verification'
git push origin main
echo 'SYNC_DONE'
