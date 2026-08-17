"""Engineering & Design K3 Batch 4 - 5 specialties."""

ENGINEERING_K3_BATCH4: dict[str, list[dict]] = {
    "engineering_power_energy_systems": [
        {"title": "Power Generation and Grid Systems Reference", "content": """# Power Generation and Grid Systems Reference

## Generation
### Thermal
- Boiler (steam), turbine, generator, condenser
- Efficiency: 30-40% (steam), 60% (CCGT)

### Nuclear
- Reactor (heat), steam, turbine, generator; ~33% efficiency

### Hydro
- Dam, penstock, turbine (Francis, Kaplan, Pelton), generator
- 90%+ efficiency; Capacity depends on head and flow

### Wind
- Turbine blades, gearbox, generator
- Onshore, offshore; Capacity factor 30-45%

### Solar
- PV: direct; CSP: thermal (mirror, steam)
- Capacity factor 15-25% (PV); Intermittent

### Natural Gas
- Combined cycle (gas + steam); 60% efficiency; Peaker plants

### Coal
- Pulverized, fluidized bed, IGCC; Declining

### Biomass
- Direct burn, biogas, biofuel

### Geothermal
- Dry steam, flash, binary

## Transmission
### Lines
- HVAC: 115-765 kV; HVDC: long distance
- Conductors: aluminum, ACSR; Towers: lattice, monopole

### Substations
- Transformer, switchgear, bus, protection, capacitors

### System Operation
- Balancing (generation = load); Frequency 60 Hz
- Reserve: spinning, non-spinning; Economic dispatch

### Stability
- Transient, dynamic, voltage, rotor angle

## Distribution
### System
- Substation (step down), feeders, laterals, service
- Voltage: 4-35 kV to 120/240V

### Configuration
- Radial (one path); Loop (alternate); Network (urban, highest reliability)

### Components
- Transformer (pole, pad); Switch; Fuse; Recloser; Capacitor

## Smart Grid
### Features
- Two-way communication; Automation; AMI; Real-time monitoring

### Technologies
- AMI; SCADA; DA; DERMS; Microgrid

### Benefits
- Reliability, efficiency, renewable integration, demand response

## Energy Storage
### Types
- Pumped hydro (largest); Battery (lithium-ion)
- Compressed air; Flywheel; Thermal; Hydrogen

### Applications
- Arbitrage; Frequency regulation; Capacity; Reserve; Renewables smoothing

### Battery
- Lithium-ion; Flow (vanadium, zinc); Lead-acid; Sodium-sulfur; Solid-state

## Power Electronics
### Devices
- Diode; Thyristor (SCR); IGBT; MOSFET

### Converters
- Rectifier (AC-DC); Inverter (DC-AC); Chopper (DC-DC); Cycloconverter

### Applications
- Variable speed drives; Renewable integration; HVDC; FACTS; EV charging

## Renewable Integration
### Challenges
- Intermittency; Uncertainty; Location; Capacity factor; Grid stability (inertia)

### Solutions
- Storage; Forecasting; Aggregation; Demand response; Interconnection

## Economics
### Costs
- Capital; Operating; Fuel; LCOE
- LCOE = (capital + O&M + fuel) / energy produced

### Market
- Wholesale; Retail; Capacity; Energy; Ancillary services

### Regulation
- Vertically integrated; Restructured; RTO/ISO

## Common Pitfalls
- Not planning for intermittency
- Underestimating transmission needs
- Ignoring reactive power
- Not considering stability
- Poor protection coordination
- Not investing in storage
""", "tags": ["power engineering", "generation", "transmission", "distribution", "renewable", "reference"]}
    ],
    "engineering_controls_automation": [
        {"title": "Control System Design and Automation Reference", "content": """# Control System Design and Automation Reference

## Classical Control
### Transfer Functions
- Laplace transform: time to s-domain
- Poles: roots of denominator; Zeros: roots of numerator
- Stability: poles in left half plane

### Block Diagrams
- Series: multiply; Parallel: add
- Feedback: G/(1+GH)

### Time Response
- First order: tau (time constant)
- Second order: natural frequency, damping
- Rise time; Settling time; Overshoot; Steady-state error

### Frequency Response
- Bode plot (magnitude, phase)
- Gain margin; Phase margin; Bandwidth

### Stability
- Routh-Hurwitz; Root locus; Nyquist criterion

### Controllers
- P, PI, PD, PID; Lead, lag, lead-lag

## PID Control
### Form
- u(t) = Kp*e + Ki*integral(e) + Kd*de/dt

### Effects
- P: fast, steady-state error
- I: eliminate steady-state error, slow
- D: anticipate, reduce overshoot, noise

### Tuning
- Ziegler-Nichols: ultimate gain and period
  - Kp = 0.6Ku, Ki = 1.2Ku/Pu, Kd = 0.075Ku*Pu
- Cohen-Coon; IMC; Auto-tune

### Implementation
- Anti-windup; Derivative filter; Setpoint weighting; Bumpless transfer

## Modern Control
### State-Space
- x' = Ax + Bu; y = Cx + Du

### Controllability
- Can we reach any state?
- Controllability matrix: [B AB A^2B ...]; Full rank = controllable

### Observability
- Can we determine state from output?
- Observability matrix; Full rank = observable

### Pole Placement
- Choose desired poles; Calculate gain K; Ackermann's formula

### Observer
- Luenberger observer; Kalman filter (optimal)

### Optimal Control
- LQR: linear quadratic regulator
- Cost: integral of x'Qx + u'Ru; Riccati equation
- LQG: LQR + Kalman

## Digital Control
### Sampling
- Discrete time; Sample rate T; Z-transform; z = e^(sT)
- Aliasing: undersampling

### Discrete Controller
- Difference equation; Digital PID; Microcontroller implementation

### Stability
- z-plane: inside unit circle; Jury test

## Nonlinear Control
### Methods
- Linearization; Feedback linearization; Sliding mode; Adaptive; Backstepping

### Phenomena
- Limit cycle; Chaos; Bifurcation

## Process Control
### Loops
- Single; Cascade (nested); Feedforward; Ratio; Override

### Architecture
- Sensor; Controller; Actuator; Process; Transmitter

### Implementation
- DCS: distributed control system
- PLC: programmable logic controller
- SCADA: supervisory
- Fieldbus: digital communication

## PLC Programming
### Languages (IEC 61131-3)
- Ladder diagram; Function block; Structured text
- Instruction list; Sequential function chart

### Logic
- Inputs (sensors, switches); Outputs (actuators)
- Internal (memory, timers, counters); Scan cycle

## Industrial Automation
### Levels
- Field (sensors, actuators); Control (PLC); Supervisory (SCADA, HMI); Planning (MES, ERP)

### Components
- Sensor; Transmitter; Controller; Actuator; HMI; Network

### Applications
- Manufacturing; Process; Packaging; Material handling; Robotics

## Common Pitfalls
- Poor tuning
- Not considering noise
- Ignoring nonlinearities
- Not testing safety
- Poor sensor placement
- Not considering failure modes
""", "tags": ["control engineering", "PID", "state-space", "PLC", "automation", "reference"]}
    ],
    "engineering_acoustical_engineering": [
        {"title": "Acoustics and Noise Control Reference", "content": """# Acoustics and Noise Control Reference

## Fundamentals
### Sound Wave
- Pressure variation; Frequency (Hz); Wavelength lambda = c/f
- Speed: c = 343 m/s (air, 20C); Amplitude; Phase

### Decibel Scale
- SPL: 20*log10(p/p_ref); p_ref = 20 microPa
- 0 dB: threshold of hearing; 120 dB: threshold of pain
- 3 dB: noticeable; 10 dB: perceived doubling

### Frequency Weighting
- A-weighting (dBA): human hearing
- C-weighting (dBC): peak
- Octave bands: 31.5 to 8000 Hz

## Room Acoustics
### Reverberation
- RT60: time to decay 60 dB
- Sabine: RT = 0.161*V/A
- V: volume; A: total absorption

### Absorption
- Coefficient alpha (0 to 1)
- Porous, membrane, resonator materials
- Frequency-dependent

### Reflection
- Specular (mirror); Diffuse (scattered)
- Diffusers: QRD, Schroeder; Echo

### Room Modes
- Axial (two surfaces); Tangential (four); Oblique (six)
- Standing waves; Bass problems in small rooms

## Architectural Acoustics
### Design Goals
- Speech intelligibility; Music richness; Noise control; Privacy

### Speech Intelligibility
- STI: speech transmission index; D/R ratio

### Concert Hall
- Shoebox; Vineyard; Surround
- Reverberation: 1.8-2.2 s

## Noise Control
### Sources
- Transportation (road, rail, air); Industrial; Building (HVAC); Community

### Path
- Airborne; Structure-borne; Flanking

### Control
- Source: reduce at origin
- Path: block or absorb
- Receiver: protect

### Barriers
- Mass; Absorption; Diffraction over top; Insertion loss

### Enclosure
- Full or partial; Mass (STC rating); Seal gaps

### Vibration Isolation
- Springs; Pads (neoprene, cork); Air pneumatic
- Natural vs forcing frequency; Transmissibility

### Damping
- Viscoelastic materials; Constrained layer; Free layer; Loss factor

## Sound Transmission
### STC (Sound Transmission Class)
- Single number rating; ASTM E90
- 25: poor, 50: excellent

### OITC
- Lower frequencies; Transportation noise

### IIC (Impact Insulation Class)
- Floor impact; Tapping machine; 50: minimum code

## HVAC Noise
### Sources
- Fans (broadband); Ducts; Terminals; Compressors (tonal); Vibration

### Control
- Low velocity design; Silencers; Duct lining
- Flexible connectors; Vibration isolation

## Measurement
### Instruments
- Sound level meter; Microphone (condenser); Analyzer; Calibrator; Dosimeter

### Standards
- ANSI; IEC; ISO; ASTM

### Parameters
- Leq: equivalent; Lmax, Lmin; L10, L50, L90; Peak

## Psychoacoustics
### Perception
- Loudness; Pitch; Timbre; Duration; Localization

### Masking
- Simultaneous; Forward; Backward; Critical bands

### Spatial Hearing
- ITD: interaural time; ILD: interaural level
- HRTF: head-related transfer function; Precedence effect

## Common Pitfalls
- Ignoring low frequencies
- Not treating flanking paths
- Over-absorbing (dead room)
- Not considering vibration
- Poor microphone placement
- Not calibrating instruments
""", "tags": ["acoustical engineering", "room acoustics", "noise control", "STC", "measurement", "reference"]}
    ],
    "engineering_marine_naval_engineering": [
        {"title": "Naval Architecture and Marine Systems Reference", "content": """# Naval Architecture and Marine Systems Reference

## Hydrostatics
### Displacement
- Displacement: weight of displaced water
- Buoyancy: upward force; Archimedes: F = rho*g*V
- Equilibrium: weight = buoyancy

### Coefficients
- Block: Cb = V/(L*B*T)
- Midship: Cm = Am/(B*T)
- Prismatic: Cp = Cb/Cm
- Waterplane: Cw = Aw/(L*B)

### Tons
- Displacement: total; Lightship: empty; Deadweight: cargo
- Gross; Net

## Stability
### Transverse
- Metacenter M; GZ: righting arm; GM: metacentric height
- Positive GM: stable; Negative: unstable
- GM = KB + BM - KG

### Curves
- GZ curve: righting arm vs heel
- Area under: energy; Maximum GZ; Range; Downflooding

### Longitudinal
- LCG, LCB; Trim; MTC: moment to change trim

### Free Surface
- Liquid in tank reduces GM; Baffles reduce effect

## Resistance
### Components
- Frictional (skin); Viscous (form); Wave; Pressure; Total

### Froude Number
- Fr = V/sqrt(g*L)
- Wave making dominant at high Fr; Friction at low Fr

### Methods
- Series (Taylor, Holtrop); CFD; Towing tank; ITTC

### Reduction
- Smooth surface; Bulbous bow; Stern shape; Air lubrication

## Propulsion
### Propeller
- Blades 3-7; Pitch; Diameter; RPM; Thrust; Torque

### Efficiency
- Open water; Behind hull; Relative rotative; Overall

### Cavitation
- Low pressure boiling; Erosion; Noise; Vibration

### Types
- Fixed pitch; Controllable pitch; Contra-rotating; Pod; Waterjet

### Alternative
- Sail; Oar; Paddle wheel; Voith-Schneider

## Structures
### Loads
- Still water; Wave; Slamming; Sloshing; Thermal; Fatigue

### Strength
- Longitudinal (hull girder); Transverse (frame); Local (panel)
- Buckling; Yield

### Materials
- Steel (common); Aluminum (light); Composites (FRP); Concrete; Titanium

### Classification
- ABS, DNV, LR; Rules; Surveys; Certificates

## Seakeeping
### Motions
- Heave; Pitch; Roll; Yaw; Sway; Surge

### Response
- RAO: response amplitude operator
- Frequency; Resonance; Periods

### Stabilization
- Bilge keel (passive); Fin (active); Tank; Gyro

## Maneuvering
### Turning
- Rudder; Drift angle; Turning circle
- Advance; Transfer; Tactical diameter

### Course Keeping
- Directional stability; Autopilot

## Marine Systems
### Propulsion Machinery
- Diesel (most common); Steam (LNG); Gas turbine (naval)
- Electric (pod); Nuclear (submarine, carrier)

### Auxiliary
- Generators; Boilers; Pumps; Compressors; Fresh water

### Systems
- Ballast; Bilge; Fire; HVAC; Fuel; Potable water

## Offshore
### Platforms
- Fixed; Jack-up; Semi-submersible; Drillship; TLP; Spar; FPSO

### Mooring
- Spread; Turret; Dynamic positioning; Anchors; Chains

### Risers
- Production; Export; Flexible; Steel catenary; Top tensioned

## Common Pitfalls
- Insufficient stability
- Not considering free surface
- Underestimating loads
- Poor fatigue design
- Not considering corrosion
- Inadequate safety systems
""", "tags": ["marine engineering", "naval architecture", "stability", "propulsion", "structures", "reference"]}
    ],
    "engineering_reliability_maintenance_engineering": [
        {"title": "Reliability Analysis and Maintenance Strategies Reference", "content": """# Reliability Analysis and Maintenance Strategies Reference

## Reliability Theory
### Definitions
- Reliability R(t): probability of function to time t
- Failure F(t) = 1 - R(t)
- Failure density f(t) = dF/dt
- Failure rate lambda(t) = f(t)/R(t)
- MTBF: mean time between failures
- MTTF: mean time to failure
- MTTR: mean time to repair

### Distributions
- Exponential: constant failure rate
  - R(t) = exp(-lambda*t); MTTF = 1/lambda
- Weibull: flexible
  - R(t) = exp(-(t/eta)^beta)
  - beta < 1: infant mortality
  - beta = 1: random (exponential)
  - beta > 1: wearout
- Lognormal; Normal; Gamma

### Bathtub Curve
- Infant mortality: decreasing failure rate
- Useful life: constant (random failures)
- Wearout: increasing failure rate

## System Reliability
### Series
- R_sys = R1 * R2 * ... * Rn
- Weakest link; Lowest reliability dominates

### Parallel
- R_sys = 1 - (1-R1)(1-R2)...(1-Rn)
- Redundancy improves reliability

### k-out-of-n
- At least k of n must work
- R = sum of combinations

### Standby
- Active: all operating
- Standby: backup off until needed
- Warm: partially energized

## Availability
### Definitions
- Availability: ready to use when needed
- A = MTBF / (MTBF + MTTR)
- Inherent: design; Achieved: actual; Operational: including logistics

### Steady State
- A = uptime / (uptime + downtime)
- A = MTBF / (MTBF + MTTR + MDT)

## Failure Analysis
### FMEA (Failure Mode and Effects Analysis)
- Identify failure modes
- Determine effects
- Assess severity, occurrence, detection
- RPN: risk priority number
- Take action on high RPN

### FTA (Fault Tree Analysis)
- Top event: undesired
- Logic gates: AND, OR
- Basic events: causes
- Cut sets: combinations
- Minimal cut sets

### RCA (Root Cause Analysis)
- 5 Whys
- Fishbone (Ishikawa)
- Fault tree
- Corrective action

## Maintenance Strategies
### Corrective (Run-to-Failure)
- Fix when breaks
- Simple, cheap items
- High downtime risk

### Preventive (Time-Based)
- Scheduled maintenance
- Reduces failures
- May over-maintain

### Predictive (Condition-Based)
- Monitor condition
- Maintain when needed
- Sensors: vibration, temperature, oil
- Reduces unnecessary work

### RCM (Reliability-Centered Maintenance)
- Identify functions and failures
- Determine consequences
- Select maintenance task
- Optimize strategy

### Proactive
- Find and fix root causes
- Prevent recurrence
- Continuous improvement

## Condition Monitoring
### Techniques
- Vibration: rotating equipment
- Thermography: heat
- Oil analysis: wear particles
- Ultrasonic: leaks, thickness
- Acoustic emission: cracks
- Motor current: electrical

### Trending
- Baseline; Monitor; Trend; Alarm; Action

## Design for Reliability
### Principles
- Derating: below rated capacity
- Redundancy: backup
- Simplicity: fewer parts
- Standardization: proven parts
- Fail-safe: safe on failure
- Maintainability: easy to repair

### HALT/HASS
- HALT: highly accelerated life test
  - Find weaknesses in design
  - Stress beyond specs
- HASS: highly accelerated stress screen
  - Production screening
  - Catch defects

## Standards
### MIL-HDBK-217
- Failure rates for electronic components
- Environment factors
- Part count and stress analysis

### ISO 14224
- Reliability data collection
- Equipment classification

### IEC 61508
- Functional safety
- Safety integrity levels (SIL)
- Probability of failure on demand

## Common Pitfalls
- Not collecting failure data
- Ignoring common cause failures
- Over-reliance on redundancy
- Not considering human factors
- Poor maintenance planning
- Not tracking metrics
""", "tags": ["reliability", "maintenance", "MTBF", "FMEA", "RCM", "reference"]}
    ],
}
