"""Egyptology K3 - All 10 specialties (2 per batch)."""

EGYPTOLOGY_K3_BATCH1: dict[str, list[dict]] = {
    "egyptology_old_egyptian": [
        {
            "title": "Old Egyptian Grammar and Pyramid Texts Reference",
            "content": """# Old Egyptian Grammar and Pyramid Texts

## Verbal System
- sdm.f: action; can be past, present, or future depending on context
- sdm.n.f: completed action (past)
- sdm.t.f: future/incomplete
- Stative (pseudoparticiple): state resulting from action
- Imperative: command
- Negations: n sdm.f, n sdm.n.f, tm sdm

## Nominal Forms
- Noun patterns: masculine, feminine (suffix -t), plural (-w), dual (-wy)
- Construct state: noun + noun (direct genitive)
- Pronominal suffix: attached to nouns, verbs, prepositions
- Independent pronouns: for emphasis
- Demonstratives: pn, tn, nn (this), pf, tf, nf (that)

## Particles
- mk: behold (introducing statement)
- ist: indeed, emphasis
- tr: question marker
- n: negative
- iw: sequential/narrative marker

## Pyramid Texts
- Earliest corpus of Egyptian religious texts
- First inscribed in pyramid of Unas (c. 2375 BCE)
- Later kings: Teti, Pepi I, Merenre, Pepi II, and queens
- Spells (utterances): ~800 total
- Purpose: assist king's ascent to the afterlife
- Themes: resurrection, celestial journey, offering rituals, protection

### Key Utterances
- UT 219-220: Cannibal Hymn (king consumes gods)
- UT 273-274: king ascends to sky
- UT 32-33: offering ritual
- UT 245: reed-floats to cross sky
- UT 355-356: king joins the stars

## Notable Old Kingdom Texts
- Palermo Stone: annals of early kings
- Biography of Weni: military and administrative career
- Biography of Harkhuf: Nubian expeditions
- Instructions of Hardedef: wisdom text (fragmentary)

## Common Pitfalls
- Confusing Old Egyptian with Middle Egyptian forms
- Assuming Pyramid Texts are coherent narrative (they are ritual spells)
- Over-translating ambiguous verbal forms
- Ignoring textual variation between pyramids
""",
            "tags": ["Old Egyptian", "grammar", "Pyramid Texts", "Old Kingdom", "reference"],
        }
    ],
    "egyptology_middle_egyptian": [
        {
            "title": "Middle Egyptian Grammar Reference",
            "content": """# Middle Egyptian Grammar Reference

## Uniliteral Signs (Egyptian "Alphabet")
```
3 (aleph)  i/y    ʿ (ayin)   w/u    b      p      f      m
n         r      h          ḥ      ḫ      ẖ      s      š
q/k       k      g          t      ṯ      d      ḏ
```

## Biliteral Signs (common)
```
mꜥ (maa)  nfr    ꜥnḫ (ankh)  ḥr (her)  sw      ir
hr (her)  im     mr         sbꜥ      ḏd (ded)  tp
```

## Triliteral Signs (common)
```
nfr (good/beautiful)  mꜥꜥ (see)    sḫr (plan)  ḥtp (peace)
wdꜥ (judge)          ꜥqꜥ (enter)   sdm (hear)
```

## Verb Forms

### sdm=f
- Circumstantial: "when he heard"
- Prospective: "may he hear" (after wishes)
- Aorist: habitual "he hears"

### sdm.n=f
- Completed action: "he heard"
- Stative/resultative

### sdm.t=f
- Future: "he will hear"
- After certain particles

### Stative (Old Perfective)
- State: "it is white", "he is seated"
- Form: root + ending (3ms: -w, 3fs: -t, 3pl: -w)

### Imperative
- Command: "hear!" (sdm)
- Negative: m sdm "do not hear"

### Negations
- n sdm.n=f: "he did not hear"
- n sdm=f: "he does not hear" (rare in Middle Egyptian)
- nn: absolute negation "there is no..."
- tm: negative verb "not to do"

## Non-Verbal Sentences
- Noun + adverb: "The god is in the temple"
- Noun + noun: "Ptah is the creator"
- Noun + stative: "The man is seated"
- Negation: nn + noun phrase

## Particles and Enclitics
- mk: "behold" (introduces statement)
- ist: "indeed" (emphasis)
- tr: interrogative
- sw: "while" (circumstantial)
- grt: "moreover"
- iw: narrative/sequential marker

## Pseudoverbal Construction
- m + infinitive: "is doing" (progressive)
- r + infinitive: "is going to do" (future)
- ḥr + infinitive: "is doing" (alternative)

## Pronouns
### Suffix Pronouns
```
1s: -i    1pl: -n
2ms: -k   2fs: -ṯ    2pl: -ṯn
3ms: -f   3fs: -s    3pl: -sn
```

### Dependent (Independent) Pronouns
```
1s: wỉ    2ms: tw     3ms: sw
1pl: nn   2fs: tm     3fs: sy
```

## Prepositions (common)
- n: to, for
- m: in, with, by means of
- r: to, at, against
- ḥr: upon, on
- ḥnꜥ: with, together with
- im: therein (adverbial)
- ḏr: since

## Common Pitfalls
- Not recognizing determinatives
- Translating word-by-word instead of parsing syntax
- Confusing sdm=f forms (context determines meaning)
- Ignoring figurative language and metaphor
- Over-relying on dictionary definitions without context
""",
            "tags": ["Middle Egyptian", "grammar", "verbs", "pronouns", "hieroglyphs", "reference"],
        }
    ],
}

