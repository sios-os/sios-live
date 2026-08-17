## TombHall.gd — Functional controller for the six Tomb halls.
##
## Each hall is a living exhibit of ANUBIS's history and governance:
##   - Hall of Genesis:    ANUBIS's first moments, first ledger entries, stats
##   - Hall of Evolution:   Skill version history, how capabilities evolved
##   - Hall of Architects:  The Constitution — authorities, change classes, laws
##   - Hall of Sovereignty: Governance and authority — who can do what
##   - Hall of Memory:      The evidence ledger — browse entries
##   - Hall of Creation:    Mission archive — all past missions
##
## The controller fetches data from the ANUBIS daemon via IPC and displays
## it on the hall's artifact pedestals as floating labels.
extends Node3D

var _ipc: Node
var _labels: Array[Label3D] = []
var _refresh_timer: float = 0.0
var _room_id: String = ""

func _ready() -> void:
	_ipc = get_node_or_null("/root/SIOSDesktop/IPCBridge")
	# Determine which hall we're in from our parent room name
	var parent = get_parent()
	if parent:
		_room_id = parent.name.replace("ROOM_", "").to_lower()
	_load_hall_data()

func _process(delta: float) -> void:
	_refresh_timer += delta
	if _refresh_timer >= 10.0:
		_refresh_timer = 0.0
		_load_hall_data()

func _load_hall_data() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_show_offline()
		return
	match _room_id:
		"hall_of_genesis":
			_load_genesis()
		"hall_of_evolution":
			_load_evolution()
		"hall_of_architects":
			_load_architects()
		"hall_of_sovereignty":
			_load_sovereignty()
		"hall_of_memory":
			_load_memory()
		"hall_of_creation":
			_load_creation()
		_:
			pass

func _clear_labels() -> void:
	for label in _labels:
		if is_instance_valid(label):
			label.queue_free()
	_labels.clear()

func _add_label(text: String, pos: Vector3, color: Color = Color("e1c77e")) -> void:
	var label := Label3D.new()
	label.text = text
	label.position = pos
	label.modulate = color
	label.font_size = 48
	label.outline_modulate = Color.BLACK
	label.outline_size = 8
	label.pixel_size = 0.01
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)
	_labels.append(label)

func _show_offline() -> void:
	_clear_labels()
	_add_label("ANUBIS OFFLINE", Vector3(0, 3, -5), Color("8b3a3a"))
	_add_label("Start the daemon to see hall data", Vector3(0, 2.5, -5), Color("78818a"))

# ------------------------------------------------------------------ halls

func _load_genesis() -> void:
	var resp: Dictionary = _ipc.get_genesis()
	if resp.has("error"):
		_show_offline()
		return
	_clear_labels()
	_add_label("HALL OF GENESIS", Vector3(0, 4.5, -5), Color("e1c77e"))
	_add_label("ANUBIS — First Moments", Vector3(0, 4.0, -5), Color("c4a35a"))

	var total_skills: int = resp.get("total_skills", 0)
	var total_entries: int = resp.get("total_ledger_entries", 0)
	var total_missions: int = resp.get("total_missions", 0)
	var successful: int = resp.get("successful_missions", 0)
	var creator: String = resp.get("creator_name", "Unknown")

	_add_label("Skills: %d" % total_skills, Vector3(-2, 3.2, -5))
	_add_label("Ledger entries: %d" % total_entries, Vector3(2, 3.2, -5))
	_add_label("Missions: %d (%d successful)" % [total_missions, successful], Vector3(0, 2.7, -5))
	if creator:
		_add_label("Creator: %s" % creator, Vector3(0, 2.2, -5), Color("7ab892"))

	# Show first ledger entries on pedestals
	var first_entries: Array = resp.get("first_entries", [])
	for i in range(min(first_entries.size(), 5)):
		var entry: Dictionary = first_entries[i]
		var z := -10 + i * 5
		_add_label("#%d %s" % [entry.get("seq", 0), entry.get("action", "?")],
			Vector3(-2, 1.6, z), Color("c4a35a"))
		_add_label(entry.get("payload_summary", ""),
			Vector3(-2, 1.2, z), Color("78818a"))

func _load_evolution() -> void:
	var resp: Dictionary = _ipc.get_skill_versions("")
	if resp.has("error"):
		_show_offline()
		return
	_clear_labels()
	_add_label("HALL OF EVOLUTION", Vector3(0, 4.5, -5), Color("e1c77e"))
	_add_label("Skill Version History", Vector3(0, 4.0, -5), Color("c4a35a"))

	var skills: Array = resp.get("skills", [])
	for i in range(min(skills.size(), 10)):
		var skill: Dictionary = skills[i]
		var z := -10 + i * 2
		var name_str: String = skill.get("name", "?")
		var ver: int = skill.get("current_version", 0)
		var total_ver: int = skill.get("total_versions", 0)
		var model: String = skill.get("model", "?")
		_add_label("%s v%d (%d versions)" % [name_str, ver, total_ver],
			Vector3(-2, 1.6, z), Color("c4a35a"))
		_add_label("by %s" % model, Vector3(-2, 1.2, z), Color("78818a"))

