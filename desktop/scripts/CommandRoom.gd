## CommandRoom.gd — The Command Chamber room controller.
##
## The Command Chamber shows the live status of the ANUBIS system:
##   - Daemon health
##   - Model availability and version
##   - Sandbox isolation state
##   - Skill and ledger counts
extends "res://scripts/RoomController.gd"

var _refresh_timer: float = 0.0

func _on_room_enter() -> void:
	_refresh()

func _process(delta: float) -> void:
	_refresh_timer += delta
	if _refresh_timer < 5.0:
		return
	_refresh_timer = 0.0
	_refresh()

func _refresh() -> void:
	_set_loading("Querying ANUBIS daemon...")
	var r := _ipc_call("get_status")
	if r.has("error"):
		_set_error(r["error"])
		return
	var text := "COMMAND CHAMBER — System Status\n"
	text += "================================\n\n"
	text += "Daemon:     %s (pid %s)\n" % [r.get("daemon", "?"), r.get("pid", "?")]
	text += "Model:      %s\n" % r.get("model", "?")
	var model_ok: bool = r.get("model_present", false)
	text += "  present:  %s\n" % ("YES" if model_ok else "NO")
	if r.get("model_error") != null and str(r.get("model_error")) != "":
		text += "  error:    %s\n" % r.get("model_error")
	text += "\nSandbox:\n"
	text += "  %s\n" % r.get("sandbox", "?")
	text += "\nCounts:\n"
	text += "  skills:   %s\n" % r.get("skills_count", 0)
	text += "  ledger:   %s entries\n" % r.get("ledger_entries", 0)
	text += "\n"
	if model_ok:
		text += "ANUBIS is operational.\n"
		text += "Model is available for missions.\n"
	else:
		text += "ANUBIS is in degraded mode.\n"
		text += "Model not available — install Ollama\n"
		text += "and pull llama3.1:8b.\n"
	_set_content(text)
