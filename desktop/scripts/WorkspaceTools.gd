## WorkspaceTools.gd — File browser, text editor, and terminal for the Workspace room.
##
## This panel provides three tools accessible from the Workspace stations:
##   - File Browser: navigate directories, open files
##   - Text Editor:  view and edit files, save with Creator approval
##   - Terminal:     run shell commands with Creator approval
##
## The panel is shown as a 2D overlay when the Creator clicks a station.
extends Control

const DEFAULT_PATH := "/mnt/d/SIOS-Build/sios-live"

var _ipc: Node
var _current_path: String = DEFAULT_PATH
var _current_file: String = ""
var _mode: String = "files"  # "files", "editor", "terminal"
var _file_dirty: bool = false

# UI elements
var _panel: PanelContainer
var _title_bar: HBoxContainer
var _title_label: Label
var _close_button: Button
var _content_area: Control
var _status_label: Label

# File browser
var _path_label: Label
var _file_list: ItemList
var _up_button: Button

# Text editor
var _editor_path_label: Label
var _editor_text: TextEdit
var _save_button: Button
var _new_button: Button

# Terminal
var _terminal_output: RichTextLabel
var _terminal_input: LineEdit
var _terminal_run_button: Button
var _terminal_history: Array[String] = []
var _terminal_history_idx: int = -1

signal close_requested()

func _ready() -> void:
	_ipc = get_node_or_null("/root/SIOSDesktop/IPCBridge")
	_build_ui()

func _build_ui() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	custom_minimum_size = Vector2(500, 400)

	_panel = PanelContainer.new()
	_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("02070d")
	sb.border_color = Color("c4a35a")
	sb.set_border_width_all(1)
	sb.set_content_margin_all(4)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 4)
	_panel.add_child(vbox)

	# Title bar
	_title_bar = HBoxContainer.new()
	_title_bar.custom_minimum_size = Vector2(0, 28)
	vbox.add_child(_title_bar)

	_title_label = Label.new()
	_title_label.text = "Workspace Tools"
	_title_label.add_theme_color_override("font_color", Color("e1c77e"))
	_title_label.add_theme_font_size_override("font_size", 16)
	_title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_title_bar.add_child(_title_label)

	_close_button = Button.new()
	_close_button.text = "X"
	_close_button.custom_minimum_size = Vector2(28, 0)
	_close_button.pressed.connect(_on_close)
	_title_bar.add_child(_close_button)

	# Mode tabs
	var tabs := HBoxContainer.new()
	tabs.custom_minimum_size = Vector2(0, 28)
	vbox.add_child(tabs)

	var btn_files := Button.new()
	btn_files.text = "Files"
	btn_files.custom_minimum_size = Vector2(80, 0)
	btn_files.pressed.connect(func(): _set_mode("files"))
	tabs.add_child(btn_files)

	var btn_editor := Button.new()
	btn_editor.text = "Editor"
	btn_editor.custom_minimum_size = Vector2(80, 0)
	btn_editor.pressed.connect(func(): _set_mode("editor"))
	tabs.add_child(btn_editor)

	var btn_term := Button.new()
	btn_term.text = "Terminal"
	btn_term.custom_minimum_size = Vector2(80, 0)
	btn_term.pressed.connect(func(): _set_mode("terminal"))
	tabs.add_child(btn_term)

	# Content area (switches based on mode)
	_content_area = Control.new()
	_content_area.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vbox.add_child(_content_area)

	# Status bar
	_status_label = Label.new()
	_status_label.text = "Ready"
	_status_label.add_theme_color_override("font_color", Color("78818a"))
	_status_label.add_theme_font_size_override("font_size", 11)
	vbox.add_child(_status_label)

	# Build each mode's UI
	_build_file_browser()
	_build_text_editor()
	_build_terminal()

	_set_mode("files")

# ------------------------------------------------------------------ file browser

func _build_file_browser() -> void:
	var container := VBoxContainer.new()
	container.set_anchors_preset(Control.PRESET_FULL_RECT)
	container.visible = false
	_content_area.add_child(container)

	var nav := HBoxContainer.new()
	nav.custom_minimum_size = Vector2(0, 26)
	container.add_child(nav)

	_up_button = Button.new()
	_up_button.text = "Up"
	_up_button.custom_minimum_size = Vector2(50, 0)
	_up_button.pressed.connect(_on_go_up)
	nav.add_child(_up_button)

	_path_label = Label.new()
	_path_label.text = DEFAULT_PATH
	_path_label.add_theme_color_override("font_color", Color("c4a35a"))
	_path_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	nav.add_child(_path_label)

	var refresh_btn := Button.new()
	refresh_btn.text = "Refresh"
	refresh_btn.custom_minimum_size = Vector2(70, 0)
	refresh_btn.pressed.connect(_refresh_files)
	nav.add_child(refresh_btn)

	_file_list = ItemList.new()
	_file_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_file_list.item_activated.connect(_on_file_activated)
	_file_list.item_selected.connect(_on_file_selected)
	container.add_child(_file_list)

	var open_btn := Button.new()
	open_btn.text = "Open"
	open_btn.custom_minimum_size = Vector2(0, 28)
	open_btn.pressed.connect(_on_open_file)
	container.add_child(open_btn)

