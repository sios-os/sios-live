#!/bin/bash
# Linux deployment test script — run inside WSL2
set -e
cd /mnt/d/SIOS-Build/sios-live

echo "=== Python Version ==="
python3 --version

echo ""
echo "=== Core Module Imports ==="
python3 -c "
import anubis.constitution
import anubis.governance
import anubis.sandbox
import anubis.local_inference
import anubis.identity
import anubis.ledger
import anubis.prospects
import anubis.knowledge_acquisition
import anubis.funding_executor
import anubis.dream_cycle
import anubis.voice_interpreter
import anubis.email_system
import anubis.phone_adapter
import anubis.operations
import anubis.research_engine
import anubis.self_modify
import anubis.mixed_model
import anubis.advanced
import anubis.orchestrator
import anubis.distillation
import anubis.custom_embeddings
import anubis.semantic
print('All core modules imported successfully')
"

echo ""
echo "=== Daemon Import ==="
python3 -c "
import sys
sys.path.insert(0, 'tools')
from anubis_daemon import AnubisDaemon
print('Daemon class imported successfully')
"

echo ""
echo "=== Unix-specific Features ==="
python3 -c "
import os, resource, signal, socket
print(f'geteuid: {os.geteuid()}')
print(f'AF_UNIX available: {hasattr(socket, \"AF_UNIX\")}')
print(f'resource.RLIMIT_AS: {resource.RLIMIT_AS}')
print(f'SIGTERM: {signal.SIGTERM}')
print('Unix features OK')
"

echo ""
echo "=== Deployment Checker ==="
python3 tools/linux_deploy_check.py

echo ""
echo "=== Quick Test Run (sandbox + knowledge) ==="
python3 -m unittest tests.test_sandbox -v 2>&1 | tail -20

echo ""
echo "=== Linux Deployment Test Complete ==="
