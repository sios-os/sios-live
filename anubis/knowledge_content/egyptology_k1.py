"""Egyptology K1 - All 10 specialties (2 per batch)."""

EGYPTOLOGY_K1_BATCH1: dict[str, list[dict]] = {
    "egyptology_old_egyptian": [
        {
            "title": "Old Egyptian - Field Overview",
            "content": """# Old Egyptian

## Definition
Old Egyptian is the earliest attested phase of the Egyptian language, used during the Old Kingdom (c. 2686-2181 BCE) and in some later texts.

## Core Areas
- Pyramid Texts: earliest religious corpus, inscribed in pyramids (5th-6th Dynasty)
- Autobiographical inscriptions: tomb biographies of officials
- Administrative documents: limited surviving examples
- Linguistic features: archaic forms, conservative grammar

## Key Features
- Older verbal system with more inflection than later phases
- Sdm.f verb form with broader temporal range
- Preserves archaic pronouns and particles
- Limited textual corpus compared to Middle Egyptian
- Written in hieroglyphs

## Relationship to Other Phases
- Precursor to Middle Egyptian (Classical Egyptian)
- Some debate about distinctness vs early Middle Egyptian
- Old Egyptian gradually transitions to Middle Egyptian by First Intermediate Period

## Foundational Texts
- Allen, "The Ancient Egyptian Language: An Historical Study"
- Loprieno, "Ancient Egyptian: A Linguistic Introduction"
- Edel, "Altägyptische Grammatik"

## Authority Note
Advisory. Old Egyptian grammar is reconstructed from limited corpus; interpretations evolve.""",
            "tags": ["Old Egyptian", "Egyptian language", "Old Kingdom", "Pyramid Texts", "overview"],
        }
    ],
    "egyptology_middle_egyptian": [
        {
            "title": "Middle Egyptian - Field Overview",
            "content": """# Middle Egyptian (Classical Egyptian)

## Definition
Middle Egyptian is the classical phase of the Egyptian language, used from c. 2000 BCE through the Middle Kingdom and continuing as a literary and religious language for millennia.

## Core Areas
- Literary texts: Sinuhe, Tale of the Shipwrecked Sailor, Eloquent Peasant
- Coffin Texts: Middle Kingdom funerary corpus
- Royal inscriptions: stelae, temple texts
- Scientific and medical papyri
- Continued as classical/liturgical language long after spoken use declined

## Key Features
- Pseudoverbal construction: sdm.n=f, mrr=f, sdm=f
- Negation: n...tm, nn
- Particles: mk, ist, tr
- Nisbe adjectives from nouns
- Pseudoparticiple (old perfective/stative)
- Written in hieroglyphs and hieratic

## Importance
- The "classical" language of Egyptian literature
- Standard teaching phase for Egyptology students
- Used for religious texts throughout Egyptian history
- Gateway to understanding all later phases

## Foundational Texts
- Gardiner, "Egyptian Grammar" (standard reference)
- Allen, "Middle Egyptian: An Introduction to the Language and Culture of Hieroglyphs"
- Hoch, "Middle Egyptian Grammar"
- Loprieno, "Ancient Egyptian: A Linguistic Introduction"

## Authority Note
Advisory. Middle Egyptian is the best-attested phase; grammar is well understood. Gardiner remains the standard reference.""",
            "tags": ["Middle Egyptian", "Classical Egyptian", "hieroglyphs", "grammar", "overview"],
        }
    ],
}