func _refresh_files() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_status_label.text = "ANUBIS offline"
		return
	_status_label.text = "Loading..."
	var resp: Dictionary = _ipc.fs_list(_current_path)
	if resp.has("error"):
		_status_label.text = "Error: " + resp["error"]
		return
	_path_label.text = resp.get("path", _current_path)
	_file_list.clear()
	var entries: Array = resp.get("entries", [])
	for entry in entries:
		var name: String = entry["name"]
		if entry["is_dir"]:
			name = "[DIR] " + name
		_file_list.add_item(name)
	_status_label.text = "%d items" % entries.size()

func _on_go_up() -> void:
	var parent := _current_path.get_base_dir()
	if parent != _current_path:
		_current_path = parent
		_refresh_files()

func _on_file_selected(idx: int) -> void:
	# Just update status
	if idx >= 0:
		var item_text: String = _file_list.get_item_text(idx)
		_status_label.text = item_text

func _on_file_activated(idx: int) -> void:
	_on_open_file()

func _on_open_file() -> void:
	var idx := _file_list.get_selected_items()
	if idx.size() == 0:
		return
	var item_text: String = _file_list.get_item_text(idx[0])
	var name_str: String = item_text.replace("[DIR] ", "")
	var full_path: String = _current_path + "/" + name_str
	if item_text.begins_with("[DIR]"):
		_current_path = full_path
		_refresh_files()
	else:
		_current_file = full_path
		_open_file_in_editor(full_path)

# ------------------------------------------------------------------ text editor

func _build_text_editor() -> void:
	var container := VBoxContainer.new()
	container.set_anchors_preset(Control.PRESET_FULL_RECT)
	container.visible = false
	_content_area.add_child(container)

	_editor_path_label = Label.new()
	_editor_path_label.text = "(no file open)"
	_editor_path_label.add_theme_color_override("font_color", Color("c4a35a"))
	container.add_child(_editor_path_label)

	_editor_text = TextEdit.new()
	_editor_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_editor_text.add_theme_color_override("font_color", Color("e9edf0"))
	_editor_text.add_theme_color_override("background_color", Color("0a0f14"))
	var ed_sb := StyleBoxFlat.new()
	ed_sb.bg_color = Color("0a0f14")
	ed_sb.border_color = Color("282d32")
	ed_sb.set_border_width_all(1)
	_editor_text.add_theme_stylebox_override("normal", ed_sb)
	_editor_text.syntax_highlighter = CodeHighlighter.new()
	_editor_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	_editor_text.text_changed.connect(_on_editor_changed)
	container.add_child(_editor_text)

	var btn_row := HBoxContainer.new()
	btn_row.custom_minimum_size = Vector2(0, 28)
	container.add_child(btn_row)

	_new_button = Button.new()
	_new_button.text = "New"
	_new_button.custom_minimum_size = Vector2(60, 0)
	_new_button.pressed.connect(_on_new_file)
	btn_row.add_child(_new_button)

	_save_button = Button.new()
	_save_button.text = "Save"
	_save_button.custom_minimum_size = Vector2(60, 0)
	_save_button.pressed.connect(_on_save_file)
	btn_row.add_child(_save_button)

func _on_editor_changed() -> void:
	_file_dirty = true
	_status_label.text = "Modified"

func _open_file_in_editor(path: String) -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_status_label.text = "ANUBIS offline"
		return
	_status_label.text = "Loading file..."
	var resp: Dictionary = _ipc.fs_read(path)
	if resp.has("error"):
		_status_label.text = "Error: " + resp["error"]
		return
	_editor_text.text = resp.get("content", "")
	_editor_path_label.text = path
	_current_file = path
	_file_dirty = false
	_status_label.text = "Loaded %d bytes" % resp.get("size", 0)
	_set_mode("editor")

func _on_new_file() -> void:
	_editor_text.text = ""
	_editor_path_label.text = "(new file)"
	_current_file = ""
	_file_dirty = false
	_status_label.text = "New file"

func _on_save_file() -> void:
	if _current_file == "":
		_status_label.text = "No file path set"
		return
	if _ipc == null or not _ipc.is_daemon_connected():
		_status_label.text = "ANUBIS offline"
		return
	# Save uses creator-approved token (the Creator clicking Save IS the approval)
	var resp: Dictionary = _ipc.fs_write(_current_file, _editor_text.text, "creator-approved")
	if resp.has("error"):
		_status_label.text = "Error: " + resp["error"]
	else:
		_file_dirty = false
		_status_label.text = "Saved %d bytes" % resp.get("size", 0)

# ------------------------------------------------------------------ terminal