func _load_architects() -> void:
	var resp: Dictionary = _ipc.get_constitution()
	if resp.has("error"):
		_show_offline()
		return
	_clear_labels()
	_add_label("HALL OF ARCHITECTS", Vector3(0, 4.5, -5), Color("e1c77e"))
	_add_label("The Constitution", Vector3(0, 4.0, -5), Color("c4a35a"))

	# Immutable laws
	var laws: Array = resp.get("immutable_laws", [])
	_add_label("Immutable Laws:", Vector3(0, 3.3, -5), Color("e1c77e"))
	for i in range(min(laws.size(), 8)):
		_add_label("  %s" % laws[i],
			Vector3(0, 2.9 - i * 0.35, -5), Color("7ab892"))

	# Change classes on pedestals
	var classes: Array = resp.get("change_classes", [])
	for i in range(min(classes.size(), 5)):
		var cc: Dictionary = classes[i]
		var z := -10 + i * 5
		var desc: String = cc.get("description", "")
		_add_label("%s (level %d)" % [cc.get("name", "?"), cc.get("value", 0)],
			Vector3(2, 1.6, z), Color("c4a35a"))
		_add_label(desc.substr(0, 60),
			Vector3(2, 1.2, z), Color("78818a"))

func _load_sovereignty() -> void:
	var resp: Dictionary = _ipc.get_constitution()
	if resp.has("error"):
		_show_offline()
		return
	_clear_labels()
	_add_label("HALL OF SOVEREIGNTY", Vector3(0, 4.5, -5), Color("e1c77e"))
	_add_label("Order of Authority", Vector3(0, 4.0, -5), Color("c4a35a"))

	var authorities: Array = resp.get("authorities", [])
	for i in range(min(authorities.size(), 7)):
		var auth: Dictionary = authorities[i]
		var z := -10 + i * 3.5
		var desc: String = auth.get("description", "")
		_add_label("%d. %s" % [auth.get("value", 0), auth.get("name", "?")],
			Vector3(-2, 1.6, z), Color("c4a35a"))
		_add_label(desc.substr(0, 60),
			Vector3(-2, 1.2, z), Color("78818a"))

func _load_memory() -> void:
	var resp: Dictionary = _ipc.get_ledger_entries(10, 0, "")
	if resp.has("error"):
		_show_offline()
		return
	_clear_labels()
	_add_label("HALL OF MEMORY", Vector3(0, 4.5, -5), Color("e1c77e"))
	_add_label("Evidence Ledger — Recent Entries", Vector3(0, 4.0, -5), Color("c4a35a"))

	var total: int = resp.get("total", 0)
	_add_label("Total entries: %d" % total, Vector3(0, 3.3, -5), Color("7ab892"))

	var entries: Array = resp.get("entries", [])
	for i in range(min(entries.size(), 10)):
		var entry: Dictionary = entries[i]
		var z := -10 + i * 2
		var summary: String = entry.get("payload_summary", "")
		_add_label("#%d %s" % [entry.get("seq", 0), entry.get("action", "?")],
			Vector3(-2, 1.6, z), Color("c4a35a"))
		_add_label(summary.substr(0, 50),
			Vector3(-2, 1.2, z), Color("78818a"))

func _load_creation() -> void:
	var resp: Dictionary = _ipc.get_mission_history()
	if resp.has("error"):
		_show_offline()
		return
	_clear_labels()
	_add_label("HALL OF CREATION", Vector3(0, 4.5, -5), Color("e1c77e"))
	_add_label("Mission Archive", Vector3(0, 4.0, -5), Color("c4a35a"))

	var missions: Array = resp.get("missions", [])
	var total: int = resp.get("total", 0)
	_add_label("Total missions: %d" % total, Vector3(0, 3.3, -5), Color("7ab892"))

	for i in range(min(missions.size(), 10)):
		var mission: Dictionary = missions[i]
		var z := -10 + i * 2
		var success: bool = mission.get("success", false)
		var status_str := "SUCCESS" if success else "FAILED"
		var color := Color("7ab892") if success else Color("8b3a3a")
		var task: String = mission.get("task", "")
		_add_label("%s: %s (%s)" % [status_str, mission.get("skill_name", "?"), task.substr(0, 40)],
			Vector3(-2, 1.6, z), color)
		_add_label("%d attempts" % mission.get("attempts", 0),
			Vector3(-2, 1.2, z), Color("78818a"))