EGYPTOLOGY_K1_BATCH2: dict[str, list[dict]] = {
    "egyptology_late_egyptian": [
        {
            "title": "Late Egyptian - Field Overview",
            "content": """# Late Egyptian

## Definition
Late Egyptian is the phase of the Egyptian language used during the New Kingdom (c. 1550-1069 BCE), reflecting the spoken language of the period while Middle Egyptian remained used for literary/religious texts.

## Core Areas
- Ramesside literature: Instructions, tales, hymns
- Administrative and legal documents
- Letters and personal correspondence
- Historical inscriptions (battle accounts, royal annals)
- Religious texts (new compositions)

## Key Features
- More analytic structure than Middle Egyptian
- Definite article p3, t3, n3 emerges
- New verb forms: sdm=f (circumstantial), mrr=f (progressive)
- Increased use of particles: tr, sw
- Prepositions develop into more complex system
- Written in hieratic and hieroglyphs

## Relationship to Other Phases
- Descends from Middle Egyptian
- More closely reflects contemporary speech
- Transitions to Demotic in Late Period
- Coexists with Middle Egyptian (diglossia)

## Foundational Texts
- Gardiner, "Late-Egyptian Stories"
- Cerny & Groll, "A Late Egyptian Grammar"
- Junge, "Late Egyptian Grammar"

## Authority Note
Advisory. Late Egyptian grammar is well-attested from New Kingdom texts.""",
            "tags": ["Late Egyptian", "New Kingdom", "Ramesside", "grammar", "overview"],
        }
    ],
    "egyptology_demotic": [
        {
            "title": "Demotic - Field Overview",
            "content": """# Demotic

## Definition
Demotic is both a script and a phase of the Egyptian language, used from c. 650 BCE through the Roman period. The script is a highly cursive derivative of hieratic.

## Core Areas
- Legal and administrative documents
- Literary texts: Setna cycle, mythological narratives
- Scientific and instructional texts
- Religious texts (late temples)
- Inscriptions on stone (Rosetta Stone)

## Key Features
- Highly cursive script, difficult to read
- Simplified sign inventory compared to hieratic
- Analytic grammar: articles, new verbal constructions
- Heavy use of particles and auxiliary verbs
- Written primarily on papyrus and ostraca

## Script
- Derived from hieratic (cursive hieroglyphic)
- Standardized during 26th Dynasty (Saite)
- Used alongside Greek in Ptolemaic period
- Gradually replaced by Coptic script

## The Rosetta Stone
- 196 BCE: decree in hieroglyphic, demotic, Greek
- Key to decipherment of Egyptian scripts
- Champollion used it alongside other evidence (1822)

## Foundational Texts
- Johnson, "Thus Wrote 'Onchsheshonqy"
- Simpson, "Demotic Grammar"
- Depauw, "A Companion to Demotic Studies"

## Authority Note
Advisory. Demotic is less commonly taught; specialists are fewer. Decipherment continues.""",
            "tags": ["Demotic", "Egyptian script", "Rosetta Stone", "Late Period", "overview"],
        }
    ],
}

EGYPTOLOGY_K1_BATCH3: dict[str, list[dict]] = {
    "egyptology_coptic": [
        {
            "title": "Coptic - Field Overview",
            "content": """# Coptic

## Definition
Coptic is the final phase of the Egyptian language, written in the Coptic alphabet (Greek letters plus demotic-derived signs) and used from c. 200 CE. It remains the liturgical language of the Coptic Orthodox Church.

## Core Areas
- Biblical translations: Old and New Testaments
- Gnostic and Manichaean texts (Nag Hammadi library)
- Patristic literature: Shenoute, Cyril
- Documentary texts: letters, legal documents
- Liturgical texts of the Coptic Church

## Dialects
- Sahidic: standard literary dialect (Upper Egypt)
- Bohairic: liturgical dialect (Delta, used by Coptic Church today)
- Akhmimic, Sub-Akhmimic, Fayumic, Lycopolitan, Oxyrhynchite (minor)

## Key Features
- Egyptian written in Greek alphabet
- 6 additional signs from Demotic for sounds not in Greek
- Fully analytic grammar
- Preserves Egyptian phonology through Greek letters
- Loanwords from Greek

## Importance
- Final phase of ancient Egyptian
- Crucial for reconstructing earlier Egyptian pronunciation
- Nag Hammadi codices: major Gnostic texts
- Bridge between ancient and medieval Egypt

## Foundational Texts
- Lambdin, "Introduction to Sahidic Coptic"
- Layton, "A Coptic Grammar"
- Crum, "A Coptic Dictionary"
- Nag Hammadi Codices (1945 discovery)

## Authority Note
Advisory. Coptic is well-attested and grammatically understood. Pronunciation varies by dialect and tradition.""",
            "tags": ["Coptic", "Egyptian language", "Nag Hammadi", "Coptic Church", "overview"],
        }
    ],
    "egyptology_hieroglyphs": [
        {
            "title": "Hieroglyphs - Field Overview",
            "content": """# Hieroglyphs

## Definition
Hieroglyphs are the formal pictorial writing system of ancient Egypt, used from c. 3200 BCE through the Roman period. The term comes from Greek "sacred carvings."

## Core Areas
- Monumental inscriptions: temples, tombs, stelae
- Religious texts: Pyramid Texts, Coffin Texts, Book of the Dead
- Royal inscriptions: annals, decrees, dedications
- Decorative and symbolic uses
- Cryptographic and playful writings (Ptolemaic period)

## Sign Types
- Logograms: signs representing words (house = pr)
- Phonograms: signs representing sounds
  - Uniliteral: one consonant (24 signs, "alphabet")
  - Biliteral: two consonants
  - Triliteral: three consonants
- Determinatives: signs indicating semantic category
- Phonetic complements: reinforce reading of biliteral/triliteral signs

## Writing Conventions
- Direction: right to left (most common), left to right, or columns
- Determine direction by which way signs face
- No punctuation, no word dividers (Middle Egyptian)
- Group signs in aesthetic blocks, not linear sequence
- Royal names in cartouches (oval rings)

## Decipherment
- Rosetta Stone (1799 discovery, 196 BCE text)
- Thomas Young: made initial progress
- Jean-Francois Champollion (1822): breakthrough
  - Recognized phonetic value of signs
  - Used Coptic to reconstruct pronunciation
  - Identified cartouches as royal names

## Number of Signs
- Old Kingdom: ~700 signs
- Ptolemaic period: ~6,000+ signs (elaboration)
- Core working vocabulary: ~200-300 signs

## Foundational Texts
- Gardiner, "Egyptian Grammar" (sign list)
- Allen, "Middle Egyptian"
- Manley, "Egyptian Hieroglyphs for Complete Beginners"
- Zauzich, "Discovering Egyptian Hieroglyphs"

## Authority Note
Advisory. Hieroglyphic reading is well-established for standard texts. Ptolemaic inscriptions remain challenging.""",
            "tags": ["hieroglyphs", "writing system", "Egyptian", "decipherment", "Champollion", "overview"],
        }
    ],
}

