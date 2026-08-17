"""Natural Sciences K3 - 17 specialties in 5 batches (4+4+3+3+3)."""

NATURAL_K3_BATCH1: dict[str, list[dict]] = {
    "natural_sciences_physics": [
        {
            "title": "Classical Mechanics and Thermodynamics Reference",
            "content": """# Classical Mechanics and Thermodynamics Reference

## Newton's Laws
1. Object at rest stays at rest; object in motion stays in motion (inertia)
2. F = ma (force = mass x acceleration)
3. For every action, equal and opposite reaction

## Conservation Laws
- Energy: total energy constant in isolated system
- Momentum: total momentum constant in isolated system
- Angular momentum: constant in absence of external torque

## Kinematics
- v = v0 + at
- x = x0 + v0 t + (1/2) a t^2
- v^2 = v0^2 + 2a(x - x0)

## Rotational Motion
- tau = r x F (torque)
- L = I omega (angular momentum)
- I = integral r^2 dm (moment of inertia)
- tau = I alpha (rotational F=ma)
- KE_rot = (1/2) I omega^2

## Simple Harmonic Motion
- F = -kx (Hooke's law)
- omega = sqrt(k/m)
- T = 2 pi / omega = 2 pi sqrt(m/k)
- x(t) = A cos(omega t + phi)

## Thermodynamics Laws
### Zeroth Law
- If A in thermal equilibrium with B, and B with C, then A with C
- Defines temperature

### First Law
- Energy conservation: dU = dQ - dW
- dU: change in internal energy
- dQ: heat added to system
- dW: work done by system

### Second Law
- Entropy of isolated system never decreases
- dS >= dQ / T
- Heat flows from hot to cold spontaneously

### Third Law
- As T -> 0, entropy approaches constant (often zero)
- Cannot reach absolute zero in finite steps

## Thermodynamic Processes
- Isothermal: T constant; W = nRT ln(V2/V1)
- Adiabatic: Q = 0; PV^gamma = constant
- Isobaric: P constant; W = P delta V
- Isovolumetric: V constant; W = 0

## Heat Engines
- Efficiency: eta = W / Q_H = 1 - T_C / T_H (Carnot)
- Carnot cycle: most efficient possible
- Otto cycle: gasoline engine
- Diesel cycle: diesel engine

## Entropy
- S = k_B ln W (Boltzmann)
- W: number of microstates
- Statistical: dS = dQ_rev / T

## Common Pitfalls
- Confusing heat and temperature
- Forgetting sign conventions (work by vs on system)
- Assuming efficiency > Carnot limit
- Ignoring conservation laws
- Confusing reversible and irreversible processes
""",
            "tags": ["physics", "mechanics", "thermodynamics", "Newton", "entropy", "reference"],
        }
    ],
    "natural_sciences_chemistry": [
        {
            "title": "Chemical Bonding and Reactions Reference",
            "content": """# Chemical Bonding and Reactions Reference

## Atomic Structure
- Protons: positive, in nucleus, determine element
- Neutrons: neutral, in nucleus, isotopes
- Electrons: negative, in shells around nucleus
- Atomic number: number of protons
- Mass number: protons + neutrons
- Isotopes: same element, different neutrons

## Electron Configuration
- Shells: n=1, 2, 3, ... (K, L, M, ...)
- Subshells: s (2e), p (6e), d (10e), f (14e)
- Aufbau: fill lowest energy first
- Hund's rule: maximize unpaired electrons
- Pauli exclusion: max 2 electrons per orbital, opposite spin

## Periodic Trends
- Atomic radius: decreases across period, increases down group
- Ionization energy: increases across period, decreases down group
- Electron affinity: increases across period
- Electronegativity: increases across period (F highest)

## Chemical Bonds

### Covalent
- Shared electron pairs
- Single, double, triple bonds
- Polar: unequal sharing (electronegativity difference)
- Nonpolar: equal sharing
- Sigma: head-on overlap; Pi: side-on overlap

### Ionic
- Transfer of electrons
- Cation (+) and anion (-)
- Lattice structure
- Strong electrostatic attraction

### Metallic
- Electron sea model
- Delocalized electrons
- Conductivity, malleability, ductility

### Intermolecular Forces
- Hydrogen bond: H with N, O, F
- Dipole-dipole: polar molecules
- London dispersion: all molecules, temporary dipoles
- Ion-dipole: ion and polar molecule

## Reaction Types
- Synthesis: A + B -> AB
- Decomposition: AB -> A + B
- Single replacement: A + BC -> AC + B
- Double replacement: AB + CD -> AD + CB
- Combustion: + O2 -> CO2 + H2O
- Acid-base: H+ transfer
- Redox: electron transfer

## Stoichiometry
- Balanced equation: same atoms on both sides
- Moles: 6.022 x 10^23
- Molar mass: g/mol
- Limiting reagent: runs out first, determines product
- Percent yield: actual / theoretical x 100

## Equilibrium
- K_c = [products] / [reactants] (with stoichiometric powers)
- Le Chatelier: system shifts to relieve stress
- K_sp: solubility product
- K_a: acid dissociation; pK_a = -log K_a
- pH = -log[H+]; pOH = -log[OH-]; pH + pOH = 14

## Kinetics
- Rate = k [A]^m [B]^n
- Order: m, n (determined experimentally)
- Activation energy: Ea (Arrhenius: k = A e^{-Ea/RT})
- Catalyst: lowers Ea, not consumed

## Common Pitfalls
- Not balancing equations
- Confusing moles with molecules
- Ignoring limiting reagent
- Confusing K_c with Q (reaction quotient)
- Forgetting catalysts don't shift equilibrium
""",
            "tags": ["chemistry", "bonding", "reactions", "stoichiometry", "equilibrium", "reference"],
        }
    ],
    "natural_sciences_biology": [
        {
            "title": "Molecular Biology and Genetics Reference",
            "content": """# Molecular Biology and Genetics Reference

## DNA Structure
- Double helix (Watson & Crick, 1953)
- Sugar-phosphate backbone
- Bases: Adenine (A), Thymine (T), Guanine (G), Cytosine (C)
- Pairing: A-T (2 H bonds), G-C (3 H bonds)
- Antiparallel strands: 5' to 3' and 3' to 5'
- Major and minor grooves

## Central Dogma
DNA -> RNA -> Protein

### Replication
- Semi-conservative: each daughter has one old, one new strand
- DNA polymerase: adds nucleotides 5' to 3'
- Leading strand: continuous
- Lagging strand: Okazaki fragments
- Primase: makes RNA primer
- Ligase: joins fragments
- Helicase: unwinds DNA
- Topoisomerase: relieves supercoiling

### Transcription
- DNA -> mRNA
- RNA polymerase
- Promoter: start site (TATA box)
- Intron: non-coding (removed by splicing)
- Exon: coding (retained)
- 5' cap and poly-A tail

### Translation
- mRNA -> protein (ribosome)
- Codon: 3 nucleotides -> 1 amino acid
- Genetic code: 64 codons, 20 amino acids, degenerate
- Start codon: AUG (Methionine)
- Stop codons: UAA, UAG, UGA
- tRNA: carries amino acid, anticodon matches codon
- Ribosome: large and small subunits

## Mendelian Genetics
- Law of segregation: alleles separate in gamete formation
- Law of independent assortment: genes on different chromosomes inherited independently
- Dominant: expressed in heterozygote
- Recessive: expressed only in homozygote
- Genotype: genetic makeup
- Phenotype: observable traits
- Monohybrid cross: Aa x Aa -> 3:1 phenotype
- Dihybrid cross: AaBb x AaBb -> 9:3:3:1 phenotype

## Extensions of Mendel
- Incomplete dominance: blend (red + white = pink)
- Codominance: both expressed (AB blood type)
- Multiple alleles: ABO blood (I^A, I^B, i)
- Polygenic: multiple genes (height, skin color)
- Epistasis: one gene affects another
- Pleiotropy: one gene affects multiple traits
- Sex-linked: on X or Y chromosome
- Linked genes: on same chromosome; recombine

## Evolution
- Natural selection: variation + inheritance + differential survival
- Fitness: reproductive success
- Genetic drift: random change in allele frequency
- Gene flow: migration between populations
- Mutation: source of new variation
- Speciation: allopatric (geographic), sympatric (same area)
- Hardy-Weinberg: p^2 + 2pq + q^2 = 1 (equilibrium)

## Common Pitfalls
- Confusing transcription with translation
- Thinking all mutations are harmful
- Confusing genotype with phenotype
- Assuming dominant = common (not necessarily)
- Forgetting introns are removed
- Confusing mitosis with meiosis
""",
            "tags": ["biology", "DNA", "genetics", "molecular biology", "evolution", "reference"],
        }
    ],
    "natural_sciences_astronomy": [
        {
            "title": "Stellar Evolution and Cosmology Reference",
            "content": """# Stellar Evolution and Cosmology Reference

## Star Formation
- Nebula: cloud of gas and dust
- Gravity causes collapse
- Protostar: heating, not yet fusing
- Main sequence: H fusion begins, stable

## Main Sequence
- H -> He fusion (proton-proton chain or CNO cycle)
- E = mc^2: mass converted to energy
- Lifetime: depends on mass (high mass = short life)
- Sun: ~10 billion years; high mass: millions; low mass: trillions

## Post-Main Sequence

### Low Mass (< 8 solar masses)
- Red giant: expands, cools
- Helium fusion: triple-alpha process
- Planetary nebula: outer layers ejected
- White dwarf: core remnant (C, O)
- Chandrasekhar limit: 1.4 solar masses max

### High Mass (> 8 solar masses)
- Red supergiant
- Fusion up to iron (Fe)
- Supernova: core collapse, explosion
- Neutron star: if remnant 1.4-3 solar masses
- Black hole: if remnant > 3 solar masses

## Hertzsprung-Russell Diagram
- X-axis: temperature (hot left, cool right)
- Y-axis: luminosity
- Main sequence: diagonal band
- Red giants: upper right
- White dwarfs: lower left

## Cosmology

### Big Bang
- Universe began ~13.8 billion years ago
- Started as hot, dense state
- Expanded and cooled
- Evidence: CMB, redshift, abundance of elements

### Cosmic Timeline
- 0: Big Bang
- 10^-43 s: Planck time
- 10^-35 s: Inflation
- 1 s: nucleosynthesis begins
- 380,000 years: atoms form, CMB released
- 400 million years: first stars
- 9 billion years: Earth forms
- 13.8 billion years: now

### Expansion
- Hubble's law: v = H0 * d
- H0 ~ 70 km/s/Mpc
- Accelerating expansion (dark energy, 1998 discovery)
- Dark matter: ~27% of universe
- Dark energy: ~68% of universe
- Ordinary matter: ~5%

### Fate of Universe
- Big Freeze: expand forever, cool (current model)
- Big Crunch: recollapse
- Big Rip: dark energy tears apart

## Distance Measurement
- Parallax: nearby stars (up to ~10,000 ly)
- Standard candles: Cepheids, Type Ia supernovae
- Redshift: distant galaxies

## Common Pitfalls
- Confusing solar mass with solar luminosity
- Thinking black holes suck things in (only if close)
- Assuming Big Bang was explosion in space (it was of space)
- Confusing dark matter with dark energy
- Ignoring lookback time in observations
""",
            "tags": ["astronomy", "stars", "stellar evolution", "cosmology", "Big Bang", "reference"],
        }
    ],
}

