"""
Cisco 設備 SSH 連線封裝（基於 netmiko）。
"""
from typing import Optional

from netmiko import ConnectHandler, SSHDetect
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
    ReadTimeout,
)
from paramiko.ssh_exception import SSHException

from models import ConnectionInfo, CommandResult

__version__ = "0.1.0"

SSH_TIMEOUT = 30
BANNER_TIMEOUT = 30
AUTH_TIMEOUT = 30


class CiscoSSHConnectionError(Exception):
    """SSH 連線失敗。"""


class CiscoSSHCommandError(Exception):
    """遠端指令執行失敗。"""


class CiscoSSHClient:
    """Cisco 設備 SSH 客戶端封裝。"""

    def __init__(self, connection: ConnectionInfo):
        self.connection = connection
        self._net_connect = None
        self._detected_type: Optional[str] = None

    def connect(self) -> None:
        device_params = {
            "host": self.connection.host,
            "username": self.connection.username,
            "password": self.connection.password,
            "port": self.connection.port,
            "timeout": SSH_TIMEOUT,
            "banner_timeout": BANNER_TIMEOUT,
            "auth_timeout": AUTH_TIMEOUT,
        }
        if self.connection.enable_password:
            device_params["secret"] = self.connection.enable_password

        try:
            if self.connection.device_type:
                device_params["device_type"] = self.connection.device_type
                self._net_connect = ConnectHandler(**device_params)
                self._detected_type = self.connection.device_type
            else:
                device_params["device_type"] = "autodetect"
                detector = SSHDetect(**device_params)
                best_match = detector.autodetect()
                if not best_match:
                    raise CiscoSSHConnectionError(
                        f"無法自動偵測 {self.connection} 的設備類型，"
                        "請手動指定 device_type"
                    )
                self._detected_type = best_match
                device_params["device_type"] = best_match
                self._net_connect = ConnectHandler(**device_params)

            if self.connection.enable_password:
                self._net_connect.enable()

        except NetmikoAuthenticationException as exc:
            raise CiscoSSHConnectionError(
                f"認證失敗：{self.connection}"
            ) from exc
        except NetmikoTimeoutException as exc:
            raise CiscoSSHConnectionError(
                f"連線逾時：{self.connection}"
            ) from exc
        except SSHException as exc:
            raise CiscoSSHConnectionError(
                f"SSH 錯誤：{exc}"
            ) from exc

    def disconnect(self) -> None:
        if self._net_connect:
            self._net_connect.disconnect()
            self._net_connect = None

    def get_device_type(self) -> str:
        return self._detected_type or "unknown"

    def execute_show(self, command: str) -> CommandResult:
        if not self._net_connect:
            raise CiscoSSHConnectionError("SSH 尚未連線")
        try:
            output = self._net_connect.send_command(
                command,
                read_timeout=SSH_TIMEOUT,
            )
            return CommandResult(
                command=command,
                output=output,
                formatted_output=output,
                success=True,
            )
        except ReadTimeout as exc:
            return CommandResult(
                command=command,
                output="",
                formatted_output="",
                success=False,
                error=f"指令逾時：{command}",
            )
        except Exception as exc:
            return CommandResult(
                command=command,
                output="",
                formatted_output="",
                success=False,
                error=str(exc),
            )

    def execute_config(self, commands: list[str]) -> CommandResult:
        if not self._net_connect:
            raise CiscoSSHConnectionError("SSH 尚未連線")

        combined_cmd = "; ".join(commands)
        try:
            output = self._net_connect.send_config_set(
                commands,
                read_timeout=SSH_TIMEOUT,
            )
            save_output = self._net_connect.save_config()
            full_output = f"{output}\n{save_output}"
            return CommandResult(
                command=combined_cmd,
                output=full_output,
                formatted_output=full_output,
                success=True,
            )
        except ReadTimeout as exc:
            return CommandResult(
                command=combined_cmd,
                output="",
                formatted_output="",
                success=False,
                error=f"設定指令逾時",
            )
        except Exception as exc:
            return CommandResult(
                command=combined_cmd,
                output="",
                formatted_output="",
                success=False,
                error=str(exc),
            )

    def __enter__(self) -> "CiscoSSHClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.disconnect()
        return False
