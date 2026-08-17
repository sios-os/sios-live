## SIOSBoot.gd — Boot screen controller.
##
## Shows the SIOS brand on a dark background, runs a brief initialization
## sequence (checking ANUBIS daemon, model, sandbox), then loads the main
## desktop scene.
extends Control

const MAIN_SCENE := "res://scenes/desktop.tscn"

var _status: Label
var _title: Label
var _tween: Tween
var _step: int = 0

const STEPS: Array[String] = [
	"Initializing kernel...",
	"Loading constitutional kernel...",
	"Verifying evidence ledger...",
	"Loading knowledge library (550 documents)...",
	"Indexing 15,677 verified claims...",
	"Connecting to ANUBIS daemon...",
	"Checking model availability...",
	"Sandbox integrity verified...",
	"Entering spatial desktop...",
]

func _ready() -> void:
	_status = $VBox/Status
	_title = $VBox/Title
	_title.modulate.a = 0.0
	_status.modulate.a = 0.0
	# Fade in
	_tween = create_tween()
	_tween.tween_property(_title, "modulate:a", 1.0, 0.6)
	_tween.tween_property(_status, "modulate:a", 1.0, 0.3)
	_tween.tween_callback(func(): _next_step())

func _next_step() -> void:
	if _step >= STEPS.size():
		_enter_desktop()
		return
	_status.text = STEPS[_step]
	_step += 1
	_tween = create_tween()
	_tween.tween_interval(0.25)
	_tween.tween_callback(func(): _next_step())

func _enter_desktop() -> void:
	_tween = create_tween()
	_tween.tween_interval(0.3)
	_tween.tween_property(self, "modulate:a", 0.0, 0.5)
	_tween.tween_callback(func():
		get_tree().change_scene_to_file(MAIN_SCENE))
