"""Agriculture & Food K1 - 12 specialties in 5 batches (3+3+2+2+2)."""

AGRICULTURE_K1_BATCH1: dict[str, list[dict]] = {
    "agriculture_agronomy": [
        {"title": "Agronomy - Field Overview", "content": """# Agronomy

## Definition
Agronomy is the science and technology of producing and using plants for food, fuel, fiber, and land reclamation.

## Core Areas
- Crop production: yield
- Soil management: fertility
- Plant breeding: varieties
- Pest management: weeds, insects, disease
- Water management: irrigation
- Precision agriculture: technology

## Key Concepts
- Crop: cultivated plant
- Yield: harvest per area
- Rotation: alternate crops
- Monoculture: single crop
- Cover crop: protect soil
- Tillage: prepare soil
- Fertilizer: nutrients
- IPM: integrated pest management

## Foundational Texts
- Plaster, "Soil Science and Management"
- Acquaah, "Principles of Crop Production"

## Authority Note
Advisory. ASA, CSSA, SSSA professional; USDA resources.""", "tags": ["agronomy", "crops", "soil", "overview"]}
    ],
    "agriculture_horticulture": [
        {"title": "Horticulture - Field Overview", "content": """# Horticulture

## Definition
Horticulture is the art, science, technology, and business of cultivating plants for food and ornamental purposes.

## Core Areas
- Pomology: fruit
- Olericulture: vegetables
- Floriculture: flowers
- Landscape: ornamental
- Viticulture: grapes
- Turf: grass
- Postharvest: handling

## Key Concepts
- Cultivar: cultivated variety
- Propagation: reproduce
- Grafting: join plants
- Pruning: shape
- Greenhouse: controlled
- Hydroponics: water culture
- Pollination: fertilize
- Cultivation: grow

## Foundational Texts
- Hartmann et al., "Plant Propagation"
- Preece & Read, "The Biology of Horticulture"

## Authority Note
Advisory. ASHS professional; USDA extension.""", "tags": ["horticulture", "plants", "fruits", "vegetables", "overview"]}
    ],
    "agriculture_soil_science": [
        {"title": "Soil Science - Field Overview", "content": """# Soil Science

## Definition
Soil science is the study of soil as a natural resource on the surface of the Earth.

## Core Areas
- Pedology: soil formation
- Edaphology: soil use
- Soil physics: properties
- Soil chemistry: reactions
- Soil biology: organisms
- Soil fertility: nutrients
- Soil classification: taxonomy

## Key Concepts
- Horizon: soil layer
- Texture: sand, silt, clay
- Structure: arrangement
- Porosity: spaces
- Permeability: water flow
- pH: acidity
- Organic matter: humus
- CEC: cation exchange

## Foundational Texts
- Brady & Weil, "The Nature and Properties of Soils"
- Schaetzl & Thompson, "Soils"

## Authority Note
Advisory. SSSA professional; USDA-NRCS resources.""", "tags": ["soil science", "soil", "fertility", "overview"]}
    ],
}

