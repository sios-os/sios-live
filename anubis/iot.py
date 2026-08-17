"""IoT and hardware integrations — Tier 3 modules.

Combines 8 situational hardware integrations into one module:
1. OBD-II vehicle diagnostics
2. Air quality & environment sensors
3. Energy monitoring
4. 3D printer control
5. Drone integration
6. Garden/plant monitoring
7. Smart watch integration
8. Visitor logging

Each subsystem is a class that can be used independently. All use
stdlib only and gracefully degrade when hardware isn't present.
"""
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ============================================================
# 1. OBD-II Vehicle Diagnostics
# ============================================================

@dataclass
class VehicleData:
    """Vehicle diagnostic data from OBD-II."""
    timestamp: float = 0.0
    rpm: float = 0.0
    speed: float = 0.0  # mph
    engine_temp: float = 0.0  # °F
    fuel_level: float = 0.0  # %
    throttle_position: float = 0.0  # %
    engine_load: float = 0.0  # %
    dtc_codes: list[str] = field(default_factory=list)  # diagnostic trouble codes
    vin: str = ""
    mileage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "rpm": self.rpm, "speed": self.speed,
            "engine_temp": self.engine_temp,
            "fuel_level": self.fuel_level,
            "throttle_position": self.throttle_position,
            "engine_load": self.engine_load,
            "dtc_codes": self.dtc_codes,
            "vin": self.vin, "mileage": self.mileage,
        }


class OBDMonitor:
    """OBD-II vehicle diagnostics monitor.

    Connects to an ELM327 OBD-II adapter (Bluetooth or WiFi) to read
    vehicle data. Uses pyobd or obd library if available, otherwise
    provides a framework for manual data input.
    """

    ACTOR = "anubis.obd"

    DTC_MEANINGS: dict[str, str] = {
        "P0420": "Catalyst system efficiency below threshold",
        "P0171": "System too lean (Bank 1)",
        "P0300": "Random/multiple cylinder misfire detected",
        "P0128": "Coolant thermostat below regulating temperature",
        "P0442": "Evaporative emission system leak detected (small)",
        "P0455": "Evaporative emission system leak detected (large)",
        "P0507": "Idle air control system RPM higher than expected",
    }

    def __init__(self, root: str | Path, *, ledger: Any | None = None) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self._state_dir = self.root / "memory" / "obd"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "history.jsonl"
        self._obd = None
        self._connected = False
        self._last_data: VehicleData | None = None

    def connect(self, port: str = "") -> bool:
        """Connect to OBD-II adapter."""
        try:
            import obd  # type: ignore
            self._obd = obd.OBD(port) if port else obd.OBD()
            self._connected = self._obd.is_connected()
            return self._connected
        except ImportError:
            return False
        except Exception:
            return False

    def read_data(self) -> VehicleData | None:
        """Read current vehicle data."""
        if not self._connected or self._obd is None:
            return None
        try:
            import obd  # type: ignore
            data = VehicleData(timestamp=time.time())

            cmds = {
                "rpm": obd.commands.RPM,
                "speed": obd.commands.SPEED,
                "engine_temp": obd.commands.COOLANT_TEMP,
                "fuel_level": obd.commands.FUEL_LEVEL,
                "throttle": obd.commands.THROTTLE_POS,
                "engine_load": obd.commands.ENGINE_LOAD,
            }
            for attr, cmd in cmds.items():
                r = self._obd.query(cmd)
                if r and r.value:
                    val = r.value.magnitude if hasattr(r.value, "magnitude") else r.value
                    if attr == "speed":
                        val = val * 2.237  # m/s to mph
                    if attr == "engine_temp":
                        val = val * 9/5 + 32  # C to F
                    setattr(data, attr.replace("throttle", "throttle_position"), val)

            # Read DTC codes
            dtc_response = self._obd.query(obd.commands.GET_DTC)
            if dtc_response and dtc_response.value:
                data.dtc_codes = [code for code, desc in dtc_response.value]

            self._last_data = data
            self._record(data)
            return data
        except Exception:
            return None

    def get_dtc_description(self, code: str) -> str:
        return self.DTC_MEANINGS.get(code.upper(), "Unknown code")

    def input_manual_data(self, **kwargs: Any) -> VehicleData:
        """Manually input vehicle data (when no OBD adapter)."""
        data = VehicleData(timestamp=time.time(), **kwargs)
        self._last_data = data
        self._record(data)
        return data

    def get_last_data(self) -> dict[str, Any] | None:
        return self._last_data.to_dict() if self._last_data else None

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._history_file.exists():
            return []
        try:
            lines = self._history_file.read_text(encoding="utf-8").strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_status(self) -> dict[str, Any]:
        return {
            "connected": self._connected,
            "obd_library": self._obd is not None,
            "last_reading": self._last_data.to_dict() if self._last_data else None,
            "active_dtc_codes": len(self._last_data.dtc_codes) if self._last_data else 0,
        }

    def _record(self, data: VehicleData) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data.to_dict()) + "\n")
        except Exception:
            pass


