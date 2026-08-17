"""K1 orientation content for all 34 Computing specialties.

Each entry is a glossary + field map + introductory overview.
This brings every Computing specialty from K0 (registered) to K1 (oriented).
"""

COMPUTING_K1: dict[str, list[dict]] = {
    "computing_computer_science": [
        {
            "title": "Computer Science - Field Overview",
            "content": """# Computer Science

## Definition
Computer science is the study of computation, information, and automation. It encompasses the theory, design, development, and application of computational systems.

## Core Areas
- Theory of computation (what can and cannot be computed)
- Algorithms and data structures (efficient problem solving)
- Programming languages and paradigms (how to express computation)
- Computer architecture (how hardware executes computation)
- Artificial intelligence (computational models of intelligence)
- Software engineering (building reliable software systems)

## Key Concepts
- Algorithm: a finite, well-defined sequence of steps that solves a problem
- Data structure: a way of organizing data for efficient access and modification
- Complexity: the resource cost (time, space) of an algorithm as input grows
- Abstraction: hiding implementation details behind interfaces
- Turing machine: the formal model of computation; Church-Turing thesis

## Sub-disciplines
Theoretical CS, systems, AI/ML, software engineering, computer graphics, databases, networks, security, HCI.

## Foundational Texts
- Knuth, "The Art of Computer Programming"
- Cormen, Leiserson, Rivest, Stein, "Introduction to Algorithms" (CLRS)
- Sipser, "Introduction to the Theory of Computation"
- Hopcroft, Motwani, Ullman, "Introduction to Automata Theory"

## Authority Note
Advisory only. Computer science is a formal/empirical discipline; claims should be verified against primary sources and reproducible experiments.""",

            "tags": ["computer science", "computation", "algorithms", "theory", "overview"],
        }
    ],
    "computing_computer_engineering": [
        {
            "title": "Computer Engineering - Field Overview",
            "content": """# Computer Engineering

## Definition
Computer engineering integrates electrical engineering and computer science to design and build computer systems and their components.

## Core Areas
- Digital logic design (gates, flip-flops, state machines)
- Microprocessor architecture (pipelining, superscalar, out-of-order)
- Memory systems (caches, DRAM, virtual memory)
- Embedded systems (microcontrollers, real-time constraints)
- Hardware-software co-design
- VLSI design (chip layout, fabrication)

## Key Concepts
- ISA (Instruction Set Architecture): the contract between hardware and software
- Pipeline: overlapping instruction execution stages for throughput
- Cache hierarchy: fast small memory near the CPU, slower larger memory further away
- Clock domain: a region of synchronous logic driven by one clock
- SoC (System on Chip): CPU, memory controller, peripherals on one die

## Hardware Description Languages
Verilog, VHDL, SystemVerilog, Chisel.

## Foundational Texts
- Patterson & Hennessy, "Computer Organization and Design"
- Hennessy & Patterson, "Computer Architecture: A Quantitative Approach"
- Weste & Harris, "CMOS VLSI Design"

## Authority Note
Advisory. Hardware specifications are authoritative from manufacturer datasheets.""",

            "tags": ["computer engineering", "hardware", "digital logic", "architecture", "overview"],
        }
    ],
    "computing_software_engineering": [
        {
            "title": "Software Engineering - Field Overview",
            "content": """# Software Engineering

## Definition
Software engineering is the systematic application of engineering principles to the design, development, maintenance, and testing of software.

## Core Areas
- Requirements engineering (eliciting, analyzing, specifying)
- Software design (architecture, patterns, interfaces)
- Construction (coding, refactoring, code review)
- Testing (unit, integration, system, acceptance, property-based)
- Maintenance (bug fixing, enhancement, migration)
- Process (agile, waterfall, DevOps, CI/CD)

## Key Concepts
- Coupling: degree of interdependence between modules (lower is better)
- Cohesion: degree to which a module's parts belong together (higher is better)
- SOLID principles: SRP, OCP, LSP, ISP, DIP
- Technical debt: the future cost of shortcuts taken now
- Code smell: a surface indicator of a deeper design problem
- Refactoring: changing internal structure without changing external behavior

## Lifecycle Models
- Waterfall: sequential phases (requirements, design, implementation, verification, maintenance)
- Agile: iterative, incremental, adaptive (Scrum, Kanban, XP)
- Spiral: risk-driven iterative
- DevOps: development + operations integration with automation

## Standards
- ISO/IEC 12207 (software lifecycle processes)
- ISO/IEC 25010 (software quality model)
- IEEE 828 (configuration management)

## Foundational Texts
- Sommerville, "Software Engineering"
- Pressman, "Software Engineering: A Practitioner's Approach"
- Beck, "Test-Driven Development"
- Fowler, "Refactoring"

## Authority Note
Advisory. Standards documents are authoritative from ISO/IEEE.""",

            "tags": ["software engineering", "design", "testing", "process", "overview"],
        }
    ],
    "computing_software_architecture": [
        {
            "title": "Software Architecture - Field Overview",
            "content": """# Software Architecture

## Definition
Software architecture is the high-level structure of a software system: its components, their relationships, and the principles guiding its design and evolution.

## Core Areas
- Architectural styles (layered, client-server, microservices, event-driven, pipe-filter)
- Quality attributes (performance, scalability, reliability, security, modifiability)
- Architectural patterns (MVC, MVVM, CQRS, event sourcing, hexagonal)
- Documentation (4+1 views, C4 model, ADRs)
- Evaluation (ATAM, SAAM, trade-off analysis)

## Key Concepts
- Component: a unit of computation with defined interfaces
- Connector: the mechanism by which components communicate
- Quality attribute: a measurable property (latency, throughput, MTBF)
- Architectural drift: gradual divergence from intended architecture
- Conway's Law: systems mirror the communication structure of the organization

## Patterns
- Layered: strict layer dependencies (presentation, business, data)
- Microservices: small independent services communicating over network
- Event-driven: components react to events asynchronously
- CQRS: separate read and write models
- Hexagonal (ports and adapters): isolate domain from infrastructure

## Foundational Texts
- Bass, Clements, Kazman, "Software Architecture in Practice"
- Richards, Ford, "Fundamentals of Software Architecture"
- Newman, "Building Microservices"
- Nygard, "Release It!"

## Authority Note
Advisory. Architecture decisions are context-dependent; no universal best architecture.""",

            "tags": ["software architecture", "patterns", "quality attributes", "overview"],
        }
    ],
    "computing_artificial_intelligence_machine_learning": [
        {
            "title": "AI and Machine Learning - Field Overview",
            "content": """# Artificial Intelligence and Machine Learning

## Definition
AI is the field of building systems that perform tasks requiring intelligence. Machine learning is a subset where systems learn patterns from data instead of being explicitly programmed.

## Core Areas
- Supervised learning (classification, regression from labeled data)
- Unsupervised learning (clustering, dimensionality reduction)
- Reinforcement learning (learning from reward signals)
- Deep learning (multi-layer neural networks)
- Generative models (GANs, VAEs, diffusion, LLMs)
- Evaluation (metrics, cross-validation, bias-variance, overfitting)

## Key Concepts
- Model: a function learned from data that maps inputs to outputs
- Training: the process of adjusting model parameters to fit data
- Inference: using a trained model to make predictions
- Loss function: a measure of prediction error to minimize
- Gradient descent: iterative parameter update using loss gradients
- Overfitting: model memorizes training data, fails to generalize
- Regularization: techniques to prevent overfitting (L1, L2, dropout)

## Common Algorithms
- Linear/logistic regression, decision trees, random forests, gradient boosting
- k-NN, SVM, naive Bayes
- Neural networks: CNN, RNN, LSTM, Transformer
- K-means, DBSCAN, PCA, t-SNE
- Q-learning, policy gradient, PPO

## Frameworks
PyTorch, TensorFlow, JAX, scikit-learn, Hugging Face Transformers.

## Foundational Texts
- Russell & Norvig, "Artificial Intelligence: A Modern Approach"
- Goodfellow, Bengio, Courville, "Deep Learning"
- Bishop, "Pattern Recognition and Machine Learning"
- Sutton & Barto, "Reinforcement Learning: An Introduction"

## Authority Note
Advisory. ML claims require reproducible experiments and held-out evaluation. Beware of benchmark overfitting and data leakage.""",

            "tags": ["AI", "machine learning", "deep learning", "neural networks", "overview"],
        }
    ],
    "computing_natural_language_processing": [
        {
            "title": "Natural Language Processing - Field Overview",
            "content": """# Natural Language Processing

## Definition
NLP is the field of computational interaction with human language: understanding, generating, translating, and analyzing text and speech.

## Core Areas
- Tokenization and text normalization
- Part-of-speech tagging, parsing, dependency analysis
- Named entity recognition, relation extraction
- Sentiment analysis, text classification
- Machine translation
- Language modeling (n-gram, neural, transformer-based)
- Question answering, summarization, dialogue systems

## Key Concepts
- Token: a unit of text (word, subword, character)
- Embedding: a vector representation of a token or sentence
- Language model: a probability distribution over sequences
- Attention: weighting relevant parts of input when producing output
- Transformer: the architecture behind modern LLMs (self-attention, no recurrence)
- Fine-tuning: adapting a pretrained model to a specific task
- Hallucination: a confident but factually wrong model output

## Models and Tools
- BERT, GPT, T5, Llama, Qwen families
- Hugging Face Transformers, spaCy, NLTK, CoreNLP

## Foundational Texts
- Jurafsky & Martin, "Speech and Language Processing"
- Manning & Schütze, "Foundations of Statistical NLP"
- Goldberg, "Neural Network Methods for Natural Language Processing"

## Authority Note
Advisory. LLM outputs are not authoritative; verify factual claims against primary sources.""",

            "tags": ["NLP", "language", "text", "transformers", "overview"],
        }
    ],
    "computing_computer_vision": [
        {
            "title": "Computer Vision - Field Overview",
            "content": """# Computer Vision

## Definition
Computer vision is the field of enabling computers to interpret and understand visual information from images and video.

## Core Areas
- Image processing (filtering, edge detection, morphology)
- Feature detection (corners, blobs, SIFT, SURF, ORB)
- Segmentation (semantic, instance, panoptic)
- Object detection (R-CNN, YOLO, SSD)
- Image classification (CNNs, ViTs)
- 3D vision (stereo, structure from motion, SLAM)
- Generative vision (GANs, diffusion for image synthesis)

## Key Concepts
- Pixel: smallest image element
- Convolution: applying a filter kernel across an image
- Pooling: downsampling feature maps
- Bounding box: rectangle localizing an object
- IoU (Intersection over Union): overlap metric for detection
- Backbone: a feature-extracting network (ResNet, EfficientNet)

## Tools
OpenCV, PIL/Pillow, scikit-image, Detectron2, MMDetection.

## Foundational Texts
- Szeliski, "Computer Vision: Algorithms and Applications"
- Goodfellow et al., "Deep Learning" (vision chapters)
- Forsyth & Ponce, "Computer Vision: A Modern Approach"

## Authority Note
Advisory. Vision models can fail adversarially; verify safety-critical detections.""",

            "tags": ["computer vision", "images", "CNN", "detection", "overview"],
        }
    ],
    "computing_speech_audio_processing": [
        {
            "title": "Speech and Audio Processing - Field Overview",
            "content": """# Speech and Audio Processing

## Definition
Computational analysis and generation of audio signals, with emphasis on human speech.

## Core Areas
- Speech recognition (ASR): audio to text
- Speech synthesis (TTS): text to audio
- Speaker identification and diarization
- Audio classification (music, environment, emotion)
- Noise suppression and enhancement
- Music information retrieval

## Key Concepts
- Sample rate: audio samples per second (Hz)
- Spectrogram: time-frequency representation of audio
- MFCC: Mel-frequency cepstral coefficients, classic speech features
- Phoneme: a unit of speech sound
- VAD: voice activity detection
- Beamforming: directional audio capture with multiple microphones

## Models
- Whisper (OpenAI), Wav2Vec2, HuBERT
- Tacotron, FastSpeech, VITS for TTS
- Webrtc VAD, RNNoise for enhancement

## Tools
librosa, soundfile, pydub, ffmpeg, ESPnet, Kaldi.

## Foundational Texts
- Rabiner & Schafer, "Theory and Applications of Digital Speech Processing"
- Quatieri, "Discrete-Time Speech Signal Processing"

## Authority Note
Advisory.""",

            "tags": ["speech", "audio", "ASR", "TTS", "overview"],
        }
    ],
    "computing_data_science_analytics": [
        {
            "title": "Data Science and Analytics - Field Overview",
            "content": """# Data Science and Analytics

## Definition
Data science extracts knowledge and insight from data using statistics, ML, and domain expertise. Analytics is the broader practice of analyzing data to drive decisions.

## Core Areas
- Data collection and cleaning
- Exploratory data analysis (EDA)
- Statistical inference and hypothesis testing
- Predictive modeling
- Data visualization
- Communication of findings

## Key Concepts
- Variable types: numerical, categorical, ordinal, temporal
- Central tendency: mean, median, mode
- Dispersion: variance, standard deviation, IQR
- Correlation: linear association between variables (does not imply causation)
- p-value: probability of observing data as extreme under null hypothesis
- Confidence interval: range estimating a population parameter
- Bias: systematic error in data collection or modeling

## Workflow
1. Define question
2. Collect data
3. Clean and preprocess
4. Explore (EDA)
5. Model
6. Validate
7. Communicate

## Tools
Python (pandas, numpy, matplotlib, seaborn, scikit-learn), R, SQL, Jupyter, Tableau, Power BI.

## Foundational Texts
- Wickham & Grolemund, "R for Data Science"
- McKinney, "Python for Data Analysis"
- Tufte, "The Visual Display of Quantitative Information"
- Hastie, Tibshirani, Friedman, "The Elements of Statistical Learning"

## Authority Note
Advisory. Statistical claims require proper methodology and disclosure of assumptions.""",

            "tags": ["data science", "analytics", "statistics", "visualization", "overview"],
        }
    ],
    "computing_data_engineering": [
        {
            "title": "Data Engineering - Field Overview",
            "content": """# Data Engineering

## Definition
Data engineering designs and builds systems that collect, store, transform, and deliver data at scale for downstream analytics and ML.

## Core Areas
- Data ingestion (batch, streaming, CDC)
- Storage (data lakes, data warehouses, lakehouses)
- ETL/ELT pipelines (extract, transform, load)
- Orchestration (DAGs, scheduling, retries)
- Data quality and observability
- Schema management and evolution

## Key Concepts
- Data lake: raw storage (files, object storage) for unstructured/structured data
- Data warehouse: structured storage optimized for analytics (columnar)
- ETL: extract from source, transform, load to destination
- ELT: load first, transform in the warehouse
- DAG: directed acyclic graph of pipeline tasks
- Idempotency: re-running a pipeline produces the same result
- Schema-on-read vs schema-on-write

## Tools
Apache Airflow, dbt, Spark, Kafka, Flink, Snowflake, BigQuery, Databricks, Prefect, Dagster.

## Foundational Texts
- Kleppmann, "Designing Data-Intensive Applications"
- Kimball & Ross, "The Data Warehouse Toolkit"

## Authority Note
Advisory.""",

            "tags": ["data engineering", "ETL", "pipelines", "warehouses", "overview"],
        }
    ],
    "computing_cybersecurity": [
        {
            "title": "Cybersecurity - Field Overview",
            "content": """# Cybersecurity

## Definition
Cybersecurity is the practice of protecting systems, networks, data, and users from digital attack, damage, and unauthorized access.

## Core Areas
- Confidentiality, Integrity, Availability (CIA triad)
- Threat modeling (STRIDE, PASTA)
- Vulnerability assessment and penetration testing
- Cryptography (symmetric, asymmetric, hashing, signing)
- Network security (firewalls, IDS/IPS, zero trust)
- Application security (OWASP Top 10, SAST, DAST)
- Incident response and forensics
- Identity and access management

## Key Concepts
- Vulnerability: a weakness that can be exploited
- Exploit: a technique that takes advantage of a vulnerability
- Threat: a potential actor or event that can cause harm
- Risk: probability x impact of a threat materializing
- Zero trust: never trust, always verify; no implicit network trust
- Defense in depth: multiple independent layers of security
- Least privilege: grant only the access needed

## Common Attack Classes
- Injection (SQL, command, XSS)
- Authentication failures
- Cryptographic failures
- Insecure deserialization
- Supply chain attacks
- Social engineering (phishing, pretexting)
- DoS/DDoS

## Standards
- NIST CSF, NIST 800-53
- ISO/IEC 27001/27002
- OWASP Top 10, ASVS
- CIS Controls

## Foundational Texts
- Anderson, "Security Engineering"
- Schneier, "Applied Cryptography" and "Secrets and Lies"
- Stallings, "Cryptography and Network Security"
- Howard & Lipner, "The Security Development Lifecycle"

## Authority Note
Advisory. Security guidance from NIST, ISO, and OWASP is authoritative. Never assist with offensive tooling against systems you do not own and are not authorized to test.""",

            "tags": ["cybersecurity", "security", "cryptography", "OWASP", "overview"],
        }
    ],
    "computing_digital_forensics": [
        {
            "title": "Digital Forensics - Field Overview",
            "content": """# Digital Forensics

## Definition
Digital forensics is the application of investigative techniques to identify, preserve, analyze, and report on digital evidence.

## Core Areas
- Disk forensics (file systems, deleted data, slack space)
- Memory forensics (RAM analysis, process artifacts)
- Network forensics (packet capture, flow analysis)
- Mobile forensics (iOS, Android extraction)
- Malware analysis (static, dynamic)
- Incident response triage

## Key Concepts
- Chain of custody: documented handling of evidence
- Write blocker: hardware/software preventing evidence modification
- Hashing (SHA-256): proving evidence integrity
- Volatility: order of evidence loss (registers, RAM, disk, network)
- Live vs dead acquisition
- Timestamp analysis (MAC times: modified, accessed, changed)

## Tools
Autopsy, Sleuth Kit, EnCase, FTK, Volatility, Wireshark, Kali, Plaso.

## Foundational Texts
- Casey, "Digital Evidence and Computer Crime"
- Carrier, "File System Forensic Analysis"

## Authority Note
Advisory. Forensic procedures must follow jurisdictional legal requirements.""",

            "tags": ["forensics", "evidence", "investigation", "overview"],
        }
    ],
    "computing_privacy_engineering": [
        {
            "title": "Privacy Engineering - Field Overview",
                "content": """# Privacy Engineering

## Definition
Privacy engineering is the practice of embedding privacy protections into the design and operation of systems.

## Core Areas
- Privacy by design (proactive, not reactive)
- Data minimization (collect only what is needed)
- Anonymization and pseudonymization
- Differential privacy
- Consent and preference management
- Privacy impact assessments

## Key Concepts
- PII: personally identifiable information
- k-anonymity, l-diversity, t-closeness: anonymity models
- Differential privacy: mathematical guarantee about disclosure risk
- Federated learning: train without centralizing raw data
- Purpose limitation: use data only for stated purposes
- Right to be forgotten: deletion on request

## Standards
- GDPR (EU), CCPA/CPRA (California)
- ISO/IEC 27701 (privacy information management)
- NIST Privacy Framework

## Foundational Texts
- Cavoukian, "Privacy by Design"
- NIST Privacy Framework 1.0
- Dwork & Roth, "The Algorithmic Foundations of Differential Privacy"

## Authority Note
Advisory. Legal privacy obligations are jurisdiction-specific and authoritative from the relevant regulator.""",

            "tags": ["privacy", "GDPR", "anonymization", "overview"],
        }
    ],
    "computing_cloud_computing": [
        {
            "title": "Cloud Computing - Field Overview",
            "content": """# Cloud Computing

## Definition
Cloud computing delivers computing services (servers, storage, databases, networking, software) over the internet on demand.

## Service Models
- IaaS: infrastructure (VMs, storage, networking) — AWS EC2, Azure VM, GCE
- PaaS: platform (managed runtime, databases) — App Engine, Elastic Beanstalk
- SaaS: software (applications) — Gmail, Salesforce, M365
- FaaS/Serverless: functions on demand — AWS Lambda, Cloud Functions

## Deployment Models
- Public cloud, private cloud, hybrid, multi-cloud

## Key Concepts
- Elasticity: scale resources up/down automatically
- Multi-tenancy: shared infrastructure, isolated tenants
- Region/Availability Zone: geographic fault isolation
- Managed service: provider operates the service, you consume it
- IaC (Infrastructure as Code): declarative infrastructure — Terraform, CloudFormation
- Container orchestration: Kubernetes, ECS, GKE

## Major Providers
AWS, Microsoft Azure, Google Cloud Platform, Alibaba Cloud, Oracle Cloud.

## Foundational Texts
- Armbrust et al., "A View of Cloud Computing" (CACM 2010)
- AWS Well-Architected Framework

## Authority Note
Advisory. Provider documentation is authoritative for managed services.""",

            "tags": ["cloud", "AWS", "Azure", "GCP", "overview"],
        }
    ],
    "computing_devops_site_reliability": [
        {
            "title": "DevOps and Site Reliability - Field Overview",
            "content": """# DevOps and Site Reliability Engineering

## Definition
DevOps integrates development and operations to shorten the delivery cycle and improve reliability. SRE applies software engineering to operations problems.

## Core Areas
- CI/CD (continuous integration, continuous delivery/deployment)
- Infrastructure as Code
- Observability (metrics, logs, traces)
- Incident management (on-call, postmortems)
- Capacity planning
- Release engineering (canary, blue/green, feature flags)

## Key Concepts
- DORA metrics: deployment frequency, lead time, change failure rate, MTTR
- SLO (Service Level Objective): a target for service reliability (e.g. 99.9% uptime)
- SLI: the indicator being measured (e.g. success rate)
- Error budget: the allowable unreliability before action is required
- Toil: repetitive, automatable, low-value work
- Blameless postmortem: focus on systems, not individuals
- Canary release: roll out to a small subset before full rollout

## Tools
Git, Jenkins, GitHub Actions, GitLab CI, ArgoCD, Terraform, Ansible, Prometheus, Grafana, ELK, OpenTelemetry, PagerDuty.

## Foundational Texts
- Kim, Humble, Debois, Willis, "The DevOps Handbook"
- Kim, "The Phoenix Project"
- Beyer et al., "Site Reliability Engineering" (Google)
- Beyer et al., "The Site Reliability Workbook"

## Authority Note
Advisory.""",

            "tags": ["DevOps", "SRE", "CI/CD", "observability", "overview"],
        }
    ],
    "computing_operating_systems": [
        {
            "title": "Operating Systems - Field Overview",
            "content": """# Operating Systems

## Definition
An operating system manages computer hardware and software resources and provides common services for computer programs.

## Core Areas
- Process and thread management (scheduling, context switching)
- Memory management (virtual memory, paging, segmentation)
- File systems (journaling, copy-on-write, distributed)
- I/O and device drivers
- Inter-process communication (pipes, sockets, shared memory, signals)
- Security and protection (users, permissions, capabilities)
- Boot and init (BIOS/UEFI, bootloader, init system)

## Key Concepts
- Process: a running program with its own address space
- Thread: a unit of execution within a process, sharing its memory
- Syscall: the interface between user programs and the kernel
- Context switch: saving/restoring state to switch execution
- Page fault: hardware event when a virtual page is not in physical memory
- Deadlock: processes waiting on each other indefinitely
- Kernel mode vs user mode

## Scheduling Algorithms
Round-robin, priority, CFS (Linux), multilevel feedback queue.

## File Systems
ext4, XFS, Btrfs, ZFS, APFS, NTFS, FAT32/exFAT.

## Init Systems
systemd, OpenRC, runit, s6.

## Foundational Texts
- Tanenbaum & Bos, "Modern Operating Systems"
- Silberschatz, Galvin, Gagne, "Operating System Concepts"
- Love, "Linux Kernel Development"
- Bovet & Cesati, "Understanding the Linux Kernel"

## Authority Note
Advisory. Kernel documentation (man pages, kernel.org docs) is authoritative.""",

            "tags": ["operating systems", "kernel", "processes", "memory", "overview"],
        }
    ],
    "computing_networking_telecommunications": [
        {
            "title": "Networking and Telecommunications - Field Overview",
            "content": """# Networking and Telecommunications

## Definition
Networking connects computers to exchange data. Telecommunications encompasses broader communication systems including voice, radio, and cellular.

## Core Areas
- Protocol layers (OSI 7-layer, TCP/IP 4-layer)
- Routing and switching
- DNS and naming
- Transport (TCP, UDP, QUIC)
- Application protocols (HTTP, HTTPS, SMTP, SSH, gRPC)
- Wireless (Wi-Fi, Bluetooth, cellular 4G/5G/6G)
- Network security (TLS, IPsec, firewalls, VPN)

## Key Concepts
- IP address: a network location (IPv4 32-bit, IPv6 128-bit)
- Port: a communication endpoint on a host (0-65535)
- Packet: a unit of network data with headers
- Handshake: negotiation that establishes a connection
- MTU: maximum transmission unit (packet size)
- NAT: network address translation
- CDN: content delivery network for low-latency distribution
- BGP: border gateway protocol, the internet's routing backbone

## Tools
Wireshark, tcpdump, nmap, curl, dig, ip/iproute2, netcat, mtr.

## Foundational Texts
- Kurose & Ross, "Computer Networking: A Top-Down Approach"
- Tanenbaum & Wetherall, "Computer Networks"
- Stevens, "TCP/IP Illustrated" (vols 1-3)

## Authority Note
Advisory. RFCs from the IETF are authoritative for internet protocols.""",

            "tags": ["networking", "TCP/IP", "DNS", "HTTP", "overview"],
        }
    ],
    "computing_databases_information_systems": [
        {
            "title": "Databases and Information Systems - Field Overview",
            "content": """# Databases and Information Systems

## Definition
A database is an organized collection of structured or unstructured data. A database management system (DBMS) provides creation, querying, and transactional access.

## Core Areas
- Relational (SQL): PostgreSQL, MySQL, SQLite, Oracle, SQL Server
- NoSQL: document (MongoDB), key-value (Redis), wide-column (Cassandra), graph (Neo4j)
- NewSQL / distributed SQL: CockroachDB, Spanner, TiDB
- Time-series (InfluxDB, TimescaleDB)
- Vector databases (pgvector, Milvus, Qdrant)
- Transactions and ACID
- Indexing (B-tree, hash, LSM, inverted)
- Query optimization

## Key Concepts
- Table, row, column, schema
- Primary key, foreign key
- Index: a structure that speeds up lookups
- Normalization (1NF-BCNF): reducing redundancy
- Transaction: atomic unit of work
- ACID: Atomicity, Consistency, Isolation, Durability
- BASE: Basically Available, Soft state, Eventual consistency (NoSQL)
- CAP theorem: consistency, availability, partition tolerance (pick 2)
- Isolation levels: read uncommitted, read committed, repeatable read, serializable

## SQL Basics
SELECT, INSERT, UPDATE, DELETE, JOIN (inner, left, right, full), GROUP BY, ORDER BY, subqueries, window functions.

## Foundational Texts
- Garcia-Molina, Ullman, Widom, "Database Systems: The Complete Book"
- Silberschatz, Korth, Sudarshan, "Database System Concepts"
- Kleppmann, "Designing Data-Intensive Applications"
- Stonebraker & Hellerstein, "What Goes Around Comes Around"

## Authority Note
Advisory. Vendor documentation is authoritative for specific DBMS behavior.""",

            "tags": ["databases", "SQL", "NoSQL", "ACID", "overview"],
        }
    ],
    "computing_distributed_systems": [
        {
            "title": "Distributed Systems - Field Overview",
            "content": """# Distributed Systems

## Definition
A distributed system is a set of independent computers that appears to its users as a single coherent system.

## Core Areas
- Communication (RPC, messaging, pub/sub)
- Consistency models (linearizability, sequential, eventual, causal)
- Consensus (Paxos, Raft, Byzantine)
- Replication and partitioning
- Failure detection and tolerance
- Time and ordering (physical, logical, hybrid clocks)
- Load balancing and sharding

## Key Concepts
- Node: a participant in the system
- Replica: a copy of data on another node
- Quorum: minimum nodes that must agree (W + R > N)
- Split-brain: two leaders after a network partition
- Byzantine fault: arbitrary/malicious behavior, not just crash
- Idempotency: an operation can be repeated safely
- Exactly-once semantics: hard; usually at-least-once + idempotency
- Gossip protocol: epidemic-style information propagation

## Consensus Algorithms
Paxos, Multi-Paxos, Raft, PBFT, HotStuff.

## Systems
etcd, ZooKeeper, Consul, Cassandra, Kafka, Spanner, DynamoDB.

## Foundational Texts
- Tanenbaum & Van Steen, "Distributed Systems"
- Coulouris, Dollimore, Kindberg, "Distributed Systems: Concepts and Design"
- Kleppmann, "Designing Data-Intensive Applications"

## Authority Note
Advisory. Distributed systems claims require formal proofs or rigorous empirical validation.""",

            "tags": ["distributed systems", "consensus", "replication", "CAP", "overview"],
        }
    ],
    "computing_highperformance_computing": [
        {
            "title": "High-performance Computing - Field Overview",
            "content": """# High-performance Computing

## Definition
HPC is the practice of aggregating computing power to solve large-scale problems faster than a single machine could.

## Core Areas
- Parallel programming models (MPI, OpenMP, CUDA, OpenCL, SYCL)
- Cluster and supercomputer architecture
- Numerical algorithms and optimization
- Performance profiling and tuning
- I/O for HPC (parallel file systems: Lustre, GPFS)
- Accelerators (GPUs, TPUs, FPGAs)

## Key Concepts
- FLOPS: floating-point operations per second
- Amdahl's law: speedup limited by serial fraction
- Gustafson's law: scaled speedup with problem size
- Roofline model: performance bound by compute or memory bandwidth
- Data locality: keep computation near its data
- SIMD: single instruction, multiple data
- NUMA: non-uniform memory access across sockets

## Tools
SLURM, PBS, MPI (OpenMPI, MPICH), CUDA, ROCm, OpenMP, PETSc, Trilinos.

## Foundational Texts
- Pacheco, "An Introduction to Parallel Programming"
- Hennessy & Patterson, "Computer Architecture: A Quantitative Approach"
- Dongarra et al., "Sourcebook of Parallel Computing"

## Authority Note
Advisory.""",

            "tags": ["HPC", "parallel", "MPI", "CUDA", "overview"],
        }
    ],
    "computing_computer_graphics": [
        {
            "title": "Computer Graphics - Field Overview",
            "content": """# Computer Graphics

## Definition
Computer graphics is the field of generating, manipulating, and displaying images with computers.

## Core Areas
- Rasterization (real-time rendering pipeline)
- Ray tracing and path tracing (physically based rendering)
- Shading and materials (PBR, BRDF, BSDF)
- Texturing and sampling
- Geometric modeling (meshes, splines, CSG)
- Animation (keyframe, skeletal, physics-based)
- GPU programming (shaders, compute)

## Key Concepts
- Pixel, fragment, vertex, primitive, triangle
- Frame buffer: the image being rendered
- Z-buffer: depth testing for hidden surface removal
- Shader: a GPU program (vertex, fragment, compute, geometry, tessellation)
- UV mapping: 2D texture to 3D surface
- Normal: surface direction for lighting
- Anti-aliasing: reducing jagged edges (MSAA, FXAA, TAA)
- Color space: sRGB, Rec.2020, linear, HDR

## APIs
OpenGL, Vulkan, DirectX 11/12, Metal, WebGL, WebGPU.

## Engines
Unreal, Unity, Godot, Blender (for authoring).

## Foundational Texts
- Shirley & Marschner, "Fundamentals of Computer Graphics"
- Pharr, Jakob, Humphreys, "Physically Based Rendering" (PBRT)
- Akenine-Möller, Haines, Hoffman, "Real-Time Rendering"

## Authority Note
Advisory.""",

            "tags": ["graphics", "rendering", "GPU", "shaders", "overview"],
        }
    ],
    "computing_web_development": [
        {
            "title": "Web Development - Field Overview",
            "content": """# Web Development

## Definition
Web development is the practice of building applications that run in a browser or communicate over HTTP.

## Core Areas
- Frontend (HTML, CSS, JavaScript, frameworks)
- Backend (servers, APIs, databases)
- Full-stack (both)
- Web performance (Core Web Vitals, caching, CDN)
- Web security (CORS, CSP, XSS, CSRF, OAuth)
- Accessibility (WCAG, ARIA)
- Progressive Web Apps, Service Workers

## Key Concepts
- DOM: the document object model, browser's representation of HTML
- HTTP method: GET, POST, PUT, PATCH, DELETE
- Status code: 1xx informational, 2xx success, 3xx redirect, 4xx client error, 5xx server error
- REST: representational state transfer, resource-oriented API style
- GraphQL: query language and runtime for APIs
- WebSocket: full-duplex persistent connection
- SSR vs CSR vs SSG: server-side rendering, client-side, static generation
- Cookie, session, JWT: authentication mechanisms

## Frontend Frameworks
React, Vue, Svelte, Angular, Solid, Qwik. Meta-frameworks: Next.js, Nuxt, SvelteKit.

## Backend Languages/Stacks
Node.js, Python (Django, Flask, FastAPI), Ruby (Rails), Go, Java (Spring), PHP (Laravel), Rust (Axum).

## Foundational Texts
- MDN Web Docs (authoritative reference)
- Flanagan, "JavaScript: The Definitive Guide"
- Haverbeke, "Eloquent JavaScript"
- Richardson & Ruby, "RESTful Web Services"

## Authority Note
Advisory. MDN and WHATWG/W3C specifications are authoritative.""",

            "tags": ["web", "frontend", "backend", "HTTP", "overview"],
        }
    ],
    "computing_mobile_development": [
        {
            "title": "Mobile Development - Field Overview",
            "content": """# Mobile Development

## Definition
Mobile development is the practice of building applications for mobile devices, primarily iOS and Android.

## Core Areas
- Native iOS (Swift, SwiftUI, UIKit)
- Native Android (Kotlin, Jetpack Compose, Views)
- Cross-platform (Flutter, React Native, .NET MAUI)
- Progressive Web Apps
- Mobile UX (touch, gestures, small screens, offline)
- App store distribution (App Store, Google Play)
- Performance and battery optimization

## Key Concepts
- Activity (Android) / ViewController (iOS): a screen
- Lifecycle: foreground, background, suspended, terminated states
- Intent (Android): a message requesting an action
- Push notification: server-initiated message via APNs/FCM
- Deep link: URL that opens a specific app screen
- Responsive layout: adapting to screen size and orientation
- Background tasks: work done when app is not foregrounded

## Tools
Xcode, Android Studio, Flutter SDK, React Native CLI, Fastlane.

## Foundational Texts
- Apple Human Interface Guidelines
- Google Material Design Guidelines
- Apple Swift Programming Language Guide
- Android Developer Documentation

## Authority Note
Advisory. Platform vendor documentation is authoritative.""",

            "tags": ["mobile", "iOS", "Android", "Flutter", "overview"],
        }
    ],
    "computing_game_development": [
        {
            "title": "Game Development - Field Overview",
            "content": """# Game Development

## Definition
Game development is the practice of designing and building interactive games, combining software engineering, art, audio, and design.

## Core Areas
- Game engines (Unity, Unreal, Godot, custom)
- Rendering (2D, 3D, shaders, lighting)
- Physics simulation (rigid body, collision, constraints)
- Audio (3D spatial, mixing, middleware: FMOD, Wwise)
- AI (pathfinding, behavior trees, utility AI)
- Networking (lockstep, client-server, rollback netcode)
- Tooling (editors, asset pipelines, scripting)
- Game design (mechanics, loops, balance, monetization)

## Key Concepts
- Game loop: input -> update -> render, repeated each frame
- Fixed timestep: deterministic physics updates at fixed intervals
- Entity-Component-System (ECS): composition over inheritance
- Scene graph: hierarchical spatial organization
- Asset: a resource (mesh, texture, sound, script)
- Prefab/Scene: a reusable game object template
- Coroutine: a function that can pause and resume across frames
- Delta time: time since last frame, used for frame-independent motion

## Scripting Languages
GDScript (Godot), C# (Unity), Lua (many engines), Python (some), C++ (Unreal, custom).

## Foundational Texts
- Gregory, "Game Engine Architecture"
- Nystrom, "Game Programming Patterns"
- Eberly, "3D Game Engine Design"
- Schell, "The Art of Game Design"

## Authority Note
Advisory.""",

            "tags": ["games", "engine", "Godot", "Unity", "overview"],
        }
    ],
    "computing_embedded_systems": [
        {
            "title": "Embedded Systems - Field Overview",
            "content": """# Embedded Systems

## Definition
An embedded system is a computer dedicated to a specific function within a larger system, often with real-time and resource constraints.

## Core Areas
- Microcontrollers (ARM Cortex-M, AVR, ESP32, RISC-V)
- Real-time operating systems (FreeRTOS, Zephyr, ThreadX)
- Bare-metal programming
- Device drivers and peripherals (GPIO, I2C, SPI, UART, ADC, PWM)
- Interrupts and ISRs
- Power management (sleep modes, low-power design)
- Hardware-software co-design

## Key Concepts
- Register: a memory-mapped hardware control location
- Interrupt: a hardware signal that suspends normal execution
- ISR: interrupt service routine
- DMA: direct memory access, peripheral-to-memory without CPU
- Watchdog timer: resets the system if not periodically kicked
- Bit-banging: implementing a protocol in software via GPIO
- Real-time: deterministic timing guarantees (hard vs soft)
- Cross-compilation: building on one architecture for another

## Tools
GCC ARM, IAR, Keil, PlatformIO, OpenOCD, JTAG/SWD debuggers, logic analyzers, oscilloscopes.

## Foundational Texts
- Barr & Massa, "Programming Embedded Systems"
- Valvano, "Embedded Microcomputer Systems"
- Yiu, "The Definitive Guide to ARM Cortex-M0/M3/M4"

## Authority Note
Advisory. Datasheets and reference manuals from silicon vendors are authoritative.""",

            "tags": ["embedded", "microcontroller", "RTOS", "firmware", "overview"],
        }
    ],
    "computing_firmware": [
        {
            "title": "Firmware - Field Overview",
            "content": """# Firmware

## Definition
Firmware is the low-level software that controls hardware, typically stored in non-volatile memory (flash, ROM, EEPROM) on the device itself.

## Core Areas
- Bootloaders (U-Boot, Coreboot, GRUB, custom)
- BIOS/UEFI
- Device firmware (peripherals, sensors, controllers)
- Firmware update mechanisms (OTA, secure boot, signed updates)
- Hardware initialization (clocks, memory, peripherals)
- Power-on self test (POST)

## Key Concepts
- ROM, flash, EEPROM: non-volatile storage types
- Bootloader: small program that loads the main OS or application
- UEFI: modern firmware interface replacing BIOS
- Secure boot: cryptographic verification of firmware/OS at boot
- Firmware update: replacing firmware, often with rollback support
- A/B partitioning: two firmware slots for safe updates
- Memory map: layout of memory regions (flash, RAM, peripherals)

## Languages
C, C++, assembly, Rust (emerging for safety).

## Foundational Texts
- UEFI Specification (UEFI Forum)
- Coreboot documentation
- Vendor BSPs (board support packages)

## Authority Note
Advisory. Vendor specifications and datasheets are authoritative.""",

            "tags": ["firmware", "bootloader", "UEFI", "BIOS", "overview"],
        }
    ],
    "computing_robotics": [
        {
            "title": "Robotics - Field Overview",
            "content": """# Robotics

## Definition
Robotics is the field of designing, building, and operating machines that sense, plan, and act in the physical world.

## Core Areas
- Kinematics and dynamics (forward, inverse)
- Perception (cameras, LIDAR, IMU, encoders)
- Localization and mapping (SLAM)
- Path planning (A*, RRT, D* Lite)
- Control (PID, MPC, adaptive)
- Manipulation (grasping, motion planning)
- Multi-robot systems

## Key Concepts
- DOF: degrees of freedom
- End effector: the tool at the end of a manipulator
- Odometry: estimating position from motion sensors
- SLAM: simultaneous localization and mapping
- TF (transform): coordinate frame transformation
- PID controller: proportional-integral-derivative feedback control
- Jacobian: relates joint velocities to end-effector velocities
- Holonomic vs non-holonomic: motion constraints

## Frameworks
ROS/ROS 2, Gazebo, PyBullet, MoveIt, OpenRAVE.

## Foundational Texts
- Siciliano, Sciavicco, Villani, Oriolo, "Robotics: Modelling, Planning and Control"
- Thrun, Burgard, Fox, "Probabilistic Robotics"
- LaValle, "Planning Algorithms"
- Spong, Hutchinson, Vidyasagar, "Robot Modeling and Control"

## Authority Note
Advisory. Safety-critical robotics must follow ISO 10218 and ISO/TS 15066.""",

            "tags": ["robotics", "ROS", "control", "SLAM", "overview"],
        }
    ],
    "computing_humancomputer_interaction": [
        {
            "title": "Human-computer Interaction - Field Overview",
            "content": """# Human-computer Interaction

## Definition
HCI is the study and design of interfaces between people and computers, focused on usability, accessibility, and experience.

## Core Areas
- User research (interviews, surveys, contextual inquiry)
- Usability evaluation (heuristics, testing, metrics)
- Interaction design (flows, gestures, commands)
- Information architecture
- Visual and interaction design
- Accessibility
- UX measurement (SUS, NPS, task success)

## Key Concepts
- Affordance: a property suggesting how an object should be used
- Mental model: a user's internal understanding of a system
- Feedback: system response to user action
- Visibility: making system state apparent
- Consistency: similar elements behave similarly
- Fitts's law: pointing time depends on distance and target size
- Hick's law: decision time grows with number of choices
- Cognitive load: mental effort required

## Standards
ISO 9241 (ergonomics of human-system interaction)
WCAG 2.1/2.2 (web accessibility)

## Foundational Texts
- Norman, "The Design of Everyday Things"
- Nielsen, "Usability Engineering"
- Krug, "Don't Make Me Think"
- Shneiderman et al., "Designing the User Interface"

## Authority Note
Advisory. WCAG and ISO 9241 are authoritative standards.""",

            "tags": ["HCI", "UX", "usability", "accessibility", "overview"],
        }
    ],
    "computing_accessibility_engineering": [
        {
            "title": "Accessibility Engineering - Field Overview",
            "content": """# Accessibility Engineering

## Definition
Accessibility engineering is the practice of ensuring that digital products can be used by people with the widest range of abilities and circumstances.

## Core Areas
- Visual accessibility (screen readers, contrast, magnification)
- Motor accessibility (keyboard navigation, voice control, large targets)
- Hearing accessibility (captions, transcripts, visual alerts)
- Cognitive accessibility (plain language, consistent layout, predictable behavior)
- Assistive technology compatibility (screen readers, switches, eye tracking)
- Accessibility testing (automated, manual, user testing)

## Key Concepts
- WCAG: Web Content Accessibility Guidelines (A, AA, AAA levels)
- ARIA: Accessible Rich Internet Applications, roles/states/properties
- Semantic HTML: elements that convey meaning to assistive tech
- Focus management: keyboard focus order and visibility
- Alt text: text alternative for images
- Caption: synchronized text for audio
- Screen reader: software that reads UI aloud (NVDA, JAWS, VoiceOver, TalkBack)
- Tab order: the sequence of keyboard focus

## Standards
- WCAG 2.1 / 2.2 (W3C/WAI)
- Section 508 (US federal)
- EN 301 549 (EU)
- ARIA 1.2 (W3C)

## Tools
axe, Lighthouse, WAVE, NVDA, VoiceOver, TalkBack, keyboard-only testing.

## Foundational Texts
- WAI-ARIA Authoring Practices
- Henry, "Accessibility for Everyone"
- Horton & Quesenbery, "A Web for Everyone"

## Authority Note
Advisory. WCAG and ARIA specifications are authoritative.""",

            "tags": ["accessibility", "WCAG", "ARIA", "screen reader", "overview"],
        }
    ],
    "computing_quality_assurance_software_testing": [
        {
            "title": "Quality Assurance and Software Testing - Field Overview",
            "content": """# Quality Assurance and Software Testing

## Definition
QA and testing are practices that verify software meets requirements and is free of defects before release.

## Core Areas
- Test types: unit, integration, system, acceptance, regression, smoke, sanity
- Test design: equivalence partitioning, boundary value, decision table, state transition
- Static analysis (linters, type checkers, security scanners)
- Dynamic analysis (fuzzing, profiling)
- Test automation frameworks
- Performance and load testing
- Mutation testing
- Property-based testing

## Key Concepts
- Test case: input, expected output, and execution condition
- Coverage: percentage of code exercised by tests (line, branch, path)
- Fixture: setup/teardown for tests
- Mock/stub: simulated dependencies
- Flaky test: a test that passes and fails without code changes
- Smoke test: a quick check that the system basically works
- Regression: a previously working feature breaks
- TDD: write test first, then code; red-green-refactor
- BDD: behavior-driven development with Given/When/Then

## Frameworks
pytest, unittest (Python), JUnit (Java), Jest/Vitest (JS), RSpec (Ruby), Go testing, Rust cargo test.

## Standards
ISO/IEC 25010 (software quality model)
ISTQB syllabus

## Foundational Texts
- Beizer, "Software Testing Techniques"
- Kaner, Bach, Pettichord, "Lessons Learned in Software Testing"
- Spolsky, "Joel on Software" (testing essays)

## Authority Note
Advisory.""",

            "tags": ["QA", "testing", "TDD", "coverage", "overview"],
        }
    ],
    "computing_it_support_administration": [
        {
            "title": "IT Support and Administration - Field Overview",
            "content": """# IT Support and Administration

## Definition
IT support and administration is the practice of operating, maintaining, and supporting computer systems and their users.

## Core Areas
- System administration (Linux, Windows, macOS)
- User and access management
- Patch and update management
- Backup and recovery
- Monitoring and alerting
- Help desk and ticketing
- Asset inventory
- Scripting for automation

## Key Concepts
- Account: identity with permissions
- Group/role: a collection of permissions assigned to users
- Privilege escalation: gaining higher access (sudo, runas)
- Patch: a software update fixing bugs or security issues
- Backup: a copy of data for recovery (full, incremental, differential)
- RPO/RTO: recovery point/time objectives
- Ticketing: tracking work items (Jira, ServiceNow, RT)
- Runbook: documented procedure for a recurring task
- Configuration management: Ansible, Puppet, Chef, Salt

## Tools
SSH, Active Directory, LDAP, Ansible, Puppet, Nagios, Zabbix, Grafana, Jira, ServiceNow.

## Foundational Texts
- Limoncelli, Hogan, Chalup, "The Practice of System and Network Administration"
- Nemeth, Snyder, Hein, Whaley, "UNIX and Linux System Administration Handbook"

## Authority Note
Advisory.""",

            "tags": ["IT", "sysadmin", "support", "administration", "overview"],
        }
    ],
    "computing_technology_project_management": [
        {
            "title": "Technology Project Management - Field Overview",
            "content": """# Technology Project Management

## Definition
Technology project management is the practice of planning, executing, and delivering technology projects within scope, time, and budget.

## Core Areas
- Project initiation (charter, stakeholders, goals)
- Planning (WBS, schedule, budget, risk, resources)
- Execution and monitoring
- Risk management
- Stakeholder communication
- Agile vs predictive approaches
- Program and portfolio management

## Key Concepts
- Scope: what the project will and will not deliver
- Triple constraint: scope, time, cost (quality often added)
- WBS: work breakdown structure
- Critical path: the longest sequence of dependent tasks
- Velocity: work completed per iteration (agile)
- Burndown/burnup: remaining work over time
- Risk register: a log of risks with mitigation plans
- RACI: responsible, accountable, consulted, informed

## Methodologies
- PMBOK (PMI)
- PRINCE2
- Agile (Scrum, Kanban, SAFe)
- Lean

## Standards
ISO 21500 (project management)
PMI PMBOK Guide

## Foundational Texts
- PMI, "A Guide to the Project Management Body of Knowledge (PMBOK Guide)"
- Brooks, "The Mythical Man-Month"
- Cohn, "Agile Estimating and Planning"
- Highsmith, "Agile Project Management"

## Authority Note
Advisory.""",

            "tags": ["project management", "PMBOK", "agile", "scrum", "overview"],
        }
    ],
    "computing_quantum_computing": [
        {
            "title": "Quantum Computing - Field Overview",
            "content": """# Quantum Computing

## Definition
Quantum computing is a computing paradigm that uses quantum-mechanical phenomena (superposition, entanglement, interference) to process information.

## Core Areas
- Qubits and quantum states
- Quantum gates and circuits
- Quantum algorithms (Shor, Grover, VQE, QAOA)
- Quantum error correction
- Quantum hardware (superconducting, trapped ion, photonic, topological)
- Quantum supremacy / advantage
- Hybrid quantum-classical algorithms

## Key Concepts
- Qubit: a two-state quantum system (|0>, |1>, superposition)
- Bloch sphere: geometric representation of a single qubit state
- Entanglement: correlated quantum states across qubits
- Hadamard gate: creates superposition
- CNOT gate: creates entanglement
- Measurement: collapses a quantum state to a classical bit
- Decoherence: loss of quantum coherence from environment interaction
- NISQ: noisy intermediate-scale quantum (current era)

## Algorithms
- Shor's: integer factorization (exponential speedup over classical)
- Grover's: unstructured search (quadratic speedup)
- VQE: variational quantum eigensolver (chemistry)
- QAOA: quantum approximate optimization

## Frameworks
Qiskit (IBM), Cirq (Google), PennyLane, Q# (Microsoft).

## Foundational Texts
- Nielsen & Chuang, "Quantum Computation and Quantum Information"
- Preskill lecture notes (Caltech)
- Yanofsky & Mannucci, "Quantum Computing for Computer Scientists"

## Authority Note
Advisory. Quantum advantage claims require careful benchmarking.""",

            "tags": ["quantum", "qubit", "Shor", "Grover", "overview"],
        }
    ],
    "computing_ai_safety_evaluation": [
        {
            "title": "AI Safety and Evaluation - Field Overview",
            "content": """# AI Safety and Evaluation

## Definition
AI safety is the field of ensuring that AI systems behave as intended and do not cause harm. Evaluation is the systematic measurement of AI capabilities, failures, and impacts.

## Core Areas
- Alignment (instructions, preferences, intent)
- Robustness (distribution shift, adversarial inputs)
- Interpretability (mechanistic, behavioral)
- Evaluation (benchmarks, red-teaming, human evaluation)
- Governance (standards, audits, disclosure)
- Failure modes (hallucination, deception, sycophancy, bias)
- Long-term and existential risk

## Key Concepts
- Alignment: the system pursues the intended objective
- Reward hacking: optimizing a proxy metric instead of true goal
- Hallucination: confident false output
- Sycophancy: telling the user what they want to hear
- Distribution shift: performance degradation on new data
- Red teaming: adversarial probing for failures
- Eval: a structured test of capabilities or risks
- Capability elicitation: drawing out latent capabilities
- Sandboxing: isolating a system to limit harm

## Standards (emerging)
- ISO/IEC 42001 (AI management systems)
- NIST AI Risk Management Framework
- EU AI Act

## Foundational Texts
- Russell, "Human Compatible"
- Christian, "The Alignment Problem"
- Amodei et al., "Concrete Problems in AI Safety" (2016)
- Hendrycks et al., "An Overview of Catastrophic AI Risks"

## Authority Note
Advisory. AI safety is an active research field; claims should be cited to peer-reviewed work or reproducible evaluations.""",

            "tags": ["AI safety", "alignment", "evaluation", "robustness", "overview"],
        }
    ],
}
