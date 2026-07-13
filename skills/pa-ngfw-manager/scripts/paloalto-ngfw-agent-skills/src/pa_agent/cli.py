from __future__ import annotations

import asyncio
import json

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.json import JSON as RichJSON
from rich.table import Table

from pa_agent.config import get_settings
from pa_agent.errors import PAAgentError
from pa_agent.models import PolicyFilter, SecurityRule, ToolResponse
from pa_agent.panos_api import PanosAPI
from pa_agent.skills import anomaly, backup_restore, policy, system

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    """Run an async coroutine from a sync typer command."""
    return asyncio.run(coro)


def _settings():
    """Load settings, catching pydantic validation errors."""
    try:
        return get_settings()
    except ValidationError as exc:
        console = Console(stderr=True)
        console.print("[red]Configuration error:[/red] required environment variables are missing or invalid.")
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err["loc"])
            console.print(f"  • {loc}: {err['msg']}")
        raise typer.Exit(1)


def _output(response: ToolResponse, output_format: str = "table"):
    """Print ToolResponse as JSON or rich table."""
    console = Console()
    if not response.ok:
        msg = response.error.get("message", str(response.error)) if isinstance(response.error, dict) else str(response.error)
        console.print(f"[red]Error:[/red] {msg}", style="red")
        raise typer.Exit(1)

    if output_format == "json":
        console.print_json(json.dumps(response.result, indent=2, default=str))
        return

    data = response.result
    if isinstance(data, list) and data and isinstance(data[0], dict):
        _render_table(console, data)
    elif isinstance(data, dict):
        _render_kv(console, data)
    else:
        console.print(data)


def _render_table(console: Console, rows: list[dict], columns: list[str] | None = None):
    """Render a list of dicts as a rich Table, auto-selecting columns."""
    if not rows:
        console.print("[dim]No results.[/dim]")
        return

    if columns is None:
        columns = list(rows[0].keys())

    table = Table(show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*(str(row.get(c, "")) for c in columns))
    console.print(table)


def _render_kv(console: Console, data: dict):
    """Render a dict as a key/value table."""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Key")
    table.add_column("Value")
    for k, v in data.items():
        table.add_row(str(k), str(v))
    console.print(table)


# Column sets for known result types
_POLICY_COLS = ["name", "from_zones", "to_zones", "source", "destination", "service", "application", "action", "disabled"]
_BACKUP_COLS = ["filename", "hostname", "timestamp", "sha256", "size"]
_ANOMALY_COLS = ["rule_id", "severity", "summary", "first_seen"]


def _output_typed(response: ToolResponse, output_format: str, columns: list[str] | None = None):
    """Output with optional column hints."""
    console = Console()
    if not response.ok:
        msg = response.error.get("message", str(response.error)) if isinstance(response.error, dict) else str(response.error)
        console.print(f"[red]Error:[/red] {msg}", style="red")
        raise typer.Exit(1)

    if output_format == "json":
        console.print_json(json.dumps(response.result, indent=2, default=str))
        return

    data = response.result
    if isinstance(data, list) and data and isinstance(data[0], dict):
        # Truncate sha256 for backup listings
        if columns and "sha256" in columns:
            for row in data:
                if "sha256" in row and isinstance(row["sha256"], str) and len(row["sha256"]) > 12:
                    row["sha256"] = row["sha256"][:12] + "…"
        _render_table(console, data, columns=columns)
    elif isinstance(data, dict):
        _render_kv(console, data)
    else:
        console.print(data)


def _split(value: str | None) -> list[str]:
    """Split a comma-separated string into a list, or return ['any']."""
    if not value:
        return ["any"]
    return [v.strip() for v in value.split(",") if v.strip()]


# ---------------------------------------------------------------------------
# Typer apps
# ---------------------------------------------------------------------------

