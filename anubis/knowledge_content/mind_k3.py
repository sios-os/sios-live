"""Mind & Behavior K3 - All 5 specialties (one per batch)."""

MIND_K3_BATCH1: dict[str, list[dict]] = {
    "mind_cognitive_science": [
        {
            "title": "Cognitive Architecture and Mental Processes Reference",
            "content": """# Cognitive Architecture Reference

## Memory Systems

### Sensory Memory
- Iconic (visual): ~500ms duration, large capacity
- Echoic (auditory): ~3-4s duration
- Haptic (touch): ~2s duration

### Short-Term / Working Memory
- Capacity: 7 +/- 2 items (Miller, 1956); revised to ~4 (Cowan)
- Duration: ~15-30s without rehearsal
- Phonological loop: verbal rehearsal
- Visuospatial sketchpad: visual/spatial storage
- Central executive: attention control (Baddeley)
- Episodic buffer: integrates information

### Long-Term Memory
- Declarative (explicit):
  - Episodic: personal events, time/place
  - Semantic: facts, concepts, knowledge
- Non-declarative (implicit):
  - Procedural: skills, habits (riding a bike)
  - Priming: exposure influences later response
  - Classical conditioning: associative learning

## Attention
- Selective attention: filter relevant, ignore irrelevant
- Divided attention: multitasking (costly, not truly parallel)
- Sustained attention: vigilance (decrements over time)
- Spotlight model: attention as beam (Posner)
- Load theory: perceptual load determines distraction (Lavie)

### Attention Biases
- Neglect: ignoring one side (usually left) after right parietal damage
- Inattentional blindness: missing unexpected stimuli (Simons & Chabris gorilla)
- Change blindness: failing to notice changes

## Reasoning and Decision-Making

### Heuristics (Kahneman & Tversky)
- Availability: judge frequency by ease of recall
- Representativeness: judge by similarity to stereotype
- Anchoring: insufficient adjustment from initial value
- Affect heuristic: decisions driven by emotion

### Biases
- Confirmation bias: seek evidence that confirms beliefs
- Hindsight bias: "I knew it all along"
- Dunning-Kruger: low ability overestimates competence
- Sunk cost fallacy: continuing due to past investment
- Framing effects: choices affected by presentation
- Base rate neglect: ignoring prior probabilities

### Dual Process Theory (Kahneman)
- System 1: fast, automatic, intuitive, emotional
- System 2: slow, deliberate, logical, effortful
- Most daily decisions use System 1
- System 2 used for novel, complex problems

## Language and Thought
- Sapir-Whorf hypothesis: language shapes thought (linguistic relativity)
- Strong version: language determines thought (largely rejected)
- Weak version: language influences thought (supported)
- Categorical perception: color, spatial relations affected by language

## Problem Solving
- Means-ends analysis: reduce gap between current and goal
- Working backward: start from goal
- Analogy: transfer solution from similar problem
- Insight: sudden realization (Aha! moment)
- Functional fixedness: inability to see new uses for objects
- Expertise: pattern recognition, chunking, automated procedures

## Consciousness
- Global workspace theory: consciousness as broadcast (Baars)
- Integrated information theory: consciousness as integrated information (Tononi, Phi)
- Higher-order theories: consciousness as representation of mental state
- Hard problem (Chalmers): why is there subjective experience at all?
- Qualia: subjective qualities of experience

## Common Pitfalls
- Treating brain imaging as mind reading
- Generalizing from small or WEIRD (Western, Educated, Industrialized, Rich, Democratic) samples
- Confusing correlation with causation in brain-behavior links
- Over-attributing to cognitive biases (they are context-dependent)
- Assuming dual process theory is fully settled
""",
            "tags": ["cognitive science", "memory", "attention", "reasoning", "consciousness", "reference"],
        }
    ],
}

