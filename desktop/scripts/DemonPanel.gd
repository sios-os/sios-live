## DemonPanel.gd — DEMON conversational interface for talking to ANUBIS.
##
## The DEMON is the mobile, voice/text interface from the SIOS UX architecture.
## This panel provides a chat interface where the Creator can talk to ANUBIS
## directly — ask questions, request explanations, give instructions.
##
## The panel is accessible from any room via a toggle button.
extends Control

const MAX_MESSAGES := 50
const TYPE_SPEED := 0.015  # seconds per character for typewriter effect

var _ipc: Node
var _messages: Array[Dictionary] = []  # {role: "user"/"anubis", text: "..."}
var _input_field: LineEdit
var _scroll_container: ScrollContainer
var _messages_container: VBoxContainer
var _send_button: Button
var _clear_button: Button
var _status_label: Label
var _thinking: bool = false
var _typing_text: String = ""
var _typing_index: int = 0
var _typing_timer: float = 0.0
var _typing_label: RichTextLabel
var _pending_mission: Dictionary = {}  # Stores mission awaiting approval
var _approve_button: Button
var _mission_poll_id: String = ""
var _mission_poll_timer: float = 0.0
var _mic_button: Button
var _speaker_button: Button
var _voice_output: bool = true  # TTS enabled by default
var _listening: bool = false

signal chat_sent(message: String)
signal chat_received(response: String)

func _ready() -> void:
	_ipc = get_node_or_null("/root/SIOSDesktop/IPCBridge")
	_build_ui()

func _build_ui() -> void:
	# Main panel
	set_anchors_preset(Control.PRESET_FULL_RECT)
	custom_minimum_size = Vector2(400, 300)

	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("02070d")
	sb.border_color = Color("c4a35a")
	sb.set_border_width_all(1)
	sb.set_content_margin_all(8)
	panel.add_theme_stylebox_override("panel", sb)
	add_child(panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 6)
	panel.add_child(vbox)

	# Header
	var header := HBoxContainer.new()
	header.custom_minimum_size = Vector2(0, 30)
	vbox.add_child(header)

	var title := Label.new()
	title.text = "DEMON"
	title.add_theme_color_override("font_color", Color("e1c77e"))
	title.add_theme_font_size_override("font_size", 18)
	title.custom_minimum_size = Vector2(100, 0)
	header.add_child(title)

	_status_label = Label.new()
	_status_label.text = "connecting..."
	_status_label.add_theme_color_override("font_color", Color("78818a"))
	_status_label.add_theme_font_size_override("font_size", 11)
	_status_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(_status_label)

	_clear_button = Button.new()
	_clear_button.text = "Clear"
	_clear_button.custom_minimum_size = Vector2(60, 0)
	_clear_button.pressed.connect(_on_clear)
	header.add_child(_clear_button)

	# Voice buttons
	_speaker_button = Button.new()
	_speaker_button.text = "Voice ON"
	_speaker_button.custom_minimum_size = Vector2(70, 0)
	_speaker_button.pressed.connect(_on_toggle_voice)
	header.add_child(_speaker_button)

	_mic_button = Button.new()
	_mic_button.text = "Mic"
	_mic_button.custom_minimum_size = Vector2(50, 0)
	_mic_button.pressed.connect(_on_mic)
	header.add_child(_mic_button)

	# Messages scroll area
	_scroll_container = ScrollContainer.new()
	_scroll_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vbox.add_child(_scroll_container)

	_messages_container = VBoxContainer.new()
	_messages_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_messages_container.add_theme_constant_override("separation", 4)
	_scroll_container.add_child(_messages_container)

	# Input row
	var input_row := HBoxContainer.new()
	input_row.custom_minimum_size = Vector2(0, 32)
	vbox.add_child(input_row)

	_input_field = LineEdit.new()
	_input_field.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_input_field.placeholder_text = "Speak to ANUBIS..."
	_input_field.add_theme_color_override("font_color", Color("e9edf0"))
	_input_field.add_theme_color_override("font_placeholder_color", Color("78818a"))
	var input_sb := StyleBoxFlat.new()
	input_sb.bg_color = Color("111419")
	input_sb.border_color = Color("282d32")
	input_sb.set_border_width_all(1)
	input_sb.set_content_margin_all(6)
	_input_field.add_theme_stylebox_override("normal", input_sb)
	var focus_sb := StyleBoxFlat.new()
	focus_sb.bg_color = Color("111419")
	focus_sb.border_color = Color("c4a35a")
	focus_sb.set_border_width_all(1)
	focus_sb.set_content_margin_all(6)
	_input_field.add_theme_stylebox_override("focus", focus_sb)
	_input_field.text_submitted.connect(_on_send)
	input_row.add_child(_input_field)

	_send_button = Button.new()
	_send_button.text = "Send"
	_send_button.custom_minimum_size = Vector2(70, 0)
	_send_button.pressed.connect(_on_send_pressed)
	input_row.add_child(_send_button)

	# Mission approval button (hidden by default)
	_approve_button = Button.new()
	_approve_button.text = "Approve Mission"
	_approve_button.custom_minimum_size = Vector2(120, 0)
	_approve_button.visible = false
	_approve_button.pressed.connect(_on_approve_mission)
	vbox.add_child(_approve_button)

	# Update status
	_update_status()