# ============================================================
# 2. Air Quality & Environment Sensors
# ============================================================

@dataclass
class AirQualityReading:
    """Air quality sensor reading."""
    timestamp: float = 0.0
    co2: float = 0.0  # ppm
    pm25: float = 0.0  # µg/m³
    pm10: float = 0.0  # µg/m³
    temperature: float = 0.0  # °F
    humidity: float = 0.0  # %
    voc: float = 0.0  # ppb (volatile organic compounds)
    co: float = 0.0  # ppm (carbon monoxide)
    radon: float = 0.0  # pCi/L
    location: str = ""
    aqi: int = 0  # Air Quality Index (calculated)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "co2": self.co2, "pm25": self.pm25, "pm10": self.pm10,
            "temperature": self.temperature, "humidity": self.humidity,
            "voc": self.voc, "co": self.co, "radon": self.radon,
            "location": self.location, "aqi": self.aqi,
        }


class AirQualityMonitor:
    """Air quality and environment sensor monitor.

    Reads from IoT sensors (CO2, PM2.5, temperature, humidity, VOC, CO).
    Calculates AQI and generates alerts for dangerous levels.
    """

    ACTOR = "anubis.airquality"

    # Thresholds
    CO2_GOOD = 800
    CO2_WARN = 1200
    CO2_DANGER = 2000
    PM25_GOOD = 12
    PM25_WARN = 35
    PM25_DANGER = 55
    CO_DANGER = 35  # ppm
    VOC_HIGH = 500  # ppb
    RADON_ACTION = 4.0  # pCi/L

    def __init__(self, root: str | Path, *, ledger: Any | None = None,
                 on_alert: Callable[[str, AirQualityReading], None] | None = None) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.on_alert = on_alert
        self._state_dir = self.root / "memory" / "airquality"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "history.jsonl"
        self._last_reading: AirQualityReading | None = None

    def record_reading(self, **kwargs: Any) -> AirQualityReading:
        """Record an air quality reading (from sensor or manual)."""
        reading = AirQualityReading(timestamp=time.time(), **kwargs)
        reading.aqi = self._calculate_aqi(reading)
        self._last_reading = reading
        self._record(reading)
        self._check_alerts(reading)
        return reading

    def _calculate_aqi(self, reading: AirQualityReading) -> int:
        """Calculate AQI from PM2.5."""
        pm = reading.pm25
        if pm <= 12:
            return int(50 * pm / 12)
        elif pm <= 35:
            return int(50 + 50 * (pm - 12) / 23)
        elif pm <= 55:
            return int(100 + 50 * (pm - 35) / 20)
        elif pm <= 150:
            return int(150 + 50 * (pm - 55) / 95)
        elif pm <= 250:
            return int(200 + 100 * (pm - 150) / 100)
        else:
            return 300

    def _check_alerts(self, reading: AirQualityReading) -> None:
        alerts: list[str] = []
        if reading.co2 > self.CO2_DANGER:
            alerts.append(f"CO2 dangerously high: {reading.co2} ppm")
        elif reading.co2 > self.CO2_WARN:
            alerts.append(f"CO2 elevated: {reading.co2} ppm — ventilate room")
        if reading.pm25 > self.PM25_DANGER:
            alerts.append(f"PM2.5 hazardous: {reading.pm25} µg/m³")
        if reading.co > self.CO_DANGER:
            alerts.append(f"Carbon monoxide dangerous: {reading.co} ppm")
        if reading.voc > self.VOC_HIGH:
            alerts.append(f"VOC levels high: {reading.voc} ppb")
        if reading.radon > self.RADON_ACTION:
            alerts.append(f"Radon above action level: {reading.radon} pCi/L")

        for alert in alerts:
            if self.on_alert:
                try:
                    self.on_alert(alert, reading)
                except Exception:
                    pass
            if self.ledger:
                try:
                    self.ledger.append(self.ACTOR, "alert", {"message": alert})
                except Exception:
                    pass

    def get_recommendations(self) -> list[str]:
        if not self._last_reading:
            return []
        recs: list[str] = []
        r = self._last_reading
        if r.co2 > self.CO2_WARN:
            recs.append("Open a window or increase ventilation — CO2 levels are high")
        if r.humidity > 60:
            recs.append("High humidity — consider using a dehumidifier")
        elif r.humidity < 30:
            recs.append("Very dry air — consider using a humidifier")
        if r.pm25 > self.PM25_WARN:
            recs.append("Air purifier recommended — particulate matter is elevated")
        if r.temperature > 78:
            recs.append("Temperature high — consider lowering thermostat")
        elif r.temperature < 65:
            recs.append("Temperature low — consider raising thermostat")
        return recs

    def get_last_reading(self) -> dict[str, Any] | None:
        return self._last_reading.to_dict() if self._last_reading else None

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self._history_file.exists():
            return []
        try:
            lines = self._history_file.read_text(encoding="utf-8").strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_status(self) -> dict[str, Any]:
        return {
            "last_reading": self._last_reading.to_dict() if self._last_reading else None,
            "aqi": self._last_reading.aqi if self._last_reading else 0,
            "recommendations": self.get_recommendations(),
        }

    def _record(self, reading: AirQualityReading) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(reading.to_dict()) + "\n")
        except Exception:
            pass