MIND_K3_BATCH2: dict[str, list[dict]] = {
    "mind_neuroscience": [
        {
            "title": "Neuroanatomy and Neural Signaling Reference",
            "content": """# Neuroanatomy and Neural Signaling Reference

## Brain Structure

### Cerebral Cortex
- Frontal lobe: executive function, planning, motor control, language production (Broca's area)
- Parietal lobe: somatosensory processing, spatial attention, integration
- Temporal lobe: auditory processing, memory (hippocampus), language comprehension (Wernicke's area)
- Occipital lobe: visual processing

### Subcortical Structures
- Hippocampus: memory formation, spatial navigation
- Amygdala: fear, emotion, social processing
- Thalamus: relay station for sensory information
- Hypothalamus: homeostasis, hormones, autonomic control
- Basal ganglia: motor control, habit learning, reward
- Cerebellum: motor coordination, balance, some cognitive functions
- Brainstem: breathing, heart rate, sleep/wake, consciousness

### Cortical Organization
- Brodmann areas: 52 regions based on cytoarchitecture
- Somatotopic maps: motor and sensory homunculi
- Tonotopic maps: frequency organization in auditory cortex
- Retinotopic maps: visual field organization in visual cortex

## Neural Signaling

### Resting Potential
- ~-70mV inside relative to outside
- Maintained by Na+/K+ pump (3 Na+ out, 2 K+ in)
- High K+ inside, high Na+ outside

### Action Potential
1. Threshold: ~-55mV
2. Depolarization: Na+ channels open, Na+ rushes in
3. Peak: ~+30mV
4. Repolarization: K+ channels open, K+ rushes out
5. Hyperpolarization: K+ channels slow to close, undershoot
6. Refractory period: cannot fire again (absolute) or harder to fire (relative)

### Synaptic Transmission
1. Action potential reaches axon terminal
2. Ca2+ channels open, Ca2+ enters
3. Vesicles release neurotransmitter into synaptic cleft
4. Neurotransmitter binds receptors on postsynaptic cell
5. Signal terminated by reuptake, degradation, or diffusion

### Neurotransmitters
- Glutamate: main excitatory; learning, memory
- GABA: main inhibitory; anxiety, sleep
- Dopamine: reward, motor control, motivation; Parkinson's (deficit), schizophrenia (excess)
- Serotonin: mood, appetite, sleep; depression (implicated)
- Norepinephrine: arousal, attention, stress response
- Acetylcholine: muscle activation, memory, learning; Alzheimer's (deficit)
- Histamine: wakefulness, allergic response
- Endorphins: pain relief, pleasure

## Neural Plasticity
- Long-term potentiation (LTP): sustained strengthening of synapses
- Long-term depression (LTD): sustained weakening
- Synaptic pruning: elimination of unused synapses (development, sleep)
- Neurogenesis: new neuron formation (hippocampus, olfactory bulb)
- Critical periods: windows of heightened plasticity (vision, language)

## Brain Imaging Methods

### Structural
- CT: X-ray based, good for bleeding, fractures
- MRI: magnetic, high resolution, soft tissue
- DTI: white matter tracts

### Functional
- fMRI: BOLD signal (blood oxygenation), ~2-6s lag, mm spatial resolution
- EEG: electrical, ms temporal resolution, cm spatial resolution
- MEG: magnetic, ms temporal, cm spatial
- PET: radioactive tracers, metabolic activity
- fNIRS: near-infrared, cortical blood oxygenation

## Common Pitfalls
- Reverse inference: seeing area X active, concluding mental process Y
- Voodoo correlations: inflated brain-behavior correlations
- Treating fMRI as direct measure of neural activity (it's blood flow)
- Ignoring individual differences in brain anatomy
- Over-generalizing from animal models to humans
- Confusing structural with functional imaging
""",
            "tags": ["neuroscience", "neuroanatomy", "action potential", "synapses", "neurotransmitters", "reference"],
        }
    ],
}

