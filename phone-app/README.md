# ANUBIS Phone Companion App

**React Native app for Android — pairs with the ANUBIS API server.**

The phone app provides:
- **Chat** — talk to ANUBIS from your phone
- **Dashboard** — view system status, active threats, cameras
- **Alerts** — receive and acknowledge notifications
- **Settings** — configure telemetry, sensory mode, emergency alerts
- **Background telemetry** — GPS, accelerometer (fall detection), health, battery

---

## Architecture

```
Phone App (React Native)
    │
    ├── Chat ──────────────► POST /api/chat
    ├── Dashboard ─────────► GET  /api/status, /api/threats, /api/cameras
    ├── Alerts ────────────► GET  /api/notifications
    │                        POST /api/notifications/delivered
    ├── Settings ──────────► POST /api/mode/{mode}
    │                        POST /api/emergency/alert
    └── Telemetry (bg) ────► POST /api/remote/location
                             POST /api/remote/accel
                             POST /api/remote/health
                             POST /api/remote/phone
                             POST /api/phone/heartbeat
                             POST /api/phone/telemetry

Setup ───────────────────► POST /api/phone/register
```

All requests use `Authorization: Bearer <API_KEY>`.

---

## Prerequisites

1. **Node.js 18+** and **npm**
2. **React Native CLI** (`npx react-native init --version 0.74`)
3. **Android Studio** with Android SDK 34
4. **Java 17** (for Android builds)
5. **A running ANUBIS API server** with `ANUBIS_API_KEY` set

---

## Building the App

### 1. Install dependencies

```bash
cd phone-app
npm install
```

### 2. Set up the Android project

If this is the first build, generate the Android native project:

```bash
npx react-native init AnubisCompanion --directory . --skip-install
```

Or copy from a fresh template and merge the `android/` directory.

### 3. Configure permissions

The app needs these Android permissions (already in `app.json`):

| Permission | Purpose |
|-----------|---------|
| `ACCESS_FINE_LOCATION` | GPS for remote monitoring |
| `ACCESS_COARSE_LOCATION` | Approximate location |
| `ACCESS_BACKGROUND_LOCATION` | Location while app is in background |
| `FOREGROUND_SERVICE` | Background telemetry service |
| `VIBRATE` | Notification vibration |
| `POST_NOTIFICATIONS` | Push notifications (Android 13+) |
| `BODY_SENSORS` | Heart rate from wearable |
| `ACTIVITY_RECOGNITION` | Step counting |

Add these to `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.VIBRATE" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
<uses-permission android:name="android.permission.BODY_SENSORS" />
<uses-permission android:name="android.permission.ACTIVITY_RECOGNITION" />
```

### 4. Run in development

Connect your phone via USB (with USB debugging enabled) or start an emulator:

```bash
npx react-native run-android
```

### 5. Build release APK

```bash
cd android
./gradlew assembleRelease
```

The APK will be at `android/app/build/outputs/apk/release/app-release.apk`.

---

## First-Time Setup

1. **Start the ANUBIS API server** on your home machine:
   ```bash
   # On the ANUBIS machine
   export ANUBIS_API_KEY="your-secret-key"
   python3 tools/anubis_daemon.py
   # Then in another terminal:
   python3 -c "
   import json, socket
   s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
   s.connect('/tmp/anubis.sock')
   s.send(json.dumps({'cmd': 'api_server_start'}).encode())
   print(json.loads(s.recv(65536).decode()))
   s.close()
   "
   ```

2. **Open the phone app** — it shows the Setup screen

3. **Enter the server URL**:
   - On your home network: `http://192.168.1.100:8765`
   - Via VPN/Tailscale: `http://anubis.local:8765`
   - Via SSH tunnel: `http://localhost:8765`

4. **Enter the API key** — the same value as `ANUBIS_API_KEY`

5. **Tap Connect** — the app verifies the connection

6. **Name your device** — e.g., "Storm Phone"

7. **Tap Register** — ANUBIS registers the phone and returns a device token

8. **Grant permissions** — when prompted, allow location, sensors, and notifications

9. **Enable telemetry** — go to Settings → toggle "Enable background telemetry"

The app is now paired. ANUBIS will receive your location, detect falls,
monitor battery, and send you alerts.

---

## Features

### Chat
- Send messages to ANUBIS and receive responses
- Messages are stored in the app session
- Uses the same chat endpoint as the desktop

