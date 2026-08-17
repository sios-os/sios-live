#!/usr/bin/env python3
"""Test the project executor with a real multi-step project."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.projects import ProjectWorkspace, Project, ProjectStep, ProjectExecutor
from anubis.skills import SkillLibrary
from anubis.ledger import Ledger
from anubis.loop import SelfDevelopmentLoop
from anubis.model import OllamaAdapter
from anubis.sandbox import Sandbox, SandboxPolicy

ROOT = Path(".")
model = OllamaAdapter("qwen2.5-coder:7b", require_tools=False)
library = SkillLibrary(ROOT / "skills")
ledger = Ledger(ROOT / "evidence" / "ledger.jsonl")
sandbox = Sandbox(SandboxPolicy(timeout_s=30, memory_mb=512, cpu_seconds=20))
loop = SelfDevelopmentLoop(model, library, ledger, sandbox, max_attempts=3)

workspace = ProjectWorkspace(ROOT / "projects")
executor = ProjectExecutor(workspace, library, loop, sandbox)

print("=== PROJECT EXECUTOR TEST ===")
print()

# Define a project: "String Toolkit" — combines 3 existing skills + 1 new one
project = Project(
    name="string_toolkit",
    description="A string manipulation toolkit combining multiple skills",
    created_at=__import__("time").time(),
    steps=[
        ProjectStep(
            name="reverse",
            description="Reverse a string",
            skill_name="reverse_string",  # reuse existing
        ),
        ProjectStep(
            name="count_words",
            description="Count words in a string",
            skill_name="count_words",  # reuse existing
        ),
        ProjectStep(
            name="title_case",
            description="Convert to title case",
            skill_name="title_case",  # reuse existing
        ),
        ProjectStep(
            name="slugify_text",
            description="Convert text to URL-friendly slug",
            skill_name="slugify",  # reuse existing
        ),
    ],
)

print(f"Project: {project.name}")
print(f"Description: {project.description}")
print(f"Steps: {len(project.steps)}")
for i, s in enumerate(project.steps):
    reuse = f"reuse {s.skill_name}" if s.skill_name else f"new: {s.task}"
    print(f"  {i+1}. {s.name} — {reuse}")
print()

# Execute
print("--- Executing project ---")
result = executor.execute(project)
print()
print(f"Status: {result.status}")
print(f"Steps completed: {sum(1 for s in result.steps if s.status == 'complete')}/{len(result.steps)}")
print()

if result.status == "complete":
    print("--- Project main.py (first 500 chars) ---")
    print(result.main_code[:500])
    print("...")
    print()
    print(f"Artifact hash: {result.artifact_hash[:32]}...")
    print(f"Main code size: {len(result.main_code)} chars")
    print(f"Test code size: {len(result.test_code)} chars")
else:
    print("--- Project FAILED ---")
    for s in result.steps:
        if s.status == "failed":
            print(f"  {s.name}: {s.error}")
    if result.integration_error:
        print(f"  Integration error: {result.integration_error[:200]}")
print()

# List all projects
print("--- All Projects ---")
for p in workspace.list_projects():
    print(f"  {p['name']}: {p['status']} ({p['steps_complete']}/{p['steps_total']} steps)")
print()

print("=== PROJECT EXECUTOR TEST COMPLETE ===")
