"""VoIP calling — make phone calls via SIP.

ANUBIS can make phone calls for:
- Emergency calls (911, emergency contacts)
- Calling the Creator when something urgent happens
- Calling emergency contacts during a crisis
- Conference calls (future)

PROTOCOLS:
- SIP (Session Initiation Protocol) — standard VoIP
- Twilio API (cloud-based, requires account)
- Linphone CLI (open-source SIP client)

Uses subprocess to call linphone-cli or curl for Twilio API.
No external Python dependencies required.

SECURITY:
- Emergency calls (911) require Creator approval
- All calls logged to evidence ledger
- Call recordings require explicit consent (one-party consent states)
- Credentials never logged
- Rate limiting to prevent abuse
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# Call types
CALL_EMERGENCY = "emergency"  # 911
CALL_CONTACT = "contact"  # emergency contact
CALL_CREATOR = "creator"  # call the Creator
CALL_SUCCESSOR = "successor"  # call successor (takeover only)
CALL_TEST = "test"  # test call

# Call status
CALL_DIALING = "dialing"
CALL_RINGING = "ringing"
CALL_CONNECTED = "connected"
CALL_ENDED = "ended"
CALL_FAILED = "failed"
CALL_REJECTED = "rejected"
CALL_NO_ANSWER = "no_answer"
CALL_BUSY = "busy"


@dataclass
class CallRecord:
    """A record of a phone call."""
    call_id: str
    phone_number: str = ""
    call_type: str = CALL_CONTACT
    status: str = CALL_DIALING
    started_at: float = 0.0
    connected_at: float = 0.0
    ended_at: float = 0.0
    duration_seconds: float = 0.0
    reason: str = ""  # why the call was made
    recipient_name: str = ""
    recording_path: str = ""
    approved: bool = False
    transcript: str = ""  # if speech-to-text is available

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "phone_number": self._mask_number(self.phone_number),
            "call_type": self.call_type,
            "status": self.status,
            "started_at": self.started_at,
            "connected_at": self.connected_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "reason": self.reason,
            "recipient_name": self.recipient_name,
            "recording_path": self.recording_path,
            "approved": self.approved,
        }

    @staticmethod
    def _mask_number(number: str) -> str:
        if len(number) <= 4:
            return number
        return number[:3] + "*" * (len(number) - 7) + number[-4:]


class VoIPSystem:
    """VoIP calling system.

    Makes phone calls via SIP (linphone-cli) or Twilio API.
    All calls require approval except test calls.
    """

    ACTOR = "anubis.voip"

    def __init__(
        self,
        root: str | Path,
        *,
        sip_account: str = "",
        sip_password: str = "",
        sip_domain: str = "",
        twilio_sid: str = "",
        twilio_token: str = "",
        twilio_from: str = "",
        ledger: Any | None = None,
        on_call_status: Callable[[CallRecord], None] | None = None,
        require_approval: bool = True,
    ) -> None:
        self.root = Path(root)
        self.sip_account = sip_account
        self.sip_password = sip_password
        self.sip_domain = sip_domain
        self.twilio_sid = twilio_sid
        self.twilio_token = twilio_token
        self.twilio_from = twilio_from
        self.ledger = ledger
        self.on_call_status = on_call_status
        self.require_approval = require_approval

        self._state_dir = self.root / "memory" / "voip"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._calls_file = self._state_dir / "calls.jsonl"

        self._linphone = shutil.which("linphonec")
        self._calls: dict[str, CallRecord] = {}

        # Rate limiting
        self._call_times: list[float] = []
        self._rate_limit_window = 3600.0  # 1 hour
        self._rate_limit_max = 10  # calls per hour

    # --------------------------------------------------- calling

    def make_call(
        self,
        phone_number: str,
        *,
        call_type: str = CALL_CONTACT,
        reason: str = "",
        recipient_name: str = "",
        approved: bool = False,
    ) -> CallRecord:
        """Make a phone call.

        For emergency calls (911), approval is always required.
        For other calls, approval is required if require_approval is True.
        """
        # Rate limit check
        if not self._check_rate_limit():
            call = CallRecord(
                call_id=self._gen_id(),
                phone_number=phone_number,
                call_type=call_type,
                status=CALL_FAILED,
                started_at=time.time(),
                reason=reason,
                recipient_name=recipient_name,
            )
            call.status = CALL_FAILED
            self._record_call(call)
            return call

        # Approval check
        needs_approval = self.require_approval or call_type == CALL_EMERGENCY
        if needs_approval and not approved:
            call = CallRecord(
                call_id=self._gen_id(),
                phone_number=phone_number,
                call_type=call_type,
                status=CALL_REJECTED,
                started_at=time.time(),
                reason=reason,
                recipient_name=recipient_name,
            )
            self._record_call(call)
            self._log("call.rejected", {"reason": "not approved", "type": call_type})
            return call

        call = CallRecord(
            call_id=self._gen_id(),
            phone_number=phone_number,
            call_type=call_type,
            status=CALL_DIALING,
            started_at=time.time(),
            reason=reason,
            recipient_name=recipient_name,
            approved=True,
        )

        # Try Twilio first (if configured)
        if self.twilio_sid and self.twilio_token:
            success = self._call_twilio(phone_number)
        # Try SIP/linphone
        elif self._linphone and self.sip_account:
            success = self._call_sip(phone_number)
        else:
            success = False

        if success:
            call.status = CALL_CONNECTED
            call.connected_at = time.time()
        else:
            call.status = CALL_FAILED

        call.ended_at = time.time()
        call.duration_seconds = call.ended_at - call.connected_at if call.connected_at else 0

        self._record_call(call)
        self._log("call.made", {
            "type": call_type, "status": call.status,
            "duration": call.duration_seconds,
        })

        if self.on_call_status:
            try:
                self.on_call_status(call)
            except Exception:
                pass

        return call

    def call_emergency(self, reason: str = "", approved: bool = False) -> CallRecord:
        """Call 911. Always requires approval."""
        return self.make_call(
            "911", call_type=CALL_EMERGENCY,
            reason=reason or "Emergency", recipient_name="Emergency Services",
            approved=approved,
        )

    def call_contact(self, phone: str, name: str, reason: str = "", approved: bool = False) -> CallRecord:
        """Call an emergency contact."""
        return self.make_call(
            phone, call_type=CALL_CONTACT,
            reason=reason, recipient_name=name,
            approved=approved,
        )

    def call_creator(self, phone: str, reason: str = "", approved: bool = True) -> CallRecord:
        """Call the Creator. Auto-approved (Creator initiated or urgent)."""
        return self.make_call(
            phone, call_type=CALL_CREATOR,
            reason=reason, recipient_name="Creator",
            approved=approved,
        )

    def call_successor(self, phone: str, reason: str = "", approved: bool = False) -> CallRecord:
        """Call the successor. Only during takeover. Requires approval."""
        return self.make_call(
            phone, call_type=CALL_SUCCESSOR,
            reason=reason or "Takeover event", recipient_name="Successor",
            approved=approved,
        )

    # --------------------------------------------------- call methods

    def _call_twilio(self, phone_number: str) -> bool:
        """Make a call via Twilio API."""
        if not self.twilio_sid or not self.twilio_token:
            return False
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Calls.json"
            data = (
                f"From={self.twilio_from}&To={phone_number}&"
                f"Url=http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient"
            ).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            import base64
            auth = base64.b64encode(
                f"{self.twilio_sid}:{self.twilio_token}".encode()
            ).decode()
            req.add_header("Authorization", f"Basic {auth}")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")

            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status in (200, 201)
        except Exception:
            return False

    def _call_sip(self, phone_number: str) -> bool:
        """Make a call via SIP using linphonec."""
        if not self._linphone:
            return False
        try:
            # Build SIP URI
            sip_uri = f"sip:{phone_number}@{self.sip_domain}"
            cmd = [
                self._linphone,  # type: ignore
                "-c", f"register sip:{self.sip_account}@{self.sip_domain} {self.sip_domain} {self.sip_password}",
                "-c", f"call {sip_uri}",
                "-c", "wait 30",
                "-c", "terminate",
                "-c", "quit",
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            return result.returncode == 0
        except Exception:
            return False

    # --------------------------------------------------- queries

    def get_calls(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._calls_file.exists():
            return []
        try:
            lines = self._calls_file.read_text(encoding="utf-8").strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_call(self, call_id: str) -> dict[str, Any] | None:
        call = self._calls.get(call_id)
        return call.to_dict() if call else None

    def get_calls_by_type(self, call_type: str) -> list[dict[str, Any]]:
        calls = self.get_calls(limit=9999)
        return [c for c in calls if c.get("call_type") == call_type]

    def get_emergency_calls(self) -> list[dict[str, Any]]:
        return self.get_calls_by_type(CALL_EMERGENCY)

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        return {
            "configured": bool(
                (self.twilio_sid and self.twilio_token) or
                (self._linphone and self.sip_account)
            ),
            "method": "twilio" if self.twilio_sid else ("sip" if self._linphone else "none"),
            "linphone_available": self._linphone is not None,
            "twilio_configured": bool(self.twilio_sid),
            "sip_configured": bool(self.sip_account and self.sip_domain),
            "require_approval": self.require_approval,
            "total_calls": len(self.get_calls(limit=9999)),
        }

    # --------------------------------------------------- helpers

    def _gen_id(self) -> str:
        return hashlib.sha256(
            f"call:{time.time()}".encode()
        ).hexdigest()[:16]

    def _check_rate_limit(self) -> bool:
        now = time.time()
        self._call_times = [t for t in self._call_times if now - t < self._rate_limit_window]
        if len(self._call_times) >= self._rate_limit_max:
            return False
        self._call_times.append(now)
        return True

    def _record_call(self, call: CallRecord) -> None:
        self._calls[call.call_id] = call
        try:
            with open(self._calls_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(call.to_dict()) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
