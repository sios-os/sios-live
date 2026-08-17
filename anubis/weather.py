"""Weather monitoring — forecasts, severe weather alerts, environmental awareness.

ANUBIS monitors weather to:
- Alert on severe weather (storms, tornadoes, floods, heat waves)
- Factor weather into recommendations ("bring in patio furniture")
- Adjust smart home based on weather (close windows if rain)
- Track patterns for the observer
- Provide daily weather briefings

DATA SOURCES:
- National Weather Service API (free, no key required, US only)
- OpenWeatherMap API (requires key, global)
- Open-Meteo API (free, no key required, global)
- Local sensor data (if available)

Uses only stdlib (urllib) — no external dependencies.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# Alert severity
SEVERITY_EXTREME = "extreme"
SEVERITY_SEVERE = "severe"
SEVERITY_MODERATE = "moderate"
SEVERITY_MINOR = "minor"
SEVERITY_INFO = "info"

# Weather conditions
COND_CLEAR = "clear"
COND_CLOUDY = "cloudy"
COND_RAIN = "rain"
COND_STORM = "storm"
COND_SNOW = "snow"
COND_FOG = "fog"
COND_WIND = "wind"
COND_HAIL = "hail"
COND_UNKNOWN = "unknown"


@dataclass
class WeatherAlert:
    """A weather alert from NWS or other source."""
    alert_id: str
    event: str = ""  # "Tornado Warning", "Flash Flood Watch"
    severity: str = SEVERITY_INFO
    description: str = ""
    area: str = ""
    starts: float = 0.0
    expires: float = 0.0
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "event": self.event,
            "severity": self.severity,
            "description": self.description,
            "area": self.area,
            "starts": self.starts,
            "expires": self.expires,
            "source": self.source,
        }


@dataclass
class WeatherConditions:
    """Current weather conditions."""
    temperature: float = 0.0  # Fahrenheit
    feels_like: float = 0.0
    humidity: float = 0.0  # percentage
    wind_speed: float = 0.0  # mph
    wind_direction: str = ""
    pressure: float = 0.0  # hPa
    visibility: float = 0.0  # miles
    condition: str = COND_UNKNOWN
    description: str = ""
    dew_point: float = 0.0
    uv_index: float = 0.0
    timestamp: float = 0.0
    location: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "pressure": self.pressure,
            "visibility": self.visibility,
            "condition": self.condition,
            "description": self.description,
            "dew_point": self.dew_point,
            "uv_index": self.uv_index,
            "timestamp": self.timestamp,
            "location": self.location,
        }


@dataclass
class WeatherForecast:
    """A weather forecast for a specific period."""
    period: str = ""  # "Today", "Tonight", "Tomorrow"
    start_time: float = 0.0
    end_time: float = 0.0
    temperature_high: float = 0.0
    temperature_low: float = 0.0
    condition: str = COND_UNKNOWN
    description: str = ""
    precipitation_probability: float = 0.0  # percentage
    wind_speed: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "period": self.period,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "temperature_high": self.temperature_high,
            "temperature_low": self.temperature_low,
            "condition": self.condition,
            "description": self.description,
            "precipitation_probability": self.precipitation_probability,
            "wind_speed": self.wind_speed,
        }


class WeatherMonitor:
    """Weather monitoring system.

    Fetches weather data from free APIs (NWS, Open-Meteo) and
    generates alerts for severe weather. Integrates with threat
    analysis and proactive recommendations.
    """

    ACTOR = "anubis.weather"

    def __init__(
        self,
        root: str | Path,
        *,
        latitude: float = 0.0,
        longitude: float = 0.0,
        location_name: str = "",
        nws_office: str = "",  # e.g. "LOT" for Chicago
        openweather_api_key: str = "",
        ledger: Any | None = None,
        on_alert: Callable[[WeatherAlert], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.latitude = latitude
        self.longitude = longitude
        self.location_name = location_name
        self.nws_office = nws_office
        self.openweather_api_key = openweather_api_key
        self.ledger = ledger
        self.on_alert = on_alert

        self._state_dir = self.root / "memory" / "weather"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "history.jsonl"
        self._alerts_file = self._state_dir / "alerts.jsonl"

        self._current: WeatherConditions | None = None
        self._forecast: list[WeatherForecast] = []
        self._active_alerts: list[WeatherAlert] = []
        self._last_update: float = 0.0
        self._alerted_ids: set[str] = set()

    # --------------------------------------------------- data fetching

    def fetch_current(self) -> WeatherConditions | None:
        """Fetch current weather conditions."""
        # Try Open-Meteo (free, no key)
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={self.latitude}&longitude={self.longitude}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                f"weather_code,wind_speed_10m,wind_direction_10m,pressure_msl,"
                f"surface_pressure,dew_point_2m,uv_index,visibility"
                f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
            )
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "ANUBIS-Weather/1.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            current = data.get("current", {})
            conditions = WeatherConditions(
                temperature=current.get("temperature_2m", 0),
                feels_like=current.get("apparent_temperature", 0),
                humidity=current.get("relative_humidity_2m", 0),
                wind_speed=current.get("wind_speed_10m", 0),
                wind_direction=self._degrees_to_direction(
                    current.get("wind_direction_10m", 0)
                ),
                pressure=current.get("pressure_msl", 0),
                visibility=current.get("visibility", 0) / 1609.34 if current.get("visibility") else 0,
                condition=self._code_to_condition(current.get("weather_code", 0)),
                description=self._code_to_description(current.get("weather_code", 0)),
                dew_point=current.get("dew_point_2m", 0),
                uv_index=current.get("uv_index", 0),
                timestamp=time.time(),
                location=self.location_name,
            )
            self._current = conditions
            self._last_update = time.time()
            self._record_history(conditions)
            return conditions
        except Exception:
            return None

    def fetch_forecast(self) -> list[WeatherForecast]:
        """Fetch weather forecast (7-day)."""
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={self.latitude}&longitude={self.longitude}"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
                f"precipitation_probability_max,wind_speed_10m_max"
                f"&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto"
                f"&forecast_days=7"
            )
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "ANUBIS-Weather/1.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            daily = data.get("daily", {})
            forecasts: list[WeatherForecast] = []
            times = daily.get("time", [])
            for i, day in enumerate(times):
                forecasts.append(WeatherForecast(
                    period=self._day_name(i),
                    start_time=time.time() + i * 86400,
                    end_time=time.time() + (i + 1) * 86400,
                    temperature_high=daily.get("temperature_2m_max", [0] * 7)[i],
                    temperature_low=daily.get("temperature_2m_min", [0] * 7)[i],
                    condition=self._code_to_condition(
                        daily.get("weather_code", [0] * 7)[i]
                    ),
                    description=self._code_to_description(
                        daily.get("weather_code", [0] * 7)[i]
                    ),
                    precipitation_probability=daily.get(
                        "precipitation_probability_max", [0] * 7
                    )[i],
                    wind_speed=daily.get("wind_speed_10m_max", [0] * 7)[i],
                ))

            self._forecast = forecasts
            return forecasts
        except Exception:
            return []

    def fetch_alerts(self) -> list[WeatherAlert]:
        """Fetch active weather alerts from NWS (US only)."""
        if not self.latitude or not self.longitude:
            return []
        try:
            url = (
                f"https://api.weather.gov/alerts/active?"
                f"point={self.latitude},{self.longitude}"
            )
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "ANUBIS-Weather/1.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            alerts: list[WeatherAlert] = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                alert_id = feature.get("id", hashlib.sha256(
                    str(time.time()).encode()
                ).hexdigest()[:16])

                alert = WeatherAlert(
                    alert_id=alert_id,
                    event=props.get("event", ""),
                    severity=props.get("severity", SEVERITY_INFO).lower(),
                    description=props.get("description", ""),
                    area=props.get("areaDesc", ""),
                    starts=0,
                    expires=0,
                    source="NWS",
                )
                alerts.append(alert)

                # New alert — trigger callback
                if alert_id not in self._alerted_ids:
                    self._alerted_ids.add(alert_id)
                    self._record_alert(alert)
                    if self.on_alert:
                        try:
                            self.on_alert(alert)
                        except Exception:
                            pass

            self._active_alerts = alerts
            return alerts
        except Exception:
            return []

    # --------------------------------------------------- helpers

    def _code_to_condition(self, code: int) -> str:
        """Map WMO weather code to condition."""
        if code == 0:
            return COND_CLEAR
        elif code in (1, 2, 3):
            return COND_CLOUDY
        elif code in (45, 48):
            return COND_FOG
        elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
            return COND_RAIN
        elif code in (71, 73, 75, 77, 85, 86):
            return COND_SNOW
        elif code in (95, 96, 99):
            return COND_STORM
        else:
            return COND_UNKNOWN

    def _code_to_description(self, code: int) -> str:
        """Map WMO weather code to text description."""
        descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy",
            3: "Overcast", 45: "Fog", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            56: "Light freezing drizzle", 57: "Dense freezing drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            66: "Light freezing rain", 67: "Heavy freezing rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
            82: "Violent rain showers", 85: "Slight snow showers",
            86: "Heavy snow showers", 95: "Thunderstorm", 96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return descriptions.get(code, "Unknown")

    def _degrees_to_direction(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction."""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = int((degrees % 360) / 22.5)
        return directions[index]

    def _day_name(self, offset: int) -> str:
        if offset == 0:
            return "Today"
        elif offset == 1:
            return "Tomorrow"
        else:
            import datetime
            date = datetime.date.today() + datetime.timedelta(days=offset)
            return date.strftime("%A")

    # --------------------------------------------------- recommendations

    def get_recommendations(self) -> list[str]:
        """Generate weather-based recommendations."""
        recs: list[str] = []
        if self._current is None:
            return recs

        c = self._current

        # Severe weather
        if c.condition == COND_STORM:
            recs.append("Thunderstorm in the area — stay indoors and unplug sensitive electronics")
        if c.wind_speed > 30:
            recs.append(f"High winds ({c.wind_speed:.0f} mph) — secure loose outdoor items")
        if c.condition == COND_HAIL:
            recs.append("Hail detected — move vehicles to covered area if possible")

        # Temperature
        if c.temperature > 100:
            recs.append(f"Extreme heat ({c.temperature:.0f}°F) — stay hydrated, limit outdoor activity")
        elif c.temperature > 90:
            recs.append(f"Hot weather ({c.temperature:.0f}°F) — drink plenty of water")
        elif c.temperature < 20:
            recs.append(f"Freezing cold ({c.temperature:.0f}°F) — dress in layers, limit exposure")
        elif c.temperature < 32:
            recs.append(f"Below freezing ({c.temperature:.0f}°F) — bundle up")

        # Rain
        if c.condition == COND_RAIN:
            recs.append("It's raining — bring an umbrella")
            recs.append("Consider closing smart windows if open")

        # Snow
        if c.condition == COND_SNOW:
            recs.append("Snowing — allow extra travel time")
            recs.append("Check driveway before driving")

        # UV
        if c.uv_index > 7:
            recs.append(f"High UV index ({c.uv_index:.0f}) — wear sunscreen")

        # Humidity
        if c.humidity > 80:
            recs.append("High humidity — AC may need to work harder")
        elif c.humidity < 20:
            recs.append("Very dry air — consider using a humidifier")

        # Visibility
        if c.visibility < 1:
            recs.append("Very low visibility — drive carefully or avoid driving")
        elif c.visibility < 3:
            recs.append("Reduced visibility — use headlights")

        # Forecast-based
        for f in self._forecast[:3]:
            if f.precipitation_probability > 70:
                recs.append(f"{f.period}: {f.precipitation_probability:.0f}% chance of precipitation")
            if f.temperature_high > 95:
                recs.append(f"{f.period}: Very hot ({f.temperature_high:.0f}°F)")
            if f.temperature_low < 20:
                recs.append(f"{f.period}: Very cold ({f.temperature_low:.0f}°F)")

        return recs

    def get_daily_briefing(self) -> str:
        """Generate a daily weather briefing."""
        if self._current is None:
            return "Weather data not available."

        c = self._current
        parts = [f"Current weather in {self.location_name or 'your area'}:"]
        parts.append(f"  {c.description}, {c.temperature:.0f}°F (feels like {c.feels_like:.0f}°F)")
        parts.append(f"  Humidity: {c.humidity:.0f}%, Wind: {c.wind_speed:.0f} mph {c.wind_direction}")

        if self._forecast:
            today = self._forecast[0]
            parts.append(f"  Today: High {today.temperature_high:.0f}°F, Low {today.temperature_low:.0f}°F")
            if today.precipitation_probability > 30:
                parts.append(f"  Precipitation chance: {today.precipitation_probability:.0f}%")

        if self._active_alerts:
            parts.append(f"\n  ⚠ {len(self._active_alerts)} active weather alert(s):")
            for alert in self._active_alerts:
                parts.append(f"    - {alert.event} ({alert.severity})")

        recs = self.get_recommendations()
        if recs:
            parts.append("\n  Recommendations:")
            for r in recs:
                parts.append(f"    - {r}")

        return "\n".join(parts)

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        return {
            "location": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "last_update": self._last_update,
            "current_conditions": self._current.to_dict() if self._current else None,
            "forecast_periods": len(self._forecast),
            "active_alerts": len(self._active_alerts),
            "alerts": [a.to_dict() for a in self._active_alerts],
        }

    def get_current(self) -> dict[str, Any] | None:
        return self._current.to_dict() if self._current else None

    def get_forecast(self) -> list[dict[str, Any]]:
        return [f.to_dict() for f in self._forecast]

    def get_alerts(self) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._active_alerts]

    # --------------------------------------------------- persistence

    def _record_history(self, conditions: WeatherConditions) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(conditions.to_dict()) + "\n")
        except Exception:
            pass

    def _record_alert(self, alert: WeatherAlert) -> None:
        try:
            with open(self._alerts_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert.to_dict()) + "\n")
        except Exception:
            pass
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, "weather.alert", alert.to_dict())
            except Exception:
                pass

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self._history_file.exists():
            return []
        try:
            lines = self._history_file.read_text(encoding="utf-8").strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []
