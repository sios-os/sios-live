#!/bin/bash
# test-desktop-live.sh — Launches the ANUBIS daemon and the Godot desktop
# together to verify the full IPC loop works.
#
# This starts:
#   1. The ANUBIS daemon (background)
#   2. The Godot desktop (with Xvfb)
#
# After 10 seconds, it captures a screenshot and shuts down.

set -uo pipefail

ROOT="/mnt/d/SIOS-Build/sios-live"
SOCKET="/tmp/anubis.sock"
SCREENSHOT="/mnt/d/SIOS-Build/sios-live/desktop/screenshot-live.png"

# Kill any stale daemon
pkill -f anubis_daemon 2>/dev/null || true
rm -f "$SOCKET"

# Start the daemon
echo "Starting ANUBIS daemon..."
cd "$ROOT"
python3 tools/anubis_daemon.py &>/tmp/anubis-daemon-live.log &
DAEMON_PID=$!
sleep 3

# Verify daemon is up
if [ ! -S "$SOCKET" ]; then
    echo "ERROR: Daemon socket not found"
    kill $DAEMON_PID 2>/dev/null
    exit 1
fi
echo "Daemon started (pid=$DAEMON_PID)"

# Start the desktop with Xvfb
echo "Starting Godot desktop..."
cd "$ROOT/desktop"
xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' \
    timeout 10 godot --rendering-driver opengl3 2>/tmp/godot-live.log &
GODOT_PID=$!

# Wait for the desktop to render
sleep 7

# Capture screenshot via import
echo "Capturing screenshot..."
DISPLAY=:99 xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' \
    import -window root "$SCREENSHOT" 2>/dev/null || true

# Check the Godot log for errors
echo "=== Godot log ==="
grep -E "ERROR|SCRIPT|error" /tmp/godot-live.log | head -10 || echo "(no errors)"
echo "=== Daemon log ==="
tail -5 /tmp/anubis-daemon-live.log

# Cleanup
kill $GODOT_PID 2>/dev/null || true
kill $DAEMON_PID 2>/dev/null || true
wait $GODOT_PID 2>/dev/null || true
wait $DAEMON_PID 2>/dev/null || true

echo "Done"
