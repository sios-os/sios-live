"""Transportation/Trades K1 - 27 specialties in 5 batches (6+6+5+5+5)."""

TRADES_K1_BATCH1: dict[str, list[dict]] = {
    "trades_transportation_planning": [
        {"title": "Transportation Planning - Field Overview", "content": """# Transportation Planning

## Definition
Transportation planning is the process of developing strategies and systems for the movement of people and goods.

## Core Areas
- Travel demand: forecasting trips
- Mode choice: how people travel
- Network design: roads, transit
- Capacity analysis: level of service
- Environmental impact: assessment
- Finance: funding projects
- Policy: regulations

## Key Concepts
- Trip generation: origins
- Trip distribution: destinations
- Mode choice: which mode
- Route assignment: which path
- Level of service: A-F
- Capacity: vehicles per hour
- VMT: vehicle miles traveled
- TOD: transit-oriented development

## Foundational Texts
- Meyer & Miller, "Urban Transportation Planning"
- Ortuzar & Willumsen, "Modelling Transport"

## Authority Note
Advisory. AASHTO standards; MPOs coordinate; federal funding.""", "tags": ["transportation planning", "demand", "transit", "overview"]}
    ],
    "trades_logistics": [
        {"title": "Logistics - Field Overview", "content": """# Logistics

## Definition
Logistics is the management of the flow of goods, information, and resources from origin to consumption.

## Core Areas
- Transportation: move goods
- Warehousing: store goods
- Inventory: manage stock
- Packaging: protect products
- Material handling: move within facility
- Distribution: deliver to customers
- Reverse logistics: returns

## Key Concepts
- Supply chain: end to end
- Lead time: order to delivery
- Cycle time: process duration
- Throughput: rate of flow
- Fill rate: orders fulfilled
- On-time delivery: schedule adherence
- LTL: less than truckload
- FTL: full truckload

## Foundational Texts
- Chopra & Meindl, "Supply Chain Management"
- Christopher, "Logistics & Supply Chain Management"

## Authority Note
Advisory. CSCMP professional; APICS certification.""", "tags": ["logistics", "supply chain", "warehousing", "distribution", "overview"]}
    ],
    "trades_warehousing": [
        {"title": "Warehousing - Field Overview", "content": """# Warehousing

## Definition
Warehousing is the storage of goods in a facility until they are needed.

## Core Areas
- Receiving: accept deliveries
- Put-away: store items
- Storage: hold inventory
- Picking: select items
- Packing: prepare orders
- Shipping: send out
- Cross-docking: bypass storage

## Key Concepts
- SKU: stock keeping unit
- Slotting: item placement
- ABC analysis: prioritize
- FIFO/LIFO: inventory methods
- WMS: warehouse management system
- Pallet: standard load
- ASN: advance shipping notice
- Cycle counting: inventory check

## Foundational Texts
- Bartholdi & Hackman, "Warehouse & Distribution Science"
- Mulcahy, "Warehouse Distribution and Operations"

## Authority Note
Advisory. WERC professional; OSHA regulates safety.""", "tags": ["warehousing", "storage", "picking", "WMS", "overview"]}
    ],
    "trades_fleet_management": [
        {"title": "Fleet Management - Field Overview", "content": """# Fleet Management

## Definition
Fleet management is the administration of a group of commercial vehicles to maximize efficiency, safety, and compliance.

## Core Areas
- Vehicle acquisition: purchase/lease
- Maintenance: scheduled and repair
- Fuel management: consumption
- Driver management: hiring, training
- Safety: accident prevention
- Compliance: regulations
- Telematics: GPS tracking
- Routing: optimize paths

## Key Concepts
- TCO: total cost of ownership
- Utilization: vehicle usage
- Downtime: not available
- Preventive maintenance: scheduled
- Telematics: vehicle data
- ELD: electronic logging device
- DOT: Department of Transportation
- HOS: hours of service

## Foundational Texts
- Sutherland, "Fleet Management"
- NAFA Fleet Management Association resources

## Authority Note
Advisory. NAFA professional; DOT/FMCSA regulate.""", "tags": ["fleet management", "vehicles", "maintenance", "telematics", "overview"]}
    ],
    "trades_aviation_operations": [
        {"title": "Aviation Operations - Field Overview", "content": """# Aviation Operations

## Definition
Aviation operations encompasses the management of aircraft, airports, air traffic, and ground services.

## Core Areas
- Air traffic control: manage flow
- Airport operations: ground services
- Flight operations: cockpit
- Aircraft maintenance: airworthiness
- Safety management: SMS
- Security: passenger, cargo
- Dispatch: flight planning

## Key Concepts
- ATC: air traffic control
- IFR: instrument flight rules
- VFR: visual flight rules
- NOTAM: notice to airmen
- METAR: weather report
- AOC: air operator certificate
- ETOPS: extended operations
- RVSM: reduced vertical separation

## Foundational Texts
- Wells & Young, "Commercial Aviation Safety"
- Nolan, "Fundamentals of Air Traffic Control"

## Authority Note
Advisory. FAA regulates (US); ICAO international.""", "tags": ["aviation operations", "ATC", "airport", "safety", "overview"]}
    ],
    "trades_rail_systems": [
        {"title": "Rail Systems - Field Overview", "content": """# Rail Systems

## Definition
Rail systems involve the operation and management of railway transportation for passengers and freight.

## Core Areas
- Operations: train movement
- Signaling: control systems
- Track: infrastructure
- Rolling stock: locomotives, cars
- Stations: passenger facilities
- Freight: cargo terminals
- Safety: accident prevention
- Maintenance: upkeep

## Key Concepts
- Gauge: track width
- Grade: slope
- Curve: radius
- Tonnage: weight
- Headway: time between trains
- Block: track section
- Interlocking: switches
- PTC: positive train control

## Foundational Texts
- Profillidis, "Railway Management and Engineering"
- AREMA manuals

## Authority Note
Advisory. FRA regulates (US); AREMA standards.""", "tags": ["rail systems", "railways", "signaling", "operations", "overview"]}
    ],
}