app = typer.Typer(name="pa-agent", help="Palo Alto NGFW Agent Skills CLI")
policy_app = typer.Typer(help="Security policy management")
config_app = typer.Typer(help="Configuration backup & restore")
system_app = typer.Typer(help="System monitoring")
anomaly_app = typer.Typer(help="Anomaly detection")

app.add_typer(policy_app, name="policy")
app.add_typer(config_app, name="config")
app.add_typer(system_app, name="system")
app.add_typer(anomaly_app, name="anomaly")


# ---------------------------------------------------------------------------
# Policy commands
# ---------------------------------------------------------------------------

@policy_app.command("list")
def policy_list(
    contains: str = typer.Option(None, "--contains", help="Filter by name contains"),
    from_zone: str = typer.Option(None, "--from-zone"),
    to_zone: str = typer.Option(None, "--to-zone"),
    tag: str = typer.Option(None, "--tag"),
    action: str = typer.Option(None, "--action"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table"),
):
    """List security policy rules."""
    settings = _settings()
    filters = PolicyFilter(
        name_contains=contains,
        from_zone=from_zone,
        to_zone=to_zone,
        tag=tag,
        action=action,
    )

    async def _inner():
        async with PanosAPI(settings) as api:
            return await policy.list_rules(api, filters)

    resp = _run(_inner())
    _output_typed(resp, output, columns=_POLICY_COLS)


@policy_app.command("add")
def policy_add(
    name: str = typer.Option(..., "--name"),
    from_zone: str = typer.Option("any", "--from-zone"),
    to_zone: str = typer.Option("any", "--to-zone"),
    source: str = typer.Option("any", "--source"),
    destination: str = typer.Option("any", "--destination"),
    service: str = typer.Option("application-default", "--service"),
    application: str = typer.Option("any", "--application"),
    action_val: str = typer.Option("allow", "--action"),
    description: str = typer.Option("", "--description"),
    log_setting: str = typer.Option(None, "--log-setting"),
    tag: str = typer.Option(None, "--tag"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
    validate: bool = typer.Option(False, "--validate"),
    commit: bool = typer.Option(False, "--commit"),
    commit_comment: str = typer.Option(None, "--commit-comment"),
    output: str = typer.Option("table", "--output", "-o"),
):
    """Add a new security policy rule."""
    settings = _settings()
    rule = SecurityRule(
        name=name,
        from_zones=_split(from_zone),
        to_zones=_split(to_zone),
        source=_split(source),
        destination=_split(destination),
        service=_split(service),
        application=_split(application),
        action=action_val,
        description=description,
        log_setting=log_setting,
        tags=_split(tag) if tag else [],
    )

    async def _inner():
        async with PanosAPI(settings) as api:
            return await policy.add_rule(
                api, rule,
                dry_run=dry_run, confirm=confirm, validate=validate,
                commit=commit, commit_comment=commit_comment,
            )

    resp = _run(_inner())
    _output_typed(resp, output)


@policy_app.command("update")
def policy_update(
    name: str = typer.Option(..., "--name"),
    set_fields: list[str] = typer.Option(None, "--set", help="Field=value pairs"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
    validate: bool = typer.Option(False, "--validate"),
    commit: bool = typer.Option(False, "--commit"),
    commit_comment: str = typer.Option(None, "--commit-comment"),
    output: str = typer.Option("table", "--output", "-o"),
):
    """Update an existing security policy rule."""
    settings = _settings()

    patches: dict = {}
    for pair in set_fields or []:
        if "=" not in pair:
            Console(stderr=True).print(f"[red]Invalid --set value:[/red] '{pair}'. Expected key=value.")
            raise typer.Exit(1)
        key, _, val = pair.partition("=")
        # Comma-separated values become lists for list-typed fields
        if "," in val:
            patches[key.strip()] = [v.strip() for v in val.split(",")]
        else:
            patches[key.strip()] = val.strip()

    async def _inner():
        async with PanosAPI(settings) as api:
            return await policy.update_rule(
                api, name, patches,
                dry_run=dry_run, confirm=confirm, validate=validate,
                commit=commit, commit_comment=commit_comment,
            )

    resp = _run(_inner())
    _output_typed(resp, output)


@policy_app.command("delete")
def policy_delete(
    name: str = typer.Option(..., "--name"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
    commit: bool = typer.Option(False, "--commit"),
    commit_comment: str = typer.Option(None, "--commit-comment"),
    output: str = typer.Option("table", "--output", "-o"),
):
    """Delete a security policy rule."""
    settings = _settings()

    async def _inner():
        async with PanosAPI(settings) as api:
            return await policy.delete_rule(
                api, name,
                dry_run=dry_run, confirm=confirm,
                commit=commit, commit_comment=commit_comment,
            )

    resp = _run(_inner())
    _output_typed(resp, output)


# ---------------------------------------------------------------------------
# Config (backup & restore) commands
# ---------------------------------------------------------------------------

@config_app.command("backup")
def config_backup(
    backend: str = typer.Option("local", "--backend", help="Storage: local or s3"),
    output: str = typer.Option("table", "--output", "-o"),
):
    """Create a configuration backup."""
    settings = _settings()
    storage = backup_restore.get_storage(backend, settings)

    async def _inner():
        async with PanosAPI(settings) as api:
            return await backup_restore.backup(api, storage)

    resp = _run(_inner())
    _output_typed(resp, output, columns=_BACKUP_COLS)


@config_app.command("restore")
def config_restore(
    backend: str = typer.Option("local", "--backend"),
    key: str = typer.Option(..., "--key", help="Backup filename or S3 key"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
    commit: bool = typer.Option(False, "--commit"),
    commit_comment: str = typer.Option(None, "--commit-comment"),
    output: str = typer.Option("table", "--output", "-o"),
):
    """Restore configuration from a backup."""
    settings = _settings()
    storage = backup_restore.get_storage(backend, settings)

    async def _inner():
        async with PanosAPI(settings) as api:
            return await backup_restore.restore(
                api, storage, key,
                dry_run=dry_run, confirm=confirm,
                commit=commit, commit_comment=commit_comment,
            )

    resp = _run(_inner())
    _output_typed(resp, output)


@config_app.command("list")
def config_list_backups(
    backend: str = typer.Option("local", "--backend"),
    output: str = typer.Option("table", "--output", "-o"),
):
    """List available configuration backups."""
    settings = _settings()
    storage = backup_restore.get_storage(backend, settings)

    async def _inner():
        return await backup_restore.list_backups(storage)

    resp = _run(_inner())
    _output_typed(resp, output, columns=_BACKUP_COLS)


# ---------------------------------------------------------------------------
# System commands
# ---------------------------------------------------------------------------

@system_app.command("usage")
def system_usage(
    output: str = typer.Option("table", "--output", "-o"),
):
    """Show firewall system resource usage."""
    settings = _settings()

    async def _inner():
        async with PanosAPI(settings) as api:
            return await system.get_usage(api)

    resp = _run(_inner())
    _output_typed(resp, output)


# ---------------------------------------------------------------------------
# Anomaly commands
# ---------------------------------------------------------------------------

@anomaly_app.command("detect")
def anomaly_detect(
    window: str = typer.Option("1h", "--window", help="Analysis window (e.g., 15m, 1h, 24h)"),
    baseline: str = typer.Option("24h", "--baseline", help="Baseline period (e.g., 24h, 7d)"),
    output: str = typer.Option("table", "--output", "-o"),
):
    """Detect anomalies in firewall traffic patterns."""
    settings = _settings()

    async def _inner():
        async with PanosAPI(settings) as api:
            return await anomaly.detect(api, window=window, baseline=baseline)

    resp = _run(_inner())
    _output_typed(resp, output, columns=_ANOMALY_COLS)
