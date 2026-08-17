"""Engineering & Design K1 - 27 specialties in 5 batches (6+6+5+5+5)."""

ENGINEERING_K1_BATCH1: dict[str, list[dict]] = {
    "engineering_mechanical_engineering": [
        {"title": "Mechanical Engineering - Field Overview", "content": """# Mechanical Engineering

## Definition
Mechanical engineering applies physics, mathematics, and materials science to design, analyze, manufacture, and maintain mechanical systems.

## Core Areas
- Mechanics: statics, dynamics, strength of materials
- Thermodynamics: heat and energy
- Fluid mechanics: liquids and gases
- Materials: properties and selection
- Machine design: components and systems
- Manufacturing: processes
- Control systems: automation
- Mechatronics: mechanical + electronic

## Key Concepts
- Force: push or pull
- Stress: force per area
- Strain: deformation
- Torque: rotational force
- Energy: capacity to do work
- Power: energy per time
- Efficiency: output / input
- Friction: resistance to motion

## Foundational Texts
- Shigley, "Mechanical Engineering Design"
- Hibbeler, "Mechanics of Materials"
- Callister, "Materials Science and Engineering"

## Authority Note
Advisory. ASME is professional society; PE licensure for practice.""", "tags": ["mechanical engineering", "mechanics", "thermodynamics", "design", "overview"]}
    ],
    "engineering_civil_engineering": [
        {"title": "Civil Engineering - Field Overview", "content": """# Civil Engineering

## Definition
Civil engineering deals with the design, construction, and maintenance of the physical and naturally built environment.

## Core Areas
- Structural: buildings, bridges
- Transportation: roads, highways, airports
- Geotechnical: soil and foundations
- Environmental: water, waste
- Water resources: dams, irrigation
- Construction: project management
- Surveying: measurement

## Key Concepts
- Load: force on structure
- Stress: internal force per area
- Bearing capacity: soil support
- Settlement: vertical movement
- Compaction: soil density
- Drainage: water management
- Pavement: road surface

## Foundational Texts
- Nilson et al., "Design of Concrete Structures"
- Das, "Principles of Geotechnical Engineering"
- Wright & Paquette, "Highway Engineering"

## Authority Note
Advisory. ASCE is professional society; PE licensure required; codes authoritative.""", "tags": ["civil engineering", "structures", "transportation", "geotechnical", "overview"]}
    ],
    "engineering_structural_engineering": [
        {"title": "Structural Engineering - Field Overview", "content": """# Structural Engineering

## Definition
Structural engineering is a subfield of civil engineering focused on the structural design and analysis of buildings, bridges, and other structures.

## Core Areas
- Building design: steel, concrete, wood
- Bridge design: various types
- Analysis: loads, stresses, deflections
- Seismic design: earthquake resistance
- Wind design: lateral loads
- Forensics: failure analysis
- Retrofit: strengthening existing

## Key Concepts
- Dead load: permanent weight
- Live load: variable occupancy
- Lateral load: wind, seismic
- Moment: bending force
- Shear: sliding force
- Axial: along member
- Deflection: bending
- Buckling: column failure

## Foundational Texts
- Segui, "Steel Design"
- McCormac & Brown, "Design of Reinforced Concrete"
- Breyer et al., "Design of Wood Structures"

## Authority Note
Advisory. IBC, ASCE 7, AISC, ACI codes are authoritative; PE required.""", "tags": ["structural engineering", "steel", "concrete", "loads", "overview"]}
    ],
    "engineering_electrical_engineering": [
        {"title": "Electrical Engineering - Field Overview", "content": """# Electrical Engineering

## Definition
Electrical engineering deals with the study and application of electricity, electronics, and electromagnetism.

## Core Areas
- Power: generation, transmission, distribution
- Electronics: circuits, devices
- Control systems: automation
- Signal processing: analysis
- Telecommunications: communication
- Computers: hardware
- Instrumentation: measurement

## Key Concepts
- Voltage: electrical potential
- Current: flow of charge
- Resistance: opposition to current
- Power: V x I
- Inductance: magnetic storage
- Capacitance: electric storage
- Impedance: AC resistance
- Frequency: cycles per second

## Foundational Texts
- Hayt et al., "Engineering Circuit Analysis"
- Nilsson & Riedel, "Electric Circuits"
- Sedra & Smith, "Microelectronic Circuits"

## Authority Note
Advisory. IEEE is professional society; PE licensure for power work.""", "tags": ["electrical engineering", "circuits", "power", "electronics", "overview"]}
    ],
    "engineering_electronic_engineering": [
        {"title": "Electronic Engineering - Field Overview", "content": """# Electronic Engineering

## Definition
Electronic engineering deals with electronic circuits, devices, and systems, including microelectronics and telecommunications.

## Core Areas
- Analog circuits: continuous signals
- Digital circuits: discrete signals
- Microelectronics: integrated circuits
- Embedded systems: microcontrollers
- Telecommunications: wireless, wired
- Signal processing: filtering, compression
- RF: radio frequency

## Key Concepts
- Transistor: amplifier, switch
- Diode: one-way current
- Op-amp: operational amplifier
- Logic gate: AND, OR, NOT
- Flip-flop: memory element
- Microcontroller: computer on chip
- ADC/DAC: analog-digital conversion
- Modulation: AM, FM, digital

## Foundational Texts
- Sedra & Smith, "Microelectronic Circuits"
- Razavi, "Design of Analog CMOS Integrated Circuits"
- Mano & Ciletti, "Digital Design"

## Authority Note
Advisory. IEEE standards; technology evolves rapidly.""", "tags": ["electronic engineering", "circuits", "microelectronics", "embedded", "overview"]}
    ],
    "engineering_chemical_engineering": [
        {"title": "Chemical Engineering - Field Overview", "content": """# Chemical Engineering

## Definition
Chemical engineering applies chemistry, physics, and mathematics to design processes that convert raw materials into useful products.

## Core Areas
- Process design: plant layout
- Reaction engineering: chemical reactors
- Separation processes: distillation, filtration
- Transport phenomena: heat, mass, momentum
- Thermodynamics: energy in reactions
- Process control: automation
- Safety: hazard management

## Key Concepts
- Mass balance: conservation of mass
- Energy balance: conservation of energy
- Reaction rate: speed of reaction
- Conversion: reactant to product
- Yield: product obtained
- Selectivity: desired vs undesired
- Equilibrium: balance state

## Foundational Texts
- Felder & Rousseau, "Elementary Principles of Chemical Processes"
- McCabe et al., "Unit Operations of Chemical Engineering"
- Fogler, "Elements of Chemical Reaction Engineering"

## Authority Note
Advisory. AIChE is professional society; PE licensure; safety critical.""", "tags": ["chemical engineering", "processes", "reactions", "separations", "overview"]}
    ],
}

