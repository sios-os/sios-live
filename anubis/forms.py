"""Form templates — structured forms the Creator can request and fill out.

DEMON can present these forms via voice, phone app, or chat. The
Creator fills in the fields and submits. DEMON saves the data.

Forms available:
1. account_form — add a new account (URL, username, password, bill info)
2. identity_form — Creator enrollment (name, passphrase, recovery contacts)
3. successor_form — Successor enrollment (name, relationship, conditions)
4. update_account_form — update an existing account
5. biometric_enroll_form — enroll face + voice for biometric auth

Each form has:
- A list of fields with names, types, labels, and whether required
- A validator that checks the submitted data
- A handler that processes the valid data

The form can be requested via:
- Voice: "Give me the account form" / "I want to add an account"
- API: {"cmd": "form_get", "form": "account_form"}
- Chat: "Send me the form to add an account"

The form is submitted via:
- API: {"cmd": "form_submit", "form": "account_form", "data": {...}}
- The daemon validates and processes the submission
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


# ===========================================================
# Form field types
# ===========================================================

FIELD_TEXT = "text"
FIELD_PASSWORD = "password"
FIELD_NUMBER = "number"
FIELD_BOOLEAN = "boolean"
FIELD_SELECT = "select"
FIELD_EMAIL = "email"
FIELD_URL = "url"
FIELD_DATE = "date"
FIELD_TEXTAREA = "textarea"


@dataclass
class FormField:
    """A single field in a form."""
    name: str
    label: str
    field_type: str = FIELD_TEXT
    required: bool = False
    placeholder: str = ""
    help_text: str = ""
    options: list[str] = field(default_factory=list)  # for select fields
    default: Any = None
    min_value: float | None = None
    max_value: float | None = None
    min_length: int = 0
    max_length: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.field_type,
            "required": self.required,
            "placeholder": self.placeholder,
            "help_text": self.help_text,
            "options": self.options,
            "default": self.default,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "min_length": self.min_length,
            "max_length": self.max_length,
        }


@dataclass
class FormDefinition:
    """A complete form definition."""
    form_id: str
    title: str
    description: str
    fields: list[FormField]
    submit_label: str = "Submit"

    def to_dict(self) -> dict[str, Any]:
        return {
            "form_id": self.form_id,
            "title": self.title,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
            "submit_label": self.submit_label,
        }

    def validate(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate submitted data against the form definition.

        Returns (valid, errors).
        """
        errors: list[str] = []

        for f in self.fields:
            value = data.get(f.name)

            # Check required
            if f.required and (value is None or value == ""):
                errors.append(f"{f.label} is required")
                continue

            # Skip further validation if field is empty and not required
            if value is None or value == "":
                continue

            # Type validation
            if f.field_type == FIELD_NUMBER:
                try:
                    num = float(value)
                    if f.min_value is not None and num < f.min_value:
                        errors.append(f"{f.label} must be at least {f.min_value}")
                    if f.max_value is not None and num > f.max_value:
                        errors.append(f"{f.label} must be at most {f.max_value}")
                except (ValueError, TypeError):
                    errors.append(f"{f.label} must be a number")

            elif f.field_type == FIELD_BOOLEAN:
                if not isinstance(value, bool):
                    # Accept string representations
                    if isinstance(value, str):
                        if value.lower() not in ("true", "false", "yes", "no", "1", "0"):
                            errors.append(f"{f.label} must be true or false")
                    else:
                        errors.append(f"{f.label} must be true or false")

            elif f.field_type == FIELD_SELECT:
                if str(value) not in f.options:
                    errors.append(f"{f.label} must be one of: {', '.join(f.options)}")

            elif f.field_type == FIELD_EMAIL:
                if "@" not in str(value) or "." not in str(value):
                    errors.append(f"{f.label} must be a valid email address")

            elif f.field_type == FIELD_URL:
                val = str(value)
                if not val.startswith(("http://", "https://")):
                    errors.append(f"{f.label} must start with http:// or https://")

            # Length validation
            if f.min_length and len(str(value)) < f.min_length:
                errors.append(f"{f.label} must be at least {f.min_length} characters")
            if f.max_length and len(str(value)) > f.max_length:
                errors.append(f"{f.label} must be at most {f.max_length} characters")

        return len(errors) == 0, errors


# ===========================================================
# Form definitions
# ===========================================================

ACCOUNT_TYPES_LIST = [
    "banking", "utility", "subscription", "social", "email",
    "shopping", "government", "health", "work", "other",
]


