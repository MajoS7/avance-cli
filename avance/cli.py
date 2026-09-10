from __future__ import annotations

import os
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pyperclip
import typer
from rich.console import Console
from rich.table import Table

from .azure_devops import AzureDevOpsClient
from .config import load_config
from .email_builder import render_email
from .models import PullRequest

app = typer.Typer(no_args_is_help=False, help="Genera correos desde PRs de Azure DevOps")
console = Console()


@app.command()
def main(
    config: Path = typer.Option(Path("avance.yml"), "--config", "-c", help="Archivo YAML"),
    desde: str = typer.Option("1d", "--desde", help="Periodo: 12h, 1d, 7d o YYYY-MM-DD"),
    copiar: bool = typer.Option(True, "--copiar/--no-copiar", help="Copiar si hay un solo correo"),
    salida: Path | None = typer.Option(None, "--salida", "-o", help="Directorio para guardar correos"),
) -> None:
    """Consulta tus PRs completados y genera los correos de integración."""
    try:
        settings = load_config(config)
        since = parse_since(desde)
        pat = (
            os.getenv("AZURE_DEVOPS_PAT")
            or os.getenv("AZDO_PAT")
            or ""
        ).strip()
        if not pat:
            raise ValueError("Define la variable de entorno AZURE_DEVOPS_PAT")

        completed: list[PullRequest] = []
        pending: list[PullRequest] = []
        with AzureDevOpsClient(settings.organization, pat) as client:
            user_id = client.authenticated_user_id()
            for repo in settings.repositories:
                completed.extend(client.list_pull_requests(repo, user_id, "completed", since))
                pending.extend(client.list_pull_requests(repo, user_id, "active"))
            completed = [replace(pr, files=client.changed_files(pr)) for pr in completed]

        completed.sort(key=lambda pr: pr.closed_date or datetime.min.replace(tzinfo=timezone.utc))
        emails = [render_email(pr, settings) for pr in completed]
        _show_results(emails, pending, salida)

        if copiar and len(emails) == 1:
            subject, body = emails[0]
            try:
                pyperclip.copy(f"Asunto: {subject}\n\n{body}")
                console.print("[green]Correo copiado al portapapeles.[/green]")
            except pyperclip.PyperclipException:
                console.print("[yellow]No se encontró un portapapeles compatible; el correo se imprimió arriba.[/yellow]")
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc


def parse_since(value: str, now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    relative = re.fullmatch(r"(\d+)([hd])", value.strip().lower())
    if relative:
        amount = int(relative.group(1))
        delta = timedelta(hours=amount) if relative.group(2) == "h" else timedelta(days=amount)
        return now - delta
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("--desde debe ser como 12h, 1d, 7d o YYYY-MM-DD") from exc
    return parsed.replace(tzinfo=timezone.utc)


def _show_results(
    emails: list[tuple[str, str]], pending: list[PullRequest], output_dir: Path | None
) -> None:
    if emails:
        for index, (subject, body) in enumerate(emails, start=1):
            console.rule(subject)
            console.print(body, markup=False)
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                safe_name = re.sub(r"[^\w.-]+", "-", subject, flags=re.UNICODE).strip("-")
                path = output_dir / f"{index:02d}-{safe_name}.txt"
                path.write_text(f"Asunto: {subject}\n\n{body}", encoding="utf-8")
                console.print(f"Guardado: {path}")
    else:
        console.print("[yellow]No encontré PRs completados en el periodo indicado.[/yellow]")

    if pending:
        table = Table(title="Pull Requests pendientes")
        table.add_column("PR")
        table.add_column("Repositorio")
        table.add_column("Rama")
        table.add_column("Título")
        for pr in pending:
            table.add_row(str(pr.id), pr.repository, pr.source_branch, pr.title)
        console.print(table)
    else:
        console.print("No tienes Pull Requests pendientes en los repositorios configurados.")


if __name__ == "__main__":
    app()

