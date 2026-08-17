"""Tests for Tier 3 IoT modules."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.iot import (
    OBDMonitor, VehicleData,
    AirQualityMonitor, AirQualityReading,
    EnergyMonitor, EnergyReading,
    Printer3D, PrintJob,
    DroneController, DroneState,
    GardenMonitor, PlantReading,
    SmartWatch, WatchData,
    VisitorLogger, VisitorLog,
)


class TestOBD(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.obd = OBDMonitor(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_not_connected(self):
        self.assertFalse(self.obd._connected)

    def test_manual_input(self):
        data = self.obd.input_manual_data(rpm=2500, speed=60, fuel_level=75)
        self.assertEqual(data.rpm, 2500)
        self.assertEqual(data.speed, 60)

    def test_dtc_description(self):
        self.assertIn("Catalyst", self.obd.get_dtc_description("P0420"))

    def test_dtc_unknown(self):
        self.assertEqual(self.obd.get_dtc_description("P9999"), "Unknown code")

    def test_get_status(self):
        status = self.obd.get_status()
        self.assertFalse(status["connected"])

    def test_history(self):
        self.obd.input_manual_data(rpm=2000)
        history = self.obd.get_history()
        self.assertEqual(len(history), 1)


class TestAirQuality(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.air = AirQualityMonitor(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_reading(self):
        reading = self.air.record_reading(co2=500, pm25=10, temperature=72, humidity=45)
        self.assertEqual(reading.co2, 500)

    def test_aqi_calculation_good(self):
        reading = self.air.record_reading(pm25=5)
        self.assertLess(reading.aqi, 50)

    def test_aqi_calculation_bad(self):
        reading = self.air.record_reading(pm25=60)
        self.assertGreater(reading.aqi, 150)

    def test_co2_alert(self):
        called = []
        air = AirQualityMonitor(Path(self.tmpdir), on_alert=lambda msg, r: called.append(msg))
        air.record_reading(co2=2500)
        self.assertTrue(len(called) > 0)

    def test_no_alert_good_air(self):
        called = []
        air = AirQualityMonitor(Path(self.tmpdir), on_alert=lambda msg, r: called.append(msg))
        air.record_reading(co2=400, pm25=5)
        self.assertEqual(len(called), 0)

    def test_recommendations_high_co2(self):
        self.air.record_reading(co2=1500, humidity=45)
        recs = self.air.get_recommendations()
        self.assertTrue(any("CO2" in r for r in recs))

    def test_recommendations_high_humidity(self):
        self.air.record_reading(co2=400, humidity=75)
        recs = self.air.get_recommendations()
        self.assertTrue(any("humidity" in r.lower() for r in recs))

    def test_recommendations_empty(self):
        self.assertEqual(self.air.get_recommendations(), [])

    def test_get_status(self):
        self.air.record_reading(co2=500)
        status = self.air.get_status()
        self.assertIsNotNone(status["last_reading"])


class TestEnergy(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.energy = EnergyMonitor(Path(self.tmpdir), cost_per_kwh=0.15)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_device(self):
        dev = self.energy.add_device("Server Rack", "computer", "office")
        self.assertEqual(dev["name"], "Server Rack")

    def test_record_reading(self):
        reading = self.energy.record_reading("Server", 500)
        self.assertEqual(reading.power_watts, 500)
        self.assertGreater(reading.cost, 0)

    def test_total_power(self):
        self.energy.record_reading("Server", 500)
        self.energy.record_reading("Lights", 100)
        total = self.energy.get_total_power()
        self.assertEqual(total, 600)

    def test_daily_cost(self):
        self.energy.record_reading("Server", 1000)
        cost = self.energy.get_daily_cost()
        self.assertIsInstance(cost, float)

    def test_get_status(self):
        status = self.energy.get_status()
        self.assertEqual(status["cost_per_kwh"], 0.15)


class TestPrinter3D(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.printer = Printer3D(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_submit_job(self):
        job = self.printer.submit_job("bracket.stl", estimated_time=3600)
        self.assertEqual(job.filename, "bracket.stl")
        self.assertEqual(job.status, "queued")

    def test_start_job(self):
        job = self.printer.submit_job("test.stl")
        self.assertTrue(self.printer.start_job(job.job_id))
        self.assertEqual(job.status, "printing")

    def test_complete_job(self):
        job = self.printer.submit_job("test.stl")
        self.printer.start_job(job.job_id)
        self.printer.update_progress(job.job_id, 100)
        self.assertEqual(job.status, "completed")

    def test_pause_resume(self):
        job = self.printer.submit_job("test.stl")
        self.printer.start_job(job.job_id)
        self.assertTrue(self.printer.pause_job(job.job_id))
        self.assertEqual(job.status, "paused")
        self.assertTrue(self.printer.resume_job(job.job_id))
        self.assertEqual(job.status, "printing")

    def test_cancel(self):
        job = self.printer.submit_job("test.stl")
        self.printer.start_job(job.job_id)
        self.assertTrue(self.printer.cancel_job(job.job_id))
        self.assertEqual(job.status, "failed")

    def test_on_complete_callback(self):
        called = []
        printer = Printer3D(Path(self.tmpdir), on_complete=lambda j: called.append(j))
        job = printer.submit_job("test.stl")
        printer.start_job(job.job_id)
        printer.update_progress(job.job_id, 100)
        self.assertEqual(len(called), 1)

    def test_get_active_jobs(self):
        job = self.printer.submit_job("test.stl")
        self.printer.start_job(job.job_id)
        active = self.printer.get_active_jobs()
        self.assertEqual(len(active), 1)

    def test_persist(self):
        self.printer.submit_job("test.stl")
        printer2 = Printer3D(Path(self.tmpdir))
        self.assertEqual(len(printer2.get_jobs()), 1)


class TestDrone(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.drone = DroneController(Path(self.tmpdir), max_altitude=50)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_not_connected(self):
        self.assertFalse(self.drone._connected)

    def test_update_state(self):
        state = self.drone.update_state(battery=80, altitude=10, flying=True)
        self.assertEqual(state.battery, 80)
        self.assertTrue(state.flying)

    def test_get_state(self):
        self.drone.update_state(battery=80)
        state = self.drone.get_state()
        self.assertIsNotNone(state)

    def test_get_status(self):
        status = self.drone.get_status()
        self.assertEqual(status["max_altitude"], 50)

    def test_arm_not_connected(self):
        self.assertFalse(self.drone.arm())


class TestGarden(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.garden = GardenMonitor(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_plant(self):
        plant = self.garden.add_plant("Tomato Plant", "tomato", "garden")
        self.assertEqual(plant["name"], "Tomato Plant")

    def test_record_reading(self):
        reading = self.garden.record_reading("Tomato", soil_moisture=30, light_level=5000)
        self.assertEqual(reading.soil_moisture, 30)

    def test_care_recommendation_water(self):
        self.garden.add_plant("Tomato", "tomato")
        self.garden.record_reading("Tomato", soil_moisture=20, light_level=30000)
        recs = self.garden.get_care_recommendations("Tomato")
        self.assertTrue(any("water" in r.lower() for r in recs))

    def test_care_recommendation_light(self):
        self.garden.add_plant("Tomato", "tomato")
        self.garden.record_reading("Tomato", soil_moisture=60, light_level=5000)
        recs = self.garden.get_care_recommendations("Tomato")
        self.assertTrue(any("light" in r.lower() for r in recs))

    def test_no_recommendations(self):
        self.garden.add_plant("Tomato", "tomato")
        self.garden.record_reading("Tomato", soil_moisture=60, light_level=30000, ph=6.5)
        recs = self.garden.get_care_recommendations("Tomato")
        self.assertEqual(len(recs), 0)

    def test_get_status(self):
        self.garden.add_plant("Test", "default")
        status = self.garden.get_status()
        self.assertEqual(status["total_plants"], 1)


class TestSmartWatch(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.watch = SmartWatch(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_receive_data(self):
        data = self.watch.receive_data(heart_rate=72, steps=5000)
        self.assertEqual(data.heart_rate, 72)
        self.assertEqual(data.steps, 5000)

    def test_high_hr_anomaly(self):
        called = []
        watch = SmartWatch(Path(self.tmpdir), on_anomaly=lambda msg, d: called.append(msg))
        watch.receive_data(heart_rate=160)
        self.assertTrue(len(called) > 0)

    def test_low_spo2_anomaly(self):
        called = []
        watch = SmartWatch(Path(self.tmpdir), on_anomaly=lambda msg, d: called.append(msg))
        watch.receive_data(spo2=85)
        self.assertTrue(len(called) > 0)

    def test_no_anomaly_normal(self):
        called = []
        watch = SmartWatch(Path(self.tmpdir), on_anomaly=lambda msg, d: called.append(msg))
        watch.receive_data(heart_rate=72, spo2=98)
        self.assertEqual(len(called), 0)

    def test_get_status(self):
        self.watch.receive_data(heart_rate=72, steps=100)
        status = self.watch.get_status()
        self.assertEqual(status["heart_rate"], 72)

    def test_history(self):
        self.watch.receive_data(heart_rate=72)
        history = self.watch.get_history()
        self.assertEqual(len(history), 1)


class TestVisitorLogger(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.visitors = VisitorLogger(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_log_arrival(self):
        log = self.visitors.log_arrival("John", "friend", face_matched=True)
        self.assertEqual(log.visitor_name, "John")
        self.assertEqual(log.visitor_type, "friend")

    def test_log_departure(self):
        self.visitors.log_arrival("John", "friend")
        self.assertTrue(self.visitors.log_departure("John"))

    def test_active_visitors(self):
        self.visitors.log_arrival("John", "friend")
        active = self.visitors.get_active_visitors()
        self.assertEqual(len(active), 1)

    def test_departure_clears_active(self):
        self.visitors.log_arrival("John", "friend")
        self.visitors.log_departure("John")
        self.assertEqual(len(self.visitors.get_active_visitors()), 0)

    def test_get_logs(self):
        self.visitors.log_arrival("John", "friend")
        self.visitors.log_arrival("Unknown", "unknown")
        logs = self.visitors.get_logs()
        self.assertEqual(len(logs), 2)

    def test_get_unknown_visitors(self):
        self.visitors.log_arrival("John", "friend")
        self.visitors.log_arrival("Stranger", "unknown")
        unknown = self.visitors.get_unknown_visitors()
        self.assertEqual(len(unknown), 1)

    def test_on_visitor_callback(self):
        called = []
        vl = VisitorLogger(Path(self.tmpdir), on_visitor=lambda v: called.append(v))
        vl.log_arrival("Test", "friend")
        self.assertEqual(len(called), 1)

    def test_get_status(self):
        self.visitors.log_arrival("John", "friend")
        status = self.visitors.get_status()
        self.assertEqual(status["total_visitors"], 1)
        self.assertEqual(status["active_visitors"], 1)

    def test_duration_calculated(self):
        self.visitors.log_arrival("John", "friend")
        time.sleep(0.1)
        self.visitors.log_departure("John")
        logs = self.visitors.get_logs()
        self.assertGreater(logs[0]["duration"], 0)


if __name__ == "__main__":
    unittest.main()
