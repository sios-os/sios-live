"""Health & Medicine K1 - 26 specialties in 5 batches (6+6+5+5+4)."""

HEALTH_K1_BATCH1: dict[str, list[dict]] = {
    "health_primary_care": [
        {"title": "Primary Care - Field Overview", "content": """# Primary Care

## Definition
Primary care is the day-to-day healthcare given by a health care provider, serving as the first contact and principal point of continuing care.

## Core Areas
- Preventive: screenings, immunizations
- Acute: minor illness, injury
- Chronic: diabetes, hypertension
- Coordination: referrals
- Health maintenance: checkups
- Patient education: counseling

## Key Concepts
- PCP: primary care physician
- Family medicine: all ages
- Internal medicine: adults
- Pediatrics: children
- Preventive care: avoid disease
- Continuity: ongoing relationship
- Comprehensive: all problems
- Coordination: specialist referral

## Foundational Texts
- Rakel, "Textbook of Family Medicine"
- Goroll & Mulley, "Primary Care Medicine"

## Authority Note
Advisory. AAFP, ACP professional; board certification.""", "tags": ["primary care", "family medicine", "preventive", "overview"]}
    ],
    "health_emergency_medicine": [
        {"title": "Emergency Medicine - Field Overview", "content": """# Emergency Medicine

## Definition
Emergency medicine is the medical specialty dedicated to the diagnosis and treatment of unforeseen illness or injury.

## Core Areas
- Resuscitation: life-threatening
- Trauma: injury care
- Cardiac: heart emergencies
- Pediatric: children
- Toxicology: poisoning
- Disaster: mass casualty
- Prehospital: EMS

## Key Concepts
- ABC: airway, breathing, circulation
- Triage: prioritize
- Golden hour: critical time
- STAT: immediately
- Code: emergency alert
- Trauma: physical injury
- Shock: inadequate perfusion
- Sepsis: systemic infection

## Foundational Texts
- Tintinalli, "Emergency Medicine"
- Marx, "Rosen's Emergency Medicine"

## Authority Note
Advisory. ACEP professional; ABEM certification.""", "tags": ["emergency medicine", "trauma", "resuscitation", "overview"]}
    ],
    "health_cardiology": [
        {"title": "Cardiology - Field Overview", "content": """# Cardiology

## Definition
Cardiology is the medical specialty dealing with disorders of the heart and blood vessels.

## Core Areas
- Coronary: heart attack
- Arrhythmia: irregular heartbeat
- Heart failure: weak pump
- Valvular: valve disease
- Hypertension: high blood pressure
- Interventional: catheter
- Electrophysiology: electrical

## Key Concepts
- ECG: electrocardiogram
- Myocardial infarction: heart attack
- Arrhythmia: abnormal rhythm
- Stent: artery support
- Bypass: surgery
- Pacemaker: rhythm control
- Echocardiogram: ultrasound
- Catheterization: imaging

## Foundational Texts
- Braunwald, "Heart Disease"
- Guyton & Hall, "Medical Physiology"

## Authority Note
Advisory. ACC/AHA guidelines; ABIM certification.""", "tags": ["cardiology", "heart", "ECG", "overview"]}
    ],
    "health_neurology": [
        {"title": "Neurology - Field Overview", "content": """# Neurology

## Definition
Neurology is the medical specialty dealing with disorders of the nervous system.

## Core Areas
- Stroke: brain attack
- Epilepsy: seizures
- Movement: Parkinson's
- Dementia: Alzheimer's
- Headache: migraine
- Neuromuscular: MS, ALS
- Sleep: disorders

## Key Concepts
- CNS: central nervous system
- PNS: peripheral nervous system
- Stroke: interrupted blood flow
- Seizure: abnormal discharge
- Dementia: cognitive decline
- Reflex: automatic response
- EEG: brain waves
- MRI: imaging

## Foundational Texts
- Adams & Victor, "Principles of Neurology"
- Bradley, "Neurology in Clinical Practice"

## Authority Note
Advisory. AAN professional; ABPN certification.""", "tags": ["neurology", "nervous system", "stroke", "overview"]}
    ],
    "health_oncology": [
        {"title": "Oncology - Field Overview", "content": """# Oncology

## Definition
Oncology is the medical specialty dealing with the diagnosis and treatment of cancer.

## Core Areas
- Medical: chemotherapy
- Radiation: radiotherapy
- Surgical: operation
- Hematology: blood cancers
- Palliative: comfort
- Screening: early detection
- Survivorship: after

## Key Concepts
- Tumor: abnormal mass
- Benign: not cancer
- Malignant: cancer
- Metastasis: spread
- Staging: extent
- Biopsy: tissue sample
- Chemotherapy: drugs
- Remission: no evidence

## Foundational Texts
- DeVita, "Cancer: Principles & Practice"
- Abeloff, "Clinical Oncology"

## Authority Note
Advisory. ASCO professional; NCCN guidelines.""", "tags": ["oncology", "cancer", "chemotherapy", "overview"]}
    ],
    "health_psychiatry": [
        {"title": "Psychiatry - Field Overview", "content": """# Psychiatry

## Definition
Psychiatry is the medical specialty devoted to the diagnosis, prevention, and treatment of mental disorders.

## Core Areas
- Mood: depression, bipolar
- Anxiety: panic, OCD, PTSD
- Psychotic: schizophrenia
- Personality: disorders
- Substance: addiction
- Child: adolescent
- Geriatric: elderly

## Key Concepts
- DSM-5: diagnostic manual
- Neurotransmitter: brain chemical
- Psychosis: loss of reality
- Mood: emotional state
- Therapy: counseling
- Medication: psychotropic
- Commitment: involuntary
- Stigma: discrimination

## Foundational Texts
- Kaplan & Sadock, "Synopsis of Psychiatry"
- DSM-5 (APA)

## Authority Note
Advisory. APA professional; ABPN certification.""", "tags": ["psychiatry", "mental health", "DSM-5", "overview"]}
    ],
}

