"""
K8S-Installer 資料模型

定義所有資料結構，包含節點連線資訊、叢集配置、執行結果等。
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class StepStatus(Enum):
    """安裝步驟狀態"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class NodeConnection:
    """K8S 節點的 SSH 連線資訊"""
    host: str
    user: str
    password: str
    port: int = 22

    def validate(self) -> list[str]:
        """驗證節點連線資訊，回傳錯誤訊息列表"""
        errors = []
        if not self.host or not self.host.strip():
            errors.append("host 不可為空")
        if not self.user or not self.user.strip():
            errors.append("user 不可為空")
        if not self.password:
            errors.append("password 不可為空")
        if not (1 <= self.port <= 65535):
            errors.append(f"port 必須在 1-65535 範圍內，目前為 {self.port}")
        return errors

    def __str__(self) -> str:
        return f"{self.user}@{self.host}:{self.port}"


@dataclass
class ClusterConfig:
    """K8S 叢集配置"""
    control_plane: NodeConnection
    workers: list[NodeConnection] = field(default_factory=list)
    pod_network_cidr: str = "10.244.0.0/16"

    def validate(self) -> list[str]:
        """驗證叢集配置，回傳錯誤訊息列表"""
        errors = []
        
        # 驗證 Control Plane
        cp_errors = self.control_plane.validate()
        if cp_errors:
            errors.extend([f"Control Plane: {e}" for e in cp_errors])
        
        # 驗證 Workers
        for i, worker in enumerate(self.workers):
            w_errors = worker.validate()
            if w_errors:
                errors.extend([f"Worker {i+1}: {e}" for e in w_errors])
        
        return errors

    def all_nodes(self) -> list[NodeConnection]:
        """取得所有節點（Control Plane + Workers）"""
        return [self.control_plane] + self.workers


@dataclass
class ExecutionResult:
    """Skill 執行結果"""
    success: bool
    message: str
    output: Optional[str] = None
    error: Optional[str] = None
    join_command: Optional[str] = None

    def to_dict(self) -> dict:
        """轉換為字典格式（用於 JSON 輸出）"""
        result = {
            "success": self.success,
            "message": self.message,
        }
        if self.output:
            result["output"] = self.output
        if self.error:
            result["error"] = self.error
        if self.join_command:
            result["join_command"] = self.join_command
        return result


@dataclass
class InstallationStep:
    """安裝步驟狀態追蹤"""
    name: str
    node: str
    status: StepStatus = StepStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None

    def mark_running(self) -> None:
        """標記為執行中"""
        self.status = StepStatus.RUNNING

    def mark_success(self, output: str = "") -> None:
        """標記為成功"""
        self.status = StepStatus.SUCCESS
        self.output = output

    def mark_failed(self, error: str) -> None:
        """標記為失敗"""
        self.status = StepStatus.FAILED
        self.error = error


@dataclass
class SkillParameter:
    """Skill 參數定義"""
    name: str
    type: str
    required: bool
    description: str
    default: Optional[str] = None


@dataclass
class SkillDefinition:
    """Skill 元資料定義"""
    name: str
    description: str
    version: str
    parameters: list[SkillParameter] = field(default_factory=list)
    entrypoint: str = "main.py"