func _build_terminal() -> void:
	var container := VBoxContainer.new()
	container.set_anchors_preset(Control.PRESET_FULL_RECT)
	container.visible = false
	_content_area.add_child(container)

	_terminal_output = RichTextLabel.new()
	_terminal_output.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_terminal_output.bbcode_enabled = true
	_terminal_output.add_theme_color_override("default_color", Color("7ab892"))
	var term_sb := StyleBoxFlat.new()
	term_sb.bg_color = Color("0a0f14")
	term_sb.border_color = Color("282d32")
	term_sb.set_border_width_all(1)
	_terminal_output.add_theme_stylebox_override("normal", term_sb)
	_terminal_output.text = "[color=#78818a]SIOS Terminal — commands run with Creator authority\nType 'help' for quick reference.[/color]\n"
	container.add_child(_terminal_output)

	var input_row := HBoxContainer.new()
	input_row.custom_minimum_size = Vector2(0, 28)
	container.add_child(input_row)

	_terminal_input = LineEdit.new()
	_terminal_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_terminal_input.placeholder_text = "Enter command..."
	_terminal_input.add_theme_color_override("font_color", Color("e9edf0"))
	var in_sb := StyleBoxFlat.new()
	in_sb.bg_color = Color("111419")
	in_sb.border_color = Color("282d32")
	in_sb.set_border_width_all(1)
	_terminal_input.add_theme_stylebox_override("normal", in_sb)
	_terminal_input.text_submitted.connect(_on_terminal_run)
	input_row.add_child(_terminal_input)

	_terminal_run_button = Button.new()
	_terminal_run_button.text = "Run"
	_terminal_run_button.custom_minimum_size = Vector2(60, 0)
	_terminal_run_button.pressed.connect(_on_terminal_run_pressed)
	input_row.add_child(_terminal_run_button)

func _on_terminal_run_pressed() -> void:
	_on_terminal_run(_terminal_input.text)

func _on_terminal_run(text: String) -> void:
	text = text.strip_edges()
	if text.is_empty():
		return
	# History
	_terminal_history.append(text)
	_terminal_history_idx = _terminal_history.size()
	_terminal_input.text = ""

	# Show command
	_terminal_output.append_text("[color=#e1c77e]$ %s[/color]\n" % text)

	if text == "help":
		_terminal_output.append_text("Commands run with Creator authority.\n")
		_terminal_output.append_text("  ls, pwd, cat, python3, git, etc.\n")
		_terminal_output.append_text("  Up/Down arrows: command history\n")
		_terminal_output.scroll_to_line(_terminal_output.get_line_count())
		return

	if text == "clear":
		_terminal_output.text = ""
		return

	# Run via daemon
	if _ipc == null or not _ipc.is_daemon_connected():
		_terminal_output.append_text("[color=#8b3a3a]ANUBIS offline[/color]\n")
		return

	_status_label.text = "Running..."
	var resp: Dictionary = _ipc.run_cmd(text, "creator-approved")
	if resp.has("error"):
		_terminal_output.append_text("[color=#8b3a3a]Error: %s[/color]\n" % resp["error"])
	else:
		var stdout: String = resp.get("stdout", "")
		var stderr: String = resp.get("stderr", "")
		var exit_code: int = resp.get("exit_code", 0)
		if stdout:
			_terminal_output.append_text("[color=#e9edf0]%s[/color]\n" % stdout)
		if stderr:
			_terminal_output.append_text("[color=#8b3a3a]%s[/color]\n" % stderr)
		if exit_code != 0:
			_terminal_output.append_text("[color=#8b3a3a](exit code %d)[/color]\n" % exit_code)
		_terminal_output.scroll_to_line(_terminal_output.get_line_count())
		_status_label.text = "Exit code: %d" % exit_code

# ------------------------------------------------------------------ mode switching

func _set_mode(mode: String) -> void:
	_mode = mode
	# Hide all containers, show the selected one
	var containers = _content_area.get_children()
	for i in range(containers.size()):
		containers[i].visible = false
	match mode:
		"files":
			containers[0].visible = true
			_title_label.text = "File Browser"
			_refresh_files()
		"editor":
			containers[1].visible = true
			_title_label.text = "Text Editor"
		"terminal":
			containers[2].visible = true
			_title_label.text = "Terminal"
			_terminal_input.grab_focus()

func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			_on_close()
		# Terminal history navigation
		if _mode == "terminal" and event.keycode == KEY_UP:
			if _terminal_history_idx > 0:
				_terminal_history_idx -= 1
				_terminal_input.text = _terminal_history[_terminal_history_idx]
				_terminal_input.caret_column = _terminal_input.text.length()
		elif _mode == "terminal" and event.keycode == KEY_DOWN:
			if _terminal_history_idx < _terminal_history.size() - 1:
				_terminal_history_idx += 1
				_terminal_input.text = _terminal_history[_terminal_history_idx]
			else:
				_terminal_history_idx = _terminal_history.size()
				_terminal_input.text = ""

func _on_close() -> void:
	visible = false
	close_requested.emit()

func show_panel(mode: String = "files") -> void:
	visible = true
	_set_mode(mode)

func show_files() -> void:
	show_panel("files")

func show_editor() -> void:
	show_panel("editor")

func show_terminal() -> void:
	show_panel("terminal")