HEALTH_K1_BATCH2: dict[str, list[dict]] = {
    "health_pediatrics": [
        {"title": "Pediatrics - Field Overview", "content": """# Pediatrics

## Definition
Pediatrics is the medical specialty dealing with the medical care of infants, children, and adolescents.

## Core Areas
- Neonatal: newborn
- Well child: checkups
- Immunization: vaccines
- Development: milestones
- Acute: illness
- Chronic: conditions
- Adolescent: teen

## Key Concepts
- Growth: physical
- Development: skills
- Milestone: expected age
- Vaccine: immunization
- Congenital: born with
- Failure to thrive: poor growth
- SIDS: sudden infant death
- Puberty: sexual maturation

## Foundational Texts
- Nelson, "Textbook of Pediatrics"
- Kliegman, "Nelson Textbook"

## Authority Note
Advisory. AAP professional; ABP certification.""", "tags": ["pediatrics", "children", "vaccines", "overview"]}
    ],
    "health_geriatrics": [
        {"title": "Geriatrics - Field Overview", "content": """# Geriatrics

## Definition
Geriatrics is the medical specialty focused on the health care of elderly people.

## Core Areas
- Comprehensive assessment: function
- Polypharmacy: multiple drugs
- Cognitive: dementia, delirium
- Mobility: falls
- Functional: ADL, IADL
- End of life: palliative
- Chronic disease: management

## Key Concepts
- ADL: activities of daily living
- IADL: instrumental ADL
- Polypharmacy: many medications
- Delirium: acute confusion
- Dementia: chronic decline
- Sarcopenia: muscle loss
- Frailty: vulnerability
- Falls: injury risk

## Foundational Texts
- Hazzard, "Principles of Geriatric Medicine"
- Bourne, "Geriatric Medicine"

## Authority Note
Advisory. AGS professional; ABIM/Geriatrics certification.""", "tags": ["geriatrics", "elderly", "aging", "overview"]}
    ],
    "health_surgery": [
        {"title": "Surgery - Field Overview", "content": """# Surgery

## Definition
Surgery is the medical specialty that uses operative manual and instrumental techniques to investigate or treat a disease or injury.

## Core Areas
- General: abdomen, soft tissue
- Cardiothoracic: heart, lung
- Neurosurgery: brain, spine
- Orthopedic: bones
- Plastic: reconstruction
- Vascular: blood vessels
- Transplant: organ

## Key Concepts
- Pre-op: before
- Intra-op: during
- Post-op: after
- Anesthesia: pain control
- Asepsis: sterile
- Hemostasis: stop bleeding
- Suture: stitch
- Laparoscopy: minimally invasive

## Foundational Texts
- Schwartz, "Principles of Surgery"
- Townsend, "Sabiston Textbook of Surgery"

## Authority Note
Advisory. ACS professional; ABS certification.""", "tags": ["surgery", "operative", "anesthesia", "overview"]}
    ],
    "health_radiology": [
        {"title": "Radiology - Field Overview", "content": """# Radiology

## Definition
Radiology is the medical specialty that uses medical imaging to diagnose and treat diseases.

## Core Areas
- Diagnostic: imaging
- Interventional: image-guided
- Radiation oncology: cancer
- Neuroradiology: brain, spine
- Pediatric: children
- Musculoskeletal: bones
- Breast: mammography

## Key Concepts
- X-ray: radiation
- CT: computed tomography
- MRI: magnetic resonance
- Ultrasound: sound waves
- Contrast: enhance
- Fluoroscopy: real-time
- PACS: image storage
- Radiation dose: limit

## Foundational Texts
- Brant & Helms, "Fundamentals of Diagnostic Radiology"
- Webb, "Textbook of Radiology"

## Authority Note
Advisory. ACR standards; ABR certification.""", "tags": ["radiology", "imaging", "X-ray", "MRI", "overview"]}
    ],
    "health_pathology": [
        {"title": "Pathology - Field Overview", "content": """# Pathology

## Definition
Pathology is the medical specialty that studies the causes and effects of diseases, particularly by examining tissues.

## Core Areas
- Anatomic: tissue
- Clinical: laboratory
- Forensic: legal
- Molecular: genetic
- Hematopathology: blood
- Microbiology: organisms
- Dermatopathology: skin

## Key Concepts
- Biopsy: tissue sample
- Histology: tissue structure
- Cytology: cells
- Autopsy: post-mortem
- Stain: visualize
- Malignant: cancer
- Inflammation: response
- Necrosis: cell death

## Foundational Texts
- Kumar et al., "Robbins Basic Pathology"
- Rosai, "Ackerman's Surgical Pathology"

## Authority Note
Advisory. CAP standards; ABP certification.""", "tags": ["pathology", "tissue", "diagnosis", "overview"]}
    ],
    "health_genetics": [
        {"title": "Genetics - Field Overview", "content": """# Genetics

## Definition
Genetics is the study of genes, genetic variation, and heredity in living organisms.

## Core Areas
- Medical: disease
- Clinical: diagnosis, counseling
- Molecular: DNA
- Cytogenetics: chromosomes
- Biochemical: metabolism
- Population: frequency
- Pharmacogenomics: drug response

## Key Concepts
- DNA: genetic code
- Gene: unit of heredity
- Chromosome: DNA package
- Mutation: change
- Inheritance: passing traits
- Genotype: genetic makeup
- Phenotype: observable
- Allele: variant

## Foundational Texts
- Thompson, "Thompson & Thompson Genetics in Medicine"
- Strachan & Read, "Human Molecular Genetics"

## Authority Note
Advisory. ACMG guidelines; ABMG certification.""", "tags": ["genetics", "DNA", "heredity", "overview"]}
    ],
}

