"""
SSH client wrapper for remote command execution.
"""
import socket
from typing import Optional, Tuple

from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import (
    AuthenticationException,
    NoValidConnectionsError,
    SSHException,
)

from models import ConnectionInfo


SSH_TIMEOUT = 30
BANNER_TIMEOUT = 30
AUTH_TIMEOUT = 30


class SSHConnectionError(Exception):
    """SSH connection failure."""


class SSHCommandError(Exception):
    """Remote command execution failure."""


class ElkSSHClient:
    """ELK installer SSH client wrapper."""

    def __init__(self, connection: ConnectionInfo):
        self.connection = connection
        self._client: Optional[SSHClient] = None

    def connect(self) -> None:
        try:
            self._client = SSHClient()
            self._client.set_missing_host_key_policy(AutoAddPolicy())
            self._client.connect(
                hostname=self.connection.host,
                port=self.connection.port,
                username=self.connection.user,
                password=self.connection.password,
                timeout=SSH_TIMEOUT,
                banner_timeout=BANNER_TIMEOUT,
                auth_timeout=AUTH_TIMEOUT,
            )
        except AuthenticationException as exc:
            raise SSHConnectionError(
                f"Authentication failed for {self.connection}"
            ) from exc
        except NoValidConnectionsError as exc:
            raise SSHConnectionError(
                f"Unable to connect to {self.connection}"
            ) from exc
        except socket.timeout as exc:
            raise SSHConnectionError(
                f"Connection timed out for {self.connection}"
            ) from exc
        except SSHException as exc:
            raise SSHConnectionError(f"SSH error: {exc}") from exc

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def execute(self, command: str) -> Tuple[str, str, int]:
        if not self._client:
            raise SSHConnectionError("SSH session not connected")

        try:
            _, stdout, stderr = self._client.exec_command(
                command,
                timeout=SSH_TIMEOUT,
            )
            exit_code = stdout.channel.recv_exit_status()
            stdout_str = stdout.read().decode("utf-8")
            stderr_str = stderr.read().decode("utf-8")
            return stdout_str, stderr_str, exit_code
        except socket.timeout as exc:
            raise SSHCommandError(
                f"Command timed out: {command[:60]}"
            ) from exc
        except SSHException as exc:
            raise SSHCommandError(f"SSH command error: {exc}") from exc

    def execute_script(self, script: str, use_sudo: bool = False) -> Tuple[str, str, int]:
        escaped_script = script.replace("'", "'\"'\"'")
        sudo_prefix = "sudo -n " if use_sudo else ""
        command = f"{sudo_prefix}bash -c '{escaped_script}'"
        return self.execute(command)

    def __enter__(self) -> "ElkSSHClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.disconnect()
        return False
