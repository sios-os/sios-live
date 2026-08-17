"""Engineering & Design K3 Batch 1 - 6 specialties."""

ENGINEERING_K3_BATCH1: dict[str, list[dict]] = {
    "engineering_mechanical_engineering": [
        {"title": "Mechanics, Thermodynamics, and Machine Design Reference", "content": """# Mechanics, Thermodynamics, and Machine Design Reference

## Statics
### Equilibrium
- Sum of forces = 0, Sum of moments = 0
- Free body diagram: isolate body
- 2D: sum Fx, Fy, M; 3D: sum Fx,Fy,Fz, Mx,My,Mz

### Supports
- Pin: resists two forces
- Roller: resists one force
- Fixed: resists forces and moments
- Cable: tension only

### Trusses
- Method of joints: each joint equilibrium
- Method of sections: cut through
- Assumptions: pin joints, loads at joints
- Two-force members

## Dynamics
### Kinematics
- Position: x(t); Velocity: v = dx/dt; Acceleration: a = dv/dt
- Constant accel: v = v0 + at, x = x0 + v0t + 0.5at^2
- Projectile: x = v0cos(theta)t, y = v0sin(theta)t - 0.5gt^2

### Kinetics
- Newton's 2nd: F = ma
- Work-energy: W = delta KE
- Impulse-momentum: F*dt = dp
- Conservation of momentum

### Rotational
- Torque: tau = r x F
- Moment of inertia: I = integral r^2 dm
- Angular momentum: L = I*omega
- Rotational KE: 0.5*I*omega^2

## Mechanics of Materials
### Stress and Strain
- Normal stress: sigma = F/A
- Shear stress: tau = V/A
- Normal strain: epsilon = dL/L
- Hooke's law: sigma = E*epsilon
- E: Young's modulus; G: shear modulus
- Poisson's ratio: nu = -epsilon_trans/epsilon_axial

### Loading
- Axial: tension/compression
- Bending: sigma = My/I
- Torsion: tau = T*r/J
- Combined: Mohr's circle
- Principal stresses: max and min

### Failure Theories
- Max normal stress: brittle
- Max shear stress: Tresca
- Distortion energy: von Mises
- Safety factor: strength / stress

## Thermodynamics
### Laws
- Zeroth: thermal equilibrium
- First: energy conservation
- Second: entropy increases
- Third: absolute zero

### Cycles
- Carnot: ideal, max efficiency
- Otto: spark ignition
- Diesel: compression ignition
- Brayton: gas turbine
- Rankine: steam power
- Refrigeration: reversed

### Properties
- Enthalpy: H = U + PV
- Entropy: disorder measure
- Specific heat: Cp, Cv
- Ideal gas: PV = nRT

## Machine Design
### Components
- Shafts: transmit torque
- Bearings: support rotation
- Gears: transmit power
- Springs: store energy
- Fasteners: bolts, screws
- Clutches/Brakes: connect/stop

### Gear Design
- Spur: parallel axes
- Helical: angled teeth
- Bevel: intersecting axes
- Worm: high reduction
- Gear ratio: driven/driver

### Fatigue
- Cyclic loading: repeated
- S-N curve: stress vs cycles
- Endurance limit: steel
- Miner's rule: cumulative damage
- Goodman: mean stress correction

## Common Pitfalls
- Not checking units
- Ignoring free body diagram
- Confusing stress and strain
- Not considering combined loading
- Ignoring fatigue
- Wrong factor of safety
""", "tags": ["mechanical engineering", "statics", "dynamics", "thermodynamics", "machine design", "reference"]}
    ],
    "engineering_civil_engineering": [
        {"title": "Civil Engineering Systems and Codes Reference", "content": """# Civil Engineering Systems and Codes Reference

## Geotechnical
### Soil Properties
- Grain size: gravel, sand, silt, clay
- Atterberg limits: liquid, plastic
- Compaction: Proctor test
- Permeability: flow through soil
- Shear strength: tau = c + sigma*tan(phi)

### Foundations
- Shallow: spread footing
- Deep: pile, drilled shaft
- Bearing capacity: q_ult
- Settlement: immediate and consolidation

### Retaining Walls
- Active: Ka; Passive: Kp; At-rest: K0
- Coulomb: inclined backfill
- Rankine: smooth wall

### Slope Stability
- Infinite slope: planar
- Circular: method of slices
- Factor of safety: resisting/driving

## Structural
### Loads (ASCE 7)
- Dead: permanent; Live: occupancy
- Snow: roof; Wind: lateral; Seismic: earthquake
- Load combinations: 1.2D + 1.6L + 0.5S, etc.

### Steel (AISC)
- A992: Fy = 50 ksi
- LRFD and ASD methods
- Flexural: Mn = Fy*Zx (compact)
- Shear: Vn = 0.6*Fy*Aw
- Compression: flexural buckling

### Concrete (ACI 318)
- f'c: 3000-6000 psi; Fy = 60 ksi
- Beam: Mn = As*Fy*(d - a/2)
- Column: tied or spiral
- Shear: Vc = 2*sqrt(f'c)*b*d

### Wood (NDS, AWC)
- Allowable stress design
- Adjustment factors: moisture, duration
- Connections: bolts, nails

## Transportation
### Highway Design
- Design speed: basis
- Lane width: 12 ft standard
- Sight distance: stopping, passing
- Horizontal curve: R = V^2/(15(e+f))
- Vertical curve: K = L/A

### Pavement
- Flexible: asphalt; Rigid: concrete
- Structural number: SN
- ESALs: equivalent single axle loads

### Traffic Engineering
- Volume: vph; Capacity: max flow
- Level of service: A (best) to F
- Signal timing: cycle length

## Water Resources
### Hydrology
- Rainfall: IDF curves
- Rational method: Q = CiA
- Hydrograph: flow over time
- SCS method: curve number

### Hydraulics
- Pressure: P = rho*g*h
- Continuity: A1*V1 = A2*V2
- Bernoulli: energy conservation
- Manning's: V = (1.49/n)*R^(2/3)*S^(1/2)

## Construction
### Project Delivery
- Design-bid-build: traditional
- Design-build: single entity
- CM at risk; IPD: integrated

### Scheduling
- Critical path method (CPM)
- Gantt chart; Activity; Duration; Float

## Common Pitfalls
- Not following current codes
- Ignoring soil investigation
- Underestimating loads
- Poor drainage design
- Inadequate safety factors
""", "tags": ["civil engineering", "geotechnical", "structural", "transportation", "codes", "reference"]}
    ],
    "engineering_structural_engineering": [
        {"title": "Structural Analysis and Design Reference", "content": """# Structural Analysis and Design Reference

## Analysis Methods
### Statics
- Equilibrium: sum F = 0, sum M = 0
- Determinate: reactions from statics
- Indeterminate: need compatibility

### Truss Analysis
- Method of joints: equilibrium at each joint
- Method of sections: cut through truss
- Zero-force members: identify

### Beam Analysis
- Simply supported: pin and roller
- Cantilever: fixed one end
- Continuous: multiple supports
- Shear and moment diagrams

### Frame Analysis
- Moment distribution: Hardy Cross
- Slope deflection; Matrix methods; FEM

### Influence Lines
- Moving loads: variable position
- Muller-Breslau principle

## Steel Design (AISC)
### Tension
- Yielding: Pn = Fy*Ag
- Fracture: Pn = Fu*Ae
- Block shear: combined

### Compression
- Flexural buckling: Euler
- K factor: effective length
- Slenderness: KL/r

### Flexure
- Plastic: Zx (compact)
- Lateral-torsional buckling: unbraced length

### Connections
- Bolts: bearing, slip-critical
- Welds: fillet, groove

## Concrete Design (ACI 318)
### Beams
- Rectangular: singly, doubly reinforced
- Mn = As*Fy*(d - a/2)
- a = As*Fy/(0.85*f'c*b)
- phi = 0.9 (tension controlled)

### Columns
- Tied: rectangular; Spiral: helical
- Axial: Pn = 0.85*f'c*(Ag-As) + Fy*As
- Interaction diagram: P-M curve

### Shear
- Vc = 2*sqrt(f'c)*b*d
- Stirrups: when Vu > phi*Vc

### Slabs
- One-way; Two-way; Flat plate; Flat slab
- Punching shear: critical

## Seismic Design
### Principles
- Ductility: absorb energy
- Redundancy: multiple paths
- Strong column, weak beam
- Capacity design

### Codes (ASCE 7)
- Seismic design category
- Base shear: V = Cs*W
- Equivalent lateral force
- Modal analysis: higher modes

### Detailing
- Special moment frames: ductile
- Confinement: hoops
- Lap splices: outside plastic hinges

## Wind Design (ASCE 7)
- Basic wind speed: V (mph)
- Exposure: B, C, D
- Wind pressure: q = 0.00256*Kz*Kzt*Kd*V^2

## Common Pitfalls
- Not checking serviceability (deflection)
- Ignoring second-order effects
- Wrong load combinations
- Not considering stability
- Poor connection design
""", "tags": ["structural engineering", "analysis", "steel", "concrete", "seismic", "reference"]}
    ],
    "engineering_electrical_engineering": [
        {"title": "Circuit Analysis and Power Systems Reference", "content": """# Circuit Analysis and Power Systems Reference

## DC Circuits
### Ohm's Law
- V = IR; P = VI = I^2R = V^2/R

### Kirchhoff's Laws
- KCL: sum currents at node = 0
- KVL: sum voltages in loop = 0

### Series and Parallel
- Series: R = R1 + R2 + ...
- Parallel: 1/R = 1/R1 + 1/R2 + ...
- Voltage divider: V1 = V*R1/(R1+R2)

### Network Theorems
- Thevenin: equivalent V and R
- Norton: equivalent I and R
- Superposition: sum of sources
- Max power transfer: R_L = R_Thevenin

## AC Circuits
### Sinusoidal
- v(t) = Vm*sin(omega*t + theta)
- RMS: V = Vm/sqrt(2)
- Phasor representation

### Impedance
- Resistor: Z = R
- Inductor: Z = j*omega*L
- Capacitor: Z = 1/(j*omega*C)

### Power
- Real: P = VI*cos(theta) (watts)
- Reactive: Q = VI*sin(theta) (VAR)
- Apparent: S = VI (VA)
- Power factor: cos(theta) = P/S

### Three-Phase
- Line voltage: V_L = sqrt(3)*V_phase (wye)
- Power: P = sqrt(3)*V_L*I_L*cos(theta)

## Power Systems
### Generation
- Synchronous generator: AC
- Turbine: steam, gas, hydro
- Frequency: 60 Hz (US), 50 Hz (Europe)

### Transmission
- High voltage: reduce losses
- Step-up/step-down transformers
- Losses: I^2*R

### Distribution
- Medium voltage to neighborhoods
- Service: 120/240V (US)
- Radial, loop, network configurations

### Transformers
- Turns ratio: a = N1/N2
- V1/V2 = a; I1/I2 = 1/a
- Losses: copper (I^2R), iron (core)

### Protection
- Relay: detects fault
- Circuit breaker: interrupts current
- Coordination: selective tripping

## Power Electronics
### Rectifiers
- AC to DC: half-wave, full-wave, three-phase

### Inverters
- DC to AC: PWM, square, sine wave

### Converters
- DC-DC: buck, boost, buck-boost
- AC-AC: cycloconverter

## Motors
### DC
- Shunt: constant speed
- Series: high starting torque
- Speed control: voltage, field

### AC
- Induction: most common, slip
- Synchronous: constant speed
- Synchronous speed: Ns = 120f/p

## Common Pitfalls
- Confusing real and reactive power
- Not considering power factor
- Ignoring three-phase relationships
- Wrong transformer connections
- Not coordinating protection
""", "tags": ["electrical engineering", "circuits", "power systems", "transformers", "motors", "reference"]}
    ],
    "engineering_electronic_engineering": [
        {"title": "Electronic Circuits and Systems Reference", "content": """# Electronic Circuits and Systems Reference

## Semiconductor Devices
### Diode
- PN junction: one-way
- Forward: 0.7V (silicon)
- Zener: breakdown; LED: light; Schottky: fast

### BJT Transistor
- NPN, PNP
- Terminals: base, emitter, collector
- Modes: cutoff, active, saturation
- Beta: Ic/Ib

### MOSFET
- NMOS, PMOS
- Terminals: gate, drain, source
- Enhancement: normally off
- Threshold: Vth

### Op-Amp
- Ideal: infinite gain, input impedance
- Inverting: Vout = -Rf/Rin * Vin
- Non-inverting: Vout = (1 + Rf/Rin) * Vin
- Summing, difference, integrator, comparator

## Analog Circuits
### Amplifiers
- Class A: linear, inefficient
- Class B: push-pull, crossover
- Class AB: reduce crossover
- Class D: switching, efficient

### Filters
- Low-pass, high-pass, band-pass, band-stop
- Butterworth: flat passband
- Chebyshev: steeper, ripple
- Bessel: linear phase

### Oscillators
- Wien bridge: sine
- Colpitts, Hartley: LC
- Crystal: precise frequency

## Digital Circuits
### Logic Gates
- AND, OR, NOT, NAND, NOR, XOR, XNOR

### Boolean Algebra
- De Morgan: (AB)' = A'+B', (A+B)' = A'B'
- Absorption: A+AB = A

### Combinational
- Decoder, encoder, multiplexer, demultiplexer
- Adder, comparator

### Sequential
- Flip-flops: SR, D, JK, T
- Register, counter, shift register

### State Machines
- Moore: output depends on state
- Mealy: output depends on state and input

## Microcontrollers
### Architecture
- CPU, memory (RAM, ROM, flash)
- I/O ports, timer, ADC
- UART, SPI, I2C, CAN

### Programming
- C: most common
- Arduino: simplified
- RTOS: FreeRTOS, Zephyr

### Common Chips
- Arduino (ATmega): 8-bit
- ESP32: 32-bit, WiFi, Bluetooth
- STM32 (ARM Cortex): 32-bit

## Communication
### Modulation
- AM, FM, PM
- ASK, FSK, PSK, QAM

### Protocols
- UART, SPI, I2C, CAN, USB, Ethernet
- Bluetooth, WiFi

### Wireless
- RF, antenna, bandwidth, channel
- Multiplexing: FDMA, TDMA, CDMA, OFDMA

## Signal Processing
### Sampling
- Nyquist: sample at 2x highest frequency
- Aliasing: undersampling distortion
- ADC, DAC

### Transforms
- Fourier: time to frequency
- FFT: fast algorithm
- Z-transform: discrete time

### Digital Filters
- FIR: finite impulse response
- IIR: infinite impulse response

## Common Pitfalls
- Not decoupling power supplies
- Ignoring ground loops
- Not considering noise
- Wrong bias point
- Not simulating before building
- Ignoring thermal limits
""", "tags": ["electronic engineering", "circuits", "semiconductors", "digital", "microcontrollers", "reference"]}
    ],
    "engineering_chemical_engineering": [
        {"title": "Chemical Processes and Transport Phenomena Reference", "content": """# Chemical Processes and Transport Phenomena Reference

## Material and Energy Balances
### Conservation
- Mass in = mass out + accumulation
- Energy in = energy out + accumulation
- Steady state: no accumulation

### Process Elements
- Input, output, recycle, purge, bypass

## Transport Phenomena
### Momentum (Fluid Mechanics)
- Viscosity: resistance to flow
- Laminar: Re < 2100; Turbulent: Re > 4000
- Reynolds: Re = rho*V*D/mu
- Pressure drop: Darcy-Weisbach
- Bernoulli: P + 0.5*rho*V^2 + rho*g*z = const

### Heat Transport
- Conduction: q = -k*dT/dx (Fourier)
- Convection: q = h*(Ts - Tinf)
- Radiation: q = epsilon*sigma*T^4
- Heat exchanger: Q = U*A*deltaT_lm

### Mass Transport
- Diffusion: J = -D*dC/dx (Fick)
- Convection: bulk flow
- Mass transfer coefficient: k

## Separation Processes
### Distillation
- Vapor-liquid equilibrium
- Relative volatility: alpha
- McCabe-Thiele: graphical
- Fenske: minimum stages
- Tray column; Packed column

### Absorption
- Gas to liquid; Henry's law
- Packed tower; NTU

### Extraction
- Liquid-liquid; Distribution coefficient
- Selectivity; Multiple stages

### Membrane
- Reverse osmosis; Ultrafiltration; Microfiltration

### Adsorption
- Surface binding; Isotherm: Langmuir, Freundlich

## Reaction Engineering
### Rate Laws
- Rate: r = k*C^n
- Arrhenius: k = A*exp(-Ea/RT)

### Reactor Types
- Batch: no flow
- CSTR: continuous stirred tank
- PFR: plug flow reactor
- PBR: packed bed

### Design Equations
- Batch: t = integral dX/r
- CSTR: V = F*X0/r
- PFR: V = integral F/r dX
- Space time: tau = V/F

## Thermodynamics
### Phase Equilibrium
- Vapor pressure: Antoine equation
- Raoult's law: ideal; Henry's: dilute
- Dew point; Bubble point

### Chemical Equilibrium
- K_eq: equilibrium constant
- delta G = -RT*ln(K)
- Le Chatelier: shift to relieve stress

## Process Control
### Feedback
- Measure, compare, adjust
- PID: proportional, integral, derivative

### PID Tuning
- Ziegler-Nichols: ultimate
- Cohen-Coon; IMC; Lambda

### Advanced
- Cascade; Feedforward; Ratio; Split range

## Safety
### Hazards
- Toxic, flammable, reactive, corrosive

### Analysis
- HAZOP: hazard and operability
- FMEA: failure mode effects
- LOPA: layer of protection

### Prevention
- Inherently safer design
- Layers of protection
- Interlocks; Relief; Detection

## Common Pitfalls
- Not checking units
- Ignoring non-ideal behavior
- Not considering heat effects
- Poor reactor selection
- Inadequate safety analysis
""", "tags": ["chemical engineering", "transport phenomena", "separations", "reactors", "process control", "reference"]}
    ],
}