EGYPTOLOGY_K1_BATCH4: dict[str, list[dict]] = {
    "egyptology_hieratic": [
        {
            "title": "Hieratic - Field Overview",
            "content": """# Hieratic

## Definition
Hieratic is the cursive form of hieroglyphic writing, used primarily for documents written with ink on papyrus, from the Early Dynastic period through the Roman era.

## Core Areas
- Administrative documents: accounts, lists, letters
- Literary texts: tales, instructions, poetry
- Religious texts: Coffin Texts, Book of the Dead
- Scientific texts: medical, mathematical, astronomical
- Personal correspondence and legal documents

## Key Features
- Cursive: signs simplified for speed
- Written left to right (primarily), in columns
- Same language as hieroglyphic texts
- Sign forms vary by period and region
- Abnormal Hieratic: variant used in southern Upper Egypt (8th-6th c. BCE)

## Relationship to Hieroglyphs
- Not a separate script, but cursive form of same system
- Sign correspondences can be traced
- Some hieratic signs become distinct over time
- Hieroglyphs reserved for formal/monumental contexts

## Periods
- Old Kingdom hieratic: relatively close to hieroglyphic forms
- Middle Kingdom: more standardized
- New Kingdom: further abbreviation
- Late Period: transitions toward Demotic

## Foundational Texts
- Möller, "Hieratische Paläographie" (sign forms by period)
- Goedicke, "Old Hieratic Paleography"
- Wente, "Late Ramesside Letters"

## Authority Note
Advisory. Hieratic requires specialized training; paleography varies significantly by period.""",
            "tags": ["hieratic", "cursive", "papyrus", "Egyptian script", "overview"],
        }
    ],
    "egyptology_epigraphy": [
        {
            "title": "Epigraphy - Field Overview",
            "content": """# Epigraphy (Egyptian)

## Definition
Epigraphy is the study and recording of inscriptions. Egyptian epigraphy focuses on documenting inscriptions on monuments, temples, tombs, stelae, and objects.

## Core Areas
- Field recording: drawing, photographing, 3D scanning inscriptions
- Palaeography: study of sign forms and their development
- Text edition: transliteration, translation, commentary
- Corpus building: systematic publication of inscriptions
- Digital epigraphy: computational tools for recording and analysis

## Methods
- Direct copying: tracing or drawing on site
- Photography: raking light, RTI (Reflectance Transformation Imaging)
- 3D scanning: laser, photogrammetry, structured light
- Squeezes: paper impressions of inscriptions (traditional)
- Digital epigraphy: Chicago House method, digitalEpyptology tools

## Major Epigraphic Projects
- Chicago Epigraphic Survey (Medinet Habu, Luxor, etc.)
- Berlin Brandenburg Academy: Inscriptions of Sinai
- Oxford Griffith Institute: Topographical Bibliography
- IFAO (Cairo): various temple publications

## Challenges
- Weathering and damage to inscriptions
- Restoration and reconstruction of fragmented texts
- Distinguishing original from later additions
- Ptolemaic inscriptions: elaborate, expanded sign inventory
- Access to sites and permissions

## Standards
- Transliteration conventions: Gardiner system
- Text layout conventions for editions
- URIs and digital identifiers for inscriptions (Trismegistos)

## Foundational Texts
- Porten & Yardeni, "Textbook of Aramaic Documents from Ancient Egypt"
- Kitchen, "Ramesside Inscriptions" (major corpus)
- Breasted, "Ancient Records of Egypt" (early corpus)

## Authority Note
Advisory. Epigraphic work requires site access and specialized training. Published editions are authoritative for their texts.""",
            "tags": ["epigraphy", "inscriptions", "recording", "temples", "overview"],
        }
    ],
}