EGYPTOLOGY_K3_BATCH2: dict[str, list[dict]] = {
    "egyptology_late_egyptian": [
        {
            "title": "Late Egyptian Grammar Reference",
            "content": """# Late Egyptian Grammar Reference

## Key Differences from Middle Egyptian
- Articles: p3 (m), t3 (f), n3 (pl) - definite; ꜥ (m), tꜥ (f), nꜥ (pl) - indefinite
- More analytic: word order and particles carry more meaning
- New verb forms and constructions
- Greater use of auxiliary verbs
- Increased use of particles

## Articles
- p3, t3, n3: "the" (definite)
- ꜥ, tꜥ, nꜥ: "a/some" (indefinite)
- Demonstrative: p3y, t3y, n3y: "this/these"
- Possessive: p3y=f "his"

## Verb Forms

### sdm=f
- Prospective: "may he hear"
- Circumstantial: "when he heard"

### sdm.n=f
- Past completed: "he heard"

### sdm.t=f
- Future: "he will hear"

### mrr=f (Progressive)
- "he is loving/doing"
- m + infinitive with suffix

### sdm=tw=f (Passive)
- "it is heard"
- tw as passive marker

### sdm=in=f
- Future with modal in

## Negation
- bw sdm=f: "he does not hear"
- nn sdm=f: "he will not hear"
- n sdm.n=f: "he did not hear"
- my-iw=f: "there is not"

## Particles
- tr: emphasis, question
- sw: circumstantial
- ist: indeed
- my: imperative particle
- ky: "other"
- iw: narrative

## Prepositions (expanded)
- m, n, r, ḥr (as Middle Egyptian)
- ḥnꜥ: with
- ẖr: under
- dr: since, from
- X r X: "from X to Y"

## Notable Late Egyptian Texts
- Tale of the Doomed Prince
- Tale of the Two Brothers
- Report of Wenamun
- Instructions of Any
- Great Hymn to the Aten (Amarna period)
- Battle of Kadesh inscriptions (Ramesses II)
- Papyrus Anastasi texts

## Common Pitfalls
- Applying Middle Egyptian grammar to Late Egyptian texts
- Confusing article + noun with demonstrative
- Not recognizing progressive and passive constructions
- Assuming Late Egyptian is "corrupt" Middle Egyptian (it's a natural evolution)
""",
            "tags": ["Late Egyptian", "grammar", "articles", "New Kingdom", "reference"],
        }
    ],
    "egyptology_demotic": [
        {
            "title": "Demotic Script and Texts Reference",
            "content": """# Demotic Script and Texts Reference

## Script Characteristics
- Highly cursive, derived from hieratic
- Standardized in 26th Dynasty (Saite period, c. 664-525 BCE)
- Used until Roman period (c. 3rd century CE)
- Written primarily on papyrus and ostraca
- Sign forms very different from hieroglyphs

## Sign Types
- Derived from hieratic signs but heavily abbreviated
- Many ligatures (combined signs)
- Some signs retain phonetic value, others become logographic
- Determinatives reduced compared to hieratic

## Demotic Egyptian Grammar
- Fully analytic: word order and particles carry meaning
- Articles: pꜣ, tꜣ, nꜣ (definite); ꜥ, tꜥ, nꜥ (indefinite)
- Possessive adjective: pꜣy=f, tꜣy=s, nꜣy=sn
- Relative adjective: nt: nt=f "who is his"
- Coptic-like constructions emerging

## Verb System
- sdm=f: subjunctive/aorist
- sdm=f r: future
- ir=f sdm: "he did" (periphrastic)
- ir=f sdm r: "he will do"
- tw=f sdm: "he is doing" (progressive)
- mtw=f sdm: "he has done" (perfect)

## Negation
- bn...i: "not" (circumstantial bn...ip)
- nn: "there is not"
- my-ir: "do not"

## Major Text Corpora
### Legal/Administrative
- Papyrus Rylands 9: long legal text
- Papyrus Cairo 30657: marriage contract
- Demotic chronicle: historical text

### Literary
- Setna Khaemwaset cycle: magical tales
- Myth of the Sun's Eye
- Instructions of Onchsheshonqy
- Petubastis cycle: pseudo-epic

### Religious
- Mythus des Sonnenauges
- Demotic Book of the Dead
- Temple ritual texts

### Scientific
- Demotic mathematical papyri
- Astronomical texts
- Medical papyri

## The Rosetta Stone
- Decree of Memphis (196 BCE)
- Three scripts: hieroglyphic, demotic, Greek
- Found 1799 by French soldiers in Egypt
- Key to decipherment
- Demotic section provided bridge between Greek and hieroglyphic

## Decipherment
- Young: identified some demotic signs
- Champollion: recognized phonetic values
- Brugsch: major demotic dictionary
- Spiegelberg: systematic grammar
- Johnson, Depauw: modern scholarship

## Common Pitfalls
- Confusing demotic script with hieratic
- Assuming demotic is a separate language (it's a script + phase of Egyptian)
- Underestimating the difficulty of reading cursive signs
- Not recognizing periphrastic verb constructions
""",
            "tags": ["Demotic", "script", "grammar", "Rosetta Stone", "reference"],
        }
    ],
}

