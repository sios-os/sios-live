"""Tests for forms and biometric authentication."""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.forms import (
    get_form, list_forms, validate_form,
    account_form, identity_form, successor_form,
    update_account_form, biometric_enroll_form,
    FormField, FormDefinition, FIELD_TEXT, FIELD_PASSWORD, FIELD_NUMBER,
    FIELD_BOOLEAN, FIELD_SELECT, FIELD_EMAIL, FIELD_URL, FIELD_TEXTAREA,
)
from anubis.biometric_auth import (
    BiometricAuth, BiometricEnrollment, VerificationResult,
    BIOMETRIC_VAULT_KEY, MAX_FAILED_ATTEMPTS, REQUIRED_CONFIDENCE,
)
from anubis.identity import IdentityVault


# ===========================================================
# FORM TESTS
# ===========================================================

class TestFormDefinitions(unittest.TestCase):
    def test_account_form(self):
        form = account_form()
        self.assertEqual(form.form_id, "account_form")
        self.assertTrue(len(form.fields) > 0)
        # Should have name, url, username, password fields
        names = [f.name for f in form.fields]
        self.assertIn("name", names)
        self.assertIn("url", names)
        self.assertIn("username", names)
        self.assertIn("password", names)

    def test_identity_form(self):
        form = identity_form()
        self.assertEqual(form.form_id, "identity_form")
        names = [f.name for f in form.fields]
        self.assertIn("display_name", names)
        self.assertIn("passphrase", names)
        self.assertIn("preferred_name", names)

    def test_successor_form(self):
        form = successor_form()
        self.assertEqual(form.form_id, "successor_form")
        names = [f.name for f in form.fields]
        self.assertIn("display_name", names)
        self.assertIn("relationship", names)
        self.assertIn("consent_given", names)

    def test_update_account_form(self):
        form = update_account_form()
        self.assertEqual(form.form_id, "update_account_form")
        names = [f.name for f in form.fields]
        self.assertIn("account_id", names)

    def test_biometric_enroll_form(self):
        form = biometric_enroll_form()
        self.assertEqual(form.form_id, "biometric_enroll_form")
        names = [f.name for f in form.fields]
        self.assertIn("face_image_path", names)
        self.assertIn("voice_audio_path", names)

    def test_get_form(self):
        form = get_form("account_form")
        self.assertIsNotNone(form)
        self.assertEqual(form.form_id, "account_form")

    def test_get_form_unknown(self):
        form = get_form("nonexistent_form")
        self.assertIsNone(form)

    def test_list_forms(self):
        forms = list_forms()
        self.assertGreater(len(forms), 0)
        ids = [f["form_id"] for f in forms]
        self.assertIn("account_form", ids)
        self.assertIn("identity_form", ids)
        self.assertIn("successor_form", ids)


