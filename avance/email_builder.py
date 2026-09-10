from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .models import AppConfig, PullRequest


TEMPLATE_DIR = Path(__file__).parent / "templates"


def extract_task(pr: PullRequest, pattern: str) -> str:
    for text in (pr.source_branch, pr.title):
        match = re.search(pattern, text)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    return f"PR{pr.id}"


def render_email(pr: PullRequest, config: AppConfig) -> tuple[str, str]:
    task = extract_task(pr, config.task_pattern)
    environment = config.environment_aliases.get(pr.target_branch, pr.target_branch)
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    body = env.get_template("correo.txt.j2").render(
        greeting=config.greeting,
        task=task,
        environment=environment,
        branch=pr.source_branch,
        files=pr.files,
        merge_commit=pr.merge_commit or "No disponible",
        pr_id=pr.id,
        pr_url=pr.url,
    )
    return f"Integración {task}", body.strip() + "\n"

