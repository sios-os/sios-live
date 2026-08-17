## SIOSDesktop.gd — Main desktop controller.
##
## This is the root of the SIOS spatial desktop. It manages:
##   - The hub view (room selection)
##   - Room loading and unloading
##   - Camera movement between rooms
##   - The HUD overlay (brand, status, navigation)
##   - Safe mode and reduced motion
##   - IPC hooks to the ANUBIS daemon (via local socket)
##
## The desktop starts at the boot screen, transitions to the hub, and from
## there the user can travel to any room they have access to.
extends Node3D

const RoomBuilder = preload("res://scripts/RoomBuilder.gd")
const IPCBridge = preload("res://scripts/IPCBridge.gd")
const DemonPanel = preload("res://scripts/DemonPanel.gd")
const WorkspaceTools = preload("res://scripts/WorkspaceTools.gd")

const ROOM_CONTROLLERS := {
	"workspace": "res://scripts/WorkspaceRoom.gd",
	"forge": "res://scripts/ForgeRoom.gd",
	"observatory": "res://scripts/ObservatoryRoom.gd",
	"command_chamber": "res://scripts/CommandRoom.gd",
	"sanctum": "res://scripts/SanctumRoom.gd",
	"tomb_entrance": "res://scripts/TombEntranceRoom.gd",
	"hall_of_genesis": "res://scripts/TombHall.gd",
	"hall_of_evolution": "res://scripts/TombHall.gd",
	"hall_of_architects": "res://scripts/TombHall.gd",
	"hall_of_sovereignty": "res://scripts/TombHall.gd",
	"hall_of_memory": "res://scripts/TombHall.gd",
	"hall_of_creation": "res://scripts/TombHall.gd",
	"the_throne": "res://scripts/ThroneRoom.gd",
	"mission_queue": "res://scripts/MissionQueuePanel.gd",
	"court": "res://scripts/CourtPanel.gd",
	"project_workspace": "res://scripts/ProjectWorkspacePanel.gd",
	"knowledge_browser": "res://scripts/KnowledgeBrowserPanel.gd",
}

var _builder: Node
var _portal: CanvasLayer
var _hud: CanvasLayer
var _safe_mode: Control
var _hud_label: Label
var _hud_title: Label
var _camera: Camera3D
var _current_room: Node3D
var _current_room_id: String = ""
var _hub: Node3D
var _reduced_motion: bool = false
var _creator_authenticated: bool = false
var _anubis_ipc: Node
var _demon_panel: Control
var _demon_visible: bool = false
var _workspace_tools: Control
var _semantic_time: float = 0.0

func _ready() -> void:
	_builder = RoomBuilder.new()
	add_child(_builder)
	# IPC bridge as a child node
	_anubis_ipc = IPCBridge.new()
	_anubis_ipc.name = "IPCBridge"
	add_child(_anubis_ipc)
	_portal = $PortalTransition
	_portal.set_reduced_motion(false)
	_portal.transition_complete.connect(_on_portal_complete)
	_build_hud()
	_build_safe_mode()
	_build_camera()
	_build_hub()
	_build_demon_panel()
	_build_workspace_tools()
	_show_hud("SIOS HUB", "Select a room to travel  |  Press D for DEMON")

func _process(delta: float) -> void:
	_semantic_time += delta
	if _current_room and not _reduced_motion:
		_animate_room(delta)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("toggle_safe_mode"):
		_safe_mode.visible = not _safe_mode.visible
	elif event.is_action_pressed("toggle_reduced_motion"):
		_reduced_motion = not _reduced_motion
		_portal.set_reduced_motion(_reduced_motion)
		_show_hud("SIOS", "Reduced motion %s" % ("ON" if _reduced_motion else "OFF"))
	elif event.is_action_pressed("return_to_hub"):
		if _current_room_id != "":
			_travel_to("")
	elif event.is_action_pressed("invoke_demon"):
		_invoke_demon()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_handle_click(event)

func _handle_click(event: InputEventMouseButton) -> void:
	# If a workspace tool panel is open, don't intercept clicks
	if _workspace_tools != null and _workspace_tools.visible:
		return
	if _demon_panel != null and _demon_panel.visible:
		return
	# Handle clicks inside rooms (e.g. Workspace stations)
	if _current_room_id != "":
		_handle_room_click(event)
		return
	if not _hub.visible:
		return
	# Raycast from camera through the click point
	var mouse_pos := event.position
	var from := _camera.project_ray_origin(mouse_pos)
	var dir := _camera.project_ray_normal(mouse_pos)
	var space_state := get_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(from, from + dir * 100.0)
	var result := space_state.intersect_ray(query)
	if result.is_empty():
		return
	var collider = result["collider"]
	# Check if we hit a portal door (StaticBody3D or MeshInstance3D)
	var room_id := ""
	if collider is StaticBody3D:
		room_id = collider.get_meta("room_id", "")
	elif collider is MeshInstance3D:
		room_id = collider.get_meta("room_id", "")
	if room_id != "":
		_travel_to(room_id)