def account_form() -> FormDefinition:
    """Form for adding a new account."""
    return FormDefinition(
        form_id="account_form",
        title="Add Account",
        description="Add a new account with credentials and optional bill tracking.",
        submit_label="Save Account",
        fields=[
            FormField(
                name="name", label="Account Name", field_type=FIELD_TEXT,
                required=True, placeholder="e.g., Electric Company",
                help_text="A friendly name for this account",
                max_length=100,
            ),
            FormField(
                name="url", label="Login URL", field_type=FIELD_URL,
                placeholder="https://example.com/login",
                help_text="The login page URL",
            ),
            FormField(
                name="username", label="Username or Email", field_type=FIELD_TEXT,
                placeholder="your@email.com",
                help_text="Your username for this account",
            ),
            FormField(
                name="password", label="Password", field_type=FIELD_PASSWORD,
                placeholder="••••••••",
                help_text="Your password (stored encrypted)",
            ),
            FormField(
                name="account_type", label="Account Type", field_type=FIELD_SELECT,
                options=ACCOUNT_TYPES_LIST, default="other",
                help_text="Category for this account",
            ),
            FormField(
                name="bill_due_day", label="Bill Due Day", field_type=FIELD_NUMBER,
                placeholder="1-31 (leave empty if no recurring bill)",
                min_value=0, max_value=31, default=0,
                help_text="Day of month the bill is due (0 = no bill)",
            ),
            FormField(
                name="bill_amount", label="Bill Amount", field_type=FIELD_NUMBER,
                placeholder="0.00", min_value=0,
                help_text="Estimated bill amount (0 if variable)",
            ),
            FormField(
                name="payment_url", label="Payment URL", field_type=FIELD_URL,
                placeholder="https://example.com/pay",
                help_text="Direct payment URL (if different from login)",
            ),
            FormField(
                name="auto_pay", label="Auto-Pay Enabled", field_type=FIELD_BOOLEAN,
                default=False,
                help_text="Is this bill on auto-pay?",
            ),
            FormField(
                name="notes", label="Notes", field_type=FIELD_TEXTAREA,
                placeholder="Any additional notes",
                help_text="Optional notes about this account",
                max_length=500,
            ),
        ],
    )


def identity_form() -> FormDefinition:
    """Form for Creator enrollment — all Creator info."""
    return FormDefinition(
        form_id="identity_form",
        title="Creator Enrollment",
        description="Set up your Creator identity. This is the master identity for ANUBIS.",
        submit_label="Enroll Creator",
        fields=[
            FormField(
                name="display_name", label="Full Name", field_type=FIELD_TEXT,
                required=True, placeholder="Your full name",
                help_text="Your legal name or the name you want ANUBIS to know you by",
                min_length=2, max_length=100,
            ),
            FormField(
                name="preferred_name", label="Preferred Name", field_type=FIELD_TEXT,
                placeholder="What should I call you?",
                help_text="The name DEMON will use when speaking to you",
                max_length=50,
            ),
            FormField(
                name="passphrase", label="Passphrase", field_type=FIELD_PASSWORD,
                required=True, placeholder="At least 8 characters",
                help_text="Master passphrase to unlock the vault. Choose carefully.",
                min_length=8, max_length=200,
            ),
            FormField(
                name="language", label="Language", field_type=FIELD_SELECT,
                options=["en", "es", "fr", "de", "it", "pt", "ja", "zh", "ko", "ar"],
                default="en",
                help_text="Your preferred language",
            ),
            FormField(
                name="recovery_email", label="Recovery Email", field_type=FIELD_EMAIL,
                placeholder="recovery@email.com",
                help_text="Email for account recovery",
            ),
            FormField(
                name="recovery_phone", label="Recovery Phone", field_type=FIELD_TEXT,
                placeholder="+1-555-0100",
                help_text="Phone number for recovery",
            ),
            FormField(
                name="accessibility_needs", label="Accessibility Needs", field_type=FIELD_TEXTAREA,
                placeholder="e.g., voice-only interface, large text",
                help_text="Any accessibility requirements",
                max_length=500,
            ),
        ],
    )


def successor_form() -> FormDefinition:
    """Form for successor enrollment."""
    return FormDefinition(
        form_id="successor_form",
        title="Successor Enrollment",
        description=(
            "Designate a successor who can take over if you are confirmed "
            "absent. The successor cannot act until the activation "
            "conditions are met."
        ),
        submit_label="Enroll Successor",
        fields=[
            FormField(
                name="display_name", label="Successor Full Name", field_type=FIELD_TEXT,
                required=True, placeholder="Successor's full name",
                min_length=2, max_length=100,
            ),
            FormField(
                name="relationship", label="Relationship", field_type=FIELD_TEXT,
                required=True, placeholder="e.g., son, daughter, spouse, friend",
                help_text="Relationship to the Creator",
                max_length=50,
            ),
            FormField(
                name="consent_given", label="Successor Has Consented", field_type=FIELD_BOOLEAN,
                required=True, default=False,
                help_text="The successor must consent to this role",
            ),
            FormField(
                name="activation_conditions", label="Activation Conditions",
                field_type=FIELD_TEXTAREA,
                placeholder="e.g., confirmed absence for 30 days, Creator incapacitation",
                help_text="Conditions that must be met before the successor can act",
                max_length=1000,
            ),
            FormField(
                name="contact_email", label="Contact Email", field_type=FIELD_EMAIL,
                placeholder="successor@email.com",
            ),
            FormField(
                name="contact_phone", label="Contact Phone", field_type=FIELD_TEXT,
                placeholder="+1-555-0100",
            ),
        ],
    )


