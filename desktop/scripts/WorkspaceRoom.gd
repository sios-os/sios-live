## WorkspaceRoom.gd — The Workspace room controller.
##
## This is where ANUBIS writes and tests code. The Creator can:
##   - See the current skill library
##   - Propose a new mission (task description + skill name)
##   - Approve the mission (consequential action requires Creator authority)
##   - Watch the mission progress in real time
##   - See the result (promoted or failed)
##
## The mission runs asynchronously in the ANUBIS daemon. This controller
## polls for status updates.
extends "res://scripts/RoomController.gd"

const MISSION_PRESETS := [
	{"name": "slugify", "task": "Convert a string to a URL-safe slug: lowercase, replace non-alphanumeric runs with hyphens, strip leading/trailing hyphens."},
	{"name": "camel_to_snake", "task": "Convert a camelCase string to snake_case."},
	{"name": "word_count", "task": "Count the number of words in a string. Words are separated by whitespace. Return an integer."},
	{"name": "is_palindrome", "task": "Check if a string is a palindrome. Case insensitive, ignore spaces and punctuation. Return bool."},
]

var _selected_preset: int = 0
var _mission_active: bool = false
var _mission_id: String = ""
var _poll_timer: float = 0.0
var _input_panel: PanelContainer
var _task_edit: LineEdit
var _name_edit: LineEdit
var _status_label: Label

func _on_room_enter() -> void:
	_build_input_panel()
	_refresh_skills()

func _build_input_panel() -> void:
	if _input_panel != null:
		return
	var canvas := get_node("RoomCanvas")
	_input_panel = PanelContainer.new()
	_input_panel.position = Vector2(650, 120)
	_input_panel.custom_minimum_size = Vector2(400, 400)
	var sb := StyleBoxFlat.new()
	sb.bg_color = SIOSBrand.COL_BG_PANEL
	sb.border_color = SIOSBrand.COL_LINE
	sb.set_border_width_all(1)
	sb.set_content_margin_all(16)
	_input_panel.add_theme_stylebox_override("panel", sb)
	canvas.add_child(_input_panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 12)
	_input_panel.add_child(vbox)

	var title := SIOSBrand.make_label("NEW MISSION", 16, SIOSBrand.COL_GOLD_BRIGHT)
	vbox.add_child(title)

	var hint := SIOSBrand.make_label(
		"Describe a capability for ANUBIS to build.\nHe will write the code, test it in the\nsandbox, and promote it if it passes.",
		11, SIOSBrand.COL_MUTED)
	vbox.add_child(hint)

	# Preset selector
	var preset_label := SIOSBrand.make_label("Presets:", 12, SIOSBrand.COL_TEXT)
	vbox.add_child(preset_label)
	for i in range(MISSION_PRESETS.size()):
		var btn := Button.new()
		btn.text = MISSION_PRESETS[i].name
		btn.add_theme_font_size_override("font_size", 11)
		btn.custom_minimum_size = Vector2(360, 28)
		btn.pressed.connect(func(): _select_preset(i))
		vbox.add_child(btn)

	# Skill name input
	var name_label := SIOSBrand.make_label("Skill name:", 12, SIOSBrand.COL_TEXT)
	vbox.add_child(name_label)
	_name_edit = LineEdit.new()
	_name_edit.placeholder_text = "e.g. slugify"
	_name_edit.add_theme_font_size_override("font_size", 12)
	vbox.add_child(_name_edit)

	# Task description input
	var task_label := SIOSBrand.make_label("Task description:", 12, SIOSBrand.COL_TEXT)
	vbox.add_child(task_label)
	_task_edit = LineEdit.new()
	_task_edit.placeholder_text = "Describe what the function should do..."
	_task_edit.add_theme_font_size_override("font_size", 12)
	_task_edit.custom_minimum_size = Vector2(360, 60)
	vbox.add_child(_task_edit)

	# Launch button
	var launch_btn := Button.new()
	launch_btn.text = "LAUNCH MISSION"
	launch_btn.add_theme_font_size_override("font_size", 13)
	launch_btn.add_theme_color_override("font_color", SIOSBrand.COL_GOLD_BRIGHT)
	launch_btn.custom_minimum_size = Vector2(360, 40)
	launch_btn.pressed.connect(_launch_mission)
	vbox.add_child(launch_btn)

	# Status
	_status_label = SIOSBrand.make_label("", 11, SIOSBrand.COL_MUTED)
	_status_label.custom_minimum_size = Vector2(360, 80)
	vbox.add_child(_status_label)

func _select_preset(i: int) -> void:
	_selected_preset = i
	_name_edit.text = MISSION_PRESETS[i].name
	_task_edit.text = MISSION_PRESETS[i].task

func _refresh_skills() -> void:
	_set_loading("Loading skill library...")
	var r := _ipc_call("get_skills")
	if r.has("error"):
		_set_error(r["error"])
		return
	var skills: Array = r.get("skills", [])
	if skills.is_empty():
		_set_content("No skills promoted yet.\n\nLaunch a mission below to have\nANUBIS write his first capability.")
		return
	var text := "SKILL LIBRARY (%d promoted)\n\n" % r.get("count", 0)
	for s in skills:
		text += "%s v%d\n" % [s["name"], s["version"]]
		text += "  hash: %s...\n" % str(s["artifact_hash"]).substr(0, 16)
		text += "  model: %s  attempt: #%d\n\n" % [s["model"], s["attempt"]]
	_set_content(text)

func _launch_mission() -> void:
	if _mission_active:
		_status_label.text = "Mission already in progress..."
		return
	var skill_name := _name_edit.text.strip_edges()
	var task := _task_edit.text.strip_edges()
	if skill_name.is_empty() or task.is_empty():
		_status_label.text = "Enter both a skill name and task description."
		return
	_status_label.text = "Requesting Creator approval..."
	# In the real system, this shows an approval dialog.
	# For now, the Creator clicks the button, which IS the approval.
	var approval := "creator-approved"
	_status_label.text = "Submitting mission to ANUBIS..."
	var r := _ipc_call("request_mission", [task, skill_name, approval])
	if r.has("error"):
		_status_label.text = "ERROR: " + str(r["error"])
		return
	_mission_id = r.get("mission_id", "")
	_mission_active = true
	_poll_timer = 0.0
	_status_label.text = "Mission started: %s\nANUBIS is working..." % _mission_id

func _process(delta: float) -> void:
	if not _mission_active:
		return
	_poll_timer += delta
	if _poll_timer < 2.0:
		return
	_poll_timer = 0.0
	var r := _ipc_call("get_mission_status", [_mission_id])
	if r.has("error"):
		_status_label.text = "Poll error: " + str(r["error"])
		return
	var status := str(r.get("status", "?"))
	match status:
		"running":
			_status_label.text = "ANUBIS is working...\n(attempt in progress)"
		"complete":
			_mission_active = false
			_status_label.text = "PROMOTED!\n%s\nattempts: %d\nduration: %ss" % [
				r.get("skill_name", "?"),
				r.get("attempts", 0),
				r.get("duration_s", 0)
			]
			_refresh_skills()
		"failed":
			_mission_active = false
			_status_label.text = "NOT PROMOTED\n%s\nattempts: %d\nreason: %s" % [
				r.get("skill_name", "?"),
				r.get("attempts", 0),
				r.get("denied_reason", "?")
			]
			_refresh_skills()
		"error":
			_mission_active = false
			_status_label.text = "ERROR: " + str(r.get("error", "?"))
