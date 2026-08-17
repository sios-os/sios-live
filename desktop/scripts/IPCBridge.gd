## IPCBridge.gd — Local IPC between the Godot desktop and the ANUBIS daemon.
##
## The ANUBIS daemon is a Python process that runs the self-development loop.
## This bridge communicates with it over a local Unix domain socket
## (/tmp/anubis.sock on Linux).
##
## All communication is local — no network is used, per Book 09.
## The bridge exposes:
##   - get_status() -> daemon health, model, sandbox state
##   - get_skills() -> list of promoted skills
##   - get_ledger_summary() -> entry count, integrity, head hash
##   - request_mission(task, skill_name, approval_token) -> start a mission
##   - get_mission_status(mission_id) -> poll an in-progress mission
##   - chat(message) -> talk to ANUBIS through the DEMON interface
##   - reset_chat() -> clear conversation history
##   - tts(text) -> text-to-speech (generate audio)
##   - stt(timeout) -> speech-to-text (record and transcribe)
##   - list_projects() -> list all projects
##   - get_project(name) -> get project details
##   - plan_project(name, description, approval_token) -> plan a new project
##   - run_project(name, approval_token) -> execute a planned project
##   - poll_project(project_id) -> poll project execution status
##   - get_constitution() -> constitutional framework (Hall of Architects)
##   - get_ledger_entries(limit, offset, action) -> browse ledger (Hall of Memory)
##   - get_skill_versions(name) -> skill version history (Hall of Evolution)
##   - get_mission_history() -> mission archive (Hall of Creation)
##   - get_genesis() -> ANUBIS first moments (Hall of Genesis)
##   - fs_list(path) -> list directory contents
##   - fs_read(path) -> read file contents
##   - fs_write(path, content, approval_token) -> write file (needs approval)
##   - run_cmd(cmd, approval_token) -> run terminal command (needs approval)
##   Self-healing commands (for Tomb Hall and dashboard screens):
##   - get_snapshot_list() / get_snapshot_status() / create_snapshot()
##   - get_self_repair_status() / run_self_repair_check() / get_self_repair_alerts()
##   - get_drive_report() / get_cold_archive_status() / create_cold_archive()
##   - get_boot_check() / get_degradation_status()
##   - get_book_status() / get_book_latest() / get_book_editions() / generate_book()
##   - get_dream_status() / get_dream_gaps() / get_dream_recommendations() / run_dream_cycle()
##   - get_scheduler_status() / get_systems_status()
##   - get_funding_status() / get_funding_pending_reviews()
##   - get_phone_status() / get_email_status()
##   - get_inference_status() / get_embeddings_status() / get_dependency_status()
##
## Consequential actions (running a mission) require an approval token that
## the desktop UI must obtain from the Creator.
extends Node

const SOCKET_PATH := "/tmp/anubis.sock"
const TIMEOUT_SECONDS := 5.0

var _connected: bool = false

signal daemon_connected()
signal daemon_disconnected()

func _ready() -> void:
	_try_connect()

func _try_connect() -> void:
	_connected = false
	# Godot's FileAccess can't detect Unix sockets, so we use a shell test.
	var output := []
	var exit := OS.execute("bash", ["-c", "test -S %s && echo yes || echo no" % SOCKET_PATH], output)
	if exit == 0 and output.size() > 0 and output[0].strip_edges() == "yes":
		_connected = true
		daemon_connected.emit()

func is_daemon_connected() -> bool:
	return _connected

const IPC_HELPER := "/opt/sios-live/tools/ipc_helper.py"

func _send_request(req: Dictionary) -> Dictionary:
	# We use a Python helper script to bridge the Unix socket, since Godot 4
	# doesn't have built-in Unix socket support in GDScript.
	# The helper reads a JSON request from a temp file and writes the response.
	if not _connected:
		return {"error": "ANUBIS daemon not running"}
	var tmp_in := "/tmp/anubis-ipc-req.json"
	var tmp_out := "/tmp/anubis-ipc-resp.json"
	# Write request
	var f := FileAccess.open(tmp_in, FileAccess.WRITE)
	if f == null:
		return {"error": "cannot write temp file"}
	f.store_string(JSON.stringify(req))
	f.close()
	# Call the helper
	var helper_path := IPC_HELPER
	if not FileAccess.file_exists(helper_path):
		# Fall back to the source tree path (for development)
		helper_path = "/mnt/d/SIOS-Build/sios-live/tools/ipc_helper.py"
	var exit := OS.execute("python3", [helper_path, tmp_in, tmp_out], [])
	if exit != 0:
		return {"error": "bridge helper failed (exit %d)" % exit}
	# Read response
	var g := FileAccess.open(tmp_out, FileAccess.READ)
	if g == null:
		return {"error": "no response file"}
	var text: String = g.get_as_text()
	g.close()
	text = text.strip_edges()
	if text.is_empty():
		return {"error": "empty response"}
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return {"error": "invalid response"}
	return parsed