HEALTH_K1_BATCH3: dict[str, list[dict]] = {
    "health_neuroscience": [
        {"title": "Neuroscience - Field Overview", "content": """# Neuroscience

## Definition
Neuroscience is the scientific study of the nervous system, combining biology, psychology, and chemistry.

## Core Areas
- Cellular: neuron function
- Molecular: proteins, genes
- Systems: circuits
- Behavioral: behavior
- Cognitive: thinking
- Developmental: growth
- Computational: modeling

## Key Concepts
- Neuron: nerve cell
- Synapse: connection
- Neurotransmitter: chemical messenger
- Action potential: electrical signal
- Brain: central organ
- Cortex: outer layer
- Plasticity: adaptability
- Memory: storage

## Foundational Texts
- Kandel et al., "Principles of Neural Science"
- Bear et al., "Neuroscience"

## Authority Note
Advisory. SfN professional; research-based.""", "tags": ["neuroscience", "brain", "neuron", "overview"]}
    ],
    "health_epidemiology": [
        {"title": "Epidemiology - Field Overview", "content": """# Epidemiology

## Definition
Epidemiology is the study of how often diseases occur in different groups of people and why.

## Core Areas
- Infectious: outbreaks
- Chronic: long-term
- Environmental: exposures
- Occupational: workplace
- Genetic: heredity
- Social: disparities
- Molecular: biomarkers

## Key Concepts
- Incidence: new cases
- Prevalence: total cases
- Outbreak: sudden increase
- Epidemic: widespread
- Pandemic: global
- Risk factor: association
- Causation: cause
- Surveillance: monitor

## Foundational Texts
- Rothman, "Epidemiology: An Introduction"
- Gordis, "Epidemiology"

## Authority Note
Advisory. CDC guidelines; ACE professional.""", "tags": ["epidemiology", "disease", "outbreak", "overview"]}
    ],
    "health_public_health": [
        {"title": "Public Health - Field Overview", "content": """# Public Health

## Definition
Public health is the science of protecting and improving the health of people and their communities.

## Core Areas
- Epidemiology: disease patterns
- Biostatistics: data
- Environmental: surroundings
- Health policy: laws
- Behavioral: choices
- Maternal/child: families
- Global: worldwide

## Key Concepts
- Prevention: avoid disease
- Population: group focus
- Vaccination: immunize
- Sanitation: clean
- Health equity: fair
- Social determinants: conditions
- Screening: early detection
- Promotion: education

## Foundational Texts
- Turnock, "Public Health: What It Is and How It Works"
- Schneider, "Introduction to Public Health"

## Authority Note
Advisory. APHA professional; CEPH accreditation.""", "tags": ["public health", "prevention", "population", "overview"]}
    ],
    "health_pharmacology": [
        {"title": "Pharmacology - Field Overview", "content": """# Pharmacology

## Definition
Pharmacology is the science of drugs and their effects on living organisms.

## Core Areas
- Pharmacokinetics: body on drug
- Pharmacodynamics: drug on body
- Pharmacogenomics: genetics
- Toxicology: adverse effects
- Clinical: therapeutics
- Neuropharmacology: brain
- Chemotherapy: cancer

## Key Concepts
- Absorption: into body
- Distribution: to tissues
- Metabolism: break down
- Excretion: remove
- Half-life: time to halve
- Efficacy: maximum effect
- Potency: dose needed
- Side effect: unwanted

## Foundational Texts
- Katzung, "Basic and Clinical Pharmacology"
- Goodman & Gilman, "The Pharmacological Basis"

## Authority Note
Advisory. ASPET professional; research-based.""", "tags": ["pharmacology", "drugs", "pharmacokinetics", "overview"]}
    ],
    "health_pharmacy": [
        {"title": "Pharmacy - Field Overview", "content": """# Pharmacy

## Definition
Pharmacy is the science and technique of preparing, dispensing, and reviewing drugs and providing additional clinical services.

## Core Areas
- Dispensing: provide medications
- Clinical: patient care
- Compounding: custom
- Hospital: inpatient
- Community: retail
- Industry: manufacturing
- Research: development

## Key Concepts
- Prescription: order
- OTC: over the counter
- Generic: equivalent
- Brand: proprietary
- Drug interaction: combine
- Adherence: compliance
- Counsel: educate
- Formulary: approved list

## Foundational Texts
- DiPiro, "Pharmacotherapy"
- Remington, "The Science and Practice of Pharmacy"

## Authority Note
Advisory. APhA professional; NABP licensure.""", "tags": ["pharmacy", "dispensing", "medication", "overview"]}
    ],
}

