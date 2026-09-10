# Avance Azure DevOps

CLI en Python que consulta tus Pull Requests en varios repositorios de Azure DevOps,
genera el correo de integración para los PR completados y muestra los PR activos como
pendientes.

## Requisitos

- Python 3.11 o superior.
- Un PAT de Azure DevOps con permiso **Code: Read** (`vso.code`).
- Acceso a los proyectos y repositorios configurados.

## Instalación

```bash
cd avance-cli
python -m venv .venv
```

En Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

En macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -e .
```

## Configuración

1. Copia `config.example.yml` como `avance.yml`.
2. Cambia `organization`, `project` y `repository` por los nombres de Azure DevOps.
3. Define el PAT sin escribirlo en el YAML ni subirlo a Git.

PowerShell:

```powershell
$env:AZURE_DEVOPS_PAT = "TU_PAT"
```

macOS/Linux:

```bash
export AZURE_DEVOPS_PAT="TU_PAT"
```

## Uso

Últimas 24 horas, copiando el correo si solo se generó uno:

```bash
avance
```

Últimos siete días:

```bash
avance --desde 7d
```

Desde una fecha y guardando los correos como archivos:

```bash
avance --desde 2026-09-01 --salida correos
```

Otra configuración:

```bash
avance --config mi-avance.yml
```

El programa identifica al usuario asociado con el PAT. No es necesario configurar el
UUID del usuario. Solo consulta PRs creados por ese usuario en los repositorios del YAML.

## Seguridad

- No guardes el PAT en `avance.yml`.
- Usa el permiso mínimo **Code: Read**.
- Agrega `avance.yml`, `.venv/` y cualquier salida de correos a tu `.gitignore` si el
  proyecto se almacena en Git.