class TestFormValidation(unittest.TestCase):
    def test_validate_account_form_valid(self):
        data = {
            "name": "Electric Company",
            "url": "https://electric.com/login",
            "username": "storm",
            "password": "mypassword",
            "account_type": "utility",
            "bill_due_day": 15,
            "bill_amount": 120.50,
        }
        valid, errors = validate_form("account_form", data)
        self.assertTrue(valid, f"Errors: {errors}")

    def test_validate_account_form_missing_required(self):
        data = {"url": "https://example.com"}
        valid, errors = validate_form("account_form", data)
        self.assertFalse(valid)
        self.assertIn("required", " ".join(errors))

    def test_validate_account_form_invalid_url(self):
        data = {"name": "Test", "url": "not_a_url"}
        valid, errors = validate_form("account_form", data)
        self.assertFalse(valid)
        self.assertIn("URL", " ".join(errors))

    def test_validate_account_form_invalid_type(self):
        data = {"name": "Test", "account_type": "invalid_type"}
        valid, errors = validate_form("account_form", data)
        self.assertFalse(valid)

    def test_validate_account_form_bill_day_range(self):
        data = {"name": "Test", "bill_due_day": 50}
        valid, errors = validate_form("account_form", data)
        self.assertFalse(valid)

    def test_validate_identity_form_valid(self):
        data = {
            "display_name": "Storm",
            "passphrase": "secure_pass_123",
            "preferred_name": "Storm",
            "language": "en",
        }
        valid, errors = validate_form("identity_form", data)
        self.assertTrue(valid, f"Errors: {errors}")

    def test_validate_identity_form_short_passphrase(self):
        data = {
            "display_name": "Storm",
            "passphrase": "short",
        }
        valid, errors = validate_form("identity_form", data)
        self.assertFalse(valid)
        self.assertIn("at least 8", " ".join(errors))

    def test_validate_identity_form_missing_name(self):
        data = {"passphrase": "secure_pass_123"}
        valid, errors = validate_form("identity_form", data)
        self.assertFalse(valid)

    def test_validate_successor_form_valid(self):
        data = {
            "display_name": "Ethan Pace",
            "relationship": "son",
            "consent_given": True,
            "activation_conditions": "Confirmed absence for 30 days",
        }
        valid, errors = validate_form("successor_form", data)
        self.assertTrue(valid, f"Errors: {errors}")

    def test_validate_successor_form_missing_relationship(self):
        data = {"display_name": "Test", "consent_given": True}
        valid, errors = validate_form("successor_form", data)
        self.assertFalse(valid)

    def test_validate_email_field(self):
        form = FormDefinition(
            form_id="test", title="Test", description="",
            fields=[FormField(name="email", label="Email", field_type=FIELD_EMAIL)],
        )
        valid, _ = form.validate({"email": "test@example.com"})
        self.assertTrue(valid)
        valid, errors = form.validate({"email": "not_an_email"})
        self.assertFalse(valid)

    def test_validate_select_field(self):
        form = FormDefinition(
            form_id="test", title="Test", description="",
            fields=[FormField(name="color", label="Color", field_type=FIELD_SELECT,
                              options=["red", "blue", "green"])],
        )
        valid, _ = form.validate({"color": "red"})
        self.assertTrue(valid)
        valid, errors = form.validate({"color": "purple"})
        self.assertFalse(valid)

    def test_validate_boolean_field(self):
        form = FormDefinition(
            form_id="test", title="Test", description="",
            fields=[FormField(name="agree", label="Agree", field_type=FIELD_BOOLEAN)],
        )
        valid, _ = form.validate({"agree": True})
        self.assertTrue(valid)
        valid, _ = form.validate({"agree": "yes"})
        self.assertTrue(valid)
        valid, errors = form.validate({"agree": "maybe"})
        self.assertFalse(valid)

    def test_validate_number_field(self):
        form = FormDefinition(
            form_id="test", title="Test", description="",
            fields=[FormField(name="age", label="Age", field_type=FIELD_NUMBER,
                              min_value=0, max_value=150)],
        )
        valid, _ = form.validate({"age": 25})
        self.assertTrue(valid)
        valid, errors = form.validate({"age": -5})
        self.assertFalse(valid)
        valid, errors = form.validate({"age": 200})
        self.assertFalse(valid)

    def test_validate_optional_field_empty(self):
        form = FormDefinition(
            form_id="test", title="Test", description="",
            fields=[
                FormField(name="name", label="Name", required=True),
                FormField(name="notes", label="Notes", required=False),
            ],
        )
        valid, _ = form.validate({"name": "Test", "notes": ""})
        self.assertTrue(valid)

    def test_validate_unknown_form(self):
        valid, errors = validate_form("nonexistent", {})
        self.assertFalse(valid)

    def test_form_to_dict(self):
        form = account_form()
        d = form.to_dict()
        self.assertEqual(d["form_id"], "account_form")
        self.assertIn("fields", d)
        self.assertIn("title", d)

    def test_form_field_to_dict(self):
        field = FormField(name="test", label="Test", field_type=FIELD_TEXT, required=True)
        d = field.to_dict()
        self.assertEqual(d["name"], "test")
        self.assertEqual(d["type"], "text")
        self.assertTrue(d["required"])


# ===========================================================
# BIOMETRIC AUTH TESTS
# ===========================================================

