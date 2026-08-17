## SanctumRoom.gd — Functional controller for the Sanctum room.
##
## The Sanctum is ANUBIS's personal space — identity, knowledge browser,
## appearance, voice, privacy, and accessibility settings.
##
## It serves as the knowledge browser, showing:
##   - Creator identity and vault status
##   - Knowledge library stats (550 docs, 15,677 claims)
##   - All 14 directors and their specialties
##   - Semantic search status
##   - Grounding system status
extends RoomController

func _on_room_enter() -> void:
	_set_loading("Loading identity and knowledge data...")
	_refresh()

func _refresh() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_set_error("ANUBIS daemon not connected. Start with: python3 tools/anubis_daemon.py")
		return

	# Fetch all data
	var identity: Dictionary = _ipc_call("get_identity_stats")
	var knowledge: Dictionary = _ipc_call("get_knowledge_stats")
	var grounding: Dictionary = _ipc_call("get_grounding_stats")
	var directors: Dictionary = _ipc_call("list_directors")

	var lines: Array[String] = []
	lines.append("=== SANCTUM ===")
	lines.append("Identity & Knowledge Browser")
	lines.append("")

	# Identity section
	if not identity.has("error"):
		lines.append("CREATOR IDENTITY:")
		lines.append("  Enrolled: %s" % ("Yes" if identity.get("enrolled", false) else "No"))
		lines.append("  Name: %s" % identity.get("creator_name", "Unknown"))
		lines.append("  Successors: %d (%d consented)" % [identity.get("successors", 0), identity.get("consented_successors", 0)])
		lines.append("  Vault: %s" % ("Unlocked" if identity.get("vault_unlocked", false) else "Locked"))
		lines.append("")

	# Knowledge library section
	if not knowledge.has("error"):
		lines.append("KNOWLEDGE LIBRARY:")
		lines.append("  Documents: %d" % knowledge.get("library_size", 0))
		lines.append("  Claims: %d" % knowledge.get("total_claims", 0))
		lines.append("  Verified: %d" % knowledge.get("verified_docs", 0))
		var tiers: Dictionary = knowledge.get("tier_distribution", {})
		lines.append("  Tiers: %s" % str(tiers))
		lines.append("")

	# Grounding section
	if not grounding.has("error"):
		lines.append("GROUNDING SYSTEM:")
		lines.append("  Semantic: %s" % ("Enabled" if grounding.get("semantic_enabled", false) else "Keyword only"))
		lines.append("  Claims indexed: %d" % grounding.get("claims_indexed", 0))
		var idx_stats: Dictionary = grounding.get("index_stats", {})
		lines.append("  Keywords: %d" % idx_stats.get("keywords_indexed", 0))
		lines.append("  Specialties: %d" % idx_stats.get("specialties_indexed", 0))
		if grounding.has("semantic_stats"):
			var ss: Dictionary = grounding.get("semantic_stats", {})
			lines.append("  Embedding dim: %d" % ss.get("embedding_dim", 0))
			lines.append("  Embedded docs: %d" % ss.get("indexed_docs", 0))
		lines.append("")

	# Directors browser
	if not directors.has("error"):
		var dirs: Array = directors.get("directors", [])
		lines.append("KNOWLEDGE DIRECTORS (%d):" % dirs.size())
		for d in dirs:
			lines.append("  %s — %s" % [d.get("director_id", "?"), d.get("name", "?")])
		lines.append("")

	# Stations
	lines.append("STATIONS:")
	lines.append("  [Identity]       Manage Creator identity and vault")
	lines.append("  [Appearance]     Customize desktop theme and visuals")
	lines.append("  [Voice]          Configure voice input/output")
	lines.append("  [Privacy]        Data privacy and retention settings")
	lines.append("  [Accessibility]  Accessibility options")
	lines.append("")
	lines.append("Use DEMON to browse knowledge by director or specialty.")
	lines.append("Example: 'Show me documents about ancient Egypt'")

	_set_content("\n".join(lines))