TRADES_K1_BATCH2: dict[str, list[dict]] = {
    "trades_maritime_operations": [
        {"title": "Maritime Operations - Field Overview", "content": """# Maritime Operations

## Definition
Maritime operations encompass the management of ships, ports, and waterborne commerce.

## Core Areas
- Ship operations: navigation
- Port operations: cargo handling
- Pilotage: harbor navigation
- Tug services: assist ships
- Marine safety: prevention
- Environmental: pollution
- Customs: trade compliance
- Salvage: rescue

## Key Concepts
- Draft: depth below water
- Tonnage: capacity measure
- Berth: ship position
- Pilot: local expert
- AIS: automatic identification
- SOLAS: safety of life at sea
- MARPOL: pollution prevention
- STCW: training standards

## Foundational Texts
- Bichou, "Port Operations"
- IMO publications

## Authority Note
Advisory. IMO international; USCG regulates (US).""", "tags": ["maritime operations", "ports", "ships", "safety", "overview"]}
    ],
    "trades_space_mission_operations": [
        {"title": "Space Mission Operations - Field Overview", "content": """# Space Mission Operations

## Definition
Space mission operations involve the planning, execution, and monitoring of spacecraft and satellite missions.

## Core Areas
- Mission planning: objectives
- Launch operations: liftoff
- Flight dynamics: orbits
- Telemetry: data from spacecraft
- Command: instructions to spacecraft
- Anomaly: problem handling
- Ground stations: communication
- Data processing: science

## Key Concepts
- Orbit: path around body
- Attitude: orientation
- Telemetry: downlink data
- Telecommand: uplink
- Ephemeris: position data
- Delta-V: velocity change
- Eclipse: shadow period
- Pass: ground station contact

## Foundational Texts
- Wertz et al., "Space Mission Engineering"
- Larson & Wertz, "Space Mission Analysis and Design"

## Authority Note
Advisory. NASA standards; ESA; commercial space.""", "tags": ["space operations", "satellites", "telemetry", "missions", "overview"]}
    ],
    "trades_utilities": [
        {"title": "Utilities - Field Overview", "content": """# Utilities

## Definition
Utilities are essential services including electricity, gas, water, and telecommunications provided to the public.

## Core Areas
- Electric power: generation, distribution
- Natural gas: distribution
- Water: supply, treatment
- Wastewater: collection, treatment
- Telecommunications: phone, internet
- District heating: thermal
- Solid waste: collection

## Key Concepts
- Grid: electrical network
- Distribution: to customers
- Transmission: high voltage
- Metering: usage measurement
- Tariff: pricing structure
- Reliability: uptime
- Demand response: load management
- Smart grid: intelligent network

## Foundational Texts
- Willis, "Power Distribution Planning Reference"
- Mays, "Water Resources Engineering"

## Authority Note
Advisory. Regulated by public utility commissions.""", "tags": ["utilities", "electric", "water", "gas", "overview"]}
    ],
    "trades_renewable_energy_operations": [
        {"title": "Renewable Energy Operations - Field Overview", "content": """# Renewable Energy Operations

## Definition
Renewable energy operations involve the management of power generation from renewable sources: solar, wind, hydro, geothermal, biomass.

## Core Areas
- Solar: PV, CSP plants
- Wind: onshore, offshore
- Hydro: dams, run-of-river
- Geothermal: steam plants
- Biomass: combustion
- Grid integration: connection
- Storage: batteries
- Maintenance: upkeep

## Key Concepts
- Capacity factor: actual / rated
- Intermittency: variable output
- Curtailed: wasted energy
- LCOE: levelized cost
- PPA: power purchase agreement
- Net metering: sell back
- Inverter: DC to AC
- SCADA: monitoring

## Foundational Texts
- Masters, "Renewable and Efficient Electric Power Systems"
- Boyle, "Renewable Energy"

## Authority Note
Advisory. NREL research; FERC regulates interstate.""", "tags": ["renewable energy", "solar", "wind", "operations", "overview"]}
    ],
    "trades_construction_management": [
        {"title": "Construction Management - Field Overview", "content": """# Construction Management

## Definition
Construction management is the planning, coordination, and control of a construction project from start to finish.

## Core Areas
- Project planning: schedule
- Cost management: budget
- Quality management: standards
- Safety management: prevent accidents
- Contract administration: agreements
- Resource management: labor, materials
- Risk management: identify, mitigate
- Communication: stakeholders

## Key Concepts
- CPM: critical path method
- Gantt chart: visual schedule
- Change order: modification
- RFI: request for information
- Submittal: product data
- Punch list: incomplete items
- Lien: legal claim
- Bond: financial guarantee

## Foundational Texts
- Halpin, "Construction Management"
- Construction Management Association of America resources

## Authority Note
Advisory. CMAA professional; AIA contracts; OSHA safety.""", "tags": ["construction management", "project", "safety", "scheduling", "overview"]}
    ],
    "trades_carpentry": [
        {"title": "Carpentry - Field Overview", "content": """# Carpentry

## Definition
Carpentry is the skilled trade of cutting, shaping, and installing building materials, primarily wood.

## Core Areas
- Rough carpentry: framing
- Finish carpentry: trim, cabinets
- Framing: walls, floors, roofs
- Siding: exterior
- Roofing: shingles
- Drywall: installation
- Doors and windows: installation
- Cabinets: built-in

## Key Concepts
- Stud: vertical framing
- Joist: floor support
- Rafter: roof support
- Plate: top/bottom of wall
- Header: above opening
- Plywood: sheet material
- Lumber: wood sizes (2x4)
- Pitch: roof slope

## Foundational Texts
- Spence, "Residential Construction Academy: Carpentry"
- Wagner, "Modern Carpentry"

## Authority Note
Advisory. NCCER certification; building codes regulate.""", "tags": ["carpentry", "framing", "wood", "construction", "overview"]}
    ],
}

