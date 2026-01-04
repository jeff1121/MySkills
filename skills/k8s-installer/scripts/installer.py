"""
K8S 安裝器

協調整個 K8S 叢集的安裝流程。
"""
from typing import Callable, Optional

from models import (
    ClusterConfig,
    ExecutionResult,
    InstallationStep,
    NodeConnection,
    StepStatus,
)
from ssh_client import K8SSSHClient, SSHConnectionError, SSHCommandError
from prompts import show_progress
from commands import (
    get_disable_swap_script,
    get_load_kernel_modules_script,
    get_configure_sysctl_script,
    get_install_containerd_script,
    get_install_kubernetes_packages_script,
    get_kubeadm_init_script,
    get_install_flannel_script,
    get_generate_join_command_script,
    get_worker_join_script,
)


class K8SInstaller:
    """K8S 叢集安裝器"""

    def __init__(self, config: ClusterConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.steps: list[InstallationStep] = []
        self.join_command: Optional[str] = None

    def install(self) -> ExecutionResult:
        """
        執行完整的 K8S 安裝流程
        
        Returns:
            ExecutionResult 執行結果
        """
        try:
            # Phase 1: 在所有節點執行前置作業
            self._run_prerequisites_on_all_nodes()
            
            # Phase 2: 在所有節點安裝套件
            self._run_package_install_on_all_nodes()
            
            # Phase 3: 初始化 Control Plane
            self._init_control_plane()
            
            # Phase 4: Worker 加入叢集
            self._join_workers()
            
            return ExecutionResult(
                success=True,
                message="K8S 叢集安裝完成",
                join_command=self.join_command,
            )
        except (SSHConnectionError, SSHCommandError) as e:
            return ExecutionResult(
                success=False,
                message="安裝失敗",
                error=str(e),
            )

    def _run_prerequisites_on_all_nodes(self) -> None:
        """在所有節點執行前置作業"""
        scripts = [
            ("停用 Swap", get_disable_swap_script),
            ("載入核心模組", get_load_kernel_modules_script),
            ("設定 Sysctl", get_configure_sysctl_script),
        ]
        
        for node in self.config.all_nodes():
            for step_name, script_fn in scripts:
                self._execute_step(node, step_name, script_fn())

    def _run_package_install_on_all_nodes(self) -> None:
        """在所有節點安裝套件"""
        scripts = [
            ("安裝 Containerd", get_install_containerd_script),
            ("安裝 K8S 套件", get_install_kubernetes_packages_script),
        ]
        
        for node in self.config.all_nodes():
            for step_name, script_fn in scripts:
                self._execute_step(node, step_name, script_fn())

    def _init_control_plane(self) -> None:
        """初始化 Control Plane"""
        cp = self.config.control_plane
        
        # 執行 kubeadm init
        self._execute_step(
            cp,
            "初始化 Control Plane",
            get_kubeadm_init_script(self.config.pod_network_cidr),
        )
        
        # 安裝 Flannel
        self._execute_step(cp, "安裝 Flannel CNI", get_install_flannel_script())
        
        # 取得 join command
        self._get_join_command()

    def _get_join_command(self) -> None:
        """從 Control Plane 取得 join 命令"""
        cp = self.config.control_plane
        show_progress("取得 Join 命令", str(cp), "running")
        
        with K8SSSHClient(cp) as client:
            stdout, stderr, exit_code = client.execute(
                get_generate_join_command_script()
            )
            if exit_code == 0:
                self.join_command = stdout.strip()
                show_progress("取得 Join 命令", str(cp), "success")
            else:
                raise SSHCommandError(f"無法取得 join 命令：{stderr}")

    def _join_workers(self) -> None:
        """Worker 節點加入叢集"""
        if not self.join_command:
            raise SSHCommandError("缺少 join 命令，無法加入 Worker")
        
        for worker in self.config.workers:
            self._execute_step(
                worker,
                "加入叢集",
                get_worker_join_script(self.join_command),
            )

    def _execute_step(
        self,
        node: NodeConnection,
        step_name: str,
        script: str,
    ) -> None:
        """
        執行單一安裝步驟
        
        Args:
            node: 目標節點
            step_name: 步驟名稱
            script: 要執行的腳本
        """
        step = InstallationStep(name=step_name, node=str(node))
        self.steps.append(step)
        
        show_progress(step_name, str(node), "running")
        step.mark_running()
        
        try:
            with K8SSSHClient(node) as client:
                stdout, stderr, exit_code = client.execute(script)
                
                if exit_code == 0:
                    step.mark_success(stdout)
                    show_progress(step_name, str(node), "success")
                else:
                    error_msg = stderr if stderr else f"Exit code: {exit_code}"
                    step.mark_failed(error_msg)
                    show_progress(step_name, str(node), "failed")
                    raise SSHCommandError(
                        f"[{node}] {step_name} 失敗：{error_msg}"
                    )
        except SSHConnectionError as e:
            step.mark_failed(str(e))
            show_progress(step_name, str(node), "failed")
            raise


def run_installation(
    config: ClusterConfig,
    verbose: bool = False,
) -> ExecutionResult:
    """
    執行 K8S 安裝
    
    Args:
        config: 叢集配置
        verbose: 是否顯示詳細輸出
        
    Returns:
        ExecutionResult 執行結果
    """
    installer = K8SInstaller(config, verbose)
    return installer.install()