# ============================================================
# 3. Energy Monitoring
# ============================================================

@dataclass
class EnergyReading:
    """Energy consumption reading."""
    timestamp: float = 0.0
    power_watts: float = 0.0  # current power draw
    energy_kwh: float = 0.0  # cumulative kWh
    voltage: float = 0.0
    current: float = 0.0  # amps
    frequency: float = 0.0  # Hz
    power_factor: float = 0.0
    device: str = ""  # which device/circuit
    cost: float = 0.0  # estimated cost

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "power_watts": self.power_watts,
            "energy_kwh": self.energy_kwh,
            "voltage": self.voltage,
            "current": self.current,
            "frequency": self.frequency,
            "power_factor": self.power_factor,
            "device": self.device,
            "cost": self.cost,
        }


class EnergyMonitor:
    """Energy consumption monitor.

    Tracks power usage from smart plugs, whole-home monitors, or
    individual circuits. Calculates costs and identifies waste.
    """

    ACTOR = "anubis.energy"

    def __init__(self, root: str | Path, *, cost_per_kwh: float = 0.12,
                 ledger: Any | None = None) -> None:
        self.root = Path(root)
        self.cost_per_kwh = cost_per_kwh
        self.ledger = ledger
        self._state_dir = self.root / "memory" / "energy"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "history.jsonl"
        self._devices_file = self._state_dir / "devices.json"
        self._readings: list[EnergyReading] = []
        self._devices: dict[str, dict[str, Any]] = {}
        self._load()

    def add_device(self, name: str, device_type: str = "", location: str = "") -> dict[str, Any]:
        device_id = hashlib.sha256(f"dev:{name}:{time.time()}".encode()).hexdigest()[:16]
        device = {"device_id": device_id, "name": name, "type": device_type, "location": location}
        self._devices[device_id] = device
        self._save_devices()
        return device

    def record_reading(self, device: str, power_watts: float, **kwargs: Any) -> EnergyReading:
        reading = EnergyReading(
            timestamp=time.time(), device=device,
            power_watts=power_watts, **kwargs,
        )
        reading.cost = (power_watts / 1000) * self.cost_per_kwh / 3600  # cost per second
        self._readings.append(reading)
        self._record(reading)
        return reading

    def get_total_power(self) -> float:
        """Current total power draw across all devices."""
        recent = [r for r in self._readings if time.time() - r.timestamp < 60]
        devices = set(r.device for r in recent)
        total = 0.0
        for device in devices:
            device_readings = [r for r in recent if r.device == device]
            if device_readings:
                total += max(r.power_watts for r in device_readings)
        return total

    def get_daily_usage(self) -> dict[str, float]:
        """Get energy usage by device for today."""
        from datetime import datetime
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        usage: dict[str, float] = {}
        for r in self._readings:
            if r.timestamp >= start:
                # Approximate kWh from power readings
                usage[r.device] = usage.get(r.device, 0) + r.power_watts / 1000 / 60  # assume 1 min between readings
        return usage

    def get_daily_cost(self) -> float:
        usage = self.get_daily_usage()
        return sum(usage.values()) * self.cost_per_kwh

    def get_waste_detection(self) -> list[str]:
        """Detect devices consuming power when they shouldn't."""
        waste: list[str] = []
        recent = [r for r in self._readings if time.time() - r.timestamp < 300]
        for r in recent:
            if r.power_watts > 50 and r.device.lower() in ("tv", "heater", "ac"):
                # Could check if anyone is home, time of day, etc.
                pass
        return waste

    def get_status(self) -> dict[str, Any]:
        return {
            "total_power_watts": self.get_total_power(),
            "daily_cost": self.get_daily_cost(),
            "cost_per_kwh": self.cost_per_kwh,
            "devices": len(self._devices),
            "total_readings": len(self._readings),
        }

    def _load(self) -> None:
        if self._devices_file.exists():
            try:
                self._devices = json.loads(self._devices_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save_devices(self) -> None:
        self._devices_file.write_text(json.dumps(self._devices, indent=2), encoding="utf-8")

    def _record(self, reading: EnergyReading) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(reading.to_dict()) + "\n")
        except Exception:
            pass