EGYPTOLOGY_K3_BATCH3: dict[str, list[dict]] = {
    "egyptology_coptic": [
        {
            "title": "Coptic Grammar and Dialects Reference",
            "content": """# Coptic Grammar and Dialects Reference

## Coptic Alphabet
- 24 Greek letters + 6-7 Demotic-derived signs
- Additional signs (varies by dialect):
  - ϣ (shai = sh)
  - ϥ (fai = f)
  - ϧ (hori = h)
  - ϫ (janja = j/g)
  - ϭ (chima = ch/kh)
  - ϯ (ti = ti)
  - ϥ (sometimes separate from Greek φ)

## Dialects

### Sahidic (Thebaic)
- Standard literary dialect of Upper Egypt
- Most surviving Coptic literature
- Used for biblical translations
- Basis for most Coptic studies
- Major: Nag Hammadi codices (mostly Sahidic)

### Bohairic
- Northern (Delta) dialect
- Liturgical language of Coptic Orthodox Church
- Only surviving spoken descendant (as liturgy)
- Different phonology: /p/ for Sahidic /f/

### Other Dialects
- Akhmimic: around Akhmim; conservative
- Sub-Akhmimic (Lycopolitan): related to Akhmimic
- Fayumic: Fayum region; distinctive features
- Oxyrhynchite (Mesokemic): Middle Egypt

## Grammar

### Nouns
- Gender: masculine, feminine (suffix -ⲉ/-ⲓ)
- Number: singular, plural (-ⲟⲩ/-ⲉ/-ⲓ)
- Definite article: ⲡ (m), ⲧ (f), ⲛ (pl)
- Indefinite article: ⲟⲩ (m), ⲟⲩ (f), ⲛ̄ⲟⲩ (pl)
- Possession: ⲡⲉϥ "his" (article + possessive pronoun)

### Pronouns
- Suffix: =ϥ (his), =ⲥ (her), =ⲟⲩ (their), =ⲓ (my), =ⲛ (our)
- Independent: ⲛⲧⲟϥ (he), ⲛⲧⲟⲥ (she), ⲛⲧⲟⲟⲩ (they)
- Demonstrative: ⲡⲁⲓ (this m), ⲧⲁⲓ (this f), ⲛⲁⲓ (these)

### Verbs
- Infinitive: base form (ⲥⲱⲧⲙ = "to hear")
- Present: ⲥⲉⲥⲱⲧⲙ = "he hears" (converter + subject + infinitive)
- Past: ⲁϥⲥⲱⲧⲙ = "he heard"
- Perfect: ⲛⲧⲉϥⲥⲱⲧⲙ = "he has heard"
- Future: ⲛⲁϥⲥⲱⲧⲙ = "he will hear"
- Imperative: ⲥⲱⲧⲙ = "hear!"
- Negative: ⲛ̄ prefix or ⲁⲛ suffix

### Prepositions
- ⲛ (of, for)
- ⲙ̄ (in)
- ⲉ (to)
- ϩⲛ̄ (in, at)
- ϩⲓ (on)
- ⲙⲡⲟⲩ (with)

## Nag Hammadi Library
- Discovered 1945 near Nag Hammadi, Egypt
- 13 codices, 52 texts
- Mostly Gnostic Christian texts
- Primarily Sahidic Coptic
- Key texts: Gospel of Thomas, Gospel of Philip, Apocryphon of John
- Translated from Greek originals

## Common Pitfalls
- Confusing Coptic dialects
- Assuming Coptic is not Egyptian (it's the final phase)
- Ignoring Greek loanwords (they're integral)
- Not recognizing that Coptic reveals earlier Egyptian pronunciation
- Treating Coptic as purely liturgical (it was a living language for centuries)
""",
            "tags": ["Coptic", "grammar", "dialects", "Sahidic", "Bohairic", "Nag Hammadi", "reference"],
        }
    ],
    "egyptology_hieroglyphs": [
        {
            "title": "Hieroglyphic Sign List and Reading Rules Reference",
            "content": """# Hieroglyphic Sign List and Reading Rules

## Gardiner Sign Categories
- A: Man and his occupations
- B: Woman and her occupations
- C: Anthropomorphic deities
- D: Parts of the human body
- E: Mammals
- F: Parts of mammals
- G: Birds
- H: Parts of birds
- I: Amphibious animals, reptiles
- K: Fishes and parts of fishes
- L: Invertebrates and lesser animals
- M: Trees and plants
- N: Sky, earth, water
- O: Buildings, parts of buildings
- P: Ships and parts of ships
- Q: Domestic and funerary furniture
- R: Temple furniture and sacred emblems
- S: Crowns, dress, staves
- T: Warfare, hunting, butchery
- U: Agriculture, crafts, professions
- V: Rope, fiber, baskets, bags
- W: Vessels of stone and earthenware
- X: Loaves and cakes
- Y: Writings, games, music
- Z: Strokes, signs derived from hieratic
- AA: Unclassified

## Common Uniliteral Signs
```
Gardiner#  Sign         Sound   Description
A1        𓀀            ꜥ (3)   seated man (determinative; 3 = vulture)
i         𓇋            i       reed
y         𓏭            y       double reed
ꜥ         𓂝            ꜥ       forearm
w         𓅱            w       quail chick
b         𓃀            b       foot
p         𓊪            p       stool
f         𓆑            f       horned viper
m         𓅓            m       owl
n         𓈖            n       water
r         𓂋            r       mouth
h         𓉔            h       reed shelter
ḥ         𓎛            ḥ       wick
ḫ         𓐍            ḫ       placenta/jar stand
ẖ         𓋴            ẖ       animal's belly
s         𓋴            s       folded cloth
š         𓈙            š       pool
q         𓏘            q/k     hill slope
k         𓎡            k       bowl
g         𓎼            g       jar stand
t         𓏏            t       loaf
ṯ         𓏏            ṯ       tethering rope (t + stroke)
d         𓂧            d       hand
ḏ         𓆓            ḏ       cobra
```

## Reading Rules

### Direction
- Signs face the direction of reading
- If signs face right, read right to left
- If signs face left, read left to right
- Columns: read top to bottom, then next column
- Royal names in cartouches: read start to end

### Sign Grouping
- Signs arranged in aesthetic blocks
- Tall signs can span two short signs
- No spaces between words
- Determinatives at end of word
- Phonetic complements reinforce biliteral/triliteral

### Determinatives
- Indicate semantic category
- Not pronounced
- Examples:
  - 𓀀 (seated man): male person
  - 𓁐 (seated woman): female person
  - 𓆳 (sun): time, day
  - 𓊪 (stool): seat, place
  - 𓄿 (bird): flight, speed
  - 𓏏 (loaf): bread, food
  - 𓈖 (water): liquids, flow

### Phonetic Complements
- Uniliteral sign added after biliteral/triliteral
- Reinforces reading
- Example: nfr + r = nfr (r is complement)
- Example: ḥtp + p = ḥtp (p is complement)

## Royal Titulary (Five Names)
1. Horus name: falcon on serekh
2. Nebty name (Two Ladies): cobra and vulture
3. Golden Horus name: falcon on gold
4. Throne name (prenomen): in cartouche, preceded by nswt-bity
5. Birth name (nomen): in cartouche, preceded by sa-ra

## Numbers
```
1: 𓏺 (stroke)
10: 𓎆 (heel bone)
100: 𓍢 (coil of rope)
1,000: 𓆼 (lotus)
10,000: 𓂭 (finger)
100,000: 𓆐 (tadpole)
1,000,000: 𓁨 (god with arms raised)
```

## Common Pitfalls
- Reading signs left to right when they face right
- Ignoring determinatives (can change word meaning)
- Not recognizing phonetic complements
- Confusing similar-looking signs
- Assuming all signs are phonetic (some are logographic/determinative)
- Forgetting cartouche indicates royal name
""",
            "tags": ["hieroglyphs", "Gardiner", "sign list", "reading rules", "determinatives", "reference"],
        }
    ],
}

