#!/bin/bash
# start-daemon.sh — Start the ANUBIS daemon in the background.
pkill -f anubis_daemon 2>/dev/null || true
rm -f /tmp/anubis.sock
cd /mnt/d/SIOS-Build/sios-live
python3 tools/anubis_daemon.py > /tmp/daemon.log 2>&1 &
sleep 3
if [ -S /tmp/anubis.sock ]; then
    echo "DAEMON_UP"
    head -10 /tmp/daemon.log
else
    echo "DAEMON_FAILED"
    cat /tmp/daemon.log
fi
