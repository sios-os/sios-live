"""Language & Communication K3 - 26 specialties in 5 batches (6+5+5+5+5)."""

LANGUAGE_K3_BATCH1: dict[str, list[dict]] = {
    "language_linguistics": [
        {"title": "Phonology, Syntax, and Semantics Reference", "content": """# Phonology, Syntax, and Semantics Reference

## Phonology

### Phonemes
- Minimal pairs: distinguish meaning (pat vs bat)
- Allophones: variants of same phoneme
  - Aspirated vs unaspirated /p/ in English
- Complementary distribution: never contrast
- Free variation: optional variation

### Syllable Structure
- Onset: initial consonant(s)
- Nucleus: vowel (required)
- Coda: final consonant(s)
- CV: most common
- English allows CCCVCCCC

### Phonological Processes
- Assimilation: become more similar
- Dissimilation: become less similar
- Insertion (epenthesis): add sound
- Deletion: remove sound
- Lenition: weakening
- Fortition: strengthening

### Suprasegmentals
- Stress: emphasis
- Tone: pitch distinguishes meaning
- Intonation: pitch across sentence
- Length: duration

## Syntax

### Generative Grammar (Chomsky)
- Phrase structure rules: S -> NP VP
- Transformational rules: move, delete, insert
- Deep structure: underlying
- Surface structure: actual
- Universal Grammar: innate
- Principles and Parameters: shared + variable

### X-bar Theory
- XP: phrase (NP, VP, AP, PP)
- X': intermediate level
- Head: X
- Specifier: sister of X'
- Complement: sister of head
- Adjunct: sister of X'

### Government and Binding
- Theta roles: agent, patient, theme, goal
- Case: nominative, accusative, etc.
- Binding: referential relations
  - Principle A: anaphors bound locally
  - Principle B: pronouns free locally
  - Principle C: R-expressions free everywhere
- Movement: NP-movement, Wh-movement

### Minimalist Program
- Merge: combine elements
- Agree: feature checking
- Move: internal merge
- Economy: least effort

### Dependency Grammar
- Head-dependent relations
- No phrase structure
- Useful for parsing

## Semantics

### Truth-Conditional
- Meaning = truth conditions
- Proposition: what can be true or false
- Entailment: A entails B if A true -> B true
- Presupposition: assumed true
- Implicature: implied but not stated (Grice)

### Compositionality
- Meaning of whole from parts + structure
- Frege's principle
- Function application: predicate + argument

### Reference
- Proper names: refer directly
- Definite descriptions: unique referent
- Deictic: context-dependent (I, here, now)
- Anaphora: refers back

### Sense Relations
- Synonymy: same meaning
- Antonymy: opposite
  - Gradable: hot/cold
  - Complementary: alive/dead
  - Converse: buy/sell
- Hyponymy: type of (dog is hyponym of animal)
- Meronymy: part of (finger is meronym of hand)

### Ambiguity
- Lexical: multiple word meanings (bank)
- Structural: multiple parses (flying planes can be dangerous)
- Scope: quantifier order (every student read a book)

## Pragmatics

### Speech Acts (Austin, Searle)
- Locutionary: saying
- Illocutionary: doing (promising, warning)
- Perlocutionary: effect
- Felicity conditions: requirements for success

### Grice's Maxims
- Quantity: right amount of info
- Quality: be truthful
- Relation: be relevant
- Manner: be clear

### Relevance Theory (Sperber & Wilson)
- Communication seeks relevance
- Cognitive effects vs processing effort

## Common Pitfalls
- Confusing phoneme with allophone
- Treating syntax as just word order
- Equating semantics with reference
- Ignoring context in pragmatics
- Treating categories as binary
""", "tags": ["linguistics", "phonology", "syntax", "semantics", "pragmatics", "Chomsky", "reference"]}
    ],
    "language_writing_rhetoric": [
        {"title": "Rhetorical Theory and Writing Process Reference", "content": """# Rhetorical Theory and Writing Process Reference

## Classical Rhetoric

### Five Canons
1. Invention (inventio): finding arguments
2. Arrangement (dispositio): organizing
3. Style (elocutio): choosing language
4. Memory (memoria): remembering
5. Delivery (pronuntiatio): presenting

### Three Appeals (Aristotle)
- Ethos: credibility of speaker
  - Phronesis: practical wisdom
  - Arete: virtue
  - Eunoia: goodwill toward audience
- Pathos: emotional appeal
  - Vivid examples
  - Storytelling
  - Emotional language
- Logos: logical appeal
  - Syllogism: major premise, minor premise, conclusion
  - Enthymeme: syllogism with assumed premise
  - Example: specific case to general

### Types of Speech (Aristotle)
- Deliberative: future policy
- Forensic: past events (legal)
- Epideictic: present (praise/blame)

### Rhetorical Situations (Bitzer)
- Exigence: problem needing address
- Audience: who can act
- Constraints: limits on action

## Modern Rhetoric

### Burke: Identification
- Persuasion through identification
- Division creates need for identification
- Terministic screen: language shapes perception
- Guilt-purification-redemption cycle

### Perelman: New Rhetoric
- Universal audience: ideal reasoners
- Particular audience: specific group
- Quasi-logical arguments
- Presence: making present to mind

### Toulmin Model
- Claim: assertion
- Data: evidence
- Warrant: connects data to claim
- Backing: support for warrant
- Qualifier: degree of certainty
- Rebuttal: exceptions

### Foucault: Discourse
- Power/knowledge
- Discourse constructs reality
- Author function
- Regimes of truth

## Writing Process

### Stages
1. Prewriting: brainstorm, research, outline
2. Drafting: get words down
3. Revising: restructure, develop
4. Editing: refine sentences
5. Proofreading: catch errors
6. Publishing: share

### Invention Techniques
- Freewriting: write without stopping
- Brainstorming: list ideas
- Clustering: map connections
- Journalist questions: who, what, when, where, why, how
- Cubing: describe, compare, associate, analyze, apply, argue

### Argumentation
- Claim: thesis
- Evidence: support
- Reasoning: connect evidence to claim
- Counterargument: acknowledge opposing view
- Rebuttal: refute counterargument

### Types of Evidence
- Empirical: data, statistics
- Anecdotal: stories
- Testimonial: expert opinion
- Analogical: comparison
- Logical: reasoning from premises

## Style

### Clarity (Williams)
- Characters as subjects
- Actions as verbs
- Old information before new
- Short sentences for emphasis
- Long sentences for connection

### Conciseness
- Remove redundancy
- Use active voice
- Strong verbs
- Specific nouns

### Tone
- Formal: academic, professional
- Informal: conversational
- Technical: specialized
- Persuasive: argumentative
- Narrative: storytelling

## Common Pitfalls
- Confusing persuasion with manipulation
- Ignoring audience
- Over-relying on one appeal
- Weak evidence
- Logical fallacies
- Not revising enough
- Confusing editing with revising
""", "tags": ["writing", "rhetoric", "Aristotle", "Toulmin", "Burke", "process", "reference"]}
    ],
    "language_journalism_media_studies": [
        {"title": "Journalism Ethics and Media Theory Reference", "content": """# Journalism Ethics and Media Theory Reference

## Journalism Ethics (SPJ Code)

### Four Principles
1. Seek truth and report it
   - Accuracy, verification
   - Don't distort
   - Identify sources when possible
   - Avoid stereotypes
   - Distinguish news from advocacy

2. Minimize harm
   - Compassion for those affected
   - Recognize privacy
   - Balance public need vs harm
   - Special care with vulnerable

3. Act independently
   - Avoid conflicts of interest
   - Disclose unavoidable conflicts
   - Refuse gifts, favors, fees
   - Hold powerful accountable

4. Be accountable and transparent
   - Explain decisions
   - Encourage dialogue
   - Acknowledge mistakes
   - Expose unethical practices

## News Values
- Timeliness: recent
- Impact: affects many
- Prominence: important people
- Proximity: close to audience
- Conflict: disagreement
- Human interest: emotional
- Novelty: unusual
- Magnitude: large scale

## Media Theory

### Agenda Setting (McCombs & Shaw)
- Media doesn't tell what to think
- Media tells what to think about
- Framing: how story presented
- Priming: activating evaluation standards

### Cultivation Theory (Gerbner)
- Heavy viewing cultivates worldview
- Mean world syndrome
- Mainstreaming: convergence of views
- Resonance: when reality matches TV

### Uses and Gratifications (Katz)
- Active audience
- Needs: information, identity, integration, entertainment
- Media chosen to fulfill needs

### Spiral of Silence (Noelle-Neumann)
- Fear of isolation
- Minority views suppressed
- Media amplifies majority
- Quasi-statistical organ: sense of opinion

### Political Economy (Garnham, Mosco)
- Ownership concentration
- Commodity audience
- Ideological role of media
- Global media flows

### Cultural Studies (Hall)
- Encoding/decoding
- Dominant, negotiated, oppositional readings
- Representation
- Ideology

## Digital Journalism

### Changes
- Speed: real-time publishing
- Multiplicity: many voices
- Interactivity: audience participation
- Data: computational journalism
- Mobile: on-the-go consumption

### Challenges
- Verification in real-time
- Misinformation and disinformation
- Filter bubbles and echo chambers
- Business model sustainability
- Trust decline

### Verification
- Multiple sources
- Original documents
- On-the-ground reporting
- Digital verification: image, video, location
- Source reliability assessment

## Media Law (US)

### First Amendment
- Freedom of press
- Limits: defamation, obscenity, incitement

### Defamation
- Libel: written
- Slander: spoken
- Elements: false, published, fault, harm
- Public figures: actual malice (New York Times v. Sullivan)
- Private figures: negligence

### Privacy
- Intrusion: physical or technological
- Private facts: embarrassing, not newsworthy
- False light: misleading portrayal
- Appropriation: using likeness

### Copyright (Fair Use)
- Purpose: news reporting favored
- Nature: factual more than creative
- Amount: small portion
- Effect: not substitute for original

### Shield Laws
- Protect sources
- Vary by state
- No federal shield (US)

## Common Pitfalls
- Publishing before verifying
- Confusing balance with false equivalence
- Sensationalism
- Conflict of interest
- Plagiarism
- Not correcting errors
- Invasion of privacy
""", "tags": ["journalism", "ethics", "SPJ", "media theory", "media law", "reference"]}
    ],
    "language_translation_studies": [
        {"title": "Translation Theory and Methods Reference", "content": """# Translation Theory and Methods Reference

## Equivalence

### Nida's Types
- Formal equivalence: form and content
- Dynamic equivalence: equivalent effect
- Functional equivalence: updated term for dynamic

### Koller's Equivalence
- Denotative: same referent
- Connotative: same connotations
- Text-normative: same text type
- Pragmatic: same effect on receiver
- Formal: same form

## Translation Strategies (Vinay & Darbelnet)

### Direct
- Borrowing: take word directly
- Calque: literal translation of phrase
- Literal translation: word for word

### Oblique
- Transposition: change word class
- Modulation: change perspective
- Equivalence: same situation, different expression
- Adaptation: cultural substitution

## Major Theories

### Skopos Theory (Vermeer, Reiss)
- Translation purpose determines method
- Target audience matters
- Function over form
- Adequacy over equivalence

### Polysystem Theory (Even-Zohar)
- Literature as system of systems
- Translated literature position: central or peripheral
- When central: innovation
- When peripheral: conservative

### Descriptive Translation Studies (Toury)
- Study actual translations
- Norms: translational behavior
- Preliminary norms: selection, policy
- Operational norms: matricial, textual-linguistic

### Cultural Turn (Bassnett, Lefevere)
- Translation as cultural practice
- Patronage: power and ideology
- Refractions: adaptations of literature
- Translation and power

### Sociological Turn (Wolf, Inghilleri)
- Translator as social agent
- Habitus (Bourdieu): dispositions
- Field: translation as social field
- Agency: translator's role

## Translation Types

### Literary
- Poetry: form and meaning
- Prose: narrative
- Drama: performability
- Challenges: wordplay, culture, voice

### Technical
- Terminology: precise
- Consistency: same term, same translation
- Subject expertise needed
- Style: clear, concise

### Legal
- Legal systems differ
- Terminology: system-specific
- Sworn translation: certified
- Challenges: equivalents across systems

### Medical
- Accuracy critical
- Terminology: standardized
- Patient-facing vs professional
- Regulatory compliance

## Translation Process

### Stages
1. Analysis: understand source
2. Transfer: convert meaning
3. Restructuring: create target text
4. Revision: review and refine

### Competence (PACTE)
- Bilingual: language skills
- Extra-linguistic: world knowledge
- Translation knowledge: theory
- Instrumental: tools
- Strategic: problem-solving
- Psycho-physiological: cognitive

## Quality Assessment

### Error Typology
- Accuracy: meaning errors
- Fluency: language errors
- Terminology: term errors
- Style: register errors
- Mechanics: spelling, punctuation

### Methods
- Error analysis: count and classify
- Holistic: overall judgment
- Back-translation: translate back, compare
- Peer review: another translator
- Client feedback: end user

## Machine Translation

### Approaches
- Rule-based: grammar rules
- Statistical: parallel corpora
- Neural (NMT): deep learning
- Hybrid: combination

### Post-editing
- Light: fix critical errors
- Full: near-human quality
- Challenges: monotony, style
- Productivity: faster than human translation

## Common Pitfalls
- Literal translation of idioms
- Ignoring cultural context
- Inconsistent terminology
- Not researching subject
- Over-domestication or over-foreignization
- Not using CAT tools
- Not proofreading
""", "tags": ["translation", "equivalence", "Skopos", "Nida", "machine translation", "reference"]}
    ],
    "language_interpretation": [
        {"title": "Interpretation Techniques and Ethics Reference", "content": """# Interpretation Techniques and Ethics Reference

## Modes of Interpretation

### Simultaneous
- Render while speaker talks
- Lag: 1-3 seconds behind
- Equipment: booth, headset, microphone
- Cognitive load: high
- Teams: 2 interpreters, 30-min shifts
- Used: conferences, EU, UN

### Consecutive
- Render after speaker pauses
- Note-taking: essential
- Segments: 2-10 minutes
- Memory: trained
- Used: meetings, court, medical

### Sight Translation
- Read source, speak target
- Hybrid: translation + interpretation
- Used: documents in court, medical

### Whispered (Chuchotage)
- Whisper to 1-2 people
- No equipment
- Used: small meetings, social events

### Relay
- Through intermediate language
- Risk: compounding errors
- Used: when no direct interpreter

### Liasion
- Three-way: interpreter mediates
- Both directions
- Used: business, community

## Consecutive Note-Taking

### Principles
- Notes aid memory, not replace it
- Note ideas, not words
- Use symbols and abbreviations
- Vertical layout: logical progression
- Links: arrows, lines
- Numbers: write out
- Proper names: write clearly

### Rozan's Principles
- Note ideas, not words
- Note less in source, more in target
- Abbreviate: standard symbols
- Transpose: change word order if helpful
- Link: show relationships

### Common Symbols
- ^: increase, up
- v: decrease, down
- ->: leads to
- !=: different from
- =: equals, same
- ?: question
- !: emphasis, important
- *: refer back

## Cognitive Skills

### Memory
- Chunking: group information
- Visualization: mental images
- Association: link to known
- Active listening: focus

### Attention
- Split attention: listen and speak
- Selective: filter distractions
- Sustained: long periods

### Anticipation
- Predict what comes next
- Based on context, structure
- Reduces lag

## Ethics

### Confidentiality
- All information confidential
- No disclosure without consent
- Exceptions: legal requirements

### Accuracy
- Render everything
- Don't add, omit, change
- Acknowledge errors

### Impartiality
- No favoring either party
- No advice or opinions
- Maintain neutrality

### Conflict of Interest
- Disclose any relationship
- Decline if conflict
- No personal gain

### Professional Conduct
- Maintain competence
- Continue professional development
- Respect colleagues
- Represent qualifications honestly

## Settings

### Conference
- Subject preparation: research topic
- Terminology: glossary
- Briefings: with speakers
- Teamwork: coordinate with partner

### Court
- Legal terminology
- Procedure: understand process
- Rights: ensure understanding
- Impartiality: critical
- Certification: required in many jurisdictions

### Medical
- Medical terminology
- Patient confidentiality (HIPAA)
- Cultural sensitivity
- Family: avoid using family members
- Certification: recommended

### Community
- Public services: social, legal, health
- Three-way communication
- Cultural broker: explain context
- Power dynamics: aware

## Common Pitfalls
- Not preparing subject matter
- Poor note-taking
- Adding or omitting information
- Giving advice or opinions
- Not acknowledging errors
- Working too long without break
- Not maintaining confidentiality
""", "tags": ["interpretation", "simultaneous", "consecutive", "note-taking", "ethics", "reference"]}
    ],
    "language_terminology_management": [
        {"title": "Terminology Theory and Practice Reference", "content": """# Terminology Theory and Practice Reference

## General Theory of Terminology (Wuster)
- Concept first: onomasiological
- Standardization: one term per concept
- Clear definitions
- International standards
- Objectivity

## Communicative Theory (Sager)
- Terms in use, not just theory
- Socioterminology: variation accepted
- Multiple terms per concept possible
- Context matters
- Documentation of usage

## Sociocognitive Terminology (Temmerman)
- Concepts evolve
- Categorization flexible
- Prototype theory: fuzzy boundaries
- Definition includes motivation

## Terminology Work

### Steps
1. Domain analysis: understand field
2. Term extraction: identify terms
3. Term research: find definitions, contexts
4. Concept analysis: clarify concepts
5. Definition writing: precise
6. Term selection: choose preferred
6. Database entry: record
7. Validation: expert review
8. Dissemination: publish

### Term Extraction
- Manual: read texts, identify
- Automatic: software tools
  - Statistical: frequency
  - Linguistic: patterns
  - Hybrid: combination
- Corpus: representative texts
- Bilingual: aligned corpora

### Definition Writing (ISO 704)
- Intensional: genus + differentia
- Extensional: list members
- Partitive: parts of whole
- Rules:
  - Not circular
  - Not negative
  - Appropriate to field
  - Concise
  - No examples in definition

## Termbase

### Structure (TBX, TermBase eXchange)
- Concept: unit of knowledge
- Term: designation
- Term entry: full record
- Language sections: per language
- Fields: term, definition, context, source, status

### Fields
- Term: the designation
- Part of speech: noun, verb
- Definition: precise meaning
- Context: usage example
- Source: where from
- Reliability: confidence
- Status: preferred, admitted, deprecated
- Synonym: same concept
- Acronym: abbreviated form
- Translation: other languages

### Standards
- ISO 704: principles and methods
- ISO 1087: terminology vocabulary
- ISO 12620: data categories
- ISO 16642: TBX format
- ISO 30042: TBX exchange

## Terminology in Practice

### Translation
- Consistency: same term, same translation
- Termbase: shared resource
- Pre-translation: prepare before project
- Validation: review during and after

### Standardization
- National bodies: ANSI, BSI, DIN
- International: ISO, IEC
- Industry: IEEE, W3C
- Company: internal standards

### Controlled Vocabularies
- Authorized terms only
- Prevent synonyms
- Aid search and retrieval
- Examples: MeSH, LCSH

## Ontologies

### Types
- Upper: general concepts (DOLCE, SUMO)
- Domain: specific field
- Task: activities
- Application: specific use

### Components
- Classes: categories
- Instances: individuals
- Properties: relationships
- Axioms: constraints

### Standards
- RDF: resource description
- OWL: web ontology language
- SKOS: simple knowledge organization

## Common Pitfalls
- Confusing term with concept
- Circular definitions
- Not validating with experts
- Inconsistent termbase structure
- Not updating termbase
- Ignoring context
- Mixing synonym and homonym
""", "tags": ["terminology", "Wuster", "ISO 704", "termbase", "TBX", "ontology", "reference"]}
    ],
}