func get_status() -> Dictionary:
	return _send_request({"cmd": "status"})

func get_skills() -> Dictionary:
	return _send_request({"cmd": "skills"})

func get_ledger_summary() -> Dictionary:
	return _send_request({"cmd": "ledger"})

func request_mission(task: String, skill_name: String, approval_token: String) -> Dictionary:
	return _send_request({
		"cmd": "mission",
		"task": task,
		"skill_name": skill_name,
		"approval_token": approval_token,
	})

func get_mission_status(mission_id: String) -> Dictionary:
	return _send_request({"cmd": "poll", "mission_id": mission_id})

func chat(message: String) -> Dictionary:
	return _send_request({"cmd": "chat", "message": message})

func reset_chat() -> Dictionary:
	return _send_request({"cmd": "reset_chat"})

func tts(text: String) -> Dictionary:
	return _send_request({"cmd": "tts", "text": text})

func stt(timeout: float = 5.0) -> Dictionary:
	return _send_request({"cmd": "stt", "timeout": timeout})

func list_projects() -> Dictionary:
	return _send_request({"cmd": "list_projects"})

func get_project(name: String) -> Dictionary:
	return _send_request({"cmd": "get_project", "name": name})

func plan_project(name: String, description: String, approval_token: String) -> Dictionary:
	return _send_request({
		"cmd": "plan_project",
		"name": name,
		"description": description,
		"approval_token": approval_token,
	})

func run_project(name: String, approval_token: String) -> Dictionary:
	return _send_request({
		"cmd": "run_project",
		"name": name,
		"approval_token": approval_token,
	})

func poll_project(project_id: String) -> Dictionary:
	return _send_request({"cmd": "poll_project", "project_id": project_id})

func get_constitution() -> Dictionary:
	return _send_request({"cmd": "constitution"})

func get_ledger_entries(limit: int = 20, offset: int = 0, action: String = "") -> Dictionary:
	var req := {"cmd": "ledger_entries", "limit": limit, "offset": offset}
	if action != "":
		req["action"] = action
	return _send_request(req)

func get_skill_versions(name: String = "") -> Dictionary:
	return _send_request({"cmd": "skill_versions", "name": name})

func get_mission_history() -> Dictionary:
	return _send_request({"cmd": "mission_history"})

func get_genesis() -> Dictionary:
	return _send_request({"cmd": "genesis"})

func fs_list(path: String = "") -> Dictionary:
	var req := {"cmd": "fs_list"}
	if path != "":
		req["path"] = path
	return _send_request(req)

func fs_read(path: String) -> Dictionary:
	return _send_request({"cmd": "fs_read", "path": path})

func fs_write(path: String, content: String, approval_token: String) -> Dictionary:
	return _send_request({
		"cmd": "fs_write",
		"path": path,
		"content": content,
		"approval_token": approval_token,
	})

func run_cmd(cmd: String, approval_token: String) -> Dictionary:
	return _send_request({
		"cmd": "run_cmd",
		"command": cmd,
		"approval_token": approval_token,
	})

# --- New module commands ---

func get_queue_stats() -> Dictionary:
	return _send_request({"cmd": "queue_stats"})

func queue_add(skill_name: String, task: String) -> Dictionary:
	return _send_request({"cmd": "queue_add", "skill_name": skill_name, "task": task})

func queue_add_batch(missions: Array) -> Dictionary:
	return _send_request({"cmd": "queue_add_batch", "missions": missions})

func queue_process(limit: int = 1) -> Dictionary:
	return _send_request({"cmd": "queue_process", "limit": limit})

func queue_list() -> Dictionary:
	return _send_request({"cmd": "queue_list"})

func orchestrate(query: String, max_directors: int = 3) -> Dictionary:
	return _send_request({"cmd": "orchestrate", "query": query, "max_directors": max_directors})

