"""
Remote installer for the Elastic Stack.
"""
from dataclasses import dataclass
from typing import Optional

from commands import (
    build_elasticsearch_config_script,
    build_elasticsearch_password_script,
    build_elasticsearch_test_script,
    build_firewall_script,
    build_install_packages_script,
    build_jvm_options_script,
    build_kibana_ca_script,
    build_kibana_config_script,
    build_kibana_test_script,
    build_logstash_ca_script,
    build_logstash_keystore_script,
    build_logstash_pipeline_script,
    build_logstash_test_script,
    build_prereq_script,
    build_repo_script,
    build_service_enable_script,
    build_update_script,
    build_wait_for_service_script,
    detect_os_family,
    _parse_version_major,
)
from models import InstallOptions, InstallResult
from ssh_client import ElkSSHClient, SSHCommandError, SSHConnectionError


class InstallerError(Exception):
    """Installer workflow error."""


@dataclass
class _InstallContext:
    os_family: Optional[str] = None
    use_sudo: bool = False
    elastic_password: Optional[str] = None
    kibana_service_token: Optional[str] = None


def run_installation(options: InstallOptions, verbose: bool = False) -> InstallResult:
    errors = options.validate()
    if errors:
        return InstallResult(
            success=False,
            message="Invalid options",
            error="; ".join(errors),
        )

    installer = ElkInstaller(options, verbose)
    try:
        return installer.run()
    except (SSHConnectionError, SSHCommandError, InstallerError) as exc:
        return InstallResult(
            success=False,
            message="Installation failed",
            error=str(exc),
        )