LANGUAGE_K3_BATCH2: dict[str, list[dict]] = {
    "language_localization": [
        {"title": "Localization Engineering and Workflows Reference", "content": """# Localization Engineering and Workflows Reference

## Internationalization (I18n)

### Principles
- Design for localization from start
- Separate code from content
- No hard-coded strings
- Unicode support
- Locale-aware functions

### Technical
- Character encoding: UTF-8
- String externalization: resource files
- Date/time: locale-aware formatting
- Numbers: locale-aware (1,000.00 vs 1.000,00)
- Currency: locale-aware
- Plural rules: varies by language
- Gender: varies by language
- Sorting: locale-aware collation
- Text direction: LTR and RTL
- Text length: expansion/contraction

### Pseudolocalization
- Test before translation
- Replace characters with accented
- Add length: detect truncation
- Detect hard-coded strings

## Localization (L10n) Process

### Steps
1. Preparation: extract translatable content
2. Translation: convert text
3. Engineering: adapt code, layout
4. Testing: verify functionality
5. Bug fixing: resolve issues
6. Release: deploy localized version

### Translatable Content
- UI strings: buttons, menus, labels
- Documentation: manuals, help
- Marketing: website, campaigns
- Audio: voiceover, subtitles
- Images: text in graphics
- Legal: terms, privacy

### File Formats
- Properties: Java
- XML: Android, generic
- JSON: web, modern
- PO/Gettext: open source
- XLIFF: industry standard
- YAML: configuration
- ResX: .NET

## Tools

### CAT (Computer-Assisted Translation)
- Translation memory: reuse previous
- Termbase: terminology
- Alignment: match source and target
- QA: consistency checks
- Examples: SDL Trados, memoQ, OmegaT

### Management Systems (TMS)
- Workflow: project management
- Automation: file handling
- Vendors: manage translators
- Reporting: metrics
- Examples: Phrase, Transifex, Crowdin, Lokalise

### Machine Translation
- Pre-translation: MT first, then post-edit
- Post-editing: human correction
- Integration: API in workflow
- Quality: NMT generally best

## Testing

### Linguistic Testing
- Translation accuracy
- Context appropriateness
- Tone and style
- Terminology consistency
- Cultural appropriateness

### Functional Testing
- UI layout: text expansion
- Truncation: text cut off
- Encoding: characters display
- Sorting: correct order
- Date/time: correct format
- Currency: correct format
- Hotkeys: conflicts

### Cosmetic Testing
- Visual appearance
- Alignment
- Fonts: support characters
- Graphics: localized images

## Locale Considerations

### Date and Time
- Format: MM/DD/YYYY vs DD/MM/YYYY
- Calendar: Gregorian, Hijri, Hebrew
- Time zone: UTC offsets
- 12 vs 24 hour

### Numbers
- Decimal separator: . vs ,
- Thousands separator: , vs .
- Negative: -123 vs (123)

### Currency
- Symbol: $, EUR, JPY
- Position: before or after
- Format: 1,000.00 vs 1.000,00

### Names and Addresses
- Name order: given-family vs family-given
- Address format: varies by country
- Postal code: varies

### Cultural
- Colors: meanings vary (red: luck in China, danger in West)
- Symbols: gestures, icons
- Taboos: religious, cultural
- Humor: doesn't translate

## Common Pitfalls
- Not internationalizing first
- Hard-coded strings
- Not testing with real content
- Ignoring text expansion
- Not supporting Unicode
- Not considering RTL
- Not testing cultural appropriateness
- Not using translation memory
""", "tags": ["localization", "I18n", "L10n", "CAT tools", "testing", "reference"]}
    ],
    "language_english": [
        {"title": "English Grammar and Usage Reference", "content": """# English Grammar and Usage Reference

## Phonology
- Vowels: 20 (RP), varies by dialect
- Consonants: 24
- Stress: variable, phonemic
- Intonation: rising (question), falling (statement)

## Parts of Speech
- Noun: person, place, thing, idea
- Pronoun: replaces noun (I, you, he, she, it, we, they)
- Verb: action or state
- Adjective: describes noun
- Adverb: describes verb, adjective, adverb
- Preposition: relationship (in, on, at)
- Conjunction: connects (and, but, or)
- Interjection: emotion (oh, wow)
- Determiner: introduces noun (the, a, this)

## Nouns
- Count: can be counted (book, books)
- Non-count: cannot (water, information)
- Proper: capitalized (London, John)
- Common: not capitalized
- Concrete: physical
- Abstract: ideas
- Collective: group (team, family)
- Possessive: 's or '

## Verbs
- Tenses:
  - Present: I walk
  - Past: I walked
  - Future: I will walk
  - Present perfect: I have walked
  - Past perfect: I had walked
  - Future perfect: I will have walked
  - Present continuous: I am walking
  - Past continuous: I was walking
  - Future continuous: I will be walking
- Aspects: simple, continuous, perfect, perfect continuous
- Moods: indicative, imperative, subjunctive
- Voice: active (I hit), passive (I was hit)
- Modal: can, could, may, might, must, shall, should, will, would

## Sentence Structure
- Simple: one clause
- Compound: two independent clauses (and, but, or)
- Complex: independent + dependent
- Compound-complex: both

### Clauses
- Independent: stands alone
- Dependent: cannot stand alone
  - Noun clause: acts as noun
  - Adjective clause: acts as adjective (relative)
  - Adverb clause: acts as adverb

### Word Order
- SVO: subject-verb-object (declarative)
- VSO: questions (Is he coming?)
- SOV: rare in English
- Inversion: VS in questions, after negatives

## Agreement
- Subject-verb: singular subject, singular verb
- Pronoun-antecedent: match in number, gender, person
- Collective nouns: singular or plural (British vs American)

## Articles
- A: before consonant sound
- An: before vowel sound
- The: specific reference
- Zero: general, plural, non-count

## Conditionals
- Zero: If + present, present (facts)
- First: If + present, will + base (real future)
- Second: If + past, would + base (unreal present)
- Third: If + past perfect, would have + past participle (unreal past)
- Mixed: combinations

## Common Errors
- There/their/they're
- Your/you're
- Its/it's
- Affect/effect
- Then/than
- Who/whom
- Who's/whose
- Lie/lay
- Sit/set
- Rise/raise

## Style (Strunk & White)
- Omit needless words
- Use active voice
- Use parallel structure
- Place emphatic words at end
- Keep related words together
- Express coordinate ideas in similar form

## Common Pitfalls
- Confusing tense and aspect
- Subject-verb agreement errors
- Misplaced modifiers
- Dangling participles
- Comma splices
- Run-on sentences
- Sentence fragments
- Overusing passive voice
""", "tags": ["English", "grammar", "tenses", "syntax", "usage", "reference"]}
    ],
    "language_spanish": [
        {"title": "Spanish Grammar and Usage Reference", "content": """# Spanish Grammar and Usage Reference

## Phonology
- Vowels: 5 (a, e, i, o, u), pure
- Consonants: distinctive /theta/ (Spain), /x/
- Stress: rules with accent marks
- Syllable-timed rhythm

## Nouns and Articles
- Gender: masculine (el), feminine (la)
- Articles: el, la, los, las, un, una, unos, unas
- Agreement: noun, article, adjective
- Neuter: lo (abstract)

## Adjectives
- Agreement: gender and number
- Position: usually after noun
- Demonstrative: este, ese, aquel
- Possessive: mi, tu, su, nuestro, vuestro
- Comparatives: mas...que, menos...que
- Superlatives: -isimo, muy

## Verbs
- Three conjugations: -ar, -er, -ir
- Tenses:
  - Present: hablo
  - Preterite: hable (completed past)
  - Imperfect: hablaba (ongoing past)
  - Future: hablare
  - Conditional: hablaria
  - Present perfect: he hablado
  - Past perfect: habia hablado
  - Future perfect: habre hablado
  - Conditional perfect: habria hablado
- Subjunctive:
  - Present: hable
  - Imperfect: hablara/hablase
  - Present perfect: haya hablado
  - Past perfect: hubiera hablado
- Imperative: habla (tu), hable (usted)
- Gerund: hablando
- Participle: hablado

## Ser vs Estar
- Ser: identity, origin, characteristics (Soy doctor)
- Estar: state, location, condition (Estoy cansado)
- DOCTOR vs PLACE mnemonic

## Por vs Para
- Por: cause, means, duration, exchange
- Para: purpose, destination, recipient, deadline

## Pronouns
- Subject: often omitted (pro-drop)
- Direct object: me, te, lo, la, nos, os, los, las
- Indirect object: me, te, le, nos, os, les
- Reflexive: me, te, se, nos, os, se
- Prepositional: mi, ti, el, ella, etc.
- Double object: se (le + lo -> se lo)

## Subjunctive Uses
- Wish: Quiero que vengas
- Emotion: Me alegro que estes aqui
- Doubt: Dudo que venga
- Impersonal: Es importante que estudies
- After certain conjunctions: antes de que, para que

## Regional Variation
- Seseo: /s/ for /theta/ (Latin America)
- Yeismo: /y/ for /ll/ (much of Spanish-speaking world)
- Voseo: use of vos (Argentina, Uruguay, etc.)
- Ustedes: replaces vosotros (Latin America)

## Common Pitfalls
- Confusing ser and estar
- Confusing por and para
- Misusing subjunctive
- Preterite vs imperfect
- Not using personal a
- Pronoun placement (enclitic)
- Gender agreement
""", "tags": ["Spanish", "grammar", "ser estar", "subjunctive", "por para", "reference"]}
    ],
    "language_french": [
        {"title": "French Grammar and Usage Reference", "content": """# French Grammar and Usage Reference

## Phonology
- Vowels: 16 (RP), including nasal
- Liaison: linking consonant
- Enchainement: consonant-vowel linking
- Stress: always final syllable

## Nouns and Articles
- Gender: masculine (le), feminine (la)
- Articles: le, la, les, un, une, des
- Partitive: du, de la, de l', des (some)
- Contractions: du (de + le), des (de + les), au (a + le), aux (a + les)

## Adjectives
- Agreement: gender and number
- Position: usually after, some before (BANGS: Beauty, Age, Number, Goodness, Size)
- Comparatives: plus...que, moins...que, aussi...que
- Superlatives: le plus, le moins

## Verbs
- Three groups: -er, -ir, -re
- Tenses:
  - Present: je parle
  - Passe compose: j'ai parle (past)
  - Imparfait: je parlais (ongoing past)
  - Passe simple: je parlai (literary)
  - Futur: je parlerai
  - Conditionnel: je parlerais
  - Plus-que-parfait: j'avais parle
  - Futur anterieur: j'aurai parle
- Subjunctive:
  - Present: que je parle
  - Past: que j'aie parle
  - Imperfect: que je parlasse (literary)
- Imperative: parle, parlons, parlez
- Participle: parle (past), parlant (present)

## Passe Compose vs Imparfait
- Passe compose: completed action
- Imparfait: ongoing, habitual, description
- Example: Je lisais quand il est arrive

## Pronouns
- Subject: je, tu, il, elle, nous, vous, ils, elles
- Direct object: me, te, le, la, nous, vous, les
- Indirect object: me, te, lui, nous, vous, leur
- Reflexive: me, te, se, nous, vous, se
- Y: there, to it
- En: some, of it
- Order: me te se nous vous + le la les + lui leur + y + en

## Subjunctive Uses
- Wish: Je veux que tu viennes
- Emotion: Je suis content que tu sois la
- Doubt: Je doute qu'il vienne
- Necessity: Il faut que tu partes
- After certain conjunctions: avant que, pour que, bien que

## Negation
- ne...pas: not
- ne...plus: no more
- ne...jamais: never
- ne...rien: nothing
- ne...personne: nobody
- ne...que: only

## Common Pitfalls
- Confusing passe compose and imparfait
- Subjunctive vs indicative
- Pronoun order
- Agreement of past participle
- Liaison errors
- Gender of nouns
- False cognates
""", "tags": ["French", "grammar", "passe compose", "imparfait", "subjunctive", "reference"]}
    ],
    "language_german": [
        {"title": "German Grammar and Usage Reference", "content": """# German Grammar and Usage Reference

## Phonology
- Vowels: a, e, i, o, u, a, o, u (umlauts), au, ei, eu
- Consonants: distinctive /x/ (ach), /c/ (ich)
- Stress: usually first syllable of root

## Nouns
- Gender: masculine (der), feminine (die), neuter (das)
- Plural: die (all plurals)
- Capitalized: all nouns

## Cases
- Nominative: subject
- Accusative: direct object
- Dative: indirect object
- Genitive: possession

### Definite Articles
- Masculine: der, den, dem, des
- Feminine: die, die, der, der
- Neuter: das, das, dem, des
- Plural: die, die, den, der

### Indefinite Articles
- Masculine: ein, einen, einem, eines
- Feminine: eine, eine, einer, einer
- Neuter: ein, ein, einem, eines

## Adjectives
- Declension: strong, mixed, weak
- Agreement: gender, number, case
- Position: before noun
- Comparative: -er
- Superlative: am -sten

## Verbs
- Two conjugations: weak (regular), strong (vowel change)
- Tenses:
  - Present: ich spreche
  - Past (imperfect): ich sprach (strong), ich machte (weak)
  - Perfect: ich habe gesprochen (most), ich bin gegangen (motion)
  - Past perfect: ich hatte gesprochen
  - Future: ich werde sprechen
  - Future perfect: ich werde gesprochen haben
- Separable prefixes: ankommen (ich komme an)
- Inseparable prefixes: verstehen
- Modal: konnen, mussen, durfen, sollen, wollen, mochten

## Word Order
- Main clause: V2 (verb second)
  - Subject verb object
  - Heute gehe ich ins Kino
- Subordinate clause: verb final
  - Ich weiß, dass er nach Hause geht
- Questions: verb first (Kommst du?)
- Commands: verb first (Komm!)

## Prepositions
- Accusative: durch, fur, gegen, ohne, um
- Dative: aus, bei, mit, nach, seit, von, zu
- Genitive: wahrend, wegen, (an)statt
- Two-way (Wechselprapositionen): an, auf, in, uber, unter, vor, zwischen, hinter, neben
  - Accusative: motion (Wohin?)
  - Dative: location (Wo?)

## Pronouns
- Subject: ich, du, er, sie, es, wir, ihr, sie/Sie
- Accusative: mich, dich, ihn, sie, es, uns, euch, sie
- Dative: mir, dir, ihm, ihr, ihm, uns, euch, ihnen
- Possessive: mein, dein, sein, ihr, sein, unser, euer, ihr

## Common Pitfalls
- Case errors
- Gender memorization
- Adjective declension
- Word order in subordinate clauses
- Separable vs inseparable prefixes
- Strong verb conjugation
- Dative vs accusative with two-way prepositions
""", "tags": ["German", "grammar", "cases", "word order", "reference"]}
    ],
}