NATURAL_K3_BATCH2: dict[str, list[dict]] = {
    "natural_sciences_geology": [
        {
            "title": "Plate Tectonics and Rock Cycle Reference",
            "content": """# Plate Tectonics and Rock Cycle Reference

## Plate Tectonics

### Theory
- Lithosphere (crust + upper mantle) broken into plates
- Plates move on asthenosphere (plastic mantle)
- Driven by convection currents and slab pull
- Rates: 1-15 cm/year

### Plate Boundaries
- Divergent: plates move apart; mid-ocean ridges, rift valleys
- Convergent: plates collide; subduction zones, mountains
- Transform: plates slide past; faults (San Andreas)

### Convergent Types
- Ocean-ocean: island arcs (Japan, Aleutians)
- Ocean-continent: volcanic arcs (Andes, Cascades)
- Continent-continent: mountains (Himalayas, Alps)

### Evidence
- Continental fit (South America-Africa)
- Fossil distribution (mesosaurus)
- Paleomagnetism (magnetic stripes)
- Seafloor spreading (mid-ocean ridges)
- Earthquake and volcano distribution

## Rock Cycle

### Igneous
- Formed from cooling magma/lava
- Intrusive (plutonic): slow cooling, coarse grains (granite, diorite, gabbro)
- Extrusive (volcanic): fast cooling, fine grains (basalt, andesite, rhyolite)
- Magma: below surface; Lava: above surface

### Sedimentary
- Formed from accumulated sediments
- Clastic: fragments (sandstone, shale, conglomerate)
- Chemical: precipitated (evaporites, some limestone)
- Biochemical: from organisms (coal, chalk, some limestone)
- Lithification: compaction and cementation

### Metamorphic
- Formed from existing rocks under heat and pressure
- Foliated: banded (slate, schist, gneiss)
- Non-foliated: no banding (marble, quartzite)
- Contact metamorphism: near igneous intrusion
- Regional metamorphism: large-scale, mountain building

## Rock Identification
- Igneous: interlocking crystals, no fossils
- Sedimentary: layers, fossils, rounded grains
- Metamorphic: foliation, recrystallization

## Minerals (Mohs Hardness)
1. Talc
2. Gypsum
3. Calcite
4. Fluorite
5. Apatite
6. Orthoclase
7. Quartz
8. Topaz
9. Corundum
10. Diamond

## Earth Structure
- Crust: 5-70 km (continental thicker)
- Mantle: to 2900 km
- Outer core: liquid, 2900-5100 km
- Inner core: solid, 5100-6371 km
- Discontinuities: Moho, Gutenberg, Lehmann

## Common Pitfalls
- Confusing magma and lava
- Thinking all mountains form the same way
- Assuming rocks are permanent (they cycle)
- Confusing mineral with rock
- Not recognizing that continents move
""",
            "tags": ["geology", "plate tectonics", "rock cycle", "igneous", "sedimentary", "metamorphic", "reference"],
        }
    ],
    "natural_sciences_meteorology": [
        {
            "title": "Weather Systems and Forecasting Reference",
            "content": """# Weather Systems and Forecasting Reference

## Atmospheric Structure
- Troposphere: 0-12 km, weather occurs here, T decreases with altitude
- Tropopause: boundary, stops convection
- Stratosphere: 12-50 km, ozone layer, T increases
- Mesosphere: 50-85 km, meteors burn up
- Thermosphere: 85-600 km, aurora, high T but low density
- Exosphere: 600+ km, merges with space

## Pressure and Wind
- Pressure gradient force: air flows high to low
- Coriolis effect: deflects right (NH), left (SH)
- Geostrophic wind: balance of pressure gradient and Coriolis
- Surface friction: slows wind, causes convergence into lows
- Jet stream: fast current at tropopause, ~10-15 km altitude

## Air Masses
- Continental polar (cP): cold, dry
- Continental tropical (cT): hot, dry
- Maritime polar (mP): cool, moist
- Maritime tropical (mT): warm, moist

## Fronts
- Cold front: cold air pushes under warm; steep, fast, thunderstorms
- Warm front: warm air over cold; gradual, wide, steady rain
- Occluded front: cold catches warm; complex weather
- Stationary front: no movement; prolonged weather

## Low Pressure Systems
- Mid-latitude cyclone: polar front, wave cyclone
- Stages: cyclogenesis, mature, occluded, dissipation
- Counterclockwise rotation (NH)
- Warm and cold sectors

## Tropical Systems
- Tropical depression: < 39 mph
- Tropical storm: 39-73 mph
- Hurricane/typhoon: >= 74 mph
- Categories (Saffir-Simpson): 1-5
- Eye: calm center; eyewall: strongest winds
- Require warm water (> 26.5 C), Coriolis, low shear

## Severe Weather
- Thunderstorm: cumulonimbus, lightning, heavy rain
- Tornado: vortex, Enhanced Fujita scale EF0-EF5
- Downburst: damaging straight-line winds
- Hail: ice in updrafts
- Lightning: electrical discharge, ~300,000 V/m

## Forecasting
- Numerical weather prediction: solve equations on computers
- Models: GFS, ECMWF, NAM, WRF
- Ensemble: multiple runs with perturbations
- Data assimilation: incorporate observations
- Verification: compare forecast to actual

## Common Pitfalls
- Confusing weather with climate
- Not accounting for uncertainty in forecasts
- Assuming high pressure always means good weather
- Forgetting Coriolis effect direction by hemisphere
- Not understanding model resolution limits
""",
            "tags": ["meteorology", "weather", "fronts", "hurricane", "forecasting", "reference"],
        }
    ],
    "natural_sciences_environmental_science": [
        {
            "title": "Environmental Cycles and Climate Reference",
            "content": """# Environmental Cycles and Climate Reference

## Carbon Cycle
- Photosynthesis: CO2 + H2O -> glucose + O2
- Respiration: glucose + O2 -> CO2 + H2O + energy
- Combustion: burning releases CO2
- Decomposition: breaks down organic matter, releases CO2/CH4
- Ocean uptake: CO2 dissolves, forms carbonic acid
- Sedimentation: burial of organic matter -> fossil fuels
- Human impact: burning fossil fuels releases stored carbon

## Nitrogen Cycle
- Fixation: N2 -> NH3 (bacteria, lightning, industrial)
- Nitrification: NH3 -> NO2- -> NO3- (bacteria)
- Assimilation: plants take up NO3-
- Denitrification: NO3- -> N2 (bacteria, anaerobic)
- Human impact: fertilizers, runoff, eutrophication

## Water Cycle
- Evaporation: liquid to gas (oceans main source)
- Transpiration: plants release water vapor
- Condensation: gas to liquid (clouds)
- Precipitation: rain, snow, hail
- Infiltration: water enters soil
- Runoff: water flows over surface
- Human impact: dams, irrigation, pollution

## Phosphorus Cycle
- Weathering: releases phosphate from rocks
- Uptake: plants absorb from soil
- Consumption: animals eat plants
- Decomposition: returns to soil
- Sedimentation: ocean burial -> rock (long time scale)
- No gaseous phase (unlike C, N)

## Climate System

### Greenhouse Effect
- Solar radiation: ~340 W/m2 at top of atmosphere
- Albedo: ~30% reflected
- Greenhouse gases absorb infrared: CO2, CH4, H2O, N2O, O3
- Natural greenhouse effect: +33 C
- Enhanced: human-caused increase

### Climate Feedbacks
- Positive: ice-albedo (warming -> less ice -> more absorption -> more warming)
- Positive: water vapor (warmer air holds more, traps more heat)
- Negative: cloud (some types cool)
- Negative: silicate weathering (CO2 removal over geologic time)

### IPCC Projections
- RCP 2.6: aggressive mitigation, ~2 C warming
- RCP 4.5: moderate, ~2.5-3 C
- RCP 6.0: ~3-4 C
- RCP 8.5: business as usual, ~4-5 C+
- SSP scenarios (AR6): updated pathways

### Impacts
- Sea level rise: thermal expansion + ice melt
- Ocean acidification: CO2 -> carbonic acid
- Extreme weather: more intense hurricanes, heat waves
- Ecosystem shifts: species migration, coral bleaching
- Agricultural impacts: crop yields, water availability

## Common Pitfalls
- Confusing weather with climate
- Thinking CO2 is the only greenhouse gas
- Ignoring feedbacks
- Assuming natural cycles negate human impact
- Confusing ozone hole with greenhouse effect
""",
            "tags": ["environmental science", "carbon cycle", "nitrogen cycle", "water cycle", "climate", "reference"],
        }
    ],
    "natural_sciences_atmospheric_science": [
        {
            "title": "Atmospheric Physics and Chemistry Reference",
            "content": """# Atmospheric Physics and Chemistry Reference

## Atmospheric Composition
- N2: 78.08%
- O2: 20.95%
- Ar: 0.93%
- CO2: ~0.042% (420 ppm, rising)
- Ne, He, CH4, Kr, H2: trace
- Water vapor: 0-4% (variable)

## Atmospheric Pressure
- Decreases exponentially with altitude
- P = P0 e^{-z/H} where H ~ 8.4 km (scale height)
- Sea level: 1013.25 hPa
- Half of atmosphere below ~5.5 km

## Temperature Profile
- Troposphere: decreases 6.5 C/km (lapse rate)
- Tropopause: ~-56 C
- Stratosphere: increases (ozone absorption)
- Stratopause: ~-2 C
- Mesosphere: decreases (coldest, ~-90 C)
- Mesopause
- Thermosphere: increases (absorbs high energy)

## Radiation

### Solar
- Sun emits ~5778 K blackbody
- Peak: ~500 nm (visible)
- Total: 1361 W/m2 at top (solar constant)
- Average: 340 W/m2 at surface (after geometry)

### Terrestrial
- Earth emits ~288 K blackbody
- Peak: ~15 micrometers (infrared)
- Greenhouse gases absorb in this range

### Radiative Transfer
- Beer-Lambert law: I = I0 e^{-tau}
- Optical depth: tau = integral sigma n ds
- Absorption, emission, scattering

## Ozone
- Stratospheric: protective, absorbs UV (200-310 nm)
- Chapman cycle: O2 + UV -> 2O; O + O2 -> O3
- Catalytic destruction: NOx, ClOx (CFCs)
- Ozone hole: Antarctic spring, polar stratospheric clouds
- Montreal Protocol (1987): phased out CFCs

## Atmospheric Chemistry

### Tropospheric Ozone
- Pollutant, not emitted directly
- NOx + VOC + sunlight -> O3
- Smog: ozone, PAN, aldehydes
- Health effects: respiratory

### Acid Rain
- SO2 + H2O -> H2SO4
- NOx + H2O -> HNO3
- pH < 5.6
- Effects: lakes, forests, buildings

### Aerosols
- Natural: sea salt, dust, volcanic
- Anthropogenic: sulfate, soot, biomass burning
- Direct effect: scatter/absorb radiation
- Indirect effect: cloud condensation nuclei
- Cooling (sulfate) or warming (soot)

## Clouds
- Cumulus: puffy, fair weather
- Cumulonimbus: thunderstorm
- Stratus: layered, drizzle
- Cirrus: high, wispy, ice
- Fog: stratus at ground

## Common Pitfalls
- Confusing stratospheric (good) with tropospheric (bad) ozone
- Thinking all aerosols cool (soot warms)
- Confusing solar constant with surface insolation
- Forgetting water vapor is a greenhouse gas
- Not distinguishing weather from climate
""",
            "tags": ["atmospheric science", "atmosphere", "ozone", "radiation", "chemistry", "reference"],
        }
    ],
}