MIND_K3_BATCH3: dict[str, list[dict]] = {
    "mind_human_factors": [
        {
            "title": "Human Error and System Safety Reference",
            "content": """# Human Error and System Safety Reference

## Error Classification (Reason)

### Slips
- Action not as intended
- Detection: usually noticed quickly
- Types:
  - Capture errors: familiar sequence overrides intended
  - Description errors: similar objects confused
  - Mode errors: wrong system mode assumed
  - Loss-of-activation errors: forgetting to do something

### Lapses
- Memory failure
- Types: forgetting intended action, place-losing

### Mistakes
- Action as intended, but plan was wrong
- Rule-based: wrong rule applied
- Knowledge-based: incomplete mental model
- Detection: often delayed

## Swiss Cheese Model (Reason)
```
Hazard -> [Organizational] -> [Supervisory] -> [Preconditions] -> [Unsafe acts] -> Accident
              holes              holes             holes              holes
```
- Each layer has defenses with holes
- Accident occurs when holes align
- Fix: reduce holes in each layer, not just blame operator

## Situation Awareness (Endsley)
1. Perception: perceive relevant elements
2. Comprehension: understand their meaning
3. Projection: anticipate future state

### Loss of SA
- Information not perceived (attention elsewhere)
- Information perceived but not understood
- Understood but not projected forward

## Crew Resource Management (CRM)
- Originated in aviation after United 173 (1978)
- Principles:
  - Communication: assertive, clear
  - Leadership: team coordination
  - Decision-making: structured, participatory
  - Workload management: task prioritization
  - Situational awareness: shared mental model
- Now used in medicine, maritime, rail, nuclear

## Automation
### Levels (Sheridan & Verplank)
1. Computer offers no assistance
2. Computer offers suggestions
3. Computer selects action, human approves
4. Computer executes, human can veto
5. Computer executes, informs human
6. Computer executes, informs only if asked
7. Computer executes, informs only if decides to
8. Computer selects method, executes, ignores human

### Automation Paradox
- More automation -> less operator engagement
- When automation fails, operator less prepared
- Solution: keep operator in the loop, practice manual skills

## Workload Assessment
### NASA-TLX
- Mental demand
- Physical demand
- Temporal demand
- Performance
- Effort
- Frustration
- Weighted score based on pairwise comparisons

### Objective Measures
- Pupil dilation: increases with workload
- Heart rate variability: decreases with workload
- Secondary task performance: degrades with primary load
- EEG: beta power increases with workload

## Fatigue
- Circadian: performance worst at 3-5 AM and 3-5 PM
- Sleep deprivation: 17h awake = 0.05% BAC; 24h = 0.10% BAC
- Microsleeps: 1-15s lapses, often unnoticed
- Chronotype: morning vs evening types
- Shift work: rotating shifts worst for adaptation

## Design Principles for Safety
- Forcing functions: prevent incorrect actions (e.g., car must be in park to start)
- Interlocks: sequence constraints
- Lock-ins: prevent premature exit
- Lock-outs: prevent entering dangerous states
- Warnings: last resort, not primary defense
- Standardization: reduce mode errors
- Feedback: make system state visible

## Common Pitfalls
- Blaming operator instead of system design
- Adding warnings instead of fixing design
- Over-automating without keeping operator engaged
- Ignoring fatigue and circadian effects
- Designing for ideal conditions, not real ones
- Not testing with real users under realistic workload
""",
            "tags": ["human factors", "human error", "safety", "CRM", "automation", "reference"],
        }
    ],
}

MIND_K3_BATCH4: dict[str, list[dict]] = {
    "mind_learning_science": [
        {
            "title": "Evidence-Based Learning Strategies Reference",
            "content": """# Evidence-Based Learning Strategies Reference

## Highly Effective Strategies

### Spaced Practice
- Distribute study over time rather than cramming
- Expanding schedule: 1 day, 3 days, 1 week, 2 weeks
- Effect size: large (d > 0.5)
- Mechanism: retrieval effort strengthens memory

### Retrieval Practice
- Testing yourself improves learning more than re-reading
- Flashcards, practice tests, free recall
- Effect size: large
- Even when retrieval fails, learning occurs
- Feedback after retrieval enhances effect

### Interleaving
- Mix different problem types rather than blocking by type
- Especially effective for math, motor skills
- Forces discrimination between strategies
- Effect size: moderate to large

### Elaboration
- Connect new information to existing knowledge
- Ask "why" and "how" questions
- Generate examples
- Create concept maps (after learning, not during)

### Dual Coding
- Combine verbal and visual information
- Words + images > words alone
- Generate mental images of concepts

## Less Effective / Ineffective Strategies

### Highlighting/Underlining
- Little benefit for learning
- Can create illusion of competence
- May focus on details at expense of main ideas

### Re-reading
- Familiarity mistaken for mastery
- Minimal learning benefit beyond first read
- Time-consuming

### Summarization
- Only effective if trained in technique
- Often done poorly by students

## Controversial Strategies

### Learning Styles
- Visual, auditory, kinesthetic learners
- No evidence that matching instruction to style improves learning
- Widely believed but unsupported (Pashler et al., 2008)

### Brain Gym
- Claimed brain exercises improve learning
- No scientific support

### Mozart Effect
- Listening to Mozart improves intelligence
- Effect is small and temporary, if real

## Motivation and Learning

### Self-Determination Theory (Deci & Ryan)
- Autonomy: sense of choice
- Competence: feeling capable
- Relatedness: connection to others
- Intrinsic motivation > extrinsic for deep learning

### Growth Mindset (Dweck)
- Intelligence is malleable, not fixed
- Effort > talent
- Praise process, not ability
- Mixed evidence on classroom interventions

### Achievement Goals
- Mastery: learn for understanding
- Performance-approach: do better than others
- Performance-avoidance: avoid doing worse
- Mastery goals associated with deeper learning

## Metacognition
- Plan: set goals, select strategies
- Monitor: check understanding during learning
- Evaluate: assess effectiveness after learning
- Judgment of learning: how well do I know this?
- Dunning-Kruger: novices overestimate, experts underestimate

## Cognitive Load Theory (Sweller)
- Intrinsic load: inherent difficulty of material
- Extraneous load: poor design adds unnecessary load
- Germane load: productive effort for schema construction
- Design instruction to minimize extraneous, optimize germane

## Common Pitfalls
- Confusing performance during learning with long-term retention
- Illusion of competence: familiarity feels like mastery
- Cramming feels productive but is less effective than spaced practice
- Not testing oneself (retrieval practice feels harder but works better)
- Believing in learning styles despite lack of evidence
- Teaching learning strategies without modeling and practice
""",
            "tags": ["learning science", "spaced practice", "retrieval practice", "motivation", "reference"],
        }
    ],
}

