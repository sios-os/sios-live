# ANUBIS Daemon API Reference

## Connection

The daemon listens on a Unix domain socket at `/tmp/anubis.sock`.

### Python Client
```python
import json, socket

def call(cmd, **kwargs):
    req = {"cmd": cmd}
    req.update(kwargs)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect("/tmp/anubis.sock")
    s.send(json.dumps(req).encode())
    s.settimeout(120)
    data = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
    s.close()
    return json.loads(data)
```

### GDScript Client (Godot)
The IPCBridge autoload handles this automatically. See `desktop/scripts/IPCBridge.gd`.

## Commands

### System

#### `status`
Returns daemon health, model availability, sandbox state, skill count, ledger entries.

**Response:**
```json
{
  "daemon": "running",
  "model": "qwen2.5-coder:7b",
  "model_present": true,
  "sandbox": "Sandbox(timeout=30.0s mem=512MB ...)",
  "skills_count": 111,
  "ledger_entries": 393,
  "pid": 12345
}
```

#### `constitution`
Returns the 8 immutable laws and constitutional framework.

#### `genesis`
Returns ANUBIS's first moments (genesis record).

---

### Chat (DEMON)

#### `chat`
Talk to ANUBIS through the DEMON interface.

**Request:**
```json
{"cmd": "chat", "message": "Who are you?"}
```

**Response:**
```json
{
  "response": "I am ANUBIS...",
  "model": "qwen2.5-coder:7b",
  "tokens": 54,
  "duration_s": 15.4,
  "knowledge_citations": ["Document Title 1", "Document Title 2"],
  "claims_used": 10,
  "knowledge_grounded": true
}
```

#### `reset_chat`
Clear conversation history.

#### `tts`
Text-to-speech.

**Request:** `{"cmd": "tts", "text": "Hello"}`

#### `stt`
Speech-to-text.

**Request:** `{"cmd": "stt", "timeout": 5.0}`

---

### Skills

#### `skills`
List all promoted skills.

**Response:**
```json
{
  "skills": [
    {"name": "reverse_string", "version": 1, "description": "..."},
    ...
  ],
  "count": 111
}
```

#### `skill_versions`
Get version history for a skill.

**Request:** `{"cmd": "skill_versions", "name": "reverse_string"}`

---

### Missions

#### `mission`
Start a self-development mission.

**Request:**
```json
{
  "cmd": "mission",
  "task": "Write a function that reverses a string",
  "skill_name": "reverse_string",
  "approval_token": "..."
}
```

#### `poll`
Check mission status.

**Request:** `{"cmd": "poll", "mission_id": "abc123"}`

#### `mission_history`
Get mission archive.

---

### Mission Queue

#### `queue_stats`
**Response:**
```json
{
  "total": 5,
  "by_status": {"completed": 5, "pending": 0},
  "pending": 0,
  "completed": 5,
  "failed": 0
}
```

#### `queue_add`
**Request:** `{"cmd": "queue_add", "skill_name": "my_func", "task": "..."}`

#### `queue_add_batch`
**Request:** `{"cmd": "queue_add_batch", "missions": [["name", "task"], ...]}`

#### `queue_process`
Process N pending missions autonomously.

**Request:** `{"cmd": "queue_process", "limit": 5}`

**Response:**
```json
{
  "results": [
    {"skill": "my_func", "status": "promoted", "version": 1},
    {"skill": "other_func", "status": "failed", "error": "..."}
  ],
  "processed": 2
}
```

#### `queue_list`
List all missions in the queue.

---

### Projects

#### `list_projects`
List all projects.

#### `get_project`
**Request:** `{"cmd": "get_project", "name": "string_toolkit"}`

#### `plan_project`
**Request:** `{"cmd": "plan_project", "name": "...", "description": "...", "approval_token": "..."}`

#### `run_project`
**Request:** `{"cmd": "run_project", "name": "...", "approval_token": "..."}`

#### `poll_project`
**Request:** `{"cmd": "poll_project", "project_id": "..."}`

---

### Knowledge

#### `knowledge_stats`
**Response:**
```json
{
  "library_size": 804,
  "total_claims": 15677,
  "verified_docs": 804
}
```

#### `knowledge_search`
**Request:** `{"cmd": "knowledge_search", "query": "ancient egypt", "limit": 10}`

#### `knowledge_ground`
Ground a query in knowledge (returns context + citations).

**Request:** `{"cmd": "knowledge_ground", "query": "object-oriented programming"}`

#### `knowledge_ingest`
Ingest a document to quarantine.

**Request:** `{"cmd": "knowledge_ingest", "title": "...", "content": "...", "specialty_id": "..."}`

#### `knowledge_promote`
Promote a document from quarantine.

**Request:** `{"cmd": "knowledge_promote", "doc_id": "..."}`

#### `claim_search`
Search claims by keyword.

