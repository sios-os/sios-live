"""Health & Medicine K3 Batch 1 - 6 specialties."""

HEALTH_K3_BATCH1: dict[str, list[dict]] = {
    "health_primary_care": [
        {"title": "Primary Care Practice Reference", "content": """# Primary Care Practice Reference

## Patient Care
### Visit Structure
1. Chief complaint: reason
2. History of present illness: HPI
3. Past medical history: PMH
4. Medications: current
5. Allergies: reactions
6. Family history: FH
7. Social history: SH
8. Review of systems: ROS
9. Physical exam: PE
10. Assessment: diagnosis
11. Plan: treatment

### Preventive Care
- Immunizations: per schedule
- Screenings: age-appropriate
  - Cancer: colon, breast, cervical
  - Cardiovascular: lipid, BP
  - Diabetes: glucose
  - Osteoporosis: DEXA
- Counseling: lifestyle
- Physical: annual

### Chronic Disease
- Hypertension: BP control
- Diabetes: glucose, A1c
- Hyperlipidemia: cholesterol
- COPD: lung function
- Asthma: control
- CHF: fluid
- CKD: kidney function
- Depression: mood

## Hypertension
### Classification (ACC/AHA)
- Normal: <120/<80
- Elevated: 120-129/<80
- Stage 1: 130-139/80-89
- Stage 2: >=140/>=90

### Treatment
- Lifestyle: diet, exercise, weight, salt
- Medications:
  - ACE inhibitor: lisinopril
  - ARB: losartan
  - CCB: amlodipine
  - Diuretic: HCTZ
  - Beta blocker: metoprolol
- Target: <130/80 (most)

## Diabetes
### Types
- Type 1: no insulin
- Type 2: insulin resistance
- Gestational: pregnancy

### Diagnosis
- A1c >= 6.5%
- Fasting glucose >= 126
- Random >= 200 with symptoms
- OGTT >= 200

### Management
- Lifestyle: diet, exercise, weight
- Monitoring: glucose, A1c
- Medications:
  - Metformin: first line
  - Sulfonylurea: glipizide
  - DPP-4: sitagliptin
  - GLP-1: semaglutide
  - SGLT2: empagliflozin
  - Insulin: type 1, advanced
- Target: A1c < 7% (most)
- Complications: prevent

## Common Conditions
### URI (Upper Respiratory Infection)
- Viral: most common
- Symptomatic: rest, fluids
- Antibiotics: not for viral
- Bacterial: strep (test)

### Otitis Media
- Often viral
- Observation: option
- Antibiotics: if severe
- Pain: acetaminophen, ibuprofen

### Sinusitis
- Viral: most
- Bacterial: >10 days, worsening
- Antibiotics: amoxicillin
- Symptomatic: saline, decongestant

### Pharyngitis
- Viral: most
- Strep: test (rapid, culture)
- Antibiotics: penicillin, amoxicillin

### Bronchitis
- Viral: most
- Cough: 1-3 weeks
- Antibiotics: usually not
- Symptomatic: rest, fluids

### Pneumonia
- Bacterial: strep pneumo
- Viral: flu, COVID
- Antibiotics: outpatient, inpatient
- Hospitalize: if severe

## Screening
### Cancer
- Colorectal: 45-75 (colonoscopy, FIT)
- Breast: 40-74 (mammography)
- Cervical: 21-65 (Pap, HPV)
- Lung: 50-80 (CT, smokers)
- Prostate: discuss (PSA)

### Cardiovascular
- Lipids: 35+ (men), 45+ (women)
- Blood pressure: all adults
- Aspirin: selective

### Other
- Diabetes: 35+ (overweight)
- HIV: 15-65
- Hepatitis C: 18-79
- Osteoporosis: 65+ (women), 70+ (men)
- Depression: all adults
- STI: risk-based

## Immunizations
### Adult
- Influenza: annually
- Tdap: every 10 years
- COVID: per guidance
- Pneumococcal: 65+
- Shingles: 50+
- HPV: to 26 (some to 45)
- MMR: if not immune
- Varicella: if not immune

### Travel
- Hepatitis A, B
- Typhoid
- Yellow fever
- Meningococcal
- Japanese encephalitis
- Rabies: pre-exposure

## Common Pitfalls
- Not following screening guidelines
- Overprescribing antibiotics
- Not addressing lifestyle
- Poor medication reconciliation
- Not coordinating with specialists
- Inadequate follow-up
""", "tags": ["primary care", "hypertension", "diabetes", "screening", "reference"]}
    ],
    "health_emergency_medicine": [
        {"title": "Emergency Medicine Practice Reference", "content": """# Emergency Medicine Practice Reference

## Approach
### ABCDE
- A: Airway (cervical spine)
- B: Breathing
- C: Circulation (bleeding)
- D: Disability (neuro)
- E: Exposure (temperature)

### Triage
- Level 1: immediate (life)
- Level 2: emergent (10 min)
- Level 3: urgent (30 min)
- Level 4: less urgent (60 min)
- Level 5: non-urgent (120 min)

## Resuscitation
### Airway
- Position: jaw thrust, head tilt
- Adjuncts: NPA, OPA
- Supraglottic: LMA
- Intubation: endotracheal
- Surgical: cricothyroidotomy

### Breathing
- Oxygen: nasal (1-5), mask (6-10)
- NRB: 15 L (high)
- BVM: bag valve mask
- CPAP/BiPAP: pressure
- Chest tube: pneumothorax

### Circulation
- IV access: 18G or larger
- IO: intraosseous
- Fluids: crystalloid
- Blood: transfuse
- CPR: chest compressions

## Cardiac Emergencies
### ACS (Acute Coronary Syndrome)
- STEMI: ST elevation
- NSTEMI: no ST elevation
- Unstable angina: no enzyme

### Management (STEMI)
- Aspirin: 325 mg chew
- P2Y12: ticagrelor, clopidogrel
- Anticoagulant: heparin
- Reperfusion:
  - PCI: <90 min (door-to-balloon)
  - Thrombolytics: if no PCI

### Arrhythmias
- VT with pulse: amiodarone, cardiovert
- VF: defibrillate, CPR, epi
- SVT: vagal, adenosine
- A-fib: rate, anticoagulate
- Bradycardia: atropine, pacing

### Cardiac Arrest
- BLS: CPR, AED
- ACLS: algorithms
- Reversible (H's and T's):
  - Hypovolemia, Hypoxia, H+, Hypo/Hyperkalemia, Hypothermia
  - Tension pneumo, Tamponade, Toxin, Thrombosis (cardiac, PE)

## Trauma
### Primary Survey
- Airway with C-spine
- Breathing
- Circulation
- Disability
- Exposure

### Secondary Survey
- Head: scalp, pupils
- Face: fractures
- Neck: tenderness, JVD
- Chest: breath sounds
- Abdomen: tenderness, rigidity
- Pelvis: stability
- Extremities: wounds, pulses
- Back: tenderness

### Head Trauma
- GCS: eye, verbal, motor
- CT: if indicated
- Herniation: unilateral fixed pupil

### Chest Trauma
- Tension pneumo: deviated trachea, needle decompress
- Hemothorax: chest tube
- Flail chest: segment, positive pressure
- Tamponade: Beck's triad

### Abdominal Trauma
- Blunt: CT scan
- Penetrating: explore
- FAST: bedside ultrasound
- DPL: diagnostic

### Spinal Trauma
- Immobilize: collar, board
- CT: cervical
- MRI: ligament
- Steroids: controversial

## Shock
### Types
- Hypovolemic: blood loss
- Cardiogenic: heart failure
- Obstructive: tamponade, PE, tension pneumo
- Distributive: septic, anaphylactic, neurogenic

### Recognition
- Tachycardia: early
- Hypotension: late
- Cold: hypovolemic, cardiogenic
- Warm: septic, neurogenic

### Treatment
- Fluids: crystalloid
- Blood: hemorrhage
- Vasopressors: shock
- Source: treat cause

## Sepsis
### Definition
- Infection + systemic response
- Sepsis: organ dysfunction
- Septic shock: hypotension despite fluids

### Management (Hour-1 Bundle)
- Lactate: measure
- Blood cultures: before antibiotics
- Antibiotics: broad-spectrum
- Fluids: 30 mL/kg crystalloid
- Vasopressors: if hypotensive

## Toxicology
### Approach
- History: what, when, how much
- Toxidrome: recognize pattern
- Decontaminate: GI, skin
- Antidote: if available
- Support: ABCs

### Common Toxidromes
- Anticholinergic: dry, hot, blind, mad
- Cholinergic: SLUDGE (salivation, lacrimation, urination, defecation, GI, emesis)
- Opioid: miosis, respiratory depression
- Sympathomimetic: mydriasis, tachy, hyper
- Sedative: depressed mental status

### Antidotes
- Naloxone: opioid
- Flumazenil: benzodiazepine
- NAC: acetaminophen
- Fomepizole: ethylene glycol, methanol
- Atropine: organophosphate
- Digoxin Fab: digoxin

## Pediatric
### Differences
- Smaller: size, weight
- Physiology: higher HR, RR
- Airway: different anatomy
- Weight-based: dosing

### Common
- Fever: source
- Dehydration: oral, IV
- Respiratory: RSV, croup, asthma
- Foreign body: airway, ingestion

## Common Pitfalls
- Not following ABCDE
- Inadequate resuscitation
- Missing time-critical diagnoses
- Not consulting specialists
- Poor documentation
- Not considering abuse (pediatric, elder)
""", "tags": ["emergency medicine", "trauma", "resuscitation", "sepsis", "reference"]}
    ],
    "health_cardiology": [
        {"title": "Cardiology Practice Reference", "content": """# Cardiology Practice Reference

## Anatomy
### Heart
- Four chambers: RA, RV, LA, LV
- Valves: tricuspid, pulmonary, mitral, aortic
- Coronary: LAD, LCx, RCA
- Conduction: SA node, AV node, His, Purkinje
- Layers: endocardium, myocardium, epicardium

## ECG
### Basics
- P wave: atrial depolarization
- PR interval: AV delay (120-200 ms)
- QRS: ventricular depolarization (<120 ms)
- ST segment: repolarization
- T wave: ventricular repolarization

### Interpretation
1. Rate: 300/RR interval
2. Rhythm: regular, irregular
3. Axis: normal, LAD, RAD
4. Intervals: PR, QRS, QT
5. Hypertrophy: atrial, ventricular
6. Ischemia: ST, T
7. Infarction: Q waves

### Ischemia/Infarction
- ST elevation: infarction
- ST depression: ischemia
- T inversion: ischemia
- Q waves: old infarct
- Location:
  - Inferior: II, III, aVF (RCA)
  - Anterior: V1-V4 (LAD)
  - Lateral: I, aVL, V5-V6 (LCx)
  - Septal: V1-V2 (LAD)

## Arrhythmias
### Brady
- Sinus bradycardia: <60
- Heart block:
  - 1st: PR >200 ms
  - 2nd Type I: progressive PR
  - 2nd Type II: constant PR, dropped
  - 3rd: complete, dissociation
- Treatment: atropine, pacing

### Tachy
- Sinus tachycardia: >100, normal P
- SVT: narrow, regular
- A-fib: irregular, no P
- A-flutter: sawtooth
- VT: wide, regular
- VF: chaotic
- Treatment:
  - Stable: medications
  - Unstable: cardiovert
  - Pulseless: defibrillate

## Coronary Artery Disease
### Risk Factors
- Non-modifiable: age, sex, family
- Modifiable: smoking, hypertension, diabetes, lipids, obesity, inactivity

### Angina
- Stable: predictable, relieved by rest
- Unstable: new, worsening, rest
- Variant (Prinzmetal): spasm

### ACS
- STEMI: ST elevation, urgent PCI
- NSTEMI: enzyme, no ST elevation
- Unstable angina: no enzyme

### Management
- Aspirin: 325 mg
- P2Y12 inhibitor: ticagrelor, clopidogrel
- Anticoagulant: heparin
- Statin: high intensity
- Beta blocker: if not in shock
- ACE inhibitor: if LV dysfunction
- Reperfusion: PCI or thrombolytics

## Heart Failure
### Types
- HFrEF: reduced EF (<40%)
- HFpEF: preserved EF (>=50%)
- Right: cor pulmonale

### Symptoms
- Left: dyspnea, orthopnea, PND, fatigue
- Right: edema, JVD, hepatomegaly

### Classification (NYHA)
- I: no symptoms
- II: slight limitation
- III: marked limitation
- IV: symptoms at rest

### Management
- Lifestyle: salt, fluid, weight
- Medications:
  - ACE inhibitor/ARB: mortality
  - Beta blocker: mortality
  - Aldosterone antagonist: mortality
  - Diuretic: symptoms
  - SGLT2 inhibitor: mortality
  - Digoxin: symptoms
- Device: ICD, CRT
- Advanced: transplant, LVAD

## Hypertension
### Classification (ACC/AHA)
- Normal: <120/<80
- Elevated: 120-129/<80
- Stage 1: 130-139/80-89
- Stage 2: >=140/>=90

### Treatment
- Lifestyle: weight, DASH diet, exercise, limit alcohol, sodium
- Medications:
  - ACE inhibitor: lisinopril
  - ARB: losartan
  - CCB: amlodipine
  - Thiazide: HCTZ, chlorthalidone
  - Beta blocker: not first line

## Valvular Disease
### Aortic Stenosis
- Systolic ejection murmur
- Symptoms: angina, syncope, heart failure
- Treatment: valve replacement (surgical, TAVR)

### Mitral Regurgitation
- Holosystolic murmur
- Acute: ischemia, endocarditis
- Chronic: degenerative
- Treatment: repair, replace

### Mitral Stenosis
- Diastolic murmur
- Cause: rheumatic
- Treatment: balloon, surgery

### Aortic Regurgitation
- Diastolic decrescendo
- Acute: dissection, endocarditis
- Chronic: degenerative
- Treatment: surgery

## Diagnostic Tests
### Echocardiography
- TTE: transthoracic
- TEE: transesophageal
- Measures: EF, valves, chambers
- Doppler: flow

### Stress Testing
- Exercise: treadmill, bike
- Pharmacologic: dobutamine, adenosine
- Imaging: ECG, echo, nuclear

### Cardiac Catheterization
- Coronary angiography
- PCI: stent
- Hemodynamics: pressures

### Other
- Holter: 24-48 hour
- Event monitor: weeks
- CT angiography: coronary
- MRI: structure, function
- Nuclear: perfusion

## Common Pitfalls
- Misreading ECG
- Not recognizing time-critical ACS
- Inadequate heart failure management
- Not addressing risk factors
- Not anticoagulating when needed
- Not following guidelines
""", "tags": ["cardiology", "ECG", "ACS", "heart failure", "arrhythmias", "reference"]}
    ],
    "health_neurology": [
        {"title": "Neurology Practice Reference", "content": """# Neurology Practice Reference

## Neurological Exam
### Mental Status
- Alertness: level
- Orientation: time, place, person
- Memory: immediate, recent, remote
- Language: fluency, comprehension, repetition
- Executive: drawing, abstraction

### Cranial Nerves
- I: olfactory (smell)
- II: optic (vision)
- III, IV, VI: eye movement
- V: trigeminal (facial sensation)
- VII: facial (movement)
- VIII: vestibulocochlear (hearing)
- IX, X: glossopharyngeal, vagus (swallow)
- XI: accessory (shoulder shrug)
- XII: hypoglossal (tongue)

### Motor
- Tone: spastic, rigid, flaccid
- Strength: 0-5 scale
- Atrophy: present
- Fasciculations: present

### Reflexes
- Deep tendon: 0-4 scale
  - Biceps, triceps, brachioradialis
  - Patellar, Achilles
- Babinski: up (abnormal)
- Hoffman: abnormal

### Sensory
- Light touch
- Pin prick (pain)
- Temperature
- Vibration (128 Hz)
- Proprioception (position)

### Coordination
- Finger-to-nose
- Heel-to-shin
- Rapid alternating
- Romberg

### Gait
- Normal
- Ataxic
- Spastic
- Shuffling
- Foot drop

## Stroke
### Types
- Ischemic: 85%
  - Thrombotic: atherosclerosis
  - Embolic: heart (A-fib)
  - Lacunar: small vessel
- Hemorrhagic: 15%
  - Intracerebral: hypertensive
  - Subarachnoid: aneurysm

### Recognition (FAST)
- Face: droop
- Arm: drift
- Speech: slurred
- Time: call 911

### Evaluation
- CT: hemorrhage vs ischemia
- CTA: vessel imaging
- MRI: diffusion (early ischemia)
- Carotid: stenosis
- ECG: A-fib
- Echo: clot source

### Treatment (Ischemic)
- tPA: <4.5 hours
- Thrombectomy: large vessel, <24 hours
- Antiplatelet: aspirin
- Statin: high intensity
- BP: permissive hypertension
- Glucose: control
- DVT prophylaxis

### Treatment (Hemorrhagic)
- BP: control
- ICP: manage
- Reverse anticoagulation
- Surgery: if needed

## Seizures
### Types
- Focal: partial
  - Aware
  - Impaired awareness
- Generalized
  - Tonic-clonic
  - Absence
  - Myoclonic
  - Atonic
- Unknown

### Status Epilepticus
- >5 minutes
- Treatment:
  - 1st: lorazepam (IV), midazolam (IM)
  - 2nd: fosphenytoin, levetiracetam
  - 3rd: intubate, propofol, midazolam drip

### Antiepileptics
- Focal: levetiracetam, lamotrigine, lacosamide
- Generalized: valproate, levetiracetam
- Absence: ethosuximide
- Consider: drug interactions, pregnancy

## Headache
### Primary
- Migraine: unilateral, throbbing, nausea, aura
- Tension: bilateral, pressure
- Cluster: unilateral, sharp, autonomic

### Secondary (Red Flags)
- Sudden: thunderclap (SAH)
- New: age >50 (temporal arteritis)
- Neurological: deficit (mass)
- Fever: infection
- Cancer: metastasis
- Pregnancy: pre-eclampsia

### Migraine Treatment
- Acute: triptan, NSAID, antiemetic
- Preventive: propranolol, topiramate, amitriptyline, CGRP
- Lifestyle: triggers, sleep, hydration

## Dementia
### Alzheimer's
- Most common
- Memory: recent
- Progressive: years
- Pathology: amyloid plaques, tau tangles
- Treatment: cholinesterase inhibitors, memantine

### Vascular
- Stepwise
- Vascular risk factors
- Imaging: infarcts

### Lewy Body
- Fluctuating cognition
- Visual hallucinations
- Parkinsonism
- REM sleep behavior

### Frontotemporal
- Personality change
- Language: early
- Age: younger

## Movement Disorders
### Parkinson's
- Resting tremor
- Bradykinesia
- Rigidity
- Postural instability
- Treatment: levodopa, dopamine agonist, MAO-B

### Essential Tremor
- Action tremor
- Family history
- Treatment: propranolol, primidone

## Neuromuscular
### Neuropathy
- Peripheral: diabetes, alcohol
- Mononeuropathy: carpal tunnel
- Diagnosis: EMG/NCS

### Myasthenia Gravis
- Fatigable weakness
- Ptosis, diplopia
- Diagnosis: AChR antibody, tensilon
- Treatment: pyridostigmine, immunosuppressant, thymectomy

### ALS
- Progressive weakness
- UMN and LMN
- No sensory
- Riluzole, edaravone

### MS
- Demyelinating
- Relapsing-remitting: most
- Diagnosis: MRI, CSF (oligoclonal)
- Treatment: DMT (disease-modifying)

## Diagnostic Tests
### Lumbar Puncture
- CSF: cells, protein, glucose
- Culture: infection
- Opening pressure

### EEG
- Seizures
- Encephalopathy
- Status epilepticus

### EMG/NCS
- Neuropathy
- Myopathy
- Neuromuscular junction

## Common Pitfalls
- Missing stroke (time-critical)
- Not recognizing status epilepticus
- Missing red flags in headache
- Not evaluating reversible dementia causes
- Not treating risk factors
- Over-ordering imaging
""", "tags": ["neurology", "stroke", "seizure", "dementia", "examination", "reference"]}
    ],
    "health_oncology": [
        {"title": "Oncology Practice Reference", "content": """# Oncology Practice Reference

## Cancer Biology
### Hallmarks
- Sustained proliferation
- Evade growth suppressors
- Resist cell death
- Replicative immortality
- Induce angiogenesis
- Invasion and metastasis
- Deregulated metabolism
- Evade immune destruction

### Genetics
- Oncogene: activated (gain)
- Tumor suppressor: inactivated (loss)
- DNA repair: defective
- Mutations: driver vs passenger

## Diagnosis
### Biopsy
- Tissue: gold standard
- Types: excisional, incisional, core, FNA
- Pathology: type, grade

### Imaging
- CT: anatomy
- MRI: detail
- PET: metabolic
- Bone scan: skeletal
- Ultrasound: guide

### Staging
- TNM system
- T: tumor size/extent
- N: lymph nodes
- M: metastasis
- Stage 0-IV

### Tumor Markers
- CEA: colon, breast
- CA-125: ovarian
- PSA: prostate
- AFP: liver, testicular
- hCG: testicular
- CA 19-9: pancreatic

## Treatment Modalities
### Surgery
- Curative: remove all
- Debulking: reduce
- Palliative: symptom
- Preventive: risk

### Radiation
- External beam: from outside
- Brachytherapy: inside
- Stereotactic: precise
- Palliative: symptom
- Side effects: local

### Chemotherapy
- Cytotoxic: kill dividing cells
- Adjuvant: after surgery
- Neoadjuvant: before surgery
- Palliative: advanced
- Side effects: systemic

### Targeted Therapy
- Kinase inhibitors: imatinib
- Monoclonal antibodies: trastuzumab
- Small molecules: erlotinib
- Biomarker: match

### Immunotherapy
- Checkpoint inhibitors: pembrolizumab
- CAR-T: cellular
- Vaccines: preventive, therapeutic
- Cytokines: IL-2, IFN

### Hormone Therapy
- Breast: tamoxifen, aromatase
- Prostate: androgen deprivation

## Common Cancers
### Breast
- Screening: mammography
- Types: ductal, lobular
- Receptors: ER, PR, HER2
- Treatment: surgery, radiation, chemo, hormone, targeted
- Risk: BRCA1/2

### Lung
- Screening: CT (smokers)
- Types: NSCLC (85%), SCLC (15%)
- Treatment: surgery, radiation, chemo, targeted, immunotherapy
- Molecular: EGFR, ALK, ROS1

### Colorectal
- Screening: colonoscopy, FIT
- Types: adenocarcinoma
- Treatment: surgery, chemo, targeted
- Genetics: APC, Lynch

### Prostate
- Screening: PSA (discuss)
- Treatment: active surveillance, surgery, radiation, hormone
- Risk: age, family, African American

### Melanoma
- Risk: UV exposure
- ABCDE: asymmetry, border, color, diameter, evolving
- Treatment: surgery, immunotherapy, targeted

### Leukemia
- Acute: AML, ALL
- Chronic: CML, CLL
- Treatment: chemo, targeted, stem cell

### Lymphoma
- Hodgkin: Reed-Sternberg
- Non-Hodgkin: many types
- Treatment: chemo, radiation, immunotherapy

## Side Effects
### Chemotherapy
- Myelosuppression: neutropenia, anemia, thrombocytopenia
- Nausea/vomiting: antiemetics
- Alopecia: hair loss
- Mucositis: mouth sores
- Neuropathy: numbness
- Fatigue: common

### Radiation
- Skin: burn
- Fatigue: common
- Local: organ specific
- Late: secondary cancer, fibrosis

### Immunotherapy
- Autoimmune: colitis, pneumonitis, hepatitis, endocrine
- Manage: steroids, hold

## Supportive Care
### Pain
- WHO ladder: non-opioid, opioid, strong
- Adjuvants: antidepressants, anticonvulsants
- Routes: oral, IV, epidural, patch

### Nausea
- 5-HT3: ondansetron
- NK1: aprepitant
- Steroids: dexamethasone
- Dopamine: metoclopramide

### Nutrition
- Assess: weight, intake
- Supplement: oral, tube, parenteral

### Palliative
- Symptoms: manage
- Goals: align with values
- Hospice: terminal

## Survivorship
### Surveillance
- Recurrence: monitor
- Second cancer: screen
- Late effects: manage

### Quality of Life
- Fatigue: exercise
- Distress: counseling
- Cognitive: chemo brain
- Sexual: address
- Financial: support

## Common Pitfalls
- Not discussing goals of care
- Not managing side effects
- Not coordinating care
- Not screening for recurrence
- Not addressing psychosocial
- Not considering clinical trials
""", "tags": ["oncology", "cancer", "chemotherapy", "radiation", "staging", "reference"]}
    ],
    "health_psychiatry": [
        {"title": "Psychiatry Practice Reference", "content": """# Psychiatry Practice Reference

## Assessment
### Mental Status Exam
- Appearance: grooming, posture
- Behavior: psychomotor, eye contact
- Speech: rate, volume, flow
- Mood: subjective (sad)
- Affect: objective (congruent)
- Thought process: logical, tangential
- Thought content: delusions, obsessions
- Perception: hallucinations
- Cognition: alert, oriented
- Insight: understanding
- Judgment: decision-making

### History
- Chief complaint
- HPI: onset, course
- Psychiatric history
- Substance use
- Medical history
- Medications
- Family history
- Social history
- Developmental history
- Forensic history

## Disorders
### Depressive Disorders
- Major depressive disorder (MDD)
  - 5+ symptoms for 2 weeks
  - SIGECAPS: Sleep, Interest, Guilt, Energy, Concentration, Appetite, Psychomotor, Suicidal
- Persistent depressive disorder: 2 years
- Adjustment: within 3 months of stressor

### Bipolar
- Bipolar I: mania (7 days) + depression
- Bipolar II: hypomania + depression
- Cyclothymic: 2 years
- Mania: elevated, grandiose, decreased sleep, pressured speech, racing thoughts, risky

### Anxiety
- GAD: excessive worry, 6 months
- Panic: recurrent attacks
- Agoraphobia: situations
- Social: performance, interaction
- Specific: object, situation

### OCD
- Obsessions: intrusive
- Compulsions: repetitive
- Cause: distress
- Treatment: SSRI, CBT (ERP)

### PTSD
- Trauma: actual, threatened
- Intrusion: memories, dreams
- Avoidance: stimuli
- Negative: mood, cognition
- Arousal: hypervigilant

### Psychotic
- Schizophrenia: 6 months
  - Positive: hallucinations, delusions, disorganized
  - Negative: flat, alogia, avolition
  - Cognitive: impaired
- Schizoaffective: psychosis + mood
- Brief: <1 month

### Personality
- Cluster A (odd): paranoid, schizoid, schizotypal
- Cluster B (dramatic): antisocial, borderline, histrionic, narcissistic
- Cluster C (anxious): avoidant, dependent, obsessive-compulsive

### Substance Use
- Intoxication: impaired
- Withdrawal: cessation
- Use disorder: tolerance, withdrawal, craving, loss of control
- Common: alcohol, opioid, stimulant, cannabis, nicotine

## Treatment
### Psychotherapy
- CBT: cognitive behavioral
  - Thoughts, feelings, behaviors
  - Skills, homework
- DBT: dialectical behavior
  - Emotion regulation, distress tolerance
- Psychodynamic: unconscious
- Supportive: practical
- IPT: interpersonal
- Family: system
- Group: peer

### Medications
#### Antidepressants
- SSRI: first line
  - Fluoxetine, sertraline, escitalopram
  - Side: GI, sexual, insomnia
- SNRI: venlafaxine, duloxetine
- Bupropion: NDRI, no sexual
- Mirtazapine: sleep, appetite
- TCA: older, toxic
- MAOI: diet restrictions

#### Mood Stabilizers
- Lithium: bipolar, monitor levels
- Valproate: bipolar
- Lamotrigine: bipolar depression
- Carbamazepine: bipolar

#### Antipsychotics
- Typical (1st gen): haloperidol
  - EPSE, tardive dyskinesia
- Atypical (2nd gen): risperidone, olanzapine, quetiapine, aripiprazole
  - Metabolic: weight, glucose, lipids
- Clozapine: treatment-resistant, monitor ANC

#### Anxiolytics
- Benzodiazepines: short-term
  - Alprazolam, lorazepam, clonazepam
  - Risk: dependence, overdose
- Buspirone: GAD, non-addictive

#### Stimulants
- ADHD: methylphenidate, amphetamine
- Side: appetite, sleep, cardiovascular

### Other Treatments
- ECT: severe depression, psychotic
- TMS: depression
- VNS: refractory
- Ketamine: treatment-resistant depression
- Light therapy: seasonal

## Emergency
### Suicide Risk
- Assess: ideation, plan, intent, means
- Risk factors: prior attempt, mood, substance, hopelessness
- Protective: reasons to live, support
- Action:
  - Low: outpatient
  - Moderate: intensive
  - High: hospitalize

### Violence
- Assess: history, command hallucinations, paranoia
- Action: hospitalize if needed

### Acute Psychosis
- Rule out: medical (delirium, drugs)
- Treat: antipsychotic
- Safety: monitor

## Special Populations
### Child/Adolescent
- ADHD: inattention, hyperactivity
- Autism: social, restricted
- ODD, conduct: behavior
- Anxiety, depression: mood

### Geriatric
- Dementia: cognitive
- Delirium: acute
- Depression: often missed
- Late-onset psychosis

### Pregnancy
- Risk vs benefit
- Avoid: valproate, lithium (1st trimester)
- Consider: SSRI (sertraline)
- Postpartum: depression, psychosis

## Common Pitfalls
- Not assessing suicide risk
- Missing medical causes
- Not monitoring medication side effects
- Not combining therapy and medication
- Not addressing substance use
- Not coordinating care
""", "tags": ["psychiatry", "mental health", "depression", "psychosis", "medications", "reference"]}
    ],
}