func _process(delta: float) -> void:
	# Typewriter effect
	if _thinking and _typing_label != null and _typing_index < _typing_text.length():
		_typing_timer += delta
		if _typing_timer >= TYPE_SPEED:
			_typing_timer = 0.0
			_typing_index += 1
			_typing_label.text = _typing_text.substr(0, _typing_index)
			# Auto-scroll
			await get_tree().process_frame
			_scroll_container.scroll_vertical = _scroll_container.get_v_scroll_bar().max_value

	# Mission polling — check status every 3 seconds
	if _mission_poll_id != "":
		_mission_poll_timer += delta
		if _mission_poll_timer >= 3.0:
			_mission_poll_timer = 0.0
			_poll_mission()

func _poll_mission() -> void:
	if _mission_poll_id == "" or _ipc == null:
		return
	var resp: Dictionary = _ipc.get_mission_status(_mission_poll_id)
	var status: String = resp.get("status", "?")
	if status == "running":
		return  # Keep polling
	# Mission finished — show result
	_mission_poll_id = ""
	if resp.get("success", false):
		var skill_name: String = resp.get("skill_name", "?")
		var attempts: int = resp.get("attempts", 0)
		_add_message("anubis", "Mission complete! I've promoted '%s' to my skill library (%d attempts)." % [skill_name, attempts])
	else:
		var reason: String = resp.get("denied_reason", resp.get("error", "unknown"))
		_add_message("anubis", "Mission failed: %s" % reason)

func _show_approve_button() -> void:
	_approve_button.visible = true

func _on_approve_mission() -> void:
	_approve_button.visible = false
	if _pending_mission.is_empty():
		return
	var task: String = _pending_mission["task"]
	var skill_name: String = _pending_mission["skill_name"]
	_pending_mission = {}

	_add_message("user", "[Approved mission: %s]" % skill_name)

	# Send the mission request with approval
	if _ipc == null or not _ipc.is_daemon_connected():
		_add_message("system", "ANUBIS is offline.")
		return

	_input_field.editable = false
	_send_button.disabled = true
	_thinking = true
	_add_message("anubis", "")
	_typing_text = "Launching mission..."
	_typing_index = 0
	_typing_label = _get_last_label()

	# Re-send the original message with approval token
	var response: Dictionary = _ipc.chat("Write me a function that %s" % task)
	_thinking = false

	if response.has("error"):
		_typing_text = "Error: " + response["error"]
		_typing_label.text = _typing_text
	else:
		var resp_text: String = response.get("response", "(no response)")
		_typing_text = resp_text
		_typing_index = 0
		_typing_label.text = ""
		_thinking = true
		if response.get("mission_launched", false):
			_mission_poll_id = response.get("mission_id", "")
			_mission_poll_timer = 0.0

	_input_field.editable = true
	_send_button.disabled = false
	_input_field.grab_focus()

func _update_status() -> void:
	if _ipc == null or not _ipc.is_daemon_connected():
		_status_label.text = "offline"
		_status_label.add_theme_color_override("font_color", Color("8b3a3a"))
		_input_field.editable = false
		_send_button.disabled = true
	else:
		_status_label.text = "online"
		_status_label.add_theme_color_override("font_color", Color("7ab892"))
		_input_field.editable = true
		_send_button.disabled = false

func _on_send_pressed() -> void:
	_on_send(_input_field.text)