TRADES_K1_BATCH3: dict[str, list[dict]] = {
    "trades_residential_electrical_work": [
        {"title": "Residential Electrical Work - Field Overview", "content": """# Residential Electrical Work

## Definition
Residential electrical work involves the installation, maintenance, and repair of electrical systems in homes.

## Core Areas
- Service: main panel
- Branch circuits: to outlets
- Lighting: fixtures
- Outlets: receptacles
- Switches: control
- Grounding: safety
- Smoke detectors: safety
- EV charging: vehicle

## Key Concepts
- Voltage: 120/240V
- Amperage: current capacity
- Circuit: protected path
- Breaker: overcurrent protection
- GFCI: ground fault interrupt
- AFCI: arc fault interrupt
- Ground: safety path
- Neutral: return path

## Foundational Texts
- Mullin, "Electrical Wiring Residential"
- NEC (National Electrical Code)

## Authority Note
Advisory. NEC code; licensure required; permits.""", "tags": ["residential electrical", "wiring", "NEC", "overview"]}
    ],
    "trades_plumbing": [
        {"title": "Plumbing - Field Overview", "content": """# Plumbing

## Definition
Plumbing is the system of pipes, fixtures, and fittings for water supply and waste removal in buildings.

## Core Areas
- Water supply: potable
- Drainage: waste removal
- Venting: air for drains
- Fixtures: sinks, toilets
- Water heaters: hot water
- Gas lines: fuel
- Irrigation: outdoor
- Backflow: prevention

## Key Concepts
- PSI: pressure
- GPM: flow rate
- DWV: drain-waste-vent
- P-trap: seal
- Vent: air admittance
- Shutoff valve: isolation
- Solder: copper joining
- PEX: flexible pipe

## Foundational Texts
- Stancliff, "Plumbing"
- IPC (International Plumbing Code)

## Authority Note
Advisory. IPC code; licensure required; permits.""", "tags": ["plumbing", "water supply", "drainage", "overview"]}
    ],
    "trades_hvac": [
        {"title": "HVAC - Field Overview", "content": """# HVAC

## Definition
HVAC (Heating, Ventilation, and Air Conditioning) is the technology of indoor environmental comfort control.

## Core Areas
- Heating: furnaces, boilers
- Cooling: air conditioners
- Ventilation: air exchange
- Air quality: filtration
- Controls: thermostats
- Ductwork: air distribution
- Refrigeration: cooling cycle
- Heat pumps: reverse cycle

## Key Concepts
- BTU: heat unit
- Ton: cooling capacity
- SEER: efficiency rating
- AFUE: furnace efficiency
- CFM: airflow
- Refrigerant: cooling fluid
- Compressor: pressure
- Evaporator: absorbs heat

## Foundational Texts
- Whitman et al., "Refrigeration and Air Conditioning"
- IMC (International Mechanical Code)

## Authority Note
Advisory. EPA 608 certification; IMC code; licensure.""", "tags": ["HVAC", "heating", "cooling", "ventilation", "overview"]}
    ],
    "trades_welding_metalworking": [
        {"title": "Welding and Metalworking - Field Overview", "content": """# Welding and Metalworking

## Definition
Welding joins metals by melting. Metalworking shapes metal through various processes.

## Core Areas
- Arc welding: SMAW, GMAW, GTAW
- Gas welding: oxy-fuel
- Resistance welding: spot
- Cutting: torch, plasma
- Bending: forming
- Grinding: finishing
- Machining: cutting
- Sheet metal: thin stock

## Key Concepts
- Electrode: filler
- Shielding gas: protect
- Flux: clean
- Penetration: depth
- Bead: weld deposit
- Filler: added metal
- Heat-affected zone: HAZ
- Distortion: warping

## Foundational Texts
- Jefferson & Woods, "Metals and How to Weld Them"
- AWS Welding Handbook

## Authority Note
Advisory. AWS certification; AWS D1.1 structural code.""", "tags": ["welding", "metalworking", "fabrication", "overview"]}
    ],
    "trades_machining": [
        {"title": "Machining - Field Overview", "content": """# Machining

## Definition
Machining is a manufacturing process that cuts material to create desired shapes and dimensions.

## Core Areas
- Turning: lathe
- Milling: milling machine
- Drilling: holes
- Grinding: precision
- CNC: computer control
- EDM: electrical discharge
- Broaching: shaping
- Tapping: threads

## Key Concepts
- Tolerance: allowable variation
- Surface finish: roughness
- Feed rate: material input
- Cutting speed: tool speed
- Depth of cut: material removed
- Chip: waste material
- Coolant: lubricate, cool
- Fixture: hold work

## Foundational Texts
- Krar et al., "Technology of Machine Tools"
- Machinery's Handbook

## Authority Note
Advisory. NIMS certification; ASME standards.""", "tags": ["machining", "turning", "milling", "CNC", "overview"]}
    ],
}

