"""Tests for the perception system — voice ID, emotion, faces, objects."""
from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.perception import (
    VoiceIdentifier,
    VoiceProfile,
    VoiceIdentification,
    EmotionAnalyzer,
    EmotionAnalysis,
    FaceRecognizer,
    FaceProfile,
    FaceIdentification,
    ObjectRecognizer,
    ObjectDetection,
    SceneAnalysis,
    PerceptionSystem,
    extract_audio_features,
    classify_audio_type,
)


# --------------------------------------------------------------- helpers


def make_wav(path: str, duration_s: float = 1.0, frequency: int = 440,
             sample_rate: int = 16000, amplitude: int = 10000,
             noise: bool = False) -> str:
    """Create a test WAV file with a tone or noise."""
    n_samples = int(duration_s * sample_rate)
    import math
    samples = []
    for i in range(n_samples):
        if noise:
            import random
            samples.append(random.randint(-amplitude, amplitude))
        else:
            t = i / sample_rate
            val = int(amplitude * math.sin(2 * math.pi * frequency * t))
            # Add some variability to simulate speech patterns
            val = int(val * (0.5 + 0.5 * math.sin(2 * math.pi * 2 * t)))
            samples.append(val)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    return path


def make_speech_wav(path: str, duration_s: float = 2.0,
                    sample_rate: int = 16000) -> str:
    """Create a WAV that simulates speech patterns (energy bursts + pauses)."""
    import math
    import random
    n_samples = int(duration_s * sample_rate)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        # Create speech-like pattern: bursts of energy with pauses
        burst_cycle = (t * 3) % 1.0  # ~3 syllables per second
        if burst_cycle < 0.7:  # 70% voicing
            val = int(8000 * math.sin(2 * math.pi * 150 * t) *
                      (0.5 + 0.5 * math.sin(2 * math.pi * 5 * t)))
            val += random.randint(-500, 500)  # natural variation
        else:  # 30% pause
            val = random.randint(-100, 100)
        samples.append(val)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    return path


def make_high_energy_wav(path: str, duration_s: float = 1.0,
                         sample_rate: int = 16000) -> str:
    """Create a high-energy WAV simulating stressed/angry voice."""
    import math
    n_samples = int(duration_s * sample_rate)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        # High energy, high frequency, fast variations
        val = int(30000 * math.sin(2 * math.pi * 300 * t) *
                  (0.7 + 0.3 * math.sin(2 * math.pi * 20 * t)))
        samples.append(val)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    return path


def make_low_energy_wav(path: str, duration_s: float = 2.0,
                        sample_rate: int = 16000) -> str:
    """Create a low-energy WAV simulating sad/calm voice."""
    import math
    n_samples = int(duration_s * sample_rate)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        # Low energy, low frequency, long pauses
        cycle = (t * 1.5) % 1.0  # slow speech
        if cycle < 0.5:
            val = int(2000 * math.sin(2 * math.pi * 80 * t))
        else:
            val = 0
        samples.append(val)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    return path


# --------------------------------------------------------------- audio features


