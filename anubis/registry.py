"""SIOS Domain and Specialty Registry.

Implements the foundational knowledge base structure from the KBP-1 plan:
  - 14 domain directors
  - 279+ specialty identities
  - 14 cross-cutting verification council members
  - Knowledge depth levels K0-K4
  - Source trust tiers T1-T5 + Q (quarantine) + X (prohibited)
  - Specialty registry schema
  - Source registry with license and provenance tracking

This is the canonical registry. Population happens through the pipeline
in anubis/knowledge.py.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------ enums

class KnowledgeDepth(IntEnum):
    """Knowledge depth levels from the KBP plan."""
    K0 = 0  # Registered — identity, scope, ontology stub
    K1 = 1  # Oriented — glossary, field map, introductory sources
    K2 = 2  # Practitioner — structured curriculum, manuals, examples
    K3 = 3  # Advanced — specialist literature, standards, datasets
    K4 = 4  # Research-capable — current literature, methods, open problems


class SourceTier(IntEnum):
    """Source trust tiers from the KBP plan."""
    T1 = 1  # Authoritative primary — laws, standards, official manuals
    T2 = 2  # Institutional synthesis — government guidance, systematic reviews
    T3 = 3  # Licensed educational — textbooks, courses, reference works
    T4 = 4  # Practitioner evidence — vendor docs, engineering notes
    T5 = 5  # Community and discovery — forums, encyclopedias, news
    Q  = 9  # Quarantine — unknown provenance, AI-generated, unverified
    X  = 99 # Prohibited — malware, stolen data, bypassed paywalls


class SourceClass(IntEnum):
    """Source status classes from KBP-1."""
    A = 0  # Open/authoritative
    B = 1  # Open scholarly
    C = 2  # Discovery metadata
    D = 3  # Licensed/restricted
    E = 4  # Unverified web
    X = 9  # Prohibited


# ------------------------------------------------------------------ data classes

@dataclass
class Specialty:
    """A single specialty identity in the registry."""
    specialty_id: str
    canonical_name: str
    aliases: list[str] = field(default_factory=list)
    parent_director_id: str = ""
    scope_statement: str = ""
    exclusions: list[str] = field(default_factory=list)
    authority_ceiling: str = "advisory"  # advisory, assistive, regulated
    regulated_domain: bool = False
    prerequisite_specialties: list[str] = field(default_factory=list)
    peer_specialties: list[str] = field(default_factory=list)
    verifier_ids: list[str] = field(default_factory=list)
    knowledge_depth: int = KnowledgeDepth.K0
    evaluation_status: str = "registered"  # registered, oriented, tested, verified
    last_verified_at: float = 0.0
    next_review_at: float = 0.0
    source_manifest_hash: str = ""
    local_availability: bool = False
    storage_budget_mb: int = 0
    compute_budget_mb: int = 0
    network_policy: str = "offline"  # offline, curated, restricted, open

    def to_dict(self) -> dict[str, Any]:
        return {
            "specialty_id": self.specialty_id,
            "canonical_name": self.canonical_name,
            "aliases": self.aliases,
            "parent_director_id": self.parent_director_id,
            "scope_statement": self.scope_statement,
            "exclusions": self.exclusions,
            "authority_ceiling": self.authority_ceiling,
            "regulated_domain": self.regulated_domain,
            "prerequisite_specialties": self.prerequisite_specialties,
            "peer_specialties": self.peer_specialties,
            "verifier_ids": self.verifier_ids,
            "knowledge_depth": self.knowledge_depth,
            "evaluation_status": self.evaluation_status,
            "last_verified_at": self.last_verified_at,
            "next_review_at": self.next_review_at,
            "source_manifest_hash": self.source_manifest_hash,
            "local_availability": self.local_availability,
            "storage_budget_mb": self.storage_budget_mb,
            "compute_budget_mb": self.compute_budget_mb,
            "network_policy": self.network_policy,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Specialty":
        return cls(
            specialty_id=data.get("specialty_id", ""),
            canonical_name=data.get("canonical_name", ""),
            aliases=data.get("aliases", []),
            parent_director_id=data.get("parent_director_id", ""),
            scope_statement=data.get("scope_statement", ""),
            exclusions=data.get("exclusions", []),
            authority_ceiling=data.get("authority_ceiling", "advisory"),
            regulated_domain=data.get("regulated_domain", False),
            prerequisite_specialties=data.get("prerequisite_specialties", []),
            peer_specialties=data.get("peer_specialties", []),
            verifier_ids=data.get("verifier_ids", []),
            knowledge_depth=data.get("knowledge_depth", KnowledgeDepth.K0),
            evaluation_status=data.get("evaluation_status", "registered"),
            last_verified_at=data.get("last_verified_at", 0.0),
            next_review_at=data.get("next_review_at", 0.0),
            source_manifest_hash=data.get("source_manifest_hash", ""),
            local_availability=data.get("local_availability", False),
            storage_budget_mb=data.get("storage_budget_mb", 0),
            compute_budget_mb=data.get("compute_budget_mb", 0),
            network_policy=data.get("network_policy", "offline"),
        )


@dataclass
class DomainDirector:
    """A domain director owning a set of specialties."""
    director_id: str
    name: str
    description: str = ""
    specialty_ids: list[str] = field(default_factory=list)
    charter: str = ""
    coverage_status: str = "registered"  # registered, mapped, populated, verified

    def to_dict(self) -> dict[str, Any]:
        return {
            "director_id": self.director_id,
            "name": self.name,
            "description": self.description,
            "specialty_ids": self.specialty_ids,
            "charter": self.charter,
            "coverage_status": self.coverage_status,
        }


@dataclass
class SourceRecord:
    """A registered source in the source registry."""
    source_id: str
    name: str
    publisher: str = ""
    url: str = ""
    tier: int = SourceTier.T5
    source_class: int = SourceClass.E
    license: str = ""
    copyright_owner: str = ""
    permitted_uses: list[str] = field(default_factory=list)
    attribution_required: bool = True
    redistribution_allowed: bool = False
    training_allowed: bool = False
    date_accessed: float = 0.0
    version: str = ""
    trust_score: float = 0.0
    status: str = "discovered"  # discovered, quarantined, verified, trusted, expired, prohibited

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "publisher": self.publisher,
            "url": self.url,
            "tier": self.tier,
            "source_class": self.source_class,
            "license": self.license,
            "copyright_owner": self.copyright_owner,
            "permitted_uses": self.permitted_uses,
            "attribution_required": self.attribution_required,
            "redistribution_allowed": self.redistribution_allowed,
            "training_allowed": self.training_allowed,
            "date_accessed": self.date_accessed,
            "version": self.version,
            "trust_score": self.trust_score,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceRecord":
        return cls(
            source_id=data.get("source_id", ""),
            name=data.get("name", ""),
            publisher=data.get("publisher", ""),
            url=data.get("url", ""),
            tier=data.get("tier", SourceTier.T5),
            source_class=data.get("source_class", SourceClass.E),
            license=data.get("license", ""),
            copyright_owner=data.get("copyright_owner", ""),
            permitted_uses=data.get("permitted_uses", []),
            attribution_required=data.get("attribution_required", True),
            redistribution_allowed=data.get("redistribution_allowed", False),
            training_allowed=data.get("training_allowed", False),
            date_accessed=data.get("date_accessed", 0.0),
            version=data.get("version", ""),
            trust_score=data.get("trust_score", 0.0),
            status=data.get("status", "discovered"),
        )


@dataclass
class VerifierIdentity:
    """A cross-cutting verification council member."""
    verifier_id: str
    name: str
    description: str = ""
    checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier_id": self.verifier_id,
            "name": self.name,
            "description": self.description,
            "checks": self.checks,
        }


# ------------------------------------------------------------------ registry

# The 14 domain directors from the KBP plan
DIRECTOR_DEFINITIONS: list[dict[str, str]] = [
    {"id": "humanities", "name": "Humanities & Culture", "description": "Philosophy, history, literature, religious studies, ethics, classics, archaeology"},
    {"id": "language", "name": "Language & Communication", "description": "Linguistics, writing, journalism, media, translation, modern and ancient languages"},
    {"id": "society", "name": "Society & Government", "description": "Political science, sociology, economics, geography, law, education, public policy"},
    {"id": "mind", "name": "Mind & Behavior", "description": "Psychology, cognitive science, neuroscience, human factors, learning science"},
    {"id": "natural_sciences", "name": "Natural Sciences", "description": "Physics, chemistry, biology, astronomy, Earth and space sciences, paleontology"},
    {"id": "formal_sciences", "name": "Formal Sciences", "description": "Mathematics, logic, statistics, theoretical computer science, computational science"},
    {"id": "computing", "name": "Computing", "description": "Computer science, software engineering, AI/ML, data science, cybersecurity, DevOps"},
    {"id": "engineering", "name": "Engineering & Design", "description": "Mechanical, electrical, civil, chemical, aerospace, robotics, architecture, product design"},
    {"id": "health", "name": "Health & Medicine", "description": "Anatomy, physiology, public health, pharmacology, diagnostics, nutrition, health informatics"},
    {"id": "agriculture", "name": "Agriculture & Food", "description": "Agronomy, soil science, animal science, food safety, culinary science, supply chains"},
    {"id": "business", "name": "Business & Operations", "description": "Accounting, finance, entrepreneurship, management, marketing, logistics, transportation"},
    {"id": "creative_arts", "name": "Creative Arts", "description": "Visual art, music, theater, film, performing arts, creative writing, conservation"},
    {"id": "egyptology", "name": "Egyptology & Ancient Worlds", "description": "Old/Middle/Late Egyptian, Demotic, Coptic, hieroglyphs, hieratic, archaeology, epigraphy"},
    {"id": "trades", "name": "Transportation, Infrastructure & Skilled Trades", "description": "Logistics, construction, carpentry, electrical, plumbing, HVAC, welding, automotive repair"},
]

# The 14 cross-cutting verification council members
VERIFIER_DEFINITIONS: list[dict[str, str]] = [
    {"id": "v_evidence", "name": "Evidence and Citation Verifier", "description": "Checks that claims have supporting evidence and accurate citations"},
    {"id": "v_logic", "name": "Logic and Contradiction Reviewer", "description": "Detects logical errors and contradictions between claims"},
    {"id": "v_stats", "name": "Statistical Methods Reviewer", "description": "Validates statistical methods and interpretations"},
    {"id": "v_security", "name": "Security Reviewer", "description": "Checks for security vulnerabilities and attack vectors"},
    {"id": "v_privacy", "name": "Privacy Reviewer", "description": "Ensures privacy minimization and data protection"},
    {"id": "v_constitutional", "name": "Constitutional and Ethics Reviewer", "description": "Checks constitutional compliance and ethical boundaries"},
    {"id": "v_legal", "name": "Legal and Licensing Reviewer", "description": "Verifies license compliance and legal restrictions"},
    {"id": "v_safety", "name": "Safety and Hazard Reviewer", "description": "Identifies safety hazards and required precautions"},
    {"id": "v_accessibility", "name": "Accessibility Reviewer", "description": "Ensures accessibility compliance"},
    {"id": "v_cost", "name": "Cost and Resource Analyst", "description": "Evaluates computational and financial costs"},
    {"id": "v_reproducibility", "name": "Reproducibility Verifier", "description": "Checks that results can be independently reproduced"},
    {"id": "v_adversarial", "name": "Adversarial Critic", "description": "Challenges claims from opposing viewpoints"},
    {"id": "v_qc", "name": "Quality-control Reviewer", "description": "General quality assessment and completeness checks"},
    {"id": "v_uncertainty", "name": "Uncertainty and Calibration Auditor", "description": "Assesses confidence calibration and uncertainty reporting"},
]

# Specialty definitions grouped by director
# These are the 279+ specialties from the KBP plan
SPECIALTY_DEFINITIONS: dict[str, list[str]] = {
    "humanities": [
        "Philosophy", "History", "Languages and Literature", "Religious Studies and Theology",
        "Classics and Ancient Civilizations", "Archaeology", "Ethics and Applied Ethics",
        "Comparative Religion and Mythology", "Heritage and Museum Studies", "Archival Science",
    ],
    "language": [
        "Linguistics", "Writing and Rhetoric", "Journalism and Media Studies",
        "Translation Studies", "Interpretation", "Terminology Management", "Localization",
        "English", "Spanish", "French", "German", "Italian", "Portuguese", "Russian",
        "Arabic", "Hebrew", "Persian", "Hindi and Urdu", "Mandarin Chinese", "Cantonese",
        "Japanese", "Korean", "Southeast Asian Languages", "African Languages",
        "Indigenous Languages", "Classical Languages",
    ],
    "society": [
        "Anthropology", "Political Science", "Sociology", "Psychology", "Economics",
        "Human Geography", "Cultural Studies", "Communication Studies", "Behavioral Science",
        "Cognitive Science", "Demography", "Criminology and Criminal Justice",
        "International Relations", "Gender and Family Studies", "Public Policy",
        "Public Administration", "Emergency Management", "Social Work", "Community Development",
    ],
    "mind": [
        "Cognitive Science", "Neuroscience", "Human Factors", "Learning Science",
        "Educational Psychology",
    ],
    "natural_sciences": [
        "Physics", "Chemistry", "Biology", "Astronomy", "Geology", "Meteorology",
        "Environmental Science", "Atmospheric Science", "Oceanography", "Space Science",
        "Paleontology", "Ecology", "Hydrology", "Forestry", "Wildlife Science",
        "Materials Science", "Nanoscience",
    ],
    "formal_sciences": [
        "Arithmetic and Fundamentals", "Algebra", "Geometry", "Trigonometry", "Calculus",
        "Mathematical Analysis", "Discrete Mathematics", "Number Theory", "Topology",
        "Logic", "Probability", "Statistics", "Optimization", "Numerical Methods",
        "Computational Science", "Operations Research", "Theoretical Computer Science",
    ],
    "computing": [
        "Computer Science", "Computer Engineering", "Software Engineering",
        "Software Architecture", "Artificial Intelligence and Machine Learning",
        "Natural Language Processing", "Computer Vision", "Speech and Audio Processing",
        "Data Science and Analytics", "Data Engineering", "Cybersecurity",
        "Digital Forensics", "Privacy Engineering", "Cloud Computing",
        "DevOps and Site Reliability", "Operating Systems",
        "Networking and Telecommunications", "Databases and Information Systems",
        "Distributed Systems", "High-performance Computing", "Computer Graphics",
        "Web Development", "Mobile Development", "Game Development", "Embedded Systems",
        "Firmware", "Robotics", "Human-computer Interaction", "Accessibility Engineering",
        "Quality Assurance and Software Testing", "IT Support and Administration",
        "Technology Project Management", "Quantum Computing", "AI Safety and Evaluation",
    ],
    "engineering": [
        "Mechanical Engineering", "Civil Engineering", "Structural Engineering",
        "Electrical Engineering", "Electronic Engineering", "Chemical Engineering",
        "Aerospace Engineering", "Automotive Engineering", "Biomedical Engineering",
        "Environmental Engineering", "Industrial Engineering", "Manufacturing Engineering",
        "Materials Engineering", "Mechatronics", "Mining Engineering", "Nuclear Engineering",
        "Petroleum Engineering", "Power and Energy Systems", "Controls and Automation",
        "Acoustical Engineering", "Marine and Naval Engineering",
        "Reliability and Maintenance Engineering", "Safety and Human Factors",
        "Architecture", "Urban and Regional Planning", "Surveying and Geomatics",
        "Additive Manufacturing and 3D Printing",
    ],
    "health": [
        "Primary Care", "Emergency Medicine", "Cardiology", "Neurology", "Oncology",
        "Psychiatry", "Pediatrics", "Geriatrics", "Surgery", "Radiology", "Pathology",
        "Genetics", "Neuroscience", "Epidemiology", "Public Health", "Pharmacology",
        "Pharmacy", "Nursing", "Dentistry", "Nutrition", "Physical Therapy",
        "Occupational Therapy", "Veterinary Medicine", "Medical Ethics", "Health Informatics",
        "Sports Medicine",
    ],
    "agriculture": [
        "Agronomy", "Horticulture", "Soil Science", "Animal Science",
        "Agricultural Engineering", "Food Science", "Food Safety", "Culinary Science",
        "Sustainable Agriculture", "Agricultural Economics", "Fisheries and Aquaculture",
        "Rangeland Management",
    ],
    "business": [
        "Accounting and Bookkeeping", "Corporate Finance", "Investment Analysis",
        "Entrepreneurship", "Business Strategy", "Operations Management",
        "Marketing and Advertising", "Market Research", "Sales", "E-commerce",
        "Supply-chain Management", "Human Resources", "Customer Service",
        "Insurance and Risk Management", "Procurement", "Product Management",
        "Project Management", "Nonprofit Administration", "Real Estate",
        "Hospitality and Tourism", "Intellectual-property Commercialization",
    ],
    "creative_arts": [
        "Visual Art", "Graphic Design", "Illustration", "Photography", "Music",
        "Theater", "Dance", "Film and Video", "Animation", "Creative Writing",
        "Editing and Fact-checking", "Sound Design", "Fashion and Textiles",
        "Interior Design", "Industrial Design", "Journalism and Media Studies",
        "Publishing and Book Production",
    ],
    "egyptology": [
        "Old Egyptian", "Middle Egyptian", "Late Egyptian", "Demotic", "Coptic",
        "Hieroglyphs", "Hieratic", "Epigraphy", "Comparative Ancient History",
        "Egyptian Archaeology",
    ],
    "trades": [
        "Transportation Planning", "Logistics", "Warehousing", "Fleet Management",
        "Aviation Operations", "Rail Systems", "Maritime Operations", "Space Mission Operations",
        "Utilities", "Renewable Energy Operations", "Construction Management",
        "Carpentry", "Residential Electrical Work", "Plumbing", "HVAC",
        "Welding and Metalworking", "Machining", "Automotive Repair", "Appliance Repair",
        "Electronics Repair", "Computer Repair", "Painting and Finishing",
        "Landscaping", "Solar Installation", "Building Inspection", "Fire Protection",
        "Facilities and Property Maintenance",
    ],
}

# Regulated domains — these specialties have authority ceiling "regulated"
REGULATED_SPECIALTIES: set[str] = {
    "Primary Care", "Emergency Medicine", "Cardiology", "Neurology", "Oncology",
    "Psychiatry", "Pediatrics", "Geriatrics", "Surgery", "Radiology", "Pathology",
    "Genetics", "Pharmacology", "Pharmacy", "Nursing", "Dentistry", "Veterinary Medicine",
    "Constitutional Law", "Civil Law", "Criminal Law", "Contract Law",
    "Intellectual Property", "Privacy and Data Protection", "Employment Law",
    "Corporate and Commercial Law", "Tax Law", "International Law",
    "Investment Analysis", "Insurance and Risk Management", "Real Estate",
    "Aviation Operations", "Maritime Operations", "Nuclear Engineering",
    "Petroleum Engineering", "Fire Protection",
}


class Registry:
    """The canonical Domain and Specialty Registry.

    Stores directors, specialties, verifiers, and sources to disk.
    All operations are local — no network required.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._directors: dict[str, DomainDirector] = {}
        self._specialties: dict[str, Specialty] = {}
        self._verifiers: dict[str, VerifierIdentity] = {}
        self._sources: dict[str, SourceRecord] = {}
        self._load()
        # Auto-seed if empty
        if not self._directors:
            self._seed()

    def _load(self) -> None:
        """Load registry from disk."""
        dfile = self.root / "directors.json"
        if dfile.exists():
            for d in json.loads(dfile.read_text(encoding="utf-8")):
                director = DomainDirector(
                    director_id=d["director_id"], name=d["name"],
                    description=d.get("description", ""),
                    specialty_ids=d.get("specialty_ids", []),
                    charter=d.get("charter", ""),
                    coverage_status=d.get("coverage_status", "registered"),
                )
                self._directors[director.director_id] = director

        sfile = self.root / "specialties.json"
        if sfile.exists():
            for s in json.loads(sfile.read_text(encoding="utf-8")):
                spec = Specialty.from_dict(s)
                self._specialties[spec.specialty_id] = spec

        vfile = self.root / "verifiers.json"
        if vfile.exists():
            for v in json.loads(vfile.read_text(encoding="utf-8")):
                verifier = VerifierIdentity(
                    verifier_id=v["verifier_id"], name=v["name"],
                    description=v.get("description", ""),
                    checks=v.get("checks", []),
                )
                self._verifiers[verifier.verifier_id] = verifier

        srcfile = self.root / "sources.json"
        if srcfile.exists():
            for s in json.loads(srcfile.read_text(encoding="utf-8")):
                src = SourceRecord.from_dict(s)
                self._sources[src.source_id] = src

    def _save(self) -> None:
        """Save registry to disk."""
        (self.root / "directors.json").write_text(
            json.dumps([d.to_dict() for d in self._directors.values()], indent=2) + "\n",
            encoding="utf-8",
        )
        (self.root / "specialties.json").write_text(
            json.dumps([s.to_dict() for s in self._specialties.values()], indent=2) + "\n",
            encoding="utf-8",
        )
        (self.root / "verifiers.json").write_text(
            json.dumps([v.to_dict() for v in self._verifiers.values()], indent=2) + "\n",
            encoding="utf-8",
        )
        (self.root / "sources.json").write_text(
            json.dumps([s.to_dict() for s in self._sources.values()], indent=2) + "\n",
            encoding="utf-8",
        )

    def _seed(self) -> None:
        """Seed the registry with the 14 directors, 279+ specialties, and 14 verifiers."""
        # Seed verifiers
        for vdef in VERIFIER_DEFINITIONS:
            self._verifiers[vdef["id"]] = VerifierIdentity(
                verifier_id=vdef["id"],
                name=vdef["name"],
                description=vdef["description"],
            )

        # Seed directors and their specialties
        for ddef in DIRECTOR_DEFINITIONS:
            did = ddef["id"]
            spec_names = SPECIALTY_DEFINITIONS.get(did, [])
            spec_ids = []
            for name in spec_names:
                # Make ID unique by including director prefix
                raw = f"{did}_{name.lower().replace(' ', '_').replace('and_', '').replace(',', '')}"
                sid = "".join(c for c in raw if c.isalnum() or c == "_")
                # Assign all verifiers to each specialty initially
                verifier_ids = list(self._verifiers.keys())
                regulated = name in REGULATED_SPECIALTIES
                authority = "regulated" if regulated else "assistive"
                spec = Specialty(
                    specialty_id=sid,
                    canonical_name=name,
                    parent_director_id=did,
                    scope_statement=f"{name} within {ddef['name']}",
                    authority_ceiling=authority,
                    regulated_domain=regulated,
                    verifier_ids=verifier_ids,
                    knowledge_depth=KnowledgeDepth.K0,
                    evaluation_status="registered",
                    network_policy="offline",
                )
                self._specialties[sid] = spec
                spec_ids.append(sid)

            self._directors[did] = DomainDirector(
                director_id=did,
                name=ddef["name"],
                description=ddef["description"],
                specialty_ids=spec_ids,
                charter=f"Maintain the field map and curriculum for {ddef['name']}",
            )

        self._save()

    # ------------------------------------------------------------------ queries

    def directors(self) -> list[DomainDirector]:
        return list(self._directors.values())

    def specialties(self) -> list[Specialty]:
        return list(self._specialties.values())

    def verifiers(self) -> list[VerifierIdentity]:
        return list(self._verifiers.values())

    def sources(self) -> list[SourceRecord]:
        return list(self._sources.values())

    def get_director(self, director_id: str) -> DomainDirector | None:
        return self._directors.get(director_id)

    def get_specialty(self, specialty_id: str) -> Specialty | None:
        return self._specialties.get(specialty_id)

    def get_source(self, source_id: str) -> SourceRecord | None:
        return self._sources.get(source_id)

    def specialties_by_director(self, director_id: str) -> list[Specialty]:
        return [s for s in self._specialties.values() if s.parent_director_id == director_id]

    def specialties_at_depth(self, depth: int) -> list[Specialty]:
        return [s for s in self._specialties.values() if s.knowledge_depth >= depth]

    # ------------------------------------------------------------------ mutations

    def register_source(self, source: SourceRecord) -> None:
        self._sources[source.source_id] = source
        self._save()

    def update_specialty_depth(self, specialty_id: str, depth: int) -> bool:
        spec = self._specialties.get(specialty_id)
        if spec is None:
            return False
        spec.knowledge_depth = depth
        spec.evaluation_status = "oriented" if depth >= KnowledgeDepth.K1 else "registered"
        spec.last_verified_at = time.time()
        self._save()
        return True

    def update_source_status(self, source_id: str, status: str) -> bool:
        src = self._sources.get(source_id)
        if src is None:
            return False
        src.status = status
        self._save()
        return True

    # ------------------------------------------------------------------ stats

    def stats(self) -> dict[str, Any]:
        depth_counts = {}
        for spec in self._specialties.values():
            depth_counts[spec.knowledge_depth] = depth_counts.get(spec.knowledge_depth, 0) + 1
        return {
            "directors": len(self._directors),
            "specialties": len(self._specialties),
            "verifiers": len(self._verifiers),
            "sources": len(self._sources),
            "regulated_specialties": sum(1 for s in self._specialties.values() if s.regulated_domain),
            "depth_distribution": depth_counts,
            "trusted_sources": sum(1 for s in self._sources.values() if s.status == "trusted"),
            "quarantined_sources": sum(1 for s in self._sources.values() if s.status == "quarantined"),
        }