LANGUAGE_K3_BATCH3: dict[str, list[dict]] = {
    "language_italian": [
        {"title": "Italian Grammar and Usage Reference", "content": """# Italian Grammar and Usage Reference

## Phonology
- Vowels: 7 (a, e, open e, i, o, open o, u)
- Double consonants: geminate
- Stress: usually penultimate
- Syllable-timed

## Nouns and Articles
- Gender: masculine (il), feminine (la)
- Articles:
  - Definite: il, lo, la, l', i, gli, le
  - Indefinite: un, uno, una, un'
- Preposition + article: del, dello, della, dei, degli, delle

## Adjectives
- Agreement: gender and number
- Position: usually after noun
- BANGS-like: before for beauty, goodness, size, age, number

## Verbs
- Three conjugations: -are, -ere, -ire
- Tenses:
  - Present: parlo
  - Passato prossimo: ho parlato (past)
  - Imperfetto: parlavo (ongoing past)
  - Passato remoto: parlai (literary past)
  - Future: parlero
  - Conditional: parlerei
  - Trapassato: avevo parlato
- Subjunctive:
  - Present: che io parli
  - Past: che io abbia parlato
  - Imperfect: che io parlassi
- Imperative: parla, parli, parliamo, parlate, parlino

## Passato Prossimo vs Imperfetto
- Passato prossimo: completed action
- Imperfetto: ongoing, habitual, description
- Example: Leggevo quando e arrivato

## Pronouns
- Subject: io, tu, lui, lei, noi, voi, loro
- Direct: mi, ti, lo, la, ci, vi, li, le
- Indirect: mi, ti, gli, le, ci, vi, gli
- Reflexive: mi, ti, si, ci, vi, si
- Position: before verb, or attached to infinitive

## Prepositions
- Simple: di, a, da, in, con, su, per, tra, fra
- Articulated: preposition + article

## Common Pitfalls
- Passato prossimo vs imperfetto
- Subjunctive vs indicative
- Article choice (il vs lo)
- Pronoun placement
- Gender agreement
- False friends with English
""", "tags": ["Italian", "grammar", "passato prossimo", "imperfetto", "subjunctive", "reference"]}
    ],
    "language_portuguese": [
        {"title": "Portuguese Grammar and Usage Reference", "content": """# Portuguese Grammar and Usage Reference

## Phonology
- Vowels: 14 (European), 8 (Brazilian), nasal
- Nasal vowels: a, e, o
- Stress: variable, accent marks

## Nouns and Articles
- Gender: masculine (o), feminine (a)
- Articles: o, a, os, as, um, uma, uns, umas
- Contractions: do, da, no, na, ao, a

## Verbs
- Three conjugations: -ar, -er, -ir
- Tenses:
  - Present: falo
  - Preterite: falei (completed past)
- Imperfect: falava (ongoing past)
  - Future: falarei
  - Conditional: falaria
  - Present perfect: tenho falado
- Subjunctive:
  - Present: que eu fale
  - Imperfect: se eu falasse
  - Future: quando eu falar
- Personal infinitive: unique to Portuguese
- Imperative: fala, fale, falemos, falai, falem

## Preterite vs Imperfect
- Preterite: completed
- Imperfect: ongoing, habitual
- Example: Eu lia quando ele chegou

## Pronouns
- Subject: eu, tu, ele, ela, nos, vos, eles, elas
- Direct: me, te, o, a, nos, vos, os, as
- Indirect: me, te, lhe, nos, vos, lhes
- Reflexive: me, te, se, nos, vos, se
- Placement: before verb, or attached (enclitic common in European)

## Brazilian vs European
- Pronoun placement: proclitic (Brazil), enclitic (Europe)
- Tu vs voce: both used in Brazil
- Gerund: falando (Brazil), a falar (Europe)
- Vocabulary: many differences
- Phonology: open vowels in European

## Common Pitfalls
- Preterite vs imperfect
- Subjunctive uses
- Pronoun placement
- Brazilian vs European differences
- Personal infinitive
- False friends
""", "tags": ["Portuguese", "grammar", "preterite", "imperfect", "Brazilian", "reference"]}
    ],
    "language_russian": [
        {"title": "Russian Grammar and Usage Reference", "content": """# Russian Grammar and Usage Reference

## Phonology
- Vowels: 5 (a, e, i, o, u), with reduction
- Consonants: voiced/voiceless pairs, palatalized
- Stress: free, phonemic
- Cyrillic: 33 letters

## Nouns
- Gender: masculine, feminine, neuter
- Number: singular, plural
- Cases: 6
  - Nominative: subject
  - Genitive: possession, negation, quantity
  - Dative: indirect object
  - Accusative: direct object
  - Instrumental: means, agent
  - Prepositional: location (with prepositions)

## Verbs
- Two aspects: perfective, imperfective
- Tenses: past, present, future
  - Present: only imperfective
  - Future: imperfective (budu + infinitive), perfective (conjugated)
- Conjugations: 1st (-u, -esh', -et, -em, -ete, -ut), 2nd (-u, -ish', -it, -im, -ite, -at)
- Verbs of motion: unidirectional vs multidirectional
- Imperative: -i, -ite

## Cases in Detail

### Nominative
- Subject: Книга на столе
- Predicate nominative

### Genitive
- Possession: книга брата
- Negation: нет книги
- Quantity: много книг

### Dative
- Indirect object: дать книгу другу
- Age: мне 20 лет

### Accusative
- Direct object: читать книгу
- Motion: идти в школу

### Instrumental
- Means: писать ручкой
- Agent (passive): написано мной

### Prepositional
- Location: в городе
- About: о книге

## Pronouns
- Personal: я, ты, он, она, оно, мы, вы, они
- Possessive: мой, твой, его, ее, наш, ваш, их
- Demonstrative: этот, тот, такой

## Verbs of Motion
- Unidirectional: идти (going one way)
- Multidirectional: ходить (going repeatedly, returning)
- Pairs: бежать/бегать, ехать/ездить, лететь/летать

## Aspect
- Imperfective: ongoing, habitual, process
- Perfective: completed, result
- Pairs: делать/сделать, писать/написать

## Common Pitfalls
- Case errors
- Aspect choice
- Verbs of motion
- Stress and vowel reduction
- Palatalization
- Particles (же, ли, бы)
""", "tags": ["Russian", "grammar", "cases", "aspect", "verbs of motion", "reference"]}
    ],
    "language_arabic": [
        {"title": "Arabic Grammar and Usage Reference", "content": """# Arabic Grammar and Usage Reference

## Phonology
- Consonants: 28, including emphatic and guttural
- Vowels: 3 short (a, i, u), 3 long (a, i, u)
- Stress: varies by dialect and word

## Root and Pattern
- Root: usually 3 consonants (k-t-b: writing)
- Pattern: vowel + consonant template
- Examples:
  - kataba: he wrote
  - kitab: book
  - maktab: office
  - maktaba: library
  - katib: writer
  - maktub: written

## Nouns
- Gender: masculine, feminine (often -a ending)
- Number: singular, dual, plural
  - Sound plural: regular
  - Broken plural: internal change
- Definite: al- (the)
- Indefinite: no article, nunation
- Construct state: idafa (possession)

## Verbs
- Forms: I-X and more, derived from root
- Form I: basic (kataba)
- Form II: causative (kattaba)
- Form III: with (kataba)
- Form IV: causative (aktaba)
- Form V: reflexive of II (takattaba)
- Form VII: passive (inkataba)
- Form VIII: reflexive (iktataba)
- Form X: seek to (istaktaba)

### Tenses
- Perfect: kataba (he wrote)
- Imperfect: yaktubu (he writes)
- Imperative: uktub (write!)
- Future: sa + imperfect or sawfa + imperfect

### Moods
- Indicative: yaktubu
- Subjunctive: yaktuba
- Jussive: yaktub

## Cases (Classical/MSA)
- Nominative: -u (subject)
- Accusative: -a (object)
- Genitive: -i (after preposition, in idafa)

## Pronouns
- Attached: suffixes (-i, -ka, -ki, -hu, -ha, -na, -kum, -hum)
- Detached: ana, anta, anti, huwa, hiya, nahnu, antum, hum
- Demonstrative: hadha, hadhihi

## Prepositions
- Common: fi (in), min (from), ila (to), ma'a (with), 'ala (on), 'an (about), li (for)

## Sentence Types
- Verbal: verb + subject (kataba al-walad)
- Nominal: subject + predicate (al-walad tawil)
- Equational: no verb (al-walad mujtahid)

## Common Pitfalls
- Root and pattern confusion
- Broken plurals
- Verb forms
- Case endings (often dropped in speech)
- Diglossia: MSA vs dialect
- Direction: right-to-left
""", "tags": ["Arabic", "grammar", "root pattern", "verb forms", "MSA", "reference"]}
    ],
    "language_hebrew": [
        {"title": "Hebrew Grammar and Usage Reference", "content": """# Hebrew Grammar and Usage Reference

## Phonology
- Consonants: 22 letters, some with dagesh (dot)
- Vowels: niqqud (points), 5 main
- Stress: usually final syllable

## Root and Pattern
- Root: usually 3 consonants (k-t-v: writing)
- Binyanim: verb patterns
  - Pa'al: simple active (katav: he wrote)
  - Nif'al: passive (nikhtav: was written)
  - Pi'el: intensive (kihtev: he dictated)
  - Pu'al: passive of Pi'el (kuhtev)
  - Hitpa'el: reflexive (hitkatev: corresponded)
  - Hif'il: causative (hiktiv: he dictated to)
  - Hof'al: passive of Hif'il (huktav)

## Nouns
- Gender: masculine, feminine (often -a or -et)
- Number: singular, plural
- Definite: ha- (the)
- Construct: smikhut (possession)

## Verbs
- Tenses:
  - Past: katavti (I wrote)
  - Present: kotev (writing, m)
  - Future: ektov (I will write)
- No present tense as finite verb; participle used
- Imperative: ktov! (write!)

## Pronouns
- Subject: ani, ata, at, hu, hi, anakhnu, atem, aten, hem, hen
- Suffixes: -i, -kha, -o, -ha, -nu, -khem, -hen, -hem

## Prepositions
- Attached: b- (in), k- (like), l- (to), m- (from)
- Separate: im (with), al (on), el (to)

## Sentence Structure
- SVO common in Modern Hebrew
- VSO in Biblical
- Definiteness: predicate must match subject in definiteness

## Common Pitfalls
- Binyanim confusion
- Root and pattern
- Gender agreement
- Definiteness in nominal sentences
- Biblical vs Modern differences
- Niqqud (often omitted in Modern)
""", "tags": ["Hebrew", "grammar", "binyanim", "root pattern", "Modern Hebrew", "reference"]}
    ],
}

