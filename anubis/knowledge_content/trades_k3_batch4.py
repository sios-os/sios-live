"""Transportation/Trades K3 Batch 4 - 5 specialties."""

TRADES_K3_BATCH4: dict[str, list[dict]] = {
    "trades_automotive_repair": [
        {"title": "Automotive Repair Practice Reference", "content": """# Automotive Repair Practice Reference

## Engine
### Four-Stroke Cycle
1. Intake: air/fuel in
2. Compression: squeeze
3. Power: ignite, expand
4. Exhaust: push out

### Components
- Block: main structure
- Pistons: move up/down
- Crankshaft: convert to rotation
- Camshaft: open valves
- Valves: intake, exhaust
- Head: top of cylinder
- Timing: belt/chain sync
- Oil: lubricate

### Diagnosis
- Compression test: cylinder seal
- Leak-down: locate leak
- Vacuum gauge: intake manifold
- OBD-II: codes
- Visual: leaks, wear

### Common Issues
- Misfire: spark, fuel, compression
- Overheating: coolant, thermostat, fan
- Oil leak: gaskets, seals
- Noise: bearings, lifters, knock
- Smoke: blue (oil), white (coolant), black (rich)

## Fuel System
### Gasoline
- Injector: spray fuel
- Pump: deliver
- Filter: clean
- Pressure: regulate
- Rail: distribute
- Throttle: air control

### Diagnosis
- Pressure: gauge
- Injector: balance, scope
- Fuel: quality
- Air/fuel: ratio (14.7:1)

### Common Issues
- No start: no fuel
- Lean: not enough
- Rich: too much
- Clogged: injector, filter

## Ignition
### Components
- Coil: high voltage
- Distributor: older
- Spark plug: ignite
- Wire: connect
- Module: control
- Crank sensor: timing

### Diagnosis
- Spark: tester
- Plug: read condition
- Wire: resistance
- Coil: output

### Common Issues
- Misfire: weak spark
- No start: no spark
- Foul: plug deposits
- Gap: wrong

## Electrical
### Battery
- 12V: lead acid
- Capacity: CCA (cold cranking amps)
- Test: voltage, load
- Maintenance: clean, charge

### Charging
- Alternator: generate
- Regulator: control
- Belt: drive
- Test: voltage (13.5-14.5V)

### Starting
- Starter: crank engine
- Solenoid: engage
- Test: current draw

### Diagnosis
- Multimeter: voltage, current
- Load test: battery
- Voltage drop: resistance
- OBD-II: codes

## Brakes
### Types
- Disc: most common (front)
  - Rotor: disc
  - Caliper: squeeze
  - Pad: friction
  - Piston: apply
- Drum: rear (older)
  - Drum: rotate
  - Shoe: friction
  - Wheel cylinder: apply

### Hydraulic
- Master cylinder: pressure
- Booster: assist (vacuum)
- Lines: distribute
- Fluid: DOT 3, 4, 5.1
- ABS: prevent lock

### Diagnosis
- Pedal: low, spongy
- Noise: squeal, grind
- Pull: side to side
- Vibration: pulsation
- Warning: light

### Service
- Pads: replace
- Rotors: machine or replace
- Bleed: remove air
- Fluid: flush
- Parking brake: adjust

## Suspension
### Components
- Springs: support (coil, leaf, air)
- Shocks/struts: dampen
- Control arms: locate
- Bushings: cushion
- Ball joints: pivot
- Sway bar: reduce roll

### Alignment
- Camber: tilt in/out
- Caster: forward/back tilt
- Toe: in/out
- Thrust: rear axle direction
- Spec: per vehicle

### Diagnosis
- Bounce: worn shocks
- Noise: clunk, squeak
- Wear: tire pattern
- Pull: alignment
- Lean: spring

## Steering
### Types
- Rack and pinion: most common
- Recirculating ball: older
- Power: hydraulic, electric

### Components
- Steering wheel: input
- Column: connect
- Rack: convert
- Tie rod: to wheel
- Pump: power (hydraulic)

### Diagnosis
- Play: loose
- Stiff: power loss
- Noise: whine
- Leak: fluid
- Wander: alignment

## Transmission
### Automatic
- Torque converter: connect
- Pump: pressure
- Valve body: control
- Clutches: engage
- Bands: hold
- Gears: ratios
- Fluid: lubricate, cool

### Manual
- Clutch: disconnect
- Gears: select
- Synchro: match speed
- Shafts: input, output, counter
- Fluid: gear oil

### Diagnosis
- Slipping: low pressure, worn
- Hard shift: pressure, solenoid
- No move: internal failure
- Leak: gasket, seal
- Noise: bearing, gear
- Fluid: color, level

### Service
- Fluid: check, change
- Filter: replace
- Adjustment: bands (some)

## Tires
### Specifications
- Size: P215/65R15
  - P: passenger
  - 215: width (mm)
  - 65: aspect ratio
  - R: radial
  - 15: wheel diameter
- Load index: weight
- Speed rating: max speed
- DOT: date code

### Maintenance
- Pressure: check monthly
- Rotation: every 5-8k miles
- Balance: prevent vibration
- Alignment: prevent wear
- Tread: depth (2/32" min)

### Diagnosis
- Wear: center (over), edge (under), cupped (shocks), feathered (alignment)
- Vibration: balance
- Pull: alignment, tire
- Noise: tread, bearing

## HVAC
### Components
- Compressor: pump
- Condenser: reject heat
- Evaporator: absorb heat
- Expansion: regulate
- Refrigerant: 134a, 1234yf
- Blower: circulate

### Service
- Charge: level
- Leak: detect
- Evacuate: remove
- Recharge: add
- Odor: cabin filter

## Exhaust
### Components
- Manifold: collect
- Catalytic converter: reduce emissions
- Muffler: quiet
- Pipe: connect
- O2 sensor: feedback

### Emissions
- CO: rich
- HC: unburned
- NOx: high temp
- O2: lean
- Catalytic: convert

## OBD-II
### Codes
- P: powertrain
- B: body
- C: chassis
- U: network
- Format: P0301 (cylinder 1 misfire)

### Diagnosis
- Scan: read codes
- Freeze frame: when set
- Live data: parameters
- Test: verify
- Clear: erase

## Common Pitfalls
- Not diagnosing before replacing
- Ignoring safety
- Wrong parts
- Not torquing fasteners
- Skipping tests
- Contaminating fluids
- Not following procedures
""", "tags": ["automotive repair", "engine", "brakes", "transmission", "diagnostics", "reference"]}
    ],
    "trades_appliance_repair": [
        {"title": "Appliance Repair Practice Reference", "content": """# Appliance Repair Practice Reference

## Safety
### Electrical
- Unplug: before service
- Capacitor: discharge
- Ground: prevent shock
- GFCI: wet areas

### General
- Gas: shut off
- Water: shut off
- Hot: wait to cool
- Sharp: edges
- Heavy: lift safely

## Diagnosis Method
### Process
1. Symptom: what's wrong
2. Visual: inspect
3. Test: measure
4. Isolate: find cause
5. Replace: part
6. Verify: works

### Tools
- Multimeter: voltage, resistance, current
- Clamp meter: current
- Thermometer: temperature
- Manifold: refrigerant
- Specialty: per appliance

## Refrigerator
### Components
- Compressor: pump
- Condenser: reject heat (back/bottom)
- Evaporator: absorb heat (inside)
- Capillary: restrict
- Thermostat: control
- Defrost: timer, heater, terminator
- Fan: evaporator, condenser
- Damper: air control

### Common Issues
- Not cooling: compressor, fan, defrost, leak
- Frost: defrost failure
- Noise: fan, compressor
- Leak: water, defrost drain
- Ice maker: water, motor, mold

### Diagnosis
- Temperature: check
- Compressor: run, vibration
- Fan: spin
- Defrost: continuity
- Refrigerant: pressure (sealed system)

### Sealed System
- Compressor: replace
- Leak: find, repair
- Evacuate: vacuum
- Recharge: weigh in

## Washer
### Components
- Motor: drive
- Transmission: agitate, spin
- Pump: drain
- Valve: fill
- Timer: control
- Lid switch: safety
- Belt: drive (some)
- Control board: electronic

### Common Issues
- No fill: valve, screen, pressure
- No agitate: motor, transmission, coupling
- No spin: lid switch, clutch, transmission
- No drain: pump, hose, filter
- Leak: hose, pump, seal
- Noise: bearing, pump

### Diagnosis
- Fill: voltage to valve
- Agitate: motor, coupling
- Spin: lid switch, clutch
- Drain: pump, voltage
- Timer: continuity

## Dryer
### Components
- Motor: drive drum, fan
- Heater: gas or electric
- Thermostat: control
- Thermal fuse: safety
- Igniter: gas (glow bar)
- Flame sensor: gas
- Gas valve: gas
- Timer: control
- Belt: drive
- Lint filter: trap

### Common Issues
- No heat: element, igniter, fuse, gas valve
- No tumble: belt, motor, door switch
- Long time: vent clogged
- Noise: roller, bearing, blower
- No start: door switch, thermal fuse, timer

### Diagnosis
- Heat: voltage, continuity
- Gas: igniter, flame sensor, valve
- Vent: airflow, clog
- Thermal: continuity

### Safety
- Lint: fire hazard
- Vent: clean regularly
- Gas: leak check

## Dishwasher
### Components
- Motor: pump, wash, drain
- Heater: water heat, dry
- Valve: fill
- Timer/control: cycle
- Float: water level
- Spray arm: distribute
- Dispenser: soap, rinse aid
- Thermostat: temperature

### Common Issues
- No fill: valve, float, pressure
- No wash: motor, pump, spray arm
- No drain: pump, hose, filter
- No heat: element, thermostat
- Leak: door seal, hose, pump
- Noise: pump, spray arm

### Diagnosis
- Fill: voltage, float
- Wash: motor, spray arm (clogged)
- Drain: pump, voltage, hose
- Heat: continuity
- Leak: observe

## Oven/Range
### Components
- Bake element: bottom
- Broil element: top
- Igniter: gas (glow)
- Gas valve: gas
- Thermostat: control
- Sensor: temperature
- Control board: electronic
- Surface element: cooktop
- Infinite switch: surface control

### Common Issues
- No bake: element, igniter, valve, control
- No broil: element, igniter
- Uneven: element, calibration
- No ignite: igniter, spark module
- No heat: element, control
- Self-clean: door lock, thermostat

### Diagnosis
- Element: continuity
- Gas igniter: amperage (2.5-3.5A)
- Gas valve: continuity, voltage
- Sensor: resistance (1080 ohms at 70F)
- Control: voltage

### Gas
- Igniter: glow bar
- Valve: opens when hot
- Safety: no gas without ignition
- Pressure: natural (3.5" WC), LP (10-11" WC)

## Microwave
### Components
- Magnetron: generate microwaves
- Capacitor: high voltage
- Transformer: step up
- Diode: rectify
- Turntable: rotate
- Control: timer
- Door switch: safety
- Fuse: protect

### Common Issues
- No heat: magnetron, diode, capacitor, transformer
- No run: door switch, fuse, control
- Spark: waveguide cover, food
- Noise: magnetron, fan
- Turntable: motor, coupler

### Safety
- HIGH VOLTAGE: capacitor retains
- Discharge: before service
- Radiation: door seal, hinges
- Magnetron: handle carefully

## Disposer
### Components
- Motor: drive
- Impeller: grind
- Flywheel: turn
- Breaker: reset
- Mount: sink

### Common Issues
- Jam: foreign object
- Hum: jammed, stuck
- No run: breaker, motor
- Leak: seal, mount
- Slow: clog, dull

### Service
- Reset: breaker
- Unjam: Allen wrench (bottom)
- Clean: ice, citrus
- Replace: if worn

## Small Appliances
### Common Components
- Motor: drive
- Heater: element
- Switch: control
- Cord: power
- Thermostat: temperature

### Diagnosis
- Power: cord, switch
- Motor: continuity, run
- Heat: element, thermostat
- Mechanical: inspect

## Common Pitfalls
- Not checking power first
- Replacing parts without diagnosis
- Ignoring safety (capacitor, gas)
- Not cleaning (lint, coils)
- Wrong part number
- Not testing after repair
- Forgetting to plug in
""", "tags": ["appliance repair", "refrigerator", "washer", "dryer", "diagnostics", "reference"]}
    ],
    "trades_electronics_repair": [
        {"title": "Electronics Repair Practice Reference", "content": """# Electronics Repair Practice Reference

## Safety
### Electrical
- Unplug: before service
- Capacitor: discharge (large)
- Isolation transformer: for hot chassis
- One hand: prevent shock path

### ESD (Electrostatic Discharge)
- Wrist strap: ground
- Mat: grounded work surface
- Bag: shield components
- Humidity: control
- Sensitive: MOS, CMOS

## Tools
### Hand
- Screwdriver: Phillips, flat, Torx
- Pliers: needle, cutter
- Tweezers: handle parts
- Spudger: pry
- Suction: remove solder

### Soldering
- Iron: temperature controlled
- Tip: various sizes
- Solder: 60/40 or lead-free
- Flux: clean
- Wick: remove solder
- Pump: suck solder

### Test Equipment
- Multimeter: V, R, I, continuity
- Oscilloscope: waveform
- Logic probe: digital
- Signal generator: inject
- Power supply: bench
- ESR meter: capacitor
- Component tester: LCR

## Soldering
### Through-Hole
- Insert: component
- Heat: pad and lead
- Apply: solder
- Remove: iron
- Inspect: shiny, cone

### Surface Mount
- Solder paste: stencil
- Place: component
- Heat: hot air or oven
- Inspect: alignment

### Desoldering
- Wick: absorb
- Pump: suck
- Hot air: melt
- Iron: melt, remove

### Tips
- Clean tip: sponge, brass
- Tin: coat tip
- Temperature: 350-400C
- Don't overheat: damage
- Flux: essential

## Diagnosis
### Process
1. Symptom: what's wrong
2. Visual: inspect
3. Power: check supply
4. Signal: trace
5. Component: test
6. Replace: faulty
7. Verify: works

### Visual Inspection
- Burn: resistor, board
- Bulge: capacitor (electrolytic)
- Leak: capacitor
- Crack: board, component
- Cold solder: dull, cracked
- Corrosion: green, white
- Wire: broken, frayed

### Power Supply
- Voltage: correct level
- Ripple: AC on DC
- Current: capacity
- Regulation: stable
- Protection: fuse, breaker

### Signal Tracing
- Input: inject signal
- Output: measure
- Stage by stage: isolate
- Compare: to known good
- Schematic: reference

## Components
### Resistor
- Color code: bands
- Measure: ohms
- Failure: open (most), value change
- Variable: potentiometer

### Capacitor
- Types: ceramic, electrolytic, film, tantalum
- Measure: capacitance, ESR
- Failure: short, open, high ESR, leak
- Electrolytic: age, heat

### Inductor
- Measure: inductance, resistance
- Failure: open (wire)
- Cores: ferrite, iron

### Diode
- Test: forward, reverse
- Forward: 0.6-0.7V (silicon)
- Failure: short, open
- Zener: breakdown voltage
- LED: light

### Transistor
- BJT: NPN, PNP
  - Test: junctions
  - Beta: gain
  - Failure: short, open
- MOSFET: N, P channel
  - Test: gate, drain, source
  - Failure: short (most)
  - Gate: sensitive to ESD

### IC (Integrated Circuit)
- Test: in circuit, out
- Voltages: pins
- Signals: clock, data
- Heat: run hot
- Substitute: known good

## Common Failures
### Capacitors
- Electrolytic: dry out, leak
- High ESR: switching supplies
- Bulging: top domed
- Replace: same or better

### Cold Solder Joints
- Dull, cracked: reflow
- Common: high stress
- Vibration: cause
- Fix: reflow, add solder

### Connectors
- Corrosion: clean
- Loose: tighten, replace
- Bent pins: straighten
- Cold solder: reflow

### Fuses
- Open: overcurrent
- Replace: same rating
- Slow blow: time delay
- Investigate: why blew

## Power Supplies
### Linear
- Transformer: step down
- Rectifier: AC to DC
- Filter: capacitor
- Regulator: stable voltage
- Simple, reliable, inefficient

### Switching (SMPS)
- Rectifier: AC to DC
- Switch: transistor, high freq
- Transformer: isolate
- Rectifier: DC
- Filter: capacitor
- Regulator: PWM
- Efficient, complex

### Diagnosis
- Fuse: check first
- Bridge: rectifier
- Switch: transistor
- Controller: IC
- Output: voltage
- Feedback: opto

## Circuit Boards
### Types
- Single layer: one side
- Double layer: two sides
- Multi-layer: inner layers
- Flexible: bend
- Green: mask

### Repair
- Trace: cut, repair
  - Wire: jumper
  - Copper: foil
- Pad: lifted
  - Epoxy: secure
  - Wire: alternate
- Via: hole
  - Wire: through

## Common Pitfalls
- Not discharging capacitors
- Replacing without diagnosis
- Heat damage: too hot
- ESD damage: no protection
- Wrong component: substitute
- Cold solder: poor joint
- Not testing after repair
""", "tags": ["electronics repair", "soldering", "diagnostics", "components", "reference"]}
    ],
    "trades_computer_repair": [
        {"title": "Computer Repair Practice Reference", "content": """# Computer Repair Practice Reference

## Hardware
### Components
- Motherboard: main board
- CPU: processor
- RAM: memory
- Storage: HDD, SSD
- GPU: graphics
- PSU: power supply
- Case: enclosure
- Cooling: fan, heatsink
- Peripherals: input, output

### Motherboard
- Chipset: north/south bridge
- BIOS/UEFI: firmware
- Slots: RAM, PCIe
- Ports: USB, audio, network
- Connectors: power, front panel
- Battery: CMOS

### CPU
- Socket: LGA, PGA
- Cores: 2, 4, 8, 16+
- Clock: GHz
- Cache: L1, L2, L3
- Thermal: paste, cooler
- Power: TDP

### RAM
- Types: DDR4, DDR5
- Speed: MHz
- Capacity: GB
- Channels: dual, quad
- ECC: error correction
- Timing: CAS latency

### Storage
- HDD: spinning disk
  - SATA: 6 Gbps
  - RPM: 5400, 7200, 10k
  - Cache: MB
- SSD: solid state
  - SATA: 6 Gbps
  - NVMe: PCIe (fast)
  - M.2: form factor
  - Endurance: TBW

### GPU
- Integrated: in CPU
- Discrete: separate card
- VRAM: video memory
- PCIe: interface
- Power: 6/8 pin
- Drivers: software

### PSU
- Wattage: total
- Efficiency: 80 Plus (Bronze, Gold, Platinum)
- Modular: cables
- Rails: 12V, 5V, 3.3V
- Connectors: 24-pin, CPU, PCIe, SATA, Molex

## Diagnosis
### POST (Power-On Self-Test)
- Beep codes: BIOS
- Debug LED: motherboard
- POST card: diagnostic
- No POST: power, CPU, RAM, motherboard

### Process
1. Symptom: what's wrong
2. Visual: inspect
3. Power: check
4. POST: boot
5. Isolate: swap parts
6. Test: verify

### Common Issues
- No power: PSU, switch, cord
- No POST: RAM, GPU, CPU, motherboard
- Random restart: heat, PSU, RAM
- Blue screen: driver, hardware, RAM
- Slow: malware, disk, RAM
- Noise: fan, HDD

## Troubleshooting
### No Power
- Outlet: test
- Cord: check
- Switch: on
- PSU: test (paperclip)
- Motherboard: short

### No POST
- RAM: reseat, one stick
- GPU: reseat, try integrated
- CPU: reseat, check paste
- Motherboard: breadboard
- Clear CMOS: reset

### Random Restart
- Temperature: monitor
- PSU: load test
- RAM: memtest
- Capacitors: bulging
- Drivers: update

### Blue Screen (BSOD)
- Code: look up
- Driver: verifier
- Hardware: RAM, disk
- Malware: scan
- System restore: rollback

### Slow
- Task manager: processes
- Malware: scan
- Startup: disable
- Disk: defrag (HDD), trim (SSD)
- RAM: upgrade
- Temperature: thermal throttle

## Software
### Operating System
- Windows: most common
- macOS: Apple
- Linux: open source
- Chrome OS: web

### Installation
- Boot: USB/DVD
- Partition: disk
- Format: file system
- Install: copy files
- Drivers: install
- Updates: patch

### Drivers
- Manufacturer: latest
- Device manager: check
- Update: fix issues
- Rollback: if problem
- Safe mode: minimal

### Registry (Windows)
- Settings: database
- Backup: before edit
- Regedit: tool
- Clean: careful
- Corrupt: repair

## Malware
### Types
- Virus: replicates
- Worm: spreads
- Trojan: disguised
- Spyware: monitors
- Ransomware: encrypts
- Adware: ads
- Rootkit: hidden

### Removal
- Safe mode: minimal
- Scanner: anti-malware
- Boot scan: before OS
- Restore: backup
- Clean install: last resort

### Prevention
- Antivirus: real-time
- Updates: patch
- Firewall: enable
- Email: caution
- Downloads: trusted source
- Backup: regular

## Data Recovery
### Causes
- Delete: accidental
- Format: wrong drive
- Corrupt: file system
- Fail: hardware
- Virus: damage

### Methods
- Recycle bin: restore
- Software: recover
- Professional: clean room
- Backup: restore
- Shadow copy: Windows

### Prevention
- Backup: 3-2-1 rule
  - 3 copies
  - 2 different media
  - 1 offsite
- Cloud: automatic
- Image: full system

## Networking
### Wired
- Ethernet: CAT5e, CAT6
- Speed: 1 Gbps typical
- Switch: connect
- Router: route

### Wireless
- WiFi: 802.11ac, ax
- Frequency: 2.4, 5 GHz
- Security: WPA2, WPA3
- Signal: strength

### Issues
- No connection: cable, driver
- Slow: interference, bandwidth
- Drop: signal, driver
- Can't find: SSID, adapter

## Maintenance
### Physical
- Dust: clean (compressed air)
- Fans: check
- Thermal paste: replace
- Cables: organize
- Temperature: monitor

### Software
- Updates: OS, drivers
- Disk: cleanup, defrag/trim
- Malware: scan
- Startup: minimize
- Services: review

## Tools
- Screwdriver: Phillips, Torx
- Multimeter: voltage
- USB: bootable
- Anti-static: strap, mat
- Thermal paste: compound
- Compressed air: clean
- Diagnostic: Memtest, CrystalDisk

## Common Pitfalls
- Not backing up before work
- Forcing connectors
- Static damage
- Wrong part
- Not testing after repair
- Over-tightening screws
- Ignoring thermal issues
""", "tags": ["computer repair", "hardware", "software", "diagnostics", "reference"]}
    ],
    "trades_painting_finishing": [
        {"title": "Painting and Finishing Practice Reference", "content": """# Painting and Finishing Practice Reference

## Surface Preparation
### Cleaning
- Wash: dirt, grease
- TSP: trisodium phosphate
- Degreaser: oil
- Bleach: mildew
- Rinse: clean
- Dry: before paint

### Repair
- Patch: holes, cracks
  - Spackle: small
  - Joint compound: large
  - Caulk: gaps
- Sand: smooth
- Prime: bare areas
- Scrape: loose paint
- Sand: existing gloss

### Sanding
- Coarse: 60-80 grit (remove)
- Medium: 100-150 grit (smooth)
- Fine: 180-220 grit (finish)
- Sponge: contours
- Block: flat
- Pole: large areas

## Paint Types
### Water-Based (Latex)
- Acrylic: durable
- Vinyl: cheaper
- Easy cleanup: water
- Fast dry: 1-2 hours
- Low odor: VOC
- Flexible: resists cracking
- Not over oil (without primer)

### Oil-Based (Alkyd)
- Durable: hard
- Smooth: flow
- Slow dry: 8-24 hours
- Cleanup: mineral spirits
- High odor: VOC
- Yellow: over time
- Good for: trim, doors

### Specialty
- Primer: base coat
- Enamel: hard finish
- Epoxy: chemical resistant
- Polyurethane: floor
- Elastomeric: masonry
- Heat: stove, radiator
- Rust: metal

## Primers
### Purpose
- Adhesion: bond
- Seal: porous
- Stain: block
- Uniform: surface
- Coverage: hide

### Types
- Latex: water based
- Oil: solvent based
- Shellac: fast, stain block
- Bonding: glossy surfaces
- Stain blocking: water, smoke, tannin

### Selection
- Surface: drywall, wood, metal
- Topcoat: latex, oil
- Condition: new, stained
- Location: interior, exterior

## Sheen
### Flat (Matte)
- No shine
- Hides imperfections
- Not washable
- Ceilings, low traffic
- Touch up: easy

### Eggshell
- Slight shine
- Washable: moderate
- Walls: living areas
- Popular: general

### Satin
- Soft shine
- Washable: good
- Walls, trim
- Bathrooms, kitchens

### Semi-Gloss
- Noticeable shine
- Washable: very good
- Trim, doors, cabinets
- Bathrooms, kitchens

### Gloss
- High shine
- Washable: excellent
- Doors, trim, cabinets
- Shows imperfections

## Interior Painting
### Order
1. Ceiling: first
2. Walls: second
3. Trim: third
4. Doors: fourth
5. Windows: fifth
6. Base: last

### Cutting In
- Brush: 2-3" at edges
- Where: ceiling, corners, trim
- Before: roll
- Steady: hand
- Quality: matters

### Rolling
- Nap: 3/8" (smooth), 1/2" (medium), 3/4" (rough)
- Load: tray
- Apply: W pattern
- Spread: smooth
- Maintain: wet edge
- Backroll: blend

### Technique
- Top to bottom
- One wall at a time
- Wet edge: blend
- Two coats: typical
- Dry between: per label

## Exterior Painting
### Preparation
- Wash: pressure wash
- Scrape: loose paint
- Sand: smooth edges
- Repair: wood, caulk
- Prime: bare areas
- Mask: windows, doors

### Conditions
- Temperature: 50-90F
- Humidity: not too high
- Wind: not too strong
- Rain: not imminent
- Sun: avoid direct (hot)

### Order
1. Siding: body
2. Trim: contrasting
3. Doors: accent
4. Shutters: accent
5. Porch: last

### Siding Materials
- Wood: prime, paint
- Vinyl: special paint, no primer
- Aluminum: prime, paint
- Stucco: masonry paint
- Brick: masonry paint (optional)

## Trim and Doors
### Preparation
- Fill: nail holes
- Caulk: gaps
- Sand: smooth
- Prime: bare

### Painting
- Brush: trim
- Flow: smooth
- Avoid: drips
- Sand between: smooth
- Two coats: typical

## Cabinets
### Preparation
- Clean: degrease
- Remove: hardware
- Sand: dull gloss
- Prime: bonding

### Painting
- Brush or spray
- Enamel: hard finish
- Multiple coats
- Sand between
- Cure: 2-3 weeks

## Drywall Finishing
### Levels
- Level 1: tape
- Level 2: skim coat
- Level 3: for heavy texture
- Level 4: for flat paint
- Level 5: for gloss

### Process
1. Tape: joints
2. Mud: first coat
3. Sand: smooth
4. Mud: second coat
5. Sand: smooth
6. Mud: third coat
7. Sand: final
8. Prime: seal

## Staining
### Preparation
- Sand: smooth (150-220)
- Clean: dust
- Conditioner: soft wood

### Application
- Wipe: with rag
- Brush: even
- Wipe excess: even
- Dry: per label
- Coats: as needed

### Types
- Oil: penetrating
- Water: fast dry
- Gel: even color
- Dye: bright

## Clear Finishes
### Types
- Polyurethane: most common
  - Oil: durable, amber
  - Water: clear, fast
- Varnish: traditional
- Lacquer: fast, spray
- Shellac: sealer
- Oil: penetrating (Tung, linseed)

### Application
- Brush: polyurethane
- Spray: lacquer
- Wipe: oil
- Sand between: 220+
- Coats: 2-3 typical

## Wallpaper
### Removal
- Score: perforate
- Wet: solvent
- Scrape: off
- Clean: residue
- Repair: wall

### Installation
- Prime: wall
- Measure: length
- Cut: strips
- Paste: activate
- Book: fold
- Hang: top to bottom
- Smooth: bubbles
- Trim: edges

## Equipment
### Brushes
- Nylon: latex
- Natural: oil
- Angle: corners, trim
- Flat: walls
- Quality: matters

### Rollers
- Nap: per surface
- Frame: sturdy
- Extension: pole
- Tray: load

### Sprayers
- Airless: fast, high pressure
- HVLP: fine finish
- Compressed: traditional
- Cleanup: important

## Common Pitfalls
- Poor preparation
- Wrong paint for surface
- Painting over gloss without sanding
- Not using primer
- Wrong nap roller
- Painting in wrong conditions
- Rushing between coats
- Not maintaining wet edge
""", "tags": ["painting", "finishing", "surface preparation", "staining", "reference"]}
    ],
}
