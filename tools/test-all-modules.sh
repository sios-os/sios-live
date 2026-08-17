#!/bin/bash
# test-all-modules.sh — Start daemon, test all new modules, stop daemon
pkill -f anubis_daemon 2>/dev/null
sleep 1
rm -f /tmp/anubis.sock
cd /mnt/d/SIOS-Build/sios-live

# Start daemon in background
python3 tools/anubis_daemon.py > /tmp/dlog.txt 2>&1 &
DAEMON_PID=$!

# Wait for socket
for i in $(seq 1 10); do
    if [ -S /tmp/anubis.sock ]; then
        break
    fi
    sleep 1
done

if [ ! -S /tmp/anubis.sock ]; then
    echo "FAIL: daemon did not start"
    cat /tmp/dlog.txt
    kill $DAEMON_PID 2>/dev/null
    exit 1
fi

echo "Daemon up (PID $DAEMON_PID)"

# Run tests
python3 tools/test_new_modules.py 2>&1
RESULT=$?

# Stop daemon
kill $DAEMON_PID 2>/dev/null
wait $DAEMON_PID 2>/dev/null

echo ""
echo "=== Daemon log ==="
cat /tmp/dlog.txt

exit $RESULT
