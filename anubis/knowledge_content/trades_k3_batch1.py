"""Transportation/Trades K3 Batch 1 - 6 specialties."""

TRADES_K3_BATCH1: dict[str, list[dict]] = {
    "trades_transportation_planning": [
        {"title": "Transportation Planning Methods Reference", "content": """# Transportation Planning Methods Reference

## Travel Demand Forecasting
### Four-Step Model
1. Trip generation: how many trips
2. Trip distribution: where they go
3. Mode choice: how they travel
4. Route assignment: which path

### Trip Generation
- Productions: origins (home)
- Attractions: destinations (work, shop)
- Regression models
- Cross-classification
- Rates: trips per household

### Trip Distribution
- Gravity model: T_ij = P_i * A_j * F_ij * K_ij
- F_ij: friction factor (distance)
- K_ij: socioeconomic factor
- Intrazonal trips: within zone

### Mode Choice
- Logit model: probability
- Utility: U = a + b*time + c*cost
- Independent variables: time, cost, income
- Multinomial: multiple modes
- Nested: correlated alternatives

### Route Assignment
- User equilibrium: no one can switch
- System optimal: minimize total cost
- All-or-nothing: shortest path
- Capacity constraints: congestion

## Capacity Analysis
### Highway Capacity Manual (HCM)
- Free flow speed
- Flow rate
- Density
- Level of service (A-F)
- LOS A: free flow; LOS F: breakdown

### Freeway
- Basic segment
- Weaving
- Ramps
- Merge/diverge

### Arterial
- Signalized intersections
- Urban street segments
- Access management

## Transit Planning
### Modes
- Bus: flexible, low capital
- BRT: bus rapid transit, dedicated lanes
- Light rail: urban, surface
- Heavy rail: subway, elevated
- Commuter rail: regional

### Service Planning
- Route design
- Stop spacing
- Headway: time between
- Span: hours of service
- Schedule: timetable

### Ridership
- Forecasting
- Fare elasticity
- Service elasticity
- Captive vs choice riders

## Travel Surveys
### Types
- Household travel survey
- Origin-destination survey
- On-board transit survey
- Cordon survey
- Screenline survey

### Data
- Trip purpose
- Mode
- Time of day
- Origin, destination
- Demographics

## Land Use and Transportation
### Relationship
- Land use generates trips
- Transportation serves land use
- Mutual feedback
- Integrated planning

### Models
- Land use transport models
- Integrated land use: LUT
- TELUM, UrbanSim
- Four-step with land use

### TOD (Transit-Oriented Development)
- Mixed use
- Higher density
- Pedestrian friendly
- Within walk of transit
- Reduced parking

## Environmental
### NEPA Process
- Categorical exclusion (CE)
- Environmental assessment (EA)
- Environmental impact statement (EIS)
- Record of decision (ROD)

### Impacts
- Air quality: emissions
- Noise: traffic
- Water: runoff
- Wetlands: section 404
- Historic: section 106
- Environmental justice

## Finance
### Sources
- Federal: gas tax, general fund
- State: gas tax, registration
- Local: property tax, sales tax
- Tolls: user fees
- P3: public-private partnership

### Federal (US)
- FHWA: highways
- FTA: transit
- FRA: rail
- FAA: aviation
- FAST Act: current authorization

## Common Pitfalls
- Poor data quality
- Not validating models
- Ignoring induced demand
- Not considering equity
- Underestimating costs
- Not planning for maintenance
""", "tags": ["transportation planning", "demand forecasting", "capacity", "transit", "reference"]}
    ],
    "trades_logistics": [
        {"title": "Supply Chain and Logistics Operations Reference", "content": """# Supply Chain and Logistics Operations Reference

## Supply Chain Management
### Definition
- Flow of goods, information, money
- From raw materials to consumer
- Coordination across organizations

### Components
- Suppliers: provide materials
- Manufacturing: transform
- Distribution: deliver
- Retail: sell to consumer
- Customer: end user

## Inventory Management
### Types
- Raw materials: inputs
- Work-in-process (WIP): being made
- Finished goods: ready to sell
- Maintenance (MRO): repair

### Costs
- Holding: storage, insurance, obsolescence
- Ordering: setup, processing
- Shortage: lost sales, backorder
- Purchase: unit cost

### Models
- EOQ: Q* = sqrt(2DS/H)
- Newsvendor: single period
- Reorder point: ROP = dL + SS
- Safety stock: SS = z*sigma*sqrt(L)

### Policies
- Continuous review: (s, Q)
- Periodic review: (R, S)
- Base stock: (s, S)
- Min-max

## Transportation
### Modes
- Truck: flexible, door-to-door
- Rail: bulk, long distance
- Air: fast, expensive
- Water: cheap, slow
- Pipeline: liquids, gases
- Intermodal: multiple modes

### Trucking
- FTL: full truckload
- LTL: less than truckload
- Parcel: small packages
- Last mile: to customer

### Intermodal
- Container: standard box
- TOFC: trailer on flatcar
- COFC: container on flatcar
- Double stack: two containers

## Warehousing
### Functions
- Receive: accept goods
- Store: hold inventory
- Pick: select items
- Pack: prepare orders
- Ship: send out
- Cross-dock: bypass storage

### Layout
- U-shaped: receive and ship same side
- I-shaped: through flow
- L-shaped: corner
- Zoned: by product type

### Storage
- Pallet rack: bulk storage
- Shelving: small items
- Flow rack: FIFO
- Drive-in: high density
- Mezzanine: vertical
- AS/RS: automated

### Picking
- Piece pick: eaches
- Case pick: full cases
- Pallet pick: full pallets
- Batch: multiple orders
- Zone: assigned area
- Wave: time grouped

## Distribution Network Design
### Facility Location
- Center of gravity: minimize distance
- P-median: p facilities
- Covering: cover all demand
- Hub and spoke: central hub

### Network Optimization
- Cost: facility + transport + inventory
- Service: delivery time
- Capacity: throughput limits
- Multi-echelon: multiple levels

## Freight Management
### Routing
- Shortest path
- Vehicle routing problem (VRP)
- Time windows
- Capacity constraints
- Multiple stops

### Load Planning
- Cube utilization: fill vehicle
- Weight limits: legal
- Pallet arrangement
- Load sequencing

### Freight Rates
- Class: NMFC
- Density: weight/volume
- Distance: per mile
- Weight breaks: volume discount
- Fuel surcharge

## International Logistics
### Terms (Incoterms)
- EXW: ex works (buyer from factory)
- FOB: free on board (seller to port)
- CIF: cost, insurance, freight
- DDP: delivered duty paid

### Customs
- HTS: harmonized tariff
- Duty: tax on import
- Broker: facilitate
- Bond: guarantee
- Clearance: approval

### Documentation
- Bill of lading: contract
- Commercial invoice: value
- Packing list: contents
- Certificate of origin
- Insurance certificate

## Technology
### WMS (Warehouse Management System)
- Inventory tracking
- Order management
- Labor management
- Slotting optimization
- Integration with ERP

### TMS (Transportation Management System)
- Route optimization
- Load planning
- Carrier selection
- Freight audit
- Tracking

### RFID and Barcodes
- Barcode: 1D, 2D
- RFID: radio frequency
- Real-time tracking
- No line of sight
- Automatic

## Performance Metrics
### KPIs
- On-time delivery: %
- Order accuracy: %
- Inventory turnover: times/year
- Fill rate: % fulfilled
- Cycle time: order to delivery
- Perfect order: all criteria met

## Common Pitfalls
- Bullwhip effect: demand distortion
- Over-reliance on forecasts
- Not planning for disruptions
- Poor inventory accuracy
- Inadequate technology
- Not measuring performance
""", "tags": ["logistics", "supply chain", "inventory", "warehousing", "transportation", "reference"]}
    ],
    "trades_warehousing": [
        {"title": "Warehouse Operations and Management Reference", "content": """# Warehouse Operations and Management Reference

## Warehouse Functions
### Core Processes
1. Receiving: accept inbound
2. Put-away: store items
3. Storage: hold inventory
4. Picking: select for orders
5. Packing: prepare shipment
6. Shipping: send outbound
7. Returns: reverse logistics

### Value-Added Services
- Kitting: assemble components
- Light assembly
- Labeling
- Gift wrapping
- Custom packaging
- Quality inspection

## Receiving
### Process
1. Schedule appointment
2. Check documentation (ASN)
3. Unload vehicle
4. Inspect for damage
5. Verify count
6. Accept or reject
7. Update system

### Documentation
- ASN: advance shipping notice
- BOL: bill of lading
- Packing slip: contents
- PO: purchase order

### Inspection
- Visual: damage
- Count: quantity
- Quality: condition
- Sample: random check

## Put-Away
### Strategies
- Directed: system assigns
- Random: any location
- Fixed: specific slot
- Zone: area assigned
- Closest: nearest open

### Considerations
- Product velocity: fast movers near
- Size: fit location
- Weight: heavy low
- Hazard: special area
- Temperature: climate control

## Storage
### Equipment
- Pallet rack: selective, drive-in, push-back
- Shelving: boltless, bin
- Flow rack: FIFO, LIFO
- Cantilever: long items
- Mezzanine: vertical
- Carousel: rotating
- AS/RS: automated

### Location Types
- Pallet: full pallet
- Case: full carton
- Each: individual
- Bulk: large quantity
- Reserve: overflow
- Forward pick: fast access

### Slotting
- ABC analysis: prioritize
- Velocity: fast, medium, slow
- Family grouping: similar items
- Compatibility: store together
- Cube: maximize space

## Picking
### Methods
- Discrete: one order at a time
- Batch: multiple orders
- Zone: picker in area
- Wave: time grouped
- Cluster: pick multiple totes

### Technologies
- Paper: pick list
- RF scanner: barcode
- Voice: spoken commands
- Pick-to-light: illuminated
- Put-to-light: sort
- AGV: automated vehicles
- Goods-to-person: system brings

### Strategies
- Single order: simple
- Batch: efficiency
- Zone: specialization
- Sort-while-pick: separate
- Pick-and-pass: relay

## Packing
### Process
1. Select appropriate container
2. Protect product (dunnage)
3. Include packing slip
4. Seal package
5. Apply label
6. Verify

### Materials
- Corrugated box: standard
- Mailer: small
- Pallet: large
- Stretch wrap: secure
- Bubble wrap: cushion
- Foam: protect
- Peanuts: fill

### Labeling
- Shipping label: address
- Barcode: track
- Hazmat: warning
- Fragile: handle
- This side up: orientation

## Shipping
### Process
1. Verify order complete
2. Select carrier
3. Generate label
4. Stage for pickup
5. Load vehicle
6. Update system
7. Track

### Carriers
- Small parcel: UPS, FedEx, USPS
- LTL: less than truckload
- FTL: full truckload
- Regional: local
- Same day: urgent

### Documentation
- BOL: bill of lading
- Shipping label
- Customs: international
- Manifest: summary

## Inventory Management
### Cycle Counting
- Count subset regularly
- ABC: count A most often
- Reconcile discrepancies
- Investigate causes
- Maintain accuracy

### Physical Inventory
- Count everything
- Stop operations
- Reconcile
- Adjust system
- Periodic (annual)

### Accuracy
- Location: where it is
- Quantity: how many
- Condition: quality
- Lot: batch tracking
- Serial: individual

## Technology
### WMS (Warehouse Management System)
- Inventory: real-time
- Orders: manage
- Labor: track
- Receiving: process
- Put-away: direct
- Picking: optimize
- Shipping: verify
- Reporting: analyze

### Hardware
- RF scanners: barcode
- Mobile computers: handheld
- Printers: label, receipt
- Scales: weigh
- Conveyors: automate
- AGV: robotic

### Integration
- ERP: enterprise system
- TMS: transportation
- OMS: order management
- E-commerce: web orders
- Carriers: shipping

## Performance
### KPIs
- Inventory accuracy: %
- Order accuracy: %
- Pick rate: lines/hour
- Receiving productivity: pallets/hour
- Shipping accuracy: %
- Cycle time: hours
- Returns rate: %
- Space utilization: %

## Safety
### OSHA
- Lifting: proper technique
- Forklift: certification
- Hazmat: training
- PPE: personal protective
- Housekeeping: clean
- Ergonomics: prevent injury

### Hazards
- Forklift: collision
- Falling: objects, people
- Chemical: exposure
- Electrical: shock
- Fire: prevention
- Slips: wet floors

## Common Pitfalls
- Poor slotting
- Inaccurate inventory
- Inefficient picking
- Not using WMS
- Inadequate safety
- Poor receiving process
- No performance metrics
""", "tags": ["warehousing", "operations", "picking", "WMS", "inventory", "reference"]}
    ],
    "trades_fleet_management": [
        {"title": "Fleet Management Operations Reference", "content": """# Fleet Management Operations Reference

## Fleet Acquisition
### Purchase vs Lease
- Purchase: own asset, depreciate
- Lease: lower upfront, return
- Lease types: closed-end, open-end
- Lifecycle cost analysis

### Selection Criteria
- Purpose: what it does
- Capacity: payload, passengers
- Fuel efficiency: mpg
- Maintenance: reliability
- Cost: TCO
- Safety: ratings
- Emissions: compliance

### Right-Sizing
- Utilization analysis
- Peak demand
- Seasonal variation
- Pool vehicles: shared
- Eliminate underused

## Vehicle Lifecycle
### Stages
1. Acquisition: purchase
2. Assignment: to driver
3. Operation: daily use
4. Maintenance: upkeep
5. Disposal: sell/retire

### Lifecycle Cost
- Depreciation: value loss
- Fuel: operating cost
- Maintenance: repairs
- Insurance: protection
- Administration: overhead
- Downtime: lost productivity

### Replacement
- Age: years
- Mileage: distance
- Condition: wear
- Cost: increasing repairs
- Cycle: planned replacement

## Maintenance
### Preventive (PM)
- Scheduled: oil, filters, inspection
- Mileage-based: every X miles
- Time-based: every X months
- Manufacturer schedule
- Reduces breakdowns

### Predictive
- Monitor condition
- Vibration analysis
- Oil analysis
- Telematics data
- Predict failure

### Corrective
- Fix when breaks
- Reactive
- Unscheduled downtime
- Higher cost

### Shop Management
- Work orders: track
- Technicians: qualified
- Parts: inventory
- Bays: capacity
- Scheduling: efficient

## Fuel Management
### Monitoring
- Fuel cards: track purchases
- Telematics: consumption
- MPG: efficiency
- Exceptions: high use
- Idle: wasted fuel

### Strategies
- Route optimization: less miles
- Idle reduction: auto shutoff
- Driver training: efficient
- Vehicle selection: efficient
- Alternative fuels: CNG, electric

### Fuel Cards
- Driver: assigned
- Vehicle: assigned
- Limits: gallons, time
- Reports: track use
- Fraud: detect

## Driver Management
### Hiring
- Background check
- MVR: motor vehicle record
- Drug testing: DOT
- Qualifications: experience
- Training: required

### Training
- Safety: defensive driving
- Procedures: company
- Equipment: specific
- Compliance: regulations
- Ongoing: refresh

### Monitoring
- Telematics: behavior
- Dash cam: record
- Coaching: improve
- Discipline: address
- Reward: good behavior

## Safety
### Accident Prevention
- Training: defensive driving
- Vehicle: maintained
- Route: planned
- Schedules: realistic
- Technology: assist

### Accident Management
- Report: immediate
- Investigate: cause
- Document: photos, statements
- Insurance: notify
- Repair: coordinate
- Analysis: prevent recurrence

### CSA (Compliance, Safety, Accountability)
- Safety scores
- Violations: weighted
- Intervention: thresholds
- Improvement: required

## Compliance
### DOT/FMCSA
- USDOT number: identifier
- MC number: interstate
- Drug testing: required
- Hours of service (HOS)
- Vehicle inspection
- Maintenance records

### HOS (Hours of Service)
- Driving limit: 11 hours
- Window: 14 hours
- Restart: 34 hours
- Breaks: 30 minutes
- ELD: electronic logging

### Inspections
- Pre-trip: driver
- Post-trip: driver
- Annual: mechanic
- DOT: roadside
- Level I: full
- Level V: in-house

## Telematics
### GPS Tracking
- Location: real-time
- History: breadcrumb
- Geofence: alert on enter/exit
- Route: actual vs planned

### Vehicle Data
- Speed: mph
- RPM: engine
- Fuel: consumption
- OBD-II: diagnostics
- Idle: time
- Mileage: odometer

### Driver Behavior
- Harsh braking
- Rapid acceleration
- Cornering: speed
- Speeding: over limit
- Seatbelt: usage
- Phone: distraction

### Applications
- Route optimization
- Dispatch: assign jobs
- Customer: ETA
- Maintenance: predict
- Safety: coach
- Compliance: HOS

## Routing and Dispatch
### Route Planning
- Shortest distance
- Fastest time
- Avoid: restrictions
- Multi-stop: sequence
- Time windows: delivery

### Dispatch
- Assign: vehicle, driver
- Communicate: instructions
- Track: progress
- Adjust: real-time
- Document: completion

### Optimization
- VRP: vehicle routing problem
- Capacity: load limits
- Time: windows, total
- Constraints: multiple
- Software: automate

## Cost Management
### TCO (Total Cost of Ownership)
- Acquisition: purchase
- Fuel: consumption
- Maintenance: repairs
- Insurance: premiums
- Administration: overhead
- Disposal: resale

### Benchmarking
- Cost per mile
- Cost per vehicle
- Cost per hour
- Industry comparison
- Identify outliers

## Alternative Fuels
### Electric
- BEV: battery electric
- PHEV: plug-in hybrid
- Charging: infrastructure
- Range: limited
- Cost: high upfront, low operating

### Natural Gas
- CNG: compressed
- LNG: liquefied
- Cleaner: emissions
- Infrastructure: limited
- Heavy duty: common

### Hydrogen
- Fuel cell: electric
- Refuel: fast
- Range: long
- Infrastructure: limited
- Emerging

## Common Pitfalls
- Poor maintenance records
- Not monitoring fuel
- Ignoring driver behavior
- Non-compliance with HOS
- Inadequate safety training
- Not analyzing TCO
- Over-fleet or under-fleet
""", "tags": ["fleet management", "maintenance", "fuel", "telematics", "compliance", "reference"]}
    ],
    "trades_aviation_operations": [
        {"title": "Aviation Operations and Safety Reference", "content": """# Aviation Operations and Safety Reference

## Air Traffic Control (ATC)
### Structure
- Tower: airport area
- TRACON: terminal radar
- Center: en route
- Clearance delivery: clearances
- Ground: taxi
- Approach/departure: transitions

### Separation
- Vertical: altitude
- Horizontal: distance
- Radar: monitored
- Non-radar: procedural
- Wake turbulence: spacing

### Procedures
- IFR: instrument flight rules
- VFR: visual flight rules
- SVFR: special VFR
- Clearances: instructions
- Handoff: transfer control

## Airport Operations
### Areas
- Airside: aircraft
- Landside: passengers
- Terminal: building
- Apron: parking
- Taxiway: connect
- Runway: takeoff/landing

### Runway
- Designation: heading (e.g., 27)
- Length: minimum for aircraft
- Width: standard
- Surface: asphalt, concrete
- Lighting: edge, centerline
- Markings: thresholds, aiming

### Taxiway
- Connect runway to apron
- Centerline: yellow
- Hold short: stop line
- Direction: signs

### Apron/Ramp
- Parking: gates
- Service: fuel, baggage
- Ground power: GPU
- Pushback: tow
- De-icing: winter

## Flight Operations
### Pre-Flight
- Weather: briefing
- NOTAMs: notices
- Flight plan: file
- Weight and balance
- Fuel: required
- Performance: calculate

### Takeoff
- Clearance: ATC
- Runway: align
- Power: apply
- Rotation: lift nose
- Climb: gear up

### Cruise
- Altitude: assigned
- Heading: route
- Speed: cruise
- Navigation: waypoints
- Weather: avoid

### Approach
- Clearance: approach
- Configuration: gear, flaps
- Speed: reduce
- Descent: glide path
- Landing: flare

### Post-Flight
- Taxi: to gate
- Shutdown: engines
- Paperwork: complete
- Debrief: issues

## Aircraft Maintenance
### Types
- Line: daily, between flights
- Base: heavy, scheduled
- Shop: component

### Checks
- A check: frequent (500 hrs)
- B check: intermediate
- C check: major (1-2 years)
- D check: overhaul (5-6 years)

### Documentation
- Logbook: record
- Work order: task
- AD: airworthiness directive
- SB: service bulletin
- MEL: minimum equipment list

### Part 91 vs 121 vs 135
- 91: general aviation
- 121: scheduled airlines
- 135: charter, commuter

## Safety Management System (SMS)
### Components
1. Safety policy
2. Safety risk management
3. Safety assurance
4. Safety promotion

### Hazard Identification
- Reports: voluntary
- Audits: systematic
- Inspections: routine
- Data analysis: trends

### Risk Assessment
- Probability: likelihood
- Severity: consequence
- Matrix: classify
- Mitigation: reduce

### Safety Culture
- Just culture: no blame
- Reporting: encouraged
- Learning: from events
- Continuous improvement

## Security
### Passenger
- TSA: screening
- Checkpoint: metal detector
- X-ray: bags
- AIT: body scanner
- Pat-down: secondary

### Cargo
- Screening: physical
- X-ray: contents
- Known shipper: trusted
- Chain of custody: track

### Airport
- Access control: SIDA
- Badges: identification
- Fencing: perimeter
- Patrol: response

## Weather
### Reports
- METAR: current conditions
- TAF: forecast
- PIREP: pilot report
- SIGMET: significant
- AIRMET: less severe

### Hazards
- Thunderstorms: turbulence, hail
- Icing: airframe
- Fog: visibility
- Wind shear: takeoff/landing
- Snow: contamination

### Decision
- Go/no-go: pilot
- Minimums: ceiling, visibility
- Alternate: backup airport
- Fuel: reserve

## Navigation
### Systems
- VOR: very high frequency
- NDB: non-directional beacon
- GPS: satellite
- ILS: instrument landing
- RNAV: area navigation
- RNP: required performance

### Procedures
- SID: standard instrument departure
- STAR: standard terminal arrival
- Approach: precision, non-precision
- Missed approach: abort

## Communications
### Phraseology
- Standard: ICAO
- Readback: confirm
- Clearance: approve
- Altitude: feet
- Heading: degrees
- Speed: knots

### Frequencies
- Tower: airport
- Ground: taxi
- Approach: arrival
- Center: en route
- Emergency: 121.5
- UNICOM: advisory

## Regulations
### FAA (US)
- 14 CFR: aviation regulations
- Part 1: definitions
- Part 61: pilot certification
- Part 91: general operating
- Part 121: airlines
- Part 135: commuter

### International
- ICAO: standards
- Annexes: specific topics
- SARPs: standards and practices
- Differences: filed

## Common Pitfalls
- Inadequate weather planning
- Fuel mismanagement
- Loss of situational awareness
- Communication errors
- Non-compliance with procedures
- Fatigue
- Inadequate maintenance
""", "tags": ["aviation operations", "ATC", "airport", "safety", "weather", "reference"]}
    ],
    "trades_rail_systems": [
        {"title": "Rail Systems Operations Reference", "content": """# Rail Systems Operations Reference

## Infrastructure
### Track
- Gauge: distance between rails
  - Standard: 1435 mm (4'8.5")
  - Narrow: < standard
  - Broad: > standard
- Rail: steel shape
  - Weight: lb/yard
  - Section: profile
- Tie: sleeper
  - Wood: traditional
  - Concrete: durable
  - Steel: strong
- Ballast: crushed stone
  - Support: load distribution
  - Drainage: water
  - Restraint: lateral

### Geometry
- Grade: slope (max ~2-3%)
- Curve: radius
  - Tangent: straight
  - Curve: circular
  - Spiral: transition
- Superelevation: outer rail higher
  - Cant: amount
  - Balance: speed
- Clearance: side, overhead

### Turnouts
- Switch: movable rail
- Frog: crossing point
- Guard rail: guide
- Number: angle (e.g., #10)
- Speed: diverging limited

## Signaling
### Principles
- Block: track section
- Signal: indicate status
- Interlocking: prevent conflicting
- Aspect: color/position
- Indication: meaning

### Types
- Manual: operator
- Automatic: track circuit
- CTC: centralized traffic control
- PTC: positive train control
- ATC: automatic train control

### Track Circuits
- Detect train: shunt
- Insulated: rail joints
- Continuous: no joints
- Axle counter: count in/out

### Signals
- Color light: red, yellow, green
- Position: semaphore
- Searchlight: single lens
- Dwarf: low speed
- Distant: approach
- Home: absolute

### Interlocking
- Routes: set
- Switches: align
- Signals: clear
- Locking: prevent conflict
- Approach: route locked

## Rolling Stock
### Locomotives
- Diesel-electric: most common
  - Diesel engine: prime mover
  - Generator: produce electricity
  - Traction motors: drive wheels
- Electric: overhead or third rail
  - Pantograph: collect power
  - Transformer: step down
  - Motors: drive
- Diesel-hydraulic: torque converter
- Steam: historical

### Freight Cars
- Boxcar: enclosed
- Hopper: bulk (coal, grain)
  - Covered: protect
  - Open: dump
- Tank car: liquids
- Flatcar: flat deck
- Gondola: open top
- Intermodal: containers
- Special: heavy, oversized

### Passenger Cars
- Coach: seating
- Sleeper: berths
- Dining: restaurant
- Baggage: luggage
- Observation: lounge
- Business: premium

### Components
- Trucks: wheel assemblies
  - Bolster: cross member
  - Side frame: structure
  - Wheels: steel
  - Axles: connect
  - Bearings: rotate
- Coupler: connect cars
  - Knuckle: automatic
  - Draft gear: cushion
- Brake: stop
  - Air: pneumatic
  - Shoe: friction
  - Disc: modern

## Operations
### Train Movement
- Authority: permission to proceed
  - Signal: green
  - Track warrant: written
  - Form D: written
  - Cab signal: in cab
- Speed: limits
  - Maximum: track class
  - Curves: reduced
  - Approach: slower
- Headway: time between trains

### Dispatching
- CTC: dispatcher controls
- Track warrant: radio
- Train order: historical
- Timetable: schedule
- Authority: granted

### Freight
- Classification: sort cars
- Yard: switching
  - Hump: gravity
  - Flat: pull
- Block: group cars
- Train: assemble
- Route: plan

### Passenger
- Schedule: timetable
- Stops: stations
- Connections: meet
- Capacity: seats
- Load factor: % full

## Stations
### Passenger
- Platform: board/alight
  - Side: alongside
  - Island: between
  - Bay: terminal
- Concourse: waiting
- Ticketing: purchase
- Information: displays
- Access: parking, transit

### Freight
- Yard: classification
- Terminal: end point
- Siding: passing
- Team track: public
- Industry: private

## Safety
### Hazards
- Derailment: off track
- Collision: train to train
- Crossing: highway
- Trespasser: pedestrian
- Bridge: structural
- Tunnel: confined

### Prevention
- Inspection: track, equipment
- Maintenance: repair
- Signals: functional
- Training: employees
- Operating rules: follow
- PTC: technology

### Grade Crossings
- Active: gates, lights
- Passive: signs
- Warning: bells
- Whistle: approach
- Surface: smooth

## Maintenance
### Track
- Inspection: visual, geometry
- Grinding: smooth rail
- Tamping: level ballast
- Replacement: worn
- Surfacing: align

### Equipment
- Wheel: truing
- Bearing: replace
- Brake: test
- Truck: inspect
- Body: repair

### Standards
- FRA: federal (US)
- AREMA: engineering
- AAR: association
- Class: track quality
  - Class 1: highest (freight 80, passenger 110)
  - Class 9: lowest

## Positive Train Control (PTC)
### Purpose
- Prevent collisions
- Overspeed derailments
- Incursions into work zones
- Movement through misaligned switches

### Technology
- GPS: location
- Wireless: communication
- Back office: data
- Locomotive: display
- Wayside: signals

## Common Pitfalls
- Inadequate track inspection
- Signal failures
- Human error in dispatching
- Grade crossing accidents
- Derailments from track defects
- Inadequate maintenance
- Not implementing PTC
""", "tags": ["rail systems", "signaling", "rolling stock", "operations", "safety", "reference"]}
    ],
}