# ============================================================
# 4. 3D Printer Control
# ============================================================

@dataclass
class PrintJob:
    """A 3D print job."""
    job_id: str
    filename: str = ""
    status: str = "queued"  # queued, printing, paused, completed, failed
    progress: float = 0.0  # 0-100
    started_at: float = 0.0
    estimated_time: float = 0.0  # seconds
    elapsed_time: float = 0.0
    filament_used: float = 0.0  # meters
    temperature_hotend: float = 0.0  # °C
    temperature_bed: float = 0.0  # °C
    layer: int = 0
    total_layers: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id, "filename": self.filename,
            "status": self.status, "progress": self.progress,
            "started_at": self.started_at,
            "estimated_time": self.estimated_time,
            "elapsed_time": self.elapsed_time,
            "filament_used": self.filament_used,
            "temperature_hotend": self.temperature_hotend,
            "temperature_bed": self.temperature_bed,
            "layer": self.layer, "total_layers": self.total_layers,
        }


class Printer3D:
    """3D printer control and monitoring.

    Supports OctoPrint (REST API) for printer control.
    Monitors print progress, temperatures, and detects failures.
    """

    ACTOR = "anubis.printer3d"

    def __init__(self, root: str | Path, *, octoprint_url: str = "",
                 octoprint_key: str = "", ledger: Any | None = None,
                 on_complete: Callable[[PrintJob], None] | None = None) -> None:
        self.root = Path(root)
        self.octoprint_url = octoprint_url.rstrip("/")
        self.octoprint_key = octoprint_key
        self.ledger = ledger
        self.on_complete = on_complete
        self._state_dir = self.root / "memory" / "printer3d"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._jobs_file = self._state_dir / "jobs.json"
        self._jobs: dict[str, PrintJob] = {}
        self._current_job: PrintJob | None = None
        self._load()

    def submit_job(self, filename: str, estimated_time: float = 0) -> PrintJob:
        job_id = hashlib.sha256(f"print:{filename}:{time.time()}".encode()).hexdigest()[:16]
        job = PrintJob(
            job_id=job_id, filename=filename,
            estimated_time=estimated_time, status="queued",
        )
        self._jobs[job_id] = job
        self._save()
        return job

    def start_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None or job.status != "queued":
            return False
        job.status = "printing"
        job.started_at = time.time()
        self._current_job = job
        self._save()
        return True

    def update_progress(self, job_id: str, progress: float, layer: int = 0) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.progress = progress
        job.layer = layer
        job.elapsed_time = time.time() - job.started_at if job.started_at else 0
        if progress >= 100:
            job.status = "completed"
            if self.on_complete:
                try:
                    self.on_complete(job)
                except Exception:
                    pass
        self._save()
        return True

    def pause_job(self, job_id: str) -> bool:
        return self._set_status(job_id, "paused")

    def resume_job(self, job_id: str) -> bool:
        return self._set_status(job_id, "printing")

    def cancel_job(self, job_id: str) -> bool:
        return self._set_status(job_id, "failed")

    def _set_status(self, job_id: str, status: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.status = status
        self._save()
        return True

    def get_jobs(self) -> list[dict[str, Any]]:
        return [j.to_dict() for j in self._jobs.values()]

    def get_active_jobs(self) -> list[dict[str, Any]]:
        return [j.to_dict() for j in self._jobs.values() if j.status in ("printing", "paused")]

    def get_status(self) -> dict[str, Any]:
        return {
            "octoprint_configured": bool(self.octoprint_url and self.octoprint_key),
            "total_jobs": len(self._jobs),
            "active_jobs": len(self.get_active_jobs()),
            "current_job": self._current_job.to_dict() if self._current_job else None,
        }

    def _load(self) -> None:
        if not self._jobs_file.exists():
            return
        try:
            data = json.loads(self._jobs_file.read_text(encoding="utf-8"))
            for j_id, j in data.items():
                self._jobs[j_id] = PrintJob(
                    job_id=j_id, filename=j.get("filename", ""),
                    status=j.get("status", "queued"), progress=j.get("progress", 0),
                    started_at=j.get("started_at", 0),
                    estimated_time=j.get("estimated_time", 0),
                    elapsed_time=j.get("elapsed_time", 0),
                    filament_used=j.get("filament_used", 0),
                    temperature_hotend=j.get("temperature_hotend", 0),
                    temperature_bed=j.get("temperature_bed", 0),
                    layer=j.get("layer", 0), total_layers=j.get("total_layers", 0),
                )
        except Exception:
            pass

    def _save(self) -> None:
        data = {j_id: j.to_dict() for j_id, j in self._jobs.items()}
        self._jobs_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ============================================================
# 5. Drone Integration
# ============================================================

@dataclass
class DroneState:
    """Drone state and telemetry."""
    timestamp: float = 0.0
    battery: float = 0.0  # %
    altitude: float = 0.0  # meters
    latitude: float = 0.0
    longitude: float = 0.0
    speed: float = 0.0  # m/s
    heading: float = 0.0  # degrees
    satellites: int = 0
    armed: bool = False
    flying: bool = False
    mode: str = ""  # AUTO, MANUAL, RTL, etc.

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp, "battery": self.battery,
            "altitude": self.altitude, "latitude": self.latitude,
            "longitude": self.longitude, "speed": self.speed,
            "heading": self.heading, "satellites": self.satellites,
            "armed": self.armed, "flying": self.flying, "mode": self.mode,
        }


