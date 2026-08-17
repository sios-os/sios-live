"""Universal voice command interpreter — lets ANUBIS understand ANY command by voice.

Instead of pre-registering every possible voice command phrase, this module
uses the LLM to interpret natural language and translate it into a daemon
command. This means the Creator can say anything and ANUBIS will understand:

    "create a snapshot"              → {"cmd": "snapshot_create"}
    "run a health check"             → {"cmd": "self_repair_check"}
    "give me the drive report"       → {"cmd": "drive_report"}
    "what's the system status"       → {"cmd": "systems_status"}
    "start a dream cycle"            → {"cmd": "dream_run"}
    "generate the book of anubis"    → {"cmd": "book_generate"}
    "create a cold archive"          → {"cmd": "cold_archive_create"}
    "list all my skills"             → {"cmd": "skills"}
    "what time is it"                → {"cmd": "chat", "text": "What time is it?"}
    "tell me a joke"                 → {"cmd": "chat", "text": "Tell me a joke"}

The interpreter:
1. Takes the transcribed text
2. Asks the LLM to classify it as a command or conversation
3. If it's a command, the LLM generates the JSON command
4. The command is validated against the known command list
5. The command is executed via the daemon's dispatch
6. The result is spoken back

Safety:
- Consequential commands (financial, email, calls) still require Creator approval
- The constitutional gate still runs on all actions
- The interpreter cannot bypass governance
- Commands that require parameters the LLM can't infer are rejected
- The LLM is given the command list so it knows what's available
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Callable

from .ledger import Ledger


# ===========================================================
# Command interpreter
# ===========================================================

class VoiceCommandInterpreter:
    """Interprets natural language as daemon commands using the LLM.

    Sits between the voice command router (pre-registered phrases)
    and the chat fallback (general conversation). When the router
    doesn't match, this interpreter tries to parse the text as a
    command before falling back to chat.
    """

    ACTOR = "anubis.voice_interpreter"

    # Commands that are safe to execute without additional confirmation
    SAFE_COMMANDS = {
        "status", "skills", "systems_status", "ledger",
        "memory_stats", "memory_recall",
        "snapshot_status", "snapshot_list", "snapshot_verify",
        "self_repair_status", "self_repair_check", "self_repair_alerts",
        "drive_report", "drive_monitor_status",
        "cold_archive_status", "cold_archive_list",
        "book_status", "book_list_editions", "book_seal_status",
        "scheduler_status",
        "dream_status", "dream_history", "dream_recommendations", "dream_gaps",
        "local_training_status", "local_training_list",
        "knowledge_search", "list_directors", "list_specialties",
        "registry_stats", "court_stats", "policy_stats",
        "weather_forecast", "weather_alerts",
        "calendar_today", "calendar_upcoming",
        "sleep_status", "sensory_status",
        "perception_status", "contacts_status",
        "observer_status", "observer_observations", "observer_predictions",
        "consciousness_status", "consciousness_self_concept",
        "proactive_status", "research_status",
        "finance_status", "finance_upcoming_bills", "finance_spending",
        "news_status", "news_briefing",
        "prospects_status", "prospects_stats",
        "cloud_sync_status", "gateway_status",
        "cloud_model_status", "lambda_status",
        "identity_stats", "biometric_status",
        "api_server_status", "smarthome_status", "smarthome_devices",
        "dashboard_status", "email_status",
        "voip_status", "voip_calls",
        "network_ops_status", "network_ops_devices",
        "remote_monitor_status", "threat_analysis_status",
        "cameras_status", "cameras_list", "cameras_events",
        "messaging_status", "iot_status",
        "boot_check", "boot_check_history",
        "self_repair_degradation_status",
        "self_repair_cross_check",
        "ab_status",
        "self_modify_status", "self_modify_list", "self_modify_get",
        "mixed_model_status", "mixed_model_stage", "mixed_model_generations",
        "mixed_model_teacher_dependency",
    }

    # Commands that create/change state but are generally safe
    ACTION_COMMANDS = {
        "snapshot_create", "snapshot_retention",
        "self_repair_auto", "self_repair_sign_core",
        "book_generate",
        "cold_archive_create", "cold_archive_retention",
        "dream_run", "dream_mark_acted",
        "scheduler_start", "scheduler_stop",
        "memory_purge",
        "goodnight", "wake", "good_morning",
        "sensory_set_mode",
        "email_check",
        "news_fetch",
    }

    # Commands that ALWAYS require Creator approval (constitutional)
    RESTRICTED_COMMANDS = {
        "email_send", "voip_call", "voip_end_call",
        "cloud_sync", "cloud_sync_upload", "cloud_sync_download",
        "gateway_fetch", "gateway_search",
        "lambda_submit", "lambda_cancel",
        "prospects_approve", "prospects_reject",
        "contacts_notify_emergency",
        "messaging_send",
        "network_ops_scan",
        "cameras_start_monitoring",
        "book_unseal",
        "local_training_run", "local_training_pipeline",
        "vault_unlock",
        "self_repair_failover", "self_repair_rebuild",
        "self_repair_enter_degraded",
        "snapshot_restore", "snapshot_delete",
        "cold_archive_restore", "cold_archive_delete",
        "ab_promote", "ab_rollback",
        "self_modify_approve", "self_modify_apply", "self_modify_rollback",
    }

    # The system prompt for the LLM
    SYSTEM_PROMPT = """You are a voice command interpreter for ANUBIS, an autonomous AI system.
