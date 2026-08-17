## SIOSBrand.gd — Autoload singleton
## The single source of truth for the SIOS visual identity.
## Every room, HUD, and transition reads from here so the brand is consistent.
extends Node

# ------------------------------------------------------------------ palette
# Extracted from the existing Tauri workspace CSS and the concept art language:
# deep near-black backgrounds, antique gold accents, cool ambient blue.
const COL_BG_DEEP       := Color("02070d")
const COL_BG_PANEL       := Color("111419")
const COL_BG_PANEL_LIGHT := Color("1a1f26")
const COL_GOLD           := Color("c4a35a")
const COL_GOLD_BRIGHT    := Color("e1c77e")
const COL_GOLD_DIM       := Color("6c5b39")
const COL_LINE           := Color("282d32")
const COL_MUTED          := Color("78818a")
const COL_TEXT           := Color("e9edf0")
const COL_GREEN          := Color("7ab892")
const COL_AMBIENT        := Color("183246")
const COL_AMBIENT_WARM   := Color("2a1e10")
const COL_HIERO_GLOW     := Color("ff9d18")
const COL_DENIED         := Color("8b3a3a")

# ------------------------------------------------------------------ fonts
# Godot 4 built-in fonts are used as fallback. The project ships .ttf files
# in res://assets/fonts/ when available; otherwise system fonts are used.
var font_display: FontFile
var font_ui: FontFile
var font_mono: FontFile

# ------------------------------------------------------------------ rooms
# The 13 rooms from the concept art, ordered by the UX architecture build stages.
# access: "open" = everyday realm, "creator" = Creator-only (Tomb and its halls)
enum Access { OPEN, CREATOR }

const ROOMS: Array[Dictionary] = [
	{"id": "workspace",       "name": "Workspace",          "access": Access.OPEN,    "stage": "workspace",         "color": "183246", "icon": "W"},
	{"id": "command_chamber", "name": "Command Chamber",    "access": Access.OPEN,    "stage": "world",             "color": "0a1622", "icon": "C"},
	{"id": "observatory",     "name": "Observatory",        "access": Access.OPEN,    "stage": "world",             "color": "0a0f1a", "icon": "O"},
	{"id": "sanctum",         "name": "Sanctum",            "access": Access.OPEN,    "stage": "world",             "color": "1a0f1a", "icon": "S"},
	{"id": "forge",           "name": "Forge",              "access": Access.OPEN,    "stage": "world",             "color": "1a0e08", "icon": "F"},
	{"id": "mission_queue",   "name": "Mission Queue",      "access": Access.OPEN,    "stage": "world",             "color": "0a1a0e", "icon": "Q"},
	{"id": "court",           "name": "The Court",          "access": Access.OPEN,    "stage": "world",             "color": "1a0a0e", "icon": "J"},
	{"id": "project_workspace","name": "Project Workshop",  "access": Access.OPEN,    "stage": "world",             "color": "0a0e1a", "icon": "P"},
	{"id": "knowledge_browser","name": "Knowledge Archive", "access": Access.OPEN,    "stage": "world",             "color": "0e0a1a", "icon": "K"},
	{"id": "tomb_entrance",   "name": "Tomb Entrance",      "access": Access.CREATOR, "stage": "outer-temple",      "color": "050303", "icon": "T"},
	{"id": "hall_of_genesis", "name": "Hall of Genesis",    "access": Access.CREATOR, "stage": "inner-temple",      "color": "0a0805", "icon": "G"},
	{"id": "hall_of_evolution","name": "Hall of Evolution", "access": Access.CREATOR, "stage": "inner-temple",      "color": "080a05", "icon": "E"},
	{"id": "hall_of_architects","name":"Hall of Architects","access": Access.CREATOR, "stage": "inner-temple",      "color": "05080a", "icon": "A"},
	{"id": "hall_of_sovereignty","name":"Hall of Sovereignty","access":Access.CREATOR, "stage": "sovereign-core",    "color": "0a0508", "icon": "V"},
	{"id": "hall_of_memory",  "name": "Hall of Memory",     "access": Access.CREATOR, "stage": "sovereign-core",    "color": "08050a", "icon": "M"},
	{"id": "hall_of_creation","name": "Hall of Creation",   "access": Access.CREATOR, "stage": "sovereign-core",    "color": "0a0a05", "icon": "R"},
	{"id": "the_throne",      "name": "The Throne",         "access": Access.CREATOR, "stage": "sovereign-core",    "color": "0a0808", "icon": "X"},
]