func _on_send(text: String) -> void:
	text = text.strip_edges()
	if text.is_empty() or _thinking:
		return
	_update_status()
	if _ipc == null or not _ipc.is_daemon_connected():
		_add_message("system", "ANUBIS is offline. Start the daemon first.")
		return

	# Show user message
	_add_message("user", text)
	_input_field.text = ""
	_input_field.editable = false
	_send_button.disabled = true

	# Show thinking indicator
	_thinking = true
	_add_message("anubis", "")
	_typing_text = "..."
	_typing_index = 0
	_typing_label = _get_last_label()

	# Send to daemon (this blocks, but the UI has already updated)
	var response: Dictionary = _ipc.chat(text)
	_thinking = false

	if response.has("error"):
		_typing_text = "Error: " + response["error"]
		_typing_index = 0
		_typing_label.text = _typing_text
		_add_message("system", "Connection error: " + str(response["error"]))
	else:
		var resp_text: String = response.get("response", "(no response)")
		_typing_text = resp_text
		_typing_index = 0
		_typing_label.text = ""
		# Start typewriter effect
		_thinking = true
		chat_received.emit(resp_text)
		# Voice output
		_speak(resp_text)

		# Show knowledge grounding citations if available
		var grounded: bool = response.get("knowledge_grounded", false)
		var citations: Array = response.get("knowledge_citations", [])
		var claims_count: int = response.get("claims_used", 0)
		if grounded and (citations.size() > 0 or claims_count > 0):
			var cite_text := "[Knowledge: "
			if citations.size() > 0:
				cite_text += "%d docs" % citations.size()
			if claims_count > 0:
				if citations.size() > 0:
					cite_text += ", "
				cite_text += "%d claims" % claims_count
			cite_text += "]"
			# Add citation as a subtle system message after the response
			call_deferred("_add_message", "system", cite_text)

		# Handle mission request response
		if response.get("mission_request", false) and response.get("needs_approval", false):
			_pending_mission = {
				"task": response.get("task", ""),
				"skill_name": response.get("skill_name", ""),
			}
			_show_approve_button()

		# Handle mission launched
		if response.get("mission_launched", false):
			_mission_poll_id = response.get("mission_id", "")
			_mission_poll_timer = 0.0

	chat_sent.emit(text)
	_input_field.editable = true
	_send_button.disabled = false
	_input_field.grab_focus()

func _on_clear() -> void:
	_messages.clear()
	for child in _messages_container.get_children():
		child.queue_free()
	_ipc.reset_chat()
	_add_message("system", "Conversation cleared.")

func _add_message(role: String, text: String) -> void:
	_messages.append({"role": role, "text": text})
	if _messages.size() > MAX_MESSAGES:
		_messages.pop_front()
		var first = _messages_container.get_child(0)
		if first:
			first.queue_free()

	var label := RichTextLabel.new()
	label.bbcode_enabled = true
	label.fit_content = true
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.custom_minimum_size = Vector2(0, 24)

	var sb := StyleBoxFlat.new()
	match role:
		"user":
			sb.bg_color = Color("111419")
			sb.border_color = Color("183246")
			label.text = "[color=#e9edf0]" + text + "[/color]"
		"anubis":
			sb.bg_color = Color("0a0f14")
			sb.border_color = Color("c4a35a")
			label.text = "[color=#e1c77e]" + text + "[/color]"
		_:
			sb.bg_color = Color("1a0a0a")
			sb.border_color = Color("8b3a3a")
			label.text = "[color=#8b3a3a]" + text + "[/color]"
	sb.set_border_width_all(1)
	sb.set_content_margin_all(8)
	sb.set_border_width_left(3)
	label.add_theme_stylebox_override("normal", sb)

	_messages_container.add_child(label)

	# Auto-scroll to bottom
	await get_tree().process_frame
	_scroll_container.scroll_vertical = _scroll_container.get_v_scroll_bar().max_value

func _get_last_label() -> RichTextLabel:
	var children = _messages_container.get_children()
	if children.size() > 0:
		return children[children.size() - 1]
	return null

func show_panel() -> void:
	visible = true
	_update_status()
	_input_field.grab_focus()

func hide_panel() -> void:
	visible = false

# ------------------------------------------------------------------ voice

func _on_toggle_voice() -> void:
	_voice_output = not _voice_output
	_speaker_button.text = "Voice ON" if _voice_output else "Voice OFF"

func _on_mic() -> void:
	if _listening or _thinking:
		return
	if _ipc == null or not _ipc.is_daemon_connected():
		_add_message("system", "ANUBIS is offline.")
		return
	_listening = true
	_mic_button.text = "Listening..."
	_mic_button.disabled = true
	_add_message("system", "Listening... speak now")

	# Request STT from daemon (this blocks)
	var resp: Dictionary = _ipc.stt(5.0)
	_listening = false
	_mic_button.text = "Mic"
	_mic_button.disabled = false

	if resp.has("error") or not resp.get("ok", false):
		_add_message("system", "Voice input failed: " + str(resp.get("error", "unknown")))
		return

	var text: String = resp.get("text", "")
	if text.strip_edges().is_empty():
		_add_message("system", "No speech detected.")
		return

	# Send the transcribed text as a chat message
	_on_send(text)

func _speak(text: String) -> void:
	"""Send text to TTS if voice output is enabled."""
	if not _voice_output or _ipc == null or not _ipc.is_daemon_connected():
		return
	# Clean text for TTS
	var clean := text
	for char in ["*", "_", "#", "`", "[", "]", "(", ")"]:
		clean = clean.replace(char, "")
	_ipc.tts(clean)