func knowledge_propose(specialty_id: String, title: String, content: String) -> Dictionary:
	return _send_request({"cmd": "knowledge_propose", "specialty_id": specialty_id, "title": title, "content": content})

func knowledge_approve(proposal_id: String) -> Dictionary:
	return _send_request({"cmd": "knowledge_approve", "proposal_id": proposal_id})

func knowledge_promote_proposal(proposal_id: String) -> Dictionary:
	return _send_request({"cmd": "knowledge_promote_proposal", "proposal_id": proposal_id})

func get_knowledge_updater_stats() -> Dictionary:
	return _send_request({"cmd": "knowledge_updater_stats"})

func backup_create(label: String = "") -> Dictionary:
	return _send_request({"cmd": "backup_create", "label": label})

func backup_list() -> Dictionary:
	return _send_request({"cmd": "backup_list"})

func backup_restore(backup_name: String) -> Dictionary:
	return _send_request({"cmd": "backup_restore", "backup_name": backup_name})

func voice_toggle_out() -> Dictionary:
	return _send_request({"cmd": "voice_toggle_out"})

func voice_toggle_in() -> Dictionary:
	return _send_request({"cmd": "voice_toggle_in"})

func voice_speak(text: String) -> Dictionary:
	return _send_request({"cmd": "voice_speak", "text": text})

func voice_status() -> Dictionary:
	return _send_request({"cmd": "voice_status"})

func docs_generate() -> Dictionary:
	return _send_request({"cmd": "docs_generate"})

# --- Self-healing commands (for Tomb Hall and dashboard screens) ---

func get_snapshot_list() -> Dictionary:
	return _send_request({"cmd": "snapshot_list"})

func get_snapshot_status() -> Dictionary:
	return _send_request({"cmd": "snapshot_status"})

func create_snapshot() -> Dictionary:
	return _send_request({"cmd": "snapshot_create"})

func get_self_repair_status() -> Dictionary:
	return _send_request({"cmd": "self_repair_status"})

func run_self_repair_check() -> Dictionary:
	return _send_request({"cmd": "self_repair_check"})

func get_self_repair_alerts() -> Dictionary:
	return _send_request({"cmd": "self_repair_alerts"})

func get_drive_report() -> Dictionary:
	return _send_request({"cmd": "drive_report"})

func get_cold_archive_status() -> Dictionary:
	return _send_request({"cmd": "cold_archive_status"})

func create_cold_archive() -> Dictionary:
	return _send_request({"cmd": "cold_archive_create"})

func get_boot_check() -> Dictionary:
	return _send_request({"cmd": "boot_check"})

func get_book_status() -> Dictionary:
	return _send_request({"cmd": "book_seal_status"})

func get_book_latest() -> Dictionary:
	return _send_request({"cmd": "book_read_latest"})

func get_book_editions() -> Dictionary:
	return _send_request({"cmd": "book_list_editions"})

func generate_book() -> Dictionary:
	return _send_request({"cmd": "book_generate"})

func get_dream_status() -> Dictionary:
	return _send_request({"cmd": "dream_status"})

func get_dream_gaps() -> Dictionary:
	return _send_request({"cmd": "dream_gaps"})

func get_dream_recommendations() -> Dictionary:
	return _send_request({"cmd": "dream_recommendations"})

func run_dream_cycle() -> Dictionary:
	return _send_request({"cmd": "dream_run"})

func get_degradation_status() -> Dictionary:
	return _send_request({"cmd": "self_repair_degradation_status"})

func get_scheduler_status() -> Dictionary:
	return _send_request({"cmd": "scheduler_status"})

func get_systems_status() -> Dictionary:
	return _send_request({"cmd": "systems_status"})

func get_funding_status() -> Dictionary:
	return _send_request({"cmd": "funding_status"})

func get_funding_pending_reviews() -> Dictionary:
	return _send_request({"cmd": "funding_pending_reviews"})

func get_phone_status() -> Dictionary:
	return _send_request({"cmd": "phone_status"})

func get_email_status() -> Dictionary:
	return _send_request({"cmd": "email_status"})

func get_inference_status() -> Dictionary:
	return _send_request({"cmd": "inference_status"})

func get_embeddings_status() -> Dictionary:
	return _send_request({"cmd": "embeddings_status"})

func get_dependency_status() -> Dictionary:
	return _send_request({"cmd": "dependency_status"})
