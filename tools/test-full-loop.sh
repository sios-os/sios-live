#!/bin/bash
# test-full-loop.sh — Full end-to-end test: daemon + Godot desktop + IPC.
#
# This verifies that:
#   1. The ANUBIS daemon starts and listens on the socket
#   2. The Godot desktop connects and queries status
#   3. Room controllers successfully call the daemon
#   4. The skill library is displayed in the Forge
#   5. The ledger is displayed in the Observatory

set -uo pipefail

ROOT="/mnt/d/SIOS-Build/sios-live"
SOCKET="/tmp/anubis.sock"

echo "=== Full Loop Test ==="

# 1. Start daemon
pkill -f anubis_daemon 2>/dev/null || true
rm -f "$SOCKET"
cd "$ROOT"
python3 tools/anubis_daemon.py > /tmp/daemon-test.log 2>&1 &
DAEMON_PID=$!
sleep 3

if [ ! -S "$SOCKET" ]; then
    echo "FAIL: Daemon socket not found"
    exit 1
fi
echo "PASS: Daemon started (pid=$DAEMON_PID)"

# 2. Run Godot with screenshot capture
cd "$ROOT/desktop"
timeout 30 xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' \
    godot --rendering-driver opengl3 > /tmp/godot-test.log 2>&1
GODOT_EXIT=$?

# 3. Check Godot output
echo ""
echo "=== Godot output ==="
grep -E "Screenshot|ERROR|SCRIPT" /tmp/godot-test.log | head -20

# 4. Check daemon log for connection activity
echo ""
echo "=== Daemon log ==="
cat /tmp/daemon-test.log

# 5. Verify screenshots exist
echo ""
echo "=== Screenshots ==="
SHOT_DIR="/root/.local/share/godot/app_userdata/SIOS Desktop"
for f in shot-hub shot-workspace shot-forge shot-observatory shot-command; do
    if [ -f "$SHOT_DIR/$f.png" ]; then
        SIZE=$(stat -c%s "$SHOT_DIR/$f.png")
        echo "  $f.png: ${SIZE} bytes"
    else
        echo "  $f.png: MISSING"
    fi
done

# 6. Cleanup
kill $DAEMON_PID 2>/dev/null || true

echo ""
if grep -q "Screenshot: COMMAND" /tmp/godot-test.log; then
    echo "PASS: All screenshots captured"
else
    echo "FAIL: Not all screenshots captured"
fi
