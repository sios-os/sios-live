#!/bin/bash
# test-tomb-halls.sh — Test Tomb hall IPC commands
pkill -f anubis_daemon 2>/dev/null || true
rm -f /tmp/anubis.sock
cd /mnt/d/SIOS-Build/sios-live
python3 tools/anubis_daemon.py > /tmp/daemon.log 2>&1 &
sleep 3
if [ ! -S /tmp/anubis.sock ]; then
    echo "FAIL: no socket"
    cat /tmp/daemon.log
    exit 1
fi
echo "Daemon up"
python3 tools/test_tomb_halls.py 2>&1
echo ""
echo "=== Daemon log ==="
cat /tmp/daemon.log
pkill -f anubis_daemon 2>/dev/null
