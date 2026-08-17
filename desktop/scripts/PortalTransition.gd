## PortalTransition.gd — Manages the five-state portal transition.
##
## States: idle -> awakening -> aligning -> transitioning -> arriving
##
## The portal is the visual bridge between rooms. When the user selects a
## destination, the portal awakens (rings begin to rotate), aligns (rings
## lock into position), transitions (the view dissolves through a gold
## flash), and arrives (the new room fades in).
##
## Reduced-motion mode skips the animation and snaps directly.
extends CanvasLayer

signal transition_complete(room_id: String)
signal state_changed(state: int)

enum State { IDLE, AWAKENING, ALIGNING, TRANSITIONING, ARRIVING }

var state: State = State.IDLE
var target_room_id: String = ""
var reduced_motion: bool = false

var _overlay: ColorRect
var _rings: Array[Control] = []
var _tween: Tween
var _state_label: Label

func _ready() -> void:
	layer = 100
	_build_overlay()
	_build_rings()
	_build_label()
	visible = false

func _build_overlay() -> void:
	_overlay = ColorRect.new()
	_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_overlay.color = Color.BLACK
	_overlay.modulate.a = 0.0
	add_child(_overlay)

func _build_rings() -> void:
	# Three concentric rings that rotate during the transition.
	var center := Control.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	center.custom_minimum_size = Vector2(400, 400)
	center.position = Vector2(-200, -200)
	add_child(center)
	for i in range(3):
		var ring := Control.new()
		ring.size = Vector2(300 - i * 80, 300 - i * 80)
		ring.position = Vector2(50 + i * 40, 50 + i * 40)
		ring.modulate.a = 0.0
		center.add_child(ring)
		_rings.append(ring)

func _build_label() -> void:
	_state_label = Label.new()
	_state_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	_state_label.position = Vector2(-200, -80)
	_state_label.custom_minimum_size = Vector2(400, 40)
	_state_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_state_label.add_theme_font_size_override("font_size", 14)
	_state_label.add_theme_color_override("font_color", SIOSBrand.COL_GOLD_BRIGHT)
	_state_label.modulate.a = 0.0
	add_child(_state_label)

func travel(to_room_id: String) -> void:
	if state != State.IDLE:
		return
	target_room_id = to_room_id
	visible = true
	if reduced_motion:
		_snap_transition()
	else:
		_run_sequence()

func _run_sequence() -> void:
	# Phase 1: awakening — overlay fades in, rings appear
	_set_state(State.AWAKENING)
	_tween = create_tween()
	_tween.set_parallel(true)
	_tween.tween_property(_overlay, "modulate:a", 0.85, 0.4)
	for i in range(_rings.size()):
		_tween.tween_property(_rings[i], "modulate:a", 1.0, 0.4).set_delay(i * 0.08)
	_tween.chain().tween_callback(func(): _set_state(State.ALIGNING))

	# Phase 2: aligning — rings rotate and lock
	_tween.tween_interval(0.3)
	_tween.tween_callback(func(): _set_state(State.TRANSITIONING))

	# Phase 3: transitioning — gold flash
	_tween.tween_property(_overlay, "color", SIOSBrand.COL_GOLD, 0.15)
	_tween.tween_property(_overlay, "modulate:a", 1.0, 0.1)
	_tween.tween_interval(0.1)
	_tween.tween_callback(func(): transition_complete.emit(target_room_id))
	_tween.tween_property(_overlay, "color", Color.BLACK, 0.1)

	# Phase 4: arriving — fade out to reveal new room
	_tween.tween_callback(func(): _set_state(State.ARRIVING))
	_tween.set_parallel(true)
	_tween.tween_property(_overlay, "modulate:a", 0.0, 0.4)
	for i in range(_rings.size()):
		_tween.tween_property(_rings[i], "modulate:a", 0.0, 0.3).set_delay(i * 0.05)
	_tween.chain().tween_callback(func(): _set_state(State.IDLE); visible = false)

func _snap_transition() -> void:
	_set_state(State.TRANSITIONING)
	_overlay.modulate.a = 1.0
	_overlay.color = Color.BLACK
	transition_complete.emit(target_room_id)
	_set_state(State.IDLE)
	_overlay.modulate.a = 0.0
	visible = false

func _set_state(s: State) -> void:
	state = s
	state_changed.emit(s)
	_state_label.text = SIOSBrand.PORTAL_STATE_NAMES[s].to_upper()
	if s != State.IDLE:
		_state_label.modulate.a = 1.0
	else:
		_state_label.modulate.a = 0.0

func set_reduced_motion(enabled: bool) -> void:
	reduced_motion = enabled
