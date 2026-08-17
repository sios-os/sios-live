## KnowledgeBrowserPanel.gd — Knowledge library browser panel.
##
## Shows the knowledge library in detail:
##   - Document count, claim count, verification status
##   - All 14 directors with their specialties
##   - Knowledge updater proposals (pending, verified, promoted)
##   - Semantic search status
extends RoomController

func _on_room_enter() -> void:
	_set_loading("Loading knowledge browser...")
	_refresh()

func _refresh() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_set_error("ANUBIS daemon not connected. Start with: python3 tools/anubis_daemon.py")
		return

	var knowledge: Dictionary = _ipc_call("get_knowledge_stats")
	var grounding: Dictionary = _ipc_call("get_grounding_stats")
	var directors: Dictionary = _ipc_call("list_directors")
	var updater: Dictionary = _ipc_call("get_knowledge_updater_stats")

	var lines: Array[String] = []
	lines.append("=== KNOWLEDGE BROWSER ===")
	lines.append("Governed knowledge library")
	lines.append("")

	if not knowledge.has("error"):
		lines.append("LIBRARY:")
		lines.append("  Documents: %d" % knowledge.get("library_size", 0))
		lines.append("  Total claims: %d" % knowledge.get("total_claims", 0))
		lines.append("  Verified docs: %d" % knowledge.get("verified_docs", 0))
		var tiers: Dictionary = knowledge.get("tier_distribution", {})
		if tiers.size() > 0:
			lines.append("  Trust tiers: %s" % str(tiers))
		lines.append("")

	if not grounding.has("error"):
		lines.append("RETRIEVAL:")
		lines.append("  Semantic: %s" % ("Enabled" if grounding.get("semantic_enabled", false) else "Keyword only"))
		lines.append("  Claims indexed: %d" % grounding.get("claims_indexed", 0))
		if grounding.has("semantic_stats"):
			var ss: Dictionary = grounding.get("semantic_stats", {})
			lines.append("  Embedded docs: %d" % ss.get("indexed_docs", 0))
			lines.append("  Embedding dim: %d" % ss.get("embedding_dim", 0))
		lines.append("")

	if not updater.has("error"):
		lines.append("KNOWLEDGE UPDATER:")
		lines.append("  Total proposals: %d" % updater.get("total_proposals", 0))
		lines.append("  Verified: %d" % updater.get("verified", 0))
		lines.append("  Approved: %d" % updater.get("approved", 0))
		lines.append("  Promoted: %d" % updater.get("promoted", 0))
		lines.append("  Rejected: %d" % updater.get("rejected", 0))
		lines.append("")

	if not directors.has("error"):
		var dirs: Array = directors.get("directors", [])
		lines.append("DIRECTORS (%d):" % dirs.size())
		for d in dirs:
			var did: String = d.get("director_id", "?")
			var dname: String = d.get("name", "?")
			var spec_count: int = d.get("specialty_count", 0)
			lines.append("  %s — %s (%d specialties)" % [did, dname, spec_count])
		lines.append("")

	lines.append("STATIONS:")
	lines.append("  [Browse]        Browse documents by director")
	lines.append("  [Search]        Semantic search across all knowledge")
	lines.append("  [Propose]       Propose new knowledge for review")
	lines.append("  [Verify]        View claim verification status")
	lines.append("")
	lines.append("Use DEMON to search and browse.")
	lines.append("Example: 'Search for ancient Egyptian burial practices'")

	_set_content("\n".join(lines))