func _handle_room_click(event: InputEventMouseButton) -> void:
	# Raycast into the room to find clicked stations
	var mouse_pos := event.position
	var from := _camera.project_ray_origin(mouse_pos)
	var dir := _camera.project_ray_normal(mouse_pos)
	var space_state := get_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(from, from + dir * 100.0)
	var result := space_state.intersect_ray(query)
	if result.is_empty():
		return
	var collider = result["collider"]
	# Check for station metadata
	var station_id := ""
	if collider is MeshInstance3D:
		station_id = collider.get_meta("station_id", "")
	# Handle Workspace room stations
	if _current_room_id == "workspace" and station_id != "":
		match station_id:
			"ST_WS_EDITOR":
				_workspace_tools.show_editor()
			"ST_WS_TERMINAL":
				_workspace_tools.show_terminal()
			"ST_WS_SANDBOX", "ST_WS_SKILLS", "ST_WS_MISSIONS":
				_workspace_tools.show_files()
			_:
				_workspace_tools.show_files()

# ------------------------------------------------------------------ hub

func _build_hub() -> void:
	_hub = Node3D.new()
	_hub.name = "HUB"
	_hub.add_child(_builder._environment(SIOSBrand.COL_BG_DEEP, SIOSBrand.COL_AMBIENT, 0.5))
	# Central platform
	_hub.add_child(_builder._cylinder("AS_HUB_PLATFORM", 6.0, 0.3, Vector3(0, 0.15, 0),
		SIOSBrand.mat_dais))
	# ANUBIS core in the center
	_hub.add_child(_builder._cylinder("AS_HUB_ANUBIS", 0.8, 3.5, Vector3(0, 2.0, 0),
		SIOSBrand.mat_gold))
	# Portal doors around the hub — one per room
	for i in range(SIOSBrand.ROOMS.size()):
		var room = SIOSBrand.ROOMS[i]
		var angle := TAU * float(i) / float(SIOSBrand.ROOMS.size())
		var radius := 12.0
		var pos := Vector3(radius * cos(angle), 1.5, -radius * sin(angle))
		var door: MeshInstance3D = _builder._box("PORTAL_%s" % room.id, Vector3(3, 4, 0.4), pos,
			SIOSBrand.mat_station)
		door.rotation.y = -angle + PI / 2.0
		door.set_meta("room_id", room.id)
		door.set_meta("room_name", room.name)
		door.set_meta("room_access", room.access)
		_hub.add_child(door)
		# Collision body so raycasts can hit the door
		var body := StaticBody3D.new()
		body.name = "PORTAL_BODY_%s" % room.id
		body.position = pos
		body.rotation.y = -angle + PI / 2.0
		var shape := BoxShape3D.new()
		shape.size = Vector3(3, 4, 0.4)
		var col := CollisionShape3D.new()
		col.shape = shape
		body.add_child(col)
		body.set_meta("room_id", room.id)
		_hub.add_child(body)
		# Label above each door
		var label3d := Label3D.new()
		label3d.text = room.name.to_upper()
		label3d.position = Vector3(pos.x, 4.0, pos.z)
		label3d.rotation.y = -angle + PI / 2.0
		label3d.font_size = 48
		label3d.modulate = SIOSBrand.COL_GOLD_BRIGHT
		label3d.outline_modulate = SIOSBrand.COL_BG_DEEP
		label3d.outline_size = 8
		label3d.pixel_size = 0.01
		label3d.billboard = BaseMaterial3D.BILLBOARD_DISABLED
		_hub.add_child(label3d)
		# Gold accent ring on the floor before each door
		_hub.add_child(_builder._cylinder("AS_HUB_RING_%s" % room.id, 1.5, 0.05,
			Vector3(pos.x * 0.7, 0.05, pos.z * 0.7),
			SIOSBrand.mat_gold_emissive))
	add_child(_hub)

# ------------------------------------------------------------------ camera

func _build_camera() -> void:
	_camera = Camera3D.new()
	_camera.name = "CAM_MAIN"
	_camera.position = Vector3(0, 3, 8)
	_camera.rotation_degrees.x = -15
	add_child(_camera)

func _focus_camera_on(pos: Vector3, duration: float = 0.5) -> void:
	if _reduced_motion:
		_camera.position = pos
		return
	var tween := create_tween()
	tween.tween_property(_camera, "position", pos, duration) \
		.set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)

# ------------------------------------------------------------------ travel

func _travel_to(room_id: String) -> void:
	if room_id == _current_room_id:
		return
	# Check access
	if room_id != "" and SIOSBrand.is_creator_room(room_id) and not _creator_authenticated:
		_show_hud("ACCESS DENIED", "%s requires Creator authority" % SIOSBrand.room_by_id(room_id).name)
		return
	_portal.travel(room_id)

