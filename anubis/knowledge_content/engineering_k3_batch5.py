"""Engineering & Design K3 Batch 5 - 5 specialties."""

ENGINEERING_K3_BATCH5: dict[str, list[dict]] = {
    "engineering_safety_human_factors": [
        {"title": "Safety Engineering and Human Factors Reference", "content": """# Safety Engineering and Human Factors Reference

## System Safety
### Principles
- Hazard: potential for harm
- Risk: probability x consequence
- ALARP: as low as reasonably practicable
- Defense in depth: multiple layers
- Inherently safer design: eliminate hazard

### Process
1. Identify hazards
2. Analyze causes
3. Evaluate risk
4. Control measures
5. Verify effectiveness
6. Monitor

## Hazard Analysis
### Techniques
- PHA: preliminary hazard analysis
- HAZOP: hazard and operability
- FMEA: failure mode and effects
- FTA: fault tree analysis
- ETA: event tree analysis
- LOPA: layer of protection analysis
- Bowtie: causes and consequences

### Risk Assessment
- Qualitative: high, medium, low
- Semi-quantitative: risk matrix
- Quantitative: QRA, probability calculations
- Risk matrix: severity x likelihood

### Risk Criteria
- Individual risk: per person
- Societal risk: F-N curves
- Environmental risk
- Economic risk

## Safety Engineering
### Design
- Inherently safer: eliminate, minimize, substitute, moderate, simplify
- Passive: no action needed (dikes, walls)
- Active: detect and respond (alarms, interlocks)
- Procedural: procedures and training

### Safety Critical Systems
- SIL: safety integrity level (1-4)
- IEC 61508: functional safety
- IEC 61511: process industry
- Redundancy; Diversity; Separation

### Safety Cases
- Demonstrate safety
- Identify hazards and controls
- ALARP argument
- UK: offshore, rail

## Human Factors
### Definition
- Apply knowledge of human capabilities and limitations to system design
- Goal: optimize performance, safety, comfort

### Human Capabilities
- Physical: strength, reach, movement
- Sensory: vision, hearing, touch
- Cognitive: attention, memory, decision
- Speed: reaction time

### Human Limitations
- Fatigue: physical, mental
- Stress: workload, time pressure
- Boredom: low arousal
- Bias: cognitive shortcuts
- Error: unintended action

## Human Error
### Classification (Reason)
- Slips: action error (skilled)
- Lapses: memory failure
- Mistakes: planning error
- Violations: intentional deviation

### Error Causes
- Inadequate training
- Poor procedures
- Bad interface design
- Time pressure
- Fatigue
- Distraction
- Organizational culture

### Error Models
- Swiss cheese: layered defenses with holes
- SHEL: software, hardware, environment, liveware
- SHELL: human at center

## Ergonomics
### Physical
- Workspace: dimensions
- Reach: controls, displays
- Posture: sitting, standing
- Force: lifting, pushing
- Repetition: strain injury

### Anthropometry
- Body dimensions
- Percentiles: 5th, 50th, 95th
- Design for range
- Adjustability

### Biomechanics
- Lifting: NIOSH equation
- Posture: neutral preferred
- Force: limits
- Frequency: repetition

## Human-Computer Interaction
### Principles
- Visibility: see system state
- Feedback: confirm actions
- Affordance: obvious use
- Consistency: similar = similar
- Error prevention: design out
- Error recovery: undo

### Displays
- Visual: text, graphics, color
- Auditory: alerts, speech
- Tactile: vibration
- Haptic: force feedback

### Controls
- Discrete: buttons, switches
- Continuous: knobs, sliders
- Direct manipulation: touch, gesture
- Voice: speech recognition

### Interface Design
- Norman's principles
- Mental models: user understanding
- Information density: not too much
- Hierarchy: organize information
- Color coding: consistent meaning

## Cognitive Engineering
### Attention
- Selective: focus
- Divided: multitask
- Sustained: vigilance
- Limitations: 7 +/- 2 items

### Memory
- Working: short term, limited
- Long-term: knowledge
- Prospective: remember to do
- Recognition vs recall

### Decision Making
- Recognition-primed: expert
- Analytical: compare options
- Heuristics: shortcuts
- Biases: confirmation, availability, anchoring

### Situation Awareness
- Level 1: perceive elements
- Level 2: understand meaning
- Level 3: project future
- Endsley model

## Safety Culture
### Elements
- Leadership commitment
- Employee involvement
- Continuous learning
- Just culture (no blame)
- Reporting culture
- Flexible culture

### Indicators
- Leading: proactive (training, audits)
- Lagging: reactive (incidents, injuries)
- Near misses: learn from

### Maturity
- Pathological: who cares
- Reactive: fix when found
- Calculative: systems in place
- Proactive: anticipate
- Generative: safety is how we do business

## Accident Investigation
### Process
1. Secure scene
2. Gather evidence
3. Interview witnesses
4. Analyze data
5. Determine causes
6. Recommendations
7. Follow up

### Causation Models
- Domino: sequence of events
- Swiss cheese: layered defenses
- AcciMap: system levels
- STAMP: systems-theoretic

### Root Cause
- 5 Whys
- Fishbone (Ishikawa)
- Fault tree
- Why-because analysis

## Regulations
### OSHA (US)
- General industry; Construction
- PSM: process safety management
- 29 CFR 1910.119

### EPA
- RMP: risk management plan
- 40 CFR Part 68

### Other
- MSHA: mining
- FRA: railroad
- FAA: aviation
- NRC: nuclear
- DOT: transportation

## Common Pitfalls
- Blaming operator without fixing system
- Not considering human limitations
- Poor interface design
- Inadequate training
- No just culture
- Not learning from near misses
- Over-reliance on procedures
""", "tags": ["safety engineering", "human factors", "ergonomics", "risk", "safety culture", "reference"]}
    ],
    "engineering_architecture": [
        {"title": "Architectural Design and Practice Reference", "content": """# Architectural Design and Practice Reference

## Design Process
### Phases (AIA)
1. Programming: define needs
2. Schematic design (SD): concepts
3. Design development (DD): details
4. Construction documents (CD): drawings, specs
5. Bidding/negotiation: select contractor
6. Construction administration (CA): observe

### Programming
- Client needs
- Space requirements
- Functional relationships
- Budget
- Site analysis
- Code research

## Design Principles
### Vitruvius
- Firmitas: firmness (structure)
- Utilitas: commodity (function)
- Venustas: delight (beauty)

### Form
- Mass: solid
- Void: empty
- Plane: flat surface
- Volume: 3D space
- Scale: relative size
- Proportion: ratio

### Space
- Enclosed: walls
- Open: minimal definition
- Transitional: in between
- Sequential: series
- Hierarchical: importance

### Order
- Axis: line of organization
- Symmetry: mirror
- Hierarchy: ranking
- Rhythm: repetition
- Datum: reference
- Transformation: change

## Site Design
### Analysis
- Topography: land form
- Climate: sun, wind, rain
- Vegetation: existing
- Access: roads, paths
- Views: visual
- Neighbors: context
- Utilities: available

### Response
- Orientation: sun, wind
- Grading: earthwork
- Drainage: water management
- Landscaping: plants
- Circulation: paths
- Parking: vehicles

## Building Systems
### Structural
- Frame: skeleton
- Load bearing: walls support
- Shear: lateral resistance
- Foundation: transfer to ground

### Enclosure
- Walls: exterior
- Roof: top
- Windows: openings
- Doors: entries
- Insulation: thermal
- Waterproofing: moisture

### Mechanical
- HVAC: heating, cooling, ventilation
- Plumbing: water, waste
- Electrical: power, lighting
- Fire: detection, suppression

### Materials
- Wood: light frame, heavy timber
- Steel: frame, cladding
- Concrete: cast, precast
- Masonry: brick, block, stone
- Glass: curtain wall
- Composites: modern

## Codes and Standards
### IBC (International Building Code)
- Occupancy: use classification
- Construction type: fire resistance
- Height and area: limits
- Egress: exits, travel distance
- Fire: separation, sprinklers
- Accessibility: ADA

### Types (IBC)
- Type I: fire resistive (most protected)
- Type II: non-combustible
- Type III: mixed
- Type IV: heavy timber
- Type V: wood frame (least protected)

### Occupancy
- A: assembly
- B: business
- E: educational
- F: factory
- H: high hazard
- I: institutional
- M: mercantile
- R: residential
- S: storage
- U: utility

## Sustainability
### LEED
- Location and transportation
- Sustainable sites
- Water efficiency
- Energy and atmosphere
- Materials and resources
- Indoor environmental quality
- Innovation
- Regional priority

### Strategies
- Passive solar: orient, mass
- Natural ventilation: airflow
- Daylighting: natural light
- Insulation: thermal envelope
- Renewable: solar, wind
- Water: harvest, reuse
- Materials: local, recycled
- Green roof: plants

### Net Zero
- Produce as much energy as used
- On-site renewable
- High efficiency
- Energy storage

## Urban Design
### Principles
- Mixed use: combine activities
- Walkability: pedestrian friendly
- Connectivity: street network
- Density: compact
- Public realm: shared spaces
- Identity: sense of place

### Patterns
- Grid: regular blocks
- Radial: from center
- Organic: informal
- Cul-de-sac: suburban

## History
### Periods
- Classical: Greek, Roman
- Romanesque: medieval
- Gothic: pointed arches
- Renaissance: rebirth
- Baroque: ornate
- Modern: 20th century
- Contemporary: current

### Movements
- Bauhaus: form follows function
- International Style: glass, steel
- Brutalism: concrete
- Postmodern: historical reference
- Deconstructivism: fragmented
- Parametric: digital

## Practice
### Services
- Design: buildings
- Planning: sites
- Interior: spaces
- Renovation: existing
- Preservation: historic
- Research: materials, methods

### Delivery
- Design-bid-build: traditional
- Design-build: single contract
- CM: construction manager
- IPD: integrated

### Technology
- CAD: 2D drafting
- BIM: 3D modeling (Revit, ArchiCAD)
- Rendering: visualization
- Parametric: Grasshopper
- VR: virtual reality
- 3D printing: models

## Common Pitfalls
- Not understanding client needs
- Ignoring site context
- Poor code compliance
- Inadequate detailing
- Not coordinating with engineers
- Over budget
- Not considering maintenance
""", "tags": ["architecture", "design", "buildings", "sustainability", "practice", "reference"]}
    ],
    "engineering_urban_regional_planning": [
        {"title": "Urban and Regional Planning Reference", "content": """# Urban and Regional Planning Reference

## Planning Process
### Steps
1. Identify issues
2. Establish goals
3. Collect data
4. Analyze
5. Develop alternatives
6. Evaluate
7. Implement
8. Monitor

### Comprehensive Plan
- Long-term vision
- Land use
- Transportation
- Housing
- Economic development
- Environment
- Community facilities
- Implementation

## Land Use
### Zoning
- Districts: residential, commercial, industrial
- Use regulations: allowed activities
- Density: units per acre
- Height: building limits
- Setbacks: yard requirements
- Lot size: minimum
- Coverage: max footprint

### Types
- Euclidean: use-based (most common)
- Performance: impact-based
- Form-based: building form
- Incentive: bonuses for amenities
- Mixed use: combined

### Smart Growth
- Mixed land use
- Compact design
- Range of housing
- Walkable neighborhoods
- Distinctive communities
- Preserve open space
- Direct development to existing
- Variety of transportation
- Predictable decisions
- Stakeholder collaboration

## Transportation
### Modes
- Highway: personal vehicle
- Transit: bus, rail
- Bicycle: lanes, paths
- Pedestrian: sidewalks, trails
- Freight: truck, rail, water

### Planning
- Travel demand: trips
- Mode choice: how people travel
- Route assignment: which roads
- Capacity: vehicles per hour
- Level of service: A-F

### Transit
- Bus: flexible
- BRT: bus rapid transit
- Light rail: urban
- Heavy rail: subway, commuter
- TOD: transit-oriented development

### Complete Streets
- All users: drivers, transit, bikes, pedestrians
- All ages and abilities
- Safe, convenient, comfortable

## Housing
### Issues
- Affordability: cost vs income
- Supply: enough units
- Quality: condition
- Location: near jobs
- Choice: variety

### Tools
- Inclusionary zoning: require affordable
- Density bonus: more units for affordable
- Housing trust fund: finance
- Vouchers: rent assistance
- LIHTC: low income housing tax credit

### Types
- Single family: detached
- Multi-family: attached
- Mixed use: with commercial
- Senior: age-restricted
- Supportive: with services

## Economic Development
### Goals
- Job creation
- Tax base
- Investment
- Revitalization
- Innovation

### Strategies
- Business attraction
- Business retention
- Business creation
- Workforce development
- Tourism
- Industry clusters

### Tools
- TIF: tax increment financing
- Enterprise zones: incentives
- Revolving loan funds
- Infrastructure
- Brownfield redevelopment

## Environmental Planning
### Issues
- Air quality
- Water quality
- Habitat
- Open space
- Climate change
- Sustainability

### Tools
- Environmental review (NEPA)
- Conservation easements
- Transfer of development rights
- Green infrastructure
- Urban growth boundary
- Cluster development

### Natural Hazards
- Flood: floodplain management
- Earthquake: building codes
- Wildfire: defensible space
- Hurricane: evacuation, codes
- Landslide: slope regulations

## Community Development
### Social Issues
- Equity: fair distribution
- Environmental justice
- Health: food access, activity
- Education: schools
- Safety: crime prevention
- Arts and culture

### Engagement
- Public meetings
- Workshops
- Surveys
- Focus groups
- Online platforms
- Stakeholder committees

## Regional Planning
### Issues
- Multi-jurisdictional
- Coordination
- Shared resources
- Transportation networks
- Watersheds
- Economic clusters

### Organizations
- MPO: metropolitan planning organization
- COG: council of governments
- Regional planning commission
- State planning

## Implementation
### Tools
- Zoning: regulations
- Subdivision: lot creation
- Site plan review: project
- Capital improvements: public projects
- Budget: funding
- Permits: approval

### Legal Basis
- Police power: protect health, safety, welfare
- Zoning: Euclid v. Ambler (1926)
- Comprehensive plan: basis
- Due process: fair procedures
- Equal protection: no discrimination
- Takings: just compensation

## Data and Analysis
### Demographics
- Population: count
- Age: distribution
- Income: economic
- Education: attainment
- Household: composition

### Economic
- Employment: jobs
- Industry: sectors
- Income: wages
- Tax: revenue
- Property: value

### GIS
- Mapping: spatial
- Analysis: overlay
- Data: layers
- Visualization: communicate

## Common Pitfalls
- Not engaging community
- Ignoring equity
- Single-use zoning (sprawl)
- Not planning for transportation
- Ignoring environmental constraints
- Not coordinating regionally
- No implementation strategy
""", "tags": ["urban planning", "land use", "zoning", "transportation", "housing", "reference"]}
    ],
    "engineering_surveying_geomatics": [
        {"title": "Surveying and Geomatics Reference", "content": """# Surveying and Geomatics Reference

## Fundamentals
### Definitions
- Surveying: measure and map earth's surface
- Geomatics: surveying + GIS, remote sensing, GPS

### Reference Systems
- Datum: reference surface
- Ellipsoid: mathematical earth
- Geoid: equipotential surface (mean sea level)
- Coordinate system: location reference

### Datums (US)
- NAD27: North American Datum 1927
- NAD83: 1983 (geocentric)
- NAVD88: vertical datum
- WGS84: World Geodetic System (GPS)

## Types of Surveying
### Land Surveying
- Property boundaries
- Legal descriptions
- Subdivision platting
- Easements
- Topographic survey

### Construction
- Layout: stake location
- As-built: verify
- Grading: earthwork
- Alignment: roads, utilities

### Topographic
- Terrain features
- Contours: elevation lines
- Spot elevations
- Drainage
- Vegetation

### Route
- Linear projects: roads, pipelines
- Centerline: alignment
- Profile: vertical
- Cross-section: perpendicular

### Geodetic
- Large areas
- Earth curvature
- High precision
- Control network

### Hydrographic
- Underwater terrain
- Depths: sounding
- Tides: water level
- Navigation charts

## Measurements
### Distance
- Tape: steel, fiberglass
- Electronic: EDM (electronic distance measurement)
- Total station: angle and distance
- Laser: precise

### Angle
- Total station: horizontal, vertical
- Theodolite: angles only
- Transit: older instrument

### Leveling
- Differential: precise elevations
- Benchmark: known elevation
- Turning point: temporary
- HI: height of instrument

### Errors
- Systematic: consistent (correctable)
- Random: unpredictable (averaged)
- Blunders: mistakes (avoided)
- Correction: apply to systematic

## GPS/GNSS
### System
- Satellites: 24+ in orbit
- Constellations: GPS (US), GLONASS (Russia), Galileo (Europe), BeiDou (China)
- Signals: L1, L2, L5
- Receivers: track satellites

### Positioning
- Trilateration: distance to satellites
- Pseudorange: code measurement
- Carrier phase: precise
- RTK: real-time kinematic (cm)
- PPP: precise point positioning

### Accuracy
- Autonomous: 3-10 m
- DGPS: 0.5-3 m
- RTK: 1-3 cm
- Static: mm

### Applications
- Control surveys
- Mapping
- Navigation
- GIS data collection
- Construction
- Agriculture
- Monitoring

## GIS
### Components
- Hardware: computers, GPS
- Software: ArcGIS, QGIS
- Data: spatial, attribute
- People: users
- Methods: procedures

### Data Types
- Vector: points, lines, polygons
- Raster: grid cells
- TIN: triangulated irregular network
- Attribute: tabular

### Analysis
- Overlay: combine layers
- Buffer: distance
- Intersect: common area
- Union: combine
- Network: routing
- Surface: terrain analysis

### Coordinate Systems
- Geographic: lat/lon
- Projected: x/y (UTM, State Plane)
- Scale: representative fraction
- Resolution: cell size

## Remote Sensing
### Types
- Aerial: airplane photography
- Satellite: orbital
- Drone (UAV): low altitude
- LiDAR: laser
- Radar: microwave
- Multispectral: multiple bands
- Hyperspectral: many bands

### Resolution
- Spatial: pixel size
- Spectral: wavelength bands
- Temporal: revisit time
- Radiometric: sensitivity

### Applications
- Land cover: classification
- Agriculture: crops, health
- Forestry: inventory
- Urban: growth
- Environment: monitoring
- Disaster: response

## Photogrammetry
### Aerial
- Stereo pairs: overlapping photos
- Parallax: depth perception
- Ground control: known points
- Orthophoto: corrected image

### Process
1. Flight planning
2. Photography
3. Ground control
4. Triangulation
5. Stereocompilation
6. Orthorectification

### Products
- Topographic maps
- Digital elevation model (DEM)
- Digital surface model (DSM)
- Orthophoto mosaic
- 3D models

## LiDAR
### Principle
- Laser: light pulses
- Time of flight: distance
- Returns: multiple (canopy, ground)
- Point cloud: 3D points

### Types
- Airborne: aircraft, drone
- Terrestrial: tripod
- Mobile: vehicle
- Bathymetric: water depth

### Products
- DEM: bare earth
- DSM: surface
- Point cloud: raw
- Contours: derived
- 3D models

## Mapping
### Projections
- Cylindrical: Mercator
- Conic: Lambert
- Azimuthal: polar
- UTM: Universal Transverse Mercator
- State Plane: local

### Scale
- Large: 1:24,000 (more detail)
- Small: 1:1,000,000 (less detail)
- Representative fraction: 1/x

### Cartography
- Generalization: simplify
- Symbolization: represent
- Labeling: identify
- Color: meaning
- Layout: design

## Common Pitfalls
- Wrong datum or coordinate system
- Not checking measurements
- Poor control network
- Not documenting work
- Ignoring errors
- Not verifying field work
- Inadequate equipment calibration
""", "tags": ["surveying", "geomatics", "GPS", "GIS", "remote sensing", "reference"]}
    ],
    "engineering_additive_manufacturing_3d_printing": [
        {"title": "Additive Manufacturing Technologies Reference", "content": """# Additive Manufacturing Technologies Reference

## Overview
### Definition
- Additive manufacturing (AM): build objects layer by layer
- From digital model
- Contrast: subtractive (machining)

### Benefits
- Complex geometry: impossible otherwise
- Customization: personalized
- Rapid prototyping: fast iteration
- Low volume: economical
- Material efficiency: little waste
- Assembly consolidation: one part

### Limitations
- Speed: slower than mass production
- Surface finish: often rough
- Material: limited selection
- Cost: high for large
- Post-processing: often needed
- Quality: variability

## Process Chain
1. CAD: design model
2. STL/OBJ: export format
3. Slice: convert to layers
4. Setup: machine preparation
5. Print: build part
6. Post-process: finish
7. Inspect: verify

## Technologies (ISO/ASTM 52900)
### Material Extrusion (FDM/FFF)
- Fused deposition modeling
- Thermoplastic filament: PLA, ABS, PETG, TPU
- Heated nozzle: melt
- Layer by layer: extrude
- Most common, affordable
- Resolution: 0.1-0.3 mm

### Vat Photopolymerization (SLA/DLP)
- Stereolithography: laser
- Digital light processing: projector
- Liquid resin: photopolymer
- UV light: cure
- High resolution: 0.025-0.1 mm
- Smooth surface
- Brittle; UV sensitive

### Powder Bed Fusion
#### SLS (Selective Laser Sintering)
- Laser: sinter polymer powder (nylon)
- Self-supporting: powder bed
- No supports needed
- Functional parts

#### DMLS/SLM (Metal)
- Direct metal laser sintering
- Selective laser melting
- Metal powder: titanium, steel, aluminum, Inconel
- High strength
- Expensive

#### MJF (Multi Jet Fusion)
- HP technology
- Fusing agent + infrared
- Nylon powder
- Fast, production quality

### Material Jetting (PolyJet/MJP)
- Print head: jet material
- UV cure: immediately
- Multiple materials: colors, properties
- High resolution
- Support material: dissolvable

### Binder Jetting
- Powder bed: metal, sand, ceramic
- Binder: jetted adhesive
- Layer by layer
- Sinter: post-process (metal)
- Sand: for casting molds
- Color: possible

### Sheet Lamination
- Sheets: stacked and bonded
- LOM: laminated object manufacturing
- UAM: ultrasonic additive manufacturing
- Metal sheets: ultrasonic welding

### Directed Energy Deposition (DED)
- Wire or powder: fed to melt
- Laser, electron beam, arc
- Large parts: possible
- Repair: build on existing
- Hybrid: with machining

## Materials
### Polymers
- PLA: easy, biodegradable
- ABS: durable, impact
- PETG: chemical resistant
- TPU: flexible
- Nylon: strong, wear
- Ultem: high temp, aerospace
- Resin: photopolymer (various)

### Metals
- Titanium (Ti6Al4V): aerospace, medical
- Stainless steel (316L, 17-4): general
- Aluminum (AlSi10Mg): light
- Inconel (718, 625): high temp
- Cobalt-chrome: medical, wear
- Copper: thermal

### Ceramics
- Alumina; Zirconia; Silicon carbide
- Technical ceramics
- Binder jetting + sinter

### Composites
- Carbon fiber reinforced
- Chopped or continuous
- FDM and DED

### Biomaterials
- Biocompatible: titanium, PEEK
- Scaffolds: tissue engineering
- Drug delivery

## Design for AM (DfAM)
### Principles
- Complexity is free: organic shapes
- Consolidation: combine parts
- Lightweight: lattice, hollow
- Customization: individual
- Internal features: channels

### Guidelines
- Minimize support: self-supporting angles
- Orient: optimize for strength, finish
- Wall thickness: minimum
- Tolerances: account for shrinkage
- Holes: round, not square
- Overhangs: < 45 degrees

### Lattice Structures
- Lightweight: reduce material
- Strength: maintain
- Energy absorption: crash
- Heat transfer: surface area
- Types: strut, TPMS (gyroid)

## Software
### CAD
- SolidWorks, Fusion 360, Inventor
- FreeCAD, Onshape
- Parametric: editable
- Direct: flexible

### Slicers
- Cura: Ultimaker, open
- Slic3r: open source
- PrusaSlicer: Prusa
- Simplify3D: commercial
- Materialise Magics: industrial

### Generative Design
- Topology optimization
- AI-driven: Autodesk
- Constraints: load, manufacturing
- Result: organic shapes

### Simulation
- Thermal: distortion
- Stress: residual
- Process: build simulation

## Post-Processing
### Removal
- Support: break or dissolve
- Powder: remove, recycle
- Resin: clean, post-cure

### Surface
- Sanding: smooth
- Bead blast: uniform
- Tumbling: batch
- Vapor smooth: solvent (ABS)

### Mechanical
- Machining: precision surfaces
- Heat treatment: stress relief
- HIP: hot isostatic pressing (metal)
- Sinter: binder jetting

### Coating
- Paint: aesthetic
- Plating: metal
- Anodize: aluminum
- Powder coat: durable

## Quality
### Inspection
- Visual: surface
- Dimensional: calipers, CMM
- CT scan: internal
- Ultrasonic: flaws

### Standards
- ISO/ASTM 52900: terminology
- ISO/ASTM 52901: requirements
- ISO/ASTM 52910: design
- ISO/ASTM 52915: file formats

### Process Control
- Melt pool: monitor
- Thermal: sensors
- In-situ: real-time
- Feedback: adjust

## Applications
### Aerospace
- Lightweight: brackets, ducts
- Consolidation: reduce parts
- High temp: Inconel
- GE LEAP: fuel nozzle

### Medical
- Implants: titanium, custom
- Dental: crowns, bridges
- Prosthetics: personalized
- Surgical guides

### Automotive
- Prototyping: rapid
- Tooling: jigs, fixtures
- End use: low volume
- Custom: classic parts

### Consumer
- Jewelry: custom
- Eyewear: personalized
- Toys: hobbyist
- Art: sculpture

### Construction
- Concrete: printed houses
- Metal: structural
- Hybrid: with traditional

### Food
- Chocolate: decorative
- Sugar: custom
- Pasta: shaped

## Common Pitfalls
- Wrong orientation
- Insufficient support
- Poor design for AM
- Not accounting for shrinkage
- Inadequate post-processing
- Not calibrating machine
- Ignoring thermal effects
- Material not suitable
""", "tags": ["additive manufacturing", "3D printing", "FDM", "SLA", "SLS", "DfAM", "reference"]}
    ],
}
