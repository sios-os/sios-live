"""Structured JSON outputs from the cloud teacher.

Forces the cloud teacher to return information in a strict JSON schema,
making its output machine-parseable for the self-development loop.

When the system queries the online model for code generation, architectural
blueprints, or kernel design concepts, the response is structured into:
- code: The actual code block
- rationale: Why this approach was chosen
- tests: Unit test parameters
- dependencies: Required libraries/modules
- risks: Potential issues to watch for

This eliminates the need for fragile text parsing and ensures the
self-development loop can directly use the teacher's output.

Features:
- Predefined schemas for common query types (code, architecture, review)
- Custom schema support
- JSON validation and repair (handles common LLM formatting issues)
- Privacy-gated (sensitive data stays local)
- Fallback to unstructured output if JSON parsing fails
- Evidence ledger logging

Uses only the Python standard library (json, re).
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

from .cloud_model import CloudModelAdapter, Completion, _check_sensitive_data
from .ledger import Ledger


# Predefined schemas for common query types
SCHEMAS: dict[str, dict[str, Any]] = {
    "code": {
        "code": "string — the generated code",
        "language": "string — programming language",
        "rationale": "string — why this approach was chosen",
        "tests": "array of strings — unit test descriptions",
        "dependencies": "array of strings — required libraries/modules",
        "risks": "array of strings — potential issues",
    },
    "architecture": {
        "components": "array of {name, description, interfaces}",
        "data_flow": "string — how data moves through the system",
        "rationale": "string — architectural reasoning",
        "scalability": "string — how to scale this design",
        "risks": "array of strings — potential issues",
    },
    "review": {
        "issues": "array of {severity, description, location, fix}",
        "summary": "string — overall assessment",
        "score": "number — quality score 0-10",
        "recommendations": "array of strings — improvement suggestions",
    },
    "analysis": {
        "findings": "array of strings — key findings",
        "conclusion": "string — overall conclusion",
        "confidence": "number — confidence 0-1",
        "evidence": "array of strings — supporting evidence",
    },
    "plan": {
        "steps": "array of {order, action, rationale, estimated_time}",
        "prerequisites": "array of strings — what must be done first",
        "risks": "array of strings — potential issues",
        "success_criteria": "string — how to know it worked",
    },
}


@dataclass
class StructuredResult:
    """Result of a structured query to the cloud teacher."""
    ok: bool
    schema_type: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    provider: str = ""
    duration_s: float = 0.0
    error: str = ""
    used_fallback: bool = False

    @property
    def code(self) -> str:
        return self.data.get("code", "")

    @property
    def rationale(self) -> str:
        return self.data.get("rationale", "")

    @property
    def tests(self) -> list[str]:
        return self.data.get("tests", [])

    @property
    def dependencies(self) -> list[str]:
        return self.data.get("dependencies", [])

    @property
    def risks(self) -> list[str]:
        return self.data.get("risks", [])


def _extract_json(text: str) -> str | None:
    """Extract a JSON object or array from text.

    Handles common LLM formatting issues:
    - JSON wrapped in markdown code blocks
    - JSON with leading/trailing text
    - JSON with trailing commas
    """
    # Try to find JSON in markdown code blocks first
    md_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if md_match:
        return _repair_json(md_match.group(1))

    # Try to find a JSON object
    # Find the first { and matching }
    start = text.find("{")
    if start == -1:
        # Try array
        start = text.find("[")
        if start == -1:
            return None
        end = text.rfind("]")
    else:
        end = text.rfind("}")

    if end == -1 or end <= start:
        return None

    return _repair_json(text[start:end + 1])


def _repair_json(text: str) -> str:
    """Attempt to repair common JSON issues from LLM output."""
    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)
    # Remove comments (// and /* */)
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _build_schema_prompt(
    query: str, schema: dict[str, Any], schema_type: str
) -> str:
    """Build a prompt that requests structured JSON output."""
    schema_desc = json.dumps(schema, indent=2, ensure_ascii=False)
    return f"""You are a structured output assistant. Respond with ONLY a JSON object.

Query: {query}

Respond with a JSON object matching this schema (field names must match exactly):
{schema_desc}

Rules:
1. Output ONLY valid JSON — no markdown, no explanations outside the JSON
2. All string values must be properly escaped
3. Arrays must contain valid objects or strings
4. Do not include any fields not in the schema

