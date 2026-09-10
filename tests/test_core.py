from datetime import datetime, timezone

from avance.azure_devops import _strip_ref
from avance.cli import parse_since
from avance.email_builder import extract_task, render_email
from avance.models import AppConfig, PullRequest, RepositoryConfig


def sample_pr() -> PullRequest:
    return PullRequest(
        id=17142,
        title="Integración task20615",
        project="Nomina",
        repository="Utilidades",
        source_branch="feature/task20615",
        target_branch="planeada",
        status="completed",
        url="https://dev.azure.com/org/Nomina/_git/Utilidades/pullrequest/17142",
        merge_commit="0dad93643c0da42085a7b253241bf90c1c5c3483",
        files=["/UtilidadesNomina/src/Consultas.java"],
    )


def test_extract_task_from_branch() -> None:
    assert extract_task(sample_pr(), r"(?i)(task\d+)") == "task20615"


def test_render_email() -> None:
    config = AppConfig("org", [RepositoryConfig("Nomina", "Utilidades")])
    subject, body = render_email(sample_pr(), config)
    assert subject == "Integración task20615"
    assert "feature/task20615" in body
    assert "/UtilidadesNomina/src/Consultas.java" in body
    assert "0dad93643c0da42085a7b253241bf90c1c5c3483" in body
    assert "Pull Request 17142" in body


def test_parse_relative_since() -> None:
    now = datetime(2026, 9, 2, 12, tzinfo=timezone.utc)
    assert parse_since("1d", now) == datetime(2026, 9, 1, 12, tzinfo=timezone.utc)


def test_strip_ref() -> None:
    assert _strip_ref("refs/heads/feature/task20615") == "feature/task20615"

