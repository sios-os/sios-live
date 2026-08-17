#!/usr/bin/env python3
"""Talk to ANUBIS through the daemon socket."""
import json
import socket
import sys

SOCKET_PATH = "/tmp/anubis.sock"

def call(cmd, **kwargs):
    req = {"cmd": cmd}
    req.update(kwargs)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET_PATH)
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

print("=== TALKING TO ANUBIS THROUGH DEMON ===")
print()

# 1. Status
print("--- Status ---")
status = call("status")
print(f"  Daemon: {status.get('daemon')}")
print(f"  Model: {status.get('model')}")
print(f"  Model present: {status.get('model_present')}")
print(f"  Skills: {status.get('skills_count')}")
print(f"  Ledger: {status.get('ledger_entries')}")
print()

# 2. Knowledge stats
print("--- Knowledge Stats ---")
ks = call("knowledge_stats")
print(f"  Library size: {ks.get('library_size')}")
print(f"  Total claims: {ks.get('total_claims')}")
print(f"  Verified docs: {ks.get('verified_docs')}")
print()

# 3. Grounding stats (should show semantic enabled)
print("--- Grounding Stats ---")
gs = call("grounding_stats")
print(f"  Semantic enabled: {gs.get('semantic_enabled')}")
print(f"  Claims indexed: {gs.get('claims_indexed')}")
if 'semantic_stats' in gs:
    ss = gs['semantic_stats']
    print(f"  Embedded docs: {ss.get('indexed_docs')}")
    print(f"  Embedding dim: {ss.get('embedding_dim')}")
print()

# 4. Identity stats
print("--- Identity Stats ---")
ident = call("identity_stats")
print(f"  Enrolled: {ident.get('enrolled')}")
print(f"  Creator: {ident.get('creator_name')}")
print(f"  Successors: {ident.get('successors')}")
print(f"  Consented: {ident.get('consented_successors')}")
print()

# 5. Queue stats
print("--- Mission Queue Stats ---")
qs = call("queue_stats")
print(f"  Total: {qs.get('total')}")
print(f"  By status: {qs.get('by_status')}")
print()

# 6. Chat with ANUBIS
print("--- Chat: 'Who are you?' ---")
chat = call("chat", message="Who are you?")
print(f"  ANUBIS: {chat.get('response', '')[:300]}")
if chat.get('citations'):
    print(f"  Citations: {chat['citations']}")
print()

# 7. Chat about knowledge
print("--- Chat: 'What is object-oriented programming?' ---")
chat2 = call("chat", message="What is object-oriented programming?")
print(f"  ANUBIS: {chat2.get('response', '')[:400]}")
if chat2.get('citations'):
    print(f"  Citations: {chat2['citations']}")
print()

# 8. Orchestrate a cross-disciplinary query
print("--- Orchestrate: 'How do I build a secure web app?' ---")
orch = call("orchestrate", query="How do I build a secure web application with a database?")
print(f"  Directors consulted: {orch.get('directors_consulted')}")
for c in orch.get('contributions', []):
    print(f"    - {c.get('director_name')}: {c.get('perspective', '')[:100]}...")
print()

# 9. Voice status
print("--- Voice Status ---")
vs = call("voice_status")
print(f"  Voice out: enabled={vs.get('voice_out_enabled')}, available={vs.get('voice_out_available')}")
print(f"  Voice in: enabled={vs.get('voice_in_enabled')}, available={vs.get('voice_in_available')}")
print()

# 10. Backup list
print("--- Backups ---")
bl = call("backup_list")
for b in bl.get("backups", []):
    print(f"  {b.get('name')}: {b.get('size_mb')} MB, label='{b.get('label')}'")
print()

print("=== DEMON CONVERSATION COMPLETE ===")
