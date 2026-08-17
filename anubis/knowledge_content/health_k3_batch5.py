"""Health & Medicine K3 Batch 5 - 4 specialties."""

HEALTH_K3_BATCH5: dict[str, list[dict]] = {
    "health_veterinary_medicine": [
        {"title": "Veterinary Medicine Reference", "content": """# Veterinary Medicine Reference

## Examination
### History
- Signalment: species, breed, age, sex
- Chief complaint
- Duration
- Vaccination: status
- Diet
- Environment
- Contact: other animals

### Physical
- TPR: temperature, pulse, respiration
- Body condition: score
- Mucous membranes: color, CRT
- Hydration: skin tent, eyes
- Lymph nodes: palpate
- Auscultation: heart, lungs
- Palpation: abdomen

## Common Species
### Dogs
- Vaccines: rabies, DHPP, Bordetella
- Common: OA, dental, obesity, ear
- Neuter/spay: elective

### Cats
- Vaccines: rabies, FVRCP, FeLV
- Common: FLUTD, dental, hyperthyroid
- Indoor: safer
- Neuter/spay: elective

### Horses
- Vaccines: rabies, EEE/WEE, WNV, tetanus
- Common: colic, lameness, dental
- Coggins: EIA test

### Cattle
- Vaccines: IBR, BVD, PI3, BRSV
- Common: mastitis, lameness, respiratory
- Herd health: important

## Common Conditions
### Infectious
- Parvovirus: dogs, GI
- Feline leukemia: cats, immunosuppression
- Kennel cough: dogs, respiratory
- FIV: cats, immunosuppression
- Rabies: all, zoonotic

### Parasites
- Heartworm: mosquito
- Roundworm: zoonotic
- Hookworm: zoonotic
- Tapeworm: flea
- Fleas: external
- Ticks: disease vector

### Dental
- Periodontal: most common
- Plaque: bacteria
- Tartar: calcified
- Extraction: if severe

### Surgery
- Spay: ovariohysterectomy
- Neuter: castration
- Soft tissue: mass, foreign body
- Orthopedic: fracture, ACL

### Emergency
- GDV: gastric dilatation (dogs)
- Urethral obstruction: cats
- Trauma: HBC (hit by car)
- Toxicity: various
- Hemorrhage: bleeding

## Diagnostics
- CBC: blood
- Chemistry: organ function
- Urinalysis: kidney
- Radiograph: imaging
- Ultrasound: imaging
- Cytology: cells
- Culture: bacteria
- PCR: viral

## Treatment
- Antibiotics: bacterial
- Antiparasitics: parasites
- NSAIDs: pain, inflammation
- Opioids: severe pain
- Surgery: operative
- Fluids: dehydration
- Blood: transfusion

## Zoonosis
- Rabies: fatal
- Ringworm: fungal
- Toxoplasmosis: cats, pregnancy
- Leptospirosis: bacterial
- Salmonella: reptiles
- Campylobacter: many

## Common Pitfalls
- Not vaccinating
- Not controlling parasites
- Missing zoonotic risk
- Not addressing dental
- Not counseling on nutrition
- Not recognizing pain
""", "tags": ["veterinary", "animals", "zoonosis", "surgery", "reference"]}
    ],
    "health_medical_ethics": [
        {"title": "Medical Ethics Reference", "content": """# Medical Ethics Reference

## Four Principles
### Autonomy
- Self-determination
- Informed consent
- Right to refuse
- Confidentiality
- Truth-telling

### Beneficence
- Act in best interest
- Promote welfare
- Prevent harm
- Remove harm

### Non-maleficence
- Do no harm
- Weigh risks/benefits
- Avoid unnecessary treatment
- Primum non nocere

### Justice
- Fair distribution
- Equal access
- Resource allocation
- Non-discrimination

## Informed Consent
### Elements
- Capacity: ability to decide
- Disclosure: information
- Comprehension: understanding
- Voluntariness: free choice
- Consent: agreement

### Exceptions
- Emergency: life-threatening
- Therapeutic privilege: rare
- Waiver: patient declines
- Legal: minor, incompetent

## End of Life
### Advance Directives
- Living will: wishes
- Healthcare proxy: decision-maker
- DNR/DNI: orders
- POLST: medical orders

### Euthanasia
- Active: administer (illegal most US)
- Passive: withhold/withdraw
- Physician-assisted: prescribe (some states)
- Palliative: comfort only

### Decisions
- Futility: non-beneficial
- Withdraw: stop treatment
- Withhold: not start
- Comfort: prioritize

## Confidentiality
### Duty
- Protect information
- HIPAA: federal law
- Exceptions:
  - Mandated reporting
  - Danger to self/others
  - Court order
  - Public health

### Breach
- Justified: report
- Unjustified: liability
- Minimize: necessary information

## Special Issues
### Beginning of Life
- Contraception
- Abortion
- Assisted reproduction
- Maternal-fetal conflict
- Neonatal decisions

### Genetics
- Testing: consent
- Privacy: family implications
- Discrimination: GINA
- Incidental findings
- Children: testing

### Research
- IRB: review
- Informed consent
- Vulnerable populations
- Placebo: ethical
- Publication: honesty

### Allocation
- Scarcity: resources
- Triage: prioritize
- Transplant: criteria
- ICU: beds
- Emergency: disaster

## Professionalism
### Commitments
- Competence: maintain
- Honesty: truthful
- Confidentiality: protect
- Appropriate relations: boundaries
- Improve quality: systems
- Improve access: care
- Just distribution: resources
- Scientific knowledge: advance
- Maintain trust: profession
- Manage conflicts: interest

## Common Dilemmas
### Competence
- Assess: capacity
- Substitute: decision-maker
- Best interest: standard
- Substituted judgment: what patient would want

### Refusal
- Competent: respect
- Document: discussion
- Consequences: explained
- Revisit: later

### Truth-telling
- Disclosure: diagnosis, prognosis
- Cultural: variations
- Therapeutic privilege: rare
- Hope: maintain

### Errors
- Disclose: honest
- Apologize: sincere
- Prevent: systems
- Learn: improve

## Framework
### Approach
1. Identify: ethical issue
2. Gather: facts
3. Identify: principles
4. Consider: options
5. Decide: action
6. Implement: plan
7. Evaluate: outcome

### Consultation
- Ethics committee
- Legal counsel
- Risk management
- Mentor

## Common Pitfalls
- Not recognizing ethical issues
- Not respecting autonomy
- Paternalism
- Not documenting discussions
- Not consulting when needed
- Conflicting values
- Cultural insensitivity
""", "tags": ["medical ethics", "bioethics", "autonomy", "consent", "end of life", "reference"]}
    ],
    "health_health_informatics": [
        {"title": "Health Informatics Reference", "content": """# Health Informatics Reference

## Electronic Health Records (EHR)
### Functions
- Chart: medical record
- Orders: prescriptions, tests
- Results: lab, imaging
- Documentation: notes
- Decision support: alerts
- Messaging: communication
- Scheduling: appointments
- Billing: coding

### Benefits
- Access: anywhere
- Legibility: typed
- Decision support: real-time
- Coordination: shared
- Quality: metrics
- Efficiency: workflow

### Challenges
- Cost: high
- Training: needed
- Workflow: change
- Interoperability: limited
- Privacy: risk
- Downtime: disruption

## Standards
### HL7
- Health Level 7: messaging
- v2: most common
- v3: comprehensive
- FHIR: modern, API

### FHIR (Fast Healthcare Interoperability Resources)
- RESTful: API
- Resources: data elements
- Modular: flexible
- Modern: web standards
- Apps: ecosystem

### Terminology
- ICD-10: diagnoses
- CPT: procedures
- SNOMED CT: clinical terms
- LOINC: lab observations
- RxNorm: medications
- NDC: drug codes

### Privacy
- HIPAA: federal
- Privacy Rule: protected health information
- Security Rule: safeguards
- Breach: notification
- Minimum necessary: standard

## Clinical Decision Support (CDS)
### Types
- Alerts: drug interaction
- Reminders: preventive
- Guidelines: protocols
- Calculators: risk scores
- Order sets: standardize
- Documentation: templates

### Implementation
- Right information
- Right person
- Right intervention format
- Right channel
- Right time

## Telemedicine
### Types
- Synchronous: real-time (video)
- Asynchronous: store-and-forward
- Remote monitoring: devices
- Mobile health: apps

### Applications
- Primary care: routine
- Mental health: therapy
- Specialty: consultation
- Chronic: monitoring
- Urgent: minor

### Reimbursement
- Medicare: expanded
- Medicaid: varies
- Private: varies
- Location: relaxed (COVID)

## Data Analytics
### Types
- Descriptive: what happened
- Predictive: what will happen
- Prescriptive: what to do

### Applications
- Quality: measure
- Population: manage
- Risk: stratify
- Cost: analyze
- Research: discover

### Tools
- SQL: query
- R: statistics
- Python: programming
- Tableau: visualize
- Dashboards: monitor

## Interoperability
### Levels
- Foundational: send
- Structural: format
- Semantic: meaning

### Approaches
- Standards: HL7, FHIR
- APIs: interface
- HIE: exchange
- Common: data model

### Barriers
- Cost
- Standards: adoption
- Privacy: concerns
- Vendor: lock-in
- Workflow: change

## Information Governance
### Data Quality
- Accuracy: correct
- Completeness: all
- Consistency: same
- Timeliness: current
- Validity: format

### Stewardship
- Steward: accountable
- Policies: manage
- Access: control
- Retention: schedule
- Disposal: secure

## Security
### Threats
- Malware: virus, ransomware
- Phishing: social
- Insider: employee
- Lost: device
- Hacking: external

### Safeguards
- Administrative: policies, training
- Physical: access, locks
- Technical: encryption, firewall, audit
- Access: role-based
- Authentication: multi-factor

## Common Pitfalls
- Poor usability
- Alert fatigue
- Copy-paste errors
- Interoperability gaps
- Privacy breaches
- Not backing up
- Not training staff
""", "tags": ["health informatics", "EHR", "HIPAA", "FHIR", "telemedicine", "reference"]}
    ],
    "health_sports_medicine": [
        {"title": "Sports Medicine Reference", "content": """# Sports Medicine Reference

## Pre-Participation Exam
### History
- Medical: conditions
- Surgical: past
- Family: sudden death
- Cardiovascular: symptoms
- Musculoskeletal: injuries
- Menstrual: females
- Supplements: use

### Physical
- Height, weight, BP
- Vision
- Cardiovascular: murmur
- Respiratory: asthma
- Musculoskeletal: screen
- Skin: contagious

### Clearance
- Full: no restrictions
- Limited: with modifications
- No: contraindicated

## Common Injuries
### Concussion
- Mechanism: head impact
- Symptoms: headache, dizziness, confusion
- Assessment: SCAT5
- Management: rest, gradual return
- Return to play: protocol
  1. Symptom-limited: rest
  2. Light aerobic
  3. Sport-specific
  4. Non-contact training
  5. Full contact (medical clearance)
  6. Return to play

### Ankle Sprain
- Lateral: most common
- Grades: I (mild), II (moderate), III (severe)
- Treatment: RICE, rehab
- Return: functional tests

### Knee
- ACL: pivot, swelling
- Meniscus: twist, catching
- Patellar: dislocation, tracking
- Osgood-Schlatter: adolescent

### Shoulder
- Dislocation: traumatic
- Rotator cuff: impingement, tear
- Labrum: SLAP
- AC: separation

### Elbow
- Lateral epicondylitis: tennis
- Medial epicondylitis: golf
- UCL: throwing

### Back
- Strain: muscle
- Spondylolysis: stress fracture
- Disc: herniation

### Overuse
- Stress fracture: bone
- Tendinopathy: tendon
- Apophysitis: growth plate

## Treatment
### Acute (RICE)
- Rest
- Ice
- Compression
- Elevation

### Rehabilitation
- Phase 1: reduce pain, swelling
- Phase 2: restore ROM, flexibility
- Phase 3: strengthen
- Phase 4: functional, sport-specific
- Phase 5: return to play

### Modalities
- Ice: acute
- Heat: chronic
- Electrical: TENS
- Ultrasound: deep heat
- Massage: soft tissue

### Injection
- Corticosteroid: inflammation
- PRP: healing
- Anesthetic: diagnose

## Taping and Bracing
- Tape: support, limit
- Brace: protect
- Indications: injury, prevention
- Technique: proper

## Exercise Prescription
### FITT
- Frequency: how often
- Intensity: how hard
- Time: how long
- Type: what kind

### Components
- Aerobic: cardio
- Strength: resistance
- Flexibility: stretch
- Balance: stability

### Special Populations
- Asthma: warm up, inhaler
- Diabetes: monitor glucose
- Hypertension: moderate
- Pregnancy: modify

## Nutrition
- Pre-event: carbs
- During: fluids, electrolytes
- Post: protein, carbs
- Hydration: before, during, after
- Supplements: evidence-based

## Performance
- Periodization: cycle training
- Overtraining: rest
- Recovery: sleep, nutrition
- Psychology: mental skills
- Ergogenic: legal aids

## Common Pitfalls
- Returning too soon
- Not following protocol
- Ignoring concussion
- Missing serious injury
- Not addressing underlying causes
- Over-treating with injections
""", "tags": ["sports medicine", "injury", "concussion", "rehabilitation", "reference"]}
    ],
}
