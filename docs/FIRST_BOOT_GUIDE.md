# ANUBIS First Boot Guide

**Complete setup from a fresh install to a fully operational ANUBIS.**

This guide walks you through every step, in order, to get ANUBIS running
on a fresh Ubuntu 24.04 installation. Each section shows the exact commands
to run and what to expect.

**Estimated time:** 2-4 hours (most of it is model downloads)

---

## Table of Contents

1. [System Prerequisites](#1-system-prerequisites)
2. [Python Environment](#2-python-environment)
3. [Ollama & Models](#3-ollama--models)
4. [System Tools](#4-system-tools)
5. [Environment Variables](#5-environment-variables)
6. [Start the Daemon](#6-start-the-daemon)
7. [Creator Enrollment](#7-creator-enrollment)
8. [Successor Enrollment](#8-successor-enrollment)
9. [Build the Semantic Index](#9-build-the-semantic-index)
10. [Sensory & Perception Setup](#10-sensory--perception-setup)
11. [Security & Emergency Contacts](#11-security--emergency-contacts)
12. [Camera Setup](#12-camera-setup)
13. [Network Operations](#13-network-operations)
14. [Smart Home Devices](#14-smart-home-devices)
15. [API Server & Remote Access](#15-api-server--remote-access)
16. [Phone Companion App](#16-phone-companion-app)
17. [Dashboard](#17-dashboard)
18. [Daily-Life Integrations](#18-daily-life-integrations)
19. [Optional Hardware (Tier 3)](#19-optional-hardware-tier-3)
20. [Optional Advanced (Tier 4)](#20-optional-advanced-tier-4)
21. [Verification](#21-verification)
22. [Troubleshooting](#22-troubleshooting)

---

## 1. System Prerequisites

ANUBIS runs on Ubuntu 24.04. Minimum hardware:

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16-32 GB |
| GPU | None (CPU inference) | NVIDIA RTX 3060+ (6GB+ VRAM) |
| Storage | 20 GB | 100+ GB (models, knowledge, backups) |

If you installed SIOS from the ISO, the OS layer is already set up
(LightDM, Plymouth, Godot desktop). This guide covers the ANUBIS
software layer.

If you're installing on a regular Ubuntu system, run the session
installer first:

```bash
cd /path/to/sios-live
sudo bash session/install-sios-session.sh
```

---

## 2. Python Environment

ANUBIS uses Python 3.12+. Check your version:

```bash
python3 --version
```

Install Python pip and venv:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
```

Create a virtual environment (recommended):

```bash
cd /opt/sios-live   # or wherever you installed
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

Install core Python dependencies:

```bash
pip install numpy scipy

# Perception (face/voice/object recognition)
pip install opencv-python-headless deepface resemblyzer librosa

# Object detection (YOLO)
pip install ultralytics

# Deep learning backends (pick one or both)
pip install torch torchvision       # PyTorch
pip install tensorflow              # TensorFlow (DeepFace uses this)

# Speech (optional but recommended)
pip install openai-whisper          # Whisper for STT
# OR
pip install vosk                    # Vosk for offline STT
```

**Note:** ANUBIS degrades gracefully if any of these are missing.
The modules detect what's available and skip features they can't
support. You can start with just numpy and add the rest later.

---

## 3. Ollama & Models

ANUBIS's brain is a local LLM running through Ollama.

### Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify:

```bash
ollama --version
```

### Pull the primary model

```bash
ollama pull qwen2.5-coder:7b
```

This is the default model ANUBIS uses. It requires ~4.7 GB of disk
space and runs on a 6GB GPU or CPU (slower).

### Pull the embedding model

```bash
ollama pull nomic-embed-text
```

This is used for semantic search across the knowledge library.
It requires ~274 MB.

### Pull the probation model (optional, for upgrades)

```bash
ollama pull qwen2.5-coder:14b
```

Larger model for when ANUBIS needs more capability. Requires ~9 GB.
Used during A/B testing before promotion.

### Verify models are available

```bash
ollama list
```

You should see:
```
NAME                    ID           SIZE     MODIFIED
qwen2.5-coder:7b        ...          4.7 GB   ...
nomic-embed-text        ...          274 MB   ...
```

### Start Ollama as a service

```bash
sudo systemctl enable ollama
sudo systemctl start ollama
```

Verify it's running:

```bash
curl http://127.0.0.1:11434/api/tags
```

---

## 4. System Tools

These are Linux command-line tools that ANUBIS uses. Install what
you need; ANUBIS detects what's available.

### Essential (install all of these)

```bash
sudo apt-get install -y \
    espeak-ng          \  # Text-to-speech (ANUBIS's voice)
    ffmpeg             \  # Camera frame capture, audio processing
    curl               \  # HTTP requests
    ping               \  # Network diagnostics
    ssh                \  # Remote machine management
    scrot              \  # Screen capture (screen watcher)
    tesseract-ocr      \  # OCR (reading screen text)
    sox                   # Audio processing
```

### Network operations (recommended)

```bash
sudo apt-get install -y \
    nmap               \  # Network scanning
    arp-scan           \  # Device discovery
    iptables              # Firewall management
```

### Audio/speech (recommended)

```bash
sudo apt-get install -y \
    arecord            \  # Audio recording (microphone)
    aplay                 # Audio playback
```

For Whisper (better STT than vosk):

```bash
pip install openai-whisper
# The whisper command will be available after install
```

### VoIP calling (optional)

```bash
sudo apt-get install -y linphone-cli
```

### Signal messaging (optional, for emergency alerts)

```bash
# Signal CLI requires Java
sudo apt-get install -y default-jre

# Install signal-cli
wget https://github.com/AsamK/signal-cli/releases/download/v0.4.1/signal-cli-0.4.1.tar.gz
sudo tar xf signal-cli-0.4.1.tar.gz -C /opt/
sudo ln -s /opt/signal-cli-0.4.1/bin/signal-cli /usr/local/bin/signal-cli

# Register your number (one-time)
signal-cli -u +1234567890 register
signal-cli -u +1234567890 verify <CODE>
```

### 3D printing (optional)

Install OctoPrint on a separate Raspberry Pi or the same machine:
```bash
# See https://octoprint.org for installation
```

### Drone (optional)

```bash
pip install dronekit pymavlink
```

### OBD-II vehicle diagnostics (optional)

```bash
pip install obd
```

Pair with an ELM327 OBD-II adapter (Bluetooth or WiFi).

---

## 5. Environment Variables

Set these before starting the daemon. Add them to `~/.bashrc` or
`/etc/environment` for persistence.

### Required

```bash
# The model ANUBIS uses (must match what you pulled)
export ANUBIS_MODEL="qwen2.5-coder:7b"

# API key for the REST API server (choose a strong random string)
export ANUBIS_API_KEY="your-secret-api-key-here"
```

Generate a strong API key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Optional

```bash
# API server port (default 8765)
export ANUBIS_API_PORT="8765"

# Ollama URL (default http://127.0.0.1:11434)
export ANUBIS_OLLAMA="http://127.0.0.1:11434"

# Embedding model (default nomic-embed-text)
export ANUBIS_EMBED_MODEL="nomic-embed-text"

# Daemon socket path (default /tmp/anubis.sock)
export ANUBIS_SOCKET="/tmp/anubis.sock"

# GPU layers for local inference (0 = CPU, 99 = all layers on GPU)
export ANUBIS_GPU_LAYERS="99"

# CPU threads for inference
export ANUBIS_THREADS="4"
```

### Email fallback (for emergency messaging without Signal)

```bash
export ANUBIS_SMTP_HOST="smtp.gmail.com"
export ANUBIS_SMTP_PORT="587"
export ANUBIS_SMTP_USER="your-email@gmail.com"
export ANUBIS_SMTP_PASS="your-app-password"
export ANUBIS_FROM_EMAIL="your-email@gmail.com"
```

### Cloud sync (optional, iDrive E2)

```bash
# Configure in config/cloud_credentials.json (not env vars)
# See anubis/cloud_sync.py for format
```

### VPN (optional, for external gateway)

```bash
# See tools/setup_vpn.sh for WireGuard setup
```

---

## 6. Start the Daemon

The daemon is the heart of ANUBIS. It exposes a Unix socket for
the desktop and API server to communicate with.

### Start manually

```bash
cd /opt/sios-live
source venv/bin/activate   # if using venv
python3 tools/anubis_daemon.py
```

You should see:
```
ANUBIS daemon listening on /tmp/anubis.sock
  skills   : 23 promoted
  ledger   : 247 entries
  integrity: OK
  model    : qwen2.5-coder:7b available
  sandbox  : network blocked, privilege dropped
  Ctrl+C to stop
```

### Start as a systemd service

If you ran the session installer, the service is already configured:

```bash
sudo systemctl enable sios-anubis
sudo systemctl start sios-anubis
```

Check status:
```bash
sudo systemctl status sios-anubis
```

### Verify the daemon is responding

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'status'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

You should see a JSON response with daemon status, model info, and
skill count.

### Check all systems at once

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'systems_status'}).encode())
print(json.dumps(json.loads(s.recv(65536).decode()), indent=2))
s.close()
"
```

This shows the status of every subsystem — perception, cameras,
threats, smart home, weather, finance, all 39 modules.

---

## 7. Creator Enrollment

**This is the most important step.** Enrollment establishes you as
the Creator — the only person ANUBIS takes authority from.

### Enroll via daemon

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'enroll_creator',
    'display_name': 'Storm',
    'passphrase': 'YOUR-STRONG-PASSPHRASE'   # at least 8 chars
}).encode())
print(json.dumps(json.loads(s.recv(65536).decode()), indent=2))
s.close()
"
```

**IMPORTANT:**
- Choose a passphrase you won't forget. It encrypts the identity vault.
- This is a one-time operation. You cannot enroll again without
  revoking first.
- The passphrase is never stored in plaintext, never logged, never
  exposed to ANUBIS or any model.

### Verify enrollment

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'identity_stats'}).encode())
print(json.dumps(json.loads(s.recv(65536).decode()), indent=2))
s.close()
"
```

You should see your Creator ID and enrollment status.

---

## 8. Successor Enrollment

The successor is the person who takes over if you become unable to
interact with ANUBIS (confirmed absence, not just emergencies).

### Enroll successor

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'enroll_creator',  # Successor enrollment uses identity service
    'display_name': 'Ethan Pace',
    'passphrase': 'YOUR-PASSPHRASE',
    'successor': True,
    'successor_name': 'Ethan Pace',
    'successor_relationship': 'family'
}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

**Note:** The successor is NEVER notified for ordinary emergencies.
They are only contacted after the defined absence/takeover conditions
are met (extended unresponsiveness, confirmed by multiple signals).

---

## 9. Build the Semantic Index

The semantic index enables ANUBIS to search its knowledge library
by meaning, not just keywords. This is required for grounded,
cited responses.

```bash
cd /opt/sios-live
python3 tools/build_semantic_index.py
```

This embeds all 550+ knowledge documents using `nomic-embed-text`.
It takes 5-15 minutes depending on your hardware.

Verify:
```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'grounding_stats'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

---

## 10. Sensory & Perception Setup

This gives ANUBIS ears (microphone), eyes (camera/screen), and
the ability to recognize voices and faces.

### Test microphone

```bash
arecord -d 3 test.wav   # record 3 seconds
aplay test.wav          # play it back
```

### Enroll your voice

Record a 10-second sample of yourself speaking:

```bash
arecord -d 10 -r 16000 my_voice.wav
```

Enroll it with ANUBIS:

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'perception_analyze_audio',
    'audio_path': '/path/to/my_voice.wav'
}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

To enroll as a known voice (do this for each household member):

```python
import sys; sys.path.insert(0, '/opt/sios-live')
from anubis.perception import PerceptionSystem
from pathlib import Path
perception = PerceptionSystem(Path('/opt/sios-live'))
result = perception.enroll_voice(
    'Storm', '/path/to/my_voice.wav',
    relationship='creator', trusted=True,
)
print(result)
```

### Enroll your face

Take a clear photo:

```bash
scrot my_face.png   # or use a webcam photo
```

Enroll it:

```python
import sys; sys.path.insert(0, '/opt/sios-live')
from anubis.perception import PerceptionSystem
from pathlib import Path
perception = PerceptionSystem(Path('/opt/sios-live'))
result = perception.enroll_face(
    'Storm', '/path/to/my_face.png',
    relationship='creator', trusted=True,
)
print(result)
```

Repeat for each household member. ANUBIS will then recognize
family members by voice and face.

### Enable sensory system

The sensory system (ambient listening, screen watching) requires
the model to be running. It initializes automatically when the
daemon detects the model.

Check status:
```bash
# Via daemon
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'sensory_status'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

Set listening mode:
```bash
# ambient = listen to everything (default)
# wake_word = only respond when name is spoken
# conversation = treat all speech as direct address
# privacy = stop listening entirely
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'sensory_set_mode', 'mode': 'ambient'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

---

## 11. Security & Emergency Contacts

Add people ANUBIS can contact in emergencies.

### Add emergency contacts

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'contacts_add',
    'name': 'Ethan',
    'phone': '+1234567890',
    'relationship': 'family'
}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

Repeat for each contact. ANUBIS will notify them (via Signal or
email-to-SMS) when emergencies are detected.

### Verify messaging is available

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'messaging_status'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

You need at least one of:
- `signal_available: true` (Signal CLI installed and registered)
- `email_configured: true` (SMTP env vars set)

### Test emergency notification (requires approval)

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'contacts_notify_emergency',
    'message': 'Test notification from ANUBIS setup',
    'approval_token': 'creator-approved'
}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

---

## 12. Camera Setup

Add cameras for home monitoring. ANUBIS supports RTSP, HTTP
snapshots, MJPEG, and local files.

### Add a home camera

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'cameras_add',
    'name': 'Front Door',
    'camera_type': 'home',
    'connection_type': 'rtsp',
    'url': 'rtsp://username:password@192.168.1.100:554/stream'
}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

### Camera types

| Type | Use | Face recognition |
|------|-----|------------------|
| `home` | Indoor/outdoor security cameras | Yes |
| `dashcam` | Vehicle dashboard camera | Yes |
| `bodycam` | Wearable body camera | Yes |
| `public` | Public traffic/weather cameras | No (privacy) |

### Connection types

| Type | Example URL |
|------|-------------|
| `rtsp` | `rtsp://user:pass@ip:554/stream` |
| `http` | `http://ip/snapshot.jpg` |
| `mjpeg` | `http://ip/mjpegfeed` |
| `file` | `/path/to/video.mp4` |

### Start monitoring

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'cameras_start_monitoring'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

ANUBIS will now capture frames, detect motion, identify faces
(for authorized cameras), and generate events.

---

## 13. Network Operations

ANUBIS can monitor your home network for unknown devices and
intrusions.

### Scan the network (requires approval)

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'network_ops_scan',
    'approval_token': 'creator-approved'
}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

### List known devices

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'network_ops_devices'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

After the first scan, ANUBIS learns your network baseline. Future
scans will flag unknown devices.

---

## 14. Smart Home Devices

Add smart home devices for ANUBIS to control.

### Add a device

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'smarthome_add_device',
    'name': 'Living Room Light',
    'device_type': 'light',
    'protocol': 'homeassistant',
    'entity_id': 'light.living_room',
    'location': 'living_room'
}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

### Device types

`light`, `thermostat`, `lock`, `garage`, `blinds`, `switch`,
`sensor`, `camera`, `speaker`, `fan`, `appliance`

### Protocols

`homeassistant`, `zigbee`, `zwave`, `mqtt`, `http`, `wifi`

### Control a device

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'smarthome_control',
    'device_id': 'DEVICE_ID_FROM_ADD',
    'action': 'turn_on'
}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

Actions: `turn_on`, `turn_off`, `toggle`, `set_brightness`,
`set_temperature`, `set_hvac_mode`, `set_blinds`

**Note:** Locks and garage doors require Creator approval to control.

---

## 15. API Server & Remote Access

The API server lets the phone app, dashboard, and external
integrations talk to ANUBIS over HTTP.

### Start the API server

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'api_server_start'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

The API server runs on `http://127.0.0.1:8765` (or your configured
port). All endpoints require the API key in the Authorization header.

### Test the API

```bash
curl -H "Authorization: Bearer $ANUBIS_API_KEY" \
     http://127.0.0.1:8765/api/status
```

### Expose externally (optional, with caution)

If you want to access ANUBIS from outside your home network:

1. **Use a VPN** (WireGuard, Tailscale) — recommended
2. **Use SSH port forwarding** — `ssh -L 8765:127.0.0.1:8765 user@home`
3. **Bind to 0.0.0.0** — NOT recommended without a firewall

Never expose the API server directly to the internet without
authentication and encryption.

---

## 16. Phone Companion App

The phone app sends telemetry (GPS, accelerometer, health) to
ANUBIS and receives notifications.

### Register your phone

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'phone_register',
    'name': 'Storm Phone',
    'owner': 'creator',
    'platform': 'android'
}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

Save the returned `token` — your phone app will use it to
authenticate.

### Phone app endpoints

The phone app communicates with the API server:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/remote/location` | POST | Send GPS data |
| `/api/remote/accelerometer` | POST | Send motion data (fall detection) |
| `/api/remote/health` | POST | Send heart rate, steps, etc. |
| `/api/remote/status` | POST | Send battery, charging status |
| `/api/notifications` | GET | Get pending notifications |
| `/api/notifications/{id}/delivered` | POST | Mark notification delivered |

All require `Authorization: Bearer <token>`.

### Build the phone app

The phone app is a separate project (React Native or Flutter).
The protocol is defined in `anubis/phone_protocol.py`.

---

## 17. Dashboard

The web dashboard provides a browser-based control panel.

The dashboard is served by the API server at the root path:

```
http://127.0.0.1:8765/
```

Open it in any browser. It shows:
- System status
- Camera feeds
- Threat alerts
- Network devices
- Remote monitor (phone location, health)
- Perception (voice/face recognition status)
- Calendar/today's schedule
- Chat interface

---

## 18. Daily-Life Integrations

### Weather

ANUBIS monitors weather automatically. Check status:

```bash
# Via daemon
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock'); s.send(json.dumps({'cmd': 'weather_forecast'}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Calendar

Add events:

```bash
python3 -c "
import json, socket, time
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'calendar_add_event',
    'title': 'Doctor appointment',
    'start_time': time.time() + 86400,  # tomorrow
    'description': 'Annual checkup'
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Email

Check inbox (requires IMAP configuration in the email system):

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock'); s.send(json.dumps({'cmd': 'email_check'}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Finance

Add a transaction:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'finance_add_transaction',
    'amount': -52.30,
    'description': 'Grocery shopping',
    'merchant': 'Whole Foods'
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### News

Fetch news:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock'); s.send(json.dumps({'cmd': 'news_fetch'}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Music

Control playback (requires MPD or VLC):

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock'); s.send(json.dumps({'cmd': 'music_set_mood', 'mood': 'focus'}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Notifications

Send a test notification:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'notifications_notify', 'title': 'Hello', 'body': 'ANUBIS is online'}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Packages

Add a package to track:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'packages_add',
    'tracking_number': '1Z1234567890123456',
    'description': 'New laptop'
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

ANUBIS auto-detects the carrier from the tracking number format.

---

## 19. Optional Hardware (Tier 3)

### OBD-II Vehicle Diagnostics

1. Plug an ELM327 adapter into your car's OBD-II port
2. Pair it via Bluetooth or WiFi
3. ANUBIS connects automatically when `obd` Python package is installed

```bash
pip install obd
```

Read vehicle data:
```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock'); s.send(json.dumps({'cmd': 'obd_read'}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Air Quality Sensors

Connect IoT sensors (CO2, PM2.5, temperature, humidity). Record
readings:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'air_quality_record',
    'co2': 650, 'pm25': 8, 'temperature': 72, 'humidity': 45
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Energy Monitoring

Connect smart plugs or whole-home energy monitor. Record readings:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'energy_record', 'device': 'Server', 'power_watts': 450}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### 3D Printer

Connect to OctoPrint:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'printer3d_submit',
    'filename': 'bracket.stl',
    'estimated_time': 3600
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Drone

Install dronekit:

```bash
pip install dronekit pymavlink
```

Connect to drone via MAVLink. ANUBIS enforces safety geofence,
max altitude, and return-to-launch on low battery.

### Garden/Plant Monitoring

Add plants and record sensor readings:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'garden_add_plant', 'name': 'Tomato', 'plant_type': 'tomato'}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Smart Watch

Pair via the phone app. The watch sends heart rate, SpO2, steps,
sleep, and stress data. ANUBIS flags anomalies.

### Visitor Logging

Automatic when cameras are running. ANUBIS logs every person who
comes to the door, identifies known faces, and tracks arrival/
departure times.

---

## 20. Optional Advanced (Tier 4)

### Emergency Services (911)

ANUBIS can call 911 but ONLY with explicit Creator approval.

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'emergency_services_request',
    'emergency_type': 'medical',
    'description': 'Fall detected, Creator unresponsive',
    'location': '123 Main St'
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

ANUBIS will request approval via notification. The call is only
made after you approve.

### Multi-Language

ANUBIS detects language automatically and can respond in 11
languages. Add translations:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'multilang_detect',
    'text': 'Hola, como estas?'
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### AR Glasses

Connect smart glasses (Meta Ray-Bans, etc.) via the phone app.
ANUBIS processes the camera feed and provides overlay information
(face recognition, object ID, text reading).

### Satellite Imagery

Fetch public satellite imagery of your property:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'satellite_fetch',
    'approval_token': 'creator-approved'
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### Blockchain Evidence

Anchor evidence on a blockchain for legal admissibility:

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'blockchain_anchor',
    'evidence': 'important-evidence-data'
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

### ANUBIS-to-ANUBIS Protocol

Connect multiple ANUBIS instances (home + workshop):

```bash
python3 -c "
import json, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({
    'cmd': 'anubis_protocol_add_peer',
    'name': 'Workshop ANUBIS',
    'address': '192.168.1.50',
    'port': 8765,
    'api_key': 'workshop-api-key'
}).encode())
print(json.loads(s.recv(65536).decode())); s.close()
"
```

---

## 21. Verification

After completing setup, verify everything is working:

### Full system status

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'systems_status'}).encode())
status = json.loads(s.recv(65536).decode())
for system, info in status.items():
    if isinstance(info, dict):
        if 'error' in info:
            print(f'  {system}: ERROR - {info[\"error\"]}')
        elif 'not_initialized' in info:
            print(f'  {system}: not initialized (needs model)')
        else:
            print(f'  {system}: OK')
    else:
        print(f'  {system}: {info}')
s.close()
"
```

### Talk to ANUBIS

```bash
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'chat', 'message': 'Hello ANUBIS. Are you online?'}).encode())
resp = json.loads(s.recv(65536).decode())
print(resp.get('response', resp.get('error', 'no response')))
s.close()
"
```

### Run the test suite

```bash
cd /opt/sios-live
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

