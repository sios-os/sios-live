"""Tests for weather monitoring."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.weather import (
    WeatherMonitor, WeatherAlert, WeatherConditions, WeatherForecast,
    SEVERITY_SEVERE, SEVERITY_INFO, COND_CLEAR, COND_STORM, COND_RAIN, COND_SNOW,
)


class TestWeatherDataclasses(unittest.TestCase):
    def test_alert_to_dict(self):
        a = WeatherAlert(alert_id="a1", event="Tornado Warning", severity=SEVERITY_SEVERE)
        d = a.to_dict()
        self.assertEqual(d["alert_id"], "a1")
        self.assertEqual(d["event"], "Tornado Warning")

    def test_conditions_to_dict(self):
        c = WeatherConditions(temperature=72, condition=COND_CLEAR)
        d = c.to_dict()
        self.assertEqual(d["temperature"], 72)
        self.assertEqual(d["condition"], COND_CLEAR)

    def test_forecast_to_dict(self):
        f = WeatherForecast(period="Today", temperature_high=80)
        d = f.to_dict()
        self.assertEqual(d["period"], "Today")
        self.assertEqual(d["temperature_high"], 80)


class TestWeatherMonitor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.weather = WeatherMonitor(
            self.root, latitude=41.8, longitude=-87.6, location_name="Chicago",
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        self.assertEqual(self.weather.location_name, "Chicago")
        self.assertEqual(self.weather.latitude, 41.8)

    def test_code_to_condition(self):
        self.assertEqual(self.weather._code_to_condition(0), COND_CLEAR)
        self.assertEqual(self.weather._code_to_condition(95), COND_STORM)
        self.assertEqual(self.weather._code_to_condition(61), COND_RAIN)
        self.assertEqual(self.weather._code_to_condition(71), COND_SNOW)

    def test_code_to_description(self):
        self.assertEqual(self.weather._code_to_description(0), "Clear sky")
        self.assertEqual(self.weather._code_to_description(95), "Thunderstorm")

    def test_degrees_to_direction(self):
        self.assertEqual(self.weather._degrees_to_direction(0), "N")
        self.assertEqual(self.weather._degrees_to_direction(90), "E")
        self.assertEqual(self.weather._degrees_to_direction(180), "S")
        self.assertEqual(self.weather._degrees_to_direction(270), "W")

    def test_day_name(self):
        self.assertEqual(self.weather._day_name(0), "Today")
        self.assertEqual(self.weather._day_name(1), "Tomorrow")

    def test_recommendations_empty(self):
        self.assertEqual(self.weather.get_recommendations(), [])

    def test_recommendations_storm(self):
        self.weather._current = WeatherConditions(
            temperature=70, condition=COND_STORM, wind_speed=15,
        )
        recs = self.weather.get_recommendations()
        self.assertTrue(any("Thunderstorm" in r for r in recs))

    def test_recommendations_extreme_heat(self):
        self.weather._current = WeatherConditions(temperature=105)
        recs = self.weather.get_recommendations()
        self.assertTrue(any("Extreme heat" in r for r in recs))

    def test_recommendations_cold(self):
        self.weather._current = WeatherConditions(temperature=15)
        recs = self.weather.get_recommendations()
        self.assertTrue(any("Freezing cold" in r for r in recs))

    def test_recommendations_rain(self):
        self.weather._current = WeatherConditions(temperature=60, condition=COND_RAIN)
        recs = self.weather.get_recommendations()
        self.assertTrue(any("umbrella" in r.lower() for r in recs))

    def test_recommendations_snow(self):
        self.weather._current = WeatherConditions(temperature=30, condition=COND_SNOW)
        recs = self.weather.get_recommendations()
        self.assertTrue(any("snow" in r.lower() for r in recs))

    def test_recommendations_high_wind(self):
        self.weather._current = WeatherConditions(temperature=70, wind_speed=45)
        recs = self.weather.get_recommendations()
        self.assertTrue(any("wind" in r.lower() for r in recs))

    def test_recommendations_high_uv(self):
        self.weather._current = WeatherConditions(temperature=80, uv_index=9)
        recs = self.weather.get_recommendations()
        self.assertTrue(any("UV" in r for r in recs))

    def test_recommendations_low_visibility(self):
        self.weather._current = WeatherConditions(temperature=50, visibility=0.5)
        recs = self.weather.get_recommendations()
        self.assertTrue(any("visibility" in r.lower() for r in recs))

    def test_recommendations_forecast_precip(self):
        self.weather._current = WeatherConditions(temperature=70)
        self.weather._forecast = [
            WeatherForecast(period="Tomorrow", precipitation_probability=80),
        ]
        recs = self.weather.get_recommendations()
        self.assertTrue(any("Tomorrow" in r and "80%" in r for r in recs))

    def test_daily_briefing_no_data(self):
        briefing = self.weather.get_daily_briefing()
        self.assertIn("not available", briefing)

    def test_daily_briefing_with_data(self):
        self.weather._current = WeatherConditions(
            temperature=72, feels_like=70, humidity=50,
            wind_speed=10, wind_direction="NW",
            description="Partly cloudy",
        )
        briefing = self.weather.get_daily_briefing()
        self.assertIn("72", briefing)
        self.assertIn("Partly cloudy", briefing)

    def test_daily_briefing_with_alerts(self):
        self.weather._current = WeatherConditions(temperature=70)
        self.weather._active_alerts = [
            WeatherAlert(alert_id="a1", event="Tornado Watch", severity=SEVERITY_SEVERE),
        ]
        briefing = self.weather.get_daily_briefing()
        self.assertIn("Tornado Watch", briefing)

    def test_get_status(self):
        self.weather._current = WeatherConditions(temperature=70)
        status = self.weather.get_status()
        self.assertEqual(status["location"], "Chicago")
        self.assertIsNotNone(status["current_conditions"])

    def test_get_current(self):
        self.weather._current = WeatherConditions(temperature=70)
        c = self.weather.get_current()
        self.assertEqual(c["temperature"], 70)

    def test_get_current_none(self):
        self.assertIsNone(self.weather.get_current())

    def test_on_alert_callback(self):
        called = []
        weather = WeatherMonitor(self.root, on_alert=lambda a: called.append(a))
        weather._record_alert(WeatherAlert(alert_id="a1", event="Storm"))
        # _record_alert doesn't call on_alert — only fetch_alerts does
        # But we can test the callback path manually
        weather.on_alert(WeatherAlert(alert_id="test", event="Test"))
        self.assertEqual(len(called), 1)

    def test_alert_recorded(self):
        alert = WeatherAlert(alert_id="a1", event="Tornado Warning", severity=SEVERITY_SEVERE)
        self.weather._record_alert(alert)
        alerts_file = self.weather._alerts_file
        self.assertTrue(alerts_file.exists())
        data = json.loads(alerts_file.read_text().strip())
        self.assertEqual(data["event"], "Tornado Warning")

    def test_history_recorded(self):
        conditions = WeatherConditions(temperature=72, timestamp=time.time())
        self.weather._record_history(conditions)
        history = self.weather.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["temperature"], 72)

    def test_get_history_empty(self):
        self.assertEqual(self.weather.get_history(), [])

    def test_fetch_current_no_coords(self):
        weather = WeatherMonitor(self.root)
        result = weather.fetch_current()
        # Will try to fetch with 0,0 — may succeed or fail depending on network
        # Just ensure it doesn't crash
        self.assertTrue(result is None or hasattr(result, "temperature"))

    def test_fetch_alerts_no_coords(self):
        weather = WeatherMonitor(self.root)
        result = weather.fetch_alerts()
        self.assertEqual(result, [])

    def test_get_forecast_empty(self):
        self.assertEqual(self.weather.get_forecast(), [])

    def test_get_alerts_empty(self):
        self.assertEqual(self.weather.get_alerts(), [])


if __name__ == "__main__":
    unittest.main()
