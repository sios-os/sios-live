## RoomBuilder.gd — Detailed procedural construction of all 13 SIOS rooms.
##
## Each room is built from Godot primitives with architectural detail:
##   - Pillared halls with gold-capped columns
##   - Tiered floor platforms with geometric patterns
##   - Wall panels with emissive hieroglyph strips
##   - Multi-layer lighting (ambient + accent + point)
##   - Ceiling details with gold rings and light fixtures
##   - Screen panels (emissive surfaces for room UI)
##   - Steps, arches, and decorative architectural elements
##
## When a GLB exists at res://generated/RM_<room>.glb, it is loaded instead.
extends Node3D

const ROOM_RADIUS := 16.0
const STATION_HEIGHT := 1.5
const PILLAR_HEIGHT := 8.0
const HIERO_STRIP_HEIGHT := 0.15

var _brand: Node

func _ready() -> void:
	_brand = get_node("/root/SIOSBrand")

## Build a complete room and return it as a Node3D ready to add to the scene.
func build_room(room_id: String) -> Node3D:
	# Try GLB first
	var glb := _try_load_glb(room_id)
	if glb:
		return glb

	match room_id:
		"workspace":
			return _build_workspace()
		"command_chamber":
			return _build_command_chamber()
		"observatory":
			return _build_observatory()
		"sanctum":
			return _build_sanctum()
		"forge":
			return _build_forge()
		"tomb_entrance":
			return _build_tomb_entrance()
		"hall_of_genesis", "hall_of_evolution", "hall_of_architects", \
		"hall_of_sovereignty", "hall_of_memory", "hall_of_creation":
			return _build_hall(room_id)
		"the_throne":
			return _build_throne()
		"mission_queue", "court", "project_workspace", "knowledge_browser":
			return _build_panel_room(room_id)
		_:
			return _build_placeholder(room_id)

# ------------------------------------------------------------------ helpers