### Dashboard
- Active threats with severity color coding
- System status (perception, cameras, network, messaging)
- Camera list with online/offline indicators
- Pull to refresh

### Alerts
- Pending notifications from ANUBIS
- Priority badges (urgent, high, normal, low)
- Dismiss/acknowledge with a tap
- Auto-polls every 30 seconds when connected

### Settings
- Toggle telemetry types (GPS, accelerometer, health, battery)
- Set update interval
- Change ANUBIS sensory mode (ambient, wake_word, conversation, privacy)
- Send emergency alert (with confirmation dialog)
- Disconnect from ANUBIS

### Background Telemetry
- **GPS**: sends latitude, longitude, accuracy, speed, altitude
- **Accelerometer**: continuous monitoring for fall detection
  - Fall threshold: 25 m/s² sudden impact
  - On fall detected: immediate alert to ANUBIS
  - 5-second quiet period to avoid duplicate alerts
- **Health**: heart rate, steps, stress, SpO2, body temperature
  - Requires Google Fit integration (native module)
- **Battery**: level and charging status
- **Heartbeat**: every interval, confirms device is active

### Fall Detection
The accelerometer runs at high frequency even when the app is in the
background. When a sudden impact is detected (magnitude > 25 m/s²),
the app immediately sends:
1. Accelerometer data to `/api/remote/accel`
2. A fall event to `/api/phone/telemetry`

ANUBIS's RemoteMonitor processes this and can trigger emergency
notifications to your contacts.

---

## File Structure

```
phone-app/
├── App.tsx                      # Main entry, tab navigation
├── app.json                     # App config and permissions
├── package.json                 # Dependencies
├── babel.config.js              # Babel config with path aliases
├── metro.config.js              # Metro config
├── tsconfig.json                # TypeScript config
├── src/
│   ├── api/
│   │   └── client.ts            # ANUBIS API client (all endpoints)
│   ├── screens/
│   │   ├── SetupScreen.tsx      # First-time setup
│   │   ├── ChatScreen.tsx       # Chat with ANUBIS
│   │   ├── DashboardScreen.tsx  # System status
│   │   ├── NotificationsScreen.tsx  # Alerts
│   │   └── SettingsScreen.tsx   # Settings
│   ├── services/
│   │   └── TelemetryService.ts  # Background telemetry + fall detection
│   ├── store/
│   │   └── appStore.tsx         # App state (React context)
│   └── theme/
│       └── theme.ts             # Colors, spacing, typography
```

---

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Connection test |
| `/api/status` | GET | Full system status |
| `/api/chat` | POST | Send message to ANUBIS |
| `/api/speak` | POST | Text-to-speech |
| `/api/mode/{mode}` | POST | Set sensory mode |
| `/api/cameras` | GET | List cameras |
| `/api/cameras/{id}/frame` | POST | Capture frame |
| `/api/cameras/monitor` | POST | Capture all cameras |
| `/api/threats` | GET | Active threats |
| `/api/threats/history` | GET | Threat history |
| `/api/threats/resolve` | POST | Resolve threat |
| `/api/contacts` | GET | List contacts |
| `/api/contacts` | POST | Add contact |
| `/api/network/devices` | GET | Network devices |
| `/api/network/status` | GET | Network status |
| `/api/network/scan` | POST | Scan network |
| `/api/notifications` | GET | Pending notifications |
| `/api/notifications/delivered` | POST | Mark delivered |
| `/api/phone/register` | POST | Register device |
| `/api/phone/heartbeat` | POST | Device heartbeat |
| `/api/phone/telemetry` | POST | Generic telemetry |
| `/api/phone/devices` | GET | List devices |
| `/api/phone/status` | GET | Protocol status |
| `/api/remote/location` | POST | GPS data |
| `/api/remote/accel` | POST | Accelerometer data |
| `/api/remote/health` | POST | Health data |
| `/api/remote/phone` | POST | Phone status |
| `/api/emergency/alert` | POST | Emergency alert |

---

## Security Notes

- The API key is stored in AsyncStorage on the phone. For production,
  consider using Android Keystore for sensitive storage.
- All communication is over HTTP (not HTTPS) when on the local network.
  For remote access, use a VPN (WireGuard/Tailscale) or SSH tunnel.
- The phone app does not store chat history permanently — messages
  are kept in memory for the session only.
- Fall detection runs locally on the phone. Only fall events are
  transmitted, not continuous accelerometer data (to save battery).
- GPS is only sent at the configured interval, not continuously.
