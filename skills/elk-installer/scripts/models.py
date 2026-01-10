"""
Data models for the ELK installer.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConnectionInfo:
    """SSH connection details for the target host."""
    host: str
    user: str
    password: str
    port: int = 22

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.host or not self.host.strip():
            errors.append("host is required")
        if not self.user or not self.user.strip():
            errors.append("user is required")
        if not self.password:
            errors.append("password is required")
        if not (1 <= self.port <= 65535):
            errors.append("port must be between 1 and 65535")
        return errors

    def __str__(self) -> str:
        return f"{self.user}@{self.host}:{self.port}"


@dataclass
class InstallOptions:
    """Installer options for the Elastic Stack."""
    connection: ConnectionInfo
    elastic_major: str = "8"
    cluster_name: str = "elk-cluster"
    node_mode: str = "single"
    bind_host: str = "0.0.0.0"
    http_port: int = 9200
    kibana_host: str = "0.0.0.0"
    kibana_port: int = 5601
    heap_size: str = "2g"
    open_firewall: bool = False
    seed_hosts: Optional[list[str]] = None
    initial_masters: Optional[list[str]] = None
    skip_tests: bool = False
    wait_seconds: int = 180

    def validate(self) -> list[str]:
        errors = self.connection.validate()
        if self.node_mode not in {"single", "multi"}:
            errors.append("node_mode must be 'single' or 'multi'")
        if self.node_mode == "multi":
            if not self.seed_hosts:
                errors.append("seed_hosts is required for multi-node")
            if not self.initial_masters:
                errors.append("initial_masters is required for multi-node")
        if not self.elastic_major or not self.elastic_major.strip():
            errors.append("elastic_major is required")
        if not self.heap_size or not self.heap_size.strip():
            errors.append("heap_size is required")
        return errors


@dataclass
class InstallResult:
    """Result of a remote installation run."""
    success: bool
    message: str
    elastic_password: Optional[str] = None
    elasticsearch_url: Optional[str] = None
    kibana_url: Optional[str] = None
    os_family: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "success": self.success,
            "message": self.message,
        }
        if self.elastic_password:
            result["elastic_password"] = self.elastic_password
        if self.elasticsearch_url:
            result["elasticsearch_url"] = self.elasticsearch_url
        if self.kibana_url:
            result["kibana_url"] = self.kibana_url
        if self.os_family:
            result["os_family"] = self.os_family
        if self.error:
            result["error"] = self.error
        return result
