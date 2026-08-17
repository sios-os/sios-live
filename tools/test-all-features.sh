#!/bin/bash
# test-all-features.sh — Test memory, mission-from-chat, and TTS
pkill -f anubis_daemon 2>/dev/null || true
rm -f /tmp/anubis.sock
rm -rf /mnt/d/SIOS-Build/sios-live/memory
cd /mnt/d/SIOS-Build/sios-live
python3 tools/anubis_daemon.py > /tmp/daemon.log 2>&1 &
sleep 3
if [ ! -S /tmp/anubis.sock ]; then
    echo "FAIL: no socket"
    cat /tmp/daemon.log
    exit 1
fi
echo "Daemon up"

# Test TTS
echo "=== TTS Test ==="
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.sendall((json.dumps({'cmd': 'tts', 'text': 'I am ANUBIS, the sovereign intelligence of SIOS.'}) + '\n').encode())
data = s.recv(65536).decode()
s.close()
print(json.loads(data))
" 2>&1

# Test memory + mission
echo ""
echo "=== Memory + Mission Test ==="
python3 tools/test_memory_chat.py 2>&1

echo ""
echo "=== Daemon log ==="
cat /tmp/daemon.log
pkill -f anubis_daemon 2>/dev/null