EGYPTOLOGY_K3_BATCH4: dict[str, list[dict]] = {
    "egyptology_hieratic": [
        {
            "title": "Hieratic Paleography Reference",
            "content": """# Hieratic Paleography Reference

## Development of Hieratic

### Early Dynastic (c. 3100-2686 BCE)
- Close to hieroglyphic forms
- Limited surviving examples (labels, jars)
- Already showing cursive tendencies

### Old Kingdom (c. 2686-2181 BCE)
- More abbreviated forms
- Administrative documents on papyrus
- Sign forms still recognizable from hieroglyphs
- Key: Abusir papyri (temple accounts)

### Middle Kingdom (c. 2055-1650 BCE)
- Standardized forms
- Literary texts: Sinuhe, Eloquent Peasant
- Hieratic becomes distinct from carved hieroglyphs
- Written in columns, right to left

### New Kingdom (c. 1550-1069 BCE)
- Further abbreviation
- Two styles: formal (literary) and cursive (administrative)
- Papyrus BM 10056 (Abbott papyrus)
- Late Egyptian texts in hieratic

### Third Intermediate / Late Period
- Increasingly cursive
- Transitions toward Demotic
- Abnormal Hieratic (8th-6th c. BCE): southern variant

## Paleographic Features
- Sign forms change over time (dating criterion)
- Individual scribal hands can be identified
- Ligatures: signs joined together
- Abbreviations: common in administrative texts
- Sign groups: conventional combinations

## Key Paleographic Resources
- Möller, "Hieratische Paläographie" (3 vols): standard reference for sign forms by period
- Goedicke, "Old Hieratic Paleography"
- Posener-Kriéger, "The Abusir Papyri"
- Wente, "Late Ramesside Letters"

## Text Types in Hieratic
### Administrative
- Temple accounts (Abusir)
- Tax lists
- Worker registers (Deir el-Medina)
- Letters (Ramesside period)

### Literary
- Tale of Sinuhe
- Eloquent Peasant
- Shipwrecked Sailor
- Instructions (wisdom literature)

### Religious
- Coffin Texts (some versions)
- Book of the Dead
- Hymns
- Ritual texts

### Scientific
- Mathematical papyri (Rhind, Moscow)
- Medical papyri (Ebers, Smith)
- Astronomical texts

## Reading Hieratic
- Requires training in sign recognition
- Sign forms differ significantly from hieroglyphs
- Context helps identify abbreviated signs
- Compare with published paleographies
- Practice with transcribed texts

## Common Pitfalls
- Assuming hieratic signs match hieroglyphic forms
- Not accounting for period-specific sign forms
- Confusing similar cursive signs
- Ignoring ligatures and abbreviations
- Not consulting paleographic reference works
""",
            "tags": ["hieratic", "paleography", "cursive", "scribes", "reference"],
        }
    ],
    "egyptology_epigraphy": [
        {
            "title": "Egyptian Epigraphic Methods Reference",
            "content": """# Egyptian Epigraphic Methods Reference

## Chicago House Method
- Developed by Epigraphic Survey of the Oriental Institute (Chicago)
- Standard for temple epigraphy
- Process:
  1. Photograph inscription with scale
  2. Large-format photograph mounted on light table
  3. Tracing on tracing paper: exact sign forms
  4. Pencil drawing checked against original on site
  5. Ink drawing on stipple board
  6. Collation: multiple Egyptologists verify accuracy
  7. Publication

## Digital Epigraphy
- 3D scanning: captures surface detail
- RTI (Reflectance Transformation Imaging): interactive lighting
- Photogrammetry: 3D models from photos
- Digital drawing tablets: combine hand-drawing with digital workflow
- Scales and color calibration essential

## Recording Standards

### Transliteration
- Latin alphabet with diacritics (Gardiner system)
- Capital letters for proper nouns
- Italic for Egyptian words in scholarly text
- Dots for missing/damaged signs
- Brackets for restored text: [restored]
- Half-brackets for partially visible: [partial]
- Angle brackets for emendations: <added>

### Translation Conventions
- Literal vs literary translation
- Notes on uncertain readings
- Commentary on context and interpretation
- Cross-references to parallel texts

## Major Epigraphic Projects

### Chicago Epigraphic Survey
- Medinet Habu (Ramesses III)
- Luxor Temple
- Karnak (various)
- Ongoing since 1924

### Other Projects
- IFAO: Karnak, Dendara, Edfu
- DAIK: Elephantine, Abydos
- EES: Saqqara, Amarna
- ARCE: conservation and recording
- University missions: various sites

## Challenges in Egyptian Epigraphy
- Weathering: wind, water, salt damage
- Graffiti: ancient and modern
- Reuse of stone: inscriptions cut over earlier ones
- Ptolemaic inscriptions: expanded sign inventory (6000+ signs)
- Cryptographic writing: deliberate obscurity
- Access: scaffolding, lighting, permissions

## Publication Standards
- Plates: facsimile drawings with photographs
- Text volume: transliteration, translation, commentary
- Index: divine names, royal names, personal names, geographical names
- Concordance: cross-reference to other publications

## Common Pitfalls
- Not collating drawings against original
- Misreading damaged signs
- Not documenting condition of inscription
- Ignoring ancient graffiti and secondary inscriptions
- Not using consistent transliteration conventions
- Publishing without adequate photographs
""",
            "tags": ["epigraphy", "Chicago House", "recording", "transliteration", "publication", "reference"],
        }
    ],
}