class TestBiometricAuth(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.vault = IdentityVault(Path(self.tmpdir))
        self.vault.unlock("test_passphrase_123")

        # Mock face recognizer and voice identifier
        self.face_recognizer = MagicMock()
        self.voice_identifier = MagicMock()

        # By default, face recognition is available
        self.face_recognizer.is_available.return_value = True

        self.auth = BiometricAuth(
            self.vault,
            self.face_recognizer,
            self.voice_identifier,
            ledger=MagicMock(),
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ===========================================================
    # INITIAL STATE
    # ===========================================================

    def test_not_enrolled_initially(self):
        self.assertFalse(self.auth.is_enrolled())
        self.assertFalse(self.auth.is_enabled())

    def test_status_not_enrolled(self):
        status = self.auth.get_status()
        self.assertFalse(status["enrolled"])

    # ===========================================================
    # ENROLLMENT
    # ===========================================================

    def test_enroll_success(self):
        # Mock successful face + voice enrollment
        face_profile = MagicMock()
        face_profile.profile_id = "face_123"
        self.face_recognizer.enroll.return_value = face_profile

        voice_profile = MagicMock()
        voice_profile.profile_id = "voice_456"
        self.voice_identifier.enroll.return_value = voice_profile

        result = self.auth.enroll(
            creator_id="creator_123",
            creator_name="Storm",
            face_image_path="/path/to/face.jpg",
            voice_audio_path="/path/to/voice.wav",
        )
        self.assertEqual(result["status"], "enrolled")
        self.assertEqual(result["face_profile_id"], "face_123")
        self.assertEqual(result["voice_profile_id"], "voice_456")
        self.assertTrue(self.auth.is_enrolled())
        self.assertTrue(self.auth.is_enabled())

    def test_enroll_vault_locked(self):
        vault = IdentityVault(Path(tempfile.mkdtemp()))
        auth = BiometricAuth(vault, self.face_recognizer, self.voice_identifier)
        result = auth.enroll(
            "creator_123", "Storm", "/face.jpg", "/voice.wav"
        )
        self.assertIn("error", result)
        self.assertIn("unlocked", result["error"].lower())

    def test_enroll_face_failure(self):
        self.face_recognizer.enroll.return_value = None
        result = self.auth.enroll(
            "creator_123", "Storm", "/face.jpg", "/voice.wav"
        )
        self.assertIn("error", result)

    def test_enroll_voice_failure(self):
        face_profile = MagicMock()
        face_profile.profile_id = "face_123"
        self.face_recognizer.enroll.return_value = face_profile
        self.voice_identifier.enroll.return_value = None
        result = self.auth.enroll(
            "creator_123", "Storm", "/face.jpg", "/voice.wav"
        )
        self.assertIn("error", result)

    def test_enroll_with_additional_samples(self):
        face_profile = MagicMock()
        face_profile.profile_id = "face_123"
        self.face_recognizer.enroll.return_value = face_profile
        self.face_recognizer.add_sample.return_value = True

        voice_profile = MagicMock()
        voice_profile.profile_id = "voice_456"
        self.voice_identifier.enroll.return_value = voice_profile
        self.voice_identifier.add_sample.return_value = True

        result = self.auth.enroll(
            "creator_123", "Storm", "/face.jpg", "/voice.wav",
            additional_faces=["/face2.jpg", "/face3.jpg"],
            additional_voices=["/voice2.wav"],
        )
        self.assertEqual(result["status"], "enrolled")
        self.assertEqual(result["face_samples"], 3)
        self.assertEqual(result["voice_samples"], 2)

    # ===========================================================
    # VERIFICATION
    # ===========================================================

    def _enroll(self):
        """Helper to enroll biometrics."""
        face_profile = MagicMock()
        face_profile.profile_id = "face_123"
        self.face_recognizer.enroll.return_value = face_profile

        voice_profile = MagicMock()
        voice_profile.profile_id = "voice_456"
        self.voice_identifier.enroll.return_value = voice_profile

        self.auth.enroll("creator_123", "Storm", "/face.jpg", "/voice.wav")

    def test_verify_both_match(self):
        self._enroll()
        # Mock successful identification
        face_result = MagicMock()
        face_result.identified = True
        face_result.confidence = 0.85
        face_result.name = "Storm"
        self.face_recognizer.identify.return_value = face_result

        voice_result = MagicMock()
        voice_result.identified = True
        voice_result.confidence = 0.80
        voice_result.name = "Storm"
        self.voice_identifier.identify.return_value = voice_result

        result = self.auth.verify("/face.jpg", "/voice.wav")
        self.assertTrue(result.success)
        self.assertTrue(result.face_matched)
        self.assertTrue(result.voice_matched)

    def test_verify_face_only_match(self):
        self._enroll()
        face_result = MagicMock()
        face_result.identified = True
        face_result.confidence = 0.85
        face_result.name = "Storm"
        self.face_recognizer.identify.return_value = face_result

        voice_result = MagicMock()
        voice_result.identified = False
        voice_result.confidence = 0.3
        self.voice_identifier.identify.return_value = voice_result

        result = self.auth.verify("/face.jpg", "/voice.wav")
        self.assertFalse(result.success)
        self.assertTrue(result.face_matched)
        self.assertFalse(result.voice_matched)

    def test_verify_voice_only_match(self):
        self._enroll()
        face_result = MagicMock()
        face_result.identified = False
        face_result.confidence = 0.3
        self.face_recognizer.identify.return_value = face_result

        voice_result = MagicMock()
        voice_result.identified = True
        voice_result.confidence = 0.80
        voice_result.name = "Storm"
        self.voice_identifier.identify.return_value = voice_result

        result = self.auth.verify("/face.jpg", "/voice.wav")
        self.assertFalse(result.success)
        self.assertFalse(result.face_matched)
        self.assertTrue(result.voice_matched)

    def test_verify_neither_match(self):
        self._enroll()
        face_result = MagicMock()
        face_result.identified = False
        face_result.confidence = 0.2
        self.face_recognizer.identify.return_value = face_result

        voice_result = MagicMock()
        voice_result.identified = False
        voice_result.confidence = 0.2
        self.voice_identifier.identify.return_value = voice_result

        result = self.auth.verify("/face.jpg", "/voice.wav")
        self.assertFalse(result.success)

    def test_verify_not_enrolled(self):
        result = self.auth.verify("/face.jpg", "/voice.wav")
        self.assertFalse(result.success)
        self.assertIn("not enrolled", result.error)

    def test_verify_disabled(self):
        self._enroll()
        self.auth.disable()
        result = self.auth.verify("/face.jpg", "/voice.wav")
        self.assertFalse(result.success)
        self.assertIn("disabled", result.error)

    def test_verify_low_confidence(self):
        self._enroll()
        # Both match but confidence below threshold
        face_result = MagicMock()
        face_result.identified = True
        face_result.confidence = 0.40  # below REQUIRED_CONFIDENCE
        face_result.name = "Storm"
        self.face_recognizer.identify.return_value = face_result

        voice_result = MagicMock()
        voice_result.identified = True
        voice_result.confidence = 0.80
        voice_result.name = "Storm"
        self.voice_identifier.identify.return_value = voice_result

        result = self.auth.verify("/face.jpg", "/voice.wav")
        self.assertFalse(result.success)

    # ===========================================================
    # RATE LIMITING
    # ===========================================================

    def test_rate_limiting_lockout(self):
        self._enroll()
        # Mock failed identification
        face_result = MagicMock()
        face_result.identified = False
        face_result.confidence = 0.2
        self.face_recognizer.identify.return_value = face_result

        voice_result = MagicMock()
        voice_result.identified = False
        voice_result.confidence = 0.2
        self.voice_identifier.identify.return_value = voice_result

        # Fail MAX_FAILED_ATTEMPTS times
        for _ in range(MAX_FAILED_ATTEMPTS):
            self.auth.verify("/face.jpg", "/voice.wav")

        # Next attempt should be locked out
        result = self.auth.verify("/face.jpg", "/voice.wav")
        self.assertFalse(result.success)
        self.assertTrue(result.locked_out)

    # ===========================================================
    # MANAGEMENT
    # ===========================================================

    def test_enable_disable(self):
        self._enroll()
        self.assertTrue(self.auth.is_enabled())
        result = self.auth.disable()
        self.assertEqual(result["status"], "disabled")
        self.assertFalse(self.auth.is_enabled())
        result = self.auth.enable()
        self.assertEqual(result["status"], "enabled")
        self.assertTrue(self.auth.is_enabled())

    def test_enable_not_enrolled(self):
        result = self.auth.enable()
        self.assertIn("error", result)

    def test_disable_not_enrolled(self):
        result = self.auth.disable()
        self.assertIn("error", result)

    def test_remove_enrollment(self):
        self._enroll()
        result = self.auth.remove_enrollment()
        self.assertEqual(result["status"], "removed")
        self.assertFalse(self.auth.is_enrolled())

    def test_remove_not_enrolled(self):
        result = self.auth.remove_enrollment()
        self.assertIn("error", result)

    # ===========================================================
    # PERSISTENCE
    # ===========================================================

    def test_enrollment_persists(self):
        self._enroll()
        # Create new auth instance with same vault
        self.vault.lock()
        self.vault.unlock("test_passphrase_123")
        auth2 = BiometricAuth(
            self.vault, self.face_recognizer, self.voice_identifier,
        )
        self.assertTrue(auth2.is_enrolled())

    # ===========================================================
    # STATUS
    # ===========================================================

    def test_status_enrolled(self):
        self._enroll()
        status = self.auth.get_status()
        self.assertTrue(status["enrolled"])
        self.assertTrue(status["enabled"])
        self.assertEqual(status["creator_name"], "Storm")
        self.assertEqual(status["face_samples"], 1)
        self.assertEqual(status["voice_samples"], 1)

    def test_verification_count_increments(self):
        self._enroll()
        # Mock successful identification
        face_result = MagicMock()
        face_result.identified = True
        face_result.confidence = 0.85
        face_result.name = "Storm"
        self.face_recognizer.identify.return_value = face_result

        voice_result = MagicMock()
        voice_result.identified = True
        voice_result.confidence = 0.80
        voice_result.name = "Storm"
        self.voice_identifier.identify.return_value = voice_result

        self.auth.verify("/face.jpg", "/voice.wav")
        self.auth.verify("/face.jpg", "/voice.wav")
        status = self.auth.get_status()
        self.assertEqual(status["verification_count"], 2)

    # ===========================================================
    # UNLOCK WITH BIOMETRICS
    # ===========================================================

    def test_unlock_with_biometrics_success(self):
        self._enroll()
        # Mock successful identification
        face_result = MagicMock()
        face_result.identified = True
        face_result.confidence = 0.85
        face_result.name = "Storm"
        self.face_recognizer.identify.return_value = face_result

        voice_result = MagicMock()
        voice_result.identified = True
        voice_result.confidence = 0.80
        voice_result.name = "Storm"
        self.voice_identifier.identify.return_value = voice_result

        result = self.auth.unlock_with_biometrics(
            "/face.jpg", "/voice.wav", "test_passphrase_123"
        )
        self.assertEqual(result["status"], "unlocked")
        self.assertEqual(result["method"], "biometric")

    def test_unlock_with_biometrics_failure(self):
        self._enroll()
        # Mock failed identification
        face_result = MagicMock()
        face_result.identified = False
        face_result.confidence = 0.2
        self.face_recognizer.identify.return_value = face_result

        voice_result = MagicMock()
        voice_result.identified = True
        voice_result.confidence = 0.80
        voice_result.name = "Storm"
        self.voice_identifier.identify.return_value = voice_result

        result = self.auth.unlock_with_biometrics(
            "/face.jpg", "/voice.wav", "test_passphrase_123"
        )
        self.assertEqual(result["status"], "biometric_failed")
        self.assertEqual(result["method"], "passphrase_fallback")


if __name__ == "__main__":
    unittest.main()
