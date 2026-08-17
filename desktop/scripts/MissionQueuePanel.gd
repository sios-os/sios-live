## MissionQueuePanel.gd — Mission queue display panel.
##
## Shows the persistent mission queue status:
##   - Pending, running, completed, failed counts
##   - Recent missions with status
##   - Allows adding new missions and processing pending ones
extends RoomController

func _on_room_enter() -> void:
	_set_loading("Loading mission queue...")
	_refresh()

func _refresh() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_set_error("ANUBIS daemon not connected. Start with: python3 tools/anubis_daemon.py")
		return

	var stats: Dictionary = _ipc_call("get_queue_stats")
	var missions: Dictionary = _ipc_call("queue_list")

	var lines: Array[String] = []
	lines.append("=== MISSION QUEUE ===")
	lines.append("Persistent autonomous work queue")
	lines.append("")

	if not stats.has("error"):
		lines.append("QUEUE STATUS:")
		lines.append("  Total missions: %d" % stats.get("total", 0))
		var by_status: Dictionary = stats.get("by_status", {})
		lines.append("  Pending: %d" % by_status.get("pending", 0))
		lines.append("  Running: %d" % by_status.get("running", 0))
		lines.append("  Completed: %d" % by_status.get("completed", 0))
		lines.append("  Failed: %d" % by_status.get("failed", 0))
		lines.append("  Skipped: %d" % by_status.get("skipped", 0))
		lines.append("")

	if not missions.has("error"):
		var all_missions: Array = missions.get("missions", [])
		lines.append("RECENT MISSIONS (%d total):" % all_missions.size())
		var shown := 0
		for m in all_missions:
			if shown >= 20:
				lines.append("  ... and %d more" % (all_missions.size() - 20))
				break
			var status_icon := "?"
			match m.get("status", ""):
				"pending":  status_icon = "[ ]"
				"running":  status_icon = "[~]"
				"completed": status_icon = "[+]"
				"failed":   status_icon = "[-]"
				"skipped":  status_icon = "[/]"
			lines.append("  %s %s — %s" % [status_icon, m.get("skill_name", "?"), m.get("status", "?")])
			if m.get("result", "") != "":
				lines.append("       result: %s" % m.get("result", ""))
			if m.get("error", "") != "":
				lines.append("       error: %s" % m.get("error", ""))
			shown += 1
		lines.append("")

	lines.append("STATIONS:")
	lines.append("  [Add Mission]    Queue a new skill for ANUBIS to develop")
	lines.append("  [Process]        Process the next pending mission")
	lines.append("  [Batch]          Add multiple missions at once")
	lines.append("")
	lines.append("Use DEMON to interact with the queue.")
	lines.append("Example: 'Queue a function that converts CSV to JSON'")

	_set_content("\n".join(lines))
