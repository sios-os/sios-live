## ThroneRoom.gd — Functional controller for The Throne room.
##
## The Throne is the seat of ANUBIS's sovereignty — the final authority
## in the SIOS governance system. It displays:
##   - The Constitution's immutable laws
##   - The order of authority
##   - Court status and recent verdicts
##   - The Creator's supreme authority
extends RoomController

func _on_room_enter() -> void:
	_set_loading("Loading governance and constitutional data...")
	_refresh()

func _refresh() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_set_error("ANUBIS daemon not connected. Start with: python3 tools/anubis_daemon.py")
		return

	# Fetch constitution
	var constitution: Dictionary = _ipc_call("get_constitution")
	# Fetch court stats
	var court: Dictionary = _ipc_call("get_court_stats")
	# Fetch policy stats
	var policy: Dictionary = _ipc_call("get_policy_stats")
	# Fetch capability stats
	var caps: Dictionary = _ipc_call("get_capability_stats")

	var lines: Array[String] = []
	lines.append("=== THE THRONE ===")
	lines.append("Seat of Sovereignty & Constitutional Authority")
	lines.append("")

	if not constitution.has("error"):
		var laws: Array = constitution.get("immutable_laws", [])
		lines.append("IMMUTABLE LAWS:")
		for i in range(min(laws.size(), 10)):
			lines.append("  %d. %s" % [i + 1, laws[i]])
		lines.append("")

		var authorities: Array = constitution.get("authorities", [])
		lines.append("ORDER OF AUTHORITY:")
		for i in range(min(authorities.size(), 7)):
			var auth: Dictionary = authorities[i]
			lines.append("  %d. %s — %s" % [
				auth.get("value", 0),
				auth.get("name", "?"),
				auth.get("description", "")[:60],
			])
		lines.append("")

	if not court.has("error"):
		lines.append("COURT:")
		lines.append(_format_dict(court))
		lines.append("")

	if not policy.has("error"):
		lines.append("POLICY ENGINE:")
		lines.append(_format_dict(policy))
		lines.append("")

	if not caps.has("error"):
		lines.append("CAPABILITIES:")
		lines.append(_format_dict(caps))
		lines.append("")

	lines.append("The Creator sits above all.")
	lines.append("ANUBIS proposes. The Constitution decides.")

	_set_content("\n".join(lines))