ENGINEERING_K1_BATCH2: dict[str, list[dict]] = {
    "engineering_aerospace_engineering": [
        {"title": "Aerospace Engineering - Field Overview", "content": """# Aerospace Engineering

## Definition
Aerospace engineering deals with the design, development, and testing of aircraft and spacecraft.

## Core Areas
- Aerodynamics: air flow
- Propulsion: engines, rockets
- Structures: airframe, fuselage
- Flight mechanics: stability, control
- Avionics: electronics
- Orbital mechanics: satellite paths
- Systems: integration

## Key Concepts
- Lift: upward force
- Drag: resistance
- Thrust: forward force
- Weight: gravity force
- Mach number: speed / sound speed
- Reynolds number: flow regime
- Specific impulse: rocket efficiency
- Delta-V: change in velocity

## Foundational Texts
- Anderson, "Fundamentals of Aerodynamics"
- Sutton & Biblarz, "Rocket Propulsion Elements"
- Nelson, "Flight Stability and Automatic Control"

## Authority Note
Advisory. AIAA is professional society; FAA regulates; safety critical.""", "tags": ["aerospace engineering", "aerodynamics", "propulsion", "flight", "overview"]}
    ],
    "engineering_automotive_engineering": [
        {"title": "Automotive Engineering - Field Overview", "content": """# Automotive Engineering

## Definition
Automotive engineering is the design, development, manufacture, and testing of vehicles, including cars, trucks, and motorcycles.

## Core Areas
- Engine design: combustion, electric
- Powertrain: transmission, drivetrain
- Chassis: frame, suspension
- Body: exterior, aerodynamics
- Safety: crash, active, passive
- Emissions: pollution control
- Autonomous: self-driving
- Electric vehicles: batteries, motors

## Key Concepts
- Horsepower: engine power
- Torque: rotational force
- Fuel efficiency: mpg, L/100km
- Emissions: CO2, NOx, particulates
- Crashworthiness: occupant protection
- NVH: noise, vibration, harshness
- Drivetrain: power transmission
- Suspension: ride, handling

## Foundational Texts
- Bosch, "Automotive Handbook"
- Heywood, "Internal Combustion Engine Fundamentals"
- Gillespie, "Fundamentals of Vehicle Dynamics"

## Authority Note
Advisory. SAE standards; NHTSA regulates safety; EPA emissions.""", "tags": ["automotive engineering", "engines", "powertrain", "safety", "overview"]}
    ],
    "engineering_biomedical_engineering": [
        {"title": "Biomedical Engineering - Field Overview", "content": """# Biomedical Engineering

## Definition
Biomedical engineering applies engineering principles to medicine and biology for healthcare purposes.

## Core Areas
- Medical devices: instruments, implants
- Biomaterials: compatible materials
- Biomechanics: body mechanics
- Medical imaging: MRI, CT, ultrasound
- Tissue engineering: grow tissues
- Prosthetics: artificial limbs
- Rehabilitation: assistive technology
- Physiological modeling: simulation

## Key Concepts
- Biocompatibility: not harmful to body
- Implant: inserted device
- Prosthesis: replacement
- Imaging: visualizing inside body
- Biosensor: biological measurement
- Tissue scaffold: support structure
- In vivo: in living
- In vitro: in glass

## Foundational Texts
- Enderle & Bronzino, "Introduction to Biomedical Engineering"
- Ratner et al., "Biomaterials Science"
- Saltzman, "Tissue Engineering"

## Authority Note
Advisory. FDA regulates devices; AIMBE professional; ethics critical.""", "tags": ["biomedical engineering", "medical devices", "biomaterials", "imaging", "overview"]}
    ],
    "engineering_environmental_engineering": [
        {"title": "Environmental Engineering - Field Overview", "content": """# Environmental Engineering

## Definition
Environmental engineering applies engineering to protect human health and the environment: water, air, waste.

## Core Areas
- Water treatment: drinking water
- Wastewater: sewage treatment
- Air pollution: control
- Solid waste: management
- Hazardous waste: remediation
- Environmental impact: assessment
- Sustainability: green engineering

## Key Concepts
- BOD: biochemical oxygen demand
- COD: chemical oxygen demand
- TSS: total suspended solids
- pH: acidity
- Turbidity: cloudiness
- Pathogen: disease-causing
- Contaminant: unwanted substance
- Remediation: cleanup

## Foundational Texts
- Davis & Masten, "Principles of Environmental Engineering and Science"
- Mihelcic & Zimmerman, "Environmental Engineering"
- Peavy et al., "Environmental Engineering"

## Authority Note
Advisory. EPA regulations; AAEES professional; standards authoritative.""", "tags": ["environmental engineering", "water", "waste", "pollution", "overview"]}
    ],
    "engineering_industrial_engineering": [
        {"title": "Industrial Engineering - Field Overview", "content": """# Industrial Engineering

## Definition
Industrial engineering optimizes complex systems, processes, and organizations by integrating people, materials, equipment, and information.

## Core Areas
- Operations research: optimization
- Production planning: scheduling
- Quality control: statistics
- Ergonomics: human factors
- Supply chain: logistics
- Facilities layout: arrangement
- Work measurement: time studies
- Simulation: modeling

## Key Concepts
- Throughput: rate of production
- Bottleneck: slowest process
- Cycle time: time per unit
- Utilization: actual / capacity
- Efficiency: output / input
- Optimization: best solution
- Queue: waiting line
- Lean: waste reduction

## Foundational Texts
- Nahmias & Olsen, "Production and Operations Analysis"
- Groover, "Automation, Production Systems, and Computer-Integrated Manufacturing"
- Hillier & Lieberman, "Introduction to Operations Research"

## Authority Note
Advisory. IISE is professional society; methods are established.""", "tags": ["industrial engineering", "operations research", "optimization", "ergonomics", "overview"]}
    ],
    "engineering_manufacturing_engineering": [
        {"title": "Manufacturing Engineering - Field Overview", "content": """# Manufacturing Engineering

## Definition
Manufacturing engineering is the design and operation of manufacturing processes and systems to produce goods.

## Core Areas
- Machining: cutting, milling
- Forming: shaping metal
- Casting: pouring liquid
- Joining: welding, fastening
- Additive: 3D printing
- Assembly: putting together
- Automation: robotics
- Quality: inspection, control

## Key Concepts
- Tolerance: allowable variation
- Surface finish: smoothness
- Tool wear: degradation
- Feed rate: material input
- Cutting speed: tool speed
- Batch: production quantity
- Yield: good units / total
- Scrap: waste material

## Foundational Texts
- Groover, "Fundamentals of Modern Manufacturing"
- Kalpakjian & Schmid, "Manufacturing Engineering and Technology"
- DeGarmo et al., "Materials and Processes in Manufacturing"

## Authority Note
Advisory. SME professional; ISO standards; quality systems matter.""", "tags": ["manufacturing engineering", "machining", "casting", "quality", "overview"]}
    ],
}