func _mat(color: Color, metallic := 0.0, roughness := 0.5, emission := Color.BLACK, emission_energy := 2.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = metallic
	m.roughness = roughness
	if emission != Color.BLACK:
		m.emission_enabled = true
		m.emission = emission
		m.emission_energy_multiplier = emission_energy
	return m

func _mesh(name_str: String, mesh: PrimitiveMesh, pos: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = name_str
	mi.mesh = mesh
	mi.position = pos
	mi.material_override = mat
	return mi

func _cylinder(name_str: String, radius: float, height: float, pos: Vector3, mat: Material) -> MeshInstance3D:
	var c := CylinderMesh.new()
	c.top_radius = radius
	c.bottom_radius = radius
	c.height = height
	return _mesh(name_str, c, pos, mat)

func _cylinder_tapered(name_str: String, top_r: float, bot_r: float, height: float, pos: Vector3, mat: Material) -> MeshInstance3D:
	var c := CylinderMesh.new()
	c.top_radius = top_r
	c.bottom_radius = bot_r
	c.height = height
	return _mesh(name_str, c, pos, mat)

func _box(name_str: String, size: Vector3, pos: Vector3, mat: Material) -> MeshInstance3D:
	var b := BoxMesh.new()
	b.size = size
	return _mesh(name_str, b, pos, mat)

func _sphere(name_str: String, radius: float, pos: Vector3, mat: Material) -> MeshInstance3D:
	var s := SphereMesh.new()
	s.radius = radius
	s.height = radius * 2.0
	return _mesh(name_str, s, pos, mat)

func _torus(name_str: String, major_r: float, minor_r: float, pos: Vector3, mat: Material) -> MeshInstance3D:
	# Godot 4 TorusMesh uses inner_radius and outer_radius (not major/minor).
	# outer_radius = distance from center to outer edge = major_r + minor_r
	# inner_radius = distance from center to inner edge = major_r - minor_r
	var t := TorusMesh.new()
	t.outer_radius = major_r + minor_r
	t.inner_radius = major_r - minor_r
	return _mesh(name_str, t, pos, mat)

func _environment(bg_color: Color, ambient: Color, ambient_energy: float, fog := false, fog_color := Color.BLACK, fog_density := 0.0) -> WorldEnvironment:
	var we := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = bg_color
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = ambient
	env.ambient_light_energy = ambient_energy
	env.glow_enabled = true
	env.glow_intensity = 0.5
	env.glow_strength = 1.2
	if fog:
		env.fog_enabled = true
		env.fog_light_color = fog_color
		env.fog_density = fog_density
	we.environment = env
	return we

func _gold_light(pos: Vector3, energy: float = 1.0) -> DirectionalLight3D:
	var l := DirectionalLight3D.new()
	l.position = pos
	l.rotation_degrees = Vector3(-55, -25, 0)
	l.light_color = SIOSBrand.COL_GOLD
	l.light_energy = energy
	return l

func _omni(pos: Vector3, color: Color, energy: float, rng: float) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.position = pos
	l.light_color = color
	l.light_energy = energy
	l.omni_range = rng
	return l

func _spot(pos: Vector3, rot: Vector3, color: Color, energy: float, angle: float = 45.0) -> SpotLight3D:
	var l := SpotLight3D.new()
	l.position = pos
	l.rotation_degrees = rot
	l.light_color = color
	l.light_energy = energy
	l.spot_angle = angle
	l.spot_range = 25.0
	return l

func _try_load_glb(room_id: String) -> Node3D:
	var path := "res://generated/RM_%s.glb" % room_id.to_upper()
	if ResourceLoader.exists(path):
		var packed := load(path) as PackedScene
		if packed:
			var node := packed.instantiate() as Node3D
			node.name = "GENERATED_%s" % room_id.to_upper()
			return node
	return null

# ------------------------------------------------------------------ architecture

func _build_floor(radius: float, color: Color) -> MeshInstance3D:
	return _cylinder("AS_FLOOR", radius, 0.2, Vector3(0, -0.1, 0),
		_mat(color, 0.1, 0.16))

func _build_tiered_floor(radius: float, tiers: int, base_color: Color, parent: Node3D) -> void:
	# Concentric tiers stepping down from center
	for i in range(tiers):
		var r := radius * (1.0 - float(i) / tiers * 0.3)
		var y := -0.1 - float(i) * 0.15
		var c := base_color.lerp(Color.BLACK, float(i) / tiers * 0.3)
		parent.add_child(_cylinder("AS_FLOOR_TIER_%d" % i, r, 0.15, Vector3(0, y, 0),
			_mat(c, 0.1, 0.2)))

func _build_floor_inlay(radius: float, parent: Node3D) -> void:
	# Gold inlay rings on the floor
	for i in range(3):
		var r := radius * (0.3 + i * 0.25)
		parent.add_child(_torus("AS_FLOOR_INLAY_%d" % i, r, 0.04, Vector3(0, 0.01, 0),
			SIOSBrand.mat_gold_emissive))

func _build_pillar(pos: Vector3, height: float, mat_col: Material, mat_cap: Material, parent: Node3D, name_prefix: String) -> void:
	# Base block
	parent.add_child(_cylinder(name_prefix + "_BASE", 0.7, 0.4, pos + Vector3(0, 0.2, 0), mat_cap))
	# Column shaft
	parent.add_child(_cylinder_tapered(name_prefix + "_SHAFT", 0.45, 0.5, height - 0.8, pos + Vector3(0, height * 0.5, 0), mat_col))
	# Capital (top)
	parent.add_child(_cylinder(name_prefix + "_CAP", 0.7, 0.4, pos + Vector3(0, height - 0.2, 0), mat_cap))
	# Gold band at top
	parent.add_child(_torus(name_prefix + "_BAND", 0.5, 0.05, pos + Vector3(0, height - 0.5, 0), SIOSBrand.mat_gold_emissive))

func _build_pillar_ring(radius: float, count: int, height: float, mat_col: Material, mat_cap: Material, parent: Node3D) -> void:
	for i in range(count):
		var angle := TAU * float(i) / float(count)
		var pos := Vector3(radius * cos(angle), 0, -radius * sin(angle))
		_build_pillar(pos, height, mat_col, mat_cap, parent, "AS_PILLAR_%03d" % i)

func _build_wall_ring(radius: float, height: float, segments: int, color: Color, parent: Node3D) -> void:
	for i in range(segments):
		var angle := TAU * float(i) / float(segments)
		var pos := Vector3(radius * cos(angle), height * 0.5, -radius * sin(angle))
		var wall := _box("AS_WALL_%03d" % i, Vector3(4.1, height, 0.44), pos,
			_mat(color, 0.05, 0.4))
		wall.rotation.y = -angle
		parent.add_child(wall)

func _build_hiero_strip(radius: float, y: float, segments: int, parent: Node3D) -> void:
	# Emissive gold strip at the top of walls — the hieroglyph band
	for i in range(segments):
		var angle := TAU * float(i) / float(segments)
		var pos := Vector3(radius * cos(angle), y, -radius * sin(angle))
		var strip := _box("AS_HIERO_%03d" % i, Vector3(4.0, HIERO_STRIP_HEIGHT, 0.46), pos,
			SIOSBrand.mat_gold_emissive)
		strip.rotation.y = -angle
		parent.add_child(strip)

func _build_ceiling(radius: float, height: float, color: Color, parent: Node3D) -> void:
	# Ceiling dome (flat cylinder)
	parent.add_child(_cylinder("AS_CEILING", radius, 0.3, Vector3(0, height, 0),
		_mat(color, 0.05, 0.6)))
	# Central gold ring
	parent.add_child(_torus("AS_CEIL_RING", radius * 0.3, 0.08, Vector3(0, height - 0.2, 0),
		SIOSBrand.mat_gold_emissive))

func _build_screen_panel(name_str: String, size: Vector2, pos: Vector3, rot_y: float, parent: Node3D) -> MeshInstance3D:
	# Emissive panel that acts as a screen/display
	var panel := _box(name_str, Vector3(size.x, size.y, 0.08), pos,
		_mat(Color("0a1525"), 0.0, 0.3, SIOSBrand.COL_AMBIENT, 1.5))
	panel.rotation.y = rot_y
	parent.add_child(panel)
	return panel

func _build_stations(station_defs: Array, parent: Node3D, mat: Material) -> Array[MeshInstance3D]:
	var stations: Array[MeshInstance3D] = []
	for s in station_defs:
		var st := _box(s[0], Vector3(3.2, STATION_HEIGHT, 2.2), s[2], mat)
		st.set_meta("station_id", s[0])
		st.set_meta("station_label", s[1])
		parent.add_child(st)
		# Add a screen panel on top of each station
		_build_screen_panel(s[0] + "_SCREEN", Vector2(2.8, 1.0),
			s[2] + Vector3(0, STATION_HEIGHT * 0.5 + 0.5, 0), 0, parent)
		stations.append(st)
	return stations

func _build_arch(pos: Vector3, width: float, height: float, mat: Material, parent: Node3D, name_prefix: String) -> void:
	# Two pillars and a lintel
	parent.add_child(_box(name_prefix + "_L", Vector3(0.6, height, 0.6), pos + Vector3(-width * 0.5, height * 0.5, 0), mat))
	parent.add_child(_box(name_prefix + "_R", Vector3(0.6, height, 0.6), pos + Vector3(width * 0.5, height * 0.5, 0), mat))
	parent.add_child(_box(name_prefix + "_LINTEL", Vector3(width + 0.6, 0.8, 0.6), pos + Vector3(0, height, 0), mat))
	# Gold accent on lintel
	parent.add_child(_box(name_prefix + "_GOLD", Vector3(width + 0.4, 0.1, 0.62), pos + Vector3(0, height - 0.3, 0), SIOSBrand.mat_gold_emissive))

func _build_steps(pos: Vector3, count: int, width: float, step_depth: float, mat: Material, parent: Node3D, name_prefix: String) -> void:
	for i in range(count):
		var y := float(i) * 0.2
		var z := pos.z + float(i) * step_depth
		parent.add_child(_box("%s_%d" % [name_prefix, i], Vector3(width, 0.2, step_depth + 0.1), Vector3(pos.x, pos.y + y, z), mat))

# ------------------------------------------------------------------ rooms

func _build_workspace() -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_WORKSPACE"
	room.add_child(_environment(Color("0a1018"), SIOSBrand.COL_AMBIENT, 0.55))
	# Tiered floor with gold inlay
	_build_tiered_floor(ROOM_RADIUS, 3, Color("0a0f14"), room)
	_build_floor_inlay(ROOM_RADIUS, room)
	# Pillared hall
	_build_pillar_ring(ROOM_RADIUS - 1.5, 8, PILLAR_HEIGHT, SIOSBrand.mat_hiero_dark, SIOSBrand.mat_gold, room)
	# Walls with hieroglyph strips
	_build_wall_ring(ROOM_RADIUS, 6.0, 16, Color("0d1218"), room)
	_build_hiero_strip(ROOM_RADIUS - 0.2, 5.5, 16, room)
	_build_ceiling(ROOM_RADIUS, PILLAR_HEIGHT, Color("0a0e14"), room)
	# Lighting — bright, productive
	room.add_child(_gold_light(Vector3(0, 10, 0), 0.9))
	room.add_child(_omni(Vector3(0, 6, 0), SIOSBrand.COL_GOLD_BRIGHT, 1.5, 25.0))
	# Central work surface — raised dais with desk
	room.add_child(_cylinder("AS_WS_DAIS", 6.0, 0.3, Vector3(0, 0.15, 0), SIOSBrand.mat_dais))
	room.add_child(_cylinder("AS_WS_DESK", 5.0, 0.8, Vector3(0, 0.55, 0),
		_mat(Color("1a1f26"), 0.3, 0.3)))
	# Gold ring on desk surface
	room.add_child(_torus("AS_WS_DESK_RING", 4.5, 0.03, Vector3(0, 0.96, 0), SIOSBrand.mat_gold_emissive))
	# Central holographic display
	room.add_child(_cylinder("AS_WS_HOLO", 0.3, 2.5, Vector3(0, 2.0, 0),
		_mat(Color("1a3050"), 0.5, 0.1, Color("00aaff"), 1.0)))
	# Work stations around the perimeter
	var stations := [
		["ST_WS_EDITOR", "Code Editor", Vector3(-10, 0.75, 7)],
		["ST_WS_TERMINAL", "Terminal", Vector3(10, 0.75, 7)],
		["ST_WS_SANDBOX", "Sandbox", Vector3(-10, 0.75, -7)],
		["ST_WS_SKILLS", "Skill Library", Vector3(10, 0.75, -7)],
		["ST_WS_MISSIONS", "Active Missions", Vector3(0, 0.75, 11)],
	]
	_build_stations(stations, room, SIOSBrand.mat_station)
	return room

func _build_command_chamber() -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_COMMAND_CHAMBER"
	room.add_child(_environment(Color("02070d"), SIOSBrand.COL_AMBIENT, 0.45))
	# Dark tiered floor
	_build_tiered_floor(ROOM_RADIUS, 4, Color("080d12"), room)
	_build_floor_inlay(ROOM_RADIUS, room)
	# Tall pillared hall
	_build_pillar_ring(ROOM_RADIUS - 1.5, 12, PILLAR_HEIGHT + 1.0, SIOSBrand.mat_hiero_dark, SIOSBrand.mat_gold, room)
	_build_wall_ring(ROOM_RADIUS, 9.0, 24, Color("0a0f14"), room)
	_build_hiero_strip(ROOM_RADIUS - 0.2, 8.5, 24, room)
	_build_ceiling(ROOM_RADIUS, PILLAR_HEIGHT + 1.0, Color("060a0e"), room)
	# Lighting — dramatic, focused on center
	room.add_child(_gold_light(Vector3(0, 10, 0), 1.1))
	room.add_child(_spot(Vector3(0, 8, 0), Vector3(-90, 0, 0), SIOSBrand.COL_GOLD_BRIGHT, 3.0, 30.0))
	# Central dais — stepped platform
	_build_steps(Vector3(0, 0, 0), 3, 8.0, 1.2, SIOSBrand.mat_dais, room, "AS_CMD_STEP")
	room.add_child(_cylinder("AS_CMD_DAIS", 4.0, 0.3, Vector3(0, 0.6, 0), SIOSBrand.mat_dais))
	# ANUBIS core — central pillar with glowing crystal
	room.add_child(_cylinder("AS_CMD_CORE_BASE", 1.2, 0.4, Vector3(0, 0.8, 0), SIOSBrand.mat_gold))
	room.add_child(_cylinder("AS_CMD_ANUBIS", 0.9, 4.2, Vector3(0, 3.0, 0), SIOSBrand.mat_gold))
	# Glowing crystal on top
	room.add_child(_sphere("AS_CMD_CRYSTAL", 0.7, Vector3(0, 5.3, 0),
		_mat(Color("1a3050"), 0.3, 0.1, SIOSBrand.COL_GOLD_BRIGHT, 2.0)))
	# Gold rings around the core
	for i in range(3):
		room.add_child(_torus("AS_CMD_RING_%d" % i, 1.5 + i * 0.5, 0.04, Vector3(0, 2 + i * 0.8, 0), SIOSBrand.mat_gold_emissive))
	# Station ring
	var stations := [
		["ST_CMD_PROCESSES", "Processes", Vector3(-7.6, 0.75, 7.6)],
		["ST_CMD_HARDWARE", "Hardware", Vector3(7.6, 0.75, -7.6)],
		["ST_CMD_NETWORK", "Network", Vector3(-7.6, 0.75, -7.6)],
		["ST_CMD_SERVICES", "Services", Vector3(-10.8, 0.75, 0)],
		["ST_CMD_AGENTS", "Agents", Vector3(10.8, 0.75, 0)],
		["ST_CMD_AUTOMATIONS", "Missions", Vector3(-4.1, 0.75, 10)],
		["ST_CMD_LOGS", "Logs", Vector3(4.1, 0.75, 10)],
	]
	_build_stations(stations, room, SIOSBrand.mat_station)
	return room

func _build_observatory() -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_OBSERVATORY"
	room.add_child(_environment(Color("02050a"), Color("0a1428"), 0.3, true, Color("02050a"), 0.02))
	# Dark floor with subtle inlay
	room.add_child(_build_floor(ROOM_RADIUS, Color("040810")))
	_build_floor_inlay(ROOM_RADIUS, room)
	# No walls — open to the stars
	# Low pillar stubs as viewing platform markers
	for i in range(6):
		var angle := TAU * float(i) / 6.0
		var pos := Vector3(10 * cos(angle), 0, -10 * sin(angle))
		# Viewing platform
		room.add_child(_cylinder("AS_OBS_PLATFORM_%d" % i, 2.5, 0.6, pos,
			_mat(Color("0a1020"), 0.4, 0.3)))
		# Gold rim on platform
		room.add_child(_torus("AS_OBS_RIM_%d" % i, 2.3, 0.04, pos + Vector3(0, 0.32, 0), SIOSBrand.mat_gold_emissive))
		# Short pillar with viewing crystal
		room.add_child(_cylinder("AS_OBS_PILLAR_%d" % i, 0.3, 1.5, pos + Vector3(0, 0.8, 0),
			_mat(Color("0a1525"), 0.5, 0.2)))
	# Central viewing crystal — large, floating
	room.add_child(_cylinder("AS_OBS_BASE", 2.0, 0.3, Vector3(0, 0.05, 0), SIOSBrand.mat_dais))
	room.add_child(_sphere("AS_OBS_CRYSTAL", 1.5, Vector3(0, 3.5, 0),
		_mat(Color("1a3050"), 0.2, 0.1, Color("004080"), 1.5)))
	# Orbiting rings
	for i in range(3):
		var ring := _torus("AS_OBS_ORBIT_%d" % i, 2.5 + i * 0.5, 0.03, Vector3(0, 3.5, 0), SIOSBrand.mat_gold_emissive)
		ring.rotation_degrees.x = 70 + i * 10
		room.add_child(ring)
	# Starfield — dense points scattered above
	for i in range(120):
		var star := _sphere("AS_OBS_STAR_%d" % i, 0.05,
			Vector3(randf_range(-14, 14), randf_range(5, 14), randf_range(-14, 14)),
			_mat(Color.WHITE, 0.0, 0.0, Color.WHITE, 1.5))
		room.add_child(star)
	# Distant nebula glow
	room.add_child(_omni(Vector3(8, 8, -8), Color("2040a0"), 0.5, 30.0))
	room.add_child(_omni(Vector3(-8, 6, 8), Color("a02040"), 0.3, 25.0))
	# Soft lighting
	room.add_child(_gold_light(Vector3(0, 12, 0), 0.5))
	room.add_child(_omni(Vector3(0, 4, 0), Color("0080ff"), 0.8, 15.0))
	return room

func _build_sanctum() -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_SANCTUM"
	room.add_child(_environment(Color("010507"), Color("173b50"), 0.42))
	_build_tiered_floor(ROOM_RADIUS, 2, Color("080a0e"), room)
	_build_floor_inlay(ROOM_RADIUS, room)
	# Pillared hall
	_build_pillar_ring(ROOM_RADIUS - 1.5, 10, PILLAR_HEIGHT - 1.0, SIOSBrand.mat_hiero_dark, SIOSBrand.mat_gold, room)
	_build_wall_ring(ROOM_RADIUS, 7.0, 20, Color("0a0e12"), room)
	_build_hiero_strip(ROOM_RADIUS - 0.2, 6.5, 20, room)
	_build_ceiling(ROOM_RADIUS, PILLAR_HEIGHT - 1.0, Color("06080c"), room)
	# Lighting — calm, reflective
	room.add_child(_gold_light(Vector3(0, 8, 0), 0.8))
	room.add_child(_omni(Vector3(0, 4, 0), Color("173b50"), 1.0, 20.0))
	# Central identity crystal — floating, glowing
	room.add_child(_cylinder("AS_SANCTUM_BASE", 2.0, 0.3, Vector3(0, 0.05, 0), SIOSBrand.mat_dais))
	room.add_child(_sphere("AS_SANCTUM_CRYSTAL", 1.5, Vector3(0, 3.0, 0),
		SIOSBrand.mat_gold_emissive))
	# Orbiting rings around crystal
	for i in range(2):
		var ring := _torus("AS_SANCTUM_ORBIT_%d" % i, 2.0 + i * 0.4, 0.03, Vector3(0, 3.0, 0), SIOSBrand.mat_gold_emissive)
		ring.rotation_degrees.x = 60 + i * 20
		room.add_child(ring)
	# Reflective basin
	room.add_child(_cylinder("AS_SANCTUM_BASIN", 3.0, 0.4, Vector3(0, 0.2, 0),
		_mat(Color("0a1520"), 0.9, 0.05)))
	room.add_child(_cylinder("AS_SANCTUM_BASIN_WATER", 2.8, 0.05, Vector3(0, 0.38, 0),
		_mat(Color("103040"), 0.8, 0.02, Color("204060"), 0.5)))
	# Personalization stations
	var stations := [
		["ST_SANCT_IDENTITY", "Identity", Vector3(-10, 0.75, 0)],
		["ST_SANCT_APPEARANCE", "Appearance", Vector3(10, 0.75, 0)],
		["ST_SANCT_VOICE", "Voice", Vector3(0, 0.75, 11)],
		["ST_SANCT_PRIVACY", "Privacy", Vector3(0, 0.75, -11)],
		["ST_SANCT_ACCESSIBILITY", "Accessibility", Vector3(-7, 0.75, -7)],
	]
	_build_stations(stations, room, SIOSBrand.mat_station)
	return room

func _build_forge() -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_FORGE"
	room.add_child(_environment(Color("0a0604"), Color("2a1e10"), 0.5, true, Color("1a0a04"), 0.03))
	# Warm dark floor
	room.add_child(_build_floor(ROOM_RADIUS, Color("120a06")))
	_build_floor_inlay(ROOM_RADIUS, room)
	# Industrial pillars
	_build_pillar_ring(ROOM_RADIUS - 1.5, 8, PILLAR_HEIGHT, SIOSBrand.mat_hiero_dark, SIOSBrand.mat_gold, room)
	_build_wall_ring(ROOM_RADIUS, 8.0, 20, Color("140a06"), room)
	_build_hiero_strip(ROOM_RADIUS - 0.2, 7.5, 20, room)
	_build_ceiling(ROOM_RADIUS, PILLAR_HEIGHT, Color("0e0804"), room)
	# Warm forge lighting
	var light := OmniLight3D.new()
	light.position = Vector3(0, 4, 0)
	light.light_color = Color("ff6a20")
	light.light_energy = 2.5
	light.omni_range = 20.0
	room.add_child(light)
	room.add_child(_gold_light(Vector3(5, 8, 5), 0.3))
	room.add_child(_omni(Vector3(0, 2, 0), Color("ff4a10"), 1.5, 12.0))
	# Central forge/anvil on stepped base
	_build_steps(Vector3(0, 0, 0), 2, 5.0, 1.0, SIOSBrand.mat_dais, room, "AS_FORGE_STEP")
	room.add_child(_box("AS_FORGE_ANVIL", Vector3(3, 1.5, 3), Vector3(0, 1.0, 0),
		_mat(Color("2a1a0a"), 0.8, 0.3, Color("3a1a05"), 1.0)))
	# Glowing forge element on top
	room.add_child(_box("AS_FORGE_GLOW", Vector3(2.5, 0.2, 2.5), Vector3(0, 1.85, 0),
		_mat(Color("ff4a10"), 0.0, 0.0, Color("ff6a20"), 3.0)))
	# Tool stations
	var stations := [
		["ST_FORGE_BUILD", "Build", Vector3(-10, 0.75, 7)],
		["ST_FORGE_TEST", "Test", Vector3(10, 0.75, 7)],
		["ST_FORGE_PACKAGE", "Package", Vector3(-10, 0.75, -7)],
		["ST_FORGE_SIGN", "Sign", Vector3(10, 0.75, -7)],
		["ST_FORGE_ARTIFACTS", "Artifacts", Vector3(0, 0.75, 11)],
	]
	_build_stations(stations, room, SIOSBrand.mat_station)
	return room

func _build_tomb_entrance() -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_TOMB_ENTRANCE"
	room.add_child(_environment(Color("050303"), Color("1a0a05"), 0.2, true, Color("050303"), 0.05))
	# Small dark floor
	room.add_child(_build_floor(ROOM_RADIUS * 0.7, Color("080404")))
	_build_floor_inlay(ROOM_RADIUS * 0.7, room)
	# Dim lighting
	room.add_child(_gold_light(Vector3(0, 6, 0), 0.4))
	room.add_child(_omni(Vector3(0, 3, -5), Color("3a2a10"), 0.8, 10.0))
	# Massive gate door with gold frame
	room.add_child(_box("AS_TOMB_GATE", Vector3(6, 8, 0.8), Vector3(0, 4, -10),
		_mat(Color("0a0604"), 0.3, 0.6)))
	# Gold frame around gate
	room.add_child(_box("AS_TOMB_GATE_FRAME_L", Vector3(0.4, 8.4, 0.9), Vector3(-3.2, 4, -10), SIOSBrand.mat_gold_emissive))
	room.add_child(_box("AS_TOMB_GATE_FRAME_R", Vector3(0.4, 8.4, 0.9), Vector3(3.2, 4, -10), SIOSBrand.mat_gold_emissive))
	room.add_child(_box("AS_TOMB_GATE_FRAME_T", Vector3(6.8, 0.4, 0.9), Vector3(0, 8.2, -10), SIOSBrand.mat_gold_emissive))
	# Archway above gate
	_build_arch(Vector3(0, 8, -10), 7.0, 3.0, SIOSBrand.mat_hiero_dark, room, "AS_TOMB_ARCH")
	# Three proof rings (concealed by default) — floating before the gate
	for i in range(3):
		var ring := _torus("AS_TOMB_RING_%d" % i, 2.0 - i * 0.4, 0.06, Vector3(0, 2 + i * 1.5, -8), SIOSBrand.mat_gold_emissive)
		ring.rotation_degrees.x = 80
		room.add_child(ring)
	# Flanking pillars with hieroglyphs
	_build_pillar(Vector3(-5, 0, -8), 7.0, SIOSBrand.mat_hiero_dark, SIOSBrand.mat_gold, room, "AS_TOMB_PILLAR_L")
	_build_pillar(Vector3(5, 0, -8), 7.0, SIOSBrand.mat_hiero_dark, SIOSBrand.mat_gold, room, "AS_TOMB_PILLAR_R")
	# Boundary wall ring
	_build_wall_ring(ROOM_RADIUS * 0.7, 5.0, 12, Color("080404"), room)
	_build_hiero_strip(ROOM_RADIUS * 0.7 - 0.2, 4.5, 12, room)
	return room

func _build_hall(room_id: String) -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_%s" % room_id.to_upper()
	var rc := SIOSBrand.room_color(room_id)
	room.add_child(_environment(rc, Color("1a1505"), 0.35, true, rc, 0.02))
	# Long corridor floor with center inlay
	var floor_mesh := BoxMesh.new()
	floor_mesh.size = Vector3(8, 0.2, 30)
	room.add_child(_mesh("AS_HALL_FLOOR", floor_mesh, Vector3(0, -0.1, 0),
		_mat(Color("0a0805"), 0.1, 0.2)))
	# Gold center strip
	room.add_child(_box("AS_HALL_CENTER_STRIP", Vector3(0.3, 0.02, 28), Vector3(0, 0.01, 0), SIOSBrand.mat_gold_emissive))
	# Corridor walls with hieroglyph strips
	room.add_child(_box("AS_HALL_WALL_L", Vector3(0.4, 6, 30), Vector3(-4, 3, 0),
		_mat(Color("0d0a06"), 0.05, 0.4)))
	room.add_child(_box("AS_HALL_WALL_R", Vector3(0.4, 6, 30), Vector3(4, 3, 0),
		_mat(Color("0d0a06"), 0.05, 0.4)))
	# Hieroglyph strips on both walls
	for z in range(-12, 14, 4):
		room.add_child(_box("AS_HALL_HIERO_L_%d" % z, Vector3(0.42, 0.15, 3.5), Vector3(-4, 5, z + 0.5), SIOSBrand.mat_gold_emissive))
		room.add_child(_box("AS_HALL_HIERO_R_%d" % z, Vector3(0.42, 0.15, 3.5), Vector3(4, 5, z + 0.5), SIOSBrand.mat_gold_emissive))
	# Ceiling
	room.add_child(_box("AS_HALL_CEIL", Vector3(8, 0.3, 30), Vector3(0, 6, 0), _mat(Color("080604"), 0.05, 0.6)))
	# Ceiling gold strip
	room.add_child(_box("AS_HALL_CEIL_STRIP", Vector3(0.3, 0.05, 28), Vector3(0, 5.85, 0), SIOSBrand.mat_gold_emissive))
	# Lighting down the corridor
	room.add_child(_gold_light(Vector3(0, 5, 0), 0.6))
	for z in range(-10, 12, 6):
		room.add_child(_omni(Vector3(0, 5, z), SIOSBrand.COL_GOLD, 0.6, 8.0))
	# Pillars lining the corridor
	for z in range(-10, 12, 5):
		_build_pillar(Vector3(-3.5, 0, z), 5.5, SIOSBrand.mat_hiero_dark, SIOSBrand.mat_gold, room, "AS_HALL_PILLAR_L_%d" % z)
		_build_pillar(Vector3(3.5, 0, z), 5.5, SIOSBrand.mat_hiero_dark, SIOSBrand.mat_gold, room, "AS_HALL_PILLAR_R_%d" % z)
	# Artifact pedestals down the corridor
	for i in range(5):
		var z := -10 + i * 5
		# Pedestal
		room.add_child(_cylinder("AS_HALL_PEDESTAL_%d" % i, 0.6, 1.0,
			Vector3(-2, 0.5, z), SIOSBrand.mat_dais))
		room.add_child(_cylinder("AS_HALL_PEDESTAL_R_%d" % i, 0.6, 1.0,
			Vector3(2, 0.5, z), SIOSBrand.mat_dais))
		# Gold rim on pedestal
		room.add_child(_torus("AS_HALL_PEDESTAL_RIM_%d" % i, 0.55, 0.03, Vector3(-2, 1.05, z), SIOSBrand.mat_gold_emissive))
		room.add_child(_torus("AS_HALL_PEDESTAL_RIM_R_%d" % i, 0.55, 0.03, Vector3(2, 1.05, z), SIOSBrand.mat_gold_emissive))
		# Artifact on each pedestal — glowing crystal
		room.add_child(_sphere("AS_HALL_ARTIFACT_%d" % i, 0.3,
			Vector3(-2, 1.4, z), SIOSBrand.mat_gold_emissive))
		room.add_child(_sphere("AS_HALL_ARTIFACT_R_%d" % i, 0.3,
			Vector3(2, 1.4, z), SIOSBrand.mat_gold_emissive))
		# Light above each artifact
		room.add_child(_omni(Vector3(-2, 2, z), SIOSBrand.COL_GOLD_BRIGHT, 0.4, 4.0))
		room.add_child(_omni(Vector3(2, 2, z), SIOSBrand.COL_GOLD_BRIGHT, 0.4, 4.0))
	# End archway with gold accent
	_build_arch(Vector3(0, 2.5, -14), 6.0, 5.0, _mat(Color("0a0805"), 0.2, 0.5), room, "AS_HALL_ARCH")
	room.add_child(_box("AS_HALL_ARCH_GOLD", Vector3(6.2, 0.1, 0.5), Vector3(0, 5.0, -14), SIOSBrand.mat_gold_emissive))
	return room

func _build_throne() -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_THE_THRONE"
	room.add_child(_environment(Color("0a0808"), Color("2a1505"), 0.3, true, Color("0a0808"), 0.03))
	# Raised floor
	room.add_child(_build_floor(10.0, Color("0c0606")))
	_build_floor_inlay(10.0, room)
	# Dramatic lighting
	room.add_child(_gold_light(Vector3(0, 8, 5), 1.2))
	room.add_child(_spot(Vector3(0, 10, 3), Vector3(-70, 0, 0), SIOSBrand.COL_GOLD_BRIGHT, 4.0, 25.0))
	room.add_child(_omni(Vector3(0, 3, 0), Color("2a1505"), 1.0, 15.0))
	# Throne dais — multi-tiered raised platform
	room.add_child(_cylinder("AS_THRONE_DAIS", 3.5, 0.3, Vector3(0, 0.15, 0), SIOSBrand.mat_dais))
	room.add_child(_cylinder("AS_THRONE_DAIS_2", 2.5, 0.4, Vector3(0, 0.5, 0),
		_mat(Color("1a1208"), 0.9, 0.2)))
	room.add_child(_cylinder("AS_THRONE_DAIS_3", 1.8, 0.3, Vector3(0, 0.85, 0), SIOSBrand.mat_gold))
	# Gold rim on top tier
	room.add_child(_torus("AS_THRONE_DAIS_RIM", 1.7, 0.04, Vector3(0, 1.0, 0), SIOSBrand.mat_gold_emissive))
	# The throne — ornate seat with tall backrest
	room.add_child(_box("AS_THRONE_SEAT", Vector3(2, 1, 1.5), Vector3(0, 1.5, 0),
		SIOSBrand.mat_gold))
	room.add_child(_box("AS_THRONE_BACK", Vector3(2, 4.5, 0.4), Vector3(0, 4.0, -0.5),
		SIOSBrand.mat_gold))
	# Gold trim on throne back
	room.add_child(_box("AS_THRONE_BACK_TRIM", Vector3(2.1, 0.15, 0.5), Vector3(0, 6.2, -0.5), SIOSBrand.mat_gold_emissive))
	room.add_child(_box("AS_THRONE_BACK_TRIM_L", Vector3(0.15, 4.5, 0.5), Vector3(-1.05, 4.0, -0.5), SIOSBrand.mat_gold_emissive))
	room.add_child(_box("AS_THRONE_BACK_TRIM_R", Vector3(0.15, 4.5, 0.5), Vector3(1.05, 4.0, -0.5), SIOSBrand.mat_gold_emissive))
	# Armrests
	room.add_child(_box("AS_THRONE_ARM_L", Vector3(0.5, 0.5, 1.2), Vector3(-1.3, 1.5, 0.2), SIOSBrand.mat_gold))
	room.add_child(_box("AS_THRONE_ARM_R", Vector3(0.5, 0.5, 1.2), Vector3(1.3, 1.5, 0.2), SIOSBrand.mat_gold))
	# Hieroglyph columns flanking the throne
	for i in range(2):
		var x := -3 if i == 0 else 3
		_build_pillar(Vector3(x, 0, 0), 6.5, SIOSBrand.mat_hiero_dark, SIOSBrand.mat_gold, room, "AS_THRONE_COLUMN_%d" % i)
	# Backing wall with hieroglyph strip
	room.add_child(_box("AS_THRONE_BACK_WALL", Vector3(8, 7, 0.4), Vector3(0, 3.5, -2),
		_mat(Color("0a0606"), 0.1, 0.5)))
	room.add_child(_box("AS_THRONE_BACK_HIERO", Vector3(7.5, 0.15, 0.42), Vector3(0, 6, -2), SIOSBrand.mat_gold_emissive))
	# Steps leading up to the throne
	_build_steps(Vector3(0, 0, 3), 3, 4.0, 0.8, SIOSBrand.mat_dais, room, "AS_THRONE_STEP")
	return room

func _build_placeholder(room_id: String) -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_%s" % room_id.to_upper()
	room.add_child(_environment(Color("02070d"), SIOSBrand.COL_AMBIENT, 0.4))
	room.add_child(_build_floor(8.0, Color("080a0d")))
	room.add_child(_box("AS_PLACEHOLDER", Vector3(4, 2, 4), Vector3(0, 1, 0),
		SIOSBrand.mat_station))
	return room

# ------------------------------------------------------------------ panel rooms

func _build_panel_room(room_id: String) -> Node3D:
	var room := Node3D.new()
	room.name = "ROOM_%s" % room_id.to_upper()
	# Dark ambient environment
	room.add_child(_environment(Color("02070d"), SIOSBrand.COL_AMBIENT, 0.4))
	room.add_child(_build_floor(8.0, Color("080a0d")))
	# Pillar ring for structure
	var mat_col := _mat(SIOSBrand.COL_PILLAR, 0.3, 0.7)
	var mat_cap := _mat(SIOSBrand.COL_GOLD, 0.8, 0.3, SIOSBrand.COL_GOLD, 1.5)
	_build_pillar_ring(6.0, 6, 5.0, mat_col, mat_cap, room)
	# Ceiling
	_build_ceiling(6.0, 5.0, Color("030610"), room)
	# Central data pedestal
	var ped_mat := _mat(SIOSBrand.COL_STONE, 0.2, 0.8)
	var ped := _cylinder("DATA_PEDESTAL", 1.2, 1.0, Vector3(0, 0.5, 0), ped_mat)
	room.add_child(ped)
	# Holographic display above pedestal
	var display_mat := _mat(SIOSBrand.COL_DATA, 0.0, 0.2, SIOSBrand.COL_DATA, 2.0)
	var display := _box("DATA_DISPLAY", Vector3(2.5, 0.1, 2.5), Vector3(0, 1.2, 0), display_mat)
	room.add_child(display)
	# Room-specific accent
	var title_text := room_id.to_upper().replace("_", " ")
	var label_mat := _mat(SIOSBrand.COL_GOLD, 0.6, 0.4, SIOSBrand.COL_GOLD, 1.5)
	var label := _box(title_text, Vector3(3, 0.4, 0.1), Vector3(0, 2.5, -3), label_mat)
	room.add_child(label)
	return room
