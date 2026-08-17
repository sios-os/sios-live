"""Transportation/Trades K3 Batch 3 - 5 specialties."""

TRADES_K3_BATCH3: dict[str, list[dict]] = {
    "trades_residential_electrical_work": [
        {"title": "Residential Electrical Work Reference", "content": """# Residential Electrical Work Reference

## Service
### Service Entrance
- Service drop: overhead
- Service lateral: underground
- Meter: measure usage
- Main disconnect: shutoff
- Service panel: breakers

### Sizing
- Load calculation: NEC 220
- Service size: 100, 200, 400 amp
- Voltage: 120/240V single phase
- Grounding: electrode system
- Bonding: connect

## Panels
### Main Panel
- Breakers: overcurrent protection
- Main breaker: disconnect all
- Bus: distribute
- Neutral bar: white wires
- Ground bar: bare wires
- Bonding: neutral and ground

### Subpanel
- Fed from main
- Separate neutral and ground
- 4-wire feeder: 2 hot, 1 neutral, 1 ground
- Location: accessible

### Breakers
- Standard: 15, 20, 30, 50 amp
- GFCI: ground fault
- AFCI: arc fault
- CAFCI: combination arc fault
- Dual function: GFCI + AFCI
- Tandem: two in one space

## Branch Circuits
### General Purpose
- 15 amp: 14 AWG
- 20 amp: 12 AWG
- 30 amp: 10 AWG
- Voltage drop: 3% max

### Small Appliance
- Kitchen: 20 amp, two minimum
- Bathroom: 20 amp
- Laundry: 20 amp
- Garage: 20 amp

### Dedicated
- Range: 40-50 amp
- Dryer: 30 amp
- Water heater: 30 amp
- Furnace: 15-30 amp
- AC: per nameplate
- EV: 40-50 amp

## Wiring Methods
### Cable
- NM (Romex): non-metallic
  - 14/2, 12/2, 10/2
  - 14/3, 12/3: three wire
- AC (BX): armored cable
- MC: metal clad
- UF: underground feeder

### Conduit
- EMT: thin wall metal
- RMC: rigid metal
- IMC: intermediate metal
- PVC: plastic
- FMC: flexible metal
- ENT: thin wall plastic

### Wire
- THHN/THWN: insulated
- Size: AWG (American Wire Gauge)
- Color: black, red (hot); white (neutral); green, bare (ground)

## Boxes
### Types
- Junction: splice
- Device: switch, receptacle
- Ceiling: light
- Floor: outlet

### Sizing (NEC 314)
- Box fill: conductors, devices, clamps
- Volume: cubic inches
- Table: per wire size
- Minimum: per code

### Installation
- Secure: fasten
- Accessible: not hidden
- Cover: plate
- Depth: in wall

## Devices
### Receptacles
- 15 amp: standard
- 20 amp: T-slot
- GFCI: kitchen, bath, outside
- AFCI: bedrooms
- Tamper resistant: required
- USB: combined

### Switches
- Single pole: one location
- Three-way: two locations
- Four-way: three or more
- Dimmer: light control
- Timer: automatic
- Occupancy: sensor

### Lighting
- Recessed: can
- Surface: fixture
- Track: adjustable
- Under cabinet: task
- Landscape: outdoor
- Emergency: battery

## Grounding
### System
- Grounding electrode: rod, plate, water pipe
- Grounding conductor: to panel
- Bonding: connect all metal
- Equipment ground: bare or green

### Purpose
- Safety: fault current path
- Lightning: path to earth
- Static: dissipate
- Reference: voltage stable

## GFCI and AFCI
### GFCI (Ground Fault Circuit Interrupter)
- Detects: 4-6 mA imbalance
- Trips: opens circuit
- Locations: kitchen, bath, outside, garage, basement
- Protects: people

### AFCI (Arc Fault Circuit Interrupter)
- Detects: arcing
- Trips: opens circuit
- Locations: bedrooms, living areas
- Protects: fire

## Code (NEC)
### Key Articles
- 210: Branch circuits
- 240: Overcurrent protection
- 250: Grounding
- 300: Wiring methods
- 314: Boxes
- 410: Lighting
- 680: Pools, spas

### Safety
- De-energize: lockout/tagout
- Test: verify dead
- PPE: gloves, glasses
- Tools: insulated
- Working space: clear

## Inspection
### Rough-in
- Wiring: before drywall
- Boxes: installed
- Cables: secured
- Inspection: by AHJ

### Final
- Devices: installed
- Plates: on
- Fixtures: hung
- Service: complete
- Inspection: by AHJ

## Common Pitfalls
- Overloaded circuits
- Wrong wire size
- Inadequate grounding
- Box fill violations
- Not using GFCI/AFCI
- Improper splices
- Working hot (energized)
""", "tags": ["residential electrical", "wiring", "NEC", "panels", "grounding", "reference"]}
    ],
    "trades_plumbing": [
        {"title": "Plumbing Practice Reference", "content": """# Plumbing Practice Reference

## Water Supply
### Source
- Municipal: city water
- Well: private
- Pressure: 40-80 psi
- Flow: GPM

### Distribution
- Main: enters building
- Service line: to meter
- Meter: measure usage
- Main shut-off: stop all
- Branch lines: to fixtures

### Piping
- Copper: type L, M, K
  - Sweat: solder
  - Press: crimp
- PEX: cross-linked polyethylene
  - Crimp: ring
  - Expansion: sleeve
- CPVC: chlorinated PVC
- Galvanized: older

### Sizing
- Fixture units: IPC table
- Pipe size: based on demand
- Pressure: maintain
- Velocity: 5-8 fps max
- Friction: pressure loss

## Drainage
### DWV (Drain-Waste-Vent)
- Drain: carry waste
- Waste: from fixtures
- Vent: air for flow
- Stack: vertical
- Branch: horizontal
- Main: building drain

### Piping
- PVC: plastic (white)
- ABS: plastic (black)
- Cast iron: quiet
- Copper: DWV
- Size: 1.5" to 4"+

### Slope
- 1/4" per foot: 2.5" and smaller
- 1/8" per foot: 3" to 6"
- 1/16" per foot: 8" and larger

### Fittings
- Sanitary tee: vertical to horizontal
- Wye: 45 degree branch
- Combo: wye + 1/8 bend
- Elbow: 90, 45, 22.5
- Cleanout: access

## Vents
### Purpose
- Air: behind water
- Drain flow: prevent siphon
- Trap seal: maintain
- Pressure: equalize

### Types
- Individual: per fixture
- Common: multiple fixtures
- Wet: also drains
- Circuit: horizontal branch
- Loop: island sink
- Air admittance: one-way valve

### Sizing
- Based on drain size
- Minimum: 1.25"
- Stack: full size at base

## Traps
### Purpose
- Water seal: prevent sewer gas
- 2-4 inches: seal depth
- Self-cleaning: flow through

### Types
- P-trap: most common
- S-trap: not allowed (siphons)
- Drum: older
- Bottle: compact

### Location
- At each fixture
- Accessible: for cleaning
- Within 24" of trap arm
- Not in wall (access)

## Fixtures
### Water Closets (Toilets)
- Gravity: most common
- Pressure assisted: powerful
- Dual flush: water saving
- 1.28 GPF: low flow
- Rough-in: 10, 12, 14"

### Lavatories (Sinks)
- Bathroom: 1.5" drain
- Kitchen: 2" drain
- Service: utility
- Bar: prep

### Bathtubs and Showers
- Tub: 1.5" drain
- Shower: 2" drain
- Shower pan: waterproof
- Faucet: mixing valve

### Other
- Urinal: commercial
- Bidet: hygiene
- Water heater: hot water
- Washing machine: 2" drain

## Water Heaters
### Types
- Tank: storage
- Tankless: on demand
- Heat pump: efficient
- Solar: renewable
- Indirect: boiler

### Tank
- Capacity: 40-50 gallon typical
- Gas: most common
- Electric: no vent
- T&P valve: temperature/pressure
- Anode rod: corrosion
- Dip tube: cold to bottom

### Tankless
- Gas: high BTU
- Electric: limited
- Flow rate: GPM
- Temperature rise: degrees
- Sizing: demand

## Gas
### Natural Gas
- Pressure: low (inches water column)
- Piping: black steel, CSST, PE
- Sizing: BTU demand
- Shut-off: at each appliance
- Vent: combustion products

### LP (Propane)
- Tank: outside
- Regulator: pressure
- Piping: same as natural
- Heavier: settles low

## Codes
### IPC (International Plumbing Code)
- Scope: plumbing
- Water supply: sizing, protection
- Drainage: vents, slopes
- Fixtures: minimum
- Backflow: prevention
- Testing: required

### Backflow Prevention
- Cross-connection: hazard
- Air gap: physical separation
- RPZ: reduced pressure zone
- Double check: intermediate
- Atmospheric vacuum breaker: hose

## Inspection
### Rough-in
- Water: pressure test
- DWV: visual, slope
- Shower pan: flood test
- Inspection: by AHJ

### Final
- Fixtures: installed
- Trim: complete
- Test: function
- Inspection: by AHJ

## Common Pitfalls
- Wrong slope on drains
- Inadequate venting
- No cleanouts
- Trap seal loss
- Backflow risk
- Wrong pipe sizing
- Not testing
""", "tags": ["plumbing", "water supply", "drainage", "venting", "fixtures", "reference"]}
    ],
    "trades_hvac": [
        {"title": "HVAC Practice Reference", "content": """# HVAC Practice Reference

## Fundamentals
### Psychrometrics
- Dry bulb: air temperature
- Wet bulb: cooling effect
- Dew point: condensation
- Relative humidity: % saturation
- Enthalpy: heat content
- Psychrometric chart: relationships

### Heat Transfer
- Conduction: through material
- Convection: fluid movement
- Radiation: electromagnetic
- U-value: conductance
- R-value: resistance (1/U)

### Load Calculation
- Heat loss: winter
- Heat gain: summer
- Manual J: ACCA method
- Factors: climate, insulation, windows, infiltration
- CFM: airflow needed

## Heating
### Furnace
- Gas: most common
  - Burner: combustion
  - Heat exchanger: transfer
  - Blower: circulate
  - Flue: vent
  - Efficiency: 80%, 90%+
- Electric: resistance
  - Elements: heat
  - No vent
  - High operating cost
- Oil: less common

### Boiler
- Hot water: radiators
- Steam: older systems
- Fuel: gas, oil, electric
- Distribution: pipes
- Radiant: floor

### Heat Pump
- Air source: most common
  - Reversing valve: heat/cool
  - Compressor: pump
  - Outdoor coil: exchange
  - Indoor coil: exchange
  - Efficiency: HSPF
- Ground source (geothermal)
  - Loop: ground
  - Constant temperature
  - Efficient
  - Expensive

## Cooling
### Air Conditioner
- Split system: most common
  - Outdoor: condenser, compressor
  - Indoor: evaporator, blower
  - Lineset: refrigerant
- Package: all in one
- Window: room
- Portable: movable

### Refrigeration Cycle
1. Compressor: low to high pressure
2. Condenser: reject heat (outdoor)
3. Expansion: high to low pressure
4. Evaporator: absorb heat (indoor)
5. Return to compressor

### Refrigerants
- R-410A: current (Puron)
- R-22: phased out
- R-32: emerging
- R-134a: automotive
- EPA 608: certification

## Ventilation
### Purpose
- Fresh air: oxygen
- Remove: odors, moisture, pollutants
- Indoor air quality: health
- Pressurization: control

### Types
- Natural: infiltration, windows
- Exhaust: remove (bath, kitchen)
- Supply: bring in
- Balanced: equal in/out
- HRV/ERV: heat/energy recovery

### ASHRAE 62.2
- Ventilation rate: CFM
- Whole building: continuous
- Local: intermittent
- Infiltration: credit

## Ductwork
### Materials
- Sheet metal: galvanized
- Flex: flexible
- Duct board: fiberglass
- PVC: plastic

### Design
- Size: airflow (CFM)
- Velocity: 600-900 fpm
- Friction: pressure loss
- Fittings: minimize loss
- Dampers: balance
- Return: adequate

### Installation
- Support: hang
- Seal: mastic, tape
- Insulate: prevent loss
- Clear: not crushed
- Test: airflow

## Controls
### Thermostat
- Programmable: schedule
- Non-programmable: manual
- Smart: learning, WiFi
- Location: interior wall
- Heat/Cool: switch
- Fan: auto/on

### Zoning
- Multiple zones: dampers
- Separate thermostats
- Damper control
- Bypass: excess air

### Advanced
- BACnet: protocol
- Modbus: protocol
- DDC: direct digital control
- BAS: building automation
- Remote: monitor

## Air Quality
### Filtration
- MERV: rating (1-16)
- HEPA: high efficiency
- Media: deep pleated
- Electronic: electrostatic
- UV: germicidal

### Humidity
- Humidifier: add moisture (winter)
- Dehumidifier: remove (summer)
- Ideal: 30-50% RH
- Too low: dry, static
- Too high: mold, comfort

### Pollutants
- CO: carbon monoxide
- VOC: volatile organic
- Radon: radioactive gas
- Dust: particulate
- Pollen: allergen
- Mold: biological

## Sizing
### Manual J (ACCA)
- Load calculation
- Heating: BTU
- Cooling: BTU, CFM
- Factors: all heat gain/loss
- Not rule of thumb

### Manual S (ACCA)
- Equipment selection
- Match to load
- Sensible and latent
- Capacity: at design conditions

### Manual D (ACCA)
- Duct design
- Size: by CFM
- Friction: pressure
- Layout: efficient

## Efficiency
### Ratings
- AFUE: furnace (annual fuel utilization)
  - 80%: standard
  - 90%+: high efficiency
- SEER: AC (seasonal energy efficiency)
  - 13: minimum
  - 16-20: high
- HSPF: heat pump heating
  - 8.2: minimum
  - 10+: high
- EER: energy efficiency ratio

### Energy Star
- Higher than minimum
- Verified performance
- Tax credits: possible

## Maintenance
### Seasonal
- Spring: AC check
- Fall: furnace check
- Filters: change regularly
- Coils: clean
- Drain: clear

### Inspection
- Refrigerant: charge
- Electrical: connections
- Burner: combustion
- Heat exchanger: cracks
- Ducts: leaks

## Common Pitfalls
- Oversized equipment
- Poor duct design
- Inadequate ventilation
- Wrong refrigerant charge
- Dirty filters
- Leaky ducts
- Not following Manual J
""", "tags": ["HVAC", "heating", "cooling", "ventilation", "refrigeration", "reference"]}
    ],
    "trades_welding_metalworking": [
        {"title": "Welding and Metalworking Practice Reference", "content": """# Welding and Metalworking Practice Reference

## Welding Processes
### SMAW (Shielded Metal Arc Welding)
- Stick welding
- Electrode: flux coated
- Shielding: flux decomposes
- Slag: remove
- Applications: construction, repair
- Versatile: outdoor, dirty

### GMAW (Gas Metal Arc Welding)
- MIG welding
- Wire: continuous feed
- Shielding: gas (argon, CO2)
- Fast: high deposition
- Applications: fabrication, production
- Clean: no slag

### GTAW (Gas Tungsten Arc Welding)
- TIG welding
- Tungsten: non-consumable
- Filler: separate rod
- Shielding: argon
- High quality: precise
- Applications: thin, critical

### FCAW (Flux Cored Arc Welding)
- Wire: flux cored
- Shielding: gas + flux
- Fast: high deposition
- Outdoor: wind resistant
- Slag: remove

### Oxy-Fuel
- Torch: oxygen + acetylene
- Flame: 5500-6300F
- Welding: join
- Cutting: burn
- Brazing: braze
- Heating: bend

### Resistance
- Spot: lap joints
- Seam: continuous
- Projection: localized
- Applications: sheet metal, auto

## Welding Parameters
### Current
- DCEP: electrode positive (most)
- DCEN: electrode negative
- AC: alternating
- Amperage: heat
- Selection: by electrode, thickness

### Voltage
- Arc length: voltage
- Too long: wide, porous
- Too short: stubby
- Stable: consistent

### Travel Speed
- Fast: narrow, low penetration
- Slow: wide, high penetration
- Consistent: uniform bead

### Polarity
- DCEP: deeper penetration
- DCEN: faster deposition
- AC: medium

## Electrodes
### SMAW Classification (AWS)
- E6010, E6011: deep penetration
- E6013: general purpose
- E7018: low hydrogen, structural
- E7024: high deposition

### Coding
- E: electrode
- 60/70: tensile strength (ksi)
- 1: all positions; 2: flat/horizontal; 4: flat
- Last digits: coating, current

### Storage
- Low hydrogen: oven (250F+)
- Keep dry: prevent hydrogen
- Other: dry, clean

## Joint Design
### Types
- Butt: end to end
- Lap: overlap
- Tee: perpendicular
- Corner: L shape
- Edge: parallel

### Weld Types
- Fillet: triangular
- Groove: bevel, V, U, J
- Plug: holes
- Slot: elongated
- Surface: build up

### Preparation
- Bevel: angle
- Gap: root opening
- Land: root face
- Clean: remove oxide, oil

## Positions
### Plate
- 1G: flat
- 2G: horizontal
- 3G: vertical
- 4G: overhead

### Pipe
- 1G: rotated (flat)
- 2G: vertical pipe, horizontal weld
- 5G: fixed, multiple positions
- 6G: 45 degree fixed (most difficult)

## Weld Quality
### Discontinuities
- Porosity: gas pockets
- Inclusion: slag, tungsten
- Undercut: groove at edge
- Overfill: excess
- Underfill: insufficient
- Overlap: excess at toe
- Crater: end depression

### Defects
- Crack: reject
- Lack of fusion: reject
- Lack of penetration: reject
- Excessive porosity: reject

### Inspection
- Visual: surface
- Dye penetrant: surface
- Magnetic particle: surface/near
- Ultrasonic: internal
- Radiographic: internal (X-ray)
- Destructive: test sample

## Distortion
### Causes
- Heat: expansion
- Contraction: shrinkage
- Sequence: order of welds

### Control
- Tack weld: hold
- Sequence: alternate
- Clamp: restrain
- Preheat: reduce gradient
- Peening: relieve stress
- Backstep: weld direction

## Cutting
### Oxy-Fuel
- Torch: oxygen + fuel
- Preheat: flame
- Oxygen: jet (burns)
- Applications: thick steel
- Clean: slag

### Plasma
- Arc: ionized gas
- High speed: fast
- Any metal: conductive
- Clean: minimal slag
- CNC: automated

### Mechanical
- Saw: blade
- Shear: cut
- Grinder: abrasive
- Laser: precise
- Waterjet: cold cut

## Metalworking
### Forming
- Bending: angle
- Rolling: curve
- Press brake: sheet
- Stamping: shape
- Drawing: deep

### Machining
- Lathe: turn
- Mill: shape
- Drill: holes
- Grinder: finish

### Finishing
- Grinding: smooth
- Sanding: finer
- Polishing: shine
- Painting: protect
- Plating: coat
- Powder coat: durable

## Safety
### Hazards
- Arc flash: UV, IR
- Burns: hot metal
- Fumes: toxic
- Electric shock: live
- Fire: sparks
- Noise: loud
- Compressed gas: explosion

### PPE
- Helmet: shield (auto-darkening)
- Gloves: leather
- Jacket: protect
- Boots: steel toe
- Respirator: fumes
- Ear protection: noise

### Ventilation
- Fumes: remove
- Confined space: special
- Local exhaust: at source
- General: room

## Codes
### AWS D1.1
- Structural steel
- Welding procedure specification (WPS)
- Procedure qualification record (PQR)
- Welder qualification
- Inspection: visual, NDT

### ASME Section IX
- Pressure vessels
- Boilers
- Welding and brazing
- Qualification: procedure, performance

## Common Pitfalls
- Wrong parameters
- Poor joint preparation
- Inadequate cleaning
- Wrong electrode
- Not controlling distortion
- Poor shielding
- Inadequate safety
""", "tags": ["welding", "metalworking", "SMAW", "GMAW", "GTAW", "fabrication", "reference"]}
    ],
    "trades_machining": [
        {"title": "Machining Practice Reference", "content": """# Machining Practice Reference

## Processes
### Turning (Lathe)
- Workpiece: rotates
- Tool: single point, stationary
- Operations:
  - Facing: end cut
  - Turning: diameter
  - Boring: internal
  - Threading: helix
  - Drilling: holes
  - Parting: cut off
  - Knurling: texture

### Milling
- Cutter: rotates
- Workpiece: feeds
- Operations:
  - Face mill: flat surface
  - End mill: slots, pockets
  - Slab mill: wide surface
  - Side mill: side cut
  - Profile: contour
  - Drilling: holes
  - Tapping: threads

### Drilling
- Drill: rotates
- Holes: create
- Twist drill: common
- Operations:
  - Drilling: through
  - Blind: partial
  - Reaming: finish
  - Tapping: internal thread
  - Counterbore: recess
  - Countersink: chamfer

### Grinding
- Abrasive: hard particles
- Wheel: rotates
- Applications:
  - Surface: flat
  - Cylindrical: round
  - Internal: holes
  - Centerless: no centers
- Precision: tight tolerance
- Finish: smooth

## CNC
### Components
- Controller: computer
- Axes: X, Y, Z (3-axis)
- 4-axis: rotary
- 5-axis: rotary + tilt
- Spindle: rotates tool
- Servo: position
- ATC: automatic tool changer

### Programming
- G-code: machine language
  - G0: rapid
  - G1: feed
  - G2/G3: arc
  - G4: dwell
  - G20/G21: units
  - G90: absolute
  - G91: incremental
- M-code: miscellaneous
  - M3/M4: spindle on/off
  - M5: spindle stop
  - M6: tool change
  - M8/M9: coolant
  - M30: end

### CAM (Computer-Aided Manufacturing)
- Software: generate G-code
- Toolpaths: define
- Post-processor: machine specific
- Simulation: verify
- Common: Fusion 360, Mastercam

### Setup
- Workholding: vise, fixture, chuck
- Tooling: holders, inserts
- Offsets: tool length, diameter
- Coordinate system: G54
- Zero: set origin

## Cutting Tools
### Materials
- HSS: high speed steel
- Carbide: most common
- Coated: TiN, TiCN, Al2O3
- Ceramic: high speed
- Diamond: very hard
- CBN: cubic boron nitride

### Geometry
- Rake: cutting angle
- Relief: clearance
- Nose radius: corner
- Insert: replaceable tip

### Selection
- Material: workpiece
- Operation: type
- Speed: surface feet per minute
- Feed: per tooth
- Depth: cut

## Parameters
### Cutting Speed (SFM)
- Surface feet per minute
- Material dependent
- HSS: lower
- Carbide: higher
- Table: reference

### Feed Rate (IPM)
- Inches per minute
- Feed per tooth x teeth x RPM
- Chip load: important
- Too high: break tool
- Too low: rubbing

### Spindle Speed (RPM)
- RPM = SFM x 3.82 / diameter
- Higher: smaller tools
- Lower: larger tools

### Depth of Cut
- Roughing: deep
- Finishing: shallow
- Chip: must form

## Workholding
### Lathe
- Chuck: 3-jaw (self-centering)
- 4-jaw: independent
- Collet: precision
- Face plate: irregular
- Centers: between
- Mandrel: hold bore

### Mill
- Vise: most common
- Clamps: strap
- Fixture: custom
- Vacuum: flat
- Magnetic: ferrous
- Indexing: rotate

## Measurement
### Precision Tools
- Caliper: 0.001"
- Micrometer: 0.0001"
- Dial indicator: 0.0005"
- Height gauge: 0.001"
- Bore gauge: internal
- Thread gauge: pitch

### Inspection
- CMM: coordinate measuring
- Surface finish: Ra, Rz
- Gauge: go/no-go
- Optical: comparator
- Vision: digital

## Materials
### Metals
- Aluminum: easy, gummy
- Steel: common, harder
- Stainless: tough, work hardens
- Brass: easy, free machining
- Copper: gummy
- Titanium: hard, reactive
- Cast iron: abrasive

### Plastics
- Delrin: easy
- Nylon: tough
- Acrylic: brittle
- UHMW: slippery

## Coolant
### Purpose
- Cool: remove heat
- Lubricate: reduce friction
- Flush: remove chips
- Prevent: built-up edge
- Rust: prevent

### Types
- Flood: flow
- Mist: spray
- Air: blow
- Through-tool: internal

## Safety
### Hazards
- Rotating: entanglement
- Chips: sharp, hot
- Coolant: slippery
- Noise: loud
- Sharp tools: cut

### PPE
- Safety glasses: required
- No loose clothing
- No gloves (rotating)
- Hearing protection
- Steel toe boots

## Common Pitfalls
- Wrong speeds and feeds
- Dull tools
- Poor workholding
- Inadequate coolant
- Not checking dimensions
- Wrong tool selection
- Not deburring parts
""", "tags": ["machining", "turning", "milling", "CNC", "measurement", "reference"]}
    ],
}