AGRICULTURE_K1_BATCH2: dict[str, list[dict]] = {
    "agriculture_animal_science": [
        {"title": "Animal Science - Field Overview", "content": """# Animal Science

## Definition
Animal science is the study of the biology of animals under human control, particularly livestock.

## Core Areas
- Nutrition: feed
- Genetics: breeding
- Reproduction: production
- Health: disease
- Behavior: welfare
- Meat science: products
- Dairy: milk
- Poultry: birds

## Key Concepts
- Breed: variety
- Ration: diet
- Forage: plant feed
- Concentrate: grain
- Digestion: process
- Gestation: pregnancy
- Lactation: milk
- Carcass: meat

## Foundational Texts
- Damron, "Animal Science"
- Field & Taylor, "Scientific Farm Animal Production"

## Authority Note
Advisory. ASAS professional; USDA extension.""", "tags": ["animal science", "livestock", "nutrition", "overview"]}
    ],
    "agriculture_agricultural_engineering": [
        {"title": "Agricultural Engineering - Field Overview", "content": """# Agricultural Engineering

## Definition
Agricultural engineering is the engineering discipline that applies engineering principles to agricultural production and processing.

## Core Areas
- Machinery: equipment
- Irrigation: water systems
- Drainage: water removal
- Structures: buildings
- Power: energy
- Processing: post-harvest
- Precision ag: technology
- Waste: management

## Key Concepts
- Tractor: power unit
- Implement: tool
- Irrigation: water supply
- Drainage: remove excess
- Ventilation: air
- Biogas: energy
- Sensor: monitor
- Automation: control

## Foundational Texts
- Hunt, "Farm Power and Machinery Management"
- Kepner et al., "Principles of Farm Machinery"

## Authority Note
Advisory. ASABE professional; PE licensure.""", "tags": ["agricultural engineering", "machinery", "irrigation", "overview"]}
    ],
    "agriculture_food_science": [
        {"title": "Food Science - Field Overview", "content": """# Food Science

## Definition
Food science is the study of the physical, biological, and chemical makeup of food and the concepts underlying food processing.

## Core Areas
- Food chemistry: components
- Food microbiology: organisms
- Food processing: preservation
- Food engineering: production
- Sensory: perception
- Nutrition: health
- Product development: new

## Key Concepts
- Macronutrient: protein, carb, fat
- Micronutrient: vitamin, mineral
- Preservation: prevent spoilage
- Fermentation: microbial
- Pasteurization: heat
- Shelf life: duration
- Additive: enhance
- Texture: physical

## Foundational Texts
- Potter & Hotchkiss, "Food Science"
- Fennema, "Food Chemistry"

## Authority Note
Advisory. IFT professional; certification available.""", "tags": ["food science", "food chemistry", "processing", "overview"]}
    ],
}

AGRICULTURE_K1_BATCH3: dict[str, list[dict]] = {
    "agriculture_food_safety": [
        {"title": "Food Safety - Field Overview", "content": """# Food Safety

## Definition
Food safety encompasses the handling, preparation, and storage of food in ways that prevent foodborne illness.

## Core Areas
- Microbiological: bacteria, virus, parasite
- Chemical: contaminants, additives
- Physical: foreign objects
- Allergen: management
- HACCP: hazard analysis
- Inspection: regulatory
- Traceability: tracking

## Key Concepts
- Pathogen: disease-causing
- Contamination: unwanted
- Cross-contamination: transfer
- Temperature danger zone: 40-140F
- HACCP: control system
- Recall: remove product
- Outbreak: multiple cases
- FSO: food safety objective

## Foundational Texts
- Marriott & Gravani, "Principles of Food Sanitation"
- Forsythe, "The Microbiology of Safe Food"

## Authority Note
Advisory. FDA, USDA-FSIS regulatory; Codex standards.""", "tags": ["food safety", "HACCP", "pathogens", "overview"]}
    ],
    "agriculture_culinary_science": [
        {"title": "Culinary Science - Field Overview", "content": """# Culinary Science

## Definition
Culinary science is the study of food preparation techniques and the science behind cooking processes.

## Core Areas
- Cooking methods: heat
- Flavor: chemistry
- Texture: physical
- Nutrition: impact
- Presentation: visual
- Recipe development: create
- Food pairing: combination
- Molecular gastronomy: science

## Key Concepts
- Maillard: browning
- Caramelization: sugar
- Emulsion: mix
- Gelatinization: starch
- Denaturation: protein
- Reduction: concentrate
- Sous vide: vacuum
- Fermentation: culture

## Foundational Texts
- McGee, "On Food and Cooking"
- Belitz et al., "Food Chemistry"

## Authority Note
Advisory. IACP, Research Chefs Association.""", "tags": ["culinary science", "cooking", "flavor", "overview"]}
    ],
}

