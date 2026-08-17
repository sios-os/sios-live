## CourtPanel.gd — Court review and governance display panel.
##
## Shows the Court status:
##   - Pending reviews
##   - Verdicts (promoted, probation, denied)
##   - Probation status for models and artifacts
extends RoomController

func _on_room_enter() -> void:
	_set_loading("Loading Court status...")
	_refresh()

func _refresh() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_set_error("ANUBIS daemon not connected. Start with: python3 tools/anubis_daemon.py")
		return

	var court: Dictionary = _ipc_call("get_court_stats")
	var policy: Dictionary = _ipc_call("get_policy_stats")
	var capability: Dictionary = _ipc_call("get_capability_stats")
	var identity: Dictionary = _ipc_call("get_identity_stats")

	var lines: Array[String] = []
	lines.append("=== THE COURT ===")
	lines.append("Governance and constitutional review")
	lines.append("")

	if not court.has("error"):
		lines.append("COURT STATUS:")
		lines.append("  Total reviews: %d" % court.get("total_reviews", 0))
		lines.append("  Pending: %d" % court.get("pending", 0))
		lines.append("  Promoted: %d" % court.get("promoted", 0))
		lines.append("  Probation: %d" % court.get("probation", 0))
		lines.append("  Denied: %d" % court.get("denied", 0))
		var reviews: Array = court.get("recent_reviews", [])
		if reviews.size() > 0:
			lines.append("")
			lines.append("RECENT REVIEWS:")
			for r in reviews:
				var artifact: String = r.get("artifact_id", "?")
				if artifact.length() > 24:
					artifact = artifact.substr(0, 24) + "..."
				lines.append("  %s — %s" % [artifact, r.get("verdict", "?")])
				if r.get("probation_days", 0) > 0:
					lines.append("    Probation: %d days" % r.get("probation_days", 0))
		lines.append("")

	if not policy.has("error"):
		lines.append("POLICY ENGINE:")
		var limits: Dictionary = policy.get("spending_limits", {})
		lines.append("  Daily limit: $%s" % str(limits.get("daily", 0)))
		lines.append("  Weekly limit: $%s" % str(limits.get("weekly", 0)))
		lines.append("  Monthly limit: $%s" % str(limits.get("monthly", 0)))
		var prohibited: Array = policy.get("prohibited_categories", [])
		lines.append("  Prohibited: %s" % ", ".join(prohibited))
		lines.append("")

	if not capability.has("error"):
		lines.append("CAPABILITY BROKER:")
		lines.append("  Active capabilities: %d" % capability.get("active", 0))
		lines.append("  Granted: %d" % capability.get("granted", 0))
		lines.append("  Revoked: %d" % capability.get("revoked", 0))
		lines.append("")

	if not identity.has("error"):
		lines.append("CREATOR BINDING:")
		lines.append("  Creator: %s" % identity.get("creator_name", "Unknown"))
		lines.append("  Enrolled: %s" % ("Yes" if identity.get("enrolled", false) else "No"))
		lines.append("  Successors: %d" % identity.get("successors", 0))
		lines.append("")

	lines.append("STATIONS:")
	lines.append("  [Submit]        Submit an artifact for Court review")
	lines.append("  [Review]        View pending reviews in detail")
	lines.append("  [Probation]     Check probation status")
	lines.append("")
	lines.append("The Court enforces constitutional governance.")
	lines.append("All promotions require Creator approval with exact hash binding.")

	_set_content("\n".join(lines))
