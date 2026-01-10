#!/usr/bin/env python3
"""
ELK-Installer CLI.
"""
import json
import sys
from typing import Optional

import click

from installer import run_installation
from models import ConnectionInfo, InstallOptions


@click.command()
@click.option("--host", prompt="HostAddr", type=str, help="Target host address")
@click.option("--port", prompt="HostPort", type=int, default=22, show_default=True)
@click.option("--user", prompt="HostUser", type=str, default="root", show_default=True)
@click.option(
    "--password",
    prompt="HostPass",
    hide_input=True,
    confirmation_prompt=False,
)
@click.option(
    "--elastic-major",
    default="8",
    show_default=True,
    help="Elastic major version (e.g. 8)",
)
@click.option(
    "--cluster-name",
    default="elk-cluster",
    show_default=True,
)
@click.option(
    "--node-mode",
    type=click.Choice(["single", "multi"], case_sensitive=False),
    default="single",
    show_default=True,
)
@click.option("--bind-host", default="0.0.0.0", show_default=True)
@click.option("--http-port", default=9200, show_default=True)
@click.option("--kibana-host", default="0.0.0.0", show_default=True)
@click.option("--kibana-port", default=5601, show_default=True)
@click.option("--logstash-port", default=5044, show_default=True)
@click.option("--heap-size", default="2g", show_default=True)
@click.option("--open-firewall", is_flag=True, default=False)
@click.option("--seed-host", multiple=True, help="Seed hosts for multi-node")
@click.option("--initial-master", multiple=True, help="Initial masters for multi-node")
@click.option("--skip-tests", is_flag=True, default=False)
@click.option("--json-output", is_flag=True, default=False)
@click.option("--yes", "-y", is_flag=True, default=False)
@click.option("--verbose", is_flag=True, default=False)
def install(
    host: str,
    port: int,
    user: str,
    password: str,
    elastic_major: str,
    cluster_name: str,
    node_mode: str,
    bind_host: str,
    http_port: int,
    kibana_host: str,
    kibana_port: int,
    logstash_port: int,
    heap_size: str,
    open_firewall: bool,
    seed_host: tuple[str, ...],
    initial_master: tuple[str, ...],
    skip_tests: bool,
    json_output: bool,
    yes: bool,
    verbose: bool,
) -> None:
    """Install Elastic Stack on a remote host via SSH."""
    connection = ConnectionInfo(
        host=host.strip(),
        port=port,
        user=user.strip(),
        password=password,
    )
    options = InstallOptions(
        connection=connection,
        elastic_major=elastic_major.strip(),
        cluster_name=cluster_name.strip(),
        node_mode=node_mode,
        bind_host=bind_host.strip(),
        http_port=http_port,
        kibana_host=kibana_host.strip(),
        kibana_port=kibana_port,
        logstash_port=logstash_port,
        heap_size=heap_size.strip(),
        open_firewall=open_firewall,
        seed_hosts=list(seed_host) or None,
        initial_masters=list(initial_master) or None,
        skip_tests=skip_tests,
    )

    errors = options.validate()
    if errors:
        _output_error("Invalid options", "; ".join(errors), json_output)
        sys.exit(1)

    if not yes and not json_output:
        if not _confirm_options(options):
            click.echo("Installation cancelled")
            sys.exit(0)

    result = run_installation(options, verbose)
    _output_result(result, json_output)
    sys.exit(0 if result.success else 1)


def _confirm_options(options: InstallOptions) -> bool:
    click.echo("\nELK-Installer configuration summary")
    click.echo("-" * 40)
    click.echo(f"Target: {options.connection}")
    click.echo(f"Elastic major: {options.elastic_major}")
    click.echo(f"Cluster name: {options.cluster_name}")
    click.echo(f"Node mode: {options.node_mode}")
    click.echo(f"Bind host: {options.bind_host}")
    click.echo(f"HTTP port: {options.http_port}")
    click.echo(f"Kibana host: {options.kibana_host}")
    click.echo(f"Kibana port: {options.kibana_port}")
    click.echo(f"Logstash port: {options.logstash_port}")
    click.echo(f"Heap size: {options.heap_size}")
    click.echo(f"Open firewall: {options.open_firewall}")
    if options.seed_hosts:
        click.echo(f"Seed hosts: {', '.join(options.seed_hosts)}")
    if options.initial_masters:
        click.echo(f"Initial masters: {', '.join(options.initial_masters)}")
    click.echo("-" * 40)
    return click.confirm("Proceed with installation?", default=False)


def _output_result(result, json_output: bool) -> None:
    if json_output:
        click.echo(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
        return

    if result.success:
        click.echo("\nInstallation succeeded")
        if result.elasticsearch_url:
            click.echo(f"Elasticsearch: {result.elasticsearch_url}")
        if result.kibana_url:
            click.echo(f"Kibana: {result.kibana_url}")
        if result.elastic_password:
            click.echo(f"Elastic password: {result.elastic_password}")
            click.echo("Store this password securely.")
    else:
        _output_error(result.message, result.error, json_output=False)


def _output_error(message: str, error: Optional[str], json_output: bool) -> None:
    if json_output:
        payload = {"success": False, "message": message}
        if error:
            payload["error"] = error
        click.echo(json.dumps(payload, ensure_ascii=True, indent=2))
        return

    click.echo(f"\nError: {message}", err=True)
    if error:
        click.echo(f"Details: {error}", err=True)


if __name__ == "__main__":
    install()