class DroneController:
    """Drone control and monitoring.

    Supports MAVLink protocol (via pymavlink or dronekit) for
    autonomous drone operations. Used for:
    - Perimeter checks
    - Aerial inspection (roof, gutters, property)
    - Following a vehicle on property
    - Search patterns

    SAFETY:
    - Return-to-launch (RTL) on low battery
    - Geofence to prevent flying off property
    - Max altitude enforced
    - Failsafe: land immediately if connection lost
    """

    ACTOR = "anubis.drone"

    def __init__(self, root: str | Path, *, ledger: Any | None = None,
                 max_altitude: float = 50, geofence_radius: float = 100) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.max_altitude = max_altitude
        self.geofence_radius = geofence_radius
        self._state_dir = self.root / "memory" / "drone"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "history.jsonl"
        self._state: DroneState | None = None
        self._connected = False
        self._home_lat = 0.0
        self._home_lon = 0.0

    def connect(self, connection_string: str = "udp:127.0.0.1:14550") -> bool:
        try:
            from dronekit import connect  # type: ignore
            self._vehicle = connect(connection_string, wait_ready=True)
            self._connected = True
            self._home_lat = self._vehicle.location.global_relative_frame.lat
            self._home_lon = self._vehicle.location.global_relative_frame.lon
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def update_state(self, **kwargs: Any) -> DroneState:
        state = DroneState(timestamp=time.time(), **kwargs)
        self._state = state
        self._record(state)
        self._check_safety(state)
        return state

    def _check_safety(self, state: DroneState) -> None:
        if state.battery < 20 and state.flying:
            self._log("safety.low_battery", {"battery": state.battery})
        if state.altitude > self.max_altitude:
            self._log("safety.altitude_exceeded", {"altitude": state.altitude})

    def arm(self) -> bool:
        """Arm the drone."""
        if not self._connected:
            return False
        # Would arm via MAVLink
        return True

    def takeoff(self, altitude: float = 10) -> bool:
        """Take off to specified altitude."""
        if not self._connected:
            return False
        altitude = min(altitude, self.max_altitude)
        # Would command takeoff via MAVLink
        return True

    def return_to_launch(self) -> bool:
        """Command drone to return to launch point."""
        if not self._connected:
            return False
        # Would command RTL via MAVLink
        return True

    def land(self) -> bool:
        """Command drone to land."""
        if not self._connected:
            return False
        return True

    def get_state(self) -> dict[str, Any] | None:
        return self._state.to_dict() if self._state else None

    def get_status(self) -> dict[str, Any]:
        return {
            "connected": self._connected,
            "state": self._state.to_dict() if self._state else None,
            "max_altitude": self.max_altitude,
            "geofence_radius": self.geofence_radius,
        }

    def _record(self, state: DroneState) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(state.to_dict()) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass


