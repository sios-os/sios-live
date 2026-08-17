"""ADB-based phone adapter — controls a physical Android phone via USB.

This module gives ANUBIS full phone capabilities through a real Android
phone connected via USB with ADB (Android Debug Bridge) debugging enabled.

Capabilities:
- Send SMS text messages
- Receive SMS text messages (polling)
- Make phone calls (including 911)
- Answer incoming calls
- End active calls
- Get call history
- Check phone battery and signal
- Get the phone's phone number
- Notify on incoming SMS (callback)

The phone must:
1. Be an Android device with USB debugging enabled
2. Be connected to the machine via USB
3. Have ADB installed on the machine (`adb` on PATH)
4. Have an active SIM card with a cellular plan

This replaces both the VoIP module (Twilio/SIP) and the messaging
module (Signal/email-SMS) with a single, reliable, real-phone solution.

Safety:
- All calls and SMS are logged to the evidence ledger
- Emergency calls (911) are flagged and logged
- SMS sending requires Creator approval (consequential action)
- Calls require Creator approval (consequential action)
- Emergency contact notifications bypass approval (governed by contacts module)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ===========================================================
# Data structures
# ===========================================================

@dataclass
class SMSMessage:
    """A single SMS message."""
    msg_id: str = ""
    timestamp: float = 0.0
    sender: str = ""
    body: str = ""
    direction: str = "inbox"  # inbox, sent
    read: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "sender": self.sender,
            "body": self.body[:200],  # truncate for safety
            "direction": self.direction,
            "read": self.read,
        }


@dataclass
class CallRecord:
    """A single call record."""
    call_id: str = ""
    timestamp: float = 0.0
    number: str = ""
    duration_seconds: int = 0
    direction: str = "outgoing"  # outgoing, incoming, missed
    contact_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "timestamp": self.timestamp,
            "number": self._mask_number(),
            "duration_seconds": self.duration_seconds,
            "direction": self.direction,
            "contact_name": self.contact_name,
        }

    def _mask_number(self) -> str:
        if len(self.number) <= 4:
            return self.number
        return self.number[:-4] + "****"


@dataclass
class PhoneStatus:
    """Phone hardware status."""
    connected: bool = False
    device_id: str = ""
    battery_level: int = -1
    battery_charging: bool = False
    signal_strength: int = -1  # 0-4 bars
    phone_number: str = ""
    sim_state: str = "unknown"  # ready, absent, locked, unknown
    network_operator: str = ""
    airplane_mode: bool = False
    screen_on: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "device_id": self.device_id,
            "battery_level": self.battery_level,
            "battery_charging": self.battery_charging,
            "signal_strength": self.signal_strength,
            "phone_number": self._mask_number(),
            "sim_state": self.sim_state,
            "network_operator": self.network_operator,
            "airplane_mode": self.airplane_mode,
            "screen_on": self.screen_on,
        }

    def _mask_number(self) -> str:
        if not self.phone_number or len(self.phone_number) <= 4:
            return self.phone_number
        return self.phone_number[:-4] + "****"


# ===========================================================
# Phone adapter
# ===========================================================

class PhoneAdapter:
    """Controls a physical Android phone via ADB.

    Requires:
    - ADB installed and on PATH (or path provided)
    - Android phone connected via USB with debugging enabled
    - Active SIM card

    Usage:
        phone = PhoneAdapter(root="/path/to/sios", ledger=ledger)
        if phone.is_connected():
            phone.send_sms("+1234567890", "Hello from ANUBIS")
            phone.make_call("+1234567890")
    """

    ACTOR = "anubis.phone_adapter"

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        adb_path: str | None = None,
        ledger: Any | None = None,
        on_speak: Callable[[str], None] | None = None,
        on_sms_received: Callable[[SMSMessage], None] | None = None,
        auto_poll: bool = False,
        poll_interval: float = 10.0,
    ) -> None:
        self.root = Path(root) if root else Path(".")
        self.ledger = ledger
        self.on_speak = on_speak
        self.on_sms_received = on_sms_received
        self.auto_poll = auto_poll
        self.poll_interval = poll_interval

        # Find ADB
        self.adb_path = adb_path or shutil.which("adb") or "adb"

        # State
        self._device_id: str | None = None
        self._last_sms_id: int = 0
        self._poll_thread: Any = None
        self._polling = False
        self._state_dir = self.root / "memory" / "phone"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._sms_log = self._state_dir / "sms_log.jsonl"
        self._call_log = self._state_dir / "call_log.jsonl"

    def _log(self, action: str, data: dict[str, Any] | None = None) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data or {})
            except Exception:
                pass

    def _speak(self, text: str) -> None:
        if self.on_speak:
            try:
                self.on_speak(text)
            except Exception:
                pass

    def _mask_number(self, number: str) -> str:
        """Mask a phone number for logging (keep last 4 digits)."""
        if not number or len(number) <= 4:
            return number
        return number[:-4] + "****"

    # ===========================================================
    # ADB CONNECTION
    # ===========================================================

    def _run_adb(self, args: list[str], timeout: int = 15) -> tuple[int, str, str]:
        """Run an ADB command and return (returncode, stdout, stderr)."""
        cmd = [self.adb_path] + args
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
            )
            return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        except FileNotFoundError:
            return -1, "", "adb not found"
        except subprocess.TimeoutExpired:
            return -2, "", "adb command timed out"
        except Exception as e:
            return -3, "", str(e)

    def _run_shell(self, command: str, timeout: int = 15) -> tuple[int, str, str]:
        """Run an ADB shell command."""
        return self._run_adb(["shell", command], timeout=timeout)

    def is_connected(self) -> bool:
        """Check if a phone is connected via ADB."""
        rc, stdout, _ = self._run_adb(["devices"], timeout=5)
        if rc != 0:
            return False
        # Parse "List of devices attached\n<id>\tdevice"
        lines = stdout.splitlines()
        for line in lines[1:]:  # skip header
            parts = line.strip().split("\t")
            if len(parts) == 2 and parts[1] == "device":
                self._device_id = parts[0]
                return True
        return False

    def get_device_id(self) -> str | None:
        """Get the connected device ID."""
        if self._device_id:
            return self._device_id
        if self.is_connected():
            return self._device_id
        return None

    # ===========================================================
    # SMS
    # ===========================================================

    def send_sms(self, to: str, body: str) -> dict[str, Any]:
        """Send an SMS message.

        Args:
            to: Recipient phone number (E.164 format, e.g. +1234567890)
            body: Message text

        Returns:
            Dict with success status and details
        """
        if not self.is_connected():
            return {"sent": False, "error": "no phone connected"}

        if not to or not body:
            return {"sent": False, "error": "missing number or message"}

        # Send via ADB intent
        # Escape quotes in body
        safe_body = body.replace('"', '\\"').replace("'", "\\'")
        cmd = (
            f'am start -a android.intent.action.SENDTO '
            f'-d sms:{to} --es sms_body "{safe_body}"'
        )
        rc, stdout, stderr = self._run_shell(cmd)

        # Press enter to send (some phones need this)
        if rc == 0:
            time.sleep(0.5)
            self._run_shell("input keyevent 22")  # Enter key
            time.sleep(0.3)
            self._run_shell("input keyevent 66")  # Enter key (alternative)

        sent = rc == 0

        # Log
        result = {
            "sent": sent,
            "to": self._mask_number(to),
            "body_length": len(body),
            "timestamp": time.time(),
        }
        if not sent:
            result["error"] = stderr or stdout or "unknown error"

        self._log_sms("sent", to, body, sent)
        self._log("phone.sms_sent", result)

        if sent:
            self._speak(f"Text message sent to {self._mask_number(to)}")
        else:
            self._speak(f"Failed to send text message: {result.get('error', 'unknown')}")

        return result

    def receive_sms(self, limit: int = 10) -> dict[str, Any]:
        """Read recent SMS messages from the phone.

        Args:
            limit: Maximum number of messages to read

        Returns:
            Dict with list of messages
        """
        if not self.is_connected():
            return {"messages": [], "error": "no phone connected"}

        # Query SMS inbox via content provider
        rc, stdout, stderr = self._run_shell(
            f'content query --uri content://sms/inbox '
            f'--projection address:body:date:_id '
            f'--sort "date DESC" '
            f'--limit {limit}',
            timeout=10,
        )

        messages: list[SMSMessage] = []
        if rc == 0 and stdout:
            for line in stdout.splitlines():
                msg = self._parse_sms_line(line, "inbox")
                if msg:
                    messages.append(msg)

        return {
            "messages": [m.to_dict() for m in messages],
            "count": len(messages),
        }

    def get_sent_sms(self, limit: int = 10) -> dict[str, Any]:
        """Read recent sent SMS messages."""
        if not self.is_connected():
            return {"messages": [], "error": "no phone connected"}

        rc, stdout, stderr = self._run_shell(
            f'content query --uri content://sms/sent '
            f'--projection address:body:date:_id '
            f'--sort "date DESC" '
            f'--limit {limit}',
            timeout=10,
        )

        messages: list[SMSMessage] = []
        if rc == 0 and stdout:
            for line in stdout.splitlines():
                msg = self._parse_sms_line(line, "sent")
                if msg:
                    messages.append(msg)

        return {
            "messages": [m.to_dict() for m in messages],
            "count": len(messages),
        }

    def _parse_sms_line(self, line: str, direction: str) -> SMSMessage | None:
        """Parse a content query output line into an SMSMessage.

        Format: "Row: 0 address=+1234567890, body=Hello there, date=1234567890, _id=1"
        Note: body can contain commas, so we parse known fields from the end.
        """
        try:
            fields: dict[str, str] = {}

            # Extract known fields with regex — they appear as key=value
            # We extract from the end (date, _id) first, then address, then body
            # _id is always last
            id_match = re.search(r'_id=(\d+)', line)
            if id_match:
                fields["_id"] = id_match.group(1)

            date_match = re.search(r'date=(\d+)', line)
            if date_match:
                fields["date"] = date_match.group(1)

            address_match = re.search(r'address=(\+?\d+)', line)
            if address_match:
                fields["address"] = address_match.group(1)

            # Body is between "body=" and ", date="
            body_match = re.search(r'body=(.*?),\s*date=', line)
            if body_match:
                fields["body"] = body_match.group(1).strip()
            else:
                # Fallback: body= until end of line
                body_match = re.search(r'body=(.+)$', line)
                if body_match:
                    fields["body"] = body_match.group(1).strip()

            return SMSMessage(
                msg_id=fields.get("_id", ""),
                timestamp=float(fields.get("date", 0)) / 1000.0,
                sender=fields.get("address", ""),
                body=fields.get("body", ""),
                direction=direction,
                read=True,
            )
        except Exception:
            return None

    def _log_sms(self, direction: str, number: str, body: str, success: bool) -> None:
        """Log an SMS to the local log file."""
        try:
            entry = {
                "timestamp": time.time(),
                "direction": direction,
                "number": self._mask_number(number),
                "body_length": len(body),
                "success": success,
            }
            with open(self._sms_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ===========================================================
    # CALLS
    # ===========================================================

    def make_call(self, number: str) -> dict[str, Any]:
        """Make a phone call.

        Args:
            number: Phone number to call (E.164 format)

        Returns:
            Dict with success status
        """
        if not self.is_connected():
            return {"called": False, "error": "no phone connected"}

        if not number:
            return {"called": False, "error": "no number provided"}

        # Check if this is an emergency number
        is_emergency = number in ("911", "112", "999", "+1911")

        # Make the call via ADB intent
        cmd = f'am start -a android.intent.action.CALL -d tel:{number}'
        rc, stdout, stderr = self._run_shell(cmd)

        called = rc == 0

        result = {
            "called": called,
            "number": self._mask_number(number),
            "emergency": is_emergency,
            "timestamp": time.time(),
        }
        if not called:
            result["error"] = stderr or stdout or "unknown error"

        self._log_call("outgoing", number, 0, called, is_emergency)
        self._log("phone.call_made", result)

        if called:
            if is_emergency:
                self._speak(f"Emergency call placed to {number}")
            else:
                self._speak(f"Calling {self._mask_number(number)}")
        else:
            self._speak(f"Failed to make call: {result.get('error', 'unknown')}")

        return result

    def answer_call(self) -> dict[str, Any]:
        """Answer an incoming call."""
        if not self.is_connected():
            return {"answered": False, "error": "no phone connected"}

        rc, _, _ = self._run_shell("input keyevent KEYCODE_CALL")
        answered = rc == 0

        self._log("phone.call_answered", {"answered": answered})
        if answered:
            self._speak("Answering call")
        return {"answered": answered}

    def end_call(self) -> dict[str, Any]:
        """End the active call."""
        if not self.is_connected():
            return {"ended": False, "error": "no phone connected"}

        rc, _, _ = self._run_shell("input keyevent KEYCODE_ENDCALL")
        ended = rc == 0

        self._log("phone.call_ended", {"ended": ended})
        if ended:
            self._speak("Call ended")
        return {"ended": ended}

    def get_call_history(self, limit: int = 20) -> dict[str, Any]:
        """Get call history from the phone."""
        if not self.is_connected():
            return {"calls": [], "error": "no phone connected"}

        # Query call log
        rc, stdout, stderr = self._run_shell(
            f'content query --uri content://call_log/calls '
            f'--projection number:duration:date:type:name '
            f'--sort "date DESC" '
            f'--limit {limit}',
            timeout=10,
        )

        calls: list[CallRecord] = []
        if rc == 0 and stdout:
            for line in stdout.splitlines():
                call = self._parse_call_line(line)
                if call:
                    calls.append(call)

        return {
            "calls": [c.to_dict() for c in calls],
            "count": len(calls),
        }

    def _parse_call_line(self, line: str) -> CallRecord | None:
        """Parse a call log line into a CallRecord.

        Format: "Row: 0 number=+1234567890, duration=120, date=1697000000000, type=2, name=John"
        """
        try:
            fields: dict[str, str] = {}

            number_match = re.search(r'number=(\+?\d+)', line)
            if number_match:
                fields["number"] = number_match.group(1)

            duration_match = re.search(r'duration=(\d+)', line)
            if duration_match:
                fields["duration"] = duration_match.group(1)

            date_match = re.search(r'date=(\d+)', line)
            if date_match:
                fields["date"] = date_match.group(1)

            type_match = re.search(r'type=(\d+)', line)
            if type_match:
                fields["type"] = type_match.group(1)

            name_match = re.search(r'name=(.*?)(?:,\s*\w+=|$)', line)
            if name_match:
                fields["name"] = name_match.group(1).strip()

            call_type = int(fields.get("type", 0))
            direction = {1: "incoming", 2: "outgoing", 3: "missed"}.get(call_type, "unknown")

            return CallRecord(
                call_id="",
                timestamp=float(fields.get("date", 0)) / 1000.0,
                number=fields.get("number", ""),
                duration_seconds=int(fields.get("duration", 0)),
                direction=direction,
                contact_name=fields.get("name", ""),
            )
        except Exception:
            return None

    def _log_call(
        self, direction: str, number: str, duration: int,
        success: bool, emergency: bool = False,
    ) -> None:
        """Log a call to the local log file."""
        try:
            entry = {
                "timestamp": time.time(),
                "direction": direction,
                "number": self._mask_number(number),
                "duration_seconds": duration,
                "success": success,
                "emergency": emergency,
            }
            with open(self._call_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ===========================================================
    # PHONE STATUS
    # ===========================================================

    def get_status(self) -> dict[str, Any]:
        """Get phone hardware status."""
        status = PhoneStatus()

        if not self.is_connected():
            return status.to_dict()

        status.connected = True
        status.device_id = self._device_id or ""

        # Battery level
        rc, stdout, _ = self._run_shell("dumpsys battery | grep level")
        if rc == 0 and stdout:
            match = re.search(r'(\d+)', stdout)
            if match:
                status.battery_level = int(match.group(1))

        # Battery charging
        rc, stdout, _ = self._run_shell("dumpsys battery | grep status")
        if rc == 0 and stdout:
            status.battery_charging = "charging" in stdout.lower()

        # Signal strength
        rc, stdout, _ = self._run_shell(
            "dumpsys telephony.registry | grep mSignalStrength"
        )
        if rc == 0 and stdout:
            # Parse signal strength (approximate)
            match = re.search(r'(\d+)', stdout)
            if match:
                level = int(match.group(1))
                status.signal_strength = min(level, 4)

        # SIM state
        rc, stdout, _ = self._run_shell("getprop gsm.sim.state")
        if rc == 0 and stdout:
            status.sim_state = stdout.strip().lower()

        # Network operator
        rc, stdout, _ = self._run_shell("getprop gsm.operator.alpha")
        if rc == 0 and stdout:
            status.network_operator = stdout.strip()

        # Airplane mode
        rc, stdout, _ = self._run_shell("settings get global airplane_mode_on")
        if rc == 0 and stdout.strip() == "1":
            status.airplane_mode = True

        # Screen on
        rc, stdout, _ = self._run_shell("dumpsys power | grep mWakefulness")
        if rc == 0 and stdout:
            status.screen_on = "Awake" in stdout

        # Phone number (may not always be available)
        rc, stdout, _ = self._run_shell(
            "content query --uri content://telephony/siminfo "
            "--projection display_name:number"
        )
        if rc == 0 and stdout:
            # Try to extract number
            match = re.search(r'number=(\+?\d+)', stdout)
            if match:
                status.phone_number = match.group(1)

        return status.to_dict()

    def get_phone_number(self) -> str:
        """Get the phone's phone number."""
        if not self.is_connected():
            return ""

        # Try multiple methods
        # Method 1: telephony service
        rc, stdout, _ = self._run_shell(
            "service call iphonesubinfo 1"
        )
        if rc == 0 and stdout:
            # Parse the output (hex-encoded phone number)
            numbers = re.findall(r"'(\d+)'", stdout)
            if numbers:
                joined = "".join(numbers)
                if len(joined) >= 10:
                    return "+" + joined

        # Method 2: SIM info
        rc, stdout, _ = self._run_shell(
            "content query --uri content://telephony/siminfo "
            "--projection number"
        )
        if rc == 0 and stdout:
            match = re.search(r'number=(\+?\d+)', stdout)
            if match:
                return match.group(1)

        # Method 3: line1 number
        rc, stdout, _ = self._run_shell(
            "dumpsys telephony.registry | grep mLine1Number"
        )
        if rc == 0 and stdout:
            match = re.search(r'(\+?\d{10,})', stdout)
            if match:
                return match.group(1)

        return ""

    # ===========================================================
    # SMS POLLING (auto-receive)
    # ===========================================================

    def start_polling(self) -> dict[str, Any]:
        """Start polling for incoming SMS messages."""
        if self._polling:
            return {"polling": True, "message": "already polling"}
        if not self.is_connected():
            return {"polling": False, "error": "no phone connected"}

        import threading
        self._polling = True
        self._poll_thread = threading.Thread(
            target=self._poll_loop, daemon=True,
        )
        self._poll_thread.start()
        self._log("phone.polling_started", {"interval": self.poll_interval})
        return {"polling": True, "interval": self.poll_interval}

    def stop_polling(self) -> dict[str, Any]:
        """Stop SMS polling."""
        self._polling = False
        if self._poll_thread:
            self._poll_thread.join(timeout=5)
            self._poll_thread = None
        self._log("phone.polling_stopped", {})
        return {"polling": False}

    def _poll_loop(self) -> None:
        """Background polling loop for incoming SMS."""
        while self._polling:
            try:
                result = self.receive_sms(limit=5)
                for msg_dict in result.get("messages", []):
                    msg_id = msg_dict.get("msg_id", "")
                    try:
                        msg_id_int = int(msg_id)
                    except (ValueError, TypeError):
                        msg_id_int = 0

                    if msg_id_int > self._last_sms_id:
                        self._last_sms_id = msg_id_int
                        msg = SMSMessage(
                            msg_id=msg_dict.get("msg_id", ""),
                            timestamp=msg_dict.get("timestamp", 0),
                            sender=msg_dict.get("sender", ""),
                            body=msg_dict.get("body", ""),
                            direction="inbox",
                        )
                        self._log("phone.sms_received", msg.to_dict())
                        if self.on_sms_received:
                            try:
                                self.on_sms_received(msg)
                            except Exception:
                                pass
            except Exception:
                pass

            time.sleep(self.poll_interval)

    # ===========================================================
    # UTILITY
    # ===========================================================

    def wake_screen(self) -> dict[str, Any]:
        """Wake the phone screen (needed for some ADB commands)."""
        if not self.is_connected():
            return {"woken": False, "error": "no phone connected"}
        rc, _, _ = self._run_shell("input keyevent KEYCODE_WAKEUP")
        return {"woken": rc == 0}

    def unlock_screen(self, pin: str = "") -> dict[str, Any]:
        """Unlock the phone screen with optional PIN."""
        if not self.is_connected():
            return {"unlocked": False, "error": "no phone connected"}

        # Wake screen first
        self.wake_screen()
        time.sleep(0.5)

        # Swipe up to dismiss lock screen
        self._run_shell("input swipe 500 1500 500 300 300")
        time.sleep(0.5)

        # Enter PIN if provided
        if pin:
            for digit in pin:
                self._run_shell(f"input keyevent KEYCODE_{digit}")
            self._run_shell("input keyevent KEYCODE_ENTER")

        return {"unlocked": True}

    def send_ussd(self, code: str) -> dict[str, Any]:
        """Send a USSD code (e.g., *#06# for IMEI, *100# for balance)."""
        if not self.is_connected():
            return {"sent": False, "error": "no phone connected"}

        rc, stdout, stderr = self._run_shell(
            f'am start -a android.intent.action.CALL -d tel:{code}'
        )
        return {"sent": rc == 0, "code": code}

    def get_imei(self) -> str:
        """Get the phone's IMEI number."""
        if not self.is_connected():
            return ""
        rc, stdout, _ = self._run_shell("service call iphonesubinfo 1")
        if rc == 0 and stdout:
            # Parse IMEI from hex output
            numbers = re.findall(r"'(\d+)'", stdout)
            if numbers:
                return "".join(numbers)
        return ""

    def get_sms_log(self, limit: int = 50) -> dict[str, Any]:
        """Get the local SMS log (not the phone's SMS inbox)."""
        entries: list[dict[str, Any]] = []
        if self._sms_log.exists():
            try:
                lines = self._sms_log.read_text(encoding="utf-8").splitlines()
                for line in lines[-limit:]:
                    if line.strip():
                        entries.append(json.loads(line))
            except Exception:
                pass
        return {"entries": entries, "count": len(entries)}

    def get_call_log_local(self, limit: int = 50) -> dict[str, Any]:
        """Get the local call log."""
        entries: list[dict[str, Any]] = []
        if self._call_log.exists():
            try:
                lines = self._call_log.read_text(encoding="utf-8").splitlines()
                for line in lines[-limit:]:
                    if line.strip():
                        entries.append(json.loads(line))
            except Exception:
                pass
        return {"entries": entries, "count": len(entries)}

    def get_system_status(self) -> dict[str, Any]:
        """Get full phone adapter status for systems_status."""
        connected = self.is_connected()
        return {
            "connected": connected,
            "device_id": self._device_id or "",
            "adb_path": self.adb_path,
            "polling": self._polling,
            "poll_interval": self.poll_interval,
            "has_sms_callback": self.on_sms_received is not None,
            "sms_log_entries": len(self.get_sms_log().get("entries", [])),
            "call_log_entries": len(self.get_call_log_local().get("entries", [])),
        }
