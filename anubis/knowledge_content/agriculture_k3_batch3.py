"""Agriculture & Food K3 Batch 3 - 2 specialties."""

AGRICULTURE_K3_BATCH3: dict[str, list[dict]] = {
    "agriculture_food_safety": [
        {"title": "Food Safety Practice Reference", "content": """# Food Safety Practice Reference

## Foodborne Hazards
### Biological
- Bacteria:
  - Salmonella: poultry, eggs
  - E. coli O157:H7: beef, produce
  - Listeria monocytogenes: deli, dairy
  - Campylobacter: poultry
  - Clostridium botulinum: canned
  - Staphylococcus aureus: toxin
  - Bacillus cereus: rice
  - Vibrio: seafood
- Viruses:
  - Norovirus: most common
  - Hepatitis A: shellfish
  - Rotavirus
- Parasites:
  - Toxoplasma: meat
  - Trichinella: pork
  - Cryptosporidium: water
  - Giardia: water
- Prions: BSE

### Chemical
- Natural toxins: mycotoxins (aflatoxin), histamine, ciguatera
- Agricultural: pesticides, veterinary drugs
- Environmental: heavy metals (lead, mercury, cadmium)
- Processing: cleaners, sanitizers
- Allergens: milk, egg, fish, shellfish, tree nut, peanut, wheat, soy, sesame

### Physical
- Metal: fragments
- Glass: shards
- Plastic: pieces
- Stone: field
- Wood: splinters
- Bone: fragments
- Hair: human

## HACCP (Hazard Analysis Critical Control Point)
### Principles
1. Conduct hazard analysis
2. Determine critical control points (CCPs)
3. Establish critical limits
4. Monitor CCPs
5. Establish corrective actions
6. Verify
7. Record-keep

### CCPs
- Cooking: temperature
- Cooling: time
- pH: acidification
- Water activity: drying
- Metal detection: foreign

### Flow
- Receiving: inspect
- Storage: temperature
- Preparation: handle
- Process: control
- Packaging: protect
- Storage: hold
- Transport: ship

## Temperature Control
### Danger Zone
- 40-140F (4-60C): bacteria grow
- 41-135F (FDA Food Code)

### Cooking
- Poultry: 165F (74C)
- Ground meat: 155F (68C)
- Pork, beef, fish: 145F (63C)
- Eggs: 145F (63C)
- Reheat: 165F (74C)

### Cooling
- 135F to 70F: within 2 hours
- 70F to 41F: within 4 more hours
- Total: 6 hours max
- Methods: shallow pan, ice bath, blast chiller

### Cold Holding
- 41F (5C) or below

### Hot Holding
- 135F (57C) or above

## Hygiene
### Personal
- Handwashing: 20 seconds
  - After: bathroom, eating, touching face, raw food, trash
  - Before: food prep, gloves
- Clothing: clean
- Hair: restrained
- Jewelry: minimal
- Illness: report
- Cuts: cover

### Facility
- Clean: surfaces
- Sanitize: reduce microbes
- Pest: control
- Waste: manage
- Water: potable
- Plumbing: proper

## Cross-Contamination
### Types
- Direct: food to food
- Indirect: surface, hands, equipment
- Drip: raw above ready

### Prevention
- Separate: raw and ready
- Color code: cutting boards
- Wash: between tasks
- Store: cover, order (raw below)
- Utensils: separate

## Allergen Management
### Big 9 (US)
- Milk
- Egg
- Fish
- Shellfish (crustacean)
- Tree nuts
- Peanuts
- Wheat
- Soybeans
- Sesame (added 2023)

### Management
- Identify: ingredients
- Label: declare
- Prevent: cross-contact
- Clean: between
- Train: staff
- Separate: storage, production

## Cleaning and Sanitizing
### Cleaning
- Remove: soil
- Detergent: chemical
- Mechanical: scrub
- Heat: hot water
- Rinse: remove

### Sanitizing
- Reduce: microbes
- Chemical: chlorine, quat, iodine
- Heat: hot water (171F)
- Contact: time
- Concentration: test

### Schedule
- Daily: food contact
- Weekly: non-contact
- Monthly: deep
- As needed: spill

## Regulations
### US Federal
- FDA: most foods
- USDA-FSIS: meat, poultry, eggs
- CDC: surveillance
- EPA: pesticides, water

### Food Safety Modernization Act (FSMA)
- Preventive controls: human food
- Produce safety: growing
- Foreign supplier: import
- Sanitary transport
- Intentional adulteration

### Codex Alimentarius
- International standards
- Guidelines
- Codes of practice

## Inspection
### Types
- Routine: scheduled
- For-cause: complaint, illness
- Pre-op: before production
- In-process: during
- Self: internal
- Third-party: audit

### HACCP Verification
- Records: review
- Calibration: instruments
- Observation: monitor
- Testing: product

## Outbreak Investigation
### Steps
1. Detect: surveillance
2. Identify: cases
3. Hypothesize: source
4. Test: hypothesis
5. Control: implement
6. Communicate: public

### Traceback
- Source: find
- Distribution: track
- Recall: remove

## Recall
### Classes
- Class I: reasonable probability of serious adverse health consequences or death
- Class II: temporary or medically reversible adverse health consequences
- Class III: not likely to cause adverse health consequences

### Process
- Identify: problem
- Notify: regulator
- Press release: public
- Remove: product
- Correct: cause

## Common Pitfalls
- Not following HACCP
- Poor temperature control
- Cross-contamination
- Poor personal hygiene
- Not managing allergens
- Inadequate cleaning
- Not training staff
""", "tags": ["food safety", "HACCP", "pathogens", "allergens", "regulations", "reference"]}
    ],
    "agriculture_culinary_science": [
        {"title": "Culinary Science Reference", "content": """# Culinary Science Reference

## Cooking Methods
### Dry Heat
- Roasting: oven, air
- Baking: oven, baked goods
- Grilling: open flame
- Broiling: top heat
- Sautéing: pan, little fat
- Pan-frying: pan, more fat
- Deep-frying: submerged
- Stir-frying: wok, fast

### Moist Heat
- Boiling: water, 212F
- Simmering: water, 185-205F
- Poaching: liquid, 160-180F
- Steaming: vapor
- Braising: brown + simmer
- Stewing: simmer in liquid

### Combination
- Braising: dry + moist
- Stewing: small pieces
- Sous vide: vacuum, water bath

## Heat Transfer
### Conduction
- Direct contact
- Pan to food
- Slow

### Convection
- Fluid movement
- Oven air, boiling water
- Faster

### Radiation
- Electromagnetic waves
- Grill, broiler, microwave
- No medium

## Chemical Reactions
### Maillard Reaction
- Amino acid + sugar
- Brown color
- Complex flavor
- Above 285F (140C)
- Examples: bread crust, sear

### Caramelization
- Sugar decomposition
- Brown color
- Sweet, complex
- Above 320F (160C)
- Examples: caramel, onion

### Gelatinization
- Starch + water + heat
- Swell, thicken
- 140-160F (60-70C)
- Examples: gravy, sauce

### Coagulation
- Protein denature + aggregate
- Solidify
- 140-180F (60-82C)
- Examples: egg, meat

### Fermentation
- Microbe + food
- Transform
- Examples: bread, cheese, wine, yogurt

## Flavor
### Taste
- Sweet: sugar
- Sour: acid
- Salty: salt
- Bitter: alkaloid
- Umami: glutamate
- Fat: new

### Aroma
- Volatile compounds
- Retronasal: mouth to nose
- Orthonasal: direct
- Thousands: distinguishable

### Texture
- Mouthfeel: physical
- Crisp, crunchy, chewy, smooth
- Temperature: affect

### Flavor Pairing
- Complement: similar
- Contrast: different
- Bridge: connect
- Cultural: tradition

## Ingredients
### Proteins
- Meat: muscle
- Fish: muscle
- Egg: protein
- Dairy: casein, whey
- Legume: plant
- Function: structure, gel, foam

### Carbohydrates
- Sugar: sweet, brown
- Starch: thicken
- Flour: structure
- Cellulose: fiber
- Pectin: gel

### Fats
- Butter: dairy, flavor
- Oil: plant
- Lard: pork
- Shortening: solid
- Function: tender, flavor, transfer heat

### Leavening
- Air: mechanical
- Steam: water
- Yeast: biological
- Baking soda: + acid
- Baking powder: + heat

## Techniques
### Thickening
- Roux: flour + fat
- Slurry: starch + cold water
- Reduction: evaporate
- Emulsion: suspend
- Gelatin: set

### Emulsions
- Oil in water: vinaigrette
- Water in oil: butter
- Stable: emulsifier (egg yolk, mustard)
- Temporary: separate
- Permanent: stable

### Stocks
- Mirepoix: onion, carrot, celery
- Bones: flavor, gelatin
- Water: extract
- Simmer: time
- Skim: impurities

### Sauces
- Mother: 5 (espagnole, velouté, béchamel, tomato, hollandaise)
- Small: derivative
- Pan: deglaze
- Reduction: concentrate

## Molecular Gastronomy
### Techniques
- Spherification: gel sphere
- Foams: stabilized
- Gels: hydrocolloid
- Liquid nitrogen: freeze
- Sous vide: precise
- Smoking: flavor

### Hydrocolloids
- Agar: gel
- Alginate: gel (with calcium)
- Gelatin: gel
- Xanthan: thicken
- Carrageenan: gel

## Baking
### Bread
- Flour, water, yeast, salt
- Knead: develop gluten
- Ferment: rise
- Proof: final rise
- Bake: oven
- Crust: Maillard

### Cake
- Flour, sugar, egg, fat, leavening
- Cream: fat + sugar
- Mix: incorporate
- Bake: rise, set

### Pastry
- Flour, fat, water
- Pie: crust
- Puff: layers
- Choux: steam leavened

## Sensory Evaluation
### Professional
- Trained panel
- Descriptive: profile
- Difference: detect

### Consumer
- Hedonic: like
- Preference: choose
- Acceptance: rate

## Common Pitfalls
- Overcooking
- Under-seasoning
- Wrong temperature
- Not resting meat
- Overworking dough
- Not balancing flavors
- Poor ingredient quality
""", "tags": ["culinary science", "cooking", "flavor", "baking", "molecular", "reference"]}
    ],
}