**Request:** `{"cmd": "claim_search", "query": "python", "limit": 20}`

#### `grounding_stats`
Get grounding system statistics (semantic search status, index size).

---

### Knowledge Updater

#### `knowledge_propose`
Propose a new knowledge document through the updater pipeline.

**Request:**
```json
{
  "cmd": "knowledge_propose",
  "specialty_id": "computing_software_engineering",
  "title": "Python Programming",
  "content": "# Python\n- Python is a high-level language\n..."
}
```

**Response:**
```json
{
  "proposal_id": "abc123",
  "status": "verified",
  "claims_extracted": 9,
  "claims_verified": 9
}
```

#### `knowledge_approve`
**Request:** `{"cmd": "knowledge_approve", "proposal_id": "abc123"}`

#### `knowledge_promote_proposal`
**Request:** `{"cmd": "knowledge_promote_proposal", "proposal_id": "abc123"}`

#### `knowledge_updater_stats`
**Response:**
```json
{
  "total_proposals": 5,
  "verified": 3,
  "approved": 2,
  "promoted": 2,
  "rejected": 0
}
```

---

### Orchestrator

#### `orchestrate`
Multi-agent cross-director query.

**Request:** `{"cmd": "orchestrate", "query": "How do I build a secure web app?", "max_directors": 3}`

**Response:**
```json
{
  "directors_consulted": 2,
  "contributions": [
    {
      "director_name": "Computing",
      "perspective": "From the Computing perspective: ...",
      "citations": ["Web Development - Field Overview", ...]
    }
  ]
}
```

---

### Governance

#### `identity_stats`
**Response:**
```json
{
  "enrolled": true,
  "creator_name": "Storm",
  "successors": 1,
  "consented_successors": 1,
  "vault_unlocked": false
}
```

#### `enroll_creator`
Enroll the Creator identity.

#### `court_stats`
**Response:**
```json
{
  "total_reviews": 1,
  "pending": 0,
  "promoted": 0,
  "probation": 1,
  "denied": 0
}
```

#### `court_submit`
Submit an artifact for Court review.

#### `policy_stats`
Returns spending limits, prohibited categories, mandates.

#### `capability_stats`
Returns active, granted, and revoked capabilities.

---

### Backup

#### `backup_create`
**Request:** `{"cmd": "backup_create", "label": "manual"}`

**Response:**
```json
{
  "backup_name": "sios_backup_20260813_162807_full_system",
  "size_mb": 4.7,
  "sha256": "b336e98f..."
}
```

#### `backup_list`
**Response:**
```json
{
  "backups": [
    {"name": "sios_backup_...", "size_mb": 4.7, "label": "full_system"}
  ]
}
```

#### `backup_restore`
**Request:** `{"cmd": "backup_restore", "backup_name": "sios_backup_..."}`

---

### Voice

#### `voice_status`
**Response:**
```json
{
  "voice_out_enabled": false,
  "voice_out_available": true,
  "voice_in_enabled": false,
  "voice_in_available": false
}
```

#### `voice_toggle_out`
Enable/disable text-to-speech.

#### `voice_toggle_in`
Enable/disable speech-to-text.

#### `voice_speak`
**Request:** `{"cmd": "voice_speak", "text": "Hello, I am ANUBIS"}`

---

### Documentation

#### `docs_generate`
Generate all documentation files.

**Response:**
```json
{
  "generated": ["docs/skills.md", "docs/system.md", "docs/knowledge.md"]
}
```

---

### Filesystem (Creator-only)

#### `fs_list`
**Request:** `{"cmd": "fs_list", "path": "/opt/sios-live"}`

#### `fs_read`
**Request:** `{"cmd": "fs_read", "path": "/opt/sios-live/anubis/skills.py"}`

#### `fs_write`
**Request:** `{"cmd": "fs_write", "path": "...", "content": "...", "approval_token": "..."}`

#### `run_cmd`
**Request:** `{"cmd": "run_cmd", "command": "ls -la", "approval_token": "..."}`

---

### Ledger

#### `ledger`
Get ledger summary (entry count, integrity, head hash).

#### `ledger_entries`
Browse ledger entries.

**Request:** `{"cmd": "ledger_entries", "limit": 20, "offset": 0, "action": "mission.start"}`

---

### Other

#### `registry_stats`
#### `list_directors`
#### `list_specialties`
#### `network_stats`
#### `hardening_stats`
#### `recovery_stats`
#### `ab_stats`
#### `egyptology_lookup`
#### `egyptology_stats`
#### `purge_now`
#### `package_stats`
#### `financial_stats`

## Error Handling

All commands return a dictionary. On error:
```json
{"error": "description of the error"}
```

## Approval Tokens

Consequential actions (missions, file writes, command execution) require an approval token. The desktop UI obtains this from the Creator through authentication.