JSON response:
"""


class StructuredTeacher:
    """Query the cloud teacher with structured JSON output.

    Wraps the CloudModelAdapter to force structured JSON responses.
    Falls back to unstructured output if JSON parsing fails.
    """

    def __init__(
        self,
        cloud_adapter: CloudModelAdapter | None = None,
        ledger: Ledger | None = None,
    ) -> None:
        self.cloud = cloud_adapter
        self.ledger = ledger

    def query(
        self,
        prompt: str,
        *,
        schema_type: str = "code",
        custom_schema: dict[str, Any] | None = None,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int | None = None,
    ) -> StructuredResult:
        """Query the cloud teacher with a structured prompt.

        Args:
            prompt: The user's query
            schema_type: Predefined schema type ("code", "architecture",
                        "review", "analysis", "plan")
            custom_schema: Custom schema (overrides schema_type)
            system: Optional system prompt
            temperature: Lower = more deterministic
            max_tokens: Max response tokens

        Returns:
            StructuredResult with parsed JSON data
        """
        t0 = time.monotonic()

        # Select schema
        if custom_schema:
            schema = custom_schema
        else:
            schema = SCHEMAS.get(schema_type, SCHEMAS["code"])

        # Privacy check
        if _check_sensitive_data(prompt):
            return StructuredResult(
                ok=False,
                schema_type=schema_type,
                error="sensitive data detected — query blocked from cloud",
                duration_s=round(time.monotonic() - t0, 3),
            )

        # No cloud adapter
        if self.cloud is None:
            return StructuredResult(
                ok=False,
                schema_type=schema_type,
                error="no cloud adapter configured",
                duration_s=round(time.monotonic() - t0, 3),
            )

        # Build structured prompt
        structured_prompt = _build_schema_prompt(prompt, schema, schema_type)
        full_system = system or "You are a structured JSON output assistant."

        # Query the cloud teacher
        try:
            completion = self.cloud.generate(
                structured_prompt,
                system=full_system,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            return StructuredResult(
                ok=False,
                schema_type=schema_type,
                error=f"cloud query failed: {exc}",
                duration_s=round(time.monotonic() - t0, 3),
            )

        raw_text = completion.text
        provider = completion.model.split(":")[0] if ":" in completion.model else completion.model

        # Try to parse JSON
        json_str = _extract_json(raw_text)
        if json_str:
            try:
                data = json.loads(json_str)
                result = StructuredResult(
                    ok=True,
                    schema_type=schema_type,
                    data=data,
                    raw_text=raw_text,
                    provider=provider,
                    duration_s=round(time.monotonic() - t0, 3),
                )
                if self.ledger:
                    self.ledger.append({
                        "event": "structured_query",
                        "schema_type": schema_type,
                        "provider": provider,
                        "success": True,
                    })
                return result
            except json.JSONDecodeError:
                pass

        # JSON parsing failed — return raw text as fallback
        result = StructuredResult(
            ok=True,
            schema_type=schema_type,
            data={"raw_response": raw_text},
            raw_text=raw_text,
            provider=provider,
            duration_s=round(time.monotonic() - t0, 3),
            used_fallback=True,
        )
        if self.ledger:
            self.ledger.append({
                "event": "structured_query",
                "schema_type": schema_type,
                "provider": provider,
                "success": True,
                "fallback": True,
            })
        return result

    def query_code(self, prompt: str, **kwargs: Any) -> StructuredResult:
        """Query for code generation (uses 'code' schema)."""
        return self.query(prompt, schema_type="code", **kwargs)

    def query_architecture(self, prompt: str, **kwargs: Any) -> StructuredResult:
        """Query for architectural design (uses 'architecture' schema)."""
        return self.query(prompt, schema_type="architecture", **kwargs)

    def query_review(self, prompt: str, **kwargs: Any) -> StructuredResult:
        """Query for code review (uses 'review' schema)."""
        return self.query(prompt, schema_type="review", **kwargs)

    def query_analysis(self, prompt: str, **kwargs: Any) -> StructuredResult:
        """Query for analysis (uses 'analysis' schema)."""
        return self.query(prompt, schema_type="analysis", **kwargs)

    def query_plan(self, prompt: str, **kwargs: Any) -> StructuredResult:
        """Query for a plan (uses 'plan' schema)."""
        return self.query(prompt, schema_type="plan", **kwargs)

    def available_schemas(self) -> dict[str, dict[str, Any]]:
        """Return all available predefined schemas."""
        return SCHEMAS.copy()

    def status(self) -> dict[str, Any]:
        """Return structured teacher status."""
        return {
            "cloud_configured": self.cloud is not None and self.cloud.is_configured,
            "schemas": list(SCHEMAS.keys()),
            "privacy_gate": True,
        }
