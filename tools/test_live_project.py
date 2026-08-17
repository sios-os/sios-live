#!/usr/bin/env python3
"""Test live project planning and execution."""
import json, socket, sys, time

SOCKET = "/tmp/anubis.sock"

def send_cmd(cmd: dict) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET)
    s.sendall((json.dumps(cmd) + "\n").encode())
    data = s.recv(65536).decode()
    s.close()
    return json.loads(data)

print("=== Live Project Test ===\n")

# Step 1: Plan a project
print("Planning project: text_analyzer")
print("  Description: A text analysis tool that counts words, finds unique words, and formats output")
resp = send_cmd({
    "cmd": "plan_project",
    "name": "text_analyzer",
    "description": "A text analysis tool that counts words, finds unique words, and formats output as JSON",
    "approval_token": "creator-approved",
})
if "error" in resp:
    print(f"ERROR: {resp['error']}")
    sys.exit(1)

project = resp.get("project", {})
print(f"\nPlan created:")
print(f"  Description: {project.get('description')}")
print(f"  Steps: {len(project.get('steps', []))}")
for i, step in enumerate(project.get("steps", [])):
    reuse = step.get("skill_name", "")
    task = step.get("task", "")
    if reuse:
        print(f"  {i+1}. {step['name']}: reuse '{reuse}' - {step['description']}")
    else:
        print(f"  {i+1}. {step['name']}: NEW - {task[:60]}")

# Step 2: Execute the project
print("\nExecuting project...")
resp = send_cmd({
    "cmd": "run_project",
    "name": "text_analyzer",
    "approval_token": "creator-approved",
})
if "error" in resp:
    print(f"ERROR: {resp['error']}")
    sys.exit(1)

project_id = resp.get("project_id", "")
print(f"  Project ID: {project_id}")

# Step 3: Poll for completion
for attempt in range(120):
    time.sleep(5)
    poll = send_cmd({"cmd": "poll_project", "project_id": project_id})
    status = poll.get("status", "?")
    print(f"  Poll {attempt+1}: {status}", end="")
    if status in ("complete", "failed", "error"):
        print()
        if status == "complete":
            proj = poll.get("project", {})
            print(f"\n  Project complete!")
            print(f"  Steps: {len(proj.get('steps', []))}")
            for i, step in enumerate(proj.get("steps", [])):
                print(f"    {i+1}. {step['name']}: {step['status']} (skill: {step.get('skill_name', '?')})")
        else:
            print(f"  Error: {poll.get('error', poll.get('project', {}).get('integration_error', '?'))}")
        break
    print(" (still running...)")
else:
    print("\n  Timed out waiting")

# Step 4: List all projects
print("\n=== All Projects ===")
resp = send_cmd({"cmd": "list_projects"})
for p in resp.get("projects", []):
    print(f"  {p['name']}: {p['status']} ({p.get('steps_complete',0)}/{p.get('steps_total',0)} steps)")
