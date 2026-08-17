"""Docker containerization — break the monolith into microservices.

Containerizes the ANUBIS architecture into isolated microservices:
- Core agent (the main loop)
- Vector database (semantic search)
- Memory service (persistent storage)
- Cloud sync (iDrive E2)
- Daemon (Unix socket API)

Once containerized, scaling becomes a configuration swap. If the local
GPU becomes a bottleneck, the core logic and memory index can move to
the host CPU/RAM, leaving the GPU open for training, or bridge to a
cloud H100 cluster.

This module generates Dockerfile and docker-compose.yml configurations.
It does NOT execute Docker commands — the Creator must review and run
the generated files. All containerization actions are logged to the
evidence ledger.

Generated files:
- Dockerfile.anubis-core
- Dockerfile.anubis-vector
- Dockerfile.anubis-memory
- Dockerfile.anubis-sync
- Dockerfile.anubis-daemon
- docker-compose.yml
- .dockerignore

Each service runs in its own container with isolated resources.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ledger import Ledger


@dataclass
class ServiceConfig:
    """Configuration for a single Docker service."""
    name: str
    build_context: str = "."
    dockerfile: str = ""
    ports: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    restart: str = "unless-stopped"
    memory_limit: str = "2g"
    gpu: bool = False

    def to_compose_dict(self) -> dict[str, Any]:
        """Convert to docker-compose service entry."""
        d: dict[str, Any] = {
            "build": {
                "context": self.build_context,
                "dockerfile": self.dockerfile,
            },
            "restart": self.restart,
            "mem_limit": self.memory_limit,
        }
        if self.ports:
            d["ports"] = self.ports
        if self.volumes:
            d["volumes"] = self.volumes
        if self.environment:
            d["environment"] = self.environment
        if self.depends_on:
            d["depends_on"] = self.depends_on
        if self.gpu:
            d["deploy"] = {
                "resources": {
                    "reservations": {
                        "devices": [{
                            "driver": "nvidia",
                            "count": 1,
                            "capabilities": ["gpu"],
                        }]
                    }
                }
            }
        return d


class DockerConfigGenerator:
    """Generate Docker configuration files for ANUBIS microservices.

    Generates Dockerfiles and docker-compose.yml for running ANUBIS
    as a set of isolated microservices. The Creator must review and
    run the generated files.
    """

    def __init__(
        self,
        output_dir: str | Path = "docker",
        ledger: Ledger | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.ledger = ledger

    def _generate_dockerfile(
        self,
        service_name: str,
        instructions: str,
    ) -> str:
        """Generate a Dockerfile for a service."""
        return f"""# Auto-generated Dockerfile for ANUBIS {service_name}
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}
# Review before building.

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git curl build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (if any)
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# Copy ANUBIS source
COPY anubis/ /app/anubis/
COPY tools/ /app/tools/
COPY config/ /app/config/
COPY knowledge/ /app/knowledge/
COPY memory/ /app/memory/
COPY skills/ /app/skills/
COPY evidence/ /app/evidence/

{instructions}

# Run as non-root user for security
RUN useradd -m anubis
USER anubis

