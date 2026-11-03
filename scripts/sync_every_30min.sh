#!/bin/zsh
# Runs on the Mac. Checkpoints RESULTS and LOGS; running model state is not captured.
set -eu
source_root="$HOME/research/AHCE-FL"
mirror="$HOME/research/AHCE-FL-checkpoint-sync"
branch="checkpoints/sensitivity-30min"
cd "$source_root"
if [ ! -d "$mirror/.git" ]; then
  git clone --quiet "$source_root" "$mirror"
fi
cd "$mirror"
git remote set-url origin https://github.com/DrShivamBhardwaj/AHCE-FL.git
if ! git show-ref --verify --quiet "refs/heads/$branch"; then
  if git ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
    git fetch --quiet origin "$branch"
    git checkout -q -b "$branch" "origin/$branch"
  else
    git checkout -q -b "$branch"
  fi
fi
git checkout -q "$branch"
if git ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
  git pull --ff-only --quiet origin "$branch"
fi
dest="$mirror/reproducibility/periodic_sensitivity"
mkdir -p "$dest/complete_runs" "$dest/configs" "$dest/logs"
find "$source_root/results" -maxdepth 1 -type f \( -name 'cifar10_compression_*_cifar10_ahce-fl_seed*.csv' -o -name 'cifar10_compression_*_cifar10_ahce-fl_seed*.json' -o -name 'cifar10_synchronization_*_cifar10_ahce-fl_seed*.csv' -o -name 'cifar10_synchronization_*_cifar10_ahce-fl_seed*.json' \) -exec cp -p {} "$dest/complete_runs/" \;
find "$source_root/configs/generated" -maxdepth 1 -type f -name 'cifar10_*.json' -exec cp -p {} "$dest/configs/" \;
for name in sensitivity_compression_resume.log sensitivity_resume_sequence.log; do
  [ ! -f "$source_root/logs/$name" ] || cp "$source_root/logs/$name" "$dest/logs/$name"
done
python3 - "$dest" <<'PY'
from pathlib import Path
import csv,hashlib,json,sys,datetime
p=Path(sys.argv[1])
valid=[]
for f in sorted((p/'complete_runs').glob('*.csv')):
 with f.open(newline='') as h:
  rows=list(csv.DictReader(h))
 if len(rows)!=100 or int(rows[-1].get('round',-1))!=100:
  raise SystemExit('INCOMPLETE CSV treated as complete: '+str(f))
 valid.append(f.name)
 partial={}
for name in ['sensitivity_compression_resume.log','sensitivity_resume_sequence.log']:
 path=p/'logs'/name
 if path.exists():
  events=[]
  for line in path.read_text(errors='replace').splitlines():
   if line.startswith('{"method"'):
    try:events.append(json.loads(line))
    except json.JSONDecodeError:pass
  partial[name]={'latest_round_in_log':events[-1].get('round') if events else None,'events_in_log':len(events)}
 summary={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'completed_sensitivity_runs':len(valid),'files':valid,
          'logs':partial,'training_model_state_checkpointed':False,
          'resume_note':'Complete runs are reusable. A partial log cannot restore live training weights or optimizer state.'}
(p/'STATUS.json').write_text(json.dumps(summary,indent=2)+'\n')
hashes={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file() and f.name not in ['SHA256SUMS.json']}
(p/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('VERIFIED_COMPLETE_RUNS',len(valid),'ACTIVE_LOG_STATUS',partial)
PY
git add reproducibility/periodic_sensitivity
if ! git diff --cached --quiet; then
  git commit -qm "Checkpoint sensitivity data $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  git push -q -u origin "$branch"
  echo "SYNC_OK $(date -u '+%Y-%m-%dT%H:%M:%SZ') $(git rev-parse --short HEAD)"
else
  echo "NO_CHANGES $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
fi