Expected: 1606 tests, OK (2 pre-existing Unix-only errors on Windows).

---

## 22. Troubleshooting

### Model not available

```
model: not available
```

**Fix:** Ensure Ollama is running and the model is pulled:
```bash
sudo systemctl start ollama
ollama list   # verify model is present
ollama pull qwen2.5-coder:7b   # if missing
```

### Daemon not responding

```
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/anubis.sock'
```

**Fix:** The daemon isn't running. Start it:
```bash
python3 tools/anubis_daemon.py
# or
sudo systemctl start sios-anubis
```

### Perception not working (no face/voice recognition)

**Cause:** Missing Python packages.

**Fix:**
```bash
pip install opencv-python-headless deepface resemblyzer
```

### Cameras not capturing

**Cause:** Missing ffmpeg or invalid URL.

**Fix:**
```bash
sudo apt install ffmpeg
# Test your camera URL with ffmpeg directly:
ffmpeg -i rtsp://user:pass@ip:554/stream -frames:v 1 test.jpg
```

### No audio (microphone not working)

**Fix:**
```bash
sudo apt install arecord sox
# Test:
arecord -l   # list recording devices
arecord -d 3 test.wav
```

### Signal CLI not available

**Fix:** See [Signal CLI installation](https://github.com/AsamK/signal-cli)

Alternatively, set up email-to-SMS fallback via the SMTP environment
variables.

### API server won't start

```
"error": "ANUBIS_API_KEY environment variable not set"
```

**Fix:**
```bash
export ANUBIS_API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

### Sandbox errors on Linux

The sandbox uses `unshare`, `setpriv`, and `resource` which are
Linux-only. On the production Linux system, these work correctly.
On Windows, they fail — this is expected and doesn't affect
development.

### Knowledge base empty

**Fix:** Rebuild the semantic index:
```bash
python3 tools/build_semantic_index.py
```

### Identity vault locked

If you forget your passphrase, there is no recovery. The vault
contains your Creator identity. You would need to revoke and
re-enroll, which requires the recovery ladder (recovery contacts
or successor).

---

## Quick Reference: Minimal Setup

For a bare minimum working ANUBIS (no perception, no cameras,
just chat and knowledge):

```bash
# 1. Install Ollama and pull model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text

# 2. Install Python deps
pip install numpy

# 3. Set environment
export ANUBIS_MODEL="qwen2.5-coder:7b"
export ANUBIS_API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

# 4. Build semantic index
python3 tools/build_semantic_index.py

# 5. Start daemon
python3 tools/anubis_daemon.py

# 6. In another terminal, enroll as Creator
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'enroll_creator', 'display_name': 'Storm', 'passphrase': 'YOUR-PASSPHRASE'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"

# 7. Talk to ANUBIS
python3 -c "
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/anubis.sock')
s.send(json.dumps({'cmd': 'chat', 'message': 'Hello ANUBIS'}).encode())
print(json.loads(s.recv(65536).decode()))
s.close()
"
```

That's it. ANUBIS is alive. Add capabilities one at a time as you
need them.
