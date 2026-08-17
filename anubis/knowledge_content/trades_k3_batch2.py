"""Transportation/Trades K3 Batch 2 - 6 specialties."""

TRADES_K3_BATCH2: dict[str, list[dict]] = {
    "trades_maritime_operations": [
        {"title": "Maritime and Port Operations Reference", "content": """# Maritime and Port Operations Reference

## Ship Operations
### Navigation
- Position: GPS, celestial
- Course: heading
- Speed: knots
- Chart: nautical map
- Pilotage: local waters
- Passage planning: route

### Watchkeeping
- Officer: in charge
- Lookout: visual
- Helm: steering
- Engine: room
- STCW: standards
- Hours of rest: required

### Bridge
- Equipment: radar, ECDIS, AIS
- Procedures: COLREGS
- Communication: VHF
- Logs: record
- Alarms: monitor

## Port Operations
### Types
- Container: boxes
- Bulk: loose cargo
- Breakbulk: individual
- Ro-Ro: roll on/off
- Liquid: tanker
- Cruise: passengers
- Multi-purpose: mixed

### Container Terminal
- Berth: ship position
- Quay crane: load/unload
- Yard: storage
- Gate: in/out
- Equipment: RTG, straddle, reach stacker
- TOS: terminal operating system

### Cargo Handling
- Loading: onto ship
- Discharging: off ship
- Stowage: placement
- Lashing: secure
- Hatch: cover
- Draft: check

### Documentation
- B/L: bill of lading
- Manifest: cargo list
- Stowage plan: location
- Cargo declaration
- Customs: clearance

## Pilotage
### Purpose
- Local knowledge
- Safe navigation
- Harbor entry/exit
- Mandatory: most ports

### Process
- Board: pilot boat
- Advice: to master
- Conning: directions
- Disembark: after passage

### Types
- Port: harbor
- River: inland
- Sea: offshore
- Deep sea: ocean

## Tug Operations
### Purpose
- Assist: maneuver
- Tow: barge
- Salvage: rescue
- Escort: safety

### Types
- Conventional: twin screw
- Tractor: omnidirectional
- ASD: azimuth stern drive
- Rotor: Voith-Schneider

### Services
- Berthing: push/pull
- Unberthing: pull off
- Escort: emergency
- Tow: barge

## Marine Safety
### COLREGS
- International regulations
- Steering and sailing rules
- Lights and shapes
- Sound signals
- Distress signals

### SOLAS
- Safety of Life at Sea
- Construction: subdivision
- Fire: protection
- Lifesaving: appliances
- Radio: communication
- Navigation: safety
- Operations: management

### MARPOL
- Marine pollution
- Annex I: oil
- Annex II: chemicals
- Annex III: harmful substances
- Annex IV: sewage
- Annex V: garbage
- Annex VI: air pollution

### STCW
- Standards of Training, Certification, Watchkeeping
- Master, officers, ratings
- Basic training: safety
- Advanced: specialization
- Medical: fitness

## Cargo Types
### Container
- TEU: twenty-foot equivalent
- FEU: forty-foot equivalent
- Reefer: refrigerated
- Tank: liquids
- Flatrack: oversized
- Open top: tall

### Bulk
- Dry: grain, coal, ore
- Liquid: oil, chemicals
- Breakbulk: individual
- Neo-bulk: cars, lumber

### Special
- Ro-Ro: vehicles
- Heavy lift: oversized
- Project: custom
- Livestock: animals
- Refrigerated: perishable

## Port Infrastructure
### Berth
- Quay: parallel
- Pier: perpendicular
- Dolphin: isolated
- Length: ship size
- Depth: draft

### Equipment
- Crane: quay, gantry, mobile
- Reach stacker: container
- Forklift: pallet
- Tractor/trailer: yard
- Conveyor: bulk
- Pump: liquid

### Yard
- Storage: containers, bulk
- Layout: blocks, rows
- Handling: move
- Gate: in/out
- Reefer: power

## Customs and Trade
### Documentation
- B/L: bill of lading
- Commercial invoice
- Packing list
- Certificate of origin
- Import/export license

### Clearance
- Entry: import
- Declaration: goods
- Duty: tax
- Examination: inspect
- Release: approve

### Free Trade Zones
- Bonded: defer duty
- Free: no duty
- Special economic
- Transshipment: transfer

## Marine Environment
### Pollution Prevention
- Oil: separator, SOPEP
- Chemical: procedures
- Garbage: management plan
- Sewage: treatment
- Air: emissions (sulfur, NOx)
- Ballast water: exchange

### Spill Response
- Report: immediate
- Contain: boom
- Recover: skimmer
- Disperse: chemicals
- Clean: shore
- Investigate: cause

## Vessel Traffic
### VTS (Vessel Traffic Service)
- Monitor: traffic
- Information: broadcast
- Advice: navigation
- Clearances: coordinate

### Reporting
- Arrival: ETA
- Position: periodic
- Departure: ETD
- Hazard: immediate

## Common Pitfalls
- Inadequate pilotage
- Poor cargo securing
- Non-compliance with COLREGS
- Insufficient safety drills
- Environmental violations
- Inadequate maintenance
- Poor communication
""", "tags": ["maritime operations", "ports", "cargo", "safety", "COLREGS", "reference"]}
    ],
    "trades_space_mission_operations": [
        {"title": "Space Mission Operations Reference", "content": """# Space Mission Operations Reference

## Mission Planning
### Phases
1. Concept: objectives
2. Design: spacecraft, orbit
3. Development: build, test
4. Launch: deploy
5. Operations: use
6. Disposal: end of life

### Requirements
- Mission objectives
- Payload: instruments
- Orbit: path
- Lifetime: duration
- Power: energy
- Communication: data
- Budget: cost

### Orbit Selection
- LEO: low earth (200-2000 km)
- MEO: medium (2000-35786 km)
- GEO: geostationary (35786 km)
- HEO: highly elliptical
- Lunar: moon
- Interplanetary: planets

## Launch Operations
### Vehicle
- Rocket: propulsion
- Stages: multiple
- Fairing: protect payload
- Payload: spacecraft
- Adapter: connect

### Launch Site
- Pad: launch point
- Tower: service
- Fuel: storage
- Control: command
- Range: safety

### Countdown
- T-: before launch
- Holds: pauses
- Tests: verify
- Weather: check
- Go/no-go: decision

### Ascent
- Lift-off: leave pad
- Pitch: turn
- Stage: separate
- Fairing: jettison
- Orbit: insert

## Flight Dynamics
### Orbital Mechanics
- Kepler's laws
- Elements: a, e, i, Omega, omega, nu
- Velocity: V = sqrt(mu/r)
- Period: T = 2*pi*sqrt(a^3/mu)
- Energy: specific orbital energy

### Maneuvers
- Hohmann: two burns (efficient)
- Bi-elliptic: three burns
- Plane change: inclination
- Phasing: adjust timing
- Rendezvous: match orbit

### Station Keeping
- GEO: longitudinal drift
- LEO: atmospheric drag
- Solar radiation pressure
- Moon/sun perturbations
- Thrusters: correct

### Reentry
- Decay: orbit lowers
- Interface: 120 km
- Heating: plasma
- Deceleration: g-load
- Landing: recover

## Spacecraft Systems
### Power
- Solar: panels
- Battery: storage
- RTG: nuclear (deep space)
- Distribution: regulate
- Management: control

### Attitude Control
- Sensors: sun, star, earth, gyro
- Actuators: thrusters, wheels, magnetic
- Modes: sun pointing, nadir, inertial
- Determination: estimate
- Control: correct

### Thermal
- Heat sources: sun, electronics
- Heat sinks: radiators, space
- Control: heaters, louvers, blankets
- Range: keep within limits

### Propulsion
- Chemical: liquid, solid
- Electric: ion, Hall
- Cold gas: simple
- Thrust: force
- Isp: efficiency

### Communications
- Frequency: S, X, Ka band
- Antenna: gain
- Transponder: receive/transmit
- Data rate: bps
- Link budget: margin

## Telemetry and Command
### Telemetry (Downlink)
- Health: voltages, temps
- Status: modes, states
- Science: data
- Format: frames
- Rate: bps

### Telecommand (Uplink)
- Instructions: to spacecraft
- Verification: confirm
- Execution: perform
- Safety: prevent harmful

### Packet Standards
- CCSDS: international
- Transfer frame
- Packet: data unit
- Version: protocol

## Ground Systems
### Ground Stations
- Antenna: receive/transmit
- Receiver: capture
- Transmitter: send
- Tracking: follow
- Equipment: baseband

### Network
- DSN: Deep Space Network (NASA)
- ESTRACK: ESA
- Commercial: KSAT, SSC
- Coverage: global

### Control Center
- Operations: monitor
- Planning: schedule
- Analysis: data
- Command: send
- Archive: store

## Operations
### Routine
- Monitoring: telemetry
- Health: check
- Schedule: activities
- Commands: send
- Data: process

### Anomaly
- Detection: alarm
- Investigation: analyze
- Workaround: temporary
- Fix: permanent
- Documentation: record

### Eclipse
- Earth shadow: no sun
- Battery: power
- Thermal: cold
- Operations: reduced

### Station Contact
- AOS: acquisition of signal
- Pass: duration
- Data: transfer
- LOS: loss of signal

## Satellite Operations
### Types
- Communication: relay
- Navigation: GPS
- Earth observation: imaging
- Weather: meteorology
- Scientific: research
- Military: defense

### Payload
- Instruments: sensors
- Data: collect
- Process: onboard
- Transmit: downlink
- Calibration: verify

### Constellation
- Multiple satellites
- Coverage: global
- Coordination: manage
- Replacement: aging

## Safety
### Debris
- Track: catalog
- Avoid: maneuver
- Mitigation: post-mission disposal
- 25-year rule: LEO

### Radiation
- Solar: particles
- Cosmic: galactic
- Belts: Van Allen
- Shielding: protect
- Effects: electronics, humans

### Collision Avoidance
- Conjunction: close approach
- Probability: calculate
- Maneuver: if needed
- Coordinate: with others

## Common Pitfalls
- Inadequate testing
- Single point failures
- Underestimating radiation
- Poor link budget
- Inadequate anomaly response
- Not planning for end of life
- Over-optimistic schedule
""", "tags": ["space operations", "satellites", "telemetry", "orbit", "ground systems", "reference"]}
    ],
    "trades_utilities": [
        {"title": "Utility Operations Reference", "content": """# Utility Operations Reference

## Electric Utility
### Generation
- Thermal: coal, gas, nuclear
- Hydro: dams
- Renewable: wind, solar
- Distributed: rooftop solar
- Capacity: maximum output

### Transmission
- High voltage: 115-765 kV
- Lines: overhead, underground
- Substations: transform
- Grid: interconnected
- NERC: reliability

### Distribution
- Medium voltage: 4-35 kV
- Service: 120/240V
- Feeders: from substation
- Transformers: pole, pad
- Meters: measure usage

### Operations
- Dispatch: balance load
- Frequency: 60 Hz
- Voltage: regulate
- Reliability: SAIDI, SAIFI
- Outage: restore

## Water Utility
### Sources
- Surface: rivers, lakes, reservoirs
- Groundwater: aquifers, wells
- Desalination: seawater
- Reclaimed: wastewater reuse
- Rain: harvested

### Treatment
- Coagulation: destabilize
- Flocculation: form flocs
- Sedimentation: settle
- Filtration: remove particles
- Disinfection: kill pathogens
- Fluoridation: dental

### Distribution
- Storage: tanks, reservoirs
- Pumping: pressure
- Pipes: mains, services
- Valves: control
- Hydrants: fire
- Meters: usage

### Quality
- EPA: Safe Drinking Water Act
- MCL: maximum contaminant level
- Lead: 15 ppb
- Bacteria: total coliform
- Turbidity: cloudiness
- Disinfectant: residual

## Wastewater Utility
### Collection
- Sewers: gravity
- Lift stations: pump
- Manholes: access
- Laterals: from buildings
- I&I: infiltration and inflow

### Treatment
- Preliminary: screens, grit
- Primary: sedimentation
- Secondary: biological
- Tertiary: advanced
- Disinfection: kill pathogens
- Discharge: to water body

### Biosolids
- Thickening: reduce volume
- Digestion: anaerobic, aerobic
- Dewatering: reduce water
- Disposal: landfill, land application
- Beneficial: fertilizer

## Gas Utility
### Natural Gas
- Supply: pipeline, LNG
- Transmission: high pressure
- Distribution: lower pressure
- Service: to meter
- Regulation: pressure
- Odorant: smell (mercaptan)

### Safety
- Leak detection: survey
- Odor: added
- Ignition: avoid
- Evacuation: if leak
- Carbon monoxide: detect

## Telecommunications
### Wireline
- Copper: telephone
- Fiber: high speed
- Coaxial: cable TV
- DSL: telephone line
- Last mile: to customer

### Wireless
- Cellular: 4G, 5G
- WiFi: local
- Microwave: point-to-point
- Satellite: remote
- IoT: connected devices

### Network
- Core: backbone
- Edge: distribution
- Access: to customer
- Peering: connect networks
- IX: internet exchange

## District Heating
### System
- Plant: heat source
- Network: insulated pipes
- Hot water: carrier
- Steam: alternative
- Customer: heat exchanger

### Sources
- Cogeneration: CHP
- Waste heat: industrial
- Geothermal: natural
- Biomass: renewable
- Solar thermal: sun

## Smart Grid
### Features
- Two-way communication
- AMI: advanced metering
- Automation: self-healing
- Monitoring: real-time
- Control: distributed

### Benefits
- Reliability: fewer outages
- Efficiency: reduced losses
- Integration: renewables
- Customer: information
- Demand response: load control

## Operations
### Control Center
- SCADA: monitor and control
- Dispatchers: operators
- Alarms: alerts
- Outage management: restore
- Switching: reconfigure

### Reliability
- SAIDI: System Average Interruption Duration Index
- SAIFI: System Average Interruption Frequency Index
- CAIDI: Customer Average Interruption Duration
- ASAI: Average Service Availability Index

### Maintenance
- Preventive: scheduled
- Corrective: fix when broken
- Predictive: condition-based
- Vegetation: tree trimming
- Inspection: patrol

## Regulation
### Public Utility Commission
- Rates: approve
- Service: standards
- Investments: approve
- Complaints: resolve
- Reports: require

### Federal
- FERC: interstate energy
- EPA: environmental
- NRC: nuclear
- FCC: telecommunications

## Rates and Billing
### Rate Design
- Fixed: customer charge
- Variable: per kWh, gallon
- Demand: peak kW
- Time of use: peak/off-peak
- Tiered: increasing block

### Metering
- Analog: dial
- Digital: display
- AMI: smart meter
- Remote: read
- Interval: time-based

## Common Pitfalls
- Aging infrastructure
- Underinvestment
- Cybersecurity threats
- Climate change impacts
- Workforce turnover
- Regulatory uncertainty
- Not planning for growth
""", "tags": ["utilities", "electric", "water", "gas", "telecommunications", "reference"]}
    ],
    "trades_renewable_energy_operations": [
        {"title": "Renewable Energy Operations Reference", "content": """# Renewable Energy Operations Reference

## Solar Power
### Photovoltaic (PV)
- Panels: convert sunlight
- Inverter: DC to AC
- Mounting: fixed, tracking
- String: series panels
- Microinverter: per panel
- Capacity factor: 15-25%

### Operations
- Monitoring: production
- Cleaning: panels
- Inspection: visual, IR
- Inverter: check
- Wiring: connections
- Vegetation: control

### CSP (Concentrating Solar Power)
- Mirrors: concentrate
- Receiver: heat
- Thermal storage: molten salt
- Turbine: generate
- Hybrid: with PV

### Issues
- Soiling: dirt reduces output
- Degradation: 0.5%/year
- Inverter failure
- Hot spots: cell damage
- Shading: obstruction

## Wind Power
### Types
- Onshore: land
- Offshore: sea
- Horizontal axis: most common
- Vertical axis: less common

### Components
- Tower: support
- Nacelle: housing
- Rotor: blades
- Generator: convert
- Gearbox: increase speed
- Control: pitch, yaw

### Operations
- Monitoring: SCADA
- Inspection: visual, drone
- Maintenance: scheduled
- Lubrication: gearbox
- Blade: inspect, repair
- Lightning: protection

### Performance
- Capacity factor: 30-50%
- Cut-in: 3-4 m/s
- Rated: 12-15 m/s
- Cut-out: 25 m/s
- Power curve: output vs wind

### Issues
- Gearbox failure: costly
- Blade damage: erosion
- Icing: cold climate
- Curtailment: grid limit
- Wake: downwind turbines

## Hydropower
### Types
- Impoundment: dam
- Diversion: run of river
- Pumped storage: pump and generate

### Components
- Dam: store water
- Penstock: to turbine
- Turbine: Francis, Kaplan, Pelton
- Generator: electricity
- Tailrace: outflow

### Operations
- Reservoir: water level
- Flow: control
- Maintenance: turbine, generator
- Spillway: flood
- Fish: passage

### Performance
- Capacity factor: 30-50%
- Head: height difference
- Flow: volume per time
- Power: P = eta * rho * g * Q * H

## Geothermal
### Types
- Dry steam: steam directly
- Flash: hot water to steam
- Binary: low temperature
- Enhanced: EGS (fractured rock)

### Operations
- Wells: production, injection
- Fluid: steam or brine
- Turbine: generate
- Cooling: condense
- Reinjection: sustain

### Issues
- Scaling: minerals
- Corrosion: chemicals
- Depletion: cooling
- Induced seismicity: EGS

## Biomass
### Types
- Direct combustion: burn
- Biogas: anaerobic digestion
- Biofuel: ethanol, biodiesel
- Cogeneration: CHP

### Feedstocks
- Wood: chips, pellets
- Agricultural: crop residue
- Waste: municipal
- Energy crops: switchgrass
- Algae: emerging

### Operations
- Fuel handling: receive, store
- Combustion: boiler
- Emissions: control
- Ash: disposal
- Maintenance: boiler, tubes

## Grid Integration
### Challenges
- Intermittency: variable output
- Uncertainty: forecasting
- Location: remote
- Capacity factor: lower
- Inertia: stability

### Solutions
- Storage: batteries, pumped hydro
- Forecasting: predict output
- Aggregation: diversify
- Demand response: shift load
- Interconnection: share
- Flexible generation: ramp

### Inverter-Based Resources
- No inertia: synthetic
- Frequency response: control
- Voltage: regulate
- Ride-through: fault
- Grid-forming: set voltage

## Energy Storage
### Battery
- Lithium-ion: common
- Flow: vanadium, zinc
- Lead-acid: traditional
- Sodium-sulfur: high temp
- Solid-state: emerging

### Applications
- Arbitrage: buy low, sell high
- Frequency regulation: balance
- Capacity: peak demand
- Reserve: backup
- Renewables: smooth output
- Black start: restart grid

### Operations
- SOC: state of charge
- SOH: state of health
- Cycling: charge/discharge
- Degradation: capacity loss
- Thermal: manage
- BMS: battery management

## Operations and Maintenance
### Monitoring
- SCADA: real-time
- Performance: ratio
- Alarms: alerts
- Analytics: predict

### Maintenance
- Preventive: scheduled
- Corrective: fix when broken
- Predictive: condition-based
- Remote: diagnose
- On-site: repair

### Performance
- Capacity factor: actual/rated
- Availability: % operating
- Performance ratio: PV
- Curtailment: wasted
- Production: energy

## Economics
### Costs
- Capital: upfront
- Operating: ongoing
- Fuel: minimal (free)
- LCOE: levelized cost

### Revenue
- PPA: power purchase agreement
- Market: wholesale
- Net metering: retail
- REC: renewable energy credit
- Capacity: payment

### Incentives
- ITC: investment tax credit
- PTC: production tax credit
- RECs: certificates
- Grants: government
- Rebates: utility

## Common Pitfalls
- Underestimating intermittency
- Inadequate forecasting
- Poor maintenance
- Not planning for storage
- Grid stability issues
- Curtailment losses
- End-of-life disposal
""", "tags": ["renewable energy", "solar", "wind", "hydro", "geothermal", "operations", "reference"]}
    ],
    "trades_construction_management": [
        {"title": "Construction Management Practice Reference", "content": """# Construction Management Practice Reference

## Project Phases
### Pre-Construction
1. Planning: define scope
2. Design: drawings, specs
3. Bidding: select contractor
4. Contract: agreement
5. Permits: approvals
6. Mobilization: setup

### Construction
1. Site work: clear, grade
2. Foundation: support
3. Structure: frame
4. Enclosure: walls, roof
5. Systems: MEP
6. Interior: finishes
7. Commissioning: test

### Post-Construction
1. Punch list: incomplete
2. Substantial completion: usable
3. Final inspection: verify
4. Certificate of occupancy
5. Closeout: documents
6. Warranty: defects

## Project Delivery
### Methods
- Design-bid-build: traditional
  - Design complete, then bid, then build
  - Clear separation
  - Adversarial risk
- Design-build: single entity
  - One contract for design and construction
  - Fast-track possible
  - Less owner control
- CM at risk: construction manager
  - CM holds trade contracts
  - Guaranteed maximum price (GMP)
  - Early involvement
- IPD: integrated project delivery
  - All parties share risk
  - Collaborative
  - Target value

## Contracts
### Types
- Lump sum: fixed price
- Unit price: per quantity
- Cost plus: actual + fee
- GMP: max price
- Time and materials: hourly

### Documents
- Agreement: contract
- General conditions: rules
- Supplementary conditions: modifications
- Drawings: plans
- Specifications: requirements
- Addenda: changes before bid

### Parties
- Owner: project owner
- Architect/Engineer: design
- Contractor: build
- Subcontractor: specialty
- Supplier: materials
- Inspector: verify

## Cost Management
### Estimate
- Conceptual: early
- Preliminary: design
- Detailed: final
- Bid: contractor
- Cost breakdown: by trade

### Elements
- Direct: materials, labor, equipment
- Indirect: overhead, profit
- Contingency: unknowns
- Bonds: payment, performance
- Insurance: liability, workers comp

### Control
- Budget: baseline
- Committed: contracted
- Actual: spent
- Forecast: projected
- Variance: difference
- Trend: direction

## Schedule
### CPM (Critical Path Method)
- Activities: tasks
- Durations: time
- Dependencies: relationships
- Critical path: longest
- Float: slack
- Milestones: key dates

### Types
- Gantt chart: visual
- Network diagram: logic
- Bar chart: simple
- Line of balance: repetitive

### Updates
- Progress: % complete
- Delays: identify
- Recovery: adjust
- Impact: analyze
- Baseline: original

## Quality Management
### Plan
- Quality standards
- Acceptance criteria
- Inspection plan
- Testing plan
- Documentation

### Control
- Inspection: verify
- Testing: materials
- Nonconformance: identify
- Corrective action: fix
- Rework: redo
- Documentation: record

### Assurance
- Audits: process
- Reviews: design
- Submittals: approve
- Mockups: sample
- Commissioning: test

## Safety Management
### OSHA
- 29 CFR 1926: construction
- General duty: safe workplace
- Training: required
- Reporting: injuries
- Inspection: compliance

### Hazards
- Falls: leading cause
  - Guardrails: prevent
  - Harnesses: arrest
  - Nets: catch
  - Holes: cover
- Struck by: objects, vehicles
- Caught in/between: collapse
- Electrical: shock
- Trenching: cave-in
  - Shoring: support
  - Sloping: angle
  - Shield: box

### Program
- Safety plan: written
- Training: all workers
- Inspections: regular
- Toolbox talks: weekly
- Incident investigation: cause
- Near miss: report

## Risk Management
### Identify
- Weather: delay
- Site conditions: unknown
- Design errors: changes
- Material prices: increase
- Labor: shortage
- Regulatory: changes
- Financial: owner

### Analyze
- Probability: likelihood
- Impact: consequence
- Matrix: classify
- Register: document

### Mitigate
- Avoid: change plan
- Reduce: minimize
- Transfer: insurance
- Accept: acknowledge

## Change Management
### Process
1. Identify: need for change
2. Document: describe
3. Price: cost
4. Approve: authorize
5. Execute: implement
6. Record: document

### Types
- Change order: formal
- Field order: minor
- RFI: request for information
- Clarification: explain

## Communication
### Meetings
- Pre-construction: kickoff
- Weekly: progress
- Monthly: pay
- Safety: toolbox
- Coordination: trades

### Documentation
- Daily reports: activities
- Meeting minutes: decisions
- RFI log: questions
- Submittal log: approvals
- Change order log: modifications
- Pay applications: billing

## Technology
### BIM (Building Information Modeling)
- 3D model: visualize
- Clash detection: conflicts
- Quantity takeoff: count
- 4D: schedule
- 5D: cost
- 6D: facilities

### Software
- Project management: Procore
- Scheduling: Primavera, MS Project
- Estimating: RSMeans, Bluebeam
- BIM: Revit, Navisworks
- Document: PlanGrid

## Common Pitfalls
- Incomplete drawings
- Inadequate site investigation
- Poor scheduling
- Inadequate safety
- Cost overruns
- Scope creep
- Poor communication
- Inadequate quality control
""", "tags": ["construction management", "project", "safety", "quality", "scheduling", "reference"]}
    ],
    "trades_carpentry": [
        {"title": "Carpentry Practice Reference", "content": """# Carpentry Practice Reference

## Wood Materials
### Lumber
- Softwood: pine, fir, spruce (structural)
- Hardwood: oak, maple, walnut (finish)
- Grades: select, common, utility
- Sizes: nominal vs actual
  - 2x4: actual 1.5 x 3.5
  - 2x6: actual 1.5 x 5.5
- Moisture: green vs kiln-dried

### Engineered
- Plywood: veneers layered
- OSB: oriented strand board
- LVL: laminated veneer lumber
- Glulam: glued laminated
- I-joist: web and flange
- Truss: prefabricated

### Fasteners
- Nails: common, box, finish
  - Penny: size (d)
  - 8d, 10d, 16d common
- Screws: wood, deck, drywall
- Bolts: carriage, lag, through
- Hangers: joist, post
- Adhesives: construction, wood

## Tools
### Hand Tools
- Hammer: claw, framing
- Saw: hand, crosscut, rip
- Level: spirit, torpedo
- Square: framing, speed
- Tape measure: 25 ft
- Chalk line: snap
- Plane: smooth
- Chisel: cut

### Power Tools
- Circular saw: cut
- Miter saw: angles
- Table saw: rip
- Drill: holes, drive
- Impact driver: screws
- Nail gun: pneumatic, cordless
- Router: shape
- Sander: smooth

## Framing
### Floor
- Sill plate: on foundation
- Joist: span
- Rim joist: outside
- Blocking: between joists
- Subfloor: on top
- Cantilever: overhang

### Walls
- Plates: top, bottom
- Studs: vertical (16" or 24" o.c.)
- Headers: above openings
- Jack stud: support header
- King stud: full length
- Cripple: short
- Corner: intersection
- Partition: T intersection

### Roof
- Rafters: slope
- Ridge: top
- Ceiling joist: bottom
- Collar tie: upper
- Rafter tie: lower
- Truss: prefabricated
- Pitch: slope (e.g., 4/12)
- Overhang: eave
- Fascia: edge
- Soffit: underside

### Sheathing
- Wall: plywood, OSB
- Roof: plywood, OSB
- Subfloor: plywood, OSB
- Thickness: 7/16, 15/32, 1/2

## Doors
### Types
- Interior: passage, closet
- Exterior: entry
- Prehung: in frame
- Slab: door only
- Bifold: closet
- Pocket: slide

### Installation
- Frame: plumb, level, square
- Hinges: 3 for exterior, 2 interior
- Clearance: 1/8" around
- Shims: adjust
- Casing: trim

## Windows
### Types
- Single hung: bottom moves
- Double hung: both move
- Casement: crank out
- Sliding: horizontal
- Awning: top hinged
- Fixed: picture
- Bay: projects out

### Installation
- Level: horizontal
- Plumb: vertical
- Square: corners
- Flashing: water
- Seal: caulk
- Insulate: gap
- Trim: finish

## Trim
### Base
- Baseboard: at floor
- Shoe: small molding
- Base cap: top

### Casing
- Door: around
- Window: around
- Extension jamb: to wall

### Crown
- Wall to ceiling
- Spring angle: common
- Coping: inside corner
- Miter: outside corner

### Other
- Chair rail: wall
- Wainscoting: lower wall
- Picture rail: upper

## Cabinets
### Types
- Base: floor
- Wall: upper
- Tall: pantry
- Vanity: bathroom

### Construction
- Face frame: traditional
- Frameless: European
- Box: plywood, MDF
- Doors: slab, shaker, raised
- Drawers: dovetail, dado
- Hardware: hinges, slides

### Installation
- Level: horizontal
- Plumb: vertical
- Shim: adjust
- Fasten: to studs
- Countertop: on base

## Stairs
### Components
- Stringer: support
- Tread: step
- Riser: vertical
- Nosing: overhang
- Newel: post
- Baluster: spindle
- Handrail: grip
- Landing: platform

### Layout
- Total rise: floor to floor
- Total run: horizontal
- Riser height: 7-7.75" max
- Tread depth: 10" min
- Headroom: 6'8" min
- Width: 36" min

## Reading Plans
### Drawings
- Floor plan: layout
- Elevation: side view
- Section: cut through
- Detail: close up
- Schedule: list

### Symbols
- Door: swing
- Window: glazing
- Wall: thickness
- Dimension: size
- Elevation: height

## Codes
### IRC (International Residential Code)
- One and two family dwellings
- Prescriptive: follow rules
- Engineered: design
- Span tables: joists, rafters
- Fire: separation, egress

## Common Pitfalls
- Not checking for level and plumb
- Wrong fastener selection
- Inadequate framing
- Poor flashing
- Not following codes
- Inadequate bracing
- Wrong material for application
""", "tags": ["carpentry", "framing", "trim", "cabinets", "wood", "reference"]}
    ],
}
