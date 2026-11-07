#!/bin/zsh
set -euo pipefail
REPO="$HOME/Research/AHCE-FL"
LABEL="org.ahce.priority-ablations"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>$LABEL</string>
<key>ProgramArguments</key><array>
<string>$REPO/.venv/bin/python</string>
<string>$REPO/scripts/ahce_priority_watchdog.py</string>
</array>
<key>RunAtLoad</key><true/>
<key>StartInterval</key><integer>300</integer>
<key>StandardOutPath</key><string>$REPO/reproducibility/priority_ablations_2026_11_07/watchdog_stdout.log</string>
<key>StandardErrorPath</key><string>$REPO/reproducibility/priority_ablations_2026_11_07/watchdog_stderr.log</string>
</dict></plist>
EOF
plutil -lint "$PLIST"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart "gui/$(id -u)/$LABEL"
echo "LAUNCHAGENT_INSTALLED=$PLIST"