HEALTH_K1_BATCH4: dict[str, list[dict]] = {
    "health_nursing": [
        {"title": "Nursing - Field Overview", "content": """# Nursing

## Definition
Nursing is a profession within the health care sector focused on the care of individuals, families, and communities.

## Core Areas
- Direct care: patient
- Assessment: examine
- Education: teach
- Advocacy: support
- Coordination: manage
- Leadership: manage
- Research: evidence

## Key Concepts
- RN: registered nurse
- LPN: licensed practical
- NP: nurse practitioner
- Assessment: evaluate
- Care plan: strategy
- Vital signs: temp, pulse, BP, resp
- ADL: daily activities
- Handoff: report

## Foundational Texts
- Potter & Perry, "Fundamentals of Nursing"
- Taylor, "Clinical Nursing Skills"

## Authority Note
Advisory. ANA professional; NCLEX licensure.""", "tags": ["nursing", "patient care", "RN", "overview"]}
    ],
    "health_dentistry": [
        {"title": "Dentistry - Field Overview", "content": """# Dentistry

## Definition
Dentistry is the medical specialty dealing with the diagnosis, prevention, and treatment of conditions of the oral cavity.

## Core Areas
- General: checkups, fillings
- Orthodontics: align
- Oral surgery: extract
- Periodontics: gums
- Endodontics: root canal
- Pediatric: children
- Prosthodontics: replace

## Key Concepts
- Cavity: decay
- Plaque: bacteria
- Tartar: calcified
- Gingivitis: gum inflammation
- Periodontitis: bone loss
- Crown: cap
- Bridge: replace
- Implant: artificial root

## Foundational Texts
- Little & Falace, "Dental Management"
- Summitt, "Fundamentals of Operative Dentistry"

## Authority Note
Advisory. ADA professional; CODA accreditation.""", "tags": ["dentistry", "teeth", "oral", "overview"]}
    ],
    "health_nutrition": [
        {"title": "Nutrition - Field Overview", "content": """# Nutrition

## Definition
Nutrition is the science of food and its relationship to health.

## Core Areas
- Macronutrients: carbs, protein, fat
- Micronutrients: vitamins, minerals
- Clinical: disease
- Public health: population
- Sports: performance
- Community: education
- Food science: processing

## Key Concepts
- Calorie: energy
- RDA: recommended daily
- BMI: body mass index
- Metabolism: chemical processes
- Deficiency: lack
- Toxicity: excess
- Antioxidant: protect
- Fiber: indigestible

## Foundational Texts
- Gropper & Smith, "Advanced Nutrition and Human Metabolism"
- Whitney & Rolfes, "Understanding Nutrition"

## Authority Note
Advisory. Academy of Nutrition and Dietetics; RD credential.""", "tags": ["nutrition", "diet", "vitamins", "overview"]}
    ],
    "health_physical_therapy": [
        {"title": "Physical Therapy - Field Overview", "content": """# Physical Therapy

## Definition
Physical therapy is the treatment of disease, injury, or deformity by physical methods such as exercise and massage.

## Core Areas
- Orthopedic: musculoskeletal
- Neurological: brain, spinal cord
- Cardiovascular: heart
- Pulmonary: lungs
- Pediatric: children
- Geriatric: elderly
- Sports: athletics

## Key Concepts
- ROM: range of motion
- Strength: force
- Endurance: stamina
- Flexibility: stretch
- Balance: stability
- Gait: walking
- Modalities: heat, cold, electrical
- Manual: hands-on

## Foundational Texts
- O'Sullivan et al., "Physical Rehabilitation"
- Magee, "Orthopedic Physical Assessment"

## Authority Note
Advisory. APTA professional; CAPTE accreditation.""", "tags": ["physical therapy", "rehabilitation", "exercise", "overview"]}
    ],
    "health_occupational_therapy": [
        {"title": "Occupational Therapy - Field Overview", "content": """# Occupational Therapy

## Definition
Occupational therapy uses everyday activities (occupations) therapeutically to help people participate in daily life.

## Core Areas
- Pediatric: children
- Geriatric: elderly
- Mental health: psychiatric
- Physical: injury, disease
- Neurological: brain, spinal cord
- Hand therapy: upper extremity
- Driving: community mobility

## Key Concepts
- Occupation: meaningful activity
- ADL: daily living
- IADL: instrumental
- Fine motor: small movements
- Gross motor: large movements
- Sensory: processing
- Adaptive: modified
- Engagement: participate

## Foundational Texts
- Crepeau et al., "Willard and Spackman's Occupational Therapy"
- Pendry, "Occupational Therapy"

## Authority Note
Advisory. AOTA professional; ACOTE accreditation.""", "tags": ["occupational therapy", "ADL", "rehabilitation", "overview"]}
    ],
}

