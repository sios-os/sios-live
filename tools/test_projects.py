#!/usr/bin/env python3
"""Quick compile check for new modules."""
from anubis.projects import ProjectWorkspace, Project, ProjectStep, parse_project_plan, plan_to_project
from anubis.loop import SelfDevelopmentLoop, AnubisRuntime
print("All imports OK")

# Test project workspace
import tempfile, os
with tempfile.TemporaryDirectory() as td:
    ws = ProjectWorkspace(td)
    p = Project(name="test_proj", description="A test project", created_at=1234.0)
    p.steps.append(ProjectStep(name="step1", description="First step", task="do something"))
    p.steps.append(ProjectStep(name="step2", description="Second step", skill_name="existing_skill"))
    ws.save(p)
    loaded = ws.load("test_proj")
    assert loaded is not None
    assert loaded.name == "test_proj"
    assert len(loaded.steps) == 2
    assert loaded.steps[0].task == "do something"
    assert loaded.steps[1].skill_name == "existing_skill"
    print("ProjectWorkspace save/load OK")

    # Test list
    projects = ws.list_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == "test_proj"
    print("ProjectWorkspace list OK")

# Test plan parsing
plan = parse_project_plan('''{
  "description": "A CSV processor",
  "steps": [
    {"name": "parse", "description": "Parse CSV", "reuse_skill": "csv_parser", "new_task": null},
    {"name": "analyze", "description": "Analyze data", "reuse_skill": null, "new_task": "Count rows and columns"}
  ]
}''')
assert plan is not None
assert len(plan["steps"]) == 2
project = plan_to_project(plan)
assert project.description == "A CSV processor"
assert project.steps[0].skill_name == "csv_parser"
assert project.steps[1].task == "Count rows and columns"
print("Plan parsing OK")

print("\nAll project tests passed!")