LANGUAGE_K3_BATCH4: dict[str, list[dict]] = {
    "language_persian": [
        {"title": "Persian Grammar and Usage Reference", "content": """# Persian Grammar and Usage Reference

## Phonology
- Vowels: 6 (a, e, o, a, i, u)
- Consonants: 23, including q and gh
- Stress: usually final syllable

## Nouns
- No gender
- Plural: -ha (general), -an (animate)
- Arabic plurals: some borrowed
- Definite: -e (enclitic) or no marker
- Indefinite: -i (enclitic)

## Verbs
- Two stems: past, present
- Person endings: -am, -i, -ad, -im, -id, -and
- Tenses:
  - Present: mi- + present stem + ending
  - Past: past stem + ending
  - Imperfect: mi- + past stem + ending
  - Future: kha- + subjunctive
- Subjunctive: be- + present stem + ending
- Imperative: be- + present stem + ending

## Ezefe
- Connects noun to modifier
- Noun-e modifier
- Examples: ketab-e khoob (good book)
- ketab-e ali (Ali's book)
- Used for: adjective, possession, attribution

## Pronouns
- Subject: man, to, u, ma, shoma, anha
- Enclitic: -am, -at, -ash, -aman, -atan, -ashan
- Demonstrative: in (this), an (that)

## Prepositions
- Common: dar (in), be (to), az (from), ba (with), baraye (for), ta (until)

## Word Order
- SOV
- Modifiers after noun (with ezafe)
- Head final

## Common Pitfalls
- Ezafe construction
- Verb stems (irregular)
- Word order
- Arabic loanwords
- Script: right-to-left, vowels not written
""", "tags": ["Persian", "Farsi", "grammar", "ezafe", "verb stems", "reference"]}
    ],
    "language_hindi_urdu": [
        {"title": "Hindi and Urdu Grammar Reference", "content": """# Hindi and Urdu Grammar Reference

## Phonology
- Vowels: 10 (a, a, i, i, u, u, e, ai, o, au)
- Consonants: aspirated and unaspirated
- Stress: not phonemic
- Intonation: important

## Nouns
- Gender: masculine, feminine
- Number: singular, plural
- Case: direct, oblique
- Postpositions: ne, ko, se, me, par, ka

## Verbs
- Stems: root + tense + agreement
- Aspect: imperfective, perfective, habitual
- Tenses:
  - Present: hai, hain
  - Past: tha, the
  - Present habitual: -ta hu
  - Past habitual: -ta tha
  - Present continuous: -raha hu
  - Past continuous: -raha tha
  - Perfect: -ne (ergative)
- Imperative: -o, -iye
- Subjunctive: -e

## Ergative Construction
- Past transitive: subject in oblique with ne
- Example: Ram ne kitab padhi (Ram read a book)
- Intransitive: no ne

## Pronouns
- Hindi: main, tu, vo, ham, tum, ve
- Urdu: main, tu, vo, ham, tum, ve
- Polite: aap (Hindi and Urdu)
- Distal: vo, ve
- Proximal: ye, ye

## Postpositions
- ne: agent (ergative)
- ko: to, object marker
- se: from, with, by
- me: in
- par: on
- ka: of (possessive)
- liye: for

## Scripts
- Hindi: Devanagari
  - Vowels: a, a, i, i, u, u, e, ai, o, au
  - Consonants: k, kh, g, gh, etc.
  - Inherent a: unless marked
- Urdu: Nastaliq (Perso-Arabic)
  - Right-to-left
  - 38 letters (Arabic + additional)
  - Vowels often not written

## Vocabulary
- Hindi: Sanskrit-derived (tatsama, tadbhava)
- Urdu: Persian and Arabic-derived
- Common: Hindustani base

## Common Pitfalls
- Gender agreement
- Ergative construction
- Postpositions vs prepositions
- Script differences
- Vocabulary choice (Hindi vs Urdu)
- Aspiration
""", "tags": ["Hindi", "Urdu", "grammar", "ergative", "postpositions", "reference"]}
    ],
    "language_mandarin_chinese": [
        {"title": "Mandarin Grammar and Characters Reference", "content": """# Mandarin Grammar and Characters Reference

## Phonology
- Initials: consonants at syllable start
- Finals: vowels and -n, -ng
- Tones: 4 + neutral
  - 1: high level (ma)
  - 2: rising (ma)
  - 3: dipping (ma)
  - 4: falling (ma)
  - Neutral: light (ma)
- Tone sandhi: 3+3 -> 2+3

## Characters
- Traditional: Taiwan, HK, Macau
- Simplified: PRC, Singapore (1956)
- Components: radical + phonetic
- Radicals: 214 (Kangxi)
- Strokes: order matters (top to bottom, left to right)

## Pinyin
- Official romanization (1958)
- Initials: b, p, m, f, d, t, n, l, g, k, h, j, q, x, zh, ch, sh, r, z, c, s, y, w
- Finals: a, o, e, i, u, u, ai, ei, ao, ou, an, en, ang, eng, er
- Tone marks: above vowel

## Nouns
- No gender, no case, no plural (usually)
- Plural: -men for people
- Classifiers (measure words): required with numbers
  - ge: general
  - ben: books
  - zhang: flat things
  - tiao: long things
  - liang: vehicles

## Verbs
- No conjugation
- Tense: time words + aspect
- Aspect:
  - le: completed
  - guo: experienced
  - zai: progressive
  - zhe: continuous
- Modal: hui (can), neng (able), keyi (may), yinggai (should)

## Sentence Structure
- SVO: subject-verb-object
- Time: before verb
- Place: before verb
- Topic-comment: common

## Particles
- le: completed action or change
- ma: question
- ne: continuation or question
- ba: object marker
- bei: passive

## Common Pitfalls
- Tones
- Measure words
- Character writing
- Aspect vs tense
- Word order (time, place)
- Homophones (many)
""", "tags": ["Mandarin", "Chinese", "grammar", "tones", "characters", "pinyin", "reference"]}
    ],
    "language_cantonese": [
        {"title": "Cantonese Grammar and Usage Reference", "content": """# Cantonese Grammar and Usage Reference

## Phonology
- Tones: 6 (modern), 9 (traditional)
  - 1: high level
  - 2: high rising
  - 3: mid level
  - 4: low falling
  - 5: low rising
  - 6: low level
  - 7, 8, 9: checked (entering, with -p, -t, -k)
- Initials: 19
- Finals: with -p, -t, -k, -m, -n, -ng

## Jyutping
- Romanization system
- Initials: b, p, m, f, d, t, n, l, g, k, ng, h, gw, kw, w, z, c, s, j
- Finals: aa, a, e, i, o, u, oe, eoi, etc.
- Tone numbers: 1-6

## Grammar
- SVO
- Similar to Mandarin but with differences
- More final particles
- No measure word "ge" (uses "go")
- More colloquial vocabulary

## Final Particles
- aa: softening
- laa: suggestion or completion
- wo: realization
- gaa: assertion
- meh: surprise question
- sin: only then
- tim: also

## Written Cantonese
- Differs from standard Chinese
- Dialect characters: unique
- Examples: 唔 (m, not), 係 (hai, is), 嘅 (ge, possessive)
- Not standardized formally

## Vocabulary
- Colloquial: Cantonese-specific words
- Formal: standard Chinese (read)
- Borrowings: English (especially HK)

## Common Pitfalls
- Tones (more than Mandarin)
- Final particles
- Written vs spoken differences
- Dialect characters
- Romanization (multiple systems)
""", "tags": ["Cantonese", "grammar", "tones", "jyutping", "particles", "reference"]}
    ],
    "language_japanese": [
        {"title": "Japanese Grammar and Writing Reference", "content": """# Japanese Grammar and Writing Reference

## Writing Systems
- Kanji: Chinese characters (2136 joyo)
- Hiragana: 46 native syllabary
- Katakana: 46 for foreign words
- Romaji: romanization

### Hiragana
- a, i, u, e, o
- ka, ki, ku, ke, ko
- sa, shi, su, se, so
- ta, chi, tsu, te, to
- na, ni, nu, ne, no
- ha, hi, fu, he, ho
- ma, mi, mu, me, mo
- ya, yu, yo
- ra, ri, ru, re, ro
- wa, wo, n

### Katakana
- Same syllables, different shapes
- Used for: foreign words, emphasis, onomatopoeia

## Phonology
- Vowels: 5 (a, i, u, e, o)
- Mora: rhythmic unit
- Pitch accent: word-level

## Grammar
- SOV
- Particles: mark function
- Agglutinative: verb conjugation

### Particles
- wa: topic
- ga: subject
- o: direct object
- ni: indirect object, location, time
- de: means, location of action
- kara: from
- made: until
- to: and, with
- ya: and (among others)
- no: possessive
- mo: also
- ka: question
- yo: assertion
- ne: confirmation

### Verbs
- Groups: 1 (godan), 2 (ichidan), 3 (irregular)
- Forms:
  - Masu: polite (tabemasu)
  - Plain: dictionary (taberu)
  - Te: gerund (tabete)
  - Ta: past (tabeta)
  - Nai: negative (tabenai)
  - Potential: can do (taberareru)
  - Passive: (taberareru)
  - Causative: make do (tabesaseru)
  - Conditional: (tabereba)
  - Imperative: (tabero)
- Aspect: continuous (te iru)

### Adjectives
- i-adjectives: end in -i (atarashii)
- na-adjectives: require na (kirei na)
- Conjugate: past, negative

### Keigo (Honorific)
- Sonkeigo: respect to subject
- Kenjougo: humble about self
- Teineigo: polite (desu/masu)
- Bikaigo: beautification

## Common Pitfalls
- Particle choice (wa vs ga)
- Keigo usage
- Kanji readings (on vs kun)
- Verb conjugation
- Pitch accent
- Writing direction
""", "tags": ["Japanese", "grammar", "kanji", "particles", "keigo", "reference"]}
    ],
}

