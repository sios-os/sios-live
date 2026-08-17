"""Tests for the camera system — home, dashcam, body cam, public cameras."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.cameras import (
    CameraSystem, Camera, CameraFrame, CameraEvent,
    CAM_HOME, CAM_DASHCAM, CAM_BODY, CAM_PUBLIC,
    CONN_RTSP, CONN_HTTP_SNAPSHOT, CONN_MJPEG, CONN_FILE, CONN_ONVIF,
    STATUS_ONLINE, STATUS_OFFLINE, STATUS_ERROR, STATUS_DISABLED,
)


class TestCamera(unittest.TestCase):
    def test_to_dict(self):
        c = Camera(camera_id="c1", name="Front Door", camera_type=CAM_HOME)
        d = c.to_dict()
        self.assertEqual(d["camera_id"], "c1")
        self.assertEqual(d["name"], "Front Door")
        self.assertEqual(d["camera_type"], CAM_HOME)

    def test_default_settings(self):
        c = Camera(camera_id="c1", name="Test")
        self.assertTrue(c.enabled)
        self.assertTrue(c.detect_faces)
        self.assertTrue(c.detect_objects)
        self.assertTrue(c.detect_motion)
        self.assertEqual(c.status, STATUS_OFFLINE)


class TestCameraFrame(unittest.TestCase):
    def test_to_dict(self):
        f = CameraFrame(frame_id="f1", camera_id="c1")
        d = f.to_dict()
        self.assertEqual(d["frame_id"], "f1")
        self.assertEqual(d["camera_id"], "c1")
        self.assertEqual(d["faces_detected"], 0)


class TestCameraEvent(unittest.TestCase):
    def test_to_dict(self):
        e = CameraEvent(
            event_id="e1", camera_id="c1",
            event_type="motion", description="test",
        )
        d = e.to_dict()
        self.assertEqual(d["event_id"], "e1")
        self.assertEqual(d["event_type"], "motion")


class TestCameraSystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.system = CameraSystem(self.root)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        self.assertEqual(self.system.get_cameras(), [])
        self.assertFalse(self.system.is_monitoring)

    def test_add_home_camera(self):
        cam = self.system.add_camera(
            name="Front Door",
            camera_type=CAM_HOME,
            connection_type=CONN_RTSP,
            url="rtsp://192.168.1.100:554/stream",
            location="front door",
        )
        self.assertEqual(cam.name, "Front Door")
        self.assertEqual(cam.camera_type, CAM_HOME)
        self.assertEqual(cam.connection_type, CONN_RTSP)
        self.assertTrue(cam.enabled)

    def test_add_dashcam(self):
        cam = self.system.add_camera(
            name="Car Dashcam",
            camera_type=CAM_DASHCAM,
            connection_type=CONN_HTTP_SNAPSHOT,
            url="http://192.168.1.200/snapshot.jpg",
            location="car",
        )
        self.assertEqual(cam.camera_type, CAM_DASHCAM)

    def test_add_body_cam(self):
        cam = self.system.add_camera(
            name="Body Cam",
            camera_type=CAM_BODY,
            connection_type=CONN_FILE,
            url="/media/bodycam/latest.jpg",
            location="body",
        )
        self.assertEqual(cam.camera_type, CAM_BODY)

    def test_add_public_camera(self):
        cam = self.system.add_public_camera(
            name="Main St & 5th Ave",
            url="http://traffic.example.com/cam1.jpg",
            location="Main St & 5th Ave",
            latitude=40.7,
            longitude=-74.0,
        )
        self.assertEqual(cam.camera_type, CAM_PUBLIC)
        self.assertFalse(cam.detect_faces)  # no face recognition on public cams
        self.assertFalse(cam.detect_motion)  # public cams have constant motion
        self.assertEqual(cam.snapshot_interval, 60.0)  # less frequent

    def test_remove_camera(self):
        cam = self.system.add_camera(
            name="Test", camera_type=CAM_HOME,
            connection_type=CONN_RTSP, url="rtsp://test",
        )
        self.assertTrue(self.system.remove_camera(cam.camera_id))
        self.assertEqual(len(self.system.get_cameras()), 0)

    def test_update_camera(self):
        cam = self.system.add_camera(
            name="Test", camera_type=CAM_HOME,
            connection_type=CONN_RTSP, url="rtsp://test",
        )
        self.assertTrue(self.system.update_camera(cam.camera_id, name="Updated"))
        data = self.system.get_camera(cam.camera_id)
        self.assertEqual(data["name"], "Updated")

    def test_enable_disable_camera(self):
        cam = self.system.add_camera(
            name="Test", camera_type=CAM_HOME,
            connection_type=CONN_RTSP, url="rtsp://test",
        )
        self.system.disable_camera(cam.camera_id)
        data = self.system.get_camera(cam.camera_id)
        self.assertFalse(data["enabled"])
        self.assertEqual(data["status"], STATUS_DISABLED)
        self.system.enable_camera(cam.camera_id)
        data = self.system.get_camera(cam.camera_id)
        self.assertTrue(data["enabled"])

    def test_get_cameras_by_type(self):
        self.system.add_camera("Home1", CAM_HOME, CONN_RTSP, "rtsp://h1")
        self.system.add_camera("Dash", CAM_DASHCAM, CONN_HTTP_SNAPSHOT, "http://d1")
        self.system.add_camera("Public", CAM_PUBLIC, CONN_HTTP_SNAPSHOT, "http://p1")
        home = self.system.get_cameras_by_type(CAM_HOME)
        dash = self.system.get_cameras_by_type(CAM_DASHCAM)
        public = self.system.get_cameras_by_type(CAM_PUBLIC)
        self.assertEqual(len(home), 1)
        self.assertEqual(len(dash), 1)
        self.assertEqual(len(public), 1)

    def test_get_enabled_cameras(self):
        cam1 = self.system.add_camera("C1", CAM_HOME, CONN_RTSP, "rtsp://1")
        cam2 = self.system.add_camera("C2", CAM_HOME, CONN_RTSP, "rtsp://2")
        self.system.disable_camera(cam2.camera_id)
        enabled = self.system.get_enabled_cameras()
        self.assertEqual(len(enabled), 1)
        self.assertEqual(enabled[0]["name"], "C1")

    def test_cameras_persist(self):
        cam = self.system.add_camera(
            "Front Door", CAM_HOME, CONN_RTSP, "rtsp://192.168.1.100",
            location="front door",
        )
        system2 = CameraSystem(self.root)
        cameras = system2.get_cameras()
        self.assertEqual(len(cameras), 1)
        self.assertEqual(cameras[0]["name"], "Front Door")
        self.assertEqual(cameras[0]["location"], "front door")

    def test_capture_disabled_camera(self):
        cam = self.system.add_camera("Test", CAM_HOME, CONN_RTSP, "rtsp://test")
        self.system.disable_camera(cam.camera_id)
        frame = self.system.capture_frame(cam.camera_id)
        self.assertIsNone(frame)

    def test_capture_nonexistent_camera(self):
        frame = self.system.capture_frame("nonexistent")
        self.assertIsNone(frame)

    def test_capture_rtsp_no_tools(self):
        # Without cv2 and ffmpeg, RTSP capture should fail gracefully
        system = CameraSystem(self.root)
        system._cv2 = None
        system._ffmpeg = None
        cam = system.add_camera("Test", CAM_HOME, CONN_RTSP, "rtsp://test")
        frame = system.capture_frame(cam.camera_id)
        self.assertIsNone(frame)
        data = system.get_camera(cam.camera_id)
        self.assertEqual(data["status"], STATUS_ERROR)

    def test_capture_http_invalid_url(self):
        cam = self.system.add_camera(
            "Test", CAM_HOME, CONN_HTTP_SNAPSHOT,
            "http://192.168.1.99:99999/nonexistent.jpg",
        )
        frame = self.system.capture_frame(cam.camera_id)
        self.assertIsNone(frame)

    def test_capture_file_nonexistent(self):
        cam = self.system.add_camera(
            "Test", CAM_BODY, CONN_FILE, "/nonexistent/path/image.jpg",
        )
        frame = self.system.capture_frame(cam.camera_id)
        self.assertIsNone(frame)

    def test_capture_http_success(self):
        # Create a small test image and serve it via file://
        # Actually, let's test with a real local file
        test_img = Path(self.tmpdir) / "test_image.jpg"
        test_img.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # fake JPEG

        # Use file:// URL won't work with urllib, so test file connection
        cam = self.system.add_camera(
            "Test File", CAM_HOME, CONN_FILE, str(test_img),
        )
        frame = self.system.capture_frame(cam.camera_id)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.camera_id, cam.camera_id)

    def test_monitor_all(self):
        # No cameras → empty list
        frames = self.system.monitor_all()
        self.assertEqual(len(frames), 0)

    def test_monitor_all_with_disabled(self):
        cam1 = self.system.add_camera("C1", CAM_HOME, CONN_RTSP, "rtsp://1")
        cam2 = self.system.add_camera("C2", CAM_HOME, CONN_RTSP, "rtsp://2")
        self.system.disable_camera(cam2.camera_id)
        # monitor_all should skip disabled cameras
        # Both will fail to capture (no real RTSP), but only C1 should be attempted
        frames = self.system.monitor_all()
        # Empty because RTSP capture fails without tools
        self.assertEqual(len(frames), 0)

    def test_start_stop_monitoring(self):
        self.system.start_monitoring()
        self.assertTrue(self.system.is_monitoring)
        self.system.stop_monitoring()
        self.assertFalse(self.system.is_monitoring)

    def test_get_events_empty(self):
        self.assertEqual(self.system.get_events(), [])

    def test_get_events_after_creation(self):
        cam = self.system.add_camera("Test", CAM_HOME, CONN_RTSP, "rtsp://test")
        self.system._create_event(
            cam, "motion", "Motion detected", "/tmp/test.jpg", "low",
        )
        events = self.system.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "motion")

    def test_get_events_by_camera(self):
        cam1 = self.system.add_camera("C1", CAM_HOME, CONN_RTSP, "rtsp://1")
        cam2 = self.system.add_camera("C2", CAM_HOME, CONN_RTSP, "rtsp://2")
        self.system._create_event(cam1, "motion", "test1", "", "low")
        self.system._create_event(cam2, "motion", "test2", "", "low")
        cam1_events = self.system.get_events_by_camera(cam1.camera_id)
        self.assertEqual(len(cam1_events), 1)

    def test_get_events_by_type(self):
        cam = self.system.add_camera("C1", CAM_HOME, CONN_RTSP, "rtsp://1")
        self.system._create_event(cam, "motion", "test1", "", "low")
        self.system._create_event(cam, "person", "test2", "", "medium")
        motion_events = self.system.get_events_by_type("motion")
        self.assertEqual(len(motion_events), 1)

    def test_on_event_callback(self):
        called = []
        system = CameraSystem(self.root, on_event=lambda e: called.append(e))
        cam = system.add_camera("Test", CAM_HOME, CONN_RTSP, "rtsp://test")
        system._create_event(cam, "motion", "test", "", "low")
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0].event_type, "motion")

    def test_check_traffic_conditions(self):
        cam = self.system.add_public_camera(
            "Main St", "http://traffic.example.com/cam1.jpg",
        )
        # Will fail to capture (no real URL), but should not crash
        result = self.system.check_traffic_conditions([cam.camera_id])
        self.assertEqual(result["cameras_checked"], 0)  # failed capture

    def test_check_traffic_conditions_nonexistent(self):
        result = self.system.check_traffic_conditions(["nonexistent"])
        self.assertEqual(result["cameras_checked"], 0)

    def test_cleanup_old_frames(self):
        # Create an old frame file
        frames_dir = self.system._frames_dir
        old_frame = frames_dir / "old_0.jpg"
        old_frame.write_bytes(b"test")
        # Set modification time to 48 hours ago
        old_time = time.time() - 48 * 3600
        os.utime(str(old_frame), (old_time, old_time))
        # Create a recent frame
        new_frame = frames_dir / "new_0.jpg"
        new_frame.write_bytes(b"test")
        count = self.system.cleanup_old_frames(max_age_hours=24.0)
        self.assertEqual(count, 1)
        self.assertFalse(old_frame.exists())
        self.assertTrue(new_frame.exists())

    def test_get_status(self):
        self.system.add_camera("Home1", CAM_HOME, CONN_RTSP, "rtsp://1")
        self.system.add_camera("Dash", CAM_DASHCAM, CONN_HTTP_SNAPSHOT, "http://1")
        self.system.add_camera("Body", CAM_BODY, CONN_FILE, "/test")
        self.system.add_public_camera("Public", "http://traffic.example.com/cam.jpg")
        status = self.system.get_status()
        self.assertEqual(status["total_cameras"], 4)
        self.assertEqual(status["home_cameras"], 1)
        self.assertEqual(status["dashcam_cameras"], 1)
        self.assertEqual(status["body_cameras"], 1)
        self.assertEqual(status["public_cameras"], 1)
        self.assertIn("opencv_available", status)
        self.assertIn("ffmpeg_available", status)

    def test_discover_onvif(self):
        # Without onvif-cli, should return empty list
        result = self.system.discover_onvif_cameras()
        self.assertIsInstance(result, list)

    def test_analyze_frame_no_perception(self):
        # Without perception system, analysis should be a no-op
        cam = self.system.add_camera("Test", CAM_HOME, CONN_RTSP, "rtsp://test")
        frame = CameraFrame(frame_id="f1", camera_id=cam.camera_id)
        # Should not crash
        self.system._analyze_frame(cam, frame)

    def test_analyze_frame_with_perception(self):
        perception = MagicMock()
        perception.faces.identify = MagicMock(return_value=MagicMock(
            face_count=1, unknown_count=0, is_known=True, name="Storm",
        ))
        perception.objects.recognize = MagicMock(return_value=MagicMock(
            people_count=1, vehicles_count=0, animals_count=0,
            objects=[], to_dict=lambda: {"people_count": 1},
        ))
        system = CameraSystem(self.root, perception=perception)
        cam = system.add_camera("Test", CAM_HOME, CONN_FILE, "")

        # Create a test image
        test_img = Path(self.tmpdir) / "test.jpg"
        test_img.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)

        frame = CameraFrame(
            frame_id="f1", camera_id=cam.camera_id,
            image_path=str(test_img),
        )
        system._analyze_frame(cam, frame)
        self.assertEqual(frame.faces_detected, 1)

    def test_motion_detection_no_cv2(self):
        system = CameraSystem(self.root)
        system._cv2 = None
        cam = system.add_camera("Test", CAM_HOME, CONN_RTSP, "rtsp://test")
        frame = CameraFrame(frame_id="f1", camera_id=cam.camera_id)
        result = system._detect_motion(cam, frame)
        self.assertFalse(result)

    def test_camera_with_credentials(self):
        cam = self.system.add_camera(
            "Secured", CAM_HOME, CONN_HTTP_SNAPSHOT,
            "http://192.168.1.100/snapshot.jpg",
            username="admin",
            password="secret",
        )
        self.assertEqual(cam.username, "admin")
        # Password should be stored (encrypted in production)
        data = self.system.get_camera(cam.camera_id)
        # to_dict doesn't expose password directly
        self.assertNotIn("password", data)


if __name__ == "__main__":
    unittest.main()
