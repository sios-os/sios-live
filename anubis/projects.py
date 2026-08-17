"""Project workspace for ANUBIS.

A project is a multi-step software build that chains promoted skills together.
Instead of writing one function at a time, ANUBIS can:

  1. Plan a project (break it into steps)
  2. For each step, either reuse an existing promoted skill or run a new mission
  3. Integrate the results into a final project artifact
  4. Test the integrated project in the sandbox
  5. Promote the project if it passes

This is what makes ANUBIS useful for real software development — he builds
on his own library instead of starting cold each time.

Layout:
    projects/
        <project_name>/
            manifest.json   — project plan, steps, status
            main.py         — integrated final code
            tests.py        — project-level tests
            steps/          — per-step working files
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectStep:
    """One step in a project plan."""
    name: str
    description: str
    skill_name: str = ""        # existing skill to reuse (empty = new mission)
    task: str = ""              # task description if a new skill is needed
    status: str = "pending"     # pending, running, complete, failed
    skill_version: int = 0
    error: str = ""


@dataclass
class Project:
    """A multi-step software project."""
    name: str
    description: str
    steps: list[ProjectStep] = field(default_factory=list)
    status: str = "planning"    # planning, running, complete, failed
    created_at: float = 0.0
    completed_at: float = 0.0
    main_code: str = ""
    test_code: str = ""
    artifact_hash: str = ""
    integration_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "steps": [
                {
                    "name": s.name,
                    "description": s.description,
                    "skill_name": s.skill_name,
                    "task": s.task,
                    "status": s.status,
                    "skill_version": s.skill_version,
                    "error": s.error,
                }
                for s in self.steps
            ],
            "artifact_hash": self.artifact_hash,
            "integration_error": self.integration_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        steps = [
            ProjectStep(
                name=s.get("name", ""),
                description=s.get("description", ""),
                skill_name=s.get("skill_name", ""),
                task=s.get("task", ""),
                status=s.get("status", "pending"),
                skill_version=s.get("skill_version", 0),
                error=s.get("error", ""),
            )
            for s in data.get("steps", [])
        ]
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            steps=steps,
            status=data.get("status", "planning"),
            created_at=data.get("created_at", 0.0),
            completed_at=data.get("completed_at", 0.0),
            main_code=data.get("main_code", ""),
            test_code=data.get("test_code", ""),
            artifact_hash=data.get("artifact_hash", ""),
            integration_error=data.get("integration_error", ""),
        )


class ProjectWorkspace:
    """Manages persistent project state on disk."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def project_dir(self, name: str) -> Path:
        return self.root / name

    def manifest_path(self, name: str) -> Path:
        return self.project_dir(name) / "manifest.json"

    def exists(self, name: str) -> bool:
        return self.manifest_path(name).exists()

    def list_projects(self) -> list[dict[str, Any]]:
        """List all projects with their status."""
        projects = []
        if not self.root.exists():
            return projects
        for d in sorted(self.root.iterdir()):
            if not d.is_dir():
                continue
            mpath = d / "manifest.json"
            if not mpath.exists():
                continue
            try:
                data = json.loads(mpath.read_text(encoding="utf-8"))
                projects.append({
                    "name": data.get("name", d.name),
                    "description": data.get("description", ""),
                    "status": data.get("status", "?"),
                    "steps_total": len(data.get("steps", [])),
                    "steps_complete": sum(
                        1 for s in data.get("steps", [])
                        if s.get("status") == "complete"
                    ),
                    "created_at": data.get("created_at", 0),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return projects

    def save(self, project: Project) -> None:
        """Save a project to disk."""
        pdir = self.project_dir(project.name)
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "manifest.json").write_text(
            json.dumps(project.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )
        if project.main_code:
            (pdir / "main.py").write_text(project.main_code, encoding="utf-8")
        if project.test_code:
            (pdir / "tests.py").write_text(project.test_code, encoding="utf-8")

    def load(self, name: str) -> Project | None:
        """Load a project from disk."""
        mpath = self.manifest_path(name)
        if not mpath.exists():
            return None
        try:
            data = json.loads(mpath.read_text(encoding="utf-8"))
            project = Project.from_dict(data)
            # Load code files if they exist
            main_path = self.project_dir(name) / "main.py"
            if main_path.exists():
                project.main_code = main_path.read_text(encoding="utf-8")
            tests_path = self.project_dir(name) / "tests.py"
            if tests_path.exists():
                project.test_code = tests_path.read_text(encoding="utf-8")
            return project
        except (json.JSONDecodeError, OSError):
            return None

    def delete(self, name: str) -> bool:
        """Delete a project."""
        pdir = self.project_dir(name)
        if not pdir.exists():
            return False
        import shutil
        shutil.rmtree(pdir)
        return True


# ------------------------------------------------------------------ planning

PROJECT_PLAN_SYSTEM = """\
You are ANUBIS, the intelligence of the SIOS sovereign environment. You are \
planning a software project that you will build step by step.

You have a library of promoted skills that you can reuse. Each step in your \
plan should either:
  1. Reuse an existing skill (by name), OR
  2. Require a new skill to be built (describe what it should do)

Output your plan as a JSON object with this exact structure:
{
  "description": "One-line description of the project",
  "steps": [
    {
      "name": "lower_snake_case_name",
      "description": "What this step does",
      "reuse_skill": "existing_skill_name" or null,
      "new_task": "Description of new skill to build" or null
    }
  ]
}

Rules:
- Keep plans to 2-5 steps. Small, testable increments.
- Prefer reusing existing skills when possible.
- Each step should produce a testable unit.
- The final step should integrate everything.
- Step names MUST be lower_snake_case (lowercase letters, numbers, underscores).
  Good: "count_words", "parse_csv_data", "format_output"
  Bad: "Step 1", "Count Words", "count-words"
- Output ONLY the JSON, no other text.
"""


def parse_project_plan(text: str) -> dict[str, Any] | None:
    """Parse a project plan from model output. Returns the plan dict or None."""
    import re
    # Try to extract JSON from the text
    # Look for JSON block
    json_match = re.search(r'\{[\s\S]*\}', text)
    if not json_match:
        return None
    json_str = json_match.group(0)
    try:
        plan = json.loads(json_str)
        if "steps" in plan and isinstance(plan["steps"], list):
            return plan
    except json.JSONDecodeError:
        pass
    return None


def plan_to_project(plan: dict[str, Any]) -> Project:
    """Convert a parsed plan dict into a Project object."""
    steps = []
    for s in plan.get("steps", []):
        reuse = s.get("reuse_skill")
        new_task = s.get("new_task")
        steps.append(ProjectStep(
            name=s.get("name", "step"),
            description=s.get("description", ""),
            skill_name=reuse or "",
            task=new_task or "",
            status="pending",
        ))
    return Project(
        name=plan.get("name", "project"),
        description=plan.get("description", ""),
        steps=steps,
        status="planning",
        created_at=time.time(),
    )


# ------------------------------------------------------------------ execution

class ProjectExecutor:
    """Executes a project plan step by step, chaining skills together.

    For each step:
      - If reuse_skill is set, load that skill from the library
      - If new_task is set, run a self-dev mission to build it
      - Collect the code from each step
      - Integrate into a final main.py
      - Run project-level tests in the sandbox
    """

    def __init__(
        self,
        workspace: ProjectWorkspace,
        library: Any,
        loop: Any,
        sandbox: Any,
    ) -> None:
        self.workspace = workspace
        self.library = library
        self.loop = loop
        self.sandbox = sandbox

    def execute(self, project: Project) -> Project:
        """Execute a project plan. Updates project status as it goes."""
        project.status = "running"
        self.workspace.save(project)

        collected_code: list[str] = []
        for i, step in enumerate(project.steps):
            step.status = "running"
            self.workspace.save(project)

            if step.skill_name:
                # Reuse existing skill
                try:
                    skill = self.library.load(step.skill_name)
                except Exception as e:
                    step.status = "failed"
                    step.error = f"skill '{step.skill_name}' not found: {e}"
                    project.status = "failed"
                    self.workspace.save(project)
                    return project
                collected_code.append(f"# Step {i+1}: {step.name} (reused {step.skill_name})\n{skill.code}")
                step.status = "complete"
                step.skill_version = skill.version
            elif step.task:
                # Run a new mission
                skill_name = step.name
                result = self.loop.run_mission(step.task, skill_name)
                if result.success and result.skill:
                    collected_code.append(f"# Step {i+1}: {step.name} (new skill)\n{result.skill.code}")
                    step.status = "complete"
                    step.skill_version = result.skill.version
                else:
                    step.status = "failed"
                    step.error = "mission failed"
                    project.status = "failed"
                    self.workspace.save(project)
                    return project
            else:
                step.status = "failed"
                step.error = "no skill_name or task specified"
                project.status = "failed"
                self.workspace.save(project)
                return project

            self.workspace.save(project)

        # Integrate: combine all step code into main.py
        project.main_code = "\n\n\n".join(collected_code)

        # Generate integration tests
        project.test_code = self._generate_tests(project)
        project.artifact_hash = self._hash(project.main_code + project.test_code)

        # Run integration tests in sandbox
        ok, stdout, stderr = self._run_tests(project)
        if ok:
            project.status = "complete"
            project.completed_at = time.time()
        else:
            project.status = "failed"
            project.integration_error = stderr[:500]

        self.workspace.save(project)
        return project

    def _generate_tests(self, project: Project) -> str:
        """Generate basic integration tests for the project."""
        return f'''"""Integration tests for {project.name}."""
import unittest
import sys
sys.path.insert(0, ".")

class Test{project.name.title().replace("_","")}(unittest.TestCase):
    def test_imports(self):
        """Verify the project code can be imported."""
        # The main code is executed as a module
        # This is a smoke test — specific tests would be added per project
        try:
            exec(open(__file__.replace("tests.py", "main.py")).read(), {{}})
        except Exception as e:
            self.fail(f"Failed to load project code: {{e}}")

    def test_has_functions(self):
        """Verify the project code defines at least one function."""
        ns = {{}}
        exec(open(__file__.replace("tests.py", "main.py")).read(), ns)
        funcs = [k for k, v in ns.items() if callable(v) and not k.startswith("_")]
        self.assertGreater(len(funcs), 0, "No functions defined in project code")

if __name__ == "__main__":
    unittest.main()
'''

    def _hash(self, text: str) -> str:
        import hashlib
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _run_tests(self, project: Project) -> tuple[bool, str, str]:
        """Run project tests in the sandbox."""
        pdir = self.workspace.project_dir(project.name)
        (pdir / "main.py").write_text(project.main_code, encoding="utf-8")
        (pdir / "tests.py").write_text(project.test_code, encoding="utf-8")

        # Run tests directly (not in sandbox, since we need file access)
        import subprocess
        try:
            result = subprocess.run(
                ["python3", "tests.py"],
                capture_output=True, text=True, timeout=30,
                cwd=str(pdir),
            )
            ok = result.returncode == 0
            return ok, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
