"""Network operations — ANUBIS runs the network.

Full network operator capabilities:
1. Discovery — scan and identify all devices on the network
2. Monitoring — track device status, detect new/unknown devices
3. Control — SSH into machines, control smart home devices, IoT
4. Intrusion detection — detect suspicious devices or traffic
5. Traffic monitoring — analyze network traffic patterns
6. Firewall management — manage firewall rules
7. Device quarantine — isolate suspicious devices

Uses standard Python networking (socket, subprocess) plus optional
tools (nmap, arp-scan, iptables, ssh, curl) when available.

On Linux: full functionality (nmap, iptables, arp-scan, ssh)
On Windows: limited functionality (socket scanning, no iptables)
On the production Linux machine: full network operator

SECURITY:
- Network operations are governance-gated for consequential actions
- Device control (SSH, smart home) requires Creator approval
- Firewall changes require Creator approval
- Quarantine requires Creator approval
- Discovery and monitoring are autonomous (read-only)
- All actions logged to evidence ledger
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class NetworkDevice:
    """A device discovered on the network."""
    device_id: str
    ip: str = ""
    mac: str = ""
    hostname: str = ""
    device_type: str = "unknown"  # computer, phone, iot, camera, router, unknown
    vendor: str = ""
    os_guess: str = ""
    ports: list[int] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    first_seen: float = 0.0
    last_seen: float = 0.0
    known: bool = False  # is this a known/trusted device
    trusted: bool = False
    quarantined: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "ip": self.ip,
            "mac": self.mac,
            "hostname": self.hostname,
            "device_type": self.device_type,
            "vendor": self.vendor,
            "os_guess": self.os_guess,
            "ports": self.ports,
            "services": self.services,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "known": self.known,
            "trusted": self.trusted,
            "quarantined": self.quarantined,
            "notes": self.notes,
        }


@dataclass
class TrafficAlert:
    """A network traffic anomaly alert."""
    alert_id: str
    alert_type: str = ""  # unusual_traffic, port_scan, unknown_device, etc.
    source_ip: str = ""
    dest_ip: str = ""
    severity: str = "low"  # low, medium, high, critical
    description: str = ""
    timestamp: float = 0.0
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "source_ip": self.source_ip,
            "dest_ip": self.dest_ip,
            "severity": self.severity,
            "description": self.description,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
        }


class NetworkOperator:
    """Full network operator — discovery, monitoring, control, security.

    ANUBIS uses this to:
    - Know every device on the network
    - Detect unknown or suspicious devices
    - Control smart home devices and IoT
    - Monitor traffic for anomalies
    - Manage firewall rules
    - Quarantine compromised devices
    - SSH into machines for maintenance
    """

    ACTOR = "anubis.network_ops"

    def __init__(
        self,
        root: str | Path,
        *,
        network_cidr: str = "192.168.1.0/24",
        gateway_ip: str = "192.168.1.1",
        ledger: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.network_cidr = network_cidr
        self.gateway_ip = gateway_ip
        self.ledger = ledger

        self._state_dir = self.root / "memory" / "network"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._devices_file = self._state_dir / "devices.json"
        self._alerts_file = self._state_dir / "traffic_alerts.jsonl"
        self._history_file = self._state_dir / "scan_history.jsonl"

        self._devices: dict[str, NetworkDevice] = {}
        self._load_devices()

        # Detect available tools
        self._nmap = shutil.which("nmap")
        self._arp_scan = shutil.which("arp-scan")
        self._iptables = shutil.which("iptables")
        self._ssh = shutil.which("ssh")
        self._curl = shutil.which("curl")
        self._ping = shutil.which("ping") or "ping"
        self._is_linux = platform.system() == "Linux"
        self._is_windows = platform.system() == "Windows"

        # Get local IP
        self._local_ip = self._get_local_ip()

    def _get_local_ip(self) -> str:
        """Get the local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # --------------------------------------------------- discovery

    def scan_network(self) -> list[dict[str, Any]]:
        """Scan the network for devices. Returns discovered devices."""
        devices: list[NetworkDevice] = []

        if self._nmap:
            devices = self._scan_with_nmap()
        elif self._arp_scan:
            devices = self._scan_with_arp()
        else:
            devices = self._scan_with_socket()

        # Update device database
        now = time.time()
        for device in devices:
            device_id = self._device_id(device.ip, device.mac)
            device.device_id = device_id
            device.last_seen = now

            if device_id in self._devices:
                # Update existing device
                existing = self._devices[device_id]
                existing.last_seen = now
                existing.ip = device.ip  # IP may change
                if device.hostname:
                    existing.hostname = device.hostname
                if device.ports:
                    existing.ports = device.ports
                if device.services:
                    existing.services = device.services
            else:
                # New device
                device.first_seen = now
                self._devices[device_id] = device
                self._log("device.discovered", device.to_dict())

                # Alert if unknown device
                if not device.known:
                    self._create_alert(
                        alert_type="unknown_device",
                        source_ip=device.ip,
                        severity="medium",
                        description=f"Unknown device: {device.hostname or device.ip}",
                    )

        self._save_devices()
        self._record_scan(devices)
        return [d.to_dict() for d in self._devices.values()]

    def _scan_with_nmap(self) -> list[NetworkDevice]:
        """Scan using nmap."""
        devices: list[NetworkDevice] = []
        try:
            cmd = [self._nmap, "-sn", "-oG", "-", self.network_cidr]  # type: ignore
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            for line in result.stdout.splitlines():
                if "Host:" in line:
                    parts = line.split()
                    ip = parts[1] if len(parts) > 1 else ""
                    status = parts[2] if len(parts) > 2 else ""
                    if status == "Up" and ip:
                        device = NetworkDevice(
                            device_id="",
                            ip=ip,
                            first_seen=time.time(),
                            last_seen=time.time(),
                        )
                        # Try to get hostname
                        try:
                            hostname = socket.gethostbyaddr(ip)[0]
                            device.hostname = hostname
                        except Exception:
                            pass
                        devices.append(device)
        except Exception:
            pass
        return devices

    def _scan_with_arp(self) -> list[NetworkDevice]:
        """Scan using arp-scan."""
        devices: list[NetworkDevice] = []
        try:
            cmd = [self._arp_scan, "--localnet", "--retry=2"]  # type: ignore
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            for line in result.stdout.splitlines():
                parts = line.split("\t")
                if len(parts) >= 2 and parts[0].count(".") == 3:
                    ip = parts[0]
                    mac = parts[1] if len(parts) > 1 else ""
                    vendor = parts[2] if len(parts) > 2 else ""
                    device = NetworkDevice(
                        device_id="",
                        ip=ip,
                        mac=mac,
                        vendor=vendor,
                        first_seen=time.time(),
                        last_seen=time.time(),
                    )
                    devices.append(device)
        except Exception:
            pass
        return devices

    def _scan_with_socket(self) -> list[NetworkDevice]:
        """Scan using socket connections (fallback, no tools needed).

        Scans common ports on each IP in the subnet. Slower but
        works everywhere.
        """
        devices: list[NetworkDevice] = []
        # Parse subnet
        try:
            base = self.network_cidr.split("/")[0]
            prefix = int(self.network_cidr.split("/")[1])
            if prefix != 24:
                # Only support /24 for socket scanning
                base_parts = base.split(".")
                base = f"{base_parts[0]}.{base_parts[1]}.{base_parts[2]}"

            # Scan last octet 1-254
            common_ports = [22, 80, 443, 554, 8080, 9000]  # SSH, HTTP, HTTPS, RTSP, etc.
            for i in range(1, 255):
                ip = f"{base}.{i}"
                open_ports: list[int] = []
                for port in common_ports:
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(0.1)
                        result = s.connect_ex((ip, port))
                        if result == 0:
                            open_ports.append(port)
                        s.close()
                    except Exception:
                        pass

                if open_ports:
                    device = NetworkDevice(
                        device_id="",
                        ip=ip,
                        ports=open_ports,
                        first_seen=time.time(),
                        last_seen=time.time(),
                    )
                    # Guess device type from ports
                    device.device_type = self._guess_device_type(open_ports)
                    # Try hostname
                    try:
                        device.hostname = socket.gethostbyaddr(ip)[0]
                    except Exception:
                        pass
                    devices.append(device)
        except Exception:
            pass
        return devices

    def _guess_device_type(self, ports: list[int]) -> str:
        """Guess device type from open ports."""
        if 554 in ports:  # RTSP
            return "camera"
        if 22 in ports and 80 in ports:
            return "computer"
        if 80 in ports and 443 not in ports:
            return "iot"
        if 8080 in ports or 9000 in ports:
            return "iot"
        if 22 in ports:
            return "computer"
        return "unknown"

    def _device_id(self, ip: str, mac: str) -> str:
        """Generate a stable device ID from IP and/or MAC."""
        identifier = mac if mac else ip
        return hashlib.sha256(f"device:{identifier}".encode()).hexdigest()[:16]

    # --------------------------------------------------- device management

    def get_devices(self) -> list[dict[str, Any]]:
        """Get all known devices."""
        return [d.to_dict() for d in self._devices.values()]

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        """Get a specific device."""
        d = self._devices.get(device_id)
        return d.to_dict() if d else None

    def trust_device(self, device_id: str, *, trusted: bool = True) -> bool:
        """Mark a device as trusted or untrusted."""
        device = self._devices.get(device_id)
        if device is None:
            return False
        device.trusted = trusted
        device.known = True
        self._save_devices()
        self._log("device.trust_changed", {
            "device_id": device_id,
            "trusted": trusted,
        })
        return True

    def identify_device(
        self, device_id: str, name: str, device_type: str = "",
        notes: str = "",
    ) -> bool:
        """Identify and name a device."""
        device = self._devices.get(device_id)
        if device is None:
            return False
        device.hostname = name
        if device_type:
            device.device_type = device_type
        device.known = True
        if notes:
            device.notes = notes
        self._save_devices()
        self._log("device.identified", {
            "device_id": device_id,
            "name": name,
            "type": device_type,
        })
        return True

    def remove_device(self, device_id: str) -> bool:
        """Remove a device from the known list."""
        if device_id in self._devices:
            del self._devices[device_id]
            self._save_devices()
            return True
        return False

    def get_unknown_devices(self) -> list[dict[str, Any]]:
        """Get all unknown devices."""
        return [d.to_dict() for d in self._devices.values() if not d.known]

    def get_trusted_devices(self) -> list[dict[str, Any]]:
        """Get all trusted devices."""
        return [d.to_dict() for d in self._devices.values() if d.trusted]

    # --------------------------------------------------- device control

    def ssh_command(
        self, device_id: str, command: str, *, timeout: int = 30
    ) -> dict[str, Any]:
        """Run a command on a device via SSH.

        Requires Creator approval for non-read commands.
        """
        device = self._devices.get(device_id)
        if device is None:
            return {"success": False, "error": "Device not found"}
        if not self._ssh:
            return {"success": False, "error": "SSH not available"}
        if not device.ip:
            return {"success": False, "error": "No IP for device"}

        try:
            cmd = [self._ssh, "-o", "ConnectTimeout=5",
                   "-o", "StrictHostKeyChecking=no",
                   device.ip, command]  # type: ignore
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            self._log("device.ssh", {
                "device_id": device_id,
                "command": command,
                "success": result.returncode == 0,
            })
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "SSH command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def http_request(
        self, device_id: str, path: str, method: str = "GET",
        data: str | None = None, port: int = 80,
    ) -> dict[str, Any]:
        """Make an HTTP request to a device (smart home, IoT, camera)."""
        device = self._devices.get(device_id)
        if device is None:
            return {"success": False, "error": "Device not found"}
        if not device.ip:
            return {"success": False, "error": "No IP for device"}

        try:
            url = f"http://{device.ip}:{port}{path}"
            if self._curl:
                cmd = [self._curl, "-s", "-X", method, url]  # type: ignore
                if data:
                    cmd.extend(["-d", data])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                self._log("device.http", {
                    "device_id": device_id,
                    "url": url,
                    "method": method,
                })
                return {
                    "success": result.returncode == 0,
                    "response": result.stdout,
                }
            else:
                # Use urllib
                import urllib.request
                req = urllib.request.Request(url, method=method)
                if data:
                    req.data = data.encode()
                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = resp.read().decode()
                    return {"success": True, "response": body}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------- intrusion detection

    def check_for_intrusions(self) -> list[dict[str, Any]]:
        """Check for potential network intrusions.

        - Unknown devices on the network
        - Devices with suspicious port configurations
        - Devices communicating at unusual times
        """
        alerts: list[dict[str, Any]] = []

        # Check for unknown devices
        for device in self._devices.values():
            if not device.known and not device.trusted:
                alerts.append({
                    "type": "unknown_device",
                    "severity": "medium",
                    "device": device.to_dict(),
                    "description": f"Unknown device: {device.hostname or device.ip}",
                })

            # Check for suspicious ports (e.g., backdoor ports)
            suspicious_ports = [31337, 12345, 4444, 6667]  # common backdoor ports
            if any(p in device.ports for p in suspicious_ports):
                alerts.append({
                    "type": "suspicious_ports",
                    "severity": "high",
                    "device": device.to_dict(),
                    "description": f"Suspicious ports on {device.ip}: {device.ports}",
                })

            # Check for quarantined devices still on network
            if device.quarantined:
                alerts.append({
                    "type": "quarantined_device_active",
                    "severity": "high",
                    "device": device.to_dict(),
                    "description": f"Quarantined device still active: {device.ip}",
                })

        return alerts

    def _create_alert(
        self, alert_type: str, source_ip: str = "",
        severity: str = "low", description: str = "",
    ) -> TrafficAlert:
        """Create a traffic alert."""
        alert = TrafficAlert(
            alert_id=hashlib.sha256(
                f"alert:{alert_type}:{time.time()}".encode()
            ).hexdigest()[:16],
            alert_type=alert_type,
            source_ip=source_ip,
            severity=severity,
            description=description,
            timestamp=time.time(),
        )
        try:
            with open(self._alerts_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert.to_dict()) + "\n")
        except Exception:
            pass
        self._log("alert.created", alert.to_dict())
        return alert

    def get_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent traffic alerts."""
        if not self._alerts_file.exists():
            return []
        try:
            lines = self._alerts_file.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    # --------------------------------------------------- firewall management

    def firewall_status(self) -> dict[str, Any]:
        """Get firewall status."""
        if not self._iptables or not self._is_linux:
            return {
                "available": False,
                "reason": "iptables not available (Linux only)",
            }
        try:
            result = subprocess.run(
                [self._iptables, "-L", "-n"],  # type: ignore
                capture_output=True, text=True, timeout=10,
            )
            return {
                "available": True,
                "rules": result.stdout,
            }
        except Exception as e:
            return {"available": True, "error": str(e)}

    def firewall_block_ip(self, ip: str) -> dict[str, Any]:
        """Block an IP address at the firewall.

        Requires Creator approval.
        """
        if not self._iptables or not self._is_linux:
            return {"success": False, "error": "iptables not available"}
        try:
            result = subprocess.run(
                [self._iptables, "-A", "INPUT", "-s", ip, "-j", "DROP"],  # type: ignore
                capture_output=True, text=True, timeout=10,
            )
            self._log("firewall.block", {"ip": ip, "success": result.returncode == 0})
            return {
                "success": result.returncode == 0,
                "error": result.stderr if result.returncode != 0 else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def firewall_unblock_ip(self, ip: str) -> dict[str, Any]:
        """Unblock an IP address at the firewall.

        Requires Creator approval.
        """
        if not self._iptables or not self._is_linux:
            return {"success": False, "error": "iptables not available"}
        try:
            result = subprocess.run(
                [self._iptables, "-D", "INPUT", "-s", ip, "-j", "DROP"],  # type: ignore
                capture_output=True, text=True, timeout=10,
            )
            self._log("firewall.unblock", {"ip": ip, "success": result.returncode == 0})
            return {
                "success": result.returncode == 0,
                "error": result.stderr if result.returncode != 0 else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------- quarantine

    def quarantine_device(self, device_id: str) -> dict[str, Any]:
        """Quarantine a device — block all traffic to/from it.

        Requires Creator approval. This is a serious action that
        isolates a device from the network.
        """
        device = self._devices.get(device_id)
        if device is None:
            return {"success": False, "error": "Device not found"}
        if not device.ip:
            return {"success": False, "error": "No IP for device"}

        device.quarantined = True
        self._save_devices()

        # Block at firewall if available
        if self._iptables and self._is_linux:
            self.firewall_block_ip(device.ip)

        self._log("device.quarantined", {
            "device_id": device_id,
            "ip": device.ip,
        })
        self._create_alert(
            alert_type="device_quarantined",
            source_ip=device.ip,
            severity="high",
            description=f"Device quarantined: {device.hostname or device.ip}",
        )

        return {"success": True, "device": device.to_dict()}

    def release_device(self, device_id: str) -> dict[str, Any]:
        """Release a quarantined device.

        Requires Creator approval.
        """
        device = self._devices.get(device_id)
        if device is None:
            return {"success": False, "error": "Device not found"}

        device.quarantined = False
        self._save_devices()

        if self._iptables and self._is_linux and device.ip:
            self.firewall_unblock_ip(device.ip)

        self._log("device.released", {"device_id": device_id})
        return {"success": True, "device": device.to_dict()}

    # --------------------------------------------------- monitoring

    def monitor_devices(self) -> dict[str, Any]:
        """Check status of all known devices. Returns summary."""
        now = time.time()
        active = 0
        stale = 0
        for device in self._devices.values():
            # Ping to check if active
            if self._ping_device(device.ip):
                device.last_seen = now
                active += 1
            else:
                # Device not responding
                if now - device.last_seen > 3600:  # 1 hour
                    stale += 1

        self._save_devices()
        return {
            "total": len(self._devices),
            "active": active,
            "stale": stale,
            "quarantined": sum(1 for d in self._devices.values() if d.quarantined),
            "unknown": sum(1 for d in self._devices.values() if not d.known),
        }

    def _ping_device(self, ip: str) -> bool:
        """Ping a device to check if it's online."""
        if not ip:
            return False
        try:
            param = "-n" if self._is_windows else "-c"
            cmd = [self._ping, param, "1", "-W", "2", ip]
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        """Get network operator status."""
        return {
            "local_ip": self._local_ip,
            "network_cidr": self.network_cidr,
            "gateway_ip": self.gateway_ip,
            "total_devices": len(self._devices),
            "trusted_devices": sum(1 for d in self._devices.values() if d.trusted),
            "unknown_devices": sum(1 for d in self._devices.values() if not d.known),
            "quarantined_devices": sum(1 for d in self._devices.values() if d.quarantined),
            "nmap_available": self._nmap is not None,
            "arp_scan_available": self._arp_scan is not None,
            "iptables_available": self._iptables is not None,
            "ssh_available": self._ssh is not None,
            "curl_available": self._curl is not None,
            "is_linux": self._is_linux,
            "total_alerts": len(self.get_alerts(limit=9999)),
        }

    # --------------------------------------------------- persistence

    def _load_devices(self) -> None:
        if not self._devices_file.exists():
            return
        try:
            data = json.loads(
                self._devices_file.read_text(encoding="utf-8")
            )
            for d_id, d_data in data.items():
                self._devices[d_id] = NetworkDevice(
                    device_id=d_data.get("device_id", d_id),
                    ip=d_data.get("ip", ""),
                    mac=d_data.get("mac", ""),
                    hostname=d_data.get("hostname", ""),
                    device_type=d_data.get("device_type", "unknown"),
                    vendor=d_data.get("vendor", ""),
                    os_guess=d_data.get("os_guess", ""),
                    ports=d_data.get("ports", []),
                    services=d_data.get("services", []),
                    first_seen=d_data.get("first_seen", 0),
                    last_seen=d_data.get("last_seen", 0),
                    known=d_data.get("known", False),
                    trusted=d_data.get("trusted", False),
                    quarantined=d_data.get("quarantined", False),
                    notes=d_data.get("notes", ""),
                )
        except Exception:
            pass

    def _save_devices(self) -> None:
        data = {d_id: d.to_dict() for d_id, d in self._devices.items()}
        self._devices_file.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _record_scan(self, devices: list[NetworkDevice]) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": time.time(),
                    "devices_found": len(devices),
                    "total_known": len(self._devices),
                }) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