def update_account_form() -> FormDefinition:
    """Form for updating an existing account."""
    return FormDefinition(
        form_id="update_account_form",
        title="Update Account",
        description="Update an existing account. Only fill in the fields you want to change.",
        submit_label="Update Account",
        fields=[
            FormField(
                name="account_id", label="Account ID", field_type=FIELD_TEXT,
                required=True, placeholder="The account ID to update",
            ),
            FormField(
                name="name", label="Account Name", field_type=FIELD_TEXT,
                placeholder="New name (leave empty to keep current)",
            ),
            FormField(
                name="url", label="Login URL", field_type=FIELD_URL,
                placeholder="https://example.com/login",
            ),
            FormField(
                name="username", label="Username", field_type=FIELD_TEXT,
            ),
            FormField(
                name="password", label="Password", field_type=FIELD_PASSWORD,
                help_text="Enter new password to update",
            ),
            FormField(
                name="account_type", label="Account Type", field_type=FIELD_SELECT,
                options=ACCOUNT_TYPES_LIST,
            ),
            FormField(
                name="bill_due_day", label="Bill Due Day", field_type=FIELD_NUMBER,
                min_value=0, max_value=31,
            ),
            FormField(
                name="bill_amount", label="Bill Amount", field_type=FIELD_NUMBER,
                min_value=0,
            ),
            FormField(
                name="payment_url", label="Payment URL", field_type=FIELD_URL,
            ),
            FormField(
                name="auto_pay", label="Auto-Pay", field_type=FIELD_BOOLEAN,
            ),
            FormField(
                name="notes", label="Notes", field_type=FIELD_TEXTAREA,
                max_length=500,
            ),
        ],
    )


def biometric_enroll_form() -> FormDefinition:
    """Form for enrolling biometric data (face + voice)."""
    return FormDefinition(
        form_id="biometric_enroll_form",
        title="Biometric Enrollment",
        description=(
            "Enroll your face and voice so DEMON can unlock the vault "
            "without a passphrase. Both face AND voice must match — "
            "neither alone is sufficient."
        ),
        submit_label="Enroll Biometrics",
        fields=[
            FormField(
                name="name", label="Your Name", field_type=FIELD_TEXT,
                required=True, placeholder="Your name as ANUBIS knows you",
                help_text="Must match your Creator name",
            ),
            FormField(
                name="face_image_path", label="Face Photo Path", field_type=FIELD_TEXT,
                required=True, placeholder="/path/to/your/photo.jpg",
                help_text="Path to a clear photo of your face",
            ),
            FormField(
                name="voice_audio_path", label="Voice Sample Path", field_type=FIELD_TEXT,
                required=True, placeholder="/path/to/voice/sample.wav",
                help_text="Path to a 5+ second voice recording",
            ),
            FormField(
                name="additional_face_images", label="Additional Face Photos",
                field_type=FIELD_TEXTAREA,
                placeholder="One path per line (optional, improves accuracy)",
                help_text="Additional photos to improve recognition accuracy",
            ),
            FormField(
                name="additional_voice_samples", label="Additional Voice Samples",
                field_type=FIELD_TEXTAREA,
                placeholder="One path per line (optional, improves accuracy)",
                help_text="Additional voice recordings to improve accuracy",
            ),
        ],
    )


# ===========================================================
# Form registry
# ===========================================================

FORMS: dict[str, Callable[[], FormDefinition]] = {
    "account_form": account_form,
    "identity_form": identity_form,
    "successor_form": successor_form,
    "update_account_form": update_account_form,
    "biometric_enroll_form": biometric_enroll_form,
}


def get_form(form_id: str) -> FormDefinition | None:
    """Get a form definition by ID."""
    factory = FORMS.get(form_id)
    return factory() if factory else None


def list_forms() -> list[dict[str, str]]:
    """List all available forms."""
    result = []
    for fid, factory in FORMS.items():
        form = factory()
        result.append({
            "form_id": form.form_id,
            "title": form.title,
            "description": form.description,
        })
    return result


def validate_form(form_id: str, data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate data against a form. Returns (valid, errors)."""
    form = get_form(form_id)
    if form is None:
        return False, [f"Unknown form: {form_id}"]
    return form.validate(data)