func _on_portal_complete(room_id: String) -> void:
	# Remove current room
	if _current_room:
		_current_room.queue_free()
		_current_room = null
		_current_room_id = ""
	if room_id == "":
		# Return to hub
		_hub.visible = true
		_show_hud("SIOS HUB", "Select a room to travel")
		_focus_camera_on(Vector3(0, 3, 8))
		return
	# Hide hub, load new room
	_hub.visible = false
	_current_room = _builder.build_room(room_id)
	_current_room_id = room_id
	add_child(_current_room)
	# Attach a room controller if one exists for this room
	if ROOM_CONTROLLERS.has(room_id):
		var script := load(ROOM_CONTROLLERS[room_id]) as GDScript
		if script != null:
			var controller := Node3D.new()
			controller.name = "RoomController"
			controller.set_script(script)
			_current_room.add_child(controller)
	var room = SIOSBrand.room_by_id(room_id)
	_show_hud(room.name, _room_subtitle(room_id))
	_focus_camera_on(Vector3(0, 3, 6))

func _room_subtitle(room_id: String) -> String:
	match room_id:
		"workspace":
			return "Where ANUBIS writes and tests code"
		"command_chamber":
			return "System oversight and control"
		"observatory":
			return "External data and observation"
		"sanctum":
			return "Personalization and identity"
		"forge":
			return "Build, test, package, and sign"
		"tomb_entrance":
			return "Creator-only boundary"
		"mission_queue":
			return "Autonomous mission queue"
		"court":
			return "Governance and constitutional review"
		"project_workspace":
			return "Multi-file project builder"
		"knowledge_browser":
			return "Governed knowledge library"
		_:
			return room_id.replace("_", " ").capitalize()

# ------------------------------------------------------------------ HUD

func _build_hud() -> void:
	_hud = CanvasLayer.new()
	_hud.layer = 50
	add_child(_hud)
	# Title
	_hud_title = SIOSBrand.make_label("SIOS", 28, SIOSBrand.COL_GOLD_BRIGHT)
	_hud_title.position = Vector2(32, 24)
	_hud.add_child(_hud_title)
	# Status line
	_hud_label = SIOSBrand.make_label("", 14, SIOSBrand.COL_MUTED)
	_hud_label.position = Vector2(32, 60)
	_hud.add_child(_hud_label)
	# Brand mark (hexagonal)
	_build_brand_mark()
	# Navigation hint
	var hint := SIOSBrand.make_label(
		"ESC Return to Hub  ·  F1 Safe Mode  ·  M Reduced Motion  ·  D DEMON",
		11, SIOSBrand.COL_GOLD_DIM)
	hint.position = Vector2(32, 88)
	_hud.add_child(hint)

func _build_brand_mark() -> void:
	var mark := Control.new()
	mark.position = Vector2(get_viewport().get_visible_rect().size.x - 80, 24)
	mark.size = Vector2(48, 48)
	# Draw the hex outline
	var line := Line2D.new()
	for i in range(7):
		var a := TAU * float(i % 6) / 6.0 + PI / 6.0
		line.add_point(Vector2(24 + 22 * cos(a), 24 + 22 * sin(a)))
	line.default_color = SIOSBrand.COL_GOLD
	line.width = 2.0
	mark.add_child(line)
	# Letter S
	var letter := SIOSBrand.make_label("S", 24, SIOSBrand.COL_GOLD_BRIGHT)
	letter.position = Vector2(16, 8)
	letter.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mark.add_child(letter)
	_hud.add_child(mark)

func _show_hud(title: String, subtitle: String) -> void:
	_hud_title.text = title
	_hud_label.text = subtitle

# ------------------------------------------------------------------ safe mode

func _build_safe_mode() -> void:
	_safe_mode = PanelContainer.new()
	_safe_mode.name = "SAFE_MODE"
	_safe_mode.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_safe_mode.visible = false
	var sb := StyleBoxFlat.new()
	sb.bg_color = SIOSBrand.COL_BG_DEEP
	_safe_mode.add_theme_stylebox_override("panel", sb)
	var label := SIOSBrand.make_label(
		"SIOS — SAFE MODE\n\nAll controls remain keyboard-operable and local.\nF1 returns to the spatial view.",
		16, SIOSBrand.COL_TEXT)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_safe_mode.add_child(label)
	_hud.add_child(_safe_mode)

# ------------------------------------------------------------------ ANUBIS IPC

func _invoke_demon() -> void:
	_demon_visible = not _demon_visible
	if _demon_visible:
		_demon_panel.show_panel()
		_show_hud("DEMON", "Conversational interface — talk to ANUBIS")
	else:
		_demon_panel.hide_panel()
		_show_hud("SIOS", "DEMON closed")

func _build_demon_panel() -> void:
	_demon_panel = DemonPanel.new()
	_demon_panel.name = "DemonPanel"
	_demon_panel.visible = false
	_hud.add_child(_demon_panel)

func _build_workspace_tools() -> void:
	_workspace_tools = WorkspaceTools.new()
	_workspace_tools.name = "WorkspaceTools"
	_workspace_tools.visible = false
	_hud.add_child(_workspace_tools)

# ------------------------------------------------------------------ animation

func _animate_room(delta: float) -> void:
	# Gentle rotation of any ANUBIS core or crystal in the room
	for child in _current_room.get_children():
		if child is MeshInstance3D:
			var n := child.name
			if n.contains("ANUBIS") or n.contains("CRYSTAL"):
				child.rotate_y(delta * 0.3)