NATURAL_K3_BATCH3: dict[str, list[dict]] = {
    "natural_sciences_oceanography": [
        {
            "title": "Ocean Circulation and Marine Systems Reference",
            "content": """# Ocean Circulation and Marine Systems Reference

## Ocean Structure
- Surface layer: 0-200 m, warm, mixed by wind
- Thermocline: 200-1000 m, rapid temperature decrease
- Deep ocean: below 1000 m, cold (~2-4 C), dark
- Average depth: ~3.7 km
- Maximum: Mariana Trench ~11 km

## Surface Currents
- Wind-driven
- Gyres: circular currents in each ocean basin
  - North Atlantic, South Atlantic, North Pacific, South Pacific, Indian
- Western boundary currents: fast, warm (Gulf Stream, Kuroshio)
- Eastern boundary currents: slow, cold (California, Canary)
- Ekman transport: Coriolis causes 90 degree deflection
- Upwelling: deep nutrient-rich water rises
- Downwelling: surface water sinks

## Deep Circulation
- Thermohaline: density-driven (temperature + salinity)
- Global conveyor belt: ~1000 years for full cycle
- North Atlantic Deep Water: forms near Greenland
- Antarctic Bottom Water: densest, forms near Antarctica
- Pacific Deep Water

## Waves
- Generated by wind
- Speed depends on wavelength and depth
- Deep water: c = sqrt(g lambda / 2 pi)
- Shallow water: c = sqrt(g h)
- Break when height/depth ratio exceeds ~0.78
- Tsunami: long wavelength, fast, generated by earthquakes

## Tides
- Caused by Moon and Sun gravity
- Semidiurnal: 2 highs, 2 lows per day
- Diurnal: 1 high, 1 low
- Mixed: combination
- Spring tide: Sun and Moon aligned (highest highs, lowest lows)
- Neap tide: Sun and Moon at right angle (lower highs, higher lows)
- Tidal range: difference between high and low

## El Nino / La Nina
- ENSO: El Nino-Southern Oscillation
- Normal: trade winds push warm water west, upwelling east
- El Nino: trade winds weaken, warm water moves east
- La Nina: stronger than normal, more upwelling
- Global weather impacts: droughts, floods

## Marine Ecosystems
- Coral reefs: tropical, high biodiversity
- Estuaries: river meets sea, nurseries
- Kelp forests: temperate, productive
- Hydrothermal vents: chemosynthesis, unique life
- Open ocean: phytoplankton base
- Deep sea: dark, cold, high pressure

## Ocean Acidification
- CO2 + H2O <-> H2CO3 <-> H+ + HCO3- <-> 2H+ + CO3^2-
- pH decreased from 8.2 to 8.1 since industrial era
- Affects calcifying organisms (corals, shellfish)
- Projected: pH 7.8-7.9 by 2100 if CO2 continues

## Common Pitfalls
- Confusing surface currents with deep circulation
- Thinking tides are only from the Moon
- Assuming oceans are uniform
- Forgetting ocean's role in climate (heat transport)
- Confusing tsunami with tidal wave
""",
            "tags": ["oceanography", "currents", "tides", "ENSO", "coral", "reference"],
        }
    ],
    "natural_sciences_space_science": [
        {
            "title": "Space Physics and Exploration Reference",
            "content": """# Space Physics and Exploration Reference

## Solar Wind
- Stream of charged particles from Sun
- Speed: 300-800 km/s
- Composition: mostly protons and electrons
- Origin: solar corona (~1-2 million K)
- Interplanetary magnetic field (IMF): carried by solar wind

## Magnetosphere
- Region where planetary magnetic field dominates
- Bow shock: where solar wind slows
- Magnetopause: boundary of magnetosphere
- Magnetotail: extends away from Sun
- Van Allen belts: trapped radiation (inner: protons, outer: electrons)
- Auroras: particles excite atmosphere (northern/southern lights)

## Space Weather
- Solar flares: X-ray bursts (minutes)
- Coronal mass ejections (CME): plasma clouds (1-3 days to Earth)
- Geomagnetic storms: disturb magnetic field
- Effects: satellite damage, power grid, GPS, radiation hazard
- Prediction: satellite monitors (SOHO, ACE, DSCOVR)

## Plasma Physics
- Plasma: ionized gas, fourth state of matter
- Most of universe is plasma
- Magnetic fields confine and guide plasma
- Frozen-in field lines: field moves with plasma
- Reconnection: field lines break and reconnect (energy release)

## Orbital Mechanics
- Kepler's laws:
  1. Orbits are ellipses with Sun at focus
  2. Equal areas in equal times
  3. T^2 proportional to a^3
- Escape velocity: v = sqrt(2GM/r)
- Geostationary: 35,786 km, 24 hour period
- LEO: 200-2000 km, ~90 min period
- Hohmann transfer: efficient orbit change
- Gravity assist: use planet to change velocity

## Space Exploration Milestones
- 1957: Sputnik 1 (first satellite)
- 1961: Gagarin (first human in space)
- 1969: Apollo 11 (Moon landing)
- 1977: Voyager 1 & 2 launched
- 1990: Hubble Space Telescope
- 1998: ISS construction begins
- 2004: Spirit and Opportunity (Mars)
- 2012: Curiosity (Mars)
- 2015: New Horizons (Pluto)
- 2021: Perseverance, Ingenuity helicopter, JWST launch

## Rocket Propulsion
- Tsiolkovsky equation: delta_v = v_e ln(m0/m1)
- Chemical: liquid (LOX/RP-1, LOX/LH2), solid
- Ion: low thrust, high Isp (Dawn, Deep Space 1)
- Nuclear thermal: tested, not flown
- Solar sail: radiation pressure (LightSail, IKAROS)

## Common Pitfalls
- Thinking space is empty (has plasma, radiation)
- Confusing escape velocity with orbital velocity
- Assuming rockets need to push against something
- Forgetting time delay in communication
- Not accounting for radiation effects on electronics
""",
            "tags": ["space science", "solar wind", "magnetosphere", "orbital mechanics", "exploration", "reference"],
        }
    ],
    "natural_sciences_paleontology": [
        {
            "title": "Fossilization and Evolution Reference",
            "content": """# Fossilization and Evolution Reference

## Fossilization Processes

### Conditions
- Rapid burial (prevents decay)
- Anoxic environment (limits decomposition)
- Hard parts (bones, shells, teeth) preserve better
- Rare: soft tissue preservation (Lagerstatten)

### Types
- Permineralization: minerals fill pores (petrified wood)
- Replacement: original material replaced (pyritized fossils)
- Cast and mold: impression filled or left
- Carbonization: organic material compressed to film
- Recrystallization: original mineral changes form
- Unaltered: frozen, amber, mummified

### Trace Fossils
- Tracks and trails
- Burrows
- Coprolites (fossilized feces)
- Gastroliths (stomach stones)
- Bite marks
- Borings

## Taphonomy
- Study of processes from death to fossil
- Necrology: death and decay
- Biostratinomy: burial processes
- Diagenesis: chemical changes after burial
- Biases: selective preservation (hard parts, certain environments)

## Geological Time Scale

### Eons
- Hadean: 4.6-4.0 Ga (no life)
- Archean: 4.0-2.5 Ga (first life, prokaryotes)
- Proterozoic: 2.5 Ga - 541 Ma (eukaryotes, multicellular)
- Phanerozoic: 541 Ma - present (visible life)

### Eras of Phanerozoic
- Paleozoic: 541-252 Ma
  - Cambrian: explosion of life
  - Ordovician, Silurian: fish, land plants
  - Devonian: "age of fish", amphibians
  - Carboniferous: forests, reptiles
  - Permian: ended with largest extinction
- Mesozoic: 252-66 Ma
  - Triassic: first dinosaurs, mammals
  - Jurassic: dinosaurs dominate
  - Cretaceous: ended with K-Pg extinction
- Cenozoic: 66 Ma - present
  - Paleogene: mammals diversify
  - Neogene: hominids appear
  - Quaternary: ice ages, humans

## Mass Extinctions
1. Ordovician-Silurian (~445 Ma): 85% species, glaciation
2. Late Devonian (~375 Ma): 75%, ocean anoxia
3. Permian-Triassic (~252 Ma): 96%, largest; volcanism, climate
4. Triassic-Jurassic (~201 Ma): 80%, volcanism
5. Cretaceous-Paleogene (~66 Ma): 76%, asteroid impact (Chicxulub)

## Evolution
- Natural selection: variation, inheritance, differential survival
- Speciation: allopatric (geographic isolation), sympatric
- Adaptive radiation: rapid diversification (Darwin's finches)
- Convergent evolution: similar traits independently (wings)
- Coevolution: reciprocal evolution (predator-prey, pollinators)
- Punctuated equilibrium: rapid change, then stasis (Gould, Eldredge)

## Key Transitional Fossils
- Tiktaalik: fish-tetrapod transition
- Archaeopteryx: dinosaur-bird
- Pakicetus: land mammal-whale
- Australopithecus: ape-human

## Common Pitfalls
- Thinking fossil record is complete (it's very incomplete)
- Assuming evolution is directional (it's not)
- Confusing transitional forms with direct ancestors
- Thinking extinction is always bad (it opens niches)
- Forgetting taphonomic biases
""",
            "tags": ["paleontology", "fossilization", "evolution", "extinction", "geological time", "reference"],
        }
    ],
}