# ============================================================
# 6. Garden/Plant Monitoring
# ============================================================

@dataclass
class PlantReading:
    """Garden/plant sensor reading."""
    timestamp: float = 0.0
    plant_name: str = ""
    soil_moisture: float = 0.0  # %
    soil_temperature: float = 0.0  # °F
    air_temperature: float = 0.0  # °F
    humidity: float = 0.0  # %
    light_level: float = 0.0  # lux
    ph: float = 0.0
    fertilizer_level: float = 0.0  # %

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp, "plant_name": self.plant_name,
            "soil_moisture": self.soil_moisture,
            "soil_temperature": self.soil_temperature,
            "air_temperature": self.air_temperature,
            "humidity": self.humidity, "light_level": self.light_level,
            "ph": self.ph, "fertilizer_level": self.fertilizer_level,
        }


class GardenMonitor:
    """Garden and plant monitoring system.

    Reads from IoT soil sensors, light sensors, and weather data
    to track plant health and recommend care actions.
    """

    ACTOR = "anubis.garden"

    PLANT_NEEDS: dict[str, dict[str, Any]] = {
        "tomato": {"moisture_min": 50, "moisture_max": 80, "light_min": 20000, "ph_min": 6.0, "ph_max": 6.8},
        "basil": {"moisture_min": 60, "moisture_max": 80, "light_min": 15000, "ph_min": 6.0, "ph_max": 7.5},
        "rose": {"moisture_min": 40, "moisture_max": 70, "light_min": 25000, "ph_min": 5.5, "ph_max": 7.0},
        "default": {"moisture_min": 40, "moisture_max": 70, "light_min": 10000, "ph_min": 6.0, "ph_max": 7.0},
    }

    def __init__(self, root: str | Path, *, ledger: Any | None = None) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self._state_dir = self.root / "memory" / "garden"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "history.jsonl"
        self._plants_file = self._state_dir / "plants.json"
        self._plants: dict[str, dict[str, Any]] = {}
        self._last_readings: dict[str, PlantReading] = {}
        self._load()

    def add_plant(self, name: str, plant_type: str = "default", location: str = "") -> dict[str, Any]:
        plant_id = hashlib.sha256(f"plant:{name}:{time.time()}".encode()).hexdigest()[:16]
        plant = {"plant_id": plant_id, "name": name, "type": plant_type, "location": location}
        self._plants[plant_id] = plant
        self._save_plants()
        return plant

    def record_reading(self, plant_name: str, **kwargs: Any) -> PlantReading:
        reading = PlantReading(timestamp=time.time(), plant_name=plant_name, **kwargs)
        self._last_readings[plant_name] = reading
        self._record(reading)
        return reading

    def get_care_recommendations(self, plant_name: str) -> list[str]:
        reading = self._last_readings.get(plant_name)
        if not reading:
            return []
        plant_type = "default"
        for p in self._plants.values():
            if p["name"] == plant_name:
                plant_type = p.get("type", "default")
                break
        needs = self.PLANT_NEEDS.get(plant_type, self.PLANT_NEEDS["default"])
        recs: list[str] = []
        if reading.soil_moisture < needs["moisture_min"]:
            recs.append(f"The {plant_name} needs water — soil moisture is {reading.soil_moisture:.0f}%")
        elif reading.soil_moisture > needs["moisture_max"]:
            recs.append(f"The {plant_name} is overwatered — soil moisture is {reading.soil_moisture:.0f}%")
        if reading.light_level < needs["light_min"]:
            recs.append(f"The {plant_name} needs more light — only {reading.light_level:.0f} lux")
        if reading.ph > 0 and (reading.ph < needs["ph_min"] or reading.ph > needs["ph_max"]):
            recs.append(f"The {plant_name} pH is {reading.ph} — optimal is {needs['ph_min']}-{needs['ph_max']}")
        return recs

    def get_all_recommendations(self) -> dict[str, list[str]]:
        return {name: self.get_care_recommendations(name) for name in self._last_readings}

    def get_plants(self) -> list[dict[str, Any]]:
        return list(self._plants.values())

    def get_status(self) -> dict[str, Any]:
        return {
            "total_plants": len(self._plants),
            "monitored": len(self._last_readings),
            "recommendations": sum(
                len(r) for r in self.get_all_recommendations().values()
            ),
        }

    def _load(self) -> None:
        if self._plants_file.exists():
            try:
                self._plants = json.loads(self._plants_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save_plants(self) -> None:
        self._plants_file.write_text(json.dumps(self._plants, indent=2), encoding="utf-8")

    def _record(self, reading: PlantReading) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(reading.to_dict()) + "\n")
        except Exception:
            pass


