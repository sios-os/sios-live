## ScreenshotCapture.gd — Captures screenshots of the desktop at intervals.
extends Node

const SHOTS := [
	{"path": "user://shot-hub.png", "delay": 3.0, "label": "HUB"},
	{"path": "user://shot-workspace.png", "delay": 7.0, "label": "WORKSPACE", "room": "workspace"},
	{"path": "user://shot-forge.png", "delay": 12.0, "label": "FORGE", "room": "forge"},
	{"path": "user://shot-observatory.png", "delay": 17.0, "label": "OBSERVATORY", "room": "observatory"},
	{"path": "user://shot-command.png", "delay": 22.0, "label": "COMMAND", "room": "command_chamber"},
]

var _desktop: Node
var _shot_index: int = 0
var _timer: float = 0.0
var _captured: bool = false

func _ready() -> void:
	_desktop = get_parent()
	_timer = 0.0

func _process(delta: float) -> void:
	_timer += delta
	if _shot_index >= SHOTS.size():
		get_tree().quit()
		return
	if _captured:
		return
	var shot = SHOTS[_shot_index]
	if _timer >= shot.delay:
		_captured = true
		# Navigate to the room if specified
		if shot.has("room") and _desktop.has_method("_travel_to"):
			_desktop._travel_to(shot.room)
			# Wait for portal transition + room load
			await get_tree().create_timer(2.0).timeout
		# Capture
		var img := get_viewport().get_texture().get_image()
		var err := img.save_png(shot.path)
		if err == OK:
			print("Screenshot: %s -> %s" % [shot.label, ProjectSettings.globalize_path(shot.path)])
		else:
			print("Screenshot failed: %s (error %d)" % [shot.label, err])
		_shot_index += 1
		_captured = false
