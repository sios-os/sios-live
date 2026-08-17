## TombEntranceRoom.gd — Functional controller for the Tomb Entrance.
##
## The Tomb Entrance is the gateway to the six halls of ANUBIS's history.
## It displays the three proof rings (constitutional gates) and shows
## which halls are available to visit.
extends RoomController

func _on_room_enter() -> void:
	_set_loading("Loading tomb entrance data...")
	_refresh()

func _refresh() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_set_error("ANUBIS daemon not connected. Start with: python3 tools/anubis_daemon.py")
		return

	var constitution: Dictionary = _ipc_call("get_constitution")
	var ledger: Dictionary = _ipc_call("get_ledger")
	var skills: Dictionary = _ipc_call("get_skills")

	var lines: Array[String] = []
	lines.append("=== TOMB ENTRANCE ===")
	lines.append("Gateway to the Halls of ANUBIS")
	lines.append("")

	lines.append("THREE PROOF RINGS (Constitutional Gates):")
	if not constitution.has("error"):
		var classes: Array = constitution.get("change_classes", [])
		for i in range(min(classes.size(), 3)):
			var cc: Dictionary = classes[i]
			lines.append("  Ring %d: %s (level %d)" % [
				i + 1,
				cc.get("name", "?"),
				cc.get("value", 0),
			])
	else:
		lines.append("  [Constitution not available]")
	lines.append("")

	lines.append("HALLS BEYOND THE GATE:")
	lines.append("  Hall of Genesis      — ANUBIS's first moments")
	lines.append("  Hall of Evolution    — Skill version history")
	lines.append("  Hall of Architects   — The Constitution")
	lines.append("  Hall of Sovereignty  — Governance and authority")
	lines.append("  Hall of Memory       — Evidence ledger")
	lines.append("  Hall of Creation     — Mission archive")
	lines.append("")

	if not ledger.has("error"):
		lines.append("LEDGER INTEGRITY:")
		lines.append("  Entries: %d" % ledger.get("entries", 0))
		lines.append("  Verified: %s" % ledger.get("integrity_ok", false))
		lines.append("  Head: %s" % ledger.get("head", "?")[:24])
		lines.append("")

	if not skills.has("error"):
		lines.append("SKILL LIBRARY:")
		lines.append("  Promoted skills: %d" % skills.get("count", 0))
		lines.append("")

	lines.append("The gate stands ready. Pass through to witness ANUBIS's history.")

	_set_content("\n".join(lines))