MIND_K3_BATCH5: dict[str, list[dict]] = {
    "mind_educational_psychology": [
        {
            "title": "Developmental Psychology and Assessment Reference",
            "content": """# Developmental Psychology and Assessment Reference

## Piaget's Stages
1. Sensorimotor (0-2): object permanence, sensory exploration
2. Preoperational (2-7): symbolic thought, egocentrism, lack conservation
3. Concrete operational (7-11): conservation, classification, logical thought
4. Formal operational (11+): abstract reasoning, hypothetical thinking

### Critiques of Piaget
- Underestimates infant competence
- Stages less discrete than proposed
- Cultural variation in timing
- Vygotsky: social interaction is central, not just individual exploration

## Vygotsky
- Zone of Proximal Development (ZPD): what learner can do with help
- Scaffolding: temporary support, gradually removed
- More Knowledgeable Other (MKO): teacher, peer, tool
- Cultural tools: language shapes thought
- Private speech: self-talk as self-regulation

## Erikson's Psychosocial Stages
1. Trust vs Mistrust (0-1): basic security
2. Autonomy vs Shame (1-3): independence
3. Initiative vs Guilt (3-6): purpose
4. Industry vs Inferiority (6-12): competence
5. Identity vs Role Confusion (12-18): self-concept
6. Intimacy vs Isolation (18-40): relationships
7. Generativity vs Stagnation (40-65): contribution
8. Integrity vs Despair (65+): life review

## Kohlberg's Moral Development
1. Preconventional: punishment, reward
2. Conventional: social norms, law and order
3. Postconventional: social contract, universal ethics

### Critique
- Gender bias (Gilligan): women emphasize care, men justice
- Cultural bias: postconventional reflects Western liberalism
- Confounds moral reasoning with moral behavior

## Intelligence Theories

### Spearman's g
- General intelligence factor
- Underlies all cognitive abilities
- Supported by factor analysis

### Gardner's Multiple Intelligences
- Linguistic, logical-mathematical, spatial, musical, bodily-kinesthetic, interpersonal, intrapersonal, naturalistic
- Popular in education but limited empirical support

### Sternberg's Triarchic Theory
- Analytical, Creative, Practical intelligence
- More empirically supported than Gardner

### Cattell-Horn-Carroll (CHC)
- Fluid intelligence (Gf): novel problem-solving
- Crystallized intelligence (Gc): acquired knowledge
- Visual processing, short-term memory, long-term storage, processing speed

## Assessment Principles

### Reliability
- Test-retest: consistency over time
- Internal consistency: items measure same construct (Cronbach's alpha)
- Inter-rater: consistency between scorers

### Validity
- Content: test covers domain
- Construct: test measures intended construct
- Criterion: test predicts outcomes
- Face: test appears to measure construct (weakest)

### Item Analysis
- Difficulty: proportion correct (0.3-0.7 ideal)
- Discrimination: high scorers more likely correct
- Distractor analysis: wrong options chosen evenly

### Bias in Testing
- Cultural bias: items favor one group
- Stereotype threat: awareness of stereotype depresses performance (Steele)
- Test anxiety: degrades performance
- Accommodations: extended time, alternative formats

## Special Education
- Learning disabilities: dyslexia (reading), dyscalculia (math), dysgraphia (writing)
- ADHD: inattention, hyperactivity, impulsivity
- Autism spectrum: social communication, restricted interests
- Giftedness: exceptional ability; needs challenge, not acceleration alone
- Response to Intervention (RTI): tiered support before special education referral
- Individualized Education Program (IEP): legal document in US

## Common Pitfalls
- Treating developmental stages as rigid
- Assuming intelligence is fixed (growth mindset)
- Over-relying on standardized tests
- Confusing reliability with validity
- Cultural bias in assessment
- Labeling students rather than supporting needs
- Not differentiating instruction for diverse learners
""",
            "tags": ["educational psychology", "development", "intelligence", "assessment", "special education", "reference"],
        }
    ],
}
