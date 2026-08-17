"""Engineering & Design K3 Batch 3 - 5 specialties."""

ENGINEERING_K3_BATCH3: dict[str, list[dict]] = {
    "engineering_materials_engineering": [
        {"title": "Materials Properties and Selection Reference", "content": """# Materials Properties and Selection Reference

## Crystal Structure
### Lattices
- Cubic: simple, BCC, FCC
- Hexagonal: HCP
- Unit cell: repeating unit

### Defects
- Point: vacancy, interstitial
- Line: dislocation (edge, screw)
- Area: grain boundary, stacking fault
- Volume: void, crack

### Strengthening
- Solid solution; Strain hardening; Grain refinement
- Precipitation; Dispersion

## Mechanical Properties
### Stress-Strain
- Elastic: Hooke's law; Plastic: permanent
- Yield: onset of plastic; Ultimate: max stress
- Ductile: large deformation; Brittle: little

### Properties
- Young's modulus (E): stiffness
- Yield strength; Ultimate strength; Ductility
- Toughness: energy absorbed; Hardness; Fatigue; Creep

### Testing
- Tension (ASTM E8); Compression; Impact (Charpy, Izod)
- Hardness (Brinell, Rockwell, Vickers); Fatigue (S-N); Creep

## Metals
### Steel
- Carbon 0.1-2.0%; Low alloy; High alloy (stainless, tool)
- Heat treatment: austenitize, quench, temper
- Martensite: hard, brittle; Pearlite: soft, ductile

### Aluminum
- Light (2.7 g/cm3); Corrosion resistant
- Series 1000-7000; Heat treatable: 2000, 6000, 7000

### Copper
- Conductive; Brass (Zn), Bronze (Sn); Ductile; Corrosion resistant

### Titanium
- Light (4.5), strong, corrosion resistant, biocompatible; Expensive

### Magnesium
- Lightest structural (1.7); Cast; Poor corrosion; Flammable

## Ceramics
### Traditional
- Clay, refractory, glass (amorphous)

### Advanced
- Alumina (Al2O3); Zirconia (ZrO2); SiC; Si3N4

### Properties
- Hard, brittle, high temp, electrical, chemical resistant

## Polymers
### Types
- Thermoplastic: melt and reform
- Thermoset: cross-linked, permanent
- Elastomer: rubber-like

### Thermoplastics
- PE, PP, PVC, PS, PET, ABS, PC, PMMA, Nylon, PTFE

### Thermosets
- Epoxy, Polyester, Phenolic, Polyurethane

### Properties
- Low density, low stiffness, low strength, high elongation
- Low temp softening; Creep; UV degradation

## Composites
### Components
- Matrix: binder; Reinforcement: strength; Interface: bond

### Types
- PMC: polymer matrix (most common)
- MMC: metal matrix; CMC: ceramic matrix

### Reinforcement
- Fiber (continuous, discontinuous); Particle; Flake
- Carbon fiber; Glass fiber (E, S); Aramid (Kevlar)

### Properties
- High strength/weight; High stiffness/weight
- Anisotropic; Good fatigue; Excellent corrosion

## Semiconductors
### Silicon
- Most common; Band gap 1.1 eV; Wafer
- Doping: n-type (P), p-type (B); p-n junction

### Others
- Germanium; GaAs (high speed); SiC (power); GaN (LEDs)

## Material Selection
### Ashby Method
- Performance metric; Material index; Chart; Selection

### Examples
- Light, stiff beam: E/rho
- Light, strong tie: sigma_y/rho
- Cheap, stiff panel: E/C

### Considerations
- Cost; Availability; Environmental; Aesthetics; Safety

## Common Pitfalls
- Not considering service conditions
- Ignoring corrosion
- Not accounting for fatigue
- Wrong heat treatment
- Not testing actual material
- Over-specifying tolerance
""", "tags": ["materials engineering", "metals", "ceramics", "polymers", "composites", "selection", "reference"]}
    ],
    "engineering_mechatronics": [
        {"title": "Mechatronic Systems and Integration Reference", "content": """# Mechatronic Systems and Integration Reference

## Sensors
### Position
- Potentiometer; LVDT; Encoder (optical, magnetic); Resolver; GPS

### Velocity
- Tachometer; Encoder (differentiate); Doppler

### Acceleration
- Accelerometer; MEMS; Piezoelectric

### Force
- Strain gauge; Load cell; Piezoelectric

### Temperature
- Thermocouple; RTD; Thermistor; IR

### Light
- Photodiode; Phototransistor; CCD/CMOS; Pyroelectric

### Other
- Humidity; Pressure; Flow; Proximity; Ultrasonic

## Actuators
### Electric
- DC motor; Stepper; Servo; AC motor; Linear motor; Solenoid

### Hydraulic
- Cylinder; Motor; Valve; Pump; High force

### Pneumatic
- Cylinder; Motor; Valve; Compressor; Fast, lower force

## Microcontrollers
### Architecture
- CPU; Memory (RAM, ROM, Flash); I/O; Timer; Interrupt
- Communication: UART, SPI, I2C, CAN

### Programming
- C: most common; Assembly; Arduino; Python (MicroPython)
- RTOS: FreeRTOS, Zephyr

### Common Chips
- Arduino (ATmega328): 8-bit
- ESP32: 32-bit, WiFi, Bluetooth
- STM32 (ARM Cortex): 32-bit
- RP2040: Raspberry Pi Pico

## Control Systems
### PID Controller
- P: proportional (current error)
- I: integral (accumulated error)
- D: derivative (rate of change)
- Tuning: Ziegler-Nichols, manual
- Anti-windup; Derivative filter

### Digital Control
- Sample; Quantize; Z-transform; Stability
- Sampling rate: Nyquist

### Implementation
- PWM: motor speed; H-bridge: direction
- Encoder: feedback; PID: algorithm

## Robotics
### Kinematics
- Forward: joint angles to position
- Inverse: position to joint angles
- DH parameters; Jacobian

### Dynamics
- Newton-Euler; Lagrangian; Manipulator equation

### Control
- Position; Trajectory; Force; Compliance

### Mobile Robots
- Differential drive; Ackermann; Omnidirectional (mecanum)
- Localization; Mapping; SLAM

## Integration
### V-model
- Requirements; Design; Implementation; Testing; Integration; Validation

### Challenges
- Interface; Timing; Noise; Power; Thermal; EMC

### Design Principles
- Modular; Hierarchical; Robust; Redundant; Fail-safe

## Programming Patterns
### State Machine
- States; Transitions; Events; Actions

### Interrupts
- Hardware; Timer; ISR; Priority

### Tasks
- Periodic; Event-driven; Priority; Scheduling (RTOS)

## Common Pitfalls
- Not debouncing switches
- Ignoring noise and interference
- Poor grounding
- Not considering timing
- Over-complicated design
- Not testing integration
- Ignoring power requirements
""", "tags": ["mechatronics", "sensors", "actuators", "microcontrollers", "robotics", "reference"]}
    ],
    "engineering_mining_engineering": [
        {"title": "Mining Methods and Safety Reference", "content": """# Mining Methods and Safety Reference

## Exploration
### Methods
- Geological mapping; Geochemical; Geophysical
- Drilling (core, rotary); Remote sensing

### Drilling
- Diamond: core sample; Reverse circulation: chips
- Borehole logging

### Resource Estimation
- Inferred: low confidence; Indicated: reasonable; Measured: high
- Reserve: Proven, Probable

## Surface Mining
### Open Pit
- Benches; Haul roads; Pit slope; Stripping ratio
- Drill, blast, load (shovels), haul (trucks)

### Strip Mining
- Strip: long narrow cut; Overburden removed; Coal common

### Placer
- Alluvial deposits; Panning; Sluice; Dredging

### Quarrying
- Dimension stone; Aggregate; Shallow open pit

## Underground Mining
### Access
- Shaft: vertical; Decline: inclined; Adit: horizontal

### Methods
#### Room and Pillar
- Rooms excavated; Pillars support; Coal common; 50-70% recovery

#### Longwall
- Long face, shearer; Hydraulic supports; Collapse behind
- High recovery; Efficient

#### Cut and Fill
- Excavate slice; Fill with waste or paste; Steep veins

#### Sublevel Caving
- Sublevels; Blast ring; Cave ore; Large ore bodies

#### Block Caving
- Undercut large block; Cave by gravity; Drawpoints; Low cost

#### Shrinkage Stoping
- Broken ore supports walls; Draw from bottom; Steep veins

## Rock Mechanics
### Stress
- In-situ; Virgin; Induced; Vertical (gravity); Horizontal (tectonic)

### Rock Properties
- Strength (compressive, tensile); Deformation; Discontinuities; Weathering

### Support
- Rock bolt; Shotcrete; Mesh; Steel sets; Timber

### Ground Control
- Pillar design; Roof span; Slope stability; Subsidence

## Mine Ventilation
### Purpose
- Air quality (oxygen); Dilute gases, dust; Temperature; Humidity

### System
- Intake; Working face; Return; Fan

### Gases
- Methane (explosive); CO (toxic); CO2 (asphyxiant); NO2; H2S

### Monitoring
- Sensors; Alarms; Emergency evacuation

## Blasting
### Explosives
- ANFO; Emulsion; Slurry; Dynamite

### Process
1. Drill; 2. Load; 3. Stem; 4. Connect; 5. Detonate

### Design
- Burden; Spacing; Hole depth; Sub-drill; Powder factor

## Mineral Processing
### Comminution
- Crushing (coarse); Grinding (fine); Liberation

### Separation
- Screening; Classification (hydrocyclone); Gravity
- Flotation (surface chemistry); Magnetic; Leaching

### Dewatering
- Thickening; Filtration; Tailings disposal

## Safety
### Hazards
- Ground fall; Explosions; Fire; Inundation; Equipment; Noise; Dust

### Regulations (US)
- MSHA; 30 CFR; Inspections; Training

### Best Practices
- Training; Equipment maintenance; Ventilation
- Ground control; Emergency preparedness

## Environmental
### Impacts
- Land disturbance; Water contamination; Air; Noise; Subsidence

### Reclamation
- Contouring; Soil replacement; Vegetation; Water treatment; Monitoring

## Common Pitfalls
- Inadequate geotechnical investigation
- Poor ventilation design
- Not monitoring ground conditions
- Inadequate training
- Not planning for closure
- Ignoring environmental impacts
""", "tags": ["mining engineering", "surface mining", "underground", "rock mechanics", "safety", "reference"]}
    ],
    "engineering_nuclear_engineering": [
        {"title": "Reactor Design and Radiation Protection Reference", "content": """# Reactor Design and Radiation Protection Reference

## Nuclear Physics
### Atomic Structure
- Nucleus: protons + neutrons; Electron orbits
- Isotope: same protons, different neutrons

### Binding Energy
- Mass defect: E = mc^2
- Fission: heavy to light; Fusion: light to heavy

### Radioactive Decay
- Alpha (He nucleus); Beta (electron/positron); Gamma; Neutron
- Half-life: t_1/2 = ln(2)/lambda
- Activity: A = lambda*N

### Cross Section
- Probability of interaction; Barns (10^-24 cm^2)
- Absorption, scattering, fission

## Reactor Theory
### Chain Reaction
- Fission releases neutrons; Cause more fission
- Critical: k=1; Subcritical: k<1; Supercritical: k>1

### Neutron Life Cycle
1. Fast fission; 2. Resonance escape; 3. Thermal utilization
4. Thermal fission; 5. Reproduction

### Six-Factor Formula
- k_eff = eta * f * p * epsilon * P_FNL * P_TNL

### Reactivity
- rho = (k_eff - 1)/k_eff
- Dollar: reactivity/beta; Beta: delayed neutron fraction

## Reactor Types
### PWR (Pressurized Water Reactor)
- Water coolant and moderator; Pressurized (no boiling)
- Two loops; Steam generator; Most common

### BWR (Boiling Water Reactor)
- Water coolant and moderator; Boils in core
- Direct cycle; Simpler than PWR

### CANDU (Heavy Water)
- Heavy water moderator; Natural uranium; Pressure tubes

### Gas-Cooled
- Graphite moderator; CO2 or He coolant; High temperature

### Fast Breeder
- No moderator; Breeds more fuel; Liquid metal (sodium)

### SMR (Small Modular Reactor)
- < 300 MWe; Modular; Scalable; Passive safety

## Reactor Safety
### Defense in Depth
1. Prevention; 2. Detection; 3. Control; 4. Accident management; 5. Emergency

### Safety Systems
- Control rods (shutdown); ECCS (cooling); Containment
- Passive (natural forces); Active (powered)

### Decay Heat
- After shutdown: ~7% of full power; Decreases over time
- Cooling required; Fukushima: loss of cooling

### Accidents
- Three Mile Island (1979); Chernobyl (1986); Fukushima (2011)

## Radiation Protection
### Quantities
- Absorbed dose: gray (Gy)
- Equivalent dose: sievert (Sv)
- Effective dose: sievert (Sv)

### Limits (ICRP)
- Occupational: 20 mSv/year
- Public: 1 mSv/year

### Principles
- Justification: benefit > risk
- Optimization: ALARA
- Limitation: dose limits

### ALARA
- Time: minimize exposure
- Distance: maximize from source
- Shielding: absorb radiation

### Shielding
- Alpha: paper; Beta: plastic/aluminum
- Gamma: lead/concrete; Neutron: hydrogen (water, plastic)

### Monitoring
- Personal dosimeter; Area monitors; Survey; Bioassay

## Fuel Cycle
### Front End
- Mining; Milling (yellowcake); Conversion (UF6)
- Enrichment (U-235 to 3-5%); Fabrication (assemblies)

### Back End
- Storage (spent fuel pools); Reprocessing; Waste; Disposal

### Waste
- High level (spent fuel); Intermediate; Low level
- Long half-life for high level; Geological disposal

## Common Pitfalls
- Underestimating decay heat
- Not considering human factors
- Poor safety culture
- Inadequate emergency planning
- Not maintaining containment
- Ignoring long-term waste
""", "tags": ["nuclear engineering", "reactors", "fission", "radiation", "safety", "fuel cycle", "reference"]}
    ],
    "engineering_petroleum_engineering": [
        {"title": "Reservoir Engineering and Drilling Reference", "content": """# Reservoir Engineering and Drilling Reference

## Petroleum Geology
### Origin
- Organic matter buried; Heat and pressure transform
- Kerogen intermediate; Oil window 60-150C; Gas window >150C

### Traps
- Structural (folds, faults); Stratigraphic (facies change)
- Combination; Seal (impermeable cap); Source rock; Reservoir rock

### Properties
- Porosity: void fraction; Permeability: flow capacity (Darcy)
- Saturation: fluid fractions; Wettability

## Reservoir Engineering
### Fluids
- Oil, gas, water; PVT analysis
- API gravity (higher = lighter); Viscosity

### Drive Mechanisms
- Water drive (aquifer); Gas cap (expansion)
- Solution gas (dissolved); Gravity; Combination

### Recovery
- Primary: natural drive
- Secondary: waterflood, gas injection
- Tertiary (EOR): thermal (steam), chemical, miscible (CO2)
- Recovery factor: % of OOIP

### Material Balance
- OOIP; Production; Pressure decline; Influx

### Reservoir Simulation
- Grid cells; Properties; Flow equations; History match; Forecast

## Drilling
### Rig Types
- Land; Offshore (jack-up, semi-submersible, drillship)
- Directional

### Process
1. Spud; 2. Drill (rotate, circulate); 3. Casing; 4. Cement; 5. Complete

### Drill String
- Bit; Drill pipe; Collars; BHA

### Mud
- Functions: cool, lubricate, carry cuttings, pressure control
- Water-based; Oil-based; Synthetic

### Directional Drilling
- Vertical; Deviated; Horizontal; Multilateral
- LWD: logging while drilling

### Casing
- Conductor; Surface; Intermediate; Production

### Cementing
- Primary (seal); Squeeze (repair); Plug (abandon)

## Well Completion
### Types
- Open hole; Perforated; Gravel pack; Fracture

### Stimulation
- Hydraulic fracturing: create fractures
- Acidizing: dissolve rock
- Proppant: keep fractures open
- Horizontal: multi-stage

### Artificial Lift
- Rod pump (beam); Gas lift; ESP; PCP

## Production
### Flow
- Natural (reservoir pressure); Artificial (lift)
- Surface separation; Processing; Transport

### Separation
- Three-phase: oil, gas, water
- Separator vessel; Free water knock out

### Processing
- Stabilization; Sweetening (remove H2S); Dehydration; NGL

### Facilities
- Wellhead; Manifold; Separator; Storage; Export

## Offshore
### Platforms
- Fixed; Compliant; TLP; Spar; Semi-submersible; FPSO

### Challenges
- Water depth (pressure); Environment (waves, wind)
- Corrosion (saltwater); Logistics; Safety

## Environmental
### Impacts
- Spills; Emissions (CO2, methane); Produced water; Land; Noise

### Mitigation
- Blowout preventer; Spill response; Flaring reduction
- Venting minimization; Decommission (plug and abandon)

## Common Pitfalls
- Poor reservoir characterization
- Underestimating water production
- Inadequate well design
- Not planning for decline
- Ignoring environmental
- Not maintaining equipment
""", "tags": ["petroleum engineering", "reservoir", "drilling", "completion", "production", "reference"]}
    ],
}