EGYPTOLOGY_K1_BATCH5: dict[str, list[dict]] = {
    "egyptology_comparative_ancient_history": [
        {
            "title": "Comparative Ancient History - Field Overview",
            "content": """# Comparative Ancient History

## Definition
Comparative ancient history examines the civilizations of the ancient world in relation to each other, identifying patterns, connections, and differences across cultures.

## Core Areas
- Egypt and Mesopotamia: parallel civilizations, interactions
- Egypt and the Aegean: trade, diplomacy, cultural exchange
- Egypt and the Levant: Canaan, Israel, Phoenicia
- Egypt and Nubia: Kerma, Kush, Napata, Meroe
- Egypt and Libya, Berber peoples
- Persia and Egypt: Achaemenid conquest
- Greece and Egypt: Hellenistic fusion
- Rome and Egypt: imperial province
- Cross-cultural: kingship, religion, economy, writing

## Key Concepts
- Diffusion vs independent invention: explaining similarities
- Core-periphery: power dynamics between civilizations
- Cultural hybridity: Hellenistic, Roman-period syncretism
- Trade networks: Mediterranean, Red Sea, Nile
- Diplomacy: Amarna letters, royal marriages
- Warfare and conquest: empires and resistance

## Major Civilizations for Comparison
- Egypt: Nile valley, pharaonic state
- Mesopotamia: Sumer, Akkad, Babylon, Assyria
- Hittites: Anatolia
- Persia: Achaemenid, Sasanian
- Greece: Minoan, Mycenaean, Archaic, Classical
- Rome: Republic, Empire
- Nubia: Kerma, Kush, Meroe
- Levant: Canaanites, Israelites, Phoenicians
- Carthage: Phoenician colony

## Foundational Texts
- Trigger et al., "Ancient Egypt: A Social History"
- Kemp, "Ancient Egypt: Anatomy of a Civilization"
- Baines & Yoffee, "Order, Legitimacy, and Wealth in Ancient Egypt"
- Van De Mieroop, "A History of the Ancient Near East"

## Authority Note
Advisory. Comparative claims must respect each civilization's specificity. Parallels do not prove contact.""",
            "tags": ["comparative history", "ancient civilizations", "Egypt", "Mesopotamia", "overview"],
        }
    ],
    "egyptology_egyptian_archaeology": [
        {
            "title": "Egyptian Archaeology - Field Overview",
            "content": """# Egyptian Archaeology

## Definition
Egyptian archaeology is the study of ancient Egyptian material culture through excavation, survey, and analysis of sites, artifacts, architecture, and landscapes.

## Core Areas
- Settlement archaeology: cities, villages, workmen's villages (Deir el-Medina, Amarna)
- Funerary archaeology: tombs, cemeteries, pyramids, mortuary landscapes
- Temple archaeology: religious architecture and practice
- Landscape archaeology: Nile, deserts, oases, quarries
- Underwater archaeology: Alexandria, submerged sites
- Material culture: pottery, lithics, metal, faience, glass, textiles

## Key Sites
- Giza: pyramids, Sphinx, worker's village, cemeteries
- Saqqara: Step Pyramid, Serapeum, New Kingdom tombs
- Luxor/Thebes: Karnak, Luxor Temple, Valley of Kings, Valley of Queens, Deir el-Medina, Deir el-Bahari
- Amarna: short-lived capital of Akhenaten
- Abydos: early kings, Osiris cult, Umm el-Qa'ab
- Tanis: Third Intermediate Period capital
- Alexandria: Hellenistic/Roman capital, submerged ruins
- Elephantine: Nubian border, Jewish community

## Methods
- Excavation: stratigraphic, careful recording
- Survey: surface, geophysical (magnetometry, GPR)
- Archaeometry: C14, ceramic petrography, isotope analysis
- Digital: 3D modeling, GIS, photogrammetry
- Bioarchaeology: human remains, diet, disease, migration
- Experimental archaeology: pottery, stone tools, pyrotechnology

## Organizations
- Supreme Council of Antiquities (Egypt): regulates all fieldwork
- IFAO (Cairo): French institute
- DAIK (Cairo): German institute
- EES: Egypt Exploration Society (UK)
- ARCE: American Research Center in Egypt
- Many university missions

## Ethical Issues
- Looting and illicit antiquities trade
- Repatriation (Rosetta Stone, Nefertiti bust, etc.)
- Tourism impact on sites
- Development threats (urban expansion, agriculture)
- Community archaeology: engaging local populations

## Foundational Texts
- Bard, "An Introduction to the Archaeology of Ancient Egypt"
- Wilkinson, "The Rise and Fall of Ancient Egypt"
- Shaw, "The Oxford History of Ancient Egypt"
- Renfrew & Bahn, "Archaeology: Theories, Methods and Practice"

## Authority Note
Advisory. Egyptian archaeology requires permits from the Egyptian government. Published reports are authoritative for excavations.""",
            "tags": ["Egyptian archaeology", "excavation", "sites", "material culture", "overview"],
        }
    ],
}