class ElkInstaller:
    """Orchestrate remote Elastic Stack installation."""

    def __init__(self, options: InstallOptions, verbose: bool = False) -> None:
        self.options = options
        self.verbose = verbose
        self.context = _InstallContext()
        self._notes: list[str] = []

    def run(self) -> InstallResult:
        with ElkSSHClient(self.options.connection) as client:
            self.client = client
            self.context.use_sudo = self._ensure_privileges()
            self.context.os_family = self._detect_os_family()

            self._run_step("Update OS", build_update_script(self.context.os_family))
            self._run_step(
                "Install prerequisites",
                build_prereq_script(self.context.os_family),
            )
            self._run_step(
                "Configure Elastic repository",
                build_repo_script(self.context.os_family, self.options.elastic_major),
            )
            self._run_step(
                "Install Elastic Stack packages",
                build_install_packages_script(self.context.os_family),
            )
            self._run_step(
                "Write Elasticsearch config",
                build_elasticsearch_config_script(
                    self.options.cluster_name,
                    self.options.bind_host,
                    self.options.http_port,
                    self.options.elastic_major,
                    self.options.node_mode,
                    self.options.seed_hosts,
                    self.options.initial_masters,
                ),
            )
            self._run_step(
                "Write Elasticsearch heap settings",
                build_jvm_options_script(self.options.heap_size),
            )
            self._run_step(
                "Enable and start Elasticsearch",
                build_service_enable_script("elasticsearch"),
            )
            self._run_step(
                "Wait for Elasticsearch",
                build_wait_for_service_script(
                    "elasticsearch",
                    self.options.wait_seconds,
                ),
            )

            self.context.elastic_password = self._reset_elasticsearch_password()
            if _parse_version_major(self.options.elastic_major) >= 8:
                self.context.kibana_service_token = (
                    self._create_kibana_service_token()
                )

            self._run_step(
                "Configure Kibana CA",
                build_kibana_ca_script(),
            )
            self._run_step(
                "Write Kibana config",
                build_kibana_config_script(
                    self.options.kibana_host,
                    self.options.kibana_port,
                    self.options.http_port,
                    self.options.elastic_major,
                    self.context.elastic_password,
                    self.context.kibana_service_token,
                ),
            )
            self._run_step(
                "Configure Logstash CA",
                build_logstash_ca_script(),
            )
            self._run_step(
                "Write Logstash pipeline",
                build_logstash_pipeline_script(
                    self.options.http_port,
                    self.options.logstash_port,
                ),
            )
            self._run_step(
                "Create Logstash keystore",
                build_logstash_keystore_script(self.context.elastic_password),
            )
            self._run_step(
                "Enable and start Kibana",
                build_service_enable_script("kibana"),
            )
            self._run_step(
                "Enable and start Logstash",
                build_service_enable_script("logstash"),
            )

            self._maybe_open_firewall()

            if not self.options.skip_tests:
                self._run_tests()

            message = "Elastic Stack installation completed"
            if self._notes:
                message = f"{message}. Notes: {'; '.join(self._notes)}"

            return InstallResult(
                success=True,
                message=message,
                elastic_password=self.context.elastic_password,
                elasticsearch_url=self._elasticsearch_url(),
                kibana_url=self._kibana_url(),
                os_family=self.context.os_family,
            )

    def _ensure_privileges(self) -> bool:
        stdout, _, exit_code = self.client.execute("id -u")
        if exit_code != 0:
            raise InstallerError("Unable to verify remote user")
        if stdout.strip() == "0":
            return False

        _, _, sudo_exit = self.client.execute("sudo -n true")
        if sudo_exit == 0:
            return True

        raise InstallerError(
            "Root or passwordless sudo is required on the target host"
        )

    def _detect_os_family(self) -> str:
        stdout, _, exit_code = self.client.execute("cat /etc/os-release")
        if exit_code != 0:
            raise InstallerError("Unable to read /etc/os-release")
        os_id, version_id = _parse_os_release(stdout)
        if not os_id:
            raise InstallerError("OS ID not found in /etc/os-release")
        if not version_id:
            raise InstallerError("OS VERSION_ID not found in /etc/os-release")
        try:
            return detect_os_family(os_id, version_id)
        except ValueError as exc:
            raise InstallerError(str(exc)) from exc

    def _reset_elasticsearch_password(self) -> str:
        stdout, stderr, exit_code = self.client.execute_script(
            build_elasticsearch_password_script(),
            use_sudo=self.context.use_sudo,
        )
        if exit_code != 0:
            raise InstallerError(
                f"Failed to reset elastic password: {stderr.strip()}"
            )
        password = _parse_password(stdout)
        if not password:
            raise InstallerError("Unable to parse elastic password output")
        return password

    def _create_kibana_service_token(self) -> str:
        token_name = "elk-installer"
        script = f"""set -e
export ES_PATH_CONF=/etc/elasticsearch
/usr/share/elasticsearch/bin/elasticsearch-service-tokens delete elastic/kibana {token_name} || true
/usr/share/elasticsearch/bin/elasticsearch-service-tokens create elastic/kibana {token_name}
chown root:elasticsearch /etc/elasticsearch/service_tokens
chmod 660 /etc/elasticsearch/service_tokens"""
        stdout, stderr, exit_code = self.client.execute_script(
            script,
            use_sudo=self.context.use_sudo,
        )
        if exit_code != 0:
            error = stderr.strip() or stdout.strip()
            raise InstallerError(
                f"Failed to create Kibana service token: {error}"
            )
        token = _parse_service_token(stdout)
        if not token:
            raise InstallerError("Unable to parse Kibana service token output")
        return token

    def _run_step(self, name: str, script: str) -> None:
        self._log(f"[RUN] {name}")
        stdout, stderr, exit_code = self.client.execute_script(
            script,
            use_sudo=self.context.use_sudo,
        )
        if exit_code != 0:
            error = stderr.strip() or stdout.strip()
            raise InstallerError(f"{name} failed: {error}")
        if self.verbose and stdout.strip():
            self._log(stdout.strip())

    def _maybe_open_firewall(self) -> None:
        if not self.options.open_firewall:
            return

        firewall_script = build_firewall_script(
            self.context.os_family,
            self.options.http_port,
            self.options.kibana_port,
            self.options.logstash_port,
        )
        if not firewall_script:
            self._notes.append("Firewall rules not applied for this OS")
            return

        self._run_step("Open firewall ports", firewall_script)

    def _run_tests(self) -> None:
        self._run_step(
            "Test Elasticsearch",
            build_elasticsearch_test_script(
                self.context.elastic_password,
                self.options.http_port,
            ),
        )
        self._run_step(
            "Test Kibana",
            build_kibana_test_script(self.options.kibana_port),
        )
        self._run_step("Test Logstash", build_logstash_test_script())

    def _log(self, message: str) -> None:
        print(message)

    def _elasticsearch_url(self) -> str:
        return f"https://{self.options.connection.host}:{self.options.http_port}"

    def _kibana_url(self) -> str:
        return f"http://{self.options.connection.host}:{self.options.kibana_port}"


def _parse_os_release(content: str) -> tuple[Optional[str], Optional[str]]:
    os_id = None
    version_id = None
    for line in content.splitlines():
        if line.startswith("ID="):
            os_id = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("VERSION_ID="):
            version_id = line.split("=", 1)[1].strip().strip('"')
    return os_id, version_id


def _parse_password(output: str) -> Optional[str]:
    for line in output.splitlines():
        if "New value:" in line:
            return line.split("New value:", 1)[1].strip()
    return None


def _parse_service_token(output: str) -> Optional[str]:
    for line in output.splitlines():
        if "SERVICE_TOKEN" in line and "=" in line:
            return line.split("=", 1)[1].strip()
    return None
