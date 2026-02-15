"""
Cisco Configer 資料模型。
"""
from dataclasses import dataclass, field
from typing import Optional

__version__ = "0.1.0"


@dataclass
class ConnectionInfo:
    """Cisco 設備 SSH 連線資訊。"""

    host: str
    username: str
    password: str
    device_type: Optional[str] = None
    enable_password: Optional[str] = None
    port: int = 22

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.host or not self.host.strip():
            errors.append("host is required")
        if not self.username or not self.username.strip():
            errors.append("username is required")
        if not self.password:
            errors.append("password is required")
        if not (1 <= self.port <= 65535):
            errors.append("port must be between 1 and 65535")
        valid_types = {"cisco_ios", "cisco_nxos", "cisco_asa", "cisco_xr"}
        if self.device_type is not None and self.device_type not in valid_types:
            errors.append(
                f"device_type must be one of {sorted(valid_types)}, "
                f"got '{self.device_type}'"
            )
        return errors

    def __str__(self) -> str:
        return f"{self.username}@{self.host}:{self.port}"


@dataclass
class CommandResult:
    """單一指令的執行結果。"""

    command: str
    output: str
    formatted_output: str
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "command": self.command,
            "output": self.output,
            "formatted_output": self.formatted_output,
            "success": self.success,
        }
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class ExecutionResult:
    """整體執行結果（可包含多條指令）。"""

    success: bool
    device_info: Optional[str] = None
    results: list[CommandResult] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        result: dict = {
            "success": self.success,
            "results": [r.to_dict() for r in self.results],
        }
        if self.device_info:
            result["device_info"] = self.device_info
        if self.error:
            result["error"] = self.error
        return result