AGRICULTURE_K1_BATCH4: dict[str, list[dict]] = {
    "agriculture_sustainable_agriculture": [
        {"title": "Sustainable Agriculture - Field Overview", "content": """# Sustainable Agriculture

## Definition
Sustainable agriculture is farming in sustainable ways to meet society's food and textile needs without compromising future generations.

## Core Areas
- Environmental: stewardship
- Economic: profitability
- Social: fairness
- Soil health: conservation
- Water: efficiency
- Biodiversity: diversity
- Energy: renewable
- Integrated: systems

## Key Concepts
- Organic: certified
- Regenerative: restore
- Permaculture: design
- Agroecology: ecology
- Crop rotation: alternate
- Cover crop: protect
- No-till: minimize
- IPM: integrated pest

## Foundational Texts
- Francis et al., "Sustainable Agriculture"
- Gliessman, "Agroecology"

## Authority Note
Advisory. USDA-SARE, ATTRA resources.""", "tags": ["sustainable agriculture", "organic", "conservation", "overview"]}
    ],
    "agriculture_agricultural_economics": [
        {"title": "Agricultural Economics - Field Overview", "content": """# Agricultural Economics

## Definition
Agricultural economics is the study of the allocation, distribution, and utilization of resources in agriculture.

## Core Areas
- Production: efficiency
- Marketing: distribution
- Policy: government
- Trade: international
- Finance: capital
- Development: growth
- Resource: environment
- Consumer: demand

## Key Concepts
- Supply: quantity produced
- Demand: quantity wanted
- Elasticity: responsiveness
- Subsidy: government support
- Tariff: import tax
- Commodity: raw product
- Futures: contract
- Elasticity: price sensitivity

## Foundational Texts
- Seitz et al., "Managerial Economics"
- Colman & Young, "Principles of Agricultural Economics"

## Authority Note
Advisory. AAEA, IAAE professional.""", "tags": ["agricultural economics", "markets", "policy", "overview"]}
    ],
}

AGRICULTURE_K1_BATCH5: dict[str, list[dict]] = {
    "agriculture_fisheries_aquaculture": [
        {"title": "Fisheries and Aquaculture - Field Overview", "content": """# Fisheries and Aquaculture

## Definition
Fisheries and aquaculture encompass the harvesting of wild fish and the farming of aquatic organisms.

## Core Areas
- Capture: wild harvest
- Aquaculture: farming
- Stock assessment: population
- Habitat: protection
- Management: regulation
- Processing: products
- Nutrition: feed
- Health: disease

## Key Concepts
- Stock: population
- Bycatch: non-target
- Trawl: net
- Hatchery: breed
- Cage: enclosure
- Pond: contained
- Feed conversion: efficiency
- Sustainability: long-term

## Foundational Texts
- Pillay & Kutty, "Aquaculture"
- Hart & Reynolds, "Fisheries Ecology"

## Authority Note
Advisory. FAO guidelines; NOAA fisheries.""", "tags": ["fisheries", "aquaculture", "fish farming", "overview"]}
    ],
    "agriculture_rangelmanagement": [
        {"title": "Rangeland Management - Field Overview", "content": """# Rangeland Management

## Definition
Rangeland management is the study and practice of managing rangelands for sustainable use.

## Core Areas
- Grazing: livestock
- Ecology: plant communities
- Restoration: repair
- Fire: management
- Invasive species: control
- Wildlife: habitat
- Watershed: water
- Monitoring: assess

## Key Concepts
- Carrying capacity: limit
- Stocking rate: density
- Rotational grazing: move
- Rest: recover
- Succession: change
- Forage: plant
- Browse: woody
- Range condition: health

## Foundational Texts
- Holechek et al., "Range Management"
- Heady & Child, "Rangeland Ecology"

## Authority Note
Advisory. SRM professional; BLM, USFS management.""", "tags": ["rangeland", "grazing", "ecology", "overview"]}
    ],
}