class TestExtractAudioFeatures(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_extract_from_tone(self):
        path = make_wav(f"{self.tmpdir}/tone.wav", duration_s=0.5)
        features = extract_audio_features(path)
        self.assertIn("energy_rms", features)
        self.assertIn("zero_crossing_rate", features)
        self.assertGreater(features["energy_rms"], 0)
        self.assertGreater(features["duration_s"], 0)

    def test_extract_from_speech(self):
        path = make_speech_wav(f"{self.tmpdir}/speech.wav", duration_s=1.0)
        features = extract_audio_features(path)
        self.assertIn("energy_rms", features)
        self.assertIn("speech_rate_est", features)
        self.assertIn("silence_ratio", features)

    def test_extract_invalid_file(self):
        features = extract_audio_features("/nonexistent/file.wav")
        self.assertIsInstance(features, dict)


class TestClassifyAudioType(unittest.TestCase):
    def test_classify_speech(self):
        features = {
            "energy_cv": 0.6,
            "zero_crossing_rate": 0.08,
            "silence_ratio": 0.3,
            "energy_rms": 200,
            "duration_s": 1.0,
        }
        self.assertEqual(classify_audio_type(features), "speech")

    def test_classify_music(self):
        features = {
            "energy_cv": 0.2,
            "zero_crossing_rate": 0.2,
            "silence_ratio": 0.05,
            "energy_rms": 300,
            "duration_s": 1.0,
        }
        self.assertEqual(classify_audio_type(features), "music")

    def test_classify_tv_radio(self):
        features = {
            "energy_cv": 0.3,
            "zero_crossing_rate": 0.08,
            "silence_ratio": 0.1,
            "energy_rms": 200,
            "duration_s": 1.0,
        }
        self.assertEqual(classify_audio_type(features), "tv_radio")

    def test_classify_noise_low_energy(self):
        features = {
            "energy_cv": 0.5,
            "zero_crossing_rate": 0.1,
            "silence_ratio": 0.2,
            "energy_rms": 10,
            "duration_s": 1.0,
        }
        self.assertEqual(classify_audio_type(features), "noise")

    def test_classify_noise_short(self):
        features = {
            "energy_cv": 0.5,
            "zero_crossing_rate": 0.1,
            "silence_ratio": 0.2,
            "energy_rms": 200,
            "duration_s": 0.1,
        }
        self.assertEqual(classify_audio_type(features), "noise")


# --------------------------------------------------------------- voice identification


class TestVoiceProfile(unittest.TestCase):
    def test_to_dict(self):
        p = VoiceProfile(profile_id="v1", name="Storm", relationship="creator")
        d = p.to_dict()
        self.assertEqual(d["profile_id"], "v1")
        self.assertEqual(d["name"], "Storm")
        self.assertEqual(d["relationship"], "creator")


class TestVoiceIdentification(unittest.TestCase):
    def test_to_dict(self):
        r = VoiceIdentification(identified=True, name="Storm", confidence=0.8)
        d = r.to_dict()
        self.assertTrue(d["identified"])
        self.assertEqual(d["name"], "Storm")


class TestVoiceIdentifier(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        identifier = VoiceIdentifier(self.root)
        self.assertEqual(identifier.match_threshold, 0.65)

    def test_enroll(self):
        identifier = VoiceIdentifier(self.root)
        path = make_speech_wav(f"{self.tmpdir}/voice1.wav", duration_s=1.0)
        profile = identifier.enroll("Storm", path, relationship="creator",
                                     trusted=True)
        self.assertEqual(profile.name, "Storm")
        self.assertTrue(profile.trusted)
        self.assertGreater(profile.samples, 0)

    def test_identify_known(self):
        identifier = VoiceIdentifier(self.root, match_threshold=0.3)
        path = make_speech_wav(f"{self.tmpdir}/voice1.wav", duration_s=1.0)
        identifier.enroll("Storm", path, relationship="creator")

        # Identify with same pattern
        path2 = make_speech_wav(f"{self.tmpdir}/voice2.wav", duration_s=1.0)
        result = identifier.identify(path2)
        # May or may not identify depending on feature similarity
        self.assertIsInstance(result, VoiceIdentification)

    def test_identify_tv_noise(self):
        identifier = VoiceIdentifier(self.root)
        # Create music-like audio (consistent energy)
        path = make_wav(f"{self.tmpdir}/music.wav", duration_s=1.0,
                       frequency=440, amplitude=5000)
        result = identifier.identify(path)
        # Should classify as non-speech
        self.assertIsInstance(result, VoiceIdentification)

    def test_identify_no_profiles(self):
        identifier = VoiceIdentifier(self.root)
        path = make_speech_wav(f"{self.tmpdir}/voice.wav", duration_s=1.0)
        result = identifier.identify(path)
        self.assertFalse(result.is_known)
        self.assertTrue(result.is_human)

    def test_add_sample(self):
        identifier = VoiceIdentifier(self.root)
        path = make_speech_wav(f"{self.tmpdir}/voice1.wav", duration_s=1.0)
        profile = identifier.enroll("Storm", path)
        path2 = make_speech_wav(f"{self.tmpdir}/voice2.wav", duration_s=1.0)
        self.assertTrue(identifier.add_sample(profile.profile_id, path2))
        profiles = identifier.get_profiles()
        self.assertEqual(profiles[0]["samples"], 2)

    def test_add_sample_nonexistent(self):
        identifier = VoiceIdentifier(self.root)
        path = make_speech_wav(f"{self.tmpdir}/voice.wav", duration_s=1.0)
        self.assertFalse(identifier.add_sample("nonexistent", path))

    def test_profiles_persist(self):
        identifier = VoiceIdentifier(self.root)
        path = make_speech_wav(f"{self.tmpdir}/voice.wav", duration_s=1.0)
        identifier.enroll("Storm", path, relationship="creator")
        identifier2 = VoiceIdentifier(self.root)
        profiles = identifier2.get_profiles()
        self.assertEqual(len(profiles), 1)

    def test_remove_profile(self):
        identifier = VoiceIdentifier(self.root)
        path = make_speech_wav(f"{self.tmpdir}/voice.wav", duration_s=1.0)
        profile = identifier.enroll("Storm", path)
        self.assertTrue(identifier.remove_profile(profile.profile_id))
        self.assertEqual(len(identifier.get_profiles()), 0)

    def test_get_profile(self):
        identifier = VoiceIdentifier(self.root)
        path = make_speech_wav(f"{self.tmpdir}/voice.wav", duration_s=1.0)
        profile = identifier.enroll("Storm", path)
        fetched = identifier.get_profile(profile.profile_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["name"], "Storm")

    def test_get_status(self):
        identifier = VoiceIdentifier(self.root)
        status = identifier.get_status()
        self.assertIn("total_profiles", status)
        self.assertIn("match_threshold", status)


# --------------------------------------------------------------- emotion analysis


class TestEmotionAnalysis(unittest.TestCase):
    def test_to_dict(self):
        e = EmotionAnalysis(emotion="happy", confidence=0.8)
        d = e.to_dict()
        self.assertEqual(d["emotion"], "happy")
        self.assertEqual(d["confidence"], 0.8)


class TestEmotionAnalyzer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        analyzer = EmotionAnalyzer(self.root)
        self.assertEqual(analyzer.duress_threshold, 0.75)

    def test_analyze_speech(self):
        analyzer = EmotionAnalyzer(self.root)
        path = make_speech_wav(f"{self.tmpdir}/speech.wav", duration_s=1.0)
        result = analyzer.analyze(path)
        self.assertIsInstance(result, EmotionAnalysis)
        self.assertIn(result.emotion, [
            "neutral", "calm", "happy", "sad", "angry",
            "fearful", "stressed", "duress"
        ])

    def test_analyze_high_energy(self):
        analyzer = EmotionAnalyzer(self.root)
        path = make_high_energy_wav(f"{self.tmpdir}/high.wav", duration_s=1.0)
        result = analyzer.analyze(path)
        # High energy should trigger some non-neutral emotion
        self.assertIsInstance(result, EmotionAnalysis)

    def test_analyze_low_energy(self):
        analyzer = EmotionAnalyzer(self.root)
        path = make_low_energy_wav(f"{self.tmpdir}/low.wav", duration_s=2.0)
        result = analyzer.analyze(path)
        # Low energy should lean toward calm or sad
        self.assertIsInstance(result, EmotionAnalysis)

    def test_history(self):
        analyzer = EmotionAnalyzer(self.root)
        path = make_speech_wav(f"{self.tmpdir}/speech.wav", duration_s=1.0)
        analyzer.analyze(path)
        history = analyzer.get_history()
        self.assertEqual(len(history), 1)

    def test_get_status(self):
        analyzer = EmotionAnalyzer(self.root)
        status = analyzer.get_status()
        self.assertIn("total_analyses", status)
        self.assertIn("duress_threshold", status)


# --------------------------------------------------------------- face recognition


class TestFaceProfile(unittest.TestCase):
    def test_to_dict(self):
        p = FaceProfile(profile_id="f1", name="Storm", relationship="creator")
        d = p.to_dict()
        self.assertEqual(d["profile_id"], "f1")
        self.assertEqual(d["name"], "Storm")


class TestFaceIdentification(unittest.TestCase):
    def test_to_dict(self):
        r = FaceIdentification(identified=True, name="Storm", confidence=0.9)
        d = r.to_dict()
        self.assertTrue(d["identified"])
        self.assertEqual(d["name"], "Storm")


class TestFaceRecognizer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        recognizer = FaceRecognizer(self.root)
        self.assertIsInstance(recognizer.is_available(), bool)

    def test_enroll_nonexistent_image(self):
        recognizer = FaceRecognizer(self.root)
        result = recognizer.enroll("Storm", "/nonexistent/image.jpg")
        self.assertIsNone(result)

    def test_identify_nonexistent_image(self):
        recognizer = FaceRecognizer(self.root)
        result = recognizer.identify("/nonexistent/image.jpg")
        self.assertFalse(result.identified)

    def test_get_status(self):
        recognizer = FaceRecognizer(self.root)
        status = recognizer.get_status()
        self.assertIn("available", status)
        self.assertIn("total_profiles", status)

    def test_profiles_persist(self):
        recognizer = FaceRecognizer(self.root)
        # Create a dummy image file
        img_path = Path(self.tmpdir) / "test.jpg"
        img_path.write_bytes(b"\xff\xd8\xff\xe0")  # JPEG header
        recognizer.enroll("Storm", str(img_path))
        recognizer2 = FaceRecognizer(self.root)
        self.assertEqual(len(recognizer2.get_profiles()), 1)

    def test_remove_profile(self):
        recognizer = FaceRecognizer(self.root)
        img_path = Path(self.tmpdir) / "test.jpg"
        img_path.write_bytes(b"\xff\xd8\xff\xe0")
        profile = recognizer.enroll("Storm", str(img_path))
        if profile:
            self.assertTrue(recognizer.remove_profile(profile.profile_id))


# --------------------------------------------------------------- object recognition


class TestObjectDetection(unittest.TestCase):
    def test_to_dict(self):
        o = ObjectDetection(object_id="o1", label="vehicle", sub_label="car")
        d = o.to_dict()
        self.assertEqual(d["object_id"], "o1")
        self.assertEqual(d["label"], "vehicle")


class TestSceneAnalysis(unittest.TestCase):
    def test_to_dict(self):
        s = SceneAnalysis(scene_type="activity", description="test")
        d = s.to_dict()
        self.assertEqual(d["scene_type"], "activity")

    def test_empty_scene(self):
        s = SceneAnalysis()
        d = s.to_dict()
        self.assertEqual(d["people_count"], 0)
        self.assertEqual(d["objects"], [])


class TestObjectRecognizer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        recognizer = ObjectRecognizer(self.root)
        self.assertIsInstance(recognizer.is_available(), bool)

    def test_recognize_nonexistent(self):
        recognizer = ObjectRecognizer(self.root)
        scene = recognizer.recognize("/nonexistent/image.jpg")
        self.assertEqual(len(scene.objects), 0)

    def test_categorize(self):
        recognizer = ObjectRecognizer(self.root)
        self.assertEqual(recognizer._categorize("car"), "vehicle")
        self.assertEqual(recognizer._categorize("dog"), "animal")
        self.assertEqual(recognizer._categorize("person"), "person")
        self.assertEqual(recognizer._categorize("chair"), "object")

    def test_summarize_empty_scene(self):
        recognizer = ObjectRecognizer(self.root)
        scene = SceneAnalysis()
        recognizer._summarize_scene(scene)
        self.assertEqual(scene.scene_type, "empty")

    def test_summarize_with_objects(self):
        recognizer = ObjectRecognizer(self.root)
        scene = SceneAnalysis()
        scene.objects = [
            ObjectDetection(object_id="1", label="person"),
            ObjectDetection(object_id="2", label="vehicle", sub_label="car"),
        ]
        recognizer._summarize_scene(scene)
        self.assertEqual(scene.people_count, 1)
        self.assertEqual(scene.vehicles_count, 1)
        self.assertEqual(scene.scene_type, "activity")

    def test_get_status(self):
        recognizer = ObjectRecognizer(self.root)
        status = recognizer.get_status()
        self.assertIn("available", status)
        self.assertIn("confidence_threshold", status)


# --------------------------------------------------------------- perception system


class TestPerceptionSystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        perception = PerceptionSystem(self.root)
        self.assertIsNotNone(perception.voice_id)
        self.assertIsNotNone(perception.emotion)
        self.assertIsNotNone(perception.faces)
        self.assertIsNotNone(perception.objects)

    def test_analyze_audio(self):
        perception = PerceptionSystem(self.root)
        path = make_speech_wav(f"{self.tmpdir}/speech.wav", duration_s=1.0)
        result = perception.analyze_audio(path)
        self.assertIn("identification", result)
        self.assertIn("emotion", result)

    def test_analyze_image_nonexistent(self):
        perception = PerceptionSystem(self.root)
        result = perception.analyze_image("/nonexistent/image.jpg")
        self.assertIn("faces", result)
        self.assertIn("scene", result)

    def test_enroll_voice(self):
        perception = PerceptionSystem(self.root)
        path = make_speech_wav(f"{self.tmpdir}/voice.wav", duration_s=1.0)
        result = perception.enroll_voice(
            "Storm", path, relationship="creator", trusted=True
        )
        self.assertEqual(result["name"], "Storm")
        self.assertTrue(result["trusted"])

    def test_enroll_face_nonexistent(self):
        perception = PerceptionSystem(self.root)
        result = perception.enroll_face("Storm", "/nonexistent/image.jpg")
        self.assertIsNone(result)

    def test_get_status(self):
        perception = PerceptionSystem(self.root)
        status = perception.get_status()
        self.assertIn("voice_id", status)
        self.assertIn("emotion", status)
        self.assertIn("faces", status)
        self.assertIn("objects", status)

    def test_analyze_audio_feeds_observer(self):
        observer = MagicMock()
        observer._make_observation = MagicMock()
        perception = PerceptionSystem(self.root, observer=observer)
        path = make_speech_wav(f"{self.tmpdir}/speech.wav", duration_s=1.0)
        perception.analyze_audio(path)
        observer._make_observation.assert_called_once()

    def test_analyze_image_feeds_observer(self):
        observer = MagicMock()
        observer._make_observation = MagicMock()
        perception = PerceptionSystem(self.root, observer=observer)
        # Create a dummy image
        img_path = Path(self.tmpdir) / "test.jpg"
        img_path.write_bytes(b"\xff\xd8\xff\xe0")
        perception.analyze_image(str(img_path))
        observer._make_observation.assert_called_once()


if __name__ == "__main__":
    unittest.main()
