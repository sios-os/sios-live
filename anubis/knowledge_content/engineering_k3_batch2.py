"""Engineering & Design K3 Batch 2 - 6 specialties."""

ENGINEERING_K3_BATCH2: dict[str, list[dict]] = {
    "engineering_aerospace_engineering": [
        {"title": "Aerodynamics and Propulsion Reference", "content": """# Aerodynamics and Propulsion Reference

## Aerodynamics
### Forces
- Lift: perpendicular to flow
- Drag: parallel to flow
- Thrust: forward; Weight: gravity

### Lift and Drag
- L = 0.5*rho*V^2*S*CL
- D = 0.5*rho*V^2*S*CD
- CD = CD0 + k*CL^2
- L/D: efficiency (max is best)

### Airfoils
- Camber, thickness, chord, angle of attack
- Stall: CL drops at high alpha

### Wings
- Aspect ratio: AR = b^2/S
- Taper, sweep, dihedral, washout

### Compressible Flow
- Mach: M = V/a
- Subsonic: M<1; Transonic: M~1; Supersonic: M>1; Hypersonic: M>5
- Shock wave: abrupt change

## Flight Mechanics
### Stability
- Static: initial tendency; Dynamic: over time
- Longitudinal: pitch; Lateral: roll; Directional: yaw

### Control
- Elevator: pitch; Aileron: roll; Rudder: yaw
- Flap: lift; Spoiler: reduce lift

### Performance
- Takeoff, climb, cruise, landing
- Range: Breguet; Endurance: loiter

## Propulsion
### Air-Breathing
- Turbojet: compressor, combustor, turbine, nozzle
- Turbofan: bypass air; High bypass: efficient
- Turboprop: turbine drives propeller

### Rocket
- Thrust: F = mdot*Ve + (Pe-P0)*Ae
- Specific impulse: Isp = F/(mdot*g)
- Solid, liquid, hybrid, electric
- Tsiolkovsky: deltaV = Ve*ln(m0/mf)
- Staging: discard mass

## Orbital Mechanics
### Kepler's Laws
1. Elliptical orbits
2. Equal areas in equal time
3. T^2 proportional to a^3

### Orbital Elements
- Semi-major axis, eccentricity, inclination
- RAAN, argument of perigee, true anomaly

### Velocity
- Circular: V = sqrt(mu/r)
- Escape: V = sqrt(2*mu/r)

### Maneuvers
- Hohmann transfer: two burns
- Plane change; Rendezvous

## Structures
### Loads
- Aerodynamic, inertial, pressurization, thermal, landing

### Materials
- Aluminum: traditional; Composites: carbon fiber
- Titanium: high temp; Steel: landing gear

## Avionics
- Navigation: GPS, INS
- Communication: radio
- Flight control: fly-by-wire
- Displays: glass cockpit

## Common Pitfalls
- Ignoring compressibility
- Not considering aeroelasticity
- Underestimating loads
- Not testing in wind tunnel
- Ignoring thermal effects
- Not considering fatigue
""", "tags": ["aerospace engineering", "aerodynamics", "propulsion", "orbital mechanics", "reference"]}
    ],
    "engineering_automotive_engineering": [
        {"title": "Vehicle Dynamics and Powertrain Reference", "content": """# Vehicle Dynamics and Powertrain Reference

## Vehicle Dynamics
### Longitudinal
- Resistances: rolling, aerodynamic, grade
- Rolling: F_r = f_r*W
- Aero: F_a = 0.5*rho*Cd*A*V^2
- Grade: F_g = W*sin(theta)
- Tractive: F_t = T_e*gear/r_tire

### Braking
- Weight transfer: load shifts
- Brake bias: front/rear
- ABS: prevent lockup
- Stopping distance: V^2/(2*a)

### Handling
- Understeer: front slides
- Oversteer: rear slides
- Slip angle; Cornering stiffness

### Ride
- Suspension: springs, dampers
- Natural frequency; Damping ratio
- Roll, pitch, heave

### Tire
- Contact patch; Vertical load
- Lateral, longitudinal force
- Friction circle: combined limits

## Powertrain
### ICE Four-Stroke
1. Intake; 2. Compression; 3. Power; 4. Exhaust

### Diesel
- Compression ignition; Higher compression; More efficient

### Parameters
- Displacement; Compression ratio; Bore x stroke
- Power: hp = torque*rpm/5252
- BSFC: brake specific fuel consumption

### Transmission
- Manual, automatic, CVT, DCT
- Gear ratio; Final drive; Differential

### Drivetrain
- FWD, RWD, AWD, 4WD
- Limited slip differential

## Electric Vehicles
### Components
- Battery, motor, inverter, controller, charger, BMS

### Battery
- Lithium-ion; Energy density (Wh/kg)
- Cycle life; SOC; SOH

### Motor Types
- BLDC, induction, PMSM, SRM

### Regenerative Braking
- Motor as generator; Recover energy

### Charging
- Level 1 (120V), Level 2 (240V), DC fast
- CCS, CHAdeMO, Tesla

## Emissions
### Pollutants
- CO, HC, NOx, PM, CO2

### Control
- Catalytic converter; EGR; DPF; SCR

### Standards
- EPA, CARB, Euro

## Safety
### Active
- ABS, ESC, TCS, AEB, LDW

### Passive
- Airbags, seatbelt, crumple zone, side impact

### Crash Testing
- NCAP, IIHS; Frontal, side, rollover

## Autonomous Driving
### Levels (SAE)
- 0: none; 1: assist; 2: partial; 3: conditional; 4: high; 5: full

### Sensors
- Camera, radar, lidar, ultrasonic, GPS, IMU

### Processing
- Perception, prediction, planning, control

## Common Pitfalls
- Ignoring weight transfer
- Not considering tire limits
- Poor suspension tuning
- Not testing safety systems
- Underestimating thermal loads
""", "tags": ["automotive engineering", "vehicle dynamics", "powertrain", "electric vehicles", "safety", "reference"]}
    ],
    "engineering_biomedical_engineering": [
        {"title": "Medical Devices and Biomaterials Reference", "content": """# Medical Devices and Biomaterials Reference

## Medical Imaging
### X-Ray
- Radiation absorption: tissue dependent
- Bone: white; Soft tissue: gray
- CT: computed tomography
- Contrast: iodine, barium

### MRI
- Magnetic field aligns protons
- RF pulse tips protons
- T1: longitudinal; T2: transverse
- Contrast: gadolinium; fMRI: functional

### Ultrasound
- Sound waves 1-20 MHz
- Piezoelectric transducer
- Doppler: blood flow
- Real-time; No radiation

### Nuclear
- PET: positron emission
- SPECT: single photon
- Radiotracer; Metabolic function

## Medical Devices
### FDA Classification
- Class I: low risk (bandages)
- Class II: moderate (infusion pumps)
- Class III: high (pacemakers)
- 510(k): substantial equivalence
- PMA: premarket approval

### Implants
- Orthopedic: hip, knee, plate
- Cardiovascular: stent, valve
- Neural: electrode; Dental; Ocular; Cochlear

### Monitoring
- ECG: heart; EEG: brain; EMG: muscle
- Pulse oximetry; Blood pressure; Glucose

### Therapeutic
- Pacemaker; Defibrillator; Insulin pump
- Dialysis; Ventilator; Infusion pump

## Biomaterials
### Requirements
- Biocompatible, non-toxic, non-carcinogenic
- Sterilizable, mechanically appropriate, durable

### Metals
- Stainless steel: strength
- Titanium: biocompatible, light
- Cobalt-chrome: wear resistant
- Nitinol: shape memory

### Polymers
- PMMA: bone cement
- PTFE (Teflon): low friction
- Polyethylene: joint surfaces
- Silicone: flexible; PLA: biodegradable; PEEK: structural

### Ceramics
- Alumina: wear resistant
- Zirconia: strong
- Hydroxyapatite: bone-like
- Bioglass: bone bonding

### Composites
- Carbon fiber: strength

### Surface
- Roughness; Coating; Porous; Drug-eluting

## Tissue Engineering
### Components
- Cells, scaffold, growth factors, bioreactor

### Process
1. Harvest cells; 2. Culture; 3. Seed on scaffold
4. Incubate; 5. Implant

### Challenges
- Vascularization; Scale; Immune rejection; Integration

## Biomechanics
### Bone
- Cortical: dense; Trabecular: spongy
- Anisotropic; Remodeling (Wolff's law)

### Soft Tissue
- Ligament, tendon, cartilage, skin
- Viscoelastic; Nonlinear

### Joints
- Synovial; Articular cartilage; Synovial fluid

## Prosthetics
### Upper Limb
- Body-powered; Myoelectric; Cosmetic

### Lower Limb
- Passive; Microprocessor; Active (powered)

## Regulatory
### FDA
- IDE: investigational; IRB: review
- Clinical trial; 510(k); PMA; Post-market

### ISO 13485
- Quality management for medical devices
- Risk management; Design controls

## Common Pitfalls
- Not testing biocompatibility
- Ignoring sterilization effects
- Underestimating fatigue
- Not considering immune response
- Poor surface finish
- Not following regulations
""", "tags": ["biomedical engineering", "medical devices", "biomaterials", "imaging", "tissue engineering", "reference"]}
    ],
    "engineering_environmental_engineering": [
        {"title": "Water Treatment and Pollution Control Reference", "content": """# Water Treatment and Pollution Control Reference

## Water Treatment
### Sources
- Surface (rivers, lakes); Groundwater; Rain; Reclaimed

### Process
1. Coagulation; 2. Flocculation; 3. Sedimentation
4. Filtration; 5. Disinfection; 6. Fluoridation; 7. Distribution

### Coagulation
- Chemicals: alum, ferric chloride
- Destabilize particles; Coagulant aid: polymers

### Filtration
- Sand; Dual media; Mixed media; Membrane

### Disinfection
- Chlorine: most common; Chloramine; Ozone; UV
- CT value: concentration x time

### Standards
- EPA Safe Drinking Water Act
- MCL: maximum contaminant level
- Lead: 15 ppb action level

## Wastewater Treatment
### Process
1. Preliminary (screens, grit); 2. Primary (sedimentation)
3. Secondary (biological); 4. Tertiary (advanced)
5. Disinfection; 6. Sludge treatment

### Primary
- Settle solids; 50-60% TSS, 30-40% BOD removal

### Secondary
- Activated sludge: suspended growth
- Trickling filter: attached growth
- BOD removal: 85-95%

### Nutrient Removal
- Nitrification: NH4 -> NO3
- Denitrification: NO3 -> N2
- Phosphorus: biological, chemical (EBPR)

### Tertiary
- Filtration; Membrane; Carbon adsorption; Ion exchange

### Sludge
- Thickening; Digestion (anaerobic, aerobic)
- Dewatering; Disposal (landfill, land application, incineration)

## Air Pollution
### Pollutants
- Particulate (PM10, PM2.5); SO2; NOx; CO; VOC; O3; Lead

### Sources
- Stationary (power plants, industry); Mobile (vehicles); Area; Natural

### Control
- Particulate: baghouse, ESP
- SO2: scrubber (limestone)
- NOx: SCR, SNCR
- VOC: thermal oxidizer, carbon

### Dispersion
- Stack height; Wind; Stability; Inversion
- Modeling: AERMOD

### Standards
- NAAQS: national ambient; Six criteria pollutants
- SIP: state implementation plan

## Solid Waste
### Hierarchy
1. Source reduction; 2. Recycling; 3. Energy recovery
4. Treatment; 5. Landfill

### Landfill
- Bottom liner; Leachate collection; Daily cover
- Final cover; Gas (methane) capture; Groundwater monitoring

### Recycling
- Collection; Sorting (MRF); Markets; Contamination

### Composting
- Organic waste; Aerobic; 55-65 C; C/N 30:1

## Hazardous Waste
### Definition
- Ignitable, corrosive, reactive, toxic (TCLP)

### Management
- Generator; Transport (DOT); Treatment (TSDF); Manifest

### Remediation
- Source removal; Pump and treat; Bioremediation
- Soil vapor extraction; Monitored natural attenuation

## Environmental Assessment
### NEPA
- EA: environmental assessment
- EIS: environmental impact statement
- FONSI: finding of no significant impact

### Impact Areas
- Air, water, noise, traffic, ecology, socioeconomic, cultural, visual

## Common Pitfalls
- Not considering all pollutants
- Underestimating treatment needs
- Poor sludge management
- Not monitoring properly
- Ignoring environmental justice
""", "tags": ["environmental engineering", "water treatment", "wastewater", "air pollution", "solid waste", "reference"]}
    ],
    "engineering_industrial_engineering": [
        {"title": "Operations Research and Optimization Reference", "content": """# Operations Research and Optimization Reference

## Linear Programming
### Formulation
- Objective: maximize or minimize
- Decision variables; Constraints; Non-negativity

### Simplex Method
- Basic feasible solution; Pivot; Optimal

### Duality
- Primal and dual problems
- Shadow price: constraint value
- Reduced cost: variable value

### Applications
- Product mix; Blending; Transportation; Assignment; Scheduling

## Integer Programming
- Integer or binary variables
- Branch and bound; Cutting planes
- Applications: facility location, scheduling

## Network Models
### Shortest Path
- Dijkstra: non-negative; Bellman-Ford: negative

### Maximum Flow
- Ford-Fulkerson; Min cut = max flow

### Minimum Spanning Tree
- Kruskal; Prim

### Transportation
- Supply, demand, cost; Northwest corner; MODI

### Assignment
- Hungarian method; One-to-one matching

## Queuing Theory
### Kendall Notation
- A/S/c/K/N/D
- A: arrival (M, D); S: service (M, D, G); c: servers

### M/M/1
- L = lambda/(mu-lambda); W = 1/(mu-lambda)
- rho = lambda/mu (utilization)

### M/M/c
- Erlang C: probability of waiting
- Lq, Wq: queue metrics

## Inventory Management
### EOQ
- Q* = sqrt(2DS/H)
- D: demand; S: order cost; H: holding cost

### Newsvendor
- Critical ratio: Cu/(Cu+Co)

### Safety Stock
- SS = z*sigma*sqrt(L)
- ROP = dL + SS

### ABC Analysis
- A: 20% items, 80% value; B: 30%, 15%; C: 50%, 5%

## Scheduling
### Single Machine
- SPT: min flow; EDD: min tardiness; Moore: min late

### Flow Shop
- Johnson's rule (two machines); Makespan

### Job Shop
- NP-hard; Heuristics; Priority rules

## Simulation
### Monte Carlo
- Random sampling; Probability distributions; Many trials

### Discrete Event
- State changes at events; Entities; Resources; Queue

### Software
- Arena; FlexSim; Simio; AnyLogic

## Statistical Quality Control
### Control Charts
- X-bar, R, S, P, C charts
- UCL, LCL: control limits

### Process Capability
- Cp = (USL-LSL)/(6*sigma)
- Cpk > 1.33: capable

### Acceptance Sampling
- Lot, sample, AQL, LTPD; OC curve

## Lean
### Waste (Muda)
1. Overproduction; 2. Waiting; 3. Transport
4. Over-processing; 5. Inventory; 6. Motion
7. Defects; 8. Unused talent

### Tools
- 5S; Kanban; Value stream mapping; Kaizen; Poka-yoke

## Common Pitfalls
- Not validating model
- Ignoring constraints
- Over-simplifying
- Not considering variability
- Confusing average and distribution
""", "tags": ["industrial engineering", "operations research", "linear programming", "queuing", "simulation", "reference"]}
    ],
    "engineering_manufacturing_engineering": [
        {"title": "Manufacturing Processes and Quality Reference", "content": """# Manufacturing Processes and Quality Reference

## Machining
### Turning
- Lathe: workpiece rotates; Single point tool
- Operations: facing, turning, boring; CNC

### Milling
- Cutter rotates; Workpiece feeds
- Face mill; End mill; CNC 3/4/5 axis

### Drilling
- Drill bit rotates; Twist drill; Reaming; Tapping

### Grinding
- Abrasive particles; Surface; Cylindrical; Precision

### Parameters
- Cutting speed V; Feed f; Depth of cut d
- MRR; Tool life: VT^n = C (Taylor)

## Forming
### Rolling
- Reduce thickness; Hot or cold

### Forging
- Compress; Open die; Closed die; Hot or cold

### Extrusion
- Push through die; Aluminum common

### Drawing
- Pull through die; Wire; Tube; Deep drawing

### Sheet Metal
- Shearing; Bending; Stamping; Punching; Spinning

## Casting
### Sand Casting
- Pattern; Sand mold; Pour; Solidify; Break mold

### Die Casting
- Metal mold; High pressure; Zinc, aluminum; High production

### Investment Casting
- Wax pattern; Lost wax; Precision; Complex parts

### Continuous
- Long shapes: billet, slab; Cut to length

## Joining
### Welding
- Arc (SMAW, GMAW, GTAW); Resistance (spot, seam)
- Gas; Laser; Electron beam

### Brazing
- Filler melts, base doesn't; Capillary action

### Soldering
- Low temp (<450C); Electronic

### Adhesive
- Epoxy; Surface preparation critical

### Fasteners
- Bolts, nuts, screws, rivets

## Additive Manufacturing
### Types
- FDM: filament (PLA, ABS)
- SLA: resin (precise)
- SLS: powder (nylon)
- MJF: powder (production)
- DMLS: metal (titanium, steel)

### Process
1. CAD; 2. STL; 3. Slice; 4. Print; 5. Post-process

### Applications
- Prototyping; Low-volume production; Custom; Complex; Tooling

## Quality
### Inspection
- Dimensional; Visual; Functional
- Non-destructive (X-ray, ultrasonic); Destructive

### Statistical Process Control
- Control charts; X-bar and R; P chart
- Cp, Cpk; Common cause vs special cause

### Tolerances
- Dimensional; Geometric (GD&T); Surface finish (Ra, Rz)
- Fit: clearance, interference

### GD&T
- Flatness; Straightness; Circularity; Cylindricity
- Profile; Position; Concentricity

## Lean Manufacturing
### Principles
- Value; Value stream; Flow; Pull; Perfection

### Tools
- 5S; Kanban; SMED; TPM; Andon; Poka-yoke

## Common Pitfalls
- Wrong process for material
- Poor tool selection
- Not controlling tolerance
- Ignoring surface finish
- Not maintaining equipment
- Over-production
- Not training operators
""", "tags": ["manufacturing engineering", "machining", "forming", "casting", "quality", "lean", "reference"]}
    ],
}
