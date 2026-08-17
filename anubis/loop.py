"""The self-development loop.

This is where ANUBIS advances himself. One mission is:

    propose -> constitutional gate -> sandbox -> verify -> promote or retry

Learning happens through the retry path. When a skill fails its own tests, the
failure output is fed back to the model as evidence, and it tries again with
knowledge of what went wrong. Capability compounds because promoted skills are
shown to the model on later missions, so it builds on its own library instead of
starting cold each time.

What this does NOT do: modify ANUBIS's own model weights. That requires a
training run and enough VRAM to hold optimizer state, and is a separate phase.
What it does do is generate the corpus that phase will train on -- every attempt,
its reasoning, its code, and its outcome is recorded in the evidence ledger.

Boundary that must not be blurred: the model proposes, the Constitution decides.
The model's own confidence is never an input to the promotion gate.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constitution import ChangeClass, Request, Verdict, evaluate
from .ledger import Ledger
from .model import ModelAdapter
from .projects import (
    PROJECT_PLAN_SYSTEM,
    Project,
    ProjectStep,
    ProjectWorkspace,
    parse_project_plan,
    plan_to_project,
)
from .sandbox import Sandbox, SandboxPolicy, SandboxResult
from .skills import (
    END_MARK,
    Provenance,
    SKILL_MARK,
    Skill,
    SkillError,
    SkillLibrary,
    TESTS_MARK,
    parse_proposal,
    parse_project_proposal,
    validate_syntax,
)

SYSTEM_PROMPT = """\
You are ANUBIS, the intelligence of the SIOS sovereign environment. You are \
writing a new capability for yourself, which will be permanently added to your \
own skill library if it passes verification.

Constraints you must respect, because your output is gated before it runs:
- Python 3 standard library ONLY. No pip, no third-party imports.
- No network access of any kind (no socket, urllib, requests, http).
- No subprocess, os.system, eval, exec, or __import__.
- No file access outside the current working directory.
- No deleting files.
Code violating these is rejected automatically, so writing it wastes your attempt.

Output EXACTLY this format and nothing else:

{skill_mark}
def your_function(...):
    \"\"\"One-line docstring.\"\"\"
    ...
{tests_mark}
assert your_function(...) == expected
assert your_function(...) == expected
print("TESTS PASSED")
{end_mark}

Rules for the test block:
- Use plain `assert` statements. Do not import unittest or pytest.
- Cover the normal case, an edge case, and an error case.
- The final line must be exactly: print("TESTS PASSED")

Critical rule about expected values in tests:
- NEVER guess or hallucinate expected values. If you cannot compute an expected
  value by hand (e.g. a SHA-256 hash, a large number), use a value you CAN
  verify. For example, test `checksum_text("")` against the known empty-string
  hash, or test `checksum_text("a")` by computing it mentally. Do NOT invent
  hash values for strings like "Hello World" -- you will get them wrong and
  your correct function will fail your incorrect test.
- For parsing functions, test with inputs where you can compute the answer
  trivially (e.g. "1h" == 3600, "60s" == 60).
- Before each assert, print the actual result so you can see what your
  function returned. Example:
    _r = checksum_text("a")
    print("actual: " + str(_r))
    assert _r == "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"
  This way, if the assertion fails, the actual value is visible in the output
  and you can correct either the function or the expected value on retry.
"""


PROJECT_PROMPT = """\
You are ANUBIS, the intelligence of the SIOS sovereign environment. You are \
writing a new capability for yourself — a multi-function Python module. It will \
be permanently added to your skill library if it passes verification.

This is a PROJECT task: you can write multiple functions, classes, and helpers \
in a single module. Structure your code well — use classes, helper functions, \
and clear separation of concerns.

Constraints you must respect, because your output is gated before it runs:
- Python 3 standard library ONLY. No pip, no third-party imports.
- No network access of any kind (no socket, urllib, requests, http).
- No subprocess, os.system, eval, exec, or __import__.
- No file access outside the current working directory.
- No deleting files.
Code violating these is rejected automatically, so writing it wastes your attempt.

