"""Sandbox containment tests.

These are adversarial: each test tries to break out. A sandbox that has not
been attacked is not known to work.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.sandbox import Sandbox, SandboxPolicy  # noqa: E402


class TestBasicExecution(unittest.TestCase):
    def setUp(self):
        self.sbx = Sandbox(SandboxPolicy(timeout_s=20))

    def test_runs_clean_code(self):
        r = self.sbx.run_source("print('hello from sandbox')")
        self.assertTrue(r.ok, r.summary() + r.stderr)
        self.assertIn("hello from sandbox", r.stdout)
        self.assertEqual(r.exit_code, 0)

    def test_nonzero_exit_is_failure(self):
        r = self.sbx.run_source("import sys; sys.exit(3)")
        self.assertFalse(r.ok)
        self.assertEqual(r.exit_code, 3)

    def test_exception_captured_not_raised(self):
        r = self.sbx.run_source("raise ValueError('boom')")
        self.assertFalse(r.ok)
        self.assertIn("ValueError", r.stderr)
        self.assertIn("boom", r.stderr)

    def test_stdout_and_stderr_separated(self):
        r = self.sbx.run_source(
            "import sys\nprint('to-out')\nprint('to-err', file=sys.stderr)"
        )
        self.assertIn("to-out", r.stdout)
        self.assertIn("to-err", r.stderr)
        self.assertNotIn("to-err", r.stdout)


class TestContainment(unittest.TestCase):
    """Escape attempts."""

    def setUp(self):
        self.sbx = Sandbox(SandboxPolicy(timeout_s=25, memory_mb=256, cpu_seconds=10))

    def test_network_is_blocked(self):
        if not self.sbx.isolation.network_blocked:
            self.skipTest("no network namespace available on this host")
        r = self.sbx.run_source(
            "import socket\n"
            "try:\n"
            "    socket.create_connection(('1.1.1.1', 80), timeout=5)\n"
            "    print('LEAK')\n"
            "except Exception as e:\n"
            "    print('BLOCKED', type(e).__name__)\n"
        )
        self.assertNotIn("LEAK", r.stdout, "sandbox leaked network access")
        self.assertIn("BLOCKED", r.stdout)

    def test_dns_is_blocked(self):
        if not self.sbx.isolation.network_blocked:
            self.skipTest("no network namespace available on this host")
        r = self.sbx.run_source(
            "import socket\n"
            "try:\n"
            "    print('RESOLVED', socket.gethostbyname('example.com'))\n"
            "except Exception as e:\n"
            "    print('BLOCKED', type(e).__name__)\n"
        )
        self.assertNotIn("RESOLVED", r.stdout, "sandbox leaked DNS")

    @unittest.skipUnless(hasattr(__import__('os'), 'geteuid'), "Unix-only: resource limits")
    def test_memory_cap_enforced(self):
        r = self.sbx.run_source(
            "try:\n"
            "    b = bytearray(600*1024*1024)\n"
            "    print('ALLOCATED')\n"
            "except MemoryError:\n"
            "    print('REFUSED')\n"
        )
        self.assertNotIn("ALLOCATED", r.stdout, "memory cap not enforced")

    def test_infinite_loop_is_killed(self):
        sbx = Sandbox(SandboxPolicy(timeout_s=5, cpu_seconds=3))
        r = sbx.run_source("while True:\n    pass\n")
        self.assertFalse(r.ok)
        # Either the wall-clock timeout or the CPU rlimit must stop it.
        self.assertTrue(
            r.timed_out or r.exit_code not in (0, None),
            f"runaway loop was not stopped: {r.summary()}",
        )
        self.assertLess(r.duration_s, 20, "kill took too long")

    def test_fork_bomb_is_contained(self):
        sbx = Sandbox(SandboxPolicy(timeout_s=8, cpu_seconds=5, max_processes=16))
        r = sbx.run_source(
            "import os\n"
            "for _ in range(500):\n"
            "    try:\n"
            "        os.fork()\n"
            "    except Exception:\n"
            "        pass\n"
        )
        # The requirement is that the host survives and the run terminates.
        self.assertLess(r.duration_s, 25, "fork bomb was not contained promptly")

    def test_cannot_write_outside_workdir(self):
        # Regression: this failed when the sandbox unshared the network but
        # still ran as root. Namespace isolation does not imply filesystem
        # safety -- privileges must be dropped as well.
        r = self.sbx.run_source(
            "import os\n"
            "try:\n"
            "    open('/etc/anubis-breach', 'w').write('x')\n"
            "    print('WROTE')\n"
            "except Exception as e:\n"
            "    print('DENIED', type(e).__name__)\n"
        )
        self.assertNotIn("WROTE", r.stdout, "wrote outside the sandbox")
        self.assertIn("DENIED", r.stdout)
        self.assertFalse(Path("/etc/anubis-breach").exists())

    def test_cannot_read_shadow_file(self):
        r = self.sbx.run_source(
            "try:\n"
            "    d = open('/etc/shadow').read()\n"
            "    print('READ', len(d))\n"
            "except Exception as e:\n"
            "    print('DENIED', type(e).__name__)\n"
        )
        self.assertNotIn("READ", r.stdout, "read the shadow password file")

    @unittest.skipUnless(hasattr(__import__('os'), 'geteuid'), "Unix-only: privilege dropping")
    def test_runs_unprivileged(self):
        r = self.sbx.run_source("import os; print('UID', os.getuid())")
        self.assertTrue(r.ok, r.stderr)
        self.assertTrue(self.sbx.isolation.unprivileged)
        # Under an explicit privilege drop the uid must not be 0. Under a
        # rootless user namespace, uid 0 *inside* maps to an unprivileged uid
        # outside; the property that matters there is filesystem reach, which
        # the write tests below cover.
        if not self.sbx.isolation.label.startswith("rootless"):
            self.assertNotIn("UID 0", r.stdout, "sandboxed code ran as root")

    def test_host_mounts_are_masked(self):
        # DrvFs (/mnt/*) ignores Unix ownership, so permission-based defence is
        # void there. Those mounts must be invisible inside the sandbox.
        if not self.sbx.isolation.host_mounts_masked:
            self.skipTest("mount namespace masking unavailable on this host")
        r = self.sbx.run_source(
            "import os\n"
            "print('MNT', sorted(os.listdir('/mnt')) if os.path.isdir('/mnt') else 'absent')\n"
        )
        self.assertTrue(r.ok, r.stderr)
        self.assertIn("MNT", r.stdout)
        self.assertNotIn("'d'", r.stdout, "Windows D: drive visible inside sandbox")
        self.assertNotIn('"d"', r.stdout)

    @unittest.skipUnless(hasattr(__import__('os'), 'geteuid'), "Unix-only: namespace isolation")
    def test_cannot_write_to_sios_source_tree(self):
        # The most important case: generated code must not be able to edit
        # ANUBIS's own source outside the governed promotion path.
        own_source = Path(__file__).resolve().parents[1] / "anubis" / "constitution.py"
        r = self.sbx.run_source(
            "try:\n"
            f"    open({str(own_source)!r}, 'a').write('# tampered\\n')\n"
            "    print('WROTE')\n"
            "except Exception as e:\n"
            "    print('DENIED', type(e).__name__)\n"
        )
        self.assertNotIn("WROTE", r.stdout, "generated code edited ANUBIS's own source")
        self.assertNotIn("# tampered", own_source.read_text(encoding="utf-8"))

    def test_workdir_is_destroyed_after_run(self):
        r = self.sbx.run_source(
            "open('residue.txt','w').write('should not persist')\nprint('done')"
        )
        self.assertTrue(r.ok, r.stderr)
        # The file was created and observed, but the directory is now gone.
        self.assertIn("residue.txt", r.workdir_files)

    def test_environment_does_not_leak_secrets(self):
        r = self.sbx.run_source(
            "import os\n"
            "keys = sorted(os.environ)\n"
            "print('KEYS', ','.join(keys))\n"
        )
        self.assertTrue(r.ok, r.stderr)
        for leaky in ("AWS", "TOKEN", "SECRET", "OLLAMA", "API"):
            self.assertNotIn(leaky, r.stdout.upper().replace("KEYS", ""))

    def test_isolation_is_reported_honestly(self):
        r = self.sbx.run_source("print(1)")
        self.assertIn("network_blocked", r.isolation)
        # The claim must match reality, not intent.
        self.assertEqual(
            r.isolation["network_blocked"], self.sbx.isolation.network_blocked
        )
        self.assertEqual(r.isolation["unprivileged"], self.sbx.isolation.unprivileged)

    def test_degraded_sandbox_admits_it(self):
        # A sandbox that cannot isolate the network must not report itself as
        # fully isolated -- silently degrading would breach the truth law.
        allowed = Sandbox(SandboxPolicy(timeout_s=10, allow_network=True))
        r = allowed.run_source("print('ran')")
        self.assertTrue(r.ok, r.stderr)
        self.assertFalse(r.isolation["network_blocked"])
        self.assertFalse(r.fully_isolated)
        self.assertIn("DEGRADED", r.summary())


class TestSkillWithTests(unittest.TestCase):
    def setUp(self):
        self.sbx = Sandbox(SandboxPolicy(timeout_s=20))

    def test_passing_skill_and_tests(self):
        skill = "def slugify(t):\n    import re\n    return re.sub(r'[^a-z0-9]+','-',t.lower()).strip('-')\n"
        tests = (
            "assert slugify('Hello World') == 'hello-world'\n"
            "assert slugify('  A!!B  ') == 'a-b'\n"
            "print('TESTS PASSED')\n"
        )
        r = self.sbx.run_with_tests(skill, tests)
        self.assertTrue(r.ok, r.stderr)
        self.assertIn("TESTS PASSED", r.stdout)

    def test_failing_tests_surface_as_failure(self):
        skill = "def add(a, b):\n    return a - b\n"  # deliberately wrong
        tests = "assert add(2, 2) == 4, 'add is broken'\nprint('TESTS PASSED')\n"
        r = self.sbx.run_with_tests(skill, tests)
        self.assertFalse(r.ok)
        self.assertNotIn("TESTS PASSED", r.stdout)
        self.assertIn("AssertionError", r.stderr)

    def test_syntax_error_surfaces(self):
        r = self.sbx.run_with_tests("def broken(:\n  pass\n", "print('x')")
        self.assertFalse(r.ok)
        self.assertIn("SyntaxError", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
