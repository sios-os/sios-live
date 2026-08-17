"""Health & Medicine K3 Batch 4 - 5 specialties."""

HEALTH_K3_BATCH4: dict[str, list[dict]] = {
    "health_nursing": [
        {"title": "Nursing Practice Reference", "content": """# Nursing Practice Reference

## Nursing Process
1. Assessment: collect data
2. Diagnosis: identify problems
3. Planning: set goals
4. Implementation: interventions
5. Evaluation: assess outcomes

## Assessment
### Vital Signs
- Temperature: 97.8-99.1F (36.5-37.3C)
- Pulse: 60-100 bpm
- Respiration: 12-20/min
- Blood pressure: <120/<80
- Oxygen saturation: >=95%
- Pain: 0-10 scale

### Head to Toe
- Head: symmetry, facial
- Eyes: pupils, conjunctiva
- Ears: hearing
- Nose: patency
- Mouth: mucosa, teeth
- Neck: thyroid, nodes, JVD
- Chest: heart, lungs
- Abdomen: bowel sounds, tenderness
- Extremities: pulses, edema, ROM
- Skin: color, integrity
- Neuro: mental, reflexes

## Documentation
### SOAP
- S: subjective (patient)
- O: objective (observed)
- A: assessment (diagnosis)
- P: plan (intervention)

### SBAR (Handoff)
- S: situation
- B: background
- A: assessment
- R: recommendation

## Medication Administration
### Rights
1. Right patient
2. Right drug
3. Right dose
4. Right route
5. Right time
6. Right documentation
7. Right reason
8. Right response

### Routes
- Oral: by mouth
- IV: intravenous
- IM: intramuscular
- Subcutaneous: under skin
- Sublingual: under tongue
- Topical: on skin
- Inhalation: breathe
- Rectal: rectum
- Vaginal: vagina

## Common Interventions
### Wound Care
- Assess: size, depth, edges
- Clean: saline
- Dress: appropriate
- Monitor: signs of infection
- Document: changes

### IV Therapy
- Access: peripheral, central
- Fluids: crystalloid, colloid
- Rate: mL/hr
- Site: assess
- Complications: infiltration, phlebitis

### Pain Management
- Assess: scale
- Non-pharm: positioning, heat/cold
- Pharm: per orders
- Monitor: effectiveness
- Side effects: sedation, constipation

### Patient Safety
- Fall risk: assess
- Restraints: last resort
- Identification: two identifiers
- Time out: before procedures
- Hand hygiene: before/after

## Common Pitfalls
- Medication errors
- Not following rights
- Poor documentation
- Not communicating changes
- Not assessing pain
- Not preventing falls
""", "tags": ["nursing", "assessment", "medication", "documentation", "reference"]}
    ],
    "health_dentistry": [
        {"title": "Dentistry Practice Reference", "content": """# Dentistry Practice Reference

## Examination
### Extraoral
- Face: symmetry
- Lymph nodes: palpate
- TMJ: function
- Lips: lesions

### Intraoral
- Soft tissue: cheek, tongue, palate
- Gingiva: color, recession
- Teeth: caries, restorations
- Occlusion: bite
- Periodontal: probing

### Charting
- Teeth: universal numbering (1-32)
- Surfaces: mesial, distal, buccal, lingual, occlusal
- Restorations: amalgam, composite
- Conditions: caries, missing

## Common Conditions
### Caries
- Cause: bacteria, sugar, acid
- Location: occlusal, interproximal, root
- Diagnosis: visual, radiograph, explorer
- Treatment: filling, crown

### Periodontal Disease
- Gingivitis: reversible
- Periodontitis: bone loss
- Diagnosis: probing (4+ mm), radiograph
- Treatment: scaling, root planing, surgery

### Malocclusion
- Class I: normal molar
- Class II: overjet (retrognathic)
- Class III: underjet (prognathic)
- Treatment: orthodontics

### Oral Lesions
- Aphthous: ulcer (canker)
- Herpes: cold sore
- Candidiasis: thrush
- Leukoplakia: white patch (biopsy)
- Cancer: squamous cell

## Procedures
### Restoration
- Amalgam: durable, posterior
- Composite: aesthetic, anterior
- Glass ionomer: fluoride
- Gold: durable

### Endodontics
- Indication: irreversible pulpitis
- Procedure: clean, shape, fill
- Success: high

### Extraction
- Indication: non-restorable, impaction
- Technique: simple, surgical
- Aftercare: bleeding, swelling

### Prosthodontics
- Crown: cap
- Bridge: replace missing
- Denture: removable
- Implant: artificial root

### Periodontal
- Scaling: remove calculus
- Root planing: smooth
- Surgery: flap, graft

## Prevention
### Home Care
- Brush: 2x/day, fluoride
- Floss: daily
- Rinse: mouthwash
- Diet: limit sugar

### Professional
- Cleaning: 6 months
- Examination: 6 months
- Radiograph: as needed
- Fluoride: varnish
- Sealant: grooves

## Common Pitfalls
- Missing caries
- Not taking radiographs
- Not probing periodontal
- Not screening for cancer
- Not educating patient
- Not using proper technique
""", "tags": ["dentistry", "teeth", "caries", "periodontal", "reference"]}
    ],
    "health_nutrition": [
        {"title": "Nutrition Practice Reference", "content": """# Nutrition Practice Reference

## Macronutrients
### Carbohydrates
- Energy: 4 kcal/g
- Types: simple, complex
- Fiber: 25-35 g/day
- Glycemic index: blood sugar

### Protein
- Energy: 4 kcal/g
- Essential: 9 amino acids
- Complete: animal, soy
- Incomplete: plant (combine)
- Need: 0.8 g/kg

### Fat
- Energy: 9 kcal/g
- Saturated: animal (limit)
- Unsaturated: plant (good)
- Trans: avoid
- Omega-3: fish (anti-inflammatory)
- Omega-6: plant

## Micronutrients
### Vitamins
- Fat-soluble: A, D, E, K
- Water-soluble: B, C
- Deficiency: specific disease
- Toxicity: possible (fat-soluble)

### Minerals
- Macro: calcium, phosphorus, magnesium
- Trace: iron, zinc, iodine, selenium
- Electrolytes: sodium, potassium, chloride

## Assessment
### Anthropometric
- Height, weight
- BMI: weight (kg) / height (m)^2
  - Underweight: <18.5
  - Normal: 18.5-24.9
  - Overweight: 25-29.9
  - Obese: >=30
- Waist: >40" men, >35" women
- Growth: children

### Biochemical
- Albumin: protein
- Prealbumin: acute
- Hemoglobin: anemia
- Ferritin: iron
- B12, folate
- Lipid panel
- Glucose

### Dietary
- 24-hour recall
- Food frequency
- Food diary

## Clinical Conditions
### Obesity
- Cause: excess calories
- Risk: diabetes, heart, joint
- Treatment: diet, exercise, behavior
- Medication: orlistat, GLP-1
- Surgery: gastric bypass, sleeve

### Diabetes
- Carbs: consistent
- Glycemic: choose low
- Fiber: increase
- Sugar: limit
- Meal: timing

### Hypertension
- DASH: diet
- Sodium: <2300 mg
- Potassium: increase
- Alcohol: limit

### Heart Disease
- Fat: reduce saturated
- Fiber: increase
- Omega-3: fish
- Plant sterols

### Kidney Disease
- Protein: adjust
- Sodium: limit
- Potassium: if high
- Phosphorus: if high
- Fluid: if retaining

### Malnutrition
- Causes: intake, absorption, increased need
- Signs: weight loss, muscle
- Treatment: supplement, tube, parenteral

## Life Stages
### Pregnancy
- Folate: 600 mcg
- Iron: 27 mg
- Calcium: 1000 mg
- Weight gain: per BMI
- Avoid: alcohol, high mercury fish

### Infant
- 0-6 months: breast or formula
- 6 months: solids
- Iron: fortified
- Allergens: introduce early

### Elderly
- Calories: decrease
- Protein: increase
- Vitamin D: supplement
- B12: supplement
- Hydration: encourage

## Common Pitfalls
- Not assessing nutrition status
- Not considering culture
- Fad diets
- Not addressing barriers
- Over-supplementing
- Not coordinating with medical care
""", "tags": ["nutrition", "macronutrients", "micronutrients", "assessment", "reference"]}
    ],
    "health_physical_therapy": [
        {"title": "Physical Therapy Practice Reference", "content": """# Physical Therapy Practice Reference

## Examination
### History
- Chief complaint
- Mechanism: injury
- Onset: when
- Course: better, worse
- Aggravating: what makes worse
- Easing: what makes better
- Past: medical, surgical
- Medications
- Occupation
- Goals

### Tests and Measures
- ROM: goniometer
- Strength: 0-5 scale
- Flexibility: reach
- Balance: tests
- Gait: observe
- Posture: assess
- Special: per region
- Functional: ADL

## Assessment
### Impairment
- ROM: limited
- Strength: weak
- Pain: present
- Balance: impaired
- Endurance: reduced

### Function
- ADL: difficulty
- IADL: difficulty
- Work: limited
- Recreation: limited

## Treatment
### Exercise
- ROM: passive, active, active-assist
- Strengthening:
  - Isometric: no movement
  - Isotonic: movement
  - Isokinetic: constant speed
  - Progressive resistance: increase
- Flexibility: stretch
- Endurance: aerobic
- Balance: stability
- Proprioception: awareness

### Manual Therapy
- Mobilization: joint
- Manipulation: thrust
- Massage: soft tissue
- Stretching: passive
- MFR: myofascial release

### Modalities
- Heat: superficial (pack), deep (US)
- Cold: ice, cold pack
- Electrical: TENS, NMES, FES
- Ultrasound: thermal, mechanical
- Traction: cervical, lumbar
- Laser: low level

### Neuromuscular
- PNF: proprioceptive neuromuscular
- Bobath: neurodevelopmental
- Brunnstrom: stages
- Rood: sensory
- Task-specific: practice

## Common Conditions
### Orthopedic
#### Low Back Pain
- Acute: <6 weeks
- Mechanical: most common
- Treatment: exercise, manual, education
- Red flags: cancer, infection, fracture

#### Neck Pain
- Mechanical: most
- Whiplash: trauma
- Treatment: exercise, manual
- Radiculopathy: nerve

#### Shoulder
- Rotator cuff: tear, tendinitis
- Frozen: adhesive capsulitis
- Impingement: bursitis
- Treatment: ROM, strengthen

#### Knee
- OA: degenerative
- Meniscus: tear
- ACL: ligament
- Patellofemoral: pain
- Treatment: strengthen, ROM

#### Ankle
- Sprain: lateral
- Fracture: rule out
- Treatment: RICE, rehab

### Neurological
#### Stroke
- Acute: rehab
- Chronic: maintain
- Treatment: PNF, task-specific
- Goals: function

#### SCI
- Level: function
- Complete vs incomplete
- Treatment: strength, function

#### MS
- Fatigue: manage
- Weakness: strengthen
- Balance: train
- Heat: sensitivity

### Other
#### Parkinson's
- Rigidity: stretch
- Bradykinesia: movement
- Balance: train
- Gait: train

#### Vestibular
- BPPV: Epley
- Balance: train
- Habituation: repeat

## Home Program
- Exercise: prescribed
- Frequency: daily
- Progression: gradual
- Self-monitor: symptoms
- Modify: as needed

## Common Pitfalls
- Not doing thorough exam
- Wrong diagnosis
- Too aggressive
- Too conservative
- Not educating patient
- Not progressing
- Not documenting outcomes
""", "tags": ["physical therapy", "rehabilitation", "exercise", "manual", "reference"]}
    ],
    "health_occupational_therapy": [
        {"title": "Occupational Therapy Practice Reference", "content": """# Occupational Therapy Practice Reference

## Philosophy
- Occupation: meaningful activity
- Enable: participation
- Client-centered: goals
- Holistic: whole person
- Adapt: environment

## Process
1. Referral: receive
2. Evaluation: assess
3. Intervention: plan and implement
4. Target: outcomes
5. Discharge: transition

## Evaluation
### Occupational Profile
- History: developmental
- Roles: life
- Values: important
- Interests: enjoy
- Habits: routines
- Goals: what matters

### Performance
- ADL: bathing, dressing, feeding
- IADL: cooking, cleaning, managing meds
- Work: job tasks
- Leisure: hobbies
- Social: participation
- Rest: sleep

### Skills
- Motor: strength, coordination
- Process: problem-solving, attention
- Communication: interaction
- Sensory: processing

### Environment
- Physical: home, work
- Social: family, community
- Cultural: values
- Temporal: time

## Intervention
### ADL Training
- Feeding: utensils, positioning
- Dressing: adaptive, technique
- Bathing: equipment, safety
- Toileting: equipment
- Grooming: adapted tools

### IADL Training
- Cooking: sequence, safety
- Cleaning: pacing, technique
- Shopping: list, mobility
- Medication: management
- Finances: budgeting

### Adaptive Equipment
- Reacher: grab
- Long-handled: sponge, shoe horn
- Sock aid: dress
- Button hook: dress
- Adaptive utensils: eat
- Shower chair: bathe
- Grab bars: safety
- Raised toilet: seat

### Splinting
- Static: immobilize
- Dynamic: assist movement
- Functional: position
- Prevent: contracture
- Fabricate: custom

### Sensory Integration
- Tactile: touch
- Vestibular: movement
- Proprioceptive: position
- Auditory: sound
- Visual: sight
- Treatment: graded exposure

### Cognitive
- Attention: train
- Memory: strategies
- Problem-solving: practice
- Executive: function
- Compensatory: aids

### Motor
- Fine: dexterity
- Gross: coordination
- Strength: exercise
- ROM: stretch
- Bilateral: integration

## Conditions
### Stroke
- Hemiparesis: weak side
- Neglect: ignore side
- Visual: field cut
- Cognitive: impaired
- Treatment: ADL, IADL, adaptive

### TBI
- Cognitive: impaired
- Behavioral: changes
- Physical: varies
- Treatment: cognitive, behavioral, ADL

### SCI
- Level: determines function
- ADL: adapt
- Equipment: wheelchair, devices
- Home: modify

### Developmental
- Autism: sensory, social
- ADHD: attention, behavior
- CP: motor, function
- Down: cognitive, motor
- Treatment: play, ADL, school

### Hand
- Tendon: repair
- Fracture: rehab
- Nerve: repair
- Amputation: prosthetic
- Treatment: ROM, strength, function

### Mental Health
- Depression: activity
- Anxiety: coping
- Schizophrenia: function
- Treatment: meaningful activity

## Common Pitfalls
- Not being client-centered
- Not considering environment
- Not addressing meaningful occupations
- Over-focusing on impairment
- Not adapting task or environment
- Not collaborating with team
""", "tags": ["occupational therapy", "ADL", "adaptation", "rehabilitation", "reference"]}
    ],
}
