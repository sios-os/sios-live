"""Web dashboard — browser-based control panel for ANUBIS.

Serves a single-page HTML dashboard that provides:
- System status overview
- Camera feeds and events
- Threat monitoring
- Contact management
- Network device list
- Remote monitor status
- Calendar and weather
- Chat interface
- Configuration

Built on top of the API server — the dashboard is pure HTML/JS/CSS
served from the same HTTP server, requiring no external dependencies.

The dashboard fetches data from /api/* endpoints and updates in real-time.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ANUBIS Control Panel</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0a; color: #e0e0e0; font-family: 'Segoe UI', monospace; }
.header { background: #1a1a2e; padding: 15px 20px; border-bottom: 2px solid #e94560; }
.header h1 { color: #e94560; font-size: 1.5em; }
.header .status { float: right; color: #0f3460; }
.header .status span { color: #e94560; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 15px; padding: 20px; }
.card { background: #16213e; border-radius: 8px; padding: 15px; border: 1px solid #0f3460; }
.card h2 { color: #e94560; font-size: 1.1em; margin-bottom: 10px; border-bottom: 1px solid #0f3460; padding-bottom: 5px; }
.card .row { display: flex; justify-content: space-between; padding: 4px 0; }
.card .label { color: #a0a0a0; }
.card .value { color: #e0e0e0; font-weight: bold; }
.card .value.ok { color: #4ecca3; }
.card .value.warn { color: #f0a500; }
.card .value.crit { color: #e94560; }
.chat { position: fixed; bottom: 20px; right: 20px; width: 350px; background: #16213e; border-radius: 8px; border: 1px solid #e94560; }
.chat-header { background: #e94560; color: #fff; padding: 10px; border-radius: 8px 8px 0 0; cursor: pointer; }
.chat-messages { height: 200px; overflow-y: auto; padding: 10px; }
.chat-msg { margin-bottom: 8px; padding: 5px 8px; border-radius: 4px; }
.chat-msg.user { background: #0f3460; text-align: right; }
.chat-msg.anubis { background: #1a1a2e; }
.chat-input { display: flex; padding: 10px; }
.chat-input input { flex: 1; padding: 8px; border: 1px solid #0f3460; background: #0a0a0a; color: #e0e0e0; border-radius: 4px; }
.chat-input button { padding: 8px 15px; background: #e94560; color: #fff; border: none; border-radius: 4px; cursor: pointer; margin-left: 5px; }
.threat-item { padding: 8px; margin: 5px 0; border-radius: 4px; }
.threat-item.critical { background: #4a0000; border-left: 3px solid #e94560; }
.threat-item.high { background: #4a3000; border-left: 3px solid #f0a500; }
.threat-item.medium { background: #00304a; border-left: 3px solid #4ecca3; }
.threat-item.low { background: #1a1a2e; border-left: 3px solid #0f3460; }
.event-item { padding: 5px 0; border-bottom: 1px solid #0f3460; font-size: 0.9em; }
.refresh-btn { background: #0f3460; color: #e0e0e0; border: none; padding: 5px 15px; border-radius: 4px; cursor: pointer; }
.refresh-btn:hover { background: #e94560; }
</style>
</head>
<body>
<div class="header">
  <h1>ANUBIS Control Panel</h1>
  <div class="status">Status: <span id="sys-status">Loading...</span></div>
</div>
<div class="grid">
  <div class="card" id="card-system">
    <h2>System</h2>
    <div class="row"><span class="label">Uptime</span><span class="value" id="sys-uptime">—</span></div>
    <div class="row"><span class="label">API Requests</span><span class="value" id="sys-requests">—</span></div>
    <div class="row"><span class="label">Monitoring</span><span class="value" id="sys-monitoring">—</span></div>
  </div>
  <div class="card" id="card-cameras">
    <h2>Cameras <button class="refresh-btn" onclick="refreshCameras()">↻</button></h2>
    <div class="row"><span class="label">Total</span><span class="value" id="cam-total">—</span></div>
    <div class="row"><span class="label">Online</span><span class="value" id="cam-online">—</span></div>
    <div id="cam-list"></div>
  </div>
  <div class="card" id="card-threats">
    <h2>Threats <button class="refresh-btn" onclick="refreshThreats()">↻</button></h2>
    <div id="threat-list"><div class="event-item">No active threats</div></div>
  </div>
  <div class="card" id="card-contacts">
    <h2>Contacts</h2>
    <div id="contact-list"><div class="event-item">No contacts configured</div></div>
  </div>
  <div class="card" id="card-network">
    <h2>Network <button class="refresh-btn" onclick="refreshNetwork()">↻</button></h2>
    <div class="row"><span class="label">Devices</span><span class="value" id="net-devices">—</span></div>
    <div id="net-list"></div>
  </div>
  <div class="card" id="card-remote">
    <h2>Remote Monitor</h2>
    <div class="row"><span class="label">Creator Status</span><span class="value" id="remote-status">—</span></div>
    <div class="row"><span class="label">Location</span><span class="value" id="remote-loc">—</span></div>
  </div>
  <div class="card" id="card-weather">
    <h2>Weather</h2>
    <div class="row"><span class="label">Temperature</span><span class="value" id="weather-temp">—</span></div>
    <div class="row"><span class="label">Condition</span><span class="value" id="weather-cond">—</span></div>
  </div>
  <div class="card" id="card-calendar">
    <h2>Today's Schedule</h2>
    <div id="cal-list"><div class="event-item">No events</div></div>
  </div>
  <div class="card" id="card-perception">
    <h2>Perception</h2>
    <div class="row"><span class="label">Voice ID</span><span class="value" id="perc-voice">—</span></div>
    <div class="row"><span class="label">Faces</span><span class="value" id="perc-faces">—</span></div>
    <div class="row"><span class="label">Objects</span><span class="value" id="perc-objects">—</span></div>
  </div>
</div>
<div class="chat" id="chat-panel">
  <div class="chat-header" onclick="toggleChat()">ANUBIS Chat</div>
  <div class="chat-messages" id="chat-messages"></div>
  <div class="chat-input">
    <input type="text" id="chat-input" placeholder="Type a message..." onkeypress="if(event.key==='Enter')sendChat()">
    <button onclick="sendChat()">Send</button>
  </div>
</div>
<script>
const API = '';
let apiKey = localStorage.getItem('anubis_api_key') || '';
function authHeader() { return apiKey ? {'Authorization': 'Bearer ' + apiKey} : {}; }
async function apiGet(path) {
  try {
    const r = await fetch(API + path, {headers: authHeader()});
    return await r.json();
  } catch(e) { return null; }
}
async function apiPost(path, body) {
  try {
    const r = await fetch(API + path, {
      method: 'POST', headers: {...authHeader(), 'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    return await r.json();
  } catch(e) { return null; }
}
async function refreshAll() {
  const status = await apiGet('/api/status');
  if (!status) { document.getElementById('sys-status').textContent = 'Offline'; return; }
  document.getElementById('sys-status').textContent = 'Online';
  document.getElementById('sys-status').className = 'value ok';
  const api = status.api_server || {};
  document.getElementById('sys-uptime').textContent = Math.round(api.uptime_seconds || 0) + 's';
  document.getElementById('sys-requests').textContent = api.total_requests || 0;
  if (status.cameras) {
    document.getElementById('cam-total').textContent = status.cameras.total_cameras || 0;
    document.getElementById('cam-online').textContent = status.cameras.online_cameras || 0;
  }
  if (status.threats) {
    const tl = document.getElementById('threat-list');
    tl.innerHTML = '';
    const threats = status.threats.active_threats || 0;
    if (threats === 0) { tl.innerHTML = '<div class="event-item">No active threats</div>'; }
  }
  if (status.network) {
    document.getElementById('net-devices').textContent = status.network.total_devices || 0;
  }
  if (status.remote) {
    document.getElementById('remote-status').textContent = status.remote.creator_state || 'unknown';
  }
  if (status.perception) {
    document.getElementById('perc-voice').textContent = status.perception.voice_id ? 'Active' : '—';
    document.getElementById('perc-faces').textContent = status.perception.faces ? 'Active' : '—';
    document.getElementById('perc-objects').textContent = status.perception.objects ? 'Active' : '—';
  }
}
async function refreshCameras() {
  const cams = await apiGet('/api/cameras');
  if (cams && cams.cameras) {
    const list = document.getElementById('cam-list');
    list.innerHTML = cams.cameras.slice(0, 5).map(c =>
      `<div class="event-item">${c.name} — ${c.status}</div>`
    ).join('');
  }
}
async function refreshThreats() {
  const threats = await apiGet('/api/threats');
  if (threats && threats.threats) {
    const list = document.getElementById('threat-list');
    list.innerHTML = threats.threats.map(t =>
      `<div class="threat-item ${t.severity}">${t.description || t.threat_type}</div>`
    ).join('') || '<div class="event-item">No active threats</div>';
  }
}
async function refreshNetwork() {
  const net = await apiGet('/api/network/devices');
  if (net && net.devices) {
    const list = document.getElementById('net-list');
    list.innerHTML = net.devices.slice(0, 10).map(d =>
      `<div class="event-item">${d.ip || d.hostname || 'Unknown'} — ${d.status || '—'}</div>`
    ).join('');
  }
}
async function sendChat() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  const msgs = document.getElementById('chat-messages');
  msgs.innerHTML += `<div class="chat-msg user">${msg}</div>`;
  msgs.scrollTop = msgs.scrollHeight;
  const resp = await apiPost('/api/chat', {message: msg});
  if (resp && resp.response) {
    msgs.innerHTML += `<div class="chat-msg anubis">${resp.response}</div>`;
  } else if (resp && resp.error) {
    msgs.innerHTML += `<div class="chat-msg anubis">Error: ${resp.error}</div>`;
  }
  msgs.scrollTop = msgs.scrollHeight;
}
function toggleChat() {
  const panel = document.getElementById('chat-panel');
  const msgs = document.getElementById('chat-messages');
  msgs.style.display = msgs.style.display === 'none' ? 'block' : 'none';
}
refreshAll();
setInterval(refreshAll, 10000);
</script>
</body>
</html>"""


class WebDashboard:
    """Web dashboard for ANUBIS.

    Serves the dashboard HTML. Designed to be served by the API server
    at the root path (/), with all data fetched from /api/* endpoints.
    """

    ACTOR = "anubis.dashboard"

    def __init__(self, root: str | Path, *, ledger: Any | None = None) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self._state_dir = self.root / "memory" / "dashboard"
        self._state_dir.mkdir(parents=True, exist_ok=True)

    def get_html(self) -> str:
        """Get the dashboard HTML."""
        return DASHBOARD_HTML

    def get_html_bytes(self) -> bytes:
        """Get the dashboard HTML as bytes."""
        return DASHBOARD_HTML.encode("utf-8")

    @property
    def content_type(self) -> str:
        return "text/html; charset=utf-8"

    @property
    def content_length(self) -> int:
        return len(self.get_html_bytes())