NATURAL_K3_BATCH4: dict[str, list[dict]] = {
    "natural_sciences_ecology": [
        {
            "title": "Ecosystem Dynamics and Biodiversity Reference",
            "content": """# Ecosystem Dynamics and Biodiversity Reference

## Trophic Structure
- Producers: autotrophs (plants, algae, cyanobacteria)
- Primary consumers: herbivores
- Secondary consumers: carnivores eating herbivores
- Tertiary consumers: top carnivores
- Decomposers: bacteria, fungi, break down dead matter
- Detritivores: eat detritus (earthworms, vultures)

## Energy Flow
- 10% rule: ~10% energy transferred between levels
- Energy pyramid: large base, small top
- Gross primary productivity (GPP): total photosynthesis
- Net primary productivity (NPP): GPP - respiration
- NPP available to consumers

## Biogeochemical Cycles
- Carbon: photosynthesis, respiration, combustion, ocean
- Nitrogen: fixation, nitrification, denitrification
- Phosphorus: weathering, uptake, sedimentation
- Water: evaporation, precipitation, runoff, infiltration

## Population Dynamics

### Growth Models
- Exponential: dN/dt = rN (unlimited)
- Logistic: dN/dt = rN(1 - N/K) (limited)
- Carrying capacity: K
- Overshoot and die-off

### Interactions
- Competition (-/-): both harmed
- Predation (+/-): predator benefits, prey harmed
- Parasitism (+/-): parasite benefits, host harmed
- Mutualism (+/+): both benefit
- Commensalism (+/0): one benefits, other unaffected

### Lotka-Volterra
- Predator-prey cycles
- dN/dt = rN - aNP (prey)
- dP/dt = baNP - mP (predator)
- Coupled oscillations

## Succession
- Primary: bare substrate (no soil) -> lichens -> mosses -> grasses -> shrubs -> trees
- Secondary: disturbed but soil remains -> grasses -> shrubs -> trees
- Climax community: stable end state
- Disturbance: fire, storm, logging resets succession

## Biodiversity

### Levels
- Genetic: variation within species
- Species: number of species
- Ecosystem: variety of habitats

### Measurement
- Species richness: number of species
- Species evenness: relative abundance
- Shannon index: H = -sum p_i ln p_i
- Simpson index: D = 1 - sum p_i^2

### Importance
- Ecosystem services: pollination, water purification, climate regulation
- Stability: diverse ecosystems more resilient
- Medicine: many drugs from nature
- Food security: genetic diversity in crops

### Threats
- HIPPO: Habitat loss, Invasive species, Pollution, Population, Overharvesting
- Climate change: shifting ranges, phenology mismatch
- Deforestation: especially tropical
- Fragmentation: isolates populations

## Biomes
- Tropical rainforest: warm, wet, high biodiversity
- Temperate forest: seasonal, deciduous
- Boreal (taiga): cold, coniferous
- Grassland: temperate, fire-maintained
- Savanna: tropical, seasonal
- Desert: <25 cm precipitation
- Tundra: cold, permafrost
- Wetland: saturated, high productivity
- Marine: coral reef, estuary, open ocean

## Common Pitfalls
- Assuming all ecosystems are stable (many are dynamic)
- Thinking biodiversity is just species count
- Ignoring ecosystem services
- Confusing richness with evenness
- Assuming competition is the only interaction
""",
            "tags": ["ecology", "ecosystems", "biodiversity", "trophic", "succession", "reference"],
        }
    ],
    "natural_sciences_hydrology": [
        {
            "title": "Water Resources and Watershed Dynamics Reference",
            "content": """# Water Resources and Watershed Dynamics Reference

## Hydrologic Cycle
- Evaporation: liquid to vapor (oceans main source)
- Transpiration: plants release vapor
- Condensation: vapor to liquid (clouds)
- Precipitation: rain, snow, hail, sleet
- Infiltration: water into soil
- Percolation: water through soil to groundwater
- Runoff: water over surface to streams
- Sublimation: solid to vapor (snow/ice)

## Water Balance
- P = ET + Q + delta S
- P: precipitation
- ET: evapotranspiration
- Q: streamflow (runoff)
- delta S: change in storage

## Watershed
- Drainage basin: area contributing to outlet
- Divide: boundary between watersheds
- Order: Strahler (1: no tributaries, 2: two 1s meet, etc.)
- Dendritic, rectangular, radial patterns

## Surface Water

### Rivers
- Discharge: Q = V A (velocity x area)
- Rating curve: stage-discharge relationship
- Flood: flow exceeding channel capacity
- Recurrence interval: 1/P (100-year flood = 1% chance/year)

### Lakes
- Oligotrophic: low nutrients, clear
- Mesotrophic: moderate
- Eutrophic: high nutrients, algae blooms
- Turnover: seasonal mixing

## Groundwater

### Aquifers
- Unconfined: water table as upper surface
- Confined: between impermeable layers
- Artesian: confined, pressurized water rises
- Porosity: fraction of void space
- Permeability: ease of flow
- Specific yield: drainable porosity

### Flow
- Darcy's law: Q = -K A dh/dl
- K: hydraulic conductivity
- dh/dl: hydraulic gradient
- Recharge: water entering aquifer
- Discharge: water leaving (springs, wells, baseflow)

### Wells
- Drawdown: water level drop during pumping
- Cone of depression: lowered water table around well
- Safe yield: sustainable extraction rate
- Overpumping: depletion, saltwater intrusion

## Water Quality
- Physical: temperature, turbidity, color
- Chemical: pH, dissolved oxygen, nutrients, metals
- Biological: coliform bacteria, pathogens
- Pollution: point (pipe), nonpoint (runoff)
- Treatment: filtration, chlorination, UV

## Water Management
- Dams: storage, flood control, hydropower
- Reservoirs: regulated release
- Irrigation: 70% of global freshwater use
- Virtual water: water embedded in products
- Water rights: prior appropriation, riparian

## Common Pitfalls
- Confusing porosity with permeability
- Thinking groundwater flows in underground rivers
- Assuming 100-year flood happens once per century
- Ignoring connection between surface and groundwater
- Not considering water quality, only quantity
""",
            "tags": ["hydrology", "water", "watershed", "groundwater", "aquifer", "reference"],
        }
    ],
    "natural_sciences_forestry": [
        {
            "title": "Forest Ecology and Management Reference",
            "content": """# Forest Ecology and Management Reference

## Forest Types

### Boreal (Taiga)
- Cold climate, short growing season
- Coniferous: spruce, fir, pine, larch
- Large carbon sink
- Fire-adapted

### Temperate
- Deciduous: oak, maple, beech, birch
- Mixed: coniferous + deciduous
- Distinct seasons
- Moderate biodiversity

### Tropical
- Rainforest: warm, wet, highest biodiversity
- Seasonal: dry season, leaf loss
- Montane: cooler, cloud forests
- Mangrove: coastal, salt-tolerant

## Forest Structure
- Overstory: dominant canopy trees
- Canopy: main tree layer
- Understory: small trees, shrubs
- Herb layer: non-woody plants
- Forest floor: litter, decomposers

## Silvicultural Systems

### Even-aged
- Clearcutting: remove all, regenerate naturally or planted
- Seed tree: leave few for seed
- Shelterwood: partial cuts to establish regeneration
- Coppice: sprouts from stumps

### Uneven-aged
- Single-tree selection: individual trees
- Group selection: small groups
- Maintains continuous canopy

## Forest Regeneration
- Natural: seed, sprout
- Artificial: planting seeds or seedlings
- Direct seeding: less common
- Nursery: containerized or bareroot

## Forest Measurements
- DBH: diameter at breast height (1.3 m)
- Basal area: cross-sectional area at DBH
- Volume: board foot, cubic meter
- Stand density: trees per area, basal area
- Site index: productivity based on height-age

## Fire Ecology
- Surface fire: understory, low intensity
- Crown fire: canopy, high intensity
- Ground fire: organic soil, smoldering
- Fire regime: frequency, intensity, season
- Fire suppression: 20th century policy, fuel buildup
- Prescribed fire: intentional, managed

## Forest Health
- Insects: bark beetles, defoliators
- Disease: fungi (Dutch elm, chestnut blight)
- Invasive species: emerald ash borer, gypsy moth
- Climate change: drought stress, range shifts
- Air pollution: acid rain, ozone

## Carbon Sequestration
- Forests: ~30% of land carbon
- Aboveground: biomass
- Belowground: roots, soil
- Products: wood, paper (temporary storage)
- REDD+: reducing emissions from deforestation

## Sustainable Forestry
- Sustained yield: harvest <= growth
- Certification: FSC, PEFC, SFI
- Biodiversity conservation
- Water protection: riparian buffers
- Soil protection: minimizing compaction

## Common Pitfalls
- Assuming all forests should be old growth
- Thinking clearcutting is always bad (some species need it)
- Ignoring soil carbon
- Not considering fire's natural role
- Confusing planting with restoration
""",
            "tags": ["forestry", "silviculture", "forest ecology", "fire", "carbon", "reference"],
        }
    ],
}

