"""Mind & Behavior K1 - All 5 specialties (one per batch)."""

MIND_K1_BATCH1: dict[str, list[dict]] = {
    "mind_cognitive_science": [
        {
            "title": "Cognitive Science - Field Overview",
            "content": """# Cognitive Science

## Definition
Cognitive science is the interdisciplinary study of mind and intelligence, combining philosophy, psychology, computer science, linguistics, neuroscience, and anthropology.

## Core Areas
- Perception: how senses construct reality
- Attention: selecting information for processing
- Memory: encoding, storage, retrieval (short-term, long-term, working)
- Language: comprehension, production, acquisition
- Reasoning and decision-making: heuristics, biases, logic
- Problem-solving: strategies, insight, expertise
- Consciousness: subjective experience, self-awareness
- Emotion: appraisal, regulation, influence on cognition

## Key Concepts
- Information processing: mind as computational system
- Representation: mental symbols standing for things
- Modularity: specialized cognitive systems (Fodor)
- Embodied cognition: mind shaped by body and environment
- Extended mind: cognition extends into tools and environment (Clark, Chalmers)
- Connectionism: neural network models of cognition
- Predictive processing: brain as prediction machine (Clark, Friston)
- Cognitive architecture: overall structure of mental processes

## Disciplines Contributing
- Philosophy: consciousness, intentionality, mental causation
- Psychology: experimental studies of cognition
- Computer science / AI: computational models
- Linguistics: language and thought (Chomsky)
- Neuroscience: brain basis of cognition
- Anthropology: cognition across cultures

## Foundational Texts
- Neisser, "Cognitive Psychology" (1967)
- Fodor, "The Modularity of Mind" (1983)
- Lakoff & Johnson, "Metaphors We Live By" (1980)
- Clark, "Supersizing the Mind" (2008)
- Thagard, "Mind: Introduction to Cognitive Science"

## Authority Note
Advisory. Cognitive science integrates multiple methods; claims should be supported by converging evidence.""",
            "tags": ["cognitive science", "mind", "cognition", "perception", "memory", "overview"],
        }
    ],
}

MIND_K1_BATCH2: dict[str, list[dict]] = {
    "mind_neuroscience": [
        {
            "title": "Neuroscience - Field Overview",
            "content": """# Neuroscience

## Definition
Neuroscience is the scientific study of the nervous system: its structure, function, development, genetics, biochemistry, physiology, pharmacology, and pathology.

## Core Areas
- Cellular neuroscience: neurons, glia, synapses
- Molecular neuroscience: ion channels, neurotransmitters, receptors
- Systems neuroscience: neural circuits and networks
- Behavioral neuroscience: brain-behavior relationships
- Cognitive neuroscience: neural basis of cognition
- Developmental neuroscience: nervous system development
- Neuroanatomy: structure of the brain and nerves
- Neurophysiology: electrical and chemical signaling
- Neuropharmacology: drugs and the nervous system
- Clinical neuroscience: neurological and psychiatric disorders

## Key Concepts
- Neuron: basic signaling unit of the nervous system
- Action potential: electrical signal along axon
- Synapse: junction between neurons
- Neurotransmitter: chemical messenger (glutamate, GABA, dopamine, serotonin, acetylcholine, norepinephrine)
- Neuroplasticity: brain's ability to reorganize
- Brain regions: cortex, cerebellum, hippocampus, amygdala, thalamus, basal ganglia, hypothalamus
- Lobes: frontal (planning, executive), parietal (sensory, spatial), temporal (auditory, memory), occipital (vision)
- Blood-brain barrier: protects brain from circulating substances
- Default mode network: active during rest, self-reflection

## Methods
- EEG: electrical activity, high temporal resolution
- MEG: magnetic fields, high temporal resolution
- fMRI: blood flow (BOLD), high spatial resolution
- PET: metabolic activity, radioactive tracers
- Optogenetics: light-controlled neurons
- Lesion studies: effects of brain damage
- Single-cell recording: individual neuron activity
- Diffusion tensor imaging (DTI): white matter tracts

## Foundational Texts
- Kandel et al., "Principles of Neural Science"
- Bear et al., "Neuroscience: Exploring the Brain"
- Purves et al., "Neuroscience"
- Gazzaniga et al., "Cognitive Neuroscience"

## Authority Note
Advisory. Neuroscience findings should be replicated; single studies are preliminary. Clinical claims require medical authority.""",
            "tags": ["neuroscience", "brain", "neurons", "synapses", "neurotransmitters", "overview"],
        }
    ],
}

