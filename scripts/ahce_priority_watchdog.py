#!/usr/bin/env python3
"""LaunchAgent watchdog: start/resume one controller, no science-code modifications."""
import datetime as dt, fcntl, json, os, subprocess, sys
from pathlib import Path

R=Path.home()/"Research/AHCE-FL"
RUNROOT=R/"reproducibility/priority_ablations_2026_11_07"
RUNROOT.mkdir(parents=True,exist_ok=True)
STATUS=RUNROOT/"status.json"
GUARD=RUNROOT/"watchdog.lock"
WSTATE=RUNROOT/"watchdog_state.json"
CONTROLLER=R/"scripts/execute_priority_ablations.py"
PYTHON=R/".venv/bin/python"
MAX_RESTARTS_PER_CASE=2
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def msg(*text):print(stamp(),*text,flush=True)
def read(path,default):
 try:return json.loads(path.read_text())
 except (OSError,json.JSONDecodeError):return default
def write(path,data):
 p=path.with_suffix(path.suffix+".tmp")
 p.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
 p.replace(path)
def running():
 p=subprocess.run(["/bin/ps","-axo","pid=,command="],capture_output=True,text=True)
 # Match only active interpreter invocation, not current watchdog or grep
 return any("scripts/execute_priority_ablations.py" in line and "python" in line
            and "ahce_priority_watchdog.py" not in line for line in p.stdout.splitlines())
def main():
 with GUARD.open("w") as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:return
  st=read(STATUS,{})
  state=read(WSTATE,{"attempts":{},"last_status":None})
  if st.get("status")=="completed" and st.get("verified_runs")==45:
   if state.get("last_status")!="COMPLETE":msg("COMPLETE",45,"/45")
   state["last_status"]="COMPLETE";write(WSTATE,state);return
  if running():
   state["last_status"]="RUNNING";state["last_seen_utc"]=stamp()
   write(WSTATE,state)
   return
  runs=st.get("runs",{})
  pending=[(n,v) for n,v in runs.items() if v.get("status")!="verified"]
  if pending:
   name,entry=pending[-1]
   key=name
  else:key="campaign_start"
  # A failed scientific run or repeated infrastructure failure needs human review.
  previous=state["attempts"].get(key,0)
  if previous>=MAX_RESTARTS_PER_CASE:
   msg("HALTED_RETRY_LIMIT",key,previous)
   state["last_status"]="HALTED_RETRY_LIMIT"
   state["halt_reason"]=key
   write(WSTATE,state)
   return
  if not PYTHON.is_file():
   msg("HALTED_MISSING_VENV");state["last_status"]="HALTED_MISSING_VENV";write(WSTATE,state);return
  state["attempts"][key]=previous+1
  state["last_status"]="STARTING"
  state["last_start_utc"]=stamp()
  state["active_case"]=key
  write(WSTATE,state)
  log=(RUNROOT/"controller.log").open("ab")
  # Detached, sequential, and idle-sleep protected. Computer must remain ON.
  proc=subprocess.Popen(["/usr/bin/caffeinate","-dimsu",str(PYTHON),"-u",
                         str(CONTROLLER)],cwd=R,stdin=subprocess.DEVNULL,
                         stdout=log,stderr=subprocess.STDOUT,
                         start_new_session=True)
  log.close()
  msg("LAUNCHED",proc.pid,"attempt",previous+1,"case",key)

if __name__=="__main__":
 try:main()
 except Exception as ex:
  msg("WATCHDOG_ERROR",repr(ex))
  raise
