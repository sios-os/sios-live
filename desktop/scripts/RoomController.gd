## RoomController.gd — Base class for functional room controllers.
##
## Each room that has real functionality extends this. It provides:
##   - A reference to the IPC bridge
##   - A HUD panel for displaying information
##   - A loading/error state system
##   - Refresh on focus
extends Node3D

var _ipc: Node
var _hud_panel: PanelContainer
var _hud_label: Label
var _hud_scroll: ScrollContainer
var _loading: bool = false

func _ready() -> void:
	_ipc = get_node_or_null("/root/SIOSDesktop/IPCBridge")
	if _ipc == null:
		_ipc = get_node_or_null("../IPCBridge")
	if _ipc == null:
		var parent := get_parent()
		while parent != null:
			var found := parent.get_node_or_null("IPCBridge")
			if found != null:
				_ipc = found
				break
			parent = parent.get_parent()
	_build_hud()
	_on_room_enter()

func _build_hud() -> void:
	var canvas := CanvasLayer.new()
	canvas.name = "RoomCanvas"
	canvas.layer = 40
	add_child(canvas)
	_hud_scroll = ScrollContainer.new()
	_hud_scroll.position = Vector2(32, 120)
	_hud_scroll.custom_minimum_size = Vector2(600, 400)
	_hud_scroll.size = Vector2(600, 400)
	canvas.add_child(_hud_scroll)
	_hud_panel = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = SIOSBrand.COL_BG_PANEL
	sb.border_color = SIOSBrand.COL_LINE
	sb.set_border_width_all(1)
	sb.set_content_margin_all(16)
	_hud_panel.add_theme_stylebox_override("panel", sb)
	_hud_scroll.add_child(_hud_panel)
	_hud_label = Label.new()
	_hud_label.add_theme_font_size_override("font_size", 13)
	_hud_label.add_theme_color_override("font_color", SIOSBrand.COL_TEXT)
	_hud_label.custom_minimum_size = Vector2(560, 360)
	_hud_label.text = "Loading..."
	_hud_panel.add_child(_hud_label)

func _on_room_enter() -> void:
	# Override in subclasses
	pass

func _debug_ipc() -> void:
	var connected := false
	if _ipc != null:
		connected = _ipc.is_daemon_connected()
	print("[RoomController] IPC connected: %s" % connected)

func _set_loading(text: String = "Loading...") -> void:
	_loading = true
	_hud_label.text = text

func _set_content(text: String) -> void:
	_loading = false
	_hud_label.text = text

func _set_error(text: String) -> void:
	_loading = false
	_hud_label.text = "[ERROR] " + text

func _ipc_call(method: String, args: Array = []) -> Dictionary:
	if _ipc == null or not _ipc.is_daemon_connected():
		return {"error": "ANUBIS daemon not connected"}
	return _ipc.callv(method, args)

func _format_dict(d: Dictionary, indent: String = "") -> String:
	var lines: Array[String] = []
	for key in d.keys():
		var val = d[key]
		if typeof(val) == TYPE_DICTIONARY:
			lines.append("%s%s:" % [indent, key])
			lines.append(_format_dict(val, indent + "  "))
		elif typeof(val) == TYPE_ARRAY:
			lines.append("%s%s: [%d items]" % [indent, key, val.size()])
		else:
			lines.append("%s%s: %s" % [indent, key, str(val)])
	return "\n".join(lines)