EGYPTOLOGY_K3_BATCH5: dict[str, list[dict]] = {
    "egyptology_comparative_ancient_history": [
        {
            "title": "Egypt and Neighboring Civilizations Reference",
            "content": """# Egypt and Neighboring Civilizations Reference

## Egypt and Mesopotamia
- Both river civilizations (Nile vs Tigris-Euphrates)
- Both developed writing early (c. 3200 BCE)
- Differences:
  - Egypt: unified state early; Mesopotamia: city-states then empires
  - Egypt: optimistic afterlife; Mesopotamia: gloomy underworld
  - Egypt: divine kingship; Mesopotamia: human servant of gods
- Contacts: trade via Levant; some shared motifs (flood myth, wisdom literature)
- Amarna letters: diplomatic correspondence with Babylon, Assyria, Mitanni

## Egypt and Nubia
- Nubia: south of Egypt, Nile valley
- Kerma culture (c. 2500-1500 BCE): powerful state
- Egypt conquered Nubia during New Kingdom (c. 1500 BCE)
- Nubian princes raised in Egyptian court
- 25th Dynasty: Nubian kings rule Egypt (Piye, Shabaka, Taharqa)
- Meroitic civilization: successor state, writing system undeciphered

## Egypt and the Levant
- Canaan: Egyptian influence during New Kingdom
- Amarna letters: Canaanite city-states petition Egypt
- Biblical connections: no direct evidence of Exodus in Egyptian records
- Shoshenq I (22nd Dynasty): biblical "Shishak" raids Judah
- Elephantine: Jewish community in Egypt (5th c. BCE)

## Egypt and the Aegean
- Minoan Crete: trade contacts (Keftiu in Egyptian texts)
- Mycenaean Greeks: trade, mercenaries
- Sea Peoples: attacked Egypt in reigns of Merenptah and Ramesses III
- Philistines: possibly settled in Canaan after defeat

## Egypt and Persia
- Cambyses conquered Egypt (525 BCE)
- 27th Dynasty: Persian satraps
- Egyptian revolts: Amyrtaeus, 28th Dynasty
- Reconquest by Artaxerxes III (343 BCE)
- Persian rule resented; seen as foreign oppression

## Egypt and Greece
- Greek mercenaries in Egyptian service (7th-6th c. BCE)
- Naucratis: Greek trading post in Delta
- Herodotus: visited Egypt, wrote about it
- Plato: studied in Egypt (tradition)
- Hellenistic: Alexander conquered Egypt (332 BCE)
- Ptolemaic Dynasty: Greek rulers, Egyptian subjects
- Cleopatra VII: last Ptolemaic ruler (died 30 BCE)

## Egypt and Rome
- Rome annexed Egypt after Cleopatra's death (30 BCE)
- Egypt as imperial province, not senatorial
- Grain supply: Egypt fed Rome
- Roman emperors depicted as pharaohs
- Christianity: Alexandria early center
- Monasticism: Anthony, Pachomius (Egyptian origins)
- Arab conquest (642 CE): end of Roman/Byzantine Egypt

## Comparative Themes

### Kingship
- Egypt: pharaoh as living god (Horus), divine son
- Mesopotamia: king as shepherd, servant of gods
- Persia: king of kings, divine mandate
- Greece: varied (tyrants, kings, democracy)
- Rome: emperor as Augustus, pontifex maximus, later divus

### Writing
- Egypt: hieroglyphs, hieratic, demotic, Coptic
- Mesopotamia: cuneiform
- Levant: alphabet (Phoenician, Hebrew, Aramaic)
- Greece: adapted Phoenician alphabet
- Rome: Latin alphabet from Greek

### Afterlife
- Egypt: judgment, Field of Reeds, preserved body
- Mesopotamia: gloomy underworld, no judgment
- Canaan/Israel: Sheol, later resurrection
- Greece: Hades, Elysium for heroes
- Rome: adapted Greek views

## Common Pitfalls
- Assuming direct influence when parallels may be independent
- Reading modern borders onto ancient world
- Privileging Egyptian perspective over neighbors'
- Treating "Egypt" as unchanging across 3000 years
- Ignoring Nubian and Levantine contributions
""",
            "tags": ["comparative history", "Egypt", "Mesopotamia", "Nubia", "Greece", "Rome", "reference"],
        }
    ],
    "egyptology_egyptian_archaeology": [
        {
            "title": "Egyptian Archaeological Sites Reference",
            "content": """# Egyptian Archaeological Sites Reference

## Predynastic and Early Dynastic
- Abydos (Umm el-Qa'ab): royal tombs of first kings (Narmer, Den, Djer)
- Hierakonpolis (Nekhen): early urban center, Narmer palette
- Naqada: type site for Naqada culture periods
- Tarkhan: early dynastic cemetery
- Saqqara: early dynastic mastabas

## Old Kingdom
- Giza: pyramids of Khufu, Khafre, Menkaure; Sphinx; worker's village; cemeteries
- Saqqara: Step Pyramid of Djoser; Serapeum; Teti pyramid; mastabas (Mereruka, Kagemni)
- Abusir: pyramids of 5th Dynasty kings; Abusir papyri
- Dahshur: Bent Pyramid and Red Pyramid of Sneferu
- Meidum: collapsed pyramid of Sneferu

## Middle Kingdom
- Lisht: pyramids of Amenemhat I and Senwosret I
- Dahshur: pyramid of Senwosret III; mudbrick pyramids
- Lahun: pyramid of Senwosret II; Kahun workmen's town
- Beni Hasan: nomarch tombs (Middle Kingdom)
- Elephantine: fortress, temple, settlement

## New Kingdom
- Thebes (Luxor):
  - Karnak Temple: largest temple complex
  - Luxor Temple: Amun cult
  - Valley of the Kings: Tutankhamun, Seti I, Ramesses VI, etc.
  - Valley of the Queens: Nefertari, etc.
  - Deir el-Bahari: Hatshepsut's mortuary temple
  - Deir el-Medina: workmen's village (tomb builders)
  - Ramesseum: Ramesses II mortuary temple
  - Medinet Habu: Ramesses III mortuary temple
- Amarna (Akhetaten): Akhenaten's capital; royal tomb; workmen's village
- Abydos: Osiris temple; Seti I temple; Osireion
- Saqqara: New Kingdom tombs (Horemheb, Maya)

## Third Intermediate and Late Period
- Tanis: capital of 21st/22nd Dynasties; royal tombs
- Bubastis: capital of 22nd Dynasty
- Sais: capital of 26th Dynasty
- Memphis: continued importance

## Ptolemaic and Roman
- Alexandria: capital; Library; Pharos lighthouse; submerged ruins
- Kom Ombo: double temple (Sobek and Haroeris)
- Edfu: best-preserved temple (Horus)
- Dendara: Hathor temple; astronomical ceiling
- Philae: Isis temple; last hieroglyphic inscription (394 CE)

## Nubian Sites (Egyptian-controlled)
- Abu Simbel: temples of Ramesses II (relocated 1960s)
- Philae: temple complex (relocated)
- Soleb: Amun temple (Amenhotep III)
- Sedeinga: Temple of Tiye
- Qasr Ibrim: fortress, multi-period occupation

## Key Discoveries
- 1799: Rosetta Stone (Napoleonic expedition)
- 1858-1881: Mariette excavations (Serapeum, Abydos)
- 1881: Deir el-Bahari royal cache (mummies)
- 1893: Deir el-Bahari cache of priests
- 1907: KV55 (Akhenaten?)
- 1922: Tutankhamun's tomb (Carter and Carnarvon)
- 1939: Tanis royal tombs (Montet)
- 1945: Nag Hammadi codices
- 1976: tomb of Nefertari (reopened 1990s)
- 2005: KV63 (embalming cache)
- 2017: KV65 (discovery announced)
- 2020: Saqqara coffin cache (27 sarcophagi)

## Common Pitfalls
- Treating sites as static (they evolve over millennia)
- Focusing on tombs and temples, ignoring settlements
- Not considering looting history
- Assuming pristine contexts (many sites were disturbed in antiquity)
- Not integrating archaeological and textual evidence
""",
            "tags": ["Egyptian archaeology", "sites", "Giza", "Thebes", "Amarna", "reference"],
        }
    ],
}