LANGUAGE_K3_BATCH5: dict[str, list[dict]] = {
    "language_korean": [
        {"title": "Korean Grammar and Hangul Reference", "content": """# Korean Grammar and Hangul Reference

## Hangul
- Created: 1443 by King Sejong
- 14 consonants, 10 vowels
- Syllable blocks: consonant + vowel (+ consonant)
- Letters combined into blocks

### Consonants
- ㄱ (g/k), ㄴ (n), ㄷ (d/t), ㄹ (r/l), ㅁ (m), ㅂ (b/p), ㅅ (s), ㅇ (ng/silent initial), ㅈ (j), ㅊ (ch), ㅋ (k), ㅌ (t), ㅍ (p), ㅎ (h)

### Vowels
- ㅏ (a), ㅑ (ya), ㅓ (eo), ㅕ (yeo), ㅗ (o), ㅛ (yo), ㅜ (u), ㅠ (yu), ㅡ (eu), ㅣ (i)

### Double consonants
- ㄲ (kk), ㄸ (tt), ㅃ (pp), ㅆ (ss), ㅉ (jj)

## Phonology
- 10 vowels
- Consonant distinctions: plain, aspirated, tense
- Pitch: not phonemic (mostly)

## Grammar
- SOV
- Agglutinative
- Particles: mark function

### Particles
- Subject: 이/가 (i/ga)
- Topic: 은/는 (eun/neun)
- Object: 을/를 (eul/reul)
- Possessive: 의 (ui)
- Dative: 에게 (ege), 한테 (hante)
- Location: 에 (e, at), 에서 (eseo, from)
- Instrument: 로/으로 (ro/euro)
- Comitative: 와/과 (wa/gwa)

### Verbs
- Stems: dictionary form ends in -da
- Conjugation: stem + ending
- Honorific: -(u)si
- Polite: -ayo, -eoyo
- Formal: -mnida, -seumnida
- Past: -ass/ess-
- Future: -gess-
- Conditional: -myeon
- Imperative: -ra, -seyo

### Speech Levels
- Hasipsio-che: formal polite (-seumnida)
- Haeyo-che: informal polite (-ayo)
- Hao-che: formal plain
- Hage-che: familiar plain
- Haera-che: formal plain (written)
- Hae-che: informal plain

### Honorifics
- Subject honorific: -usi (gasi - to go)
- Object humble: -drida (deurida - to give)
- Special vocabulary: jip -> jib (house -> humble), mom -> mom (body -> respect)

## Nouns
- No gender
- No plural (typically)
- Plural: -deul (sometimes)
- Numbers: native, Sino-Korean

## Common Pitfalls
- Speech level choice
- Honorific usage
- Particle choice (eun/neun vs i/ga)
- Verb conjugation
- Numbers (two systems)
- Pronunciation rules
""", "tags": ["Korean", "grammar", "Hangul", "honorifics", "speech levels", "reference"]}
    ],
    "language_southeast_asian_languages": [
        {"title": "Southeast Asian Language Structures Reference", "content": """# Southeast Asian Language Structures Reference

## Thai

### Phonology
- Tones: 5 (mid, low, falling, high, rising)
- Initials: 21 consonant classes (high, mid, low)
- Finals: 8
- Vowels: long and short

### Script
- Abugida: consonant + vowel
- 44 consonants, 32 vowels
- No spaces between words
- Tone marks

### Grammar
- SVO
- No inflection
- No tense: time words
- Classifiers: with numbers
- Polite particles: khrap (m), kha (f)

## Vietnamese

### Phonology
- Tones: 6 (ngang, huyen, hoi, nga, sac, nang)
- Initials: consonants
- Finals: vowels + -c, -ch, -nh, -ng, -n

### Script
- Quoc ngu: Latin-based (17th c)
- Diacritics: tone and vowel quality

### Grammar
- SVO
- No inflection
- Classifiers: with numbers
- Tense: time words

## Burmese

### Phonology
- Tones: 3 (creaky, low, high) + killed
- Initials: consonants
- Finals: -h, glottal stop

### Script
- Abugida: derived from Mon
- Circular letters
- No spaces between words

### Grammar
- SOV
- No gender
- No plural (usually)
- Polite: -pa

## Khmer

### Phonology
- Register: breathy vs clear
- No tones
- Vowels: long and short

### Script
- Abugida: derived from Pallava
- 33 consonants, 23 vowels
- No spaces between words

### Grammar
- SVO
- No inflection
- No tense: time words
- Classifiers

## Malay/Indonesian

### Phonology
- No tones
- Vowels: a, e, i, o, u
- Consonants: 25

### Script
- Latin (Rumi): standard
- Jawi: Arabic script (traditional, Malaysia)

### Grammar
- SVO
- No inflection
- No gender
- No tense: time words
- Reduplication: plural
- Affixation: derivation

## Common Features
- Isolating morphology
- SVO or SOV
- No tense (time words)
- Classifiers with numbers
- Polite particles
- Abugida or Latin scripts
- Tone (mainland, not island)

## Common Pitfalls
- Tones (Thai, Vietnamese, Lao)
- Script (abugidas)
- No word boundaries in script
- Register vs tone (Khmer)
- Classifier choice
- Politeness levels
""", "tags": ["Southeast Asian", "Thai", "Vietnamese", "Burmese", "Khmer", "Malay", "reference"]}
    ],
    "language_african_languages": [
        {"title": "African Language Structures Reference", "content": """# African Language Structures Reference

## Niger-Congo (Bantu)

### Swahili
- Phonology: 5 vowels, no tones
- Grammar: SVO, noun classes (18)
- Noun class: prefix marks class
  - m-/wa-: people (mtu, watu)
  - m-/mi-: trees (mti, miti)
  - ki-/vi-: objects (kitu, vitu)
  - n-/n-: liquids (maji)
  - u-: abstract (upendo)
- Agreement: verb agrees with subject
- Tense: -na- (present), -li- (past), -ta- (future)

### Yoruba
- Phonology: 3 tones (high, mid, low)
- Grammar: SVO, isolating
- No noun classes
- Tones: phonemic

### Zulu
- Phonology: clicks (with Khoisan influence)
- Grammar: SVO, noun classes (15+)
- Tones: 2 (high, low)

## Afro-Asiatic

### Amharic
- Phonology: 7 vowels, ejectives
- Grammar: SOV, gender
- Script: Ge'ez (abugida)
- Root and pattern: Semitic

### Hausa
- Phonology: tones (2), ejectives, glottalized
- Grammar: SVO
- Script: Latin (Boko), Arabic (Ajami)
- Tones: phonemic

### Oromo
- Phonology: 5 vowels, long and short
- Grammar: SOV
- Script: Latin (Qubee)

## Nilo-Saharan

### Luo
- Phonology: tones
- Grammar: SVO, ATR vowel harmony
- No noun classes

### Maasai
- Phonology: tones
- Grammar: SVO/VSO

## Khoisan
- Click consonants: |, ||, !, =
- Few speakers
- Endangered
- Examples: N|uu, Khoekhoe

## Common Features
- Niger-Congo: noun classes, tone
- Afro-Asiatic: gender, root and pattern (Semitic)
- Nilo-Saharan: tone, vowel harmony
- Khoisan: clicks

## Scripts
- Latin: most (Swahili, Yoruba, Hausa, Zulu)
- Ge'ez: Ethiopian (Amharic, Tigrinya)
- Arabic: historically (Swahili Ajami, Hausa Ajami)
- N'Ko: Mande languages (West Africa)
- Vai, Bamum: indigenous syllabaries

## Common Pitfalls
- Assuming all African languages are similar
- Ignoring tone
- Confusing language and dialect
- Not recognizing noun classes
- Assuming Latin script universal
- Endangerment: many languages at risk
""", "tags": ["African languages", "Swahili", "Yoruba", "Bantu", "noun classes", "reference"]}
    ],
    "language_indigenous_languages": [
        {"title": "Indigenous Language Revitalization Reference", "content": """# Indigenous Language Revitalization Reference

## Endangerment Scale (UNESCO)
- Safe: spoken by all generations
- Vulnerable: most children speak, restricted domains
- Definitely endangered: children no longer learn
- Severely endangered: only grandparents
- Critically endangered: only very few, elderly
- Extinct: no speakers

## Causes of Endangerment
- Colonialism and assimilation policies
- Government suppression (residential schools)
- Urbanization and migration
- Economic pressure: dominant language for jobs
- Media and technology: dominant language
- Intermarriage
- Lack of institutional support

## Revitalization Approaches

### Fishman's Reversing Language Shift (RLS)
- Stage 1: language in higher education, government
- Stage 2: home, neighborhood, community
- Stage 3: intergenerational families
- Stage 4: compulsory education
- Stage 5: literacy in home
- Stage 6: family, community
- Stage 7: older generation
- Stage 8: isolated speakers

### Immersion Schools
- Full language education
- All subjects in target language
- Examples: Hawaiian, Maori, Navajo
- Effective but resource-intensive

### Master-Apprentice Program
- One-on-one: elder and learner
- Oral: focus on speaking
- Daily life: language in context
- California: developed for Native American languages

### Language Nests (Maori model)
- Preschool immersion
- Elders and young children
- Maori: kohanga reo
- Hawaiian: punana leo
- Effective for young children

### Community Classes
- After-school or evening
- Less intensive
- Reach more learners
- Build awareness

### Documentation
- Recording: audio, video
- Transcription: write down
- Translation: to dominant language
- Grammar: describe structure
- Dictionary: compile lexicon
- Text collection: stories, speeches

## Successful Cases

### Hawaiian
- 1980s: few native speakers
- Immersion schools: Punana Leo
- College programs: University of Hawaii
- Government support
- Thousands of speakers now

### Maori
- 1980s: decline
- Kohanga reo: language nests
- Kura kaupapa: immersion schools
- Whare wananga: universities
- Government: Maori Language Commission

### Hebrew (revival)
- 19th-20th c: from liturgical to spoken
- Ben-Yehuda: leadership
- Israel: national language
- Unique: full revival

## Challenges
- Few fluent teachers
- Limited resources
- Lack of materials
- Community motivation
- Dominant language pressure
- Funding
- Standardization (dialects)

## Technology
- Apps: Duolingo, Memrise (some indigenous)
- Online dictionaries
- Social media: communities
- Recording: digital archives
- Text-to-speech: for some languages
- Keyboards: for scripts

## Policy
- Official status: helps
- Education: required for schools
- Media: radio, TV, online
- Government services: in language
- Signs and place names

## Common Pitfalls
- Not involving community
- Top-down approaches
- Focusing on documentation only
- Not creating new speakers
- Ignoring youth
- Not addressing economic factors
- Unrealistic timelines
""", "tags": ["indigenous languages", "revitalization", "endangerment", "immersion", "Fishman", "reference"]}
    ],
    "language_classical_languages": [
        {"title": "Classical Language Traditions Reference", "content": """# Classical Language Traditions Reference

## Latin

### History
- Old Latin: to 1st c BCE
- Classical: 1st c BCE - 2nd c CE (Cicero, Caesar, Virgil)
- Late Latin: 3rd-6th c
- Medieval: 6th-14th c
- Renaissance: 14th-17th c
- Neo-Latin: modern

### Grammar
- Cases: nominative, genitive, dative, accusative, ablative, vocative
- Declensions: 5
- Gender: masculine, feminine, neuter
- Conjugations: 4
- Moods: indicative, subjunctive, imperative
- Voices: active, passive, deponent
- Word order: SOV (flexible)

### Influence
- Romance languages: French, Spanish, Italian, Portuguese, Romanian
- English vocabulary: 60% of words Latin-derived
- Scientific terminology
- Legal terminology
- Catholic Church: official language until 1960s

## Ancient Greek

### Dialects
- Attic: Athens (Plato, Aristotle)
- Ionic: Herodotus, Hippocrates
- Doric: lyric poetry, Pindar
- Aeolic: Sappho, Alcaeus
- Koine: common, Hellenistic, New Testament

### Grammar
- Cases: nominative, genitive, dative, accusative, vocative
- Declensions: 3
- Gender: masculine, feminine, neuter
- Conjugations: many
- Moods: indicative, subjunctive, optative, imperative
- Voices: active, middle, passive
- Aspect: present, aorist, perfect

### Influence
- Philosophy: Plato, Aristotle
- Science: medicine, mathematics
- Literature: Homer, tragedy, comedy
- New Testament: Koine Greek
- English vocabulary: scientific and technical

## Sanskrit

### History
- Vedic: 1500-500 BCE (Vedas)
- Classical: 500 BCE onward (Panini)
- Modern: scholarly and liturgical

### Grammar (Panini)
- Highly systematic
- 8 cases: nominative, accusative, instrumental, dative, ablative, genitive, locative, vocative
- 3 genders, 3 numbers (singular, dual, plural)
- Verbs: 10 conjugations
- Sandhi: word combination rules

### Influence
- Indo-European linguistics
- Hinduism: Vedas, Upanishads
- Buddhism: Mahayana texts
- Indian languages: Hindi, Bengali, Marathi, etc.
- Southeast Asian scripts

## Classical Chinese

### Characteristics
- Literary language: until early 20th c
- Concise: one character per word
- No inflection
- Classical: pre-Han (Confucius, Laozi)
- Literary: later written form

### Influence
- East Asia: China, Japan, Korea, Vietnam
- Kanbun: Japanese reading of Chinese
- Hanja: Korean use of Chinese characters
- Chu Nom: Vietnamese adaptation
- East Asian cultural sphere

## Classical Arabic

### Characteristics
- Quranic language
- Root and pattern system
- Classical grammar: Sibawayh
- Diglossia: with modern dialects

### Influence
- Islam: Quran, liturgy
- Arabic literature: poetry, prose
- Islamic civilization: science, philosophy
- Modern Standard Arabic: derived

## Biblical Hebrew

### Characteristics
- Tanakh: Hebrew Bible
- 22 consonants, no vowels written
- Cases: limited (nominative, accusative, genitive)
- Verb: aspect (perfect, imperfect)

### Influence
- Judaism: Torah, liturgy
- Christianity: Old Testament
- Modern Hebrew: revival

## Common Pitfalls
- Treating classical as dead (still studied, used)
- Confusing periods (Classical vs Medieval Latin)
- Assuming pronunciation known
- Ignoring influence on modern languages
- Underestimating difficulty
""", "tags": ["classical languages", "Latin", "Greek", "Sanskrit", "Classical Chinese", "reference"]}
    ],
}