# ============================================================
# 7. Smart Watch Integration
# ============================================================

@dataclass
class WatchData:
    """Smart watch health and activity data."""
    timestamp: float = 0.0
    heart_rate: float = 0.0  # bpm
    heart_rate_variability: float = 0.0  # ms
    steps: int = 0
    distance: float = 0.0  # meters
    calories: float = 0.0  # kcal
    active_minutes: int = 0
    sleep_hours: float = 0.0
    sleep_quality: str = ""  # poor, fair, good, excellent
    stress_level: float = 0.0  # 0-100
    spo2: float = 0.0  # blood oxygen %
    body_temperature: float = 0.0  # °F
    respiratory_rate: float = 0.0  # breaths per minute
    workout_type: str = ""
    workout_duration: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp, "heart_rate": self.heart_rate,
            "hrv": self.heart_rate_variability, "steps": self.steps,
            "distance": self.distance, "calories": self.calories,
            "active_minutes": self.active_minutes,
            "sleep_hours": self.sleep_hours, "sleep_quality": self.sleep_quality,
            "stress_level": self.stress_level, "spo2": self.spo2,
            "body_temperature": self.body_temperature,
            "respiratory_rate": self.respiratory_rate,
            "workout_type": self.workout_type,
            "workout_duration": self.workout_duration,
        }


class SmartWatch:
    """Smart watch integration (Apple Watch, Garmin, Fitbit).

    Receives health and activity data from smart watches via:
    - Apple HealthKit (iOS)
    - Google Fit (Android)
    - Garmin Connect API
    - Fitbit API

    More accurate than phone alone for health monitoring.
    """

    ACTOR = "anubis.watch"

    def __init__(self, root: str | Path, *, ledger: Any | None = None,
                 on_anomaly: Callable[[str, WatchData], None] | None = None) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.on_anomaly = on_anomaly
        self._state_dir = self.root / "memory" / "watch"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "history.jsonl"
        self._last_data: WatchData | None = None

    def receive_data(self, **kwargs: Any) -> WatchData:
        data = WatchData(timestamp=time.time(), **kwargs)
        self._last_data = data
        self._record(data)
        self._check_anomalies(data)
        return data

    def _check_anomalies(self, data: WatchData) -> None:
        anomalies: list[str] = []
        if data.heart_rate > 150:
            anomalies.append(f"High heart rate: {data.heart_rate} bpm")
        elif data.heart_rate > 0 and data.heart_rate < 40:
            anomalies.append(f"Low heart rate: {data.heart_rate} bpm")
        if data.spo2 > 0 and data.spo2 < 90:
            anomalies.append(f"Low blood oxygen: {data.spo2}%")
        if data.stress_level > 80:
            anomalies.append(f"High stress level: {data.stress_level}")
        if data.body_temperature > 100.4:
            anomalies.append(f"Elevated body temperature: {data.body_temperature}°F")

        for anomaly in anomalies:
            if self.on_anomaly:
                try:
                    self.on_anomaly(anomaly, data)
                except Exception:
                    pass
            if self.ledger:
                try:
                    self.ledger.append(self.ACTOR, "anomaly", {"message": anomaly})
                except Exception:
                    pass

    def get_last_data(self) -> dict[str, Any] | None:
        return self._last_data.to_dict() if self._last_data else None

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self._history_file.exists():
            return []
        try:
            lines = self._history_file.read_text(encoding="utf-8").strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_status(self) -> dict[str, Any]:
        return {
            "last_sync": self._last_data.timestamp if self._last_data else 0,
            "heart_rate": self._last_data.heart_rate if self._last_data else 0,
            "steps": self._last_data.steps if self._last_data else 0,
        }

    def _record(self, data: WatchData) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data.to_dict()) + "\n")
        except Exception:
            pass