ENGINEERING_K1_BATCH3: dict[str, list[dict]] = {
    "engineering_materials_engineering": [
        {"title": "Materials Engineering - Field Overview", "content": """# Materials Engineering

## Definition
Materials engineering studies the properties, design, and application of materials: metals, ceramics, polymers, composites, semiconductors.

## Core Areas
- Metals: steel, aluminum, titanium
- Ceramics: traditional, advanced
- Polymers: plastics, elastomers
- Composites: fiber-reinforced
- Semiconductors: silicon, electronics
- Biomaterials: medical
- Nanomaterials: nano-scale

## Key Concepts
- Crystal structure: atomic arrangement
- Grain: crystal region
- Phase: homogeneous state
- Alloy: metal mixture
- Stress: force per area
- Strain: deformation
- Elastic: returns to shape
- Plastic: permanent deformation
- Hardness: resistance to indentation
- Toughness: energy absorption

## Foundational Texts
- Callister & Rethwisch, "Materials Science and Engineering"
- Shackelford, "Introduction to Materials Science for Engineers"
- Askeland & Wright, "The Science and Engineering of Materials"

## Authority Note
Advisory. ASM International professional; materials data critical.""", "tags": ["materials engineering", "metals", "polymers", "composites", "overview"]}
    ],
    "engineering_mechatronics": [
        {"title": "Mechatronics - Field Overview", "content": """# Mechatronics

## Definition
Mechatronics is the synergistic integration of mechanical, electrical, electronic, and computer engineering to create intelligent systems.

## Core Areas
- Mechanical: structure, mechanisms
- Electronics: circuits, sensors
- Control: feedback systems
- Computing: microcontrollers, software
- Robotics: autonomous systems
- Automation: industrial
- Embedded systems: integrated

## Key Concepts
- Sensor: measures physical quantity
- Actuator: creates motion
- Microcontroller: small computer
- Feedback: output affects input
- PID: proportional-integral-derivative
- H-bridge: motor driver
- PWM: pulse width modulation
- Real-time: deterministic timing

## Foundational Texts
- Bolton, "Mechatronics: Electronic Control Systems in Mechanical Engineering"
- Alciatore & Histand, "Introduction to Mechatronics and Measurement Systems"
- Bishop, "The Mechatronics Handbook"

## Authority Note
Advisory. Mechatronics is interdisciplinary; IEEE and ASME relevant.""", "tags": ["mechatronics", "sensors", "actuators", "control", "overview"]}
    ],
    "engineering_mining_engineering": [
        {"title": "Mining Engineering - Field Overview", "content": """# Mining Engineering

## Definition
Mining engineering is the practice of extracting minerals from the earth safely, efficiently, and responsibly.

## Core Areas
- Exploration: finding deposits
- Surface mining: open pit, strip
- Underground mining: shafts, tunnels
- Mineral processing: beneficiation
- Mine ventilation: air quality
- Rock mechanics: stability
- Environmental: reclamation
- Safety: hazard management

## Key Concepts
- Ore: valuable mineral
- Grade: concentration
- Overburden: material above
- Tailings: waste residue
- Extraction: removing ore
- Benching: stepped excavation
- Pillar: support structure
- Reclamation: restoring land

## Foundational Texts
- Hartman, "Introductory Mining Engineering"
- Hustrulid et al., "Open Pit Mine Planning and Design"
- Darling, "SME Mining Engineering Handbook"

## Authority Note
Advisory. SME professional; MSHA regulates safety; environmental critical.""", "tags": ["mining engineering", "extraction", "mineral processing", "safety", "overview"]}
    ],
    "engineering_nuclear_engineering": [
        {"title": "Nuclear Engineering - Field Overview", "content": """# Nuclear Engineering

## Definition
Nuclear engineering deals with the application of nuclear and radiation processes: power, medicine, research.

## Core Areas
- Reactor design: fission plants
- Nuclear fuels: uranium, plutonium
- Radiation protection: shielding
- Nuclear materials: behavior
- Thermal hydraulics: cooling
- Reactor safety: accident prevention
- Nuclear medicine: imaging, therapy
- Fusion: future energy

## Key Concepts
- Fission: splitting nucleus
- Fusion: combining nuclei
- Criticality: sustained chain reaction
- Half-life: decay time
- Radiation: alpha, beta, gamma, neutron
- Dosimetry: radiation measurement
- Containment: prevent release
- Decay heat: post-shutdown heat

## Foundational Texts
- Lamarsh & Baratta, "Introduction to Nuclear Engineering"
- Duderstadt & Hamilton, "Nuclear Reactor Analysis"
- Shultis & Faw, "Fundamentals of Nuclear Science and Engineering"

## Authority Note
Advisory. ANS professional; NRC regulates; safety paramount.""", "tags": ["nuclear engineering", "reactors", "fission", "radiation", "overview"]}
    ],
    "engineering_petroleum_engineering": [
        {"title": "Petroleum Engineering - Field Overview", "content": """# Petroleum Engineering

## Definition
Petroleum engineering is the practice of finding, extracting, and producing oil and gas resources.

## Core Areas
- Exploration: finding reservoirs
- Drilling: well construction
- Reservoir engineering: flow modeling
- Production: extracting hydrocarbons
- Well completion: finishing well
- Enhanced recovery: improving yield
- Refining: processing crude
- Offshore: marine operations

## Key Concepts
- Reservoir: underground formation
- Porosity: void space
- Permeability: flow capacity
- Pressure: drive mechanism
- Viscosity: fluid resistance
- API gravity: oil density
- Recovery factor: % extracted
- Waterflood: injection for pressure

## Foundational Texts
- Lyons & Plisga, "Standard Handbook of Petroleum and Natural Gas Engineering"
- Ahmed, "Reservoir Engineering Handbook"
- Bourgoyne et al., "Applied Drilling Engineering"

## Authority Note
Advisory. SPE professional; regulations vary; environmental concerns.""", "tags": ["petroleum engineering", "drilling", "reservoir", "production", "overview"]}
    ],
}

