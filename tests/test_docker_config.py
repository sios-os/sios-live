"""Tests for the Docker configuration generator.

Tests verify:
- Dockerfile generation for each service
- docker-compose.yml generation
- .dockerignore generation
- Service configuration (ports, volumes, GPU, dependencies)
- Full generation (all files)
- Status endpoint
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.docker_config import (
    DockerConfigGenerator,
    ServiceConfig,
)


class TestServiceConfig(unittest.TestCase):
    """Tests for ServiceConfig."""

    def test_basic_config(self):
        svc = ServiceConfig(name="test", dockerfile="Dockerfile.test")
        d = svc.to_compose_dict()
        self.assertEqual(d["restart"], "unless-stopped")
        self.assertIn("build", d)

    def test_with_ports(self):
        svc = ServiceConfig(name="test", dockerfile="Dockerfile.test", ports=["8080:8080"])
        d = svc.to_compose_dict()
        self.assertEqual(d["ports"], ["8080:8080"])

    def test_with_volumes(self):
        svc = ServiceConfig(
            name="test", dockerfile="Dockerfile.test",
            volumes=["data:/app/data"],
        )
        d = svc.to_compose_dict()
        self.assertEqual(d["volumes"], ["data:/app/data"])

    def test_with_gpu(self):
        svc = ServiceConfig(name="test", dockerfile="Dockerfile.test", gpu=True)
        d = svc.to_compose_dict()
        self.assertIn("deploy", d)
        self.assertIn("resources", d["deploy"])

    def test_with_depends_on(self):
        svc = ServiceConfig(
            name="test", dockerfile="Dockerfile.test",
            depends_on=["core"],
        )
        d = svc.to_compose_dict()
        self.assertEqual(d["depends_on"], ["core"])

    def test_no_ports_when_empty(self):
        svc = ServiceConfig(name="test", dockerfile="Dockerfile.test")
        d = svc.to_compose_dict()
        self.assertNotIn("ports", d)


class TestDockerfileGeneration(unittest.TestCase):
    """Tests for Dockerfile generation."""

    def setUp(self):
        self.gen = DockerConfigGenerator()

    def test_core_dockerfile(self):
        df = self.gen.generate_core_dockerfile()
        self.assertIn("FROM python:3.12-slim", df)
        self.assertIn("anubis", df.lower())
        self.assertIn("ANUBIS_OLLAMA", df)

    def test_vector_dockerfile(self):
        df = self.gen.generate_vector_dockerfile()
        self.assertIn("FROM python:3.12-slim", df)
        self.assertIn("vector", df.lower())

    def test_memory_dockerfile(self):
        df = self.gen.generate_memory_dockerfile()
        self.assertIn("FROM python:3.12-slim", df)

    def test_sync_dockerfile(self):
        df = self.gen.generate_sync_dockerfile()
        self.assertIn("FROM python:3.12-slim", df)

    def test_daemon_dockerfile(self):
        df = self.gen.generate_daemon_dockerfile()
        self.assertIn("FROM python:3.12-slim", df)

    def test_all_dockerfiles_have_non_root_user(self):
        for method_name in [
            "generate_core_dockerfile",
            "generate_vector_dockerfile",
            "generate_memory_dockerfile",
            "generate_sync_dockerfile",
            "generate_daemon_dockerfile",
        ]:
            df = getattr(self.gen, method_name)()
            self.assertIn("USER anubis", df, f"{method_name} missing non-root user")

    def test_all_dockerfiles_copy_source(self):
        df = self.gen.generate_core_dockerfile()
        self.assertIn("COPY anubis/", df)


class TestComposeFile(unittest.TestCase):
    """Tests for docker-compose.yml generation."""

    def setUp(self):
        self.gen = DockerConfigGenerator()

    def test_compose_has_version(self):
        compose = self.gen.generate_compose_file()
        self.assertIn("version", compose)
        self.assertIn("3.8", compose)

    def test_compose_has_services(self):
        compose = self.gen.generate_compose_file()
        self.assertIn("services", compose)

    def test_compose_has_volumes(self):
        compose = self.gen.generate_compose_file()
        self.assertIn("volumes", compose)
        self.assertIn("anubis_memory", compose)

    def test_compose_has_networks(self):
        compose = self.gen.generate_compose_file()
        self.assertIn("networks", compose)

    def test_compose_with_custom_services(self):
        custom = [ServiceConfig(name="custom", dockerfile="Dockerfile.custom")]
        compose = self.gen.generate_compose_file(services=custom)
        self.assertIn("custom", compose)

    def test_compose_is_valid_json(self):
        compose = self.gen.generate_compose_file()
        # Strip comment lines
        lines = [l for l in compose.splitlines() if not l.startswith("#")]
        data = json.loads("\n".join(lines))
        self.assertIn("services", data)


class TestDockerignore(unittest.TestCase):
    """Tests for .dockerignore generation."""

    def setUp(self):
        self.gen = DockerConfigGenerator()

    def test_dockerignore_excludes_git(self):
        content = self.gen.generate_dockerignore()
        self.assertIn(".git", content)

    def test_dockerignore_excludes_pycache(self):
        content = self.gen.generate_dockerignore()
        self.assertIn("__pycache__", content)

    def test_dockerignore_excludes_identity(self):
        content = self.gen.generate_dockerignore()
        self.assertIn("identity/", content)


class TestGenerateAll(unittest.TestCase):
    """Tests for generating all Docker files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-docker-")
        self.gen = DockerConfigGenerator(output_dir=self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_all_creates_files(self):
        result = self.gen.generate_all()
        self.assertTrue(result["generated"])
        self.assertEqual(result["service_count"], 5)
        # Check files exist
        for f in result["files"]:
            self.assertTrue(Path(f).exists(), f"{f} not found")

    def test_generate_all_creates_dockerfiles(self):
        self.gen.generate_all()
        self.assertTrue((Path(self.tmpdir) / "Dockerfile.anubis-core").exists())
        self.assertTrue((Path(self.tmpdir) / "Dockerfile.anubis-vector").exists())

    def test_generate_all_creates_compose(self):
        self.gen.generate_all()
        self.assertTrue((Path(self.tmpdir) / "docker-compose.yml").exists())

    def test_generate_all_creates_dockerignore(self):
        self.gen.generate_all()
        self.assertTrue((Path(self.tmpdir) / ".dockerignore").exists())


class TestStatus(unittest.TestCase):
    """Tests for the status endpoint."""

    def test_status_before_generation(self):
        tmpdir = tempfile.mkdtemp(prefix="anubis-docker-st-")
        try:
            gen = DockerConfigGenerator(output_dir=tmpdir)
            status = gen.status()
            self.assertFalse(status["config_exists"])
            self.assertIn("services", status)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_status_after_generation(self):
        tmpdir = tempfile.mkdtemp(prefix="anubis-docker-st2-")
        try:
            gen = DockerConfigGenerator(output_dir=tmpdir)
            gen.generate_all()
            status = gen.status()
            self.assertTrue(status["config_exists"])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