MIND_K1_BATCH3: dict[str, list[dict]] = {
    "mind_human_factors": [
        {
            "title": "Human Factors - Field Overview",
            "content": """# Human Factors

## Definition
Human factors (ergonomics) is the scientific study of how humans interact with systems, tools, and environments, applying knowledge to improve safety, efficiency, and comfort.

## Core Areas
- Physical ergonomics: posture, biomechanics, workspace design
- Cognitive ergonomics: mental workload, decision-making, attention
- Organizational ergonomics: teamwork, shift work, communication
- Human-computer interaction: interface design, usability
- Safety engineering: error reduction, accident analysis
- Aviation human factors: cockpit design, crew resource management
- Medical human factors: patient safety, surgical teamwork
- Automotive human factors: driver attention, interface design

## Key Concepts
- Human error: slips (action), lapses (memory), mistakes (planning)
- Swiss cheese model: accidents occur when defenses align (Reason)
- Situation awareness: perceiving, comprehending, projecting (Endsley)
- Mental workload: cognitive demand vs capacity
- Affordance: perceived action possibilities (Gibson)
- Automation paradox: automation can reduce skills needed for manual takeover
- Fatigue: degrades performance; circadian rhythms matter
- Vigilance decrement: attention drops over time

## Methods
- Task analysis: decompose activities into steps
- Workload assessment: NASA-TLX, subjective ratings
- Usability testing: user performance with system
- Incident analysis: root cause, human factors analysis
- Simulation: controlled study of operator behavior
- Anthropometry: body measurements for design

## Foundational Texts
- Wickens et al., "An Introduction to Human Factors Engineering"
- Norman, "The Design of Everyday Things"
- Reason, "Human Error"
- Salvendy, "Handbook of Human Factors and Ergonomics"

## Authority Note
Advisory. Human factors guidance from FAA, FDA, and ISO standards is authoritative for regulated domains.""",
            "tags": ["human factors", "ergonomics", "usability", "safety", "human error", "overview"],
        }
    ],
}

MIND_K1_BATCH4: dict[str, list[dict]] = {
    "mind_learning_science": [
        {
            "title": "Learning Science - Field Overview",
            "content": """# Learning Science

## Definition
Learning science is the interdisciplinary study of how people learn, drawing on cognitive science, educational psychology, computer science, neuroscience, and anthropology to design effective learning environments.

## Core Areas
- Learning theories: behaviorism, cognitivism, constructivism, connectivism
- Instructional design: systematic design of learning experiences
- Assessment: measuring learning outcomes
- Learning environments: physical, digital, hybrid
- Collaborative learning: peer interaction, group cognition
- Motivation: intrinsic, extrinsic, self-determination theory
- Metacognition: thinking about one's own thinking
- Transfer: applying learning to new contexts
- Expertise development: novice-to-expert progression

## Key Concepts
- Schema: mental framework for organizing knowledge
- Zone of proximal development: gap between what learner can do alone vs with help (Vygotsky)
- Scaffolding: temporary support for learning
- Spaced repetition: distributed practice improves retention
- Active learning: engaging with material vs passive reception
- Desirable difficulties: challenges that enhance long-term learning (Bjork)
- Cognitive load: working memory capacity limits (Sweller)
- Constructivism: learners actively build knowledge (Piaget, Vygotsky)
- Communities of practice: social learning (Lave & Wenger)

## Learning Theories
- Behaviorism: learning as behavior change (Skinner, Pavlov)
- Cognitivism: learning as mental process (Piaget, Bruner)
- Constructivism: learning as knowledge construction (Vygotsky, Papert)
- Social learning: learning through observation (Bandura)
- Connectivism: learning in networked environments (Siemens)

## Foundational Texts
- Bransford et al., "How People Learn"
- Sawyer, "The Cambridge Handbook of the Learning Sciences"
- Vygotsky, "Mind in Society"
- Papert, "Mindstorms"

## Authority Note
Advisory. Educational claims should be supported by empirical evidence from controlled studies.""",
            "tags": ["learning science", "education", "learning theories", "instructional design", "overview"],
        }
    ],
}

MIND_K1_BATCH5: dict[str, list[dict]] = {
    "mind_educational_psychology": [
        {
            "title": "Educational Psychology - Field Overview",
            "content": """# Educational Psychology

## Definition
Educational psychology is the study of how people learn in educational settings, including learning processes, instructional methods, individual differences, and assessment.

## Core Areas
- Developmental psychology: cognitive, social, emotional development
- Learning and motivation: what drives learning
- Individual differences: intelligence, learning styles, disabilities
- Instructional psychology: effective teaching methods
- Classroom management: behavior, climate, engagement
- Assessment and measurement: tests, grades, portfolios
- Special education: learning disabilities, giftedness, interventions
- Multicultural education: cultural factors in learning

## Key Concepts
- Intelligence: general (g), multiple (Gardner), triarchic (Sternberg)
- Working memory: limited capacity, central to learning
- Self-efficacy: belief in one's capability (Bandura)
- Growth mindset: ability is malleable (Dweck)
- Achievement goal theory: mastery vs performance goals
- Self-regulated learning: planning, monitoring, reflecting
- Pygmalion effect: expectations influence performance
- Bloom's taxonomy: knowledge, comprehension, application, analysis, synthesis, evaluation

## Developmental Stages
- Piaget: sensorimotor, preoperational, concrete, formal
- Erikson: trust, autonomy, initiative, industry, identity, intimacy, generativity, integrity
- Kohlberg: preconventional, conventional, postconventional moral reasoning

## Assessment Types
- Formative: ongoing, for learning (feedback during)
- Summative: final, of learning (exams, grades)
- Diagnostic: identify gaps and needs
- Authentic: real-world tasks, portfolios
- Norm-referenced: compare to peers
- Criterion-referenced: compare to standards

## Foundational Texts
- Woolfolk, "Educational Psychology"
- Slavin, "Educational Psychology: Theory and Practice"
- Piaget, "The Psychology of the Child"
- Vygotsky, "Thought and Language"
- Dweck, "Mindset"

## Authority Note
Advisory. Educational psychology findings should be replicated in diverse settings. Single studies may not generalize.""",
            "tags": ["educational psychology", "development", "assessment", "motivation", "overview"],
        }
    ],
}
