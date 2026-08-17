## ProjectWorkspacePanel.gd — Project workspace display panel.
##
## Shows multi-file project status:
##   - Active projects and their step progress
##   - Completed projects with artifact hashes
##   - Project descriptions and step details
extends RoomController

func _on_room_enter() -> void:
	_set_loading("Loading project workspace...")
	_refresh()

func _refresh() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_set_error("ANUBIS daemon not connected. Start with: python3 tools/anubis_daemon.py")
		return

	var projects: Dictionary = _ipc_call("list_projects")

	var lines: Array[String] = []
	lines.append("=== PROJECT WORKSPACE ===")
	lines.append("Multi-file project builder")
	lines.append("")

	if projects.has("error"):
		lines.append("ERROR: %s" % projects.get("error", "unknown"))
	elif projects.has("projects"):
		var all_projects: Array = projects.get("projects", [])
		lines.append("PROJECTS (%d):" % all_projects.size())
		lines.append("")
		for p in all_projects:
			lines.append("  %s — %s" % [p.get("name", "?"), p.get("status", "?")])
			lines.append("    Steps: %d/%d" % [p.get("steps_complete", 0), p.get("steps_total", 0)])
			if p.get("description", "") != "":
				lines.append("    Description: %s" % p.get("description", ""))
			if p.get("artifact_hash", "") != "":
				var h: String = p.get("artifact_hash", "")
				if h.length() > 32:
					h = h.substr(0, 32) + "..."
				lines.append("    Hash: %s" % h)
			lines.append("")
	else:
		lines.append("No projects found.")
		lines.append("")

	lines.append("STATIONS:")
	lines.append("  [New Project]   Plan a new multi-file project")
	lines.append("  [Run Project]   Execute a planned project")
	lines.append("  [View Code]     Browse project source code")
	lines.append("")
	lines.append("Use DEMON to create projects.")
	lines.append("Example: 'Build a string toolkit with reverse, count, and slugify'")

	_set_content("\n".join(lines))