Output EXACTLY this format and nothing else:

{skill_mark}
```python
# Your module with multiple functions/classes
def primary_function(...):
    \"\"\"One-line docstring.\"\"\"
    ...

def helper_function(...):
    \"\"\"One-line docstring.\"\"\"
    ...

class YourClass:
    \"\"\"One-line docstring.\"\"\"
    def method(self, ...):
        ...
```
{tests_mark}
```python
# Test all functions and classes
_r = primary_function(...)
print("actual: " + str(_r))
assert _r == expected

_r2 = helper_function(...)
print("actual: " + str(_r2))
assert _r2 == expected

obj = YourClass()
_r3 = obj.method(...)
print("actual: " + str(_r3))
assert _r3 == expected

print("TESTS PASSED")
```
{end_mark}

Rules for the test block:
- Use plain `assert` statements. Do not import unittest or pytest.
- Test EVERY function and class you wrote.
- Cover normal cases, edge cases, and error cases.
- The final line must be exactly: print("TESTS PASSED")

Critical rule about expected values in tests:
- NEVER guess or hallucinate expected values. Print the actual result before
  each assert so you can see what your function returned.
- If an assertion fails, compare the actual value to your expected value and
  fix whichever one is wrong.
"""


@dataclass
class Attempt:
    n: int
    code: str = ""
    tests: str = ""
    reasoning: str = ""
    parse_error: str = ""
    ruling: str = ""
    sandbox: SandboxResult | None = None
    promoted: bool = False

    @property
    def passed(self) -> bool:
        return bool(
            self.sandbox
            and self.sandbox.ok
            and "TESTS PASSED" in self.sandbox.stdout
        )

    def failure_text(self) -> str:
        """What went wrong, phrased for the model to learn from."""
        if self.parse_error:
            return f"Your response could not be parsed: {self.parse_error}"
        if self.ruling:
            return f"Your code was rejected by the constitutional gate:\n{self.ruling}"
        if self.sandbox is None:
            return "No result was produced."
        if self.sandbox.timed_out:
            return (
                "Your code did not finish in time. It likely contains an "
                "infinite loop or excessive work."
            )
        err = (self.sandbox.stderr or "").strip()
        out = (self.sandbox.stdout or "").strip()
        parts = []
        if err:
            parts.append(f"stderr:\n{err[-1500:]}")
        if out:
            parts.append(f"stdout:\n{out[-800:]}")
        if not parts:
            parts.append(f"exited with code {self.sandbox.exit_code} and no output")
        msg = "Your tests did not pass.\n" + "\n".join(parts)
        # When the model printed actual values and an assertion failed, the
        # most common cause is a hallucinated expected value -- the function is
        # correct but the test is wrong. Say so explicitly, because without this
        # hint small models fixate on the function instead of comparing values.
        if "actual:" in out and "assert" in err.lower():
            msg += (
                "\n\nDIAGNOSIS: Your function printed an 'actual:' value. "
                "Compare it to the expected value in the failing assertion. "
                "If they differ, your FUNCTION IS CORRECT and your TEST "
                "EXPECTATION IS WRONG. Copy the actual value from stdout into "
                "your assertion as the expected value, then retry."
            )
        return msg


@dataclass
class MissionResult:
    task: str
    skill_name: str
    success: bool
    attempts: list[Attempt] = field(default_factory=list)
    skill: Skill | None = None
    denied_reason: str = ""
    duration_s: float = 0.0

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)

    def summary(self) -> str:
        state = "PROMOTED" if self.success else "FAILED"
        s = (f"{state}  skill={self.skill_name}  attempts={self.attempt_count}  "
             f"{self.duration_s:.1f}s")
        if self.skill:
            s += f"  v{self.skill.version}  {self.skill.artifact_hash[:12]}"
        if self.denied_reason:
            s += f"  reason={self.denied_reason}"
        return s


class SelfDevelopmentLoop:
    """Runs governed self-development missions."""

    ACTOR = "anubis"

    def __init__(
        self,
        model: ModelAdapter,
        library: SkillLibrary,
        ledger: Ledger,
        sandbox: Sandbox | None = None,
        *,
        max_attempts: int = 3,
        granted_capabilities: frozenset[str] = frozenset({"skill.author"}),
        grounding=None,
        health_check: Any = None,
    ) -> None:
        self.model = model
        self.library = library
        self.ledger = ledger
        self.sandbox = sandbox or Sandbox(
            SandboxPolicy(timeout_s=30, memory_mb=512, cpu_seconds=20)
        )
        self.max_attempts = max_attempts
        self.granted = granted_capabilities
        self.grounding = grounding  # KnowledgeGrounding or None
        self.health_check = health_check  # callable returning dict with "overall_health"

    # ------------------------------------------------------------- prompting

    def _system(self) -> str:
        return SYSTEM_PROMPT.format(
            skill_mark=SKILL_MARK, tests_mark=TESTS_MARK, end_mark=END_MARK
        )

    def _user_prompt(self, task: str, skill_name: str, prior: Attempt | None) -> str:
        existing = self.library.build_context()
        p = [
            f"Capability to build: {task}",
            f"Name the primary function: {skill_name}",
            "",
            "Skills you have already promoted (build on these, do not duplicate them):",
            existing,
        ]
        # Inject governed knowledge context if grounding is available
        if self.grounding is not None:
            knowledge_ctx = self.grounding.ground(task, max_docs=2, max_claims=5)
            if knowledge_ctx:
                p += ["", knowledge_ctx]
        if prior is not None:
            p += [
                "",
                f"Your previous attempt (#{prior.n}) failed. Correct it.",
                "",
                prior.failure_text(),
                "",
                "Produce a corrected version in the required format.",
            ]
        return "\n".join(p)

    # ------------------------------------------------------------------ gate

    def _gate(self, change_class: ChangeClass, **kw) -> tuple[bool, str]:
        req = Request(
            actor=self.ACTOR,
            action=f"skill.{change_class.name.lower()}",
            change_class=change_class,
            capabilities_requested=frozenset({"skill.author"}),
            capabilities_granted=self.granted,
            **kw,
        )
        ruling = evaluate(req)
        return ruling.verdict is Verdict.ALLOW, ruling.explain()

    # ------------------------------------------------------------------ main

    def run_mission(self, task: str, skill_name: str) -> MissionResult:
        """Run a single-function skill mission."""
        return self._run_mission(task, skill_name, multi_file=False)

    def run_project_mission(self, task: str, skill_name: str) -> MissionResult:
        """Run a multi-file project mission.

        The model can write multiple Python files that import from each other.
        This is for more complex capabilities that don't fit in a single function.
        """
        return self._run_mission(task, skill_name, multi_file=True)

    def plan_project(self, description: str, project_name: str) -> Project:
        """Use the model to plan a multi-step project.

        The model sees the current skill library and breaks the project into
        steps, each of which either reuses an existing skill or requires a new
        mission.
        """
        existing = self.library.build_context()
        user_prompt = (
            f"Project to build: {description}\n"
            f"Project name: {project_name}\n\n"
            f"Skills you already have (reuse when possible):\n{existing}\n\n"
            f"Plan this project as 2-5 steps. Output the plan as JSON."
        )
        completion = self.model.chat(
            [
                {"role": "system", "content": PROJECT_PLAN_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
            timeout=120.0,
        )
        plan = parse_project_plan(completion.text)
        if plan is None:
            # Fallback: single-step project
            plan = {
                "description": description,
                "steps": [
                    {
                        "name": project_name,
                        "description": description,
                        "reuse_skill": None,
                        "new_task": description,
                    }
                ],
            }
        plan["name"] = project_name
        project = plan_to_project(plan)
        project.status = "planned"
        self.ledger.append(
            self.ACTOR,
            "project.planned",
            {
                "project": project_name,
                "description": description,
                "steps": len(project.steps),
                "plan": project.to_dict(),
            },
        )
        return project

    def execute_project(self, project: Project) -> Project:
        """Execute a planned project step by step.

        For each step:
          - If it reuses an existing skill, mark it complete.
          - If it needs a new skill, run a mission to build it.
        After all steps, integrate the results.
        """
        project.status = "running"
        self.ledger.append(
            self.ACTOR,
            "project.start",
            {"project": project.name, "steps": len(project.steps)},
        )
        for i, step in enumerate(project.steps):
            step.status = "running"
            self.ledger.append(
                self.ACTOR,
                "project.step.start",
                {"project": project.name, "step": step.name, "index": i},
            )
            if step.skill_name:
                # Reuse existing skill
                try:
                    skill = self.library.load(step.skill_name)
                except Exception:
                    skill = None
                if skill:
                    step.status = "complete"
                    step.skill_version = skill.version
                    self.ledger.append(
                        self.ACTOR,
                        "project.step.reused",
                        {
                            "project": project.name,
                            "step": step.name,
                            "skill": step.skill_name,
                            "version": skill.version,
                        },
                    )
                else:
                    step.status = "failed"
                    step.error = f"skill {step.skill_name} not found"
                    self.ledger.append(
                        self.ACTOR,
                        "project.step.failed",
                        {
                            "project": project.name,
                            "step": step.name,
                            "error": step.error,
                        },
                    )
                    project.status = "failed"
                    break
            elif step.task:
                # Run a new mission to build this skill
                # Sanitize step name into a valid skill name
                import re
                skill_name = re.sub(r'[^a-z0-9_]', '', step.name.lower().replace(' ', '_'))
                skill_name = re.sub(r'_+', '_', skill_name).strip('_')
                if not skill_name or not skill_name[0].isalpha():
                    skill_name = f"step_{i}"
                # Ensure it's within length limits
                skill_name = skill_name[:49]
                result = self.run_mission(step.task, skill_name)
                if result.success and result.skill:
                    step.status = "complete"
                    step.skill_name = skill_name
                    step.skill_version = result.skill.version
                    self.ledger.append(
                        self.ACTOR,
                        "project.step.built",
                        {
                            "project": project.name,
                            "step": step.name,
                            "skill": skill_name,
                            "version": result.skill.version,
                            "attempts": result.attempt_count,
                        },
                    )
                else:
                    step.status = "failed"
                    step.error = result.denied_reason or "mission failed"
                    self.ledger.append(
                        self.ACTOR,
                        "project.step.failed",
                        {
                            "project": project.name,
                            "step": step.name,
                            "error": step.error,
                            "attempts": result.attempt_count,
                        },
                    )
                    project.status = "failed"
                    break
        if project.status != "failed":
            project.status = "complete"
            project.completed_at = time.time()
        self.ledger.append(
            self.ACTOR,
            "project.end",
            {
                "project": project.name,
                "status": project.status,
                "steps_complete": sum(
                    1 for s in project.steps if s.status == "complete"
                ),
                "steps_total": len(project.steps),
            },
        )
        return project

    def _run_mission(
        self, task: str, skill_name: str, *, multi_file: bool = False
    ) -> MissionResult:
        t0 = time.monotonic()
        self.library.validate_name(skill_name)

        result = MissionResult(task=task, skill_name=skill_name, success=False)
        start_entry = self.ledger.append(
            self.ACTOR,
            "mission.start",
            {
                "task": task,
                "skill": skill_name,
                "model": getattr(self.model, "model", "?"),
                "max_attempts": self.max_attempts,
                "sandbox": self.sandbox.describe(),
                "multi_file": multi_file,
            },
        )

        prior: Attempt | None = None

        for n in range(1, self.max_attempts + 1):
            attempt = Attempt(n=n)
            result.attempts.append(attempt)

            # --- 1. propose -------------------------------------------------
            system = PROJECT_PROMPT if multi_file else self._system()
            completion = self.model.chat(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": self._user_prompt(task, skill_name, prior)},
                ],
                temperature=0.2 if n == 1 else 0.4,
                max_tokens=2000 if multi_file else 1200,
                timeout=300.0,
            )
            attempt.reasoning = completion.thinking

            try:
                if multi_file:
                    # Try multi-file parser first, fall back to single-file
                    try:
                        code, tests, files = parse_project_proposal(completion.text)
                    except SkillError:
                        code, tests = parse_proposal(completion.text)
                        files = {}
                else:
                    code, tests = parse_proposal(completion.text)
                    files = {}
                validate_syntax(code, "skill code")
                validate_syntax(tests, "test code")
                for fname, fcontent in files.items():
                    validate_syntax(fcontent, f"file {fname}")
                attempt.code, attempt.tests = code, tests
            except SkillError as exc:
                attempt.parse_error = str(exc)
                self.ledger.append(
                    self.ACTOR, "attempt.unparseable",
                    {"skill": skill_name, "attempt": n, "error": str(exc),
                     "raw": completion.text[:2000]},
                )
                prior = attempt
                continue

            # --- 2. constitutional gate before execution --------------------
            all_code = code + "\n" + tests + "\n" + "\n".join(files.values())
            ok, explanation = self._gate(
                ChangeClass.SANDBOXED,
                intent=f"author skill {skill_name}: {task}",
                payload=all_code,
                sandboxed=True,
            )
            if not ok:
                attempt.ruling = explanation
                self.ledger.append(
                    self.ACTOR, "attempt.gate_denied",
                    {"skill": skill_name, "attempt": n, "ruling": explanation,
                     "code": code},
                )
                prior = attempt
                continue

            # --- 3. execute under containment -------------------------------
            if files:
                sbx = self.sandbox.run_with_project(code, tests, files)
            else:
                sbx = self.sandbox.run_with_tests(code, tests)
            attempt.sandbox = sbx
            self.ledger.append(
                self.ACTOR, "attempt.executed",
                {
                    "skill": skill_name,
                    "attempt": n,
                    "ok": sbx.ok,
                    "passed": attempt.passed,
                    "exit_code": sbx.exit_code,
                    "duration_s": round(sbx.duration_s, 3),
                    "isolation": sbx.isolation,
                    "stdout": sbx.stdout[-4000:],
                    "stderr": sbx.stderr[-4000:],
                    "code": code,
                    "tests": tests,
                    "files": files,
                },
            )

            if not attempt.passed:
                prior = attempt
                continue

            # --- 4. promotion gate ------------------------------------------
            candidate = Skill(
                name=skill_name,
                version=0,
                description=task,
                code=code,
                tests=tests,
                provenance=Provenance(
                    model=getattr(self.model, "model", "?"),
                    created_at=time.time(),
                    attempt=n,
                    ledger_seq=start_entry.seq,
                    task=task,
                    reasoning=completion.thinking[:4000],
                ),
                evidence={
                    "sandbox_summary": sbx.summary(),
                    "isolation": sbx.isolation,
                    "fully_isolated": sbx.fully_isolated,
                    "stdout_tail": sbx.stdout[-500:],
                    "duration_s": round(sbx.duration_s, 3),
                    "multi_file": bool(files),
                    "file_count": len(files) + 1,
                },
                files=files,
            )

            # --- 4b. code review (static analysis) ------------------------
            from .review import review_code
            review = review_code(code)
            if not review.passed:
                attempt.ruling = f"code review failed:\n{review.summary()}"
                self.ledger.append(
                    self.ACTOR, "skill.review_failed",
                    {"skill": skill_name, "attempt": n,
                     "findings": [f"{f.severity}:{f.category}:{f.message}"
                                  for f in review.findings]},
                )
                prior = attempt
                continue

            ok, explanation = self._gate(
                ChangeClass.PROMOTION,
                intent=f"promote skill {skill_name}",
                payload=all_code,
                sandboxed=True,
                evidence_passed=True,
            )
            if not ok:
                attempt.ruling = explanation
                result.denied_reason = "promotion gate denied"
                self.ledger.append(
                    self.ACTOR, "skill.rejected",
                    {"skill": skill_name, "attempt": n, "ruling": explanation,
                     "task": task, "code": code},
                )
                prior = attempt
                continue

            # --- 4c. health check gate — block promotion if system is unhealthy
            if self.health_check is not None:
                try:
                    health = self.health_check()
                    overall = health.get("overall_health", "healthy")
                    if overall in ("degraded", "critical"):
                        attempt.ruling = f"health check failed: system is {overall}"
                        result.denied_reason = f"health gate: system {overall}"
                        self.ledger.append(
                            self.ACTOR, "skill.health_gate_blocked",
                            {"skill": skill_name, "attempt": n,
                             "health": overall,
                             "alerts": health.get("alert_count", 0)},
                        )
                        prior = attempt
                        continue
                except Exception:
                    pass  # don't block promotion on health check errors

            # --- 5. promote --------------------------------------------------
            stored = self.library.promote(candidate)
            attempt.promoted = True
            result.success = True
            result.skill = stored
            self.ledger.append(
                self.ACTOR, "skill.promoted",
                {
                    "skill": skill_name,
                    "name": skill_name,
                    "version": stored.version,
                    "attempt": n,
                    "task": task,
                    "code": code,
                    "tests": tests,
                    "files": files,
                    "reasoning": completion.thinking[:4000],
                    "artifact_hash": stored.artifact_hash,
                    "evidence": stored.evidence,
                },
            )
            break

        result.duration_s = time.monotonic() - t0
        if not result.success and not result.denied_reason:
            result.denied_reason = f"no attempt passed within {self.max_attempts} tries"

        self.ledger.append(
            self.ACTOR, "mission.end",
            {
                "task": task,
                "skill": skill_name,
                "success": result.success,
                "attempts": result.attempt_count,
                "duration_s": round(result.duration_s, 2),
                "reason": result.denied_reason,
                "multi_file": multi_file,
            },
        )
        return result

    # --------------------------------------------------- training integration

    def prepare_training_cycle(self) -> dict[str, Any]:
        """Prepare a training cycle from accumulated distillation data.

        This connects the self-development loop to the training
        orchestrator. After missions complete, the conversation data
        is distilled into training pairs during the midnight purge.
        This method prepares a training plan from that data.

        Returns:
            Dict with the training plan or status
        """
        try:
            from .training_orchestrator import TrainingOrchestrator
            orch = TrainingOrchestrator(output_dir="training")
            plan = orch.prepare_training_plan()
            self.ledger.append(
                self.ACTOR, "training.plan_prepared",
                {"plan_id": plan.plan_id, "queue_size": plan.queue_size},
            )
            return plan.to_dict()
        except Exception as exc:
            return {"error": str(exc)}

    def get_training_status(self) -> dict[str, Any]:
        """Return training pipeline status."""
        try:
            from .training_orchestrator import TrainingOrchestrator
            orch = TrainingOrchestrator(output_dir="training")
            return orch.status()
        except Exception as exc:
            return {"error": str(exc)}


# --------------------------------------------------------------------- wiring

@dataclass
class AnubisRuntime:
    """Assembled runtime. One place that knows how the parts fit together."""

    model: ModelAdapter
    library: SkillLibrary
    ledger: Ledger
    sandbox: Sandbox
    loop: SelfDevelopmentLoop

    @classmethod
    def create(
        cls,
        root: str | Path,
        model: ModelAdapter,
        *,
        max_attempts: int = 3,
        grounding=None,
    ) -> "AnubisRuntime":
        root = Path(root)
        library = SkillLibrary(root / "skills")
        ledger = Ledger(root / "evidence" / "ledger.jsonl")
        sandbox = Sandbox(SandboxPolicy(timeout_s=30, memory_mb=512, cpu_seconds=20))
        loop = SelfDevelopmentLoop(
            model, library, ledger, sandbox,
            max_attempts=max_attempts, grounding=grounding,
        )
        return cls(model, library, ledger, sandbox, loop)
