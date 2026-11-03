#!/bin/zsh
set -eu
cd "$HOME/research/AHCE-FL"
mkdir -p logs
if [ -f reproducibility/revision_analysis/FINALIZED.json ]; then
 echo "ALREADY_FINALIZED"
 exit 0
fi
complete=$(.venv/bin/python - <<'PY'
from pathlib import Path
import csv
count=0
for p in Path('reproducibility/sync_corrected').glob('cifar10_sync_corrected_*seed*.csv'):
 try:
  with p.open() as h:
   rows=list(csv.DictReader(h))
  if len(rows)==100 and int(rows[-1]['round'])==100:count+=1
 except Exception:pass
print(count)
PY
)
echo "CORRECTED_COMPLETE $complete/12"
if [ "$complete" -ne 12 ]; then
 exit 0
fi
.venv/bin/python scripts/analyze_revision.py
.venv/bin/python - <<'PY'
import json,datetime,hashlib
from pathlib import Path
p=Path('reproducibility/revision_analysis')
s=json.loads((Path('reproducibility/sync_corrected')/'gap_summary.json').read_text())
counts=[v['mean_sync_count'] for v in s.values()]
if len(set(counts))!=4:raise SystemExit('Four gaps did not yield distinct synchronization counts')
data={'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'corrected_run_count':12,'sync_counts':s,'scope':'simulated CIFAR-10 experiments, modeled payload bytes'}
(p/'FINALIZED.json').write_text(json.dumps(data,indent=2)+'\n')
hashes={}
for folder in ('reproducibility/cifar10_sensitivity','reproducibility/sync_corrected','reproducibility/revision_analysis'):
 for f in sorted(Path(folder).glob('*')):
  if f.is_file() and f.name!='SHA256SUMS.json':
   hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
(p/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')
PY
git add ahce/train.py scripts/unattended_revision.py scripts/analyze_revision.py scripts/finalize_revision.sh scripts/sync_every_30min.sh reproducibility/sync_corrected reproducibility/revision_analysis
git add configs/generated/cifar10_sync_corrected_gap_*.json
if ! git diff --cached --quiet; then
 git commit -m 'Archive corrected synchronization ablation and statistical analysis'
fi
git push origin main
scripts/sync_every_30min.sh
echo FINALIZED_AND_SYNCED
