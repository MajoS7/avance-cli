from __future__ import annotations

from pathlib import Path

import yaml

from .models import AppConfig, RepositoryConfig


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ValueError(f"No existe el archivo de configuración: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    organization = str(data.get("organization", "")).strip()
    raw_repositories = data.get("repositories") or []

    if not organization:
        raise ValueError("Falta 'organization' en la configuración")
    if not raw_repositories:
        raise ValueError("Configura al menos un repositorio")

    repositories: list[RepositoryConfig] = []
    for index, item in enumerate(raw_repositories, start=1):
        if not isinstance(item, dict) or not item.get("project") or not item.get("repository"):
            raise ValueError(f"Repositorio #{index}: se requieren 'project' y 'repository'")
        repositories.append(
            RepositoryConfig(project=str(item["project"]), repository=str(item["repository"]))
        )

    email = data.get("email") or {}
    return AppConfig(
        organization=organization,
        repositories=repositories,
        task_pattern=str(data.get("task_pattern", r"(?i)(task\d+)")),
        greeting=str(email.get("greeting", "Buen día")),
        environment_aliases={str(k): str(v) for k, v in (data.get("environment_aliases") or {}).items()},
    )

