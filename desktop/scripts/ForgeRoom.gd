## ForgeRoom.gd — The Forge room controller.
##
## The Forge is where built and tested artifacts live. This controller
## displays the full skill library with provenance, hashes, and evidence.
extends "res://scripts/RoomController.gd"

func _on_room_enter() -> void:
	_refresh()

func _refresh() -> void:
	_set_loading("Loading skill library from ANUBIS...")
	var r := _ipc_call("get_skills")
	if r.has("error"):
		_set_error(r["error"])
		return
	var skills: Array = r.get("skills", [])
	if skills.is_empty():
		_set_content("FORGE — No skills forged yet.\n\nVisit the Workspace to launch\na mission and have ANUBIS\nbuild his first capability.")
		return
	var text := "FORGE — Skill Library\n"
	text += "%d capabilities promoted\n" % r.get("count", 0)
	text += "================================\n\n"
	for s in skills:
		text += "%s v%d\n" % [s["name"], s["version"]]
		text += "  artifact: %s...\n" % str(s["artifact_hash"]).substr(0, 24)
		text += "  model:    %s\n" % s["model"]
		text += "  attempt:  #%d\n" % s["attempt"]
		text += "  desc:     %s\n\n" % str(s["description"]).substr(0, 60)
	_set_content(text)
