#!/usr/bin/env python3
"""Read-only localhost dashboard for AHCE-FL; browser refreshes every five minutes."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import datetime as dt
import json
import re
import subprocess

ROOT=Path.home()/"Research/AHCE-FL"
CAMPAIGN=ROOT/"reproducibility/priority_ablations_2026_11_07"
PORT=8765

PAGE=r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>AHCE-FL Live Research Status</title>
<style>
:root{font-family:system-ui,-apple-system,sans-serif;color-scheme:dark;background:#0d1526;color:#e9eefb}
body{max-width:880px;padding:24px;margin:auto}header{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}
h1{font-size:1.6rem}h2{font-size:1.15rem;margin-top:27px}.muted{color:#a8b7cf}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.card{border:1px solid #344158;border-radius:12px;padding:18px;background:#162139}
.value{font-size:2.3rem;font-weight:750}.ok{color:#71d49e}.warn{color:#ffd080}.fail{color:#ff889c}
.progress{height:14px;border-radius:12px;background:#35425a;overflow:hidden}.bar{height:100%;background:#62c99e;transition:width .5s}
p,li{line-height:1.55}.button{border:1px solid #5b7092;background:#20314f;color:#fff;padding:9px 15px;border-radius:10px;cursor:pointer}
pre{white-space:pre-wrap;word-break:break-word;border:1px solid #344158;background:#101b2e;border-radius:10px;padding:14px;font-size:.88rem}
a{color:#8dc6ff}footer{color:#a8b7cf;margin-top:25px;font-size:.88rem}
@media(max-width:540px){.cards{grid-template-columns:1fr 1fr}.value{font-size:1.8rem}}
</style></head><body>
<header><div><h1>AHCE-FL · Live Campaign</h1><div class="muted">P2 → P3 · Verified experimental evidence</div></div>
<button class="button" onclick="refresh()">Refresh now</button></header>
<p class="muted" id="updated">Loading verified status…</p>
<div class="cards">
<div class="card"><div class="muted">Verified experiments</div><div class="value ok" id="verified">—</div></div>
<div class="card"><div class="muted">Active experiment</div><div class="value" id="round">—</div><div class="muted">rounds / 100</div></div>
<div class="card"><div class="muted">Recorded failures</div><div class="value" id="failed">—</div></div>
</div>
<h2>Overall verified progress</h2>
<div class="progress"><div class="bar" id="bar" style="width:0%"></div></div><p id="progress">—</p>
<h2>Execution health</h2>
<div class="card"><div id="health">Checking…</div><p id="active" class="muted">—</p><p id="lastlog" class="muted">—</p><p id="backup" class="muted">—</p></div>
<h2>Priority status</h2>
<div class="card"><p id="p2">P2 —</p><p id="p3">P3 —</p><p id="remaining">Remaining —</p></div>
<h2>Recent controller activity</h2><pre id="logs">Checking…</pre>
<p><a href="https://github.com/DrShivamBhardwaj/AHCE-FL/tree/research/priority-ablations-2026-11" target="_blank" rel="noopener noreferrer">GitHub research branch</a></p>
<footer>This dashboard fetches actual local run records every five minutes while the page remains open. It does not invent completions. Powered-off Macs cannot execute experiments or serve this page.</footer>
<script>
const esc = s => String(s??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function refresh(){
try{
 const r=await fetch("/api/status?at="+Date.now(),{cache:"no-store"});
 if(!r.ok)throw Error("HTTP "+r.status);
 const d=await r.json(), v=d.verified||0,n=d.total||45;
 document.getElementById("verified").textContent=v+"/"+n;
 document.getElementById("failed").textContent=d.failed??0;
 document.getElementById("round").textContent=d.active_round??"—";
 document.getElementById("bar").style.width=(100*v/n)+"%";
 document.getElementById("progress").textContent=(100*v/n).toFixed(1)+"% verified, "+(n-v)+" not yet verified";
 document.getElementById("active").textContent="Current: "+(d.active_name||"None")+(d.active_round!=null?" · round "+d.active_round+"/100":"");
 document.getElementById("health").innerHTML="<strong class='"+(d.controller_running?"ok":"warn")+"'>"+(d.controller_running?"Training controller running":"Controller not detected")+"</strong>"+" · watchdog: "+esc(d.watchdog);
 document.getElementById("lastlog").textContent="Latest round log: "+(d.log_updated_utc||"—");
 document.getElementById("backup").textContent="Last verified Git checkpoint: "+(d.github_commit||"—");
 document.getElementById("p2").textContent="P2 · Resource weights: "+d.p2_verified+"/18 verified";
 document.getElementById("p3").textContent="P3 · Synchronization: "+d.p3_verified+"/27 verified";
 document.getElementById("remaining").textContent="Remaining: "+(n-v)+" experiments";
 document.getElementById("logs").textContent=(d.recent_controller||[]).join("\n")||"No controller messages";
 document.getElementById("updated").textContent="Updated: "+new Date().toLocaleString()+" · local data timestamp "+(d.state_updated_utc||"—")+" · automatic refresh every 5 minutes";
}catch(e){document.getElementById("updated").textContent="Refresh error: "+e+" — retrying in 5 minutes";}
}
refresh();setInterval(refresh,300000);
</script></body></html>'''

def data():
    def load(path):
        try:return json.loads(path.read_text())
        except (OSError,json.JSONDecodeError):return {}
    s=load(CAMPAIGN/"status.json")
    w=load(CAMPAIGN/"watchdog_state.json")
    runs=s.get("runs",{})
    active=[name for name,obj in runs.items() if obj.get("status")=="running"]
    name=active[0] if active else None
    latest_round=None
    modified=None
    if name:
        path=CAMPAIGN/"run_logs"/(name+".log")
        if path.exists():
            modified=dt.datetime.fromtimestamp(path.stat().st_mtime,dt.timezone.utc).isoformat()
            # Only last 10 lines for efficient polling.
            lines=path.read_text(errors="replace").splitlines()[-10:]
            hits=[int(m.group(1)) for line in lines if (m:=re.search(r'"round":\s*(\d+)',line))]
            latest_round=max(hits) if hits else None
    output=subprocess.run(["/bin/ps","-axo","command="],capture_output=True,text=True,timeout=6)
    running=any("scripts/execute_priority_ablations.py" in line and "python" in line
                for line in output.stdout.splitlines())
    last=CAMPAIGN/"controller.log"
    original=Path("/tmp/ahce_p2_p3_campaign_20261107.log")
    log=last if last.exists() else original
    recent=log.read_text(errors="replace").splitlines()[-9:] if log.exists() else []
    git=subprocess.run(["git","rev-parse","--short","HEAD"],cwd=ROOT,text=True,capture_output=True,timeout=5)
    verified=[n for n,x in runs.items() if x.get("status")=="verified"]
    return {"total":45,"verified":len(verified),
        "failed":sum(x.get("status")=="error" for x in runs.values()),
        "p2_verified":sum(n.startswith("weights_") for n in verified),
        "p3_verified":sum(n.startswith("gap") for n in verified),
        "active_name":name,"active_round":latest_round,"log_updated_utc":modified,
        "controller_running":running,"watchdog":w.get("last_status","unavailable"),
        "github_commit":git.stdout.strip() if git.returncode==0 else None,
        "recent_controller":recent,"state_updated_utc":s.get("updated_utc")}
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=self.path.split("?",1)[0]
        if path=="/":
            payload=PAGE.encode()
            mime="text/html; charset=utf-8"
        elif path=="/api/status":
            payload=json.dumps(data()).encode()
            mime="application/json; charset=utf-8"
        else:
            self.send_error(404);return
        self.send_response(200);self.send_header("Content-Type",mime)
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(payload)))
        self.end_headers();self.wfile.write(payload)
    def log_message(self,*args):pass

if __name__=="__main__":
    print(f"AHCE-FL dashboard http://127.0.0.1:{PORT}/",flush=True)
    ThreadingHTTPServer(("127.0.0.1",PORT),Handler).serve_forever()