NATURAL_K3_BATCH5: dict[str, list[dict]] = {
    "natural_sciences_wildlife_science": [
        {
            "title": "Wildlife Population and Conservation Reference",
            "content": """# Wildlife Population and Conservation Reference

## Population Estimation
- Direct count: census (small populations)
- Mark-recapture: Lincoln-Petersen estimator
  - N = (M * C) / R (marked, captured, recaptured)
- Distance sampling: detectability decreases with distance
- Camera traps: capture-mark-recapture with photos
- Genetic sampling: DNA from scat, hair
- Aerial surveys: planes, drones

## Population Dynamics
- Birth rate (b), death rate (d)
- r = b - d (intrinsic rate)
- Immigration, emigration
- Lambda = N(t+1) / N(t) (finite rate)
- Stable: lambda = 1; growing: > 1; declining: < 1

### Life Tables
- x: age
- lx: survivorship to age x
- bx: fecundity at age x
- R0 = sum lx bx (net reproductive rate)
- Generation time: T = sum x lx bx / R0
- r approx ln(R0) / T

### Survivorship Curves
- Type I: high survival until old age (humans, elephants)
- Type II: constant mortality (birds)
- Type III: high early mortality (fish, insects, plants)

## Behavior
- Foraging: optimal foraging theory
- Mating: monogamy, polygyny, polyandry, promiscuity
- Territoriality: defend area for resources
- Migration: seasonal, navigation
- Communication: visual, auditory, chemical, tactile
- Social: groups, hierarchies, cooperation

## Conservation

### Threats
- Habitat loss: #1 threat
- Fragmentation: isolates populations
- Overexploitation: hunting, fishing, poaching
- Invasive species: competition, predation
- Climate change: range shifts, phenology
- Pollution: pesticides, plastics

### Small Population Issues
- Genetic drift: random allele loss
- Inbreeding depression: reduced fitness
- Allee effect: low density reduces reproduction
- Extinction vortex: downward spiral
- Minimum viable population (MVP)

### Conservation Strategies
- Protected areas: national parks, reserves
- Corridors: connect fragmented habitats
- Captive breeding: zoo programs
- Reintroduction: release into former range
- Habitat restoration: improve degraded land
- Translocation: move to new area

### International Agreements
- CITES: trade in endangered species
- Convention on Biological Diversity (CBD)
- Ramsar: wetlands
- Migratory Bird Treaty Act (US)

## Human-Wildlife Conflict
- Crop raiding: elephants, primates
- Livestock predation: wolves, big cats
- Vehicle collisions: deer, etc.
- Disease transmission: bats, rodents
- Solutions: fencing, compensation, deterrents, coexistence

## Common Pitfalls
- Assuming more habitat always means more wildlife
- Ignoring genetic diversity in small populations
- Translocating without considering disease
- Focusing on charismatic species only
- Not involving local communities
""",
            "tags": ["wildlife science", "population", "conservation", "behavior", "reference"],
        }
    ],
    "natural_sciences_materials_science": [
        {
            "title": "Material Properties and Characterization Reference",
            "content": """# Material Properties and Characterization Reference

## Mechanical Properties

### Stress-Strain
- Stress: sigma = F / A (Pa or MPa)
- Strain: epsilon = delta L / L (dimensionless)
- Young's modulus: E = sigma / epsilon (elastic region)
- Yield strength: stress where plastic deformation begins
- Ultimate tensile strength: maximum stress
- Ductility: elongation before fracture
- Toughness: energy absorbed before fracture (area under curve)

### Hardness
- Resistance to deformation
- Tests: Brinell, Vickers, Rockwell, Mohs
- Related to strength

### Fatigue
- Failure under cyclic loading
- Below yield strength
- S-N curve: stress vs cycles to failure
- Endurance limit: stress below which no fatigue (steels)

### Creep
- Slow deformation under constant stress
- Temperature-dependent (T > 0.4 T_m for metals)
- Three stages: primary, secondary, tertiary

## Thermal Properties
- Thermal conductivity: rate of heat flow
- Thermal expansion: delta L / L = alpha delta T
- Specific heat: energy to raise temperature
- Melting point
- Glass transition (polymers): Tg

## Electrical Properties
- Conductors: metals (free electrons)
- Insulators: ceramics, polymers
- Semiconductors: Si, Ge, GaAs
  - Band gap: energy to excite electron
  - Doping: n-type (extra electrons), p-type (holes)
  - Diode: p-n junction, one-way current
  - Transistor: amplify or switch
- Superconductors: zero resistance below Tc

## Magnetic Properties
- Ferromagnetic: strongly magnetic (Fe, Ni, Co)
- Paramagnetic: weakly attracted
- Diamagnetic: weakly repelled
- Curie temperature: ferromagnetic -> paramagnetic
- Hysteresis: lag in magnetization

## Crystal Structures

### Bravais Lattices (14)
- Cubic: simple, BCC, FCC
- Tetragonal: simple, BCT
- Orthorhombic: simple, base-centered, BCC, FCC
- Monoclinic, triclinic, hexagonal, rhombohedral

### Common Metal Structures
- BCC: Fe (alpha), Cr, W
- FCC: Al, Cu, Au, Ag, Fe (gamma)
- HCP: Mg, Ti, Zn

### Defects
- Point: vacancies, interstitials, substitutions
- Line: dislocations (edge, screw)
- Planar: grain boundaries, stacking faults
- Volume: voids, cracks

## Material Processing
- Casting: pour liquid into mold
- Forging: shape with compressive force
- Rolling: reduce thickness
- Extrusion: push through die
- Sintering: heat powder below melting
- Heat treatment: anneal, quench, temper

## Characterization Techniques
- XRD: crystal structure, phases
- SEM: surface morphology
- TEM: internal structure, atomic resolution
- DSC: thermal transitions
- TGA: thermal decomposition
- Tensile test: mechanical properties
- Spectroscopy: chemical composition

## Common Pitfalls
- Confusing strength and toughness
- Not considering temperature effects
- Ignoring defects in real materials
- Assuming bulk properties apply at nanoscale
- Not accounting for processing history
""",
            "tags": ["materials science", "properties", "crystal structure", "characterization", "reference"],
        }
    ],
    "natural_sciences_nanoscience": [
        {
            "title": "Nanomaterials and Nanofabrication Reference",
            "content": """# Nanomaterials and Nanofabrication Reference

## Why Nanoscale is Different
- Surface area to volume ratio: increases as size decreases
- Quantum confinement: energy levels discrete at nanoscale
- Surface energy dominates
- New properties emerge (color, melting point, reactivity)

## Types of Nanomaterials

### Zero-dimensional (0D)
- Nanoparticles: 1-100 nm
- Quantum dots: semiconductor nanocrystals
  - Size-tunable band gap
  - Fluorescence color depends on size
  - Applications: displays, solar cells, bioimaging

### One-dimensional (1D)
- Nanowires: high aspect ratio
- Nanotubes: hollow
  - Carbon nanotubes (CNT): single-wall (SWCNT), multi-wall (MWCNT)
  - Metallic or semiconducting depending on chirality
  - Strength: ~100x steel, lightweight
- Nanorods

### Two-dimensional (2D)
- Graphene: single layer of carbon, hexagonal
  - 200x stronger than steel
  - Excellent conductor
  - Transparent, flexible
- MoS2, h-BN, phosphorene
- MXenes: transition metal carbides

### Three-dimensional (3D)
- Nanocomposites: nanoparticles in matrix
- Nanoporous materials: zeolites, MOFs
- Dendrimers: branched polymers

## Nanofabrication

### Top-Down
- Photolithography: UV light through mask
  - Resolution: ~lambda/2 (diffraction limit)
  - EUV: 13.5 nm wavelength
- Electron beam lithography: finer features
- Focused ion beam: direct write
- Etching: wet (chemical), dry (plasma)

### Bottom-Up
- Self-assembly: spontaneous organization
- Chemical synthesis: grow from molecules
- Atomic layer deposition (ALD): one layer at a time
- Molecular beam epitaxy (MBE): precise crystal growth
- CVD: chemical vapor deposition (graphene, CNTs)

## Characterization at Nanoscale

### Microscopy
- STM: scanning tunneling, images atoms (conductors)
- AFM: atomic force, any surface
- SEM: scanning electron, surface morphology
- TEM: transmission electron, internal structure

### Spectroscopy
- XPS: X-ray photoelectron, surface composition
- EDS: energy dispersive X-ray, elemental analysis
- Raman: vibrational modes
- UV-Vis: optical properties

### Surface Area
- BET: gas adsorption, specific surface area

## Applications

### Electronics
- Smaller transistors (Moore's law)
- Quantum computing: quantum dots as qubits
- Flexible electronics: nanowires, graphene

### Medicine
- Drug delivery: targeted nanoparticles
- Imaging: quantum dots, gold nanoparticles
- Biosensors: nanowire FETs
- Tissue engineering: nanofibers

### Energy
- Solar cells: nanostructured for efficiency
- Batteries: nanomaterial electrodes
- Catalysis: high surface area
- Hydrogen storage: MOFs

### Environment
- Water filtration: nanoporous membranes
- Sensors: pollutant detection
- Remediation: nanoparticles for cleanup

## Safety and Ethics
- Nanotoxicology: health effects unknown for many materials
- Penetration: can enter cells, cross blood-brain barrier
- Environmental: persistence, bioaccumulation
- Regulation: evolving, limited specific standards
- Responsible development: assess risks

## Common Pitfalls
- Assuming nanomaterials behave like bulk materials
- Not considering aggregation
- Ignoring surface chemistry effects
- Overhyping applications before testing
- Not assessing toxicity
""",
            "tags": ["nanoscience", "nanomaterials", "nanofabrication", "quantum dots", "graphene", "reference"],
        }
    ],
}