ENGINEERING_K1_BATCH4: dict[str, list[dict]] = {
    "engineering_power_energy_systems": [
        {"title": "Power and Energy Systems - Field Overview", "content": """# Power and Energy Systems

## Definition
Power and energy engineering deals with the generation, transmission, distribution, and use of electric power.

## Core Areas
- Generation: power plants
- Transmission: high-voltage lines
- Distribution: local delivery
- Renewable: solar, wind, hydro
- Energy storage: batteries, pumped hydro
- Smart grid: intelligent network
- Power electronics: conversion
- Load forecasting: demand prediction

## Key Concepts
- Voltage: electrical potential
- Current: flow of charge
- Power: V x I (watts)
- Three-phase: AC system
- Frequency: 50 or 60 Hz
- Transformer: voltage conversion
- Grid: interconnected system
- Capacity: maximum output
- Load: demand
- Intermittency: variable output (renewables)

## Foundational Texts
- Chapman, "Electric Machinery Fundamentals"
- Glover et al., "Power System Analysis and Design"
- Masters, "Renewable and Efficient Electric Power Systems"

## Authority Note
Advisory. IEEE standards; NERC reliability; regulations vary.""", "tags": ["power engineering", "energy", "grid", "renewable", "overview"]}
    ],
    "engineering_controls_automation": [
        {"title": "Controls and Automation - Field Overview", "content": """# Controls and Automation

## Definition
Control engineering deals with the design of systems that automatically regulate processes. Automation applies control to operate without human intervention.

## Core Areas
- Classical control: transfer functions
- Modern control: state-space
- Digital control: discrete-time
- Nonlinear control: complex dynamics
- Adaptive control: changing systems
- Process control: industrial
- Robotics: motion control
- SCADA: supervisory systems

## Key Concepts
- Feedback: output affects input
- Open loop: no feedback
- Closed loop: with feedback
- Setpoint: desired value
- Error: difference from setpoint
- Stability: returns to equilibrium
- PID: proportional-integral-derivative
- Transfer function: input-output relationship
- Bode plot: frequency response

## Foundational Texts
- Ogata, "Modern Control Engineering"
- Franklin et al., "Feedback Control of Dynamic Systems"
- Astrom & Murray, "Feedback Systems"

## Authority Note
Advisory. ISA professional; IEEE standards; safety critical.""", "tags": ["control engineering", "automation", "feedback", "PID", "overview"]}
    ],
    "engineering_acoustical_engineering": [
        {"title": "Acoustical Engineering - Field Overview", "content": """# Acoustical Engineering

## Definition
Acoustical engineering deals with sound and vibration: generation, propagation, control, and effects.

## Core Areas
- Architectural acoustics: room sound
- Noise control: reduction
- Audio engineering: recording, reproduction
- Ultrasonics: high frequency
- Underwater acoustics: sonar
- Musical acoustics: instruments
- Vibration: mechanical oscillation
- Psychoacoustics: perception

## Key Concepts
- Frequency: pitch (Hz)
- Amplitude: loudness (dB)
- Wavelength: speed/frequency
- Decibel: logarithmic scale
- Reverberation: sound persistence
- Absorption: sound reduction
- Reflection: bouncing
- Diffraction: bending
- Resonance: natural frequency

## Foundational Texts
- Kinsler et al., "Fundamentals of Acoustics"
- Beranek, "Acoustics"
- Long, "Architectural Acoustics"

## Authority Note
Advisory. ASA professional; standards for noise; OSHA regulates.""", "tags": ["acoustical engineering", "sound", "noise control", "vibration", "overview"]}
    ],
    "engineering_marine_naval_engineering": [
        {"title": "Marine and Naval Engineering - Field Overview", "content": """# Marine and Naval Engineering

## Definition
Marine and naval engineering deals with the design, construction, and operation of ships, boats, and offshore structures.

## Core Areas
- Naval architecture: hull design
- Marine engineering: propulsion, systems
- Offshore: platforms, wind
- Hydrodynamics: water flow
- Structural: ship strength
- Stability: upright tendency
- Propulsion: engines, propellers
- Marine systems: piping, HVAC

## Key Concepts
- Buoyancy: upward force
- Displacement: weight of water
- Stability: righting arm
- Freeboard: height above water
- Draft: depth below water
- Resistance: drag
- Propeller: thrust generation
- Metacentric height: stability measure

## Foundational Texts
- Rawson & Tupper, "Basic Ship Theory"
- Lewis, "Principles of Naval Architecture"
- Gillmer & Johnson, "Introduction to Naval Architecture"

## Authority Note
Advisory. SNAME professional; IMO and Coast Guard regulate; safety critical.""", "tags": ["marine engineering", "naval architecture", "ships", "hydrodynamics", "overview"]}
    ],
    "engineering_reliability_maintenance_engineering": [
        {"title": "Reliability and Maintenance Engineering - Field Overview", "content": """# Reliability and Maintenance Engineering

## Definition
Reliability engineering ensures systems perform as intended over time. Maintenance engineering keeps systems operating.

## Core Areas
- Reliability: probability of function
- Maintainability: ease of repair
- Availability: ready to use
- Failure analysis: root cause
- Predictive maintenance: condition-based
- Preventive maintenance: scheduled
- FMEA: failure mode analysis
- Risk assessment: probability x consequence

## Key Concepts
- MTBF: mean time between failures
- MTTR: mean time to repair
- Availability: MTBF / (MTBF + MTTR)
- Failure rate: failures per time
- Bathtub curve: failure over life
- Redundancy: backup
- Derating: below capacity
- Burn-in: early failure screening

## Foundational Texts
- O'Connor & Kleyner, "Practical Reliability Engineering"
- Moubray, "Reliability-Centered Maintenance"
- Ebeling, "An Introduction to Reliability and Maintainability Engineering"

## Authority Note
Advisory. ASQ and IEEE standards; safety-critical applications.""", "tags": ["reliability", "maintenance", "MTBF", "FMEA", "overview"]}
    ],
}