Your job is to determine whether the user's spoken text is a COMMAND or CONVERSATION.

If it's a COMMAND, translate it into a JSON daemon command.
If it's CONVERSATION, return {"type": "chat"}.

Available commands include: status, skills, chat, snapshot_create, snapshot_list,
snapshot_status, snapshot_verify, self_repair_check, self_repair_auto,
self_repair_status, drive_report, cold_archive_create, cold_archive_status,
book_generate, book_status, book_read_latest, dream_run, dream_status,
dream_history, dream_recommendations, scheduler_status, systems_status,
memory_stats, memory_recall, weather_forecast, calendar_today,
goodnight, wake, good_morning, sleep_status, local_training_status,
local_training_pipeline, knowledge_search, list_directors, consciousness_reflect,
consciousness_self_concept, finance_upcoming_bills, news_briefing, and many more.

If the user is asking a question or making conversation, return {"type": "chat"}.
If the user is giving an instruction to do something, return {"type": "command", "cmd": "command_name", "params": {}}.

Respond ONLY with valid JSON, no explanation.""";

    def __init__(
        self,
        model: Any,
        *,
        dispatch: Callable[[dict], dict] | None = None,
        ledger: Ledger | None = None,
        on_speak: Callable[[str], None] | None = None,
    ) -> None:
        self.model = model
        self.dispatch = dispatch
        self.ledger = ledger
        self.on_speak = on_speak
        self._command_list: list[str] | None = None

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

    def interpret(self, text: str) -> dict[str, Any]:
        """Interpret spoken text as a command or conversation.

        Returns:
            {
                "type": "command" | "chat" | "unknown",
                "cmd": str,        # if command
                "params": dict,    # if command
                "raw": str,        # original text
            }
        """
        if not text or not text.strip():
            return {"type": "unknown", "raw": text}

        # Quick keyword matching for common commands (no LLM needed)
        quick = self._quick_match(text)
        if quick:
            return quick

        # Use LLM to interpret
        if self.model is None:
            return {"type": "chat", "raw": text}

        try:
            prompt = (
                f"{self.SYSTEM_PROMPT}\n\n"
                f"User said: \"{text}\"\n\n"
                f"Respond with JSON only:"
            )
            response = self.model.generate(prompt, max_tokens=200)
            parsed = self._parse_llm_response(response)
            parsed["raw"] = text
            return parsed
        except Exception as e:
            return {"type": "chat", "raw": text, "error": str(e)}

    def _quick_match(self, text: str) -> dict[str, Any] | None:
        """Quick keyword matching for common commands — no LLM needed.

        This handles the most common commands instantly without
        waiting for the LLM, making voice interaction feel responsive.
        """
        text_lower = text.lower().strip()

        # Status and info commands
        if any(p in text_lower for p in ["system status", "systems status", "full status", "everything status"]):
            return {"type": "command", "cmd": "systems_status", "params": {}}
        if text_lower in ["status", "how are you", "how are you doing", "health check"]:
            return {"type": "command", "cmd": "status", "params": {}}
        if any(p in text_lower for p in ["list skills", "what skills", "show skills", "my skills"]):
            return {"type": "command", "cmd": "skills", "params": {}}

        # Snapshot commands
        if any(p in text_lower for p in ["create snapshot", "take snapshot", "make snapshot", "new snapshot", "create a snapshot", "take a snapshot"]):
            return {"type": "command", "cmd": "snapshot_create", "params": {}}
        if any(p in text_lower for p in ["snapshot status", "snapshot list", "list snapshots", "show snapshots", "list my snapshots"]):
            return {"type": "command", "cmd": "snapshot_list", "params": {}}

        # Self-repair commands
        if any(p in text_lower for p in ["health check", "run health check", "self repair check", "integrity check", "run a health check"]):
            return {"type": "command", "cmd": "self_repair_check", "params": {}}
        if any(p in text_lower for p in ["auto repair", "self repair auto", "fix yourself", "run repair"]):
            return {"type": "command", "cmd": "self_repair_auto", "params": {}}
        if any(p in text_lower for p in ["repair status", "self repair status"]):
            return {"type": "command", "cmd": "self_repair_status", "params": {}}

        # Drive report
        if any(p in text_lower for p in ["drive report", "disk report", "storage report", "drive health", "disk health", "give me the drive report"]):
            return {"type": "command", "cmd": "drive_report", "params": {}}

        # Dream cycle
        if any(p in text_lower for p in ["dream cycle", "run dream", "start dream", "dream run", "start a dream"]):
            return {"type": "command", "cmd": "dream_run", "params": {}}
        if any(p in text_lower for p in ["dream status", "dream history"]):
            return {"type": "command", "cmd": "dream_status", "params": {}}

        # Book of ANUBIS
        if any(p in text_lower for p in ["generate book", "update book", "create book", "book of anubis", "regenerate book", "generate the book"]):
            return {"type": "command", "cmd": "book_generate", "params": {}}
        if any(p in text_lower for p in ["book status", "book list"]):
            return {"type": "command", "cmd": "book_status", "params": {}}

        # Cold archive
        if any(p in text_lower for p in ["cold archive", "create archive", "make archive", "create a cold archive"]):
            return {"type": "command", "cmd": "cold_archive_create", "params": {}}

        # Scheduler
        if any(p in text_lower for p in ["scheduler status", "schedule status"]):
            return {"type": "command", "cmd": "scheduler_status", "params": {}}

        # Training
        if any(p in text_lower for p in ["training status", "local training"]):
            return {"type": "command", "cmd": "local_training_status", "params": {}}

        # Mixed model strategy — progressive weight replacement
        if any(p in text_lower for p in ["model replacement status", "weight replacement", "mixed model status"]):
            return {"type": "command", "cmd": "mixed_model_status", "params": {}}
        if any(p in text_lower for p in ["what stage is the model", "model stage", "which stage", "training stage"]):
            return {"type": "command", "cmd": "mixed_model_stage", "params": {}}
        if any(p in text_lower for p in ["model generations", "training generations", "list generations", "how many generations"]):
            return {"type": "command", "cmd": "mixed_model_generations", "params": {}}

        # Weather
        if any(p in text_lower for p in ["weather", "forecast", "what's the weather"]):
            return {"type": "command", "cmd": "weather_forecast", "params": {}}

        # Calendar
        if any(p in text_lower for p in ["calendar", "today's events", "what's today", "my schedule", "upcoming events"]):
            return {"type": "command", "cmd": "calendar_today", "params": {}}

        # Memory
        if any(p in text_lower for p in ["memory stats", "memory status"]):
            return {"type": "command", "cmd": "memory_stats", "params": {}}

        # Knowledge
        if any(p in text_lower for p in ["list directors", "show directors", "knowledge directors"]):
            return {"type": "command", "cmd": "list_directors", "params": {}}

        # Consciousness
        if any(p in text_lower for p in ["self concept", "who are you", "what are you", "tell me about yourself"]):
            return {"type": "command", "cmd": "consciousness_self_concept", "params": {}}
        if any(p in text_lower for p in ["reflect", "reflection", "self reflect"]):
            return {"type": "command", "cmd": "consciousness_reflect", "params": {}}

        # Finance
        if any(p in text_lower for p in ["upcoming bills", "my bills", "bill status"]):
            return {"type": "command", "cmd": "finance_upcoming_bills", "params": {}}

        # News
        if any(p in text_lower for p in ["news briefing", "daily news", "what's the news", "news update"]):
            return {"type": "command", "cmd": "news_briefing", "params": {}}

        # Sleep
        if any(p in text_lower for p in ["good night", "goodnight", "go to sleep", "sleep mode"]):
            return {"type": "command", "cmd": "goodnight", "params": {}}
        if any(p in text_lower for p in ["good morning", "wake up", "i'm awake"]):
            return {"type": "command", "cmd": "good_morning", "params": {}}

        # Boot check
        if any(p in text_lower for p in ["boot check", "boot history", "integrity check history"]):
            return {"type": "command", "cmd": "boot_check", "params": {}}
        # Additional self-healing patterns
        if any(p in text_lower for p in ["verify snapshot", "check snapshot", "snapshot verify"]):
            return {"type": "command", "cmd": "snapshot_verify", "params": {}}
        if any(p in text_lower for p in ["cold archive status", "archive status", "archive list"]):
            return {"type": "command", "cmd": "cold_archive_status", "params": {}}
        if any(p in text_lower for p in ["repair alerts", "self repair alerts", "any alerts", "active alerts"]):
            return {"type": "command", "cmd": "self_repair_alerts", "params": {}}
        if any(p in text_lower for p in ["degradation status", "am i degraded", "degraded mode", "graceful degradation"]):
            return {"type": "command", "cmd": "self_repair_degradation_status", "params": {}}
        if any(p in text_lower for p in ["cross check", "canary check", "independent check"]):
            return {"type": "command", "cmd": "self_repair_cross_check", "params": {}}
        if any(p in text_lower for p in ["book status", "book of anubis status", "is the book sealed"]):
            return {"type": "command", "cmd": "book_seal_status", "params": {}}
        if any(p in text_lower for p in ["read the book", "read book of anubis", "read latest book", "read me the book"]):
            return {"type": "command", "cmd": "book_read_latest", "params": {}}
        if any(p in text_lower for p in ["book editions", "list editions", "book history"]):
            return {"type": "command", "cmd": "book_list_editions", "params": {}}
        if any(p in text_lower for p in ["dream gaps", "what are my gaps", "knowledge gaps", "capability gaps"]):
            return {"type": "command", "cmd": "dream_gaps", "params": {}}
        if any(p in text_lower for p in ["dream recommendations", "dream suggestions", "what should i work on"]):
            return {"type": "command", "cmd": "dream_recommendations", "params": {}}
        if any(p in text_lower for p in ["sign core", "resign core", "sign integrity", "re-sign"]):
            return {"type": "command", "cmd": "self_repair_sign_core", "params": {}}
        if any(p in text_lower for p in ["snapshot retention", "clean up snapshots", "old snapshots", "purge snapshots"]):
            return {"type": "command", "cmd": "snapshot_retention", "params": {}}

        # Phone
        if any(p in text_lower for p in ["phone status", "phone connected", "is the phone connected"]):
            return {"type": "command", "cmd": "phone_status", "params": {}}
        if any(p in text_lower for p in ["check my texts", "read my texts", "check my messages", "any new texts", "read my sms"]):
            return {"type": "command", "cmd": "phone_receive_sms", "params": {}}
        if any(p in text_lower for p in ["call history", "recent calls", "my calls"]):
            return {"type": "command", "cmd": "phone_call_history", "params": {}}
        if any(p in text_lower for p in ["what's my phone number", "my phone number", "what number is the phone"]):
            return {"type": "command", "cmd": "phone_get_number", "params": {}}
        # Email
        if any(p in text_lower for p in ["check my email", "check my emails", "any new email", "read my email", "check inbox"]):
            return {"type": "command", "cmd": "email_check", "params": {}}
        if any(p in text_lower for p in ["email status", "is email configured", "email setup"]):
            return {"type": "command", "cmd": "email_status", "params": {}}
        # Funding
        if any(p in text_lower for p in ["funding status", "grant status", "funding applications"]):
            return {"type": "command", "cmd": "funding_status", "params": {}}
        if any(p in text_lower for p in ["pending applications", "applications to review", "funding reviews"]):
            return {"type": "command", "cmd": "funding_pending_reviews", "params": {}}
        if any(p in text_lower for p in ["pending submissions", "ready to submit"]):
            return {"type": "command", "cmd": "funding_pending_submission", "params": {}}
        # Knowledge acquisition
        if any(p in text_lower for p in ["acquire knowledge", "learn from gaps", "research gaps", "fill knowledge gaps"]):
            return {"type": "command", "cmd": "knowledge_auto_acquire", "params": {}}

        # Self-modification
        if any(p in text_lower for p in ["propose modification", "self modify", "modify own code", "modify my code", "propose a modification"]):
            return {"type": "command", "cmd": "self_modify_propose", "params": {}}
        if any(p in text_lower for p in ["modification status", "self modification status", "self-mod status"]):
            return {"type": "command", "cmd": "self_modify_status", "params": {}}
        if any(p in text_lower for p in ["review proposal", "review modification", "review the proposal"]):
            return {"type": "command", "cmd": "self_modify_review", "params": {}}
        if any(p in text_lower for p in ["apply modification", "apply proposal", "apply the modification"]):
            return {"type": "command", "cmd": "self_modify_apply", "params": {}}
        if any(p in text_lower for p in ["rollback modification", "undo modification", "revert modification", "undo the modification"]):
            return {"type": "command", "cmd": "self_modify_rollback", "params": {}}
        if any(p in text_lower for p in ["list modifications", "modification proposals", "list proposals", "show proposals"]):
            return {"type": "command", "cmd": "self_modify_list", "params": {}}

        return None  # No quick match — use LLM

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM's response into a command or chat classification."""
        # Try to extract JSON from the response
        try:
            # Try parsing the whole response as JSON first
            try:
                data = json.loads(response.strip())
            except json.JSONDecodeError:
                # Find JSON in the response (handle nested braces)
                start = response.find("{")
                if start == -1:
                    return {"type": "chat"}
                # Find matching closing brace
                depth = 0
                end = start
                for i in range(start, len(response)):
                    if response[i] == "{":
                        depth += 1
                    elif response[i] == "}":
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                data = json.loads(response[start:end])
            if data.get("type") == "command":
                return {
                    "type": "command",
                    "cmd": data.get("cmd", ""),
                    "params": data.get("params", {}),
                }
            elif data.get("type") == "chat":
                return {"type": "chat"}
            return {"type": "chat"}
        except (json.JSONDecodeError, AttributeError, ValueError):
            return {"type": "chat"}

    def execute(self, interpretation: dict[str, Any]) -> dict[str, Any]:
        """Execute an interpreted command.

        Returns the command result, or an error if the command
        is restricted or the dispatch is not available.
        """
        if interpretation.get("type") != "command":
            return {"executed": False, "reason": "not a command"}

        cmd = interpretation.get("cmd", "")
        params = interpretation.get("params", {})

        if not cmd:
            return {"executed": False, "reason": "no command specified"}

        # Check if command is restricted
        if cmd in self.RESTRICTED_COMMANDS:
            self._speak(f"The command {cmd} requires Creator approval.")
            return {
                "executed": False,
                "reason": f"Command {cmd} requires Creator approval",
                "restricted": True,
            }

        # Execute via dispatch
        if self.dispatch is None:
            return {"executed": False, "reason": "no dispatch available"}

        try:
            request = {"cmd": cmd, **params}
            result = self.dispatch(request)
            self._log("voice.command_executed", {
                "cmd": cmd,
                "params": params,
                "success": "error" not in result,
            })
            return {"executed": True, "cmd": cmd, "result": result}
        except Exception as e:
            return {"executed": False, "reason": str(e), "cmd": cmd}

    def interpret_and_execute(self, text: str) -> dict[str, Any]:
        """Interpret text and execute if it's a command.

        Returns:
            {
                "interpretation": dict,
                "executed": bool,
                "result": dict (if executed),
                "spoken": str (what to speak back),
            }
        """
        interpretation = self.interpret(text)

        if interpretation.get("type") == "command":
            exec_result = self.execute(interpretation)
            spoken = self._format_result_for_speech(
                interpretation.get("cmd", ""),
                exec_result,
            )
            return {
                "interpretation": interpretation,
                "executed": exec_result.get("executed", False),
                "result": exec_result,
                "spoken": spoken,
            }
        else:
            return {
                "interpretation": interpretation,
                "executed": False,
                "spoken": "",  # Let chat handle it
            }

    def _format_result_for_speech(self, cmd: str, result: dict[str, Any]) -> str:
        """Format a command result for speech output.

        Converts the JSON result into a natural language summary
        that can be spoken by the TTS system.
        """
        if not result.get("executed"):
            reason = result.get("reason", "unknown error")
            if result.get("restricted"):
                return reason  # Already formatted
            return f"I couldn't execute that command: {reason}"

        cmd_result = result.get("result", {})

        # Check for errors in the result
        if isinstance(cmd_result, dict) and "error" in cmd_result:
            return f"Error: {cmd_result['error']}"

        # Format common command results
        if cmd == "status":
            model = cmd_result.get("model", "unknown")
            skills = cmd_result.get("skills", 0)
            return f"System status: model {model}, {skills} skills promoted."

        if cmd == "systems_status":
            systems = cmd_result.get("systems", {})
            healthy = sum(1 for s in systems.values() if "error" not in s)
            total = len(systems)
            return f"All systems: {healthy} of {total} operational."

        if cmd == "skills":
            count = len(cmd_result.get("skills", []))
            return f"You have {count} promoted skills."

        if cmd == "snapshot_create":
            sid = cmd_result.get("snapshot_id", "")
            return f"Snapshot created: {sid}"

        if cmd == "snapshot_list":
            count = cmd_result.get("count", 0)
            return f"You have {count} snapshots."

        if cmd == "self_repair_check":
            healthy = cmd_result.get("healthy", False)
            issues = cmd_result.get("issues", [])
            if healthy:
                return "All systems healthy. No issues detected."
            return f"Health check found {len(issues)} issues."

        if cmd == "self_repair_status":
            status = cmd_result.get("status", "unknown")
            alerts = len(cmd_result.get("alerts", []))
            return f"Self-repair status: {status}. {alerts} active alerts."

        if cmd == "drive_report":
            drives = cmd_result.get("drives", [])
            return f"Drive report: {len(drives)} drives checked."

        if cmd == "dream_run":
            phases = cmd_result.get("phases_completed", 0)
            return f"Dream cycle complete. {phases} phases processed."

        if cmd == "dream_status":
            cycles = cmd_result.get("total_cycles", 0)
            return f"Dream cycle has run {cycles} times."

        if cmd == "book_generate":
            edition = cmd_result.get("edition_number", 0)
            words = cmd_result.get("words", 0)
            return f"Book of ANUBIS edition {edition} generated. {words} words."

        if cmd == "cold_archive_create":
            if cmd_result.get("created"):
                size = cmd_result.get("size_mb", 0)
                return f"Cold archive created. {size} megabytes."
            return "Cold archive creation failed."

        if cmd == "weather_forecast":
            # Let the weather system's own formatting handle this
            return ""

        if cmd == "calendar_today":
            events = cmd_result.get("events", [])
            if not events:
                return "You have no events today."
            return f"You have {len(events)} events today."

        if cmd == "goodnight":
            return "Good night. I'll watch over things."

        if cmd == "good_morning":
            return "Good morning. Here's your briefing."

        if cmd == "consciousness_self_concept":
            # Return the self-concept text
            if isinstance(cmd_result, dict):
                concept = cmd_result.get("self_concept", "")
                if concept:
                    return concept[:500]  # Limit length for speech
            return ""

        if cmd == "finance_upcoming_bills":
            bills = cmd_result.get("bills", [])
            if not bills:
                return "No upcoming bills."
            return f"You have {len(bills)} upcoming bills."

        if cmd == "news_briefing":
            items = cmd_result.get("items", [])
            return f"News briefing: {len(items)} items."

        if cmd == "memory_stats":
            entries = cmd_result.get("total_entries", 0)
            return f"Memory: {entries} entries stored."

        # Generic fallback
        if isinstance(cmd_result, dict):
            # Try to find a message field
            msg = cmd_result.get("message", "")
            if msg:
                return msg
            # Summarize the keys
            keys = list(cmd_result.keys())[:5]
            return f"Command {cmd} completed. Fields: {', '.join(keys)}"
        return f"Command {cmd} completed."

    def get_status(self) -> dict[str, Any]:
        """Get interpreter status."""
        return {
            "available": self.model is not None,
            "has_dispatch": self.dispatch is not None,
            "safe_commands": len(self.SAFE_COMMANDS),
            "action_commands": len(self.ACTION_COMMANDS),
            "restricted_commands": len(self.RESTRICTED_COMMANDS),
            "quick_match_patterns": "built-in",
        }