TRADES_K1_BATCH4: dict[str, list[dict]] = {
    "trades_automotive_repair": [
        {"title": "Automotive Repair - Field Overview", "content": """# Automotive Repair

## Definition
Automotive repair is the diagnosis and correction of problems in motor vehicles.

## Core Areas
- Engine: diagnosis, repair
- Transmission: gearbox
- Brakes: stopping
- Suspension: ride
- Electrical: wiring, electronics
- HVAC: climate
- Exhaust: emissions
- Tires: wheels

## Key Concepts
- OBD-II: onboard diagnostics
- Diagnostic code: error
- Torque: rotational force
- Compression: cylinder pressure
- Timing: valve sync
- Misfire: no combustion
- Slipping: transmission
- Bleeding: brakes

## Foundational Texts
- Halderman, "Automotive Technology"
- ASE study guides

## Authority Note
Advisory. ASE certification; EPA refrigerant.""", "tags": ["automotive repair", "engine", "diagnostics", "overview"]}
    ],
    "trades_appliance_repair": [
        {"title": "Appliance Repair - Field Overview", "content": """# Appliance Repair

## Definition
Appliance repair is the diagnosis and correction of problems in household appliances.

## Core Areas
- Refrigerators: cooling
- Washers: laundry
- Dryers: drying
- Dishwashers: cleaning
- Ovens: cooking
- Microwaves: heating
- Disposals: waste
- Small appliances: misc

## Key Concepts
- Compressor: refrigeration
- Thermostat: temperature control
- Heating element: resistance
- Motor: rotating
- Timer: cycle control
- Solenoid: valve control
- Capacitor: motor start
- Relay: switch

## Foundational Texts
- Walker, "Major Appliances"
- PSA (Professional Service Association) materials

## Authority Note
Advisory. PSA certification; manufacturer training.""", "tags": ["appliance repair", "refrigerator", "washer", "overview"]}
    ],
    "trades_electronics_repair": [
        {"title": "Electronics Repair - Field Overview", "content": """# Electronics Repair

## Definition
Electronics repair is the diagnosis and correction of problems in electronic devices and equipment.

## Core Areas
- Consumer electronics: TVs, audio
- Computers: laptops, desktops
- Mobile devices: phones, tablets
- Power supplies: conversion
- Circuit boards: components
- Soldering: joining
- Test equipment: meters, scopes
- Data recovery: storage

## Key Concepts
- Solder: metal join
- Flux: clean
- Multimeter: measure
- Oscilloscope: waveform
- Continuity: connected
- Voltage: potential
- Resistance: opposition
- Capacitor: storage

## Foundational Texts
- Geier, "How to Diagnose and Fix Everything Electronic"
- Homer Davidson, "Troubleshooting and Repairing Consumer Electronics"

## Authority Note
Advisory. ETA certification; manufacturer training.""", "tags": ["electronics repair", "soldering", "diagnostics", "overview"]}
    ],
    "trades_computer_repair": [
        {"title": "Computer Repair - Field Overview", "content": """# Computer Repair

## Definition
Computer repair is the diagnosis and correction of hardware and software problems in computers.

## Core Areas
- Hardware: components
- Software: operating system
- Networking: connectivity
- Data recovery: lost files
- Virus removal: malware
- Upgrades: improvements
- Peripherals: printers, etc
- Laptops: portable

## Key Concepts
- POST: power-on self-test
- BIOS: basic input/output
- Driver: device software
- Registry: Windows settings
- Partition: disk section
- Format: file system
- Boot: startup
- Blue screen: crash

## Foundational Texts
- Mueller, "Upgrading and Repairing PCs"
- CompTIA A+ study guide

## Authority Note
Advisory. CompTIA A+ certification; vendor certs.""", "tags": ["computer repair", "hardware", "software", "overview"]}
    ],
    "trades_painting_finishing": [
        {"title": "Painting and Finishing - Field Overview", "content": """# Painting and Finishing

## Definition
Painting and finishing is the application of protective and decorative coatings to surfaces.

## Core Areas
- Interior: walls, trim
- Exterior: siding, trim
- Staining: wood
- Varnishing: clear coat
- Wallpaper: covering
- Drywall finishing: smooth
- Power washing: clean
- Caulking: seal

## Key Concepts
- Primer: base coat
- Latex: water-based
- Oil: solvent-based
- Sheen: gloss level
- Coverage: area per gallon
- Cure: full hardness
- Dry time: to touch
- VOC: volatile organic

## Foundational Texts
- PDCA (Painting and Decorating Contractors of America) materials
- Benjamin Moore Professional resources

## Authority Note
Advisory. PDCA standards; EPA VOC limits.""", "tags": ["painting", "finishing", "coatings", "overview"]}
    ],
}

