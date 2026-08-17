#!/bin/bash
# test-live-project.sh — Test live project planning and execution
pkill -f anubis_daemon 2>/dev/null || true
rm -f /tmp/anubis.sock
rm -rf /mnt/d/SIOS-Build/sios-live/projects  # Start fresh
cd /mnt/d/SIOS-Build/sios-live
python3 tools/anubis_daemon.py > /tmp/daemon.log 2>&1 &
sleep 3
if [ ! -S /tmp/anubis.sock ]; then
    echo "FAIL: no socket"
    cat /tmp/daemon.log
    exit 1
fi
echo "Daemon up"
python3 tools/test_live_project.py 2>&1
echo ""
echo "=== Daemon log (last 20 lines) ==="
tail -20 /tmp/daemon.log
pkill -f anubis_daemon 2>/dev/null
