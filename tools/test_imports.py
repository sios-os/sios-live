#!/usr/bin/env python3
"""Quick import test."""
import sys
sys.path.insert(0, ".")
try:
    from anubis.registry import Registry
    from anubis.knowledge import KnowledgeBase
    from anubis.identity import IdentityService
    from anubis.governance import PolicyEngine, CapabilityBroker, Court
    from anubis.operations import MidnightPurge, PackageManager, FinancialLedger
    from anubis.system import NetworkManager, SystemHardening, RecoveryManager, ArtifactSigner
    from anubis.system2 import ABImageManager, EgyptologySupport
    print("All imports OK")
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
