from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RepositoryConfig:
    project: str
    repository: str


@dataclass(frozen=True)
class AppConfig:
    organization: str
    repositories: list[RepositoryConfig]
    task_pattern: str = r"(?i)(task\d+)"
    greeting: str = "Buen día"
    environment_aliases: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PullRequest:
    id: int
    title: str
    project: str
    repository: str
    source_branch: str
    target_branch: str
    status: str
    url: str
    merge_commit: str | None = None
    closed_date: datetime | None = None
    files: list[str] = field(default_factory=list)

