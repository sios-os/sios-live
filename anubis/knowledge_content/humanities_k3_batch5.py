"""Humanities K3 Batch 5: Heritage and Museum Studies, Archival Science."""

HUMANITIES_K3_BATCH5: dict[str, list[dict]] = {
    "humanities_heritage_museum_studies": [
        {
            "title": "Museum Practice and Heritage Management Reference",
            "content": """# Museum Practice and Heritage Management Reference

## Museum Functions

### Collection Management
- Acquisition: purchase, donation, bequest, field collection
- Accessioning: registering new items with unique numbers
- Cataloging: recording metadata (material, dimensions, provenance, condition)
- Inventory: periodic audit of holdings
- Deaccessioning: removing items (ethical and legal considerations)
- Loans: incoming and outgoing, insurance, transport

### Conservation
- Preventive: climate control (temperature 18-22C, RH 45-55%), light control, pest management
- Interventive: treatment of individual objects
- Restoration: returning to assumed original state (controversial)
- Digital: 3D scanning, virtual reconstruction
- Materials science: analyzing pigments, textiles, metals

### Exhibition Development
1. Concept and narrative
2. Object selection
3. Interpretive planning
4. Design (layout, lighting, graphics, interactives)
5. Fabrication and installation
6. Evaluation (front-end, formative, summative)
7. Maintenance and rotation

## UNESCO World Heritage

### Convention (1972)
- Sites of Outstanding Universal Value (OUV)
- Cultural, natural, or mixed criteria (10 criteria)
- Inscription process: tentative list, nomination, evaluation (ICOMOS/IUCN), committee decision
- State of conservation reporting
- In Danger list: threatened sites

### Notable Sites
- Pyramids of Giza (1979)
- Great Wall of China (1987)
- Taj Mahal (1983)
- Machu Picchu (1983)
- Venice and its Lagoon (1987)
- Angkor (1992)
- Stonehenge (1986)

## Intangible Heritage (2003 Convention)
- Oral traditions and expressions
- Performing arts
- Social practices, rituals, festive events
- Knowledge and practices concerning nature and universe
- Traditional craftsmanship
- Examples: kabuki, flamenco, Mediterranean diet, Belgian beer culture

## Heritage Ethics

### Repatriation
- NAGPRA (1990, US): Native American human remains and cultural items
- Elgin Marbles: Greece requests return from British Museum
- Benin Bronzes: from Africa, many in Western museums
- Ethical arguments: cultural property, contextual integrity, restorative justice
- Counter-arguments: universal museum, preservation, legal acquisition

### Decolonization
- Recognizing colonial origins of many collections
- Sharing authority with source communities
- Reinterpreting displays from multiple perspectives
- Returning control of narratives

### Community Engagement
- Participatory curation
- Oral history projects
- Community advisory boards
- Co-curation with descendant communities
- Living exhibitions

## Digital Heritage
- Digitization standards: FADGI, METS/ALTO
- 3D scanning: photogrammetry, structured light, LiDAR
- Virtual museums: online exhibitions, VR tours
- Digital preservation: format migration, emulation
- Access: open access images, IIIF, Creative Commons

## Museum Types and Examples
- Universal/encyclopedic: British Museum, Louvre, Metropolitan
- Art: MoMA, Uffizi, Prado
- Natural history: Smithsonian, Natural History Museum London
- Science: Exploratorium, Deutsches Museum
- History: Imperial War Museum, Holocaust Memorial Museum
- Ethnography: Musee du Quai Branly, Pitt Rivers
- Open-air: Colonial Williamsburg, Skansen

## Common Pitfalls
- Displaying objects without source community consent
- Treating living cultures as "extinct"
- Over-restoration destroying original material
- Ignoring provenance research (especially colonial-era acquisitions)
- Prioritizing blockbuster exhibitions over collection care
- Not evaluating visitor experience
- Treating digital as a substitute rather than complement
""",
            "tags": ["museum", "heritage", "conservation", "UNESCO", "repatriation", "reference"],
        },
    ],
    "humanities_archival_science": [
        {
            "title": "Archival Standards and Digital Preservation Reference",
            "content": """# Archival Standards and Digital Preservation Reference

## Archival Principles

### Respect des Fonds
- Keep records of a single creator together
- Do not mix records from different creators
- Foundation of arrangement (Netherlands, 1840s; Jenkinson)

### Original Order
- Maintain the order imposed by the creator
- Reveals relationships and context
- Do not reorganize by subject or format
- Exception: when original order is lost or harmful

### Provenance
- Document the origin and chain of custody
- Essential for authenticity and context
- Provenance research: who created, owned, transferred

## Arrangement Levels
1. Fonds: all records of one creator
2. Series: files grouped by function/activity
3. Sub-series: subdivision of series
4. File: group of related documents
5. Item: individual document

## Description Standards

### ISAD(G) - General International Standard Archival Description
- Multi-level description
- Identity statement area: reference code, title, dates
- Context area: creator, administrative history
- Content area: scope, content, appraisal
- Conditions area: access, reproduction, language
- Allied materials area: existence of copies, related units
- Note area

### ISAAR(CPF) - International Standard Archival Authority Record
- Describes creators (persons, families, corporate bodies)
- Separate from description of records
- Links records to their creators

### EAD - Encoded Archival Description
- XML format for finding aids
- Hierarchical structure matching arrangement
- Interoperable across institutions
- EAD3: current version

### DACS - Describing Archives: A Content Standard
- US standard for archival description
- Rules for creating finding aids
- Compatible with ISAD(G) and EAD

## Digital Preservation

### Threats to Digital Records
- Media degradation: bit rot, CD/DVD decay, hard drive failure
- Format obsolescence: software/hardware no longer available
- Hardware obsolescence: readers unavailable
- Chain of custody: proving authenticity over time

### Strategies
- Migration: convert to new formats periodically
- Emulation: recreate old environment on new hardware
- Encapsulation: bundle data with metadata and software
- Refreshment: copy to new media

### Standards
- OAIS (ISO 14721): Open Archival Information System reference model
  - Producer, Management, Archive, Consumer
  - SIP (Submission Information Package)
  - AIP (Archival Information Package)
  - DIP (Dissemination Information Package)
- PREMIS: Preservation Metadata
- METS: Metadata Encoding and Transmission Standard
- BagIt: packaging format for transfer

### Trusted Digital Repository (TDR)
- ISO 16363: Audit and certification
- Criteria: governance, organizational viability, security, transparency
- Examples: Internet Archive, HathiTrust, national libraries

### File Format Recommendations
- Text: PDF/A, plain text (UTF-8), XML
- Images: TIFF (uncompressed), PNG
- Audio: WAV (BWF), FLAC
- Video: FFV1 in Matroska container
- Avoid: proprietary formats, DRM-protected files

## Records Management

### Records Lifecycle
1. Creation/receipt
2. Active use
3. Semi-active (storage)
4. Appraisal (keep or destroy)
5. Archives (permanent) or destruction

### Retention Schedules
- Specify how long each record type is kept
- Based on legal, fiscal, administrative, historical value
- Example: financial records 7 years; permanent records to archives

### Functional Requirements
- ICA-Req: Model Requirements for Records Management
- MoReq: Model Requirements for Electronic Records Management
- DoD 5015.02: US Department of Defense standard

## Common Pitfalls
- Not appraising (keeping everything or nothing)
- Losing provenance information during transfer
- Not documenting arrangement decisions
- Ignoring digital preservation until formats are obsolete
- Treating backups as preservation (backups are not preservation)
- Not having disaster recovery plans
- Restricting access unnecessarily
- Not training staff on digital preservation
""",
            "tags": ["archival science", "digital preservation", "ISAD(G)", "EAD", "OAIS", "reference"],
        },
    ],
}