CMD ["python", "-m", "tools.anubis_daemon"]
"""

    def generate_core_dockerfile(self) -> str:
        """Generate Dockerfile for the core agent service."""
        return self._generate_dockerfile(
            "core",
            "# Core agent runs the self-development loop\n"
            "# Requires GPU access for local inference\n"
            "ENV ANUBIS_OLLAMA=http://host.docker.internal:11434",
        )

    def generate_vector_dockerfile(self) -> str:
        """Generate Dockerfile for the vector index service."""
        return self._generate_dockerfile(
            "vector",
            "# Vector index service — no GPU needed\n"
            "# Runs on CPU with system RAM",
        )

    def generate_memory_dockerfile(self) -> str:
        """Generate Dockerfile for the memory service."""
        return self._generate_dockerfile(
            "memory",
            "# Memory service — persistent storage on volume",
        )

    def generate_sync_dockerfile(self) -> str:
        """Generate Dockerfile for the cloud sync service."""
        return self._generate_dockerfile(
            "sync",
            "# Cloud sync service — handles iDrive E2 backups\n"
            "# Runs periodically via cron or systemd timer",
        )

    def generate_daemon_dockerfile(self) -> str:
        """Generate Dockerfile for the daemon service."""
        return self._generate_dockerfile(
            "daemon",
            "# Daemon service — exposes Unix socket API\n"
            "# Expose port for network access (optional)",
        )

    def generate_compose_file(
        self, services: list[ServiceConfig] | None = None
    ) -> str:
        """Generate docker-compose.yml.

        Args:
            services: Custom service configurations. If None, uses defaults.
        """
        if services is None:
            services = self._default_services()

        compose: dict[str, Any] = {
            "version": "3.8",
            "services": {},
        }

        for svc in services:
            compose["services"][svc.name] = svc.to_compose_dict()

        # Add volumes section
        compose["volumes"] = {
            "anubis_memory": {},
            "anubis_knowledge": {},
            "anubis_evidence": {},
        }

        # Add networks section
        compose["networks"] = {
            "anubis_net": {
                "driver": "bridge",
            },
        }

        return (
            "# Auto-generated docker-compose.yml for ANUBIS\n"
            f"# Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            "# Review before running: docker-compose up -d\n\n"
            + json.dumps(compose, indent=2, ensure_ascii=False)
            + "\n"
        )

    def _default_services(self) -> list[ServiceConfig]:
        """Return default service configurations."""
        return [
            ServiceConfig(
                name="anubis-core",
                dockerfile="Dockerfile.anubis-core",
                volumes=[
                    "anubis_memory:/app/memory",
                    "anubis_knowledge:/app/knowledge",
                    "./config:/app/config",
                ],
                environment={
                    "ANUBIS_ACTIVE_DRIVE": "/app",
                    "ANUBIS_OLLAMA": "http://host.docker.internal:11434",
                },
                gpu=True,
                memory_limit="4g",
            ),
            ServiceConfig(
                name="anubis-vector",
                dockerfile="Dockerfile.anubis-vector",
                volumes=[
                    "anubis_memory:/app/memory",
                    "anubis_knowledge:/app/knowledge",
                ],
                depends_on=["anubis-core"],
                memory_limit="2g",
            ),
            ServiceConfig(
                name="anubis-memory",
                dockerfile="Dockerfile.anubis-memory",
                volumes=[
                    "anubis_memory:/app/memory",
                ],
                depends_on=["anubis-core"],
                memory_limit="1g",
            ),
            ServiceConfig(
                name="anubis-sync",
                dockerfile="Dockerfile.anubis-sync",
                volumes=[
                    "anubis_memory:/app/memory",
                    "anubis_knowledge:/app/knowledge",
                    "./config:/app/config",
                ],
                depends_on=["anubis-memory"],
                memory_limit="512m",
            ),
            ServiceConfig(
                name="anubis-daemon",
                dockerfile="Dockerfile.anubis-daemon",
                ports=["8080:8080"],
                volumes=[
                    "anubis_memory:/app/memory",
                    "./config:/app/config",
                ],
                depends_on=["anubis-core", "anubis-vector"],
                memory_limit="1g",
            ),
        ]

    def generate_dockerignore(self) -> str:
        """Generate .dockerignore file."""
        return """# Auto-generated .dockerignore
.git
.github
__pycache__
*.pyc
*.pyo
*.egg-info
.pytest_cache
.coverage
htmlcov
dist
build
.eggs
*.so
.env
.venv
venv
env
node_modules
*.log
*.tmp
*.bak
*.swp
.DS_Store
Thumbs.db
docker/
*.tar.gz
*.zip
backups/
identity/
"""

    def generate_all(self) -> dict[str, Any]:
        """Generate all Docker configuration files.

        Returns:
            Dict with file paths and status
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        files: dict[str, str] = {}

        # Generate Dockerfiles
        files["Dockerfile.anubis-core"] = self.generate_core_dockerfile()
        files["Dockerfile.anubis-vector"] = self.generate_vector_dockerfile()
        files["Dockerfile.anubis-memory"] = self.generate_memory_dockerfile()
        files["Dockerfile.anubis-sync"] = self.generate_sync_dockerfile()
        files["Dockerfile.anubis-daemon"] = self.generate_daemon_dockerfile()

        # Generate compose file
        files["docker-compose.yml"] = self.generate_compose_file()

        # Generate .dockerignore
        files[".dockerignore"] = self.generate_dockerignore()

        # Write all files
        written = []
        for filename, content in files.items():
            path = self.output_dir / filename
            path.write_text(content, encoding="utf-8")
            written.append(str(path))

        if self.ledger:
            self.ledger.append({
                "event": "docker_config_generated",
                "files": written,
                "service_count": 5,
            })

        return {
            "generated": True,
            "files": written,
            "service_count": 5,
            "output_dir": str(self.output_dir),
        }

    def status(self) -> dict[str, Any]:
        """Return Docker configuration status."""
        compose_path = self.output_dir / "docker-compose.yml"
        return {
            "config_exists": compose_path.exists(),
            "output_dir": str(self.output_dir),
            "services": ["core", "vector", "memory", "sync", "daemon"],
            "note": "Run 'docker-compose up -d' to start all services",
        }
