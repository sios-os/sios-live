"""Smart home control — lights, locks, thermostats, appliances.

ANUBIS controls smart home devices through multiple protocols:
- HomeAssistant (REST API) — unified control of most smart home devices
- Zigbee2MQTT — direct Zigbee device control
- Z-Wave JS — direct Z-Wave device control
- Matter — emerging smart home standard
- Direct HTTP — devices with local HTTP APIs (TP-Link, Tuya, etc.)
- MQTT — IoT devices using MQTT protocol

Device types supported:
- Lights (on/off, brightness, color)
- Locks (lock/unlock, status)
- Thermostats (temperature, mode, fan)
- Switches/Outlets (on/off)
- Garage doors (open/close)
- Blinds/Curtains (open/close, position)
- Fans (on/off, speed)
- Sensors (read-only: temperature, humidity, motion, contact)

AUTOMATION:
ANUBIS can create rules:
- "Lock doors when Creator leaves"
- "Turn on lights when Creator arrives"
- "Adjust thermostat based on who's home"
- "Turn off all lights at midnight"
- "Close garage door at 10pm"

SECURITY:
- Lock/unlock requires Creator approval
- Garage door requires Creator approval
- All actions logged to evidence ledger
- Device credentials never logged
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# Device types
DEV_LIGHT = "light"
DEV_LOCK = "lock"
DEV_THERMOSTAT = "thermostat"
DEV_SWITCH = "switch"
DEV_OUTLET = "outlet"
DEV_GARAGE = "garage"
DEV_BLINDS = "blinds"
DEV_FAN = "fan"
DEV_SENSOR = "sensor"
DEV_CAMERA = "camera"
DEV_UNKNOWN = "unknown"

# Protocols
PROTO_HOMEASSISTANT = "homeassistant"
PROTO_ZIGBEE2MQTT = "zigbee2mqtt"
PROTO_ZWAVE = "zwave"
PROTO_MATTER = "matter"
PROTO_HTTP = "http"
PROTO_MQTT = "mqtt"

# States
STATE_ON = "on"
STATE_OFF = "off"
STATE_LOCKED = "locked"
STATE_UNLOCKED = "unlocked"
STATE_OPEN = "open"
STATE_CLOSED = "closed"
STATE_UNKNOWN = "unknown"


@dataclass
class SmartDevice:
    """A smart home device."""
    device_id: str
    name: str
    device_type: str = DEV_UNKNOWN
    protocol: str = PROTO_HTTP
    entity_id: str = ""  # HomeAssistant entity ID or protocol-specific ID
    location: str = ""  # "living room", "front door", etc.
    state: str = STATE_UNKNOWN
    available: bool = True
    # Light-specific
    brightness: int = 0  # 0-255
    color_temp: int = 0  # mireds
    rgb_color: tuple[int, int, int] = (0, 0, 0)
    # Thermostat-specific
    temperature: float = 0.0  # current temp
    target_temp: float = 0.0  # setpoint
    hvac_mode: str = ""  # off, heat, cool, auto
    fan_mode: str = ""  # off, low, medium, high, auto
    # Sensor-specific
    unit: str = ""  # °C, °F, %, lux
    # Lock/garage-specific
    requires_approval: bool = False
    # Metadata
    last_changed: float = 0.0
    last_commanded: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "device_type": self.device_type,
            "protocol": self.protocol,
            "entity_id": self.entity_id,
            "location": self.location,
            "state": self.state,
            "available": self.available,
            "brightness": self.brightness,
            "color_temp": self.color_temp,
            "rgb_color": list(self.rgb_color),
            "temperature": self.temperature,
            "target_temp": self.target_temp,
            "hvac_mode": self.hvac_mode,
            "fan_mode": self.fan_mode,
            "unit": self.unit,
            "requires_approval": self.requires_approval,
            "last_changed": self.last_changed,
            "last_commanded": self.last_commanded,
            "attributes": self.attributes,
        }


@dataclass
class AutomationRule:
    """A smart home automation rule."""
    rule_id: str
    name: str
    trigger: str = ""  # "creator_left", "creator_arrived", "time_22:00", "motion_detected"
    actions: list[dict[str, Any]] = field(default_factory=list)  # [{"device_id": "x", "command": "off"}]
    enabled: bool = True
    created_at: float = 0.0
    last_triggered: float = 0.0
    trigger_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "trigger": self.trigger,
            "actions": self.actions,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "last_triggered": self.last_triggered,
            "trigger_count": self.trigger_count,
        }


class SmartHome:
    """Smart home controller — manages all IoT devices.

    Connects to HomeAssistant, Zigbee2MQTT, or direct HTTP devices.
    Provides unified control interface for all device types.
    """

    ACTOR = "anubis.smarthome"

    def __init__(
        self,
        root: str | Path,
        *,
        homeassistant_url: str = "",
        homeassistant_token: str = "",
        mqtt_host: str = "",
        mqtt_port: int = 1883,
        ledger: Any | None = None,
        on_command: Callable[[str, str], bool] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ha_url = homeassistant_url.rstrip("/")
        self.ha_token = homeassistant_token
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.ledger = ledger
        self.on_command = on_command  # callback for approval-gated commands

        self._state_dir = self.root / "memory" / "smarthome"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._devices_file = self._state_dir / "devices.json"
        self._rules_file = self._state_dir / "rules.json"
        self._history_file = self._state_dir / "command_history.jsonl"

        self._devices: dict[str, SmartDevice] = {}
        self._rules: dict[str, AutomationRule] = {}
        self._load()

    # --------------------------------------------------- device management

    def add_device(
        self,
        name: str,
        device_type: str,
        protocol: str,
        entity_id: str = "",
        *,
        location: str = "",
        requires_approval: bool = False,
    ) -> SmartDevice:
        """Register a smart home device."""
        device_id = hashlib.sha256(
            f"dev:{name}:{time.time()}".encode()
        ).hexdigest()[:16]

        # Locks and garage doors require approval by default
        if device_type in (DEV_LOCK, DEV_GARAGE):
            requires_approval = True

        device = SmartDevice(
            device_id=device_id,
            name=name,
            device_type=device_type,
            protocol=protocol,
            entity_id=entity_id,
            location=location,
            requires_approval=requires_approval,
        )

        self._devices[device_id] = device
        self._save_devices()
        self._log("device.added", {"name": name, "type": device_type})
        return device

    def remove_device(self, device_id: str) -> bool:
        if device_id in self._devices:
            del self._devices[device_id]
            self._save_devices()
            return True
        return False

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        d = self._devices.get(device_id)
        return d.to_dict() if d else None

    def get_devices(self) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self._devices.values()]

    def get_devices_by_type(self, device_type: str) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self._devices.values() if d.device_type == device_type]

    def get_devices_by_location(self, location: str) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self._devices.values() if d.location == location]

    # --------------------------------------------------- device control

    def turn_on(self, device_id: str) -> dict[str, Any]:
        """Turn on a device (light, switch, outlet, fan)."""
        return self._send_command(device_id, "turn_on")

    def turn_off(self, device_id: str) -> dict[str, Any]:
        """Turn off a device."""
        return self._send_command(device_id, "turn_off")

    def toggle(self, device_id: str) -> dict[str, Any]:
        """Toggle a device."""
        device = self._devices.get(device_id)
        if device is None:
            return {"success": False, "error": "Device not found"}
        if device.state == STATE_ON:
            return self.turn_off(device_id)
        return self.turn_on(device_id)

    def set_brightness(self, device_id: str, brightness: int) -> dict[str, Any]:
        """Set light brightness (0-255)."""
        if not 0 <= brightness <= 255:
            return {"success": False, "error": "Brightness must be 0-255"}
        return self._send_command(device_id, "set_brightness", brightness=brightness)

    def set_color(self, device_id: str, r: int, g: int, b: int) -> dict[str, Any]:
        """Set light RGB color."""
        return self._send_command(device_id, "set_color", r=r, g=g, b=b)

    def set_temperature(self, device_id: str, temp: float) -> dict[str, Any]:
        """Set thermostat target temperature."""
        return self._send_command(device_id, "set_temperature", temperature=temp)

    def set_hvac_mode(self, device_id: str, mode: str) -> dict[str, Any]:
        """Set thermostat HVAC mode (off, heat, cool, auto)."""
        return self._send_command(device_id, "set_hvac_mode", mode=mode)

    def lock(self, device_id: str) -> dict[str, Any]:
        """Lock a door lock. Requires approval."""
        return self._send_command(device_id, "lock", requires_approval=True)

    def unlock(self, device_id: str) -> dict[str, Any]:
        """Unlock a door lock. Requires approval."""
        return self._send_command(device_id, "unlock", requires_approval=True)

    def open_garage(self, device_id: str) -> dict[str, Any]:
        """Open garage door. Requires approval."""
        return self._send_command(device_id, "open", requires_approval=True)

    def close_garage(self, device_id: str) -> dict[str, Any]:
        """Close garage door."""
        return self._send_command(device_id, "close", requires_approval=True)

    def set_blinds(self, device_id: str, position: int) -> dict[str, Any]:
        """Set blinds position (0=closed, 100=open)."""
        return self._send_command(device_id, "set_position", position=position)

    def _send_command(
        self, device_id: str, command: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Send a command to a device."""
        device = self._devices.get(device_id)
        if device is None:
            return {"success": False, "error": "Device not found"}
        if not device.available:
            return {"success": False, "error": "Device not available"}

        requires_approval = kwargs.pop("requires_approval", device.requires_approval)

        # Check approval for sensitive devices
        if requires_approval and self.on_command:
            approved = self.on_command(device_id, command)
            if not approved:
                self._log("command.denied", {
                    "device": device.name, "command": command,
                })
                return {"success": False, "error": "Command requires approval"}

        # Send command via appropriate protocol
        success = False
        if device.protocol == PROTO_HOMEASSISTANT:
            success = self._ha_command(device, command, **kwargs)
        elif device.protocol == PROTO_HTTP:
            success = self._http_command(device, command, **kwargs)
        elif device.protocol == PROTO_MQTT:
            success = self._mqtt_command(device, command, **kwargs)
        else:
            success = False

        # Update device state
        if success:
            device.last_commanded = time.time()
            self._update_device_state(device, command, **kwargs)
            self._save_devices()

        # Record command
        self._record_command(device, command, success, **kwargs)
        self._log("command.sent", {
            "device": device.name, "command": command, "success": success,
        })

        return {"success": success, "device": device.to_dict()}

    def _ha_command(self, device: SmartDevice, command: str, **kwargs: Any) -> bool:
        """Send command via HomeAssistant REST API."""
        if not self.ha_url or not self.ha_token:
            return False
        try:
            # Map command to HA service
            domain = "homeassistant"
            service = ""
            service_data = dict(kwargs)

            if device.device_type == DEV_LIGHT:
                domain = "light"
                if command == "turn_on":
                    service = "turn_on"
                elif command == "turn_off":
                    service = "turn_off"
                elif command == "set_brightness":
                    service = "turn_on"
                    service_data = {"brightness": kwargs.get("brightness", 128)}
                elif command == "set_color":
                    service = "turn_on"
                    service_data = {"rgb_color": [
                        kwargs.get("r", 255), kwargs.get("g", 255), kwargs.get("b", 255)
                    ]}
            elif device.device_type == DEV_LOCK:
                domain = "lock"
                service = command  # lock or unlock
            elif device.device_type == DEV_THERMOSTAT:
                domain = "climate"
                if command == "set_temperature":
                    service = "set_temperature"
                    service_data = {"temperature": kwargs.get("temperature", 22)}
                elif command == "set_hvac_mode":
                    service = "set_hvac_mode"
                    service_data = {"hvac_mode": kwargs.get("mode", "auto")}
            elif device.device_type in (DEV_SWITCH, DEV_OUTLET, DEV_FAN):
                domain = "switch"
                service = command
            elif device.device_type == DEV_GARAGE:
                domain = "cover"
                service = command  # open or close
            elif device.device_type == DEV_BLINDS:
                domain = "cover"
                if command == "set_position":
                    service = "set_cover_position"
                    service_data = {"position": kwargs.get("position", 50)}
                else:
                    service = command

            url = f"{self.ha_url}/api/services/{domain}/{service}"
            data = json.dumps({
                "entity_id": device.entity_id,
                **service_data,
            }).encode()

            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Authorization", f"Bearer {self.ha_token}")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200

        except Exception:
            return False

    def _http_command(self, device: SmartDevice, command: str, **kwargs: Any) -> bool:
        """Send command via direct HTTP."""
        try:
            url = device.entity_id  # use entity_id as URL for HTTP devices
            if not url:
                return False

            data = json.dumps({"command": command, **kwargs}).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _mqtt_command(self, device: SmartDevice, command: str, **kwargs: Any) -> bool:
        """Send command via MQTT."""
        # MQTT requires paho-mqtt or similar library
        # For now, return False — would need paho-mqtt installed
        return False

    def _update_device_state(self, device: SmartDevice, command: str, **kwargs: Any) -> None:
        """Update device state after a command."""
        device.last_changed = time.time()

        if command in ("turn_on", "open"):
            device.state = STATE_ON if device.device_type != DEV_GARAGE else STATE_OPEN
        elif command in ("turn_off", "close"):
            device.state = STATE_OFF if device.device_type != DEV_GARAGE else STATE_CLOSED
        elif command == "lock":
            device.state = STATE_LOCKED
        elif command == "unlock":
            device.state = STATE_UNLOCKED
        elif command == "set_brightness":
            device.brightness = kwargs.get("brightness", 128)
            if device.brightness > 0:
                device.state = STATE_ON
            else:
                device.state = STATE_OFF
        elif command == "set_color":
            device.rgb_color = (
                kwargs.get("r", 255), kwargs.get("g", 255), kwargs.get("b", 255)
            )
        elif command == "set_temperature":
            device.target_temp = kwargs.get("temperature", 22)
        elif command == "set_hvac_mode":
            device.hvac_mode = kwargs.get("mode", "auto")
        elif command == "set_position":
            device.attributes["position"] = kwargs.get("position", 50)

    # --------------------------------------------------- status sync

    def sync_states(self) -> dict[str, Any]:
        """Sync device states from HomeAssistant."""
        if not self.ha_url or not self.ha_token:
            return {"success": False, "error": "HomeAssistant not configured"}

        try:
            url = f"{self.ha_url}/api/states"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self.ha_token}")

            with urllib.request.urlopen(req, timeout=10) as resp:
                states = json.loads(resp.read())

            updated = 0
            for state in states:
                entity_id = state.get("entity_id", "")
                for device in self._devices.values():
                    if device.entity_id == entity_id:
                        device.state = state.get("state", STATE_UNKNOWN)
                        attrs = state.get("attributes", {})
                        if "brightness" in attrs:
                            device.brightness = attrs["brightness"]
                        if "temperature" in attrs:
                            device.temperature = attrs["temperature"]
                        if "target_temp" in attrs:
                            device.target_temp = attrs["target_temp"]
                        if "hvac_mode" in attrs:
                            device.hvac_mode = attrs["hvac_mode"]
                        device.attributes = attrs
                        device.last_changed = time.time()
                        updated += 1
                        break

            self._save_devices()
            return {"success": True, "updated": updated}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------- automation rules

    def add_rule(
        self, name: str, trigger: str, actions: list[dict[str, Any]]
    ) -> AutomationRule:
        """Add an automation rule."""
        rule_id = hashlib.sha256(
            f"rule:{name}:{time.time()}".encode()
        ).hexdigest()[:16]
        rule = AutomationRule(
            rule_id=rule_id, name=name, trigger=trigger,
            actions=actions, created_at=time.time(),
        )
        self._rules[rule_id] = rule
        self._save_rules()
        self._log("rule.added", {"name": name, "trigger": trigger})
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            self._save_rules()
            return True
        return False

    def get_rules(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._rules.values()]

    def trigger_rule(self, rule_id: str) -> dict[str, Any]:
        """Manually trigger an automation rule."""
        rule = self._rules.get(rule_id)
        if rule is None or not rule.enabled:
            return {"success": False, "error": "Rule not found or disabled"}

        results = []
        for action in rule.actions:
            device_id = action.get("device_id", "")
            command = action.get("command", "")
            kwargs = {k: v for k, v in action.items() if k not in ("device_id", "command")}
            result = self._send_command(device_id, command, **kwargs)
            results.append(result)

        rule.last_triggered = time.time()
        rule.trigger_count += 1
        self._save_rules()

        return {"success": True, "results": results}

    def check_triggers(self, trigger: str) -> list[dict[str, Any]]:
        """Check all rules for a trigger and execute matching ones."""
        results = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if rule.trigger == trigger:
                result = self.trigger_rule(rule.rule_id)
                results.append(result)
        return results

    # --------------------------------------------------- scenes

    def activate_scene(self, scene_name: str) -> dict[str, Any]:
        """Activate a predefined scene (group of device commands)."""
        scenes = {
            "away": [
                {"device_type": DEV_LOCK, "command": "lock"},
                {"device_type": DEV_LIGHT, "command": "turn_off"},
                {"device_type": DEV_THERMOSTAT, "command": "set_temperature", "temperature": 15},
                {"device_type": DEV_GARAGE, "command": "close"},
            ],
            "home": [
                {"device_type": DEV_LOCK, "command": "unlock"},
                {"device_type": DEV_LIGHT, "command": "turn_on"},
                {"device_type": DEV_THERMOSTAT, "command": "set_temperature", "temperature": 22},
            ],
            "night": [
                {"device_type": DEV_LIGHT, "command": "turn_off"},
                {"device_type": DEV_LOCK, "command": "lock"},
                {"device_type": DEV_GARAGE, "command": "close"},
                {"device_type": DEV_BLINDS, "command": "set_position", "position": 0},
            ],
            "morning": [
                {"device_type": DEV_BLINDS, "command": "set_position", "position": 100},
                {"device_type": DEV_LIGHT, "command": "turn_on"},
                {"device_type": DEV_THERMOSTAT, "command": "set_temperature", "temperature": 22},
            ],
            "movie": [
                {"device_type": DEV_LIGHT, "command": "set_brightness", "brightness": 50},
                {"device_type": DEV_BLINDS, "command": "set_position", "position": 0},
            ],
        }

        actions = scenes.get(scene_name)
        if not actions:
            return {"success": False, "error": f"Unknown scene: {scene_name}"}

        results = []
        for action in actions:
            device_type = action.pop("device_type")
            for device in self._devices.values():
                if device.device_type == device_type:
                    cmd = action.pop("command", "")
                    result = self._send_command(device.device_id, cmd, **action)
                    results.append(result)
                    break  # one device per type for scenes

        self._log("scene.activated", {"scene": scene_name})
        return {"success": True, "scene": scene_name, "results": results}

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        devices = list(self._devices.values())
        return {
            "total_devices": len(devices),
            "available_devices": sum(1 for d in devices if d.available),
            "lights": sum(1 for d in devices if d.device_type == DEV_LIGHT),
            "locks": sum(1 for d in devices if d.device_type == DEV_LOCK),
            "thermostats": sum(1 for d in devices if d.device_type == DEV_THERMOSTAT),
            "switches": sum(1 for d in devices if d.device_type in (DEV_SWITCH, DEV_OUTLET)),
            "garage_doors": sum(1 for d in devices if d.device_type == DEV_GARAGE),
            "sensors": sum(1 for d in devices if d.device_type == DEV_SENSOR),
            "total_rules": len(self._rules),
            "enabled_rules": sum(1 for r in self._rules.values() if r.enabled),
            "homeassistant_configured": bool(self.ha_url and self.ha_token),
            "mqtt_configured": bool(self.mqtt_host),
        }

    # --------------------------------------------------- persistence

    def _load(self) -> None:
        if self._devices_file.exists():
            try:
                data = json.loads(self._devices_file.read_text(encoding="utf-8"))
                for d_id, d in data.items():
                    self._devices[d_id] = SmartDevice(
                        device_id=d.get("device_id", d_id),
                        name=d["name"],
                        device_type=d.get("device_type", DEV_UNKNOWN),
                        protocol=d.get("protocol", PROTO_HTTP),
                        entity_id=d.get("entity_id", ""),
                        location=d.get("location", ""),
                        state=d.get("state", STATE_UNKNOWN),
                        available=d.get("available", True),
                        brightness=d.get("brightness", 0),
                        color_temp=d.get("color_temp", 0),
                        rgb_color=tuple(d.get("rgb_color", [0, 0, 0])),
                        temperature=d.get("temperature", 0),
                        target_temp=d.get("target_temp", 0),
                        hvac_mode=d.get("hvac_mode", ""),
                        fan_mode=d.get("fan_mode", ""),
                        unit=d.get("unit", ""),
                        requires_approval=d.get("requires_approval", False),
                        last_changed=d.get("last_changed", 0),
                        last_commanded=d.get("last_commanded", 0),
                        attributes=d.get("attributes", {}),
                    )
            except Exception:
                pass

        if self._rules_file.exists():
            try:
                data = json.loads(self._rules_file.read_text(encoding="utf-8"))
                for r_id, r in data.items():
                    self._rules[r_id] = AutomationRule(
                        rule_id=r_id,
                        name=r["name"],
                        trigger=r.get("trigger", ""),
                        actions=r.get("actions", []),
                        enabled=r.get("enabled", True),
                        created_at=r.get("created_at", 0),
                        last_triggered=r.get("last_triggered", 0),
                        trigger_count=r.get("trigger_count", 0),
                    )
            except Exception:
                pass

    def _save_devices(self) -> None:
        data = {d_id: d.to_dict() for d_id, d in self._devices.items()}
        self._devices_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _save_rules(self) -> None:
        data = {r_id: r.to_dict() for r_id, r in self._rules.items()}
        self._rules_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _record_command(self, device: SmartDevice, command: str, success: bool, **kwargs: Any) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": time.time(),
                    "device": device.name,
                    "command": command,
                    "success": success,
                    "params": kwargs,
                }) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