TRADES_K1_BATCH5: dict[str, list[dict]] = {
    "trades_landscaping": [
        {"title": "Landscaping - Field Overview", "content": """# Landscaping

## Definition
Landscaping is the modification of visible features of an area of land, including living and non-living elements.

## Core Areas
- Design: plan
- Planting: trees, shrubs, flowers
- Lawn care: grass
- Irrigation: watering
- Hardscaping: patios, walls
- Lighting: outdoor
- Drainage: water management
- Maintenance: upkeep

## Key Concepts
- Hardiness zone: climate
- Soil pH: acidity
- Mulch: cover
- Compost: organic matter
- Grading: slope
- Retaining wall: hold earth
- Paver: stone, brick
- Xeriscape: drought tolerant

## Foundational Texts
- Hannebaum, "Landscape Design"
- ALCA (Associated Landscape Contractors of America) materials

## Authority Note
Advisory. ALCA professional; local regulations.""", "tags": ["landscaping", "design", "planting", "overview"]}
    ],
    "trades_solar_installation": [
        {"title": "Solar Installation - Field Overview", "content": """# Solar Installation

## Definition
Solar installation is the setup of photovoltaic (PV) systems to convert sunlight into electricity.

## Core Areas
- Site assessment: shading, roof
- System design: size, layout
- Mounting: racking
- Panels: PV modules
- Inverter: DC to AC
- Wiring: connections
- Battery: storage
- Grid connection: net metering

## Key Concepts
- kW: kilowatt (power)
- kWh: kilowatt-hour (energy)
- MPPT: max power point
- String inverter: centralized
- Microinverter: per panel
- Net metering: sell back
- Azimuth: direction
- Tilt: angle

## Foundational Texts
- Dunlop, "Photovoltaic Systems"
- NABCEP study materials

## Authority Note
Advisory. NABCEP certification; NEC 690; permits.""", "tags": ["solar installation", "PV", "inverter", "overview"]}
    ],
    "trades_building_inspection": [
        {"title": "Building Inspection - Field Overview", "content": """# Building Inspection

## Definition
Building inspection is the examination of buildings to verify compliance with codes and assess condition.

## Core Areas
- Residential: homes
- Commercial: businesses
- Electrical: wiring
- Plumbing: pipes
- Structural: foundation
- Mechanical: HVAC
- Energy: efficiency
- Pest: termites

## Key Concepts
- Code: building regulations
- Permit: approval
- CO: certificate of occupancy
- Defect: problem
- Safety: hazard
- Foundation: base
- Load bearing: supports
- Egress: exit

## Foundational Texts
- Casey, "The Complete Book of Home Inspection"
- ICC (International Code Council) materials

## Authority Note
Advisory. ICC certification; AHJ (authority having jurisdiction).""", "tags": ["building inspection", "codes", "compliance", "overview"]}
    ],
    "trades_fire_protection": [
        {"title": "Fire Protection - Field Overview", "content": """# Fire Protection

## Definition
Fire protection is the practice of preventing and mitigating the effects of fire.

## Core Areas
- Detection: alarms
- Suppression: sprinklers
- Prevention: education
- Egress: escape
- Construction: fire-rated
- Hazmat: hazardous materials
- Investigation: cause
- Code compliance: NFPA

## Key Concepts
- NFPA: National Fire Protection Assoc
- Fire triangle: fuel, heat, oxygen
- Class A: ordinary
- Class B: flammable liquid
- Class C: electrical
- Class D: metal
- Class K: kitchen
- Sprinkler: automatic

## Foundational Texts
- NFPA Fire Protection Handbook
- Cote, "Principles of Fire Protection"

## Authority Note
Advisory. NFPA codes; NICET certification; AHJ.""", "tags": ["fire protection", "sprinklers", "alarms", "NFPA", "overview"]}
    ],
    "trades_facilities_property_maintenance": [
        {"title": "Facilities and Property Maintenance - Field Overview", "content": """# Facilities and Property Maintenance

## Definition
Facilities and property maintenance is the upkeep of buildings, grounds, and systems to ensure functionality and safety.

## Core Areas
- Building systems: HVAC, electrical, plumbing
- Grounds: landscaping
- Cleaning: janitorial
- Repairs: fix problems
- Preventive: scheduled
- Security: access control
- Waste: disposal
- Energy: efficiency

## Key Concepts
- CMMS: computerized maintenance management
- Work order: task
- PM: preventive maintenance
- Reactive: fix when broken
- SLA: service level agreement
- KPI: key performance indicator
- Inventory: parts stock
- Lifecycle: asset life

## Foundational Texts
- Cotts et al., "The Facility Management Handbook"
- IFMA (International Facility Management Association) materials

## Authority Note
Advisory. IFMA professional; BOMA standards.""", "tags": ["facilities maintenance", "property", "CMMS", "overview"]}
    ],
}