HEALTH_K1_BATCH5: dict[str, list[dict]] = {
    "health_veterinary_medicine": [
        {"title": "Veterinary Medicine - Field Overview", "content": """# Veterinary Medicine

## Definition
Veterinary medicine is the branch of medicine that deals with the prevention, diagnosis, and treatment of disease in animals.

## Core Areas
- Small animal: dogs, cats
- Large animal: horses, cattle
- Exotic: birds, reptiles
- Food animal: production
- Public health: zoonosis
- Research: laboratory
- Wildlife: free-ranging

## Key Concepts
- Zoonosis: animal to human
- Vaccination: prevent
- Surgery: operate
- Dentistry: teeth
- Herd health: group
- Reproduction: breeding
- Euthanasia: humane death
- One Health: interconnected

## Foundational Texts
- Ettinger, "Textbook of Veterinary Internal Medicine"
- Merck Veterinary Manual

## Authority Note
Advisory. AVMA professional; NAVLE licensure.""", "tags": ["veterinary", "animals", "zoonosis", "overview"]}
    ],
    "health_medical_ethics": [
        {"title": "Medical Ethics - Field Overview", "content": """# Medical Ethics

## Definition
Medical ethics is a system of moral principles that apply values to the practice of medicine.

## Core Areas
- Patient autonomy: choice
- Beneficence: do good
- Non-maleficence: do no harm
- Justice: fair
- Confidentiality: privacy
- Informed consent: agree
- End of life: decisions

## Key Concepts
- Autonomy: self-determination
- Beneficence: act in best interest
- Non-maleficence: avoid harm
- Justice: equitable
- Consent: informed agreement
- Capacity: ability to decide
- Confidentiality: private
- Advance directive: wishes

## Foundational Texts
- Beauchamp & Childress, "Principles of Biomedical Ethics"
- Jonsen et al., "Clinical Ethics"

## Authority Note
Advisory. AMA Code; bioethics councils.""", "tags": ["medical ethics", "bioethics", "autonomy", "overview"]}
    ],
    "health_health_informatics": [
        {"title": "Health Informatics - Field Overview", "content": """# Health Informatics

## Definition
Health informatics is the intersection of information science, computer science, and health care.

## Core Areas
- Electronic health records: EHR
- Clinical decision support: CDS
- Health information exchange: HIE
- Telemedicine: remote
- Data analytics: insights
- Privacy: HIPAA
- Standards: interoperability

## Key Concepts
- EHR: electronic health record
- HIPAA: privacy law
- Interoperability: communicate
- HL7: standard
- FHIR: API standard
- ICD: coding
- SNOMED: terminology
- Telemedicine: remote care

## Foundational Texts
- Shortliffe & Cimino, "Biomedical Informatics"
- Hoyt, "Health Informatics"

## Authority Note
Advisory. AMIA professional; HIMSS standards.""", "tags": ["health informatics", "EHR", "HIPAA", "overview"]}
    ],
    "health_sports_medicine": [
        {"title": "Sports Medicine - Field Overview", "content": """# Sports Medicine

## Definition
Sports medicine is the medical specialty concerned with the treatment of injuries related to sports and exercise.

## Core Areas
- Injury prevention: avoid
- Diagnosis: identify
- Treatment: heal
- Rehabilitation: recover
- Performance: optimize
- Exercise prescription: recommend
- Team coverage: events

## Key Concepts
- Concussion: brain injury
- Sprain: ligament
- Strain: muscle
- Tendinitis: tendon
- Fracture: bone
- Overuse: repetitive
- RICE: rest, ice, compression, elevation
- Return to play: criteria

## Foundational Texts
- Madden, "Netter's Sports Medicine"
- Brukner & Khan, "Clinical Sports Medicine"

## Authority Note
Advisory. AMSSM professional; CAQ certification.""", "tags": ["sports medicine", "athletics", "injury", "overview"]}
    ],
}