# ------------------------------------------------------------------ portal
# Five states from the UX architecture: idle -> awakening -> aligning -> transitioning -> arriving
enum PortalState { IDLE, AWAKENING, ALIGNING, TRANSITIONING, ARRIVING }
const PORTAL_STATE_NAMES: Array[String] = ["idle", "awakening", "aligning", "transitioning", "arriving"]

# ------------------------------------------------------------------ materials
var mat_floor: StandardMaterial3D
var mat_wall: StandardMaterial3D
var mat_gold: StandardMaterial3D
var mat_gold_emissive: StandardMaterial3D
var mat_dais: StandardMaterial3D
var mat_station: StandardMaterial3D
var mat_station_active: StandardMaterial3D
var mat_denied: StandardMaterial3D
var mat_hiero_dark: StandardMaterial3D
var mat_hiero_lit: StandardMaterial3D

func _ready() -> void:
	_load_fonts()
	_build_materials()

func _load_fonts() -> void:
	# Try to load shipped fonts; fall back to Godot defaults.
	if ResourceLoader.exists("res://assets/fonts/CormorantGaramond.ttf"):
		font_display = load("res://assets/fonts/CormorantGaramond.ttf") as FontFile
	if ResourceLoader.exists("res://assets/fonts/Inter.ttf"):
		font_ui = load("res://assets/fonts/Inter.ttf") as FontFile
	if ResourceLoader.exists("res://assets/fonts/mono.ttf"):
		font_mono = load("res://assets/fonts/mono.ttf") as FontFile

func _build_materials() -> void:
	mat_floor = _mat(COL_BG_DEEP, 0.1, 0.16)
	mat_wall = _mat(COL_BG_PANEL, 0.05, 0.4)
	mat_gold = _mat(COL_GOLD, 0.9, 0.28)
	mat_gold_emissive = _mat(COL_GOLD_BRIGHT, 0.6, 0.22, COL_GOLD)
	mat_dais = _mat(Color("151b20"), 0.9, 0.24)
	mat_station = _mat(Color("111a22"), 0.8, 0.25, Color("003e72"))
	mat_station_active = _mat(Color("1a2a3a"), 0.8, 0.2, COL_GOLD)
	mat_denied = _mat(Color("1a0a0a"), 0.3, 0.5, COL_DENIED)
	mat_hiero_dark = _mat(Color("171007"), 0.55, 0.45)
	mat_hiero_lit = _mat(COL_GOLD, 0.3, 0.3, COL_HIERO_GLOW, 3.0)

func _mat(albedo: Color, metallic: float, roughness: float, emission := Color.BLACK, emission_energy := 2.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = albedo
	m.metallic = metallic
	m.roughness = roughness
	if emission != Color.BLACK:
		m.emission_enabled = true
		m.emission = emission
		m.emission_energy_multiplier = emission_energy
	return m

# ------------------------------------------------------------------ queries

func room_by_id(id: String) -> Dictionary:
	for room in ROOMS:
		if room.id == id:
			return room
	return {}

func room_index(id: String) -> int:
	for i in range(ROOMS.size()):
		if ROOMS[i].id == id:
			return i
	return -1

func room_color(id: String) -> Color:
	var room := room_by_id(id)
	return Color(room.get("color", "02070d"))

func is_creator_room(id: String) -> bool:
	var room := room_by_id(id)
	return room.get("access", Access.OPEN) == Access.CREATOR

# ------------------------------------------------------------------ helpers

func make_label(text: String, font_size: int, color: Color = COL_TEXT) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	if font_display != null:
		l.add_theme_font_override("font", font_display)
	return l

func make_panel(min_size: Vector2) -> PanelContainer:
	var p := PanelContainer.new()
	p.custom_minimum_size = min_size
	var sb := StyleBoxFlat.new()
	sb.bg_color = COL_BG_PANEL
	sb.border_color = COL_LINE
	sb.set_border_width_all(1)
	sb.set_content_margin_all(16)
	p.add_theme_stylebox_override("panel", sb)
	return p
