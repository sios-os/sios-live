"""Humanities K3 Batch 1: Philosophy, History."""

HUMANITIES_K3_BATCH1: dict[str, list[dict]] = {
    "humanities_philosophy": [
        {
            "title": "Logic and Argumentation Reference",
            "content": """# Logic and Argumentation Reference

## Deductive Arguments
- Valid: conclusion follows necessarily from premises
- Sound: valid + true premises
- Form: modus ponens, modus tollens, hypothetical syllogism, disjunctive syllogism

### Valid Forms
- Modus ponens: If P then Q; P; therefore Q
- Modus tollens: If P then Q; not Q; therefore not P
- Hypothetical syllogism: If P then Q; if Q then R; therefore if P then R
- Disjunctive syllogism: P or Q; not P; therefore Q

### Fallacies
- Affirming the consequent: If P then Q; Q; therefore P (INVALID)
- Denying the antecedent: If P then Q; not P; therefore not Q (INVALID)
- Equivocation: using a word in two senses
- Begging the question (petitio principii): assuming what you need to prove
- Ad hominem: attacking the person not the argument
- Straw man: misrepresenting the opponent's position
- False dilemma: presenting only two options when more exist
- Slippery slope: claiming a chain without showing each link
- Appeal to authority: citing authority instead of evidence
- Appeal to popularity: many believe it, therefore true
- Post hoc: after it, therefore because of it
- Composition/division: what's true of parts is true of whole (or vice versa)

## Propositional Logic
- Operators: NOT (¬), AND (∧), OR (∨), IMPLIES (→), IFF (↔)
- Truth tables
- Tautology: always true (P ∨ ¬P)
- Contradiction: always false (P ∧ ¬P)
- Contingent: depends on assignment

## Predicate Logic
- Quantifiers: ∀ (all), ∃ (some)
- ∀x P(x): for all x, P(x) is true
- ∃x P(x): there exists an x such that P(x)
- Negation: ¬∀x P(x) ≡ ∃x ¬P(x); ¬∃x P(x) ≡ ∀x ¬P(x)

## Modal Logic
- □P: necessarily P
- ◇P: possibly P
- Systems: T, S4, S5 (increasing strength)

## Informal Reasoning
- Abduction: inference to best explanation
- Analogy: argument from similarity
- Bayesian reasoning: updating beliefs with evidence
  - P(H|E) = P(E|H) * P(H) / P(E)

## Common Pitfalls
- Confusing validity with soundness
- Ignoring hidden premises
- Equivocation on key terms
- Treating induction as deduction
- Ignoring base rates in probabilistic reasoning
- Motivated reasoning: seeking evidence that confirms existing beliefs
""",
            "tags": ["logic", "argumentation", "fallacies", "deduction", "reference"],
        },
        {
            "title": "Major Philosophical Arguments Reference",
            "content": """# Major Philosophical Arguments Reference

## Epistemology

### Descartes' Cogito
- "I think, therefore I am" (Cogito ergo sum)
- Even if I doubt everything, I cannot doubt that I am doubting
- Therefore, my existence as a thinking thing is certain
- Critique: establishes only a thinking self, not an embodied one

### Gettier Problems
- Justified true belief is not sufficient for knowledge
- Example: Smith has justified belief that Jones owns a Ford; Smith infers Jones owns a Ford or Brown is in Barcelona; Brown happens to be in Barcelona; belief is true and justified but not knowledge
- Responses: reliabilism, virtue epistemology, defeasibility theory

### Hume's Problem of Induction
- We cannot justify induction deductively (conclusion goes beyond premises)
- We cannot justify induction inductively (circular)
- Response: Popper (falsificationism), Bayesian (probabilistic), naturalized epistemology

## Metaphysics

### Free Will
- Compatibilism: free will compatible with determinism (Hume, Frankfurt)
- Libertarianism: free will requires genuine alternative possibilities
- Hard determinism: no free will, all determined
- Frankfurt cases: show moral responsibility without alternative possibilities

### Personal Identity
- Psychological continuity (Locke): same person = same consciousness
- Bodily continuity: same organism
- Narrative identity (MacIntyre, Schechtman): self as story
- Bundle theory (Hume): no persisting self, only bundle of perceptions

## Ethics

### Trolley Problem
- Switch: 5 vs 1 (most people switch)
- Push: push someone to save 5 (most people won't push)
- Reveals deontological vs consequentialist intuitions
- Critique: unrealistic, ignores real-world complexity

### Is-Ought Problem (Hume)
- Cannot derive "ought" from "is"
- Fact alone does not imply value
- Response: moral naturalism, constructivism

### Original Position (Rawls)
- Design justice behind "veil of ignorance"
- Not knowing your place in society
- Would choose: equal basic liberties, difference principle
- Critique: Nozick (entitlement theory), communitarian critique

## Philosophy of Mind

### Chinese Room (Searle)
- Person in room follows rules to manipulate Chinese symbols
- Produces correct output but no understanding
- Argues: syntax is not semantics; strong AI fails
- Response: systems reply, robot reply

### Knowledge Argument (Jackson)
- Mary knows all physical facts about color but has never seen red
- When she sees red, she learns something new
- Therefore: physicalism is false
- Response: ability hypothesis, acquaintance hypothesis

## Philosophy of Religion

### Problem of Evil
- If God is omnipotent, omniscient, and omnibenevolent, evil should not exist
- Evil exists
- Responses: free will defense, soul-making theodicy, skeptical theism

### Cosmological Argument
- Everything has a cause
- Chain of causes cannot be infinite
- Therefore: first cause (God)
- Critique: what causes God? (Hume, Russell)

### Ontological Argument (Anselm)
- God is that than which nothing greater can be conceived
- Existence in reality is greater than existence in understanding
- Therefore: God exists
- Critique: existence is not a predicate (Kant); parody (Gaunilo)

## Common Pitfalls
- Treating thought experiments as empirical evidence
- Confusing logical possibility with metaphysical possibility
- Ignoring alternative formulations of arguments
- Anachronism: reading present concerns into past arguments
""",
            "tags": ["philosophy", "arguments", "epistemology", "metaphysics", "ethics", "reference"],
        },
    ],
    "humanities_history": [
        {
            "title": "Historiography and Historical Methods Reference",
            "content": """# Historiography and Historical Methods Reference

## Schools of Historiography

### Rankean (Empiricist)
- "How it really was" (wie es eigentlich gewesen)
- Objective reconstruction from primary sources
- Focus on diplomacy, politics, great men
- Critique: no perspective is truly neutral

### Marxist
- History driven by material conditions and class struggle
- Base (economy) determines superstructure (culture, politics)
- Modes of production: feudalism, capitalism, socialism
- Key figures: Marx, Engels, Hobsbawm, Thompson

### Annales School
- Longue duree: long-term historical structures
- Total history: geography, economy, demography, mentalities
- Against event-centered political history
- Key figures: Bloch, Febvre, Braudel, Le Goff

### Postmodern / Post-structuralist
- History as narrative construction
- No single objective truth; multiple perspectives
- Discourse analysis (Foucault): power shapes what counts as knowledge
- Key figures: Foucault, White, Ankersmit

### Subaltern Studies
- History from below; voices of the marginalized
- Originated in South Asian history
- Critique of elite nationalist historiography
- Key figures: Guha, Spivak, Chakrabarty

### World Systems Theory
- Core, periphery, semi-periphery
- Global economic structures shape local histories
- Key figure: Wallerstein

## Historical Methods

### Source Criticism
1. Authenticity: is the source genuine?
2. Credibility: is the source reliable?
   - Internal: consistency, language, style
   - External: corroboration, provenance
3. Bias assessment: whose perspective? what interests?

### Types of Sources
- Primary: created at the time (documents, artifacts, oral)
- Secondary: analysis after the fact
- Tertiary: encyclopedias, textbooks

### Quantitative Methods
- Cliometrics: economic history with statistical methods
- Demographic analysis: census, parish records
- Prosopography: collective biography
- GIS: spatial analysis of historical data

### Oral History
- Recorded interviews with participants
- Strengths: captures lived experience, marginalized voices
- Weaknesses: memory distortion, interviewer bias
- Best practice: contextualize, corroborate, archive

## Causation in History
- Multiple causation: rarely one cause
- Proximate vs distal causes
- Structural vs contingent causes
- Counterfactual reasoning: what if X had not happened?
- Path dependence: early events constrain later options

## Common Pitfalls
- Presentism: judging past by present standards
- Teleology: reading history as leading inevitably to present
- Great man fallacy: attributing all to individuals
- Cherry-picking sources that support a thesis
- Ignoring structural factors
- Confusing correlation with causation
- Survivorship bias: only studying what survived
- Nationalist bias: framing history to serve present politics
""",
            "tags": ["historiography", "historical methods", "source criticism", "Annales", "reference"],
        },
        {
            "title": "World History Timeline Reference",
            "content": """# World History Timeline Reference

## Ancient Period (3000 BCE - 500 CE)

### Mesopotamia
- ~3500 BCE: Sumerian civilization, cuneiform writing
- ~2334 BCE: Akkadian Empire (Sargon)
- ~1792 BCE: Hammurabi's Code (Babylon)
- ~911 BCE: Neo-Assyrian Empire
- 609 BCE: Fall of Assyria
- 539 BCE: Cyrus the Great captures Babylon (Persian Empire)

### Egypt
- ~3100 BCE: Unification of Upper and Lower Egypt (Narmer)
- ~2660 BCE: Old Kingdom, first pyramids
- ~2055 BCE: Middle Kingdom
- ~1550 BCE: New Kingdom (Hatshepsut, Akhenaten, Ramesses II)
- 1070 BCE: Third Intermediate Period
- 525 BCE: Persian conquest
- 332 BCE: Alexander conquers Egypt
- 30 BCE: Roman annexation (Cleopatra VII dies)

### Greece
- ~2700 BCE: Minoan civilization (Crete)
- ~1600 BCE: Mycenaean civilization
- ~1200 BCE: Bronze Age collapse
- ~800 BCE: Archaic period begins
- 776 BCE: Traditional date of first Olympics
- 508 BCE: Athenian democracy (Cleisthenes)
- 490 BCE: Battle of Marathon
- 480 BCE: Battles of Thermopylae and Salamis
- 431-404 BCE: Peloponnesian War
- 336 BCE: Alexander the Great begins conquests
- 323 BCE: Death of Alexander; Hellenistic period
- 146 BCE: Roman conquest of Greece

### Rome
- 753 BCE: Traditional founding of Rome
- 509 BCE: Roman Republic established
- 264-146 BCE: Punic Wars
- 44 BCE: Assassination of Julius Caesar
- 27 BCE: Augustus establishes Empire
- 476 CE: Fall of Western Roman Empire
- 1453 CE: Fall of Constantinople (Eastern Empire ends)

### China
- ~1600 BCE: Shang Dynasty
- 1046 BCE: Zhou Dynasty
- 551 BCE: Birth of Confucius
- 221 BCE: Qin unification (Shi Huangdi)
- 206 BCE - 220 CE: Han Dynasty
- 618-907 CE: Tang Dynasty
- 960-1279 CE: Song Dynasty
- 1271-1368 CE: Yuan Dynasty (Mongol)
- 1368-1644 CE: Ming Dynasty
- 1644-1912 CE: Qing Dynasty

### India
- ~2600 BCE: Indus Valley Civilization (Harappa, Mohenjo-daro)
- ~1500 BCE: Vedic period
- ~563 BCE: Birth of Buddha
- 322-185 BCE: Mauryan Empire (Ashoka)
- 320-550 CE: Gupta Empire

## Medieval Period (500 - 1500 CE)

- 622 CE: Hijra; beginning of Islamic calendar
- 632 CE: Death of Muhammad
- 711 CE: Umayyad conquest of Spain
- 800 CE: Charlemagne crowned Emperor
- 1066 CE: Norman Conquest of England
- 1095 CE: First Crusade
- 1206 CE: Genghis Khan proclaimed
- 1258 CE: Mongols sack Baghdad
- 1337-1453 CE: Hundred Years' War
- 1347-1351 CE: Black Death
- 1453 CE: Fall of Constantinople

## Early Modern (1500 - 1800 CE)

- 1492 CE: Columbus reaches Americas
- 1517 CE: Luther's 95 Theses (Reformation)
- 1519-1521 CE: Cortes conquers Aztec Empire
- 1532-1533 CE: Pizarro conquers Inca Empire
- 1543 CE: Copernicus publishes heliocentric theory
- 1648 CE: Peace of Westphalia (modern state system)
- 1687 CE: Newton's Principia
- 1776 CE: American Declaration of Independence
- 1789 CE: French Revolution begins

## Late Modern (1800 - 1945)

- 1804 CE: Haitian independence
- 1815 CE: Congress of Vienna
- 1839-1842 CE: First Opium War
- 1848 CE: Revolutions across Europe; Communist Manifesto
- 1859 CE: Darwin's Origin of Species
- 1861-1865 CE: American Civil War
- 1868 CE: Meiji Restoration (Japan)
- 1885 CE: Berlin Conference (Scramble for Africa)
- 1914-1918 CE: World War I
- 1917 CE: Russian Revolution
- 1929 CE: Great Depression begins
- 1939-1945 CE: World War II
- 1945 CE: Atomic bombs on Hiroshima and Nagasaki

## Contemporary (1945 - present)

- 1947 CE: Indian independence and partition
- 1948 CE: Universal Declaration of Human Rights; Israel established
- 1949 CE: PRC established; NATO founded
- 1955-1975 CE: Vietnam War
- 1957 CE: Sputnik; Space Race begins
- 1960 CE: Year of Africa (17 countries gain independence)
- 1989 CE: Fall of Berlin Wall
- 1991 CE: Dissolution of USSR; World Wide Web
- 2001 CE: September 11 attacks
- 2008 CE: Global financial crisis
- 2020 CE: COVID-19 pandemic

## Common Pitfalls
- Eurocentric timelines ignoring other civilizations
- Treating dates as precise when sources are uncertain
- Periodization imposing artificial boundaries
- Assuming linear progress
- Ignoring simultaneous developments in different regions
""",
            "tags": ["history", "timeline", "chronology", "world history", "reference"],
        },
    ],
}