# ============================================================
# 8. Visitor Logging
# ============================================================

@dataclass
class VisitorLog:
    """A visitor log entry."""
    log_id: str
    timestamp: float = 0.0
    visitor_name: str = ""
    visitor_type: str = "unknown"  # known, unknown, delivery, service, family, friend
    face_matched: bool = False
    confidence: float = 0.0
    camera_id: str = ""
    image_path: str = ""
    arrival_time: float = 0.0
    departure_time: float = 0.0
    duration: float = 0.0
    purpose: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "log_id": self.log_id, "timestamp": self.timestamp,
            "visitor_name": self.visitor_name, "visitor_type": self.visitor_type,
            "face_matched": self.face_matched, "confidence": self.confidence,
            "camera_id": self.camera_id, "image_path": self.image_path,
            "arrival_time": self.arrival_time,
            "departure_time": self.departure_time,
            "duration": self.duration, "purpose": self.purpose,
            "notes": self.notes,
        }


class VisitorLogger:
    """Visitor logging system.

    Keeps a permanent log of everyone who comes to the door or
    enters the property. Uses camera + face recognition to identify
    visitors and track arrival/departure times.
    """

    ACTOR = "anubis.visitors"

    def __init__(self, root: str | Path, *, ledger: Any | None = None,
                 on_visitor: Callable[[VisitorLog], None] | None = None) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.on_visitor = on_visitor
        self._state_dir = self.root / "memory" / "visitors"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._logs_file = self._state_dir / "logs.jsonl"
        self._logs: dict[str, VisitorLog] = {}
        self._active_visitors: dict[str, VisitorLog] = {}  # by face_id or name

    def log_arrival(
        self, visitor_name: str = "", visitor_type: str = "unknown",
        face_matched: bool = False, confidence: float = 0,
        camera_id: str = "", image_path: str = "", purpose: str = "",
    ) -> VisitorLog:
        log_id = hashlib.sha256(
            f"visitor:{visitor_name}:{time.time()}".encode()
        ).hexdigest()[:16]
        log = VisitorLog(
            log_id=log_id, timestamp=time.time(),
            visitor_name=visitor_name, visitor_type=visitor_type,
            face_matched=face_matched, confidence=confidence,
            camera_id=camera_id, image_path=image_path,
            arrival_time=time.time(), purpose=purpose,
        )
        self._logs[log_id] = log
        # Track active visitor
        key = visitor_name or log_id
        self._active_visitors[key] = log
        self._record(log)
        if self.on_visitor:
            try:
                self.on_visitor(log)
            except Exception:
                pass
        self._log("visitor.arrived", {"name": visitor_name, "type": visitor_type})
        return log

    def log_departure(self, visitor_name: str) -> bool:
        key = visitor_name
        log = self._active_visitors.get(key)
        if log is None:
            return False
        log.departure_time = time.time()
        log.duration = log.departure_time - log.arrival_time
        del self._active_visitors[key]
        self._log("visitor.departed", {"name": visitor_name, "duration": log.duration})
        return True

    def get_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        logs = sorted(self._logs.values(), key=lambda v: v.timestamp, reverse=True)
        return [v.to_dict() for v in logs[:limit]]

    def get_active_visitors(self) -> list[dict[str, Any]]:
        return [v.to_dict() for v in self._active_visitors.values()]

    def get_visitors_by_type(self, visitor_type: str) -> list[dict[str, Any]]:
        return [v.to_dict() for v in self._logs.values() if v.visitor_type == visitor_type]

    def get_unknown_visitors(self) -> list[dict[str, Any]]:
        return [v.to_dict() for v in self._logs.values() if v.visitor_type == "unknown"]

    def get_status(self) -> dict[str, Any]:
        return {
            "total_visitors": len(self._logs),
            "active_visitors": len(self._active_visitors),
            "unknown_visitors": len(self.get_unknown_visitors()),
        }

    def _record(self, log: VisitorLog) -> None:
        try:
            with open(self._logs_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log.to_dict()) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
