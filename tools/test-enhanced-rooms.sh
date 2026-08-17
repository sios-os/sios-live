#!/bin/bash
# test-enhanced-rooms.sh — Test enhanced rooms with IPC
pkill -f anubis_daemon 2>/dev/null || true
rm -f /tmp/anubis.sock
cd /mnt/d/SIOS-Build/sios-live
python3 tools/anubis_daemon.py > /tmp/daemon.log 2>&1 &
sleep 3
if [ ! -S /tmp/anubis.sock ]; then
    echo "FAIL: no socket"
    exit 1
fi
echo "Daemon up, socket exists"

cd desktop
sed -i 's|res://scenes/boot.tscn|res://scenes/screenshot.tscn|' project.godot
timeout 60 xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' \
    godot --rendering-driver opengl3 2>&1 | grep -E "Screenshot|RoomController|IPC|connected" | head -20
sed -i 's|res://scenes/screenshot.tscn|res://scenes/boot.tscn|' project.godot

echo "=== Daemon log ==="
cat /tmp/daemon.log
pkill -f anubis_daemon 2>/dev/null