ENGINEERING_K1_BATCH5: dict[str, list[dict]] = {
    "engineering_safety_human_factors": [
        {"title": "Safety and Human Factors - Field Overview", "content": """# Safety and Human Factors Engineering

## Definition
Safety engineering prevents accidents and minimizes harm. Human factors engineering designs systems that work well with human capabilities and limitations.

## Core Areas
- System safety: hazard analysis
- Risk assessment: identify and evaluate
- Human factors: ergonomics, interfaces
- Cognitive engineering: mental processes
- User interface: human-computer
- Accident investigation: root cause
- Safety culture: organizational
- Regulatory compliance: standards

## Key Concepts
- Hazard: potential harm
- Risk: probability x consequence
- ALARP: as low as reasonably practicable
- Human error: unintended action
- Swiss cheese model: layered defenses
- Normalization of deviance: accepting risk
- Situational awareness: understanding
- Workload: mental demand

## Foundational Texts
- Reason, "Human Error"
- Wickens et al., "An Introduction to Human Factors Engineering"
- Roland & Moriarty, "System Safety Engineering and Management"

## Authority Note
Advisory. HFES professional; OSHA regulates; safety critical.""", "tags": ["safety engineering", "human factors", "ergonomics", "risk", "overview"]}
    ],
    "engineering_architecture": [
        {"title": "Architecture - Field Overview", "content": """# Architecture

## Definition
Architecture is the art and science of designing buildings and other physical structures.

## Core Areas
- Design: conceptual, schematic
- Technical: structure, systems
- Sustainability: green design
- Urban design: city scale
- Interior: spaces
- Landscape: outdoor
- Historic preservation: restoration
- Digital: BIM, parametric

## Key Concepts
- Form: shape and space
- Function: purpose
- Context: surroundings
- Scale: relative size
- Proportion: ratio
- Light: natural, artificial
- Material: building substance
- Circulation: movement through
- Program: requirements

## Foundational Texts
- Ching, "Architecture: Form, Space, and Order"
- Kostof, "A History of Architecture"
- Le Corbusier, "Towards a New Architecture"

## Authority Note
Advisory. AIA professional; licensure required; codes regulate.""", "tags": ["architecture", "design", "buildings", "sustainability", "overview"]}
    ],
    "engineering_urban_regional_planning": [
        {"title": "Urban and Regional Planning - Field Overview", "content": """# Urban and Regional Planning

## Definition
Urban and regional planning is the practice of designing and managing the use of land, resources, and infrastructure in cities and regions.

## Core Areas
- Land use: zoning, development
- Transportation: mobility
- Housing: affordability, supply
- Economic development: jobs, investment
- Environmental: sustainability
- Community: social needs
- Infrastructure: utilities, services
- Regional: multi-jurisdictional

## Key Concepts
- Zoning: land use regulation
- Comprehensive plan: long-term vision
- Density: units per area
- Mixed use: combined activities
- Transit-oriented: near transit
- Smart growth: compact, walkable
- Gentrification: neighborhood change
- Sprawl: low-density expansion

## Foundational Texts
- Levy, "Contemporary Urban Planning"
- Hall, "Urban and Regional Planning"
- Berke et al., "Urban Land Use Planning"

## Authority Note
Advisory. APA professional; AICP certification; local regulations.""", "tags": ["urban planning", "land use", "zoning", "transportation", "overview"]}
    ],
    "engineering_surveying_geomatics": [
        {"title": "Surveying and Geomatics - Field Overview", "content": """# Surveying and Geomatics

## Definition
Surveying is the science of measuring and mapping the earth's surface. Geomatics includes surveying plus GIS, remote sensing, and GPS.

## Core Areas
- Land surveying: property boundaries
- Topographic: terrain features
- Construction: layout, as-built
- Geodetic: earth shape
- GPS: satellite positioning
- GIS: geographic information
- Remote sensing: satellite, aerial
- Photogrammetry: photo measurement

## Key Concepts
- Datum: reference surface
- Coordinate system: location reference
- Elevation: height above datum
- Benchmark: known point
- Traverse: series of connected points
- Triangulation: angle measurement
- Accuracy: closeness to true
- Precision: repeatability

## Foundational Texts
- Ghilani & Wolf, "Elementary Surveying"
- Bannister et al., "Surveying"
- Hofmann-Wellenhof et al., "GPS: Theory and Practice"

## Authority Note
Advisory. NSPS professional; licensure for surveyors; NGS standards.""", "tags": ["surveying", "geomatics", "GPS", "GIS", "overview"]}
    ],
    "engineering_additive_manufacturing_3d_printing": [
        {"title": "Additive Manufacturing and 3D Printing - Field Overview", "content": """# Additive Manufacturing and 3D Printing

## Definition
Additive manufacturing (AM) builds objects layer by layer from digital models, contrasted with subtractive methods.

## Core Areas
- FDM: fused deposition (filament)
- SLA: stereolithography (resin)
- SLS: selective laser sintering (powder)
- MJF: multi jet fusion (powder)
- DMLS: direct metal laser sintering
- Material jetting: PolyJet
- Binder jetting: powder + binder
- Sheet lamination: layered sheets

## Key Concepts
- CAD: computer-aided design
- STL: standard tessellation language
- Slicer: converts to layers
- Layer height: resolution
- Infill: internal structure
- Support: overhang structure
- Orientation: print direction
- Post-processing: finishing

## Foundational Texts
- Gibson et al., "Additive Manufacturing Technologies"
- Noorani, "3D Printing: Technology, Engineering, and Science"
- ASTM/ISO 52900 standards

## Authority Note
Advisory. ASTM/ISO standards; technology evolving rapidly.""", "tags": ["additive manufacturing", "3D printing", "FDM", "SLA", "overview"]}
    ],
}
