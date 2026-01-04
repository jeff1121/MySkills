"""
SSH Client 封裝

提供 SSH 連線、命令執行、錯誤處理功能。
"""
import socket
from typing import Optional, Tuple

from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import (
    AuthenticationException,
    NoValidConnectionsError,
    SSHException,
)

from models import NodeConnection


# SSH 連線逾時設定（秒）
SSH_TIMEOUT = 30
BANNER_TIMEOUT = 30
AUTH_TIMEOUT = 30


class SSHConnectionError(Exception):
    """SSH 連線錯誤"""
    pass


class SSHCommandError(Exception):
    """SSH 命令執行錯誤"""
    pass


class K8SSSHClient:
    """K8S 安裝用 SSH Client 封裝"""

    def __init__(self, node: NodeConnection):
        self.node = node
        self._client: Optional[SSHClient] = None

    def connect(self) -> None:
        """建立 SSH 連線"""
        try:
            self._client = SSHClient()
            self._client.set_missing_host_key_policy(AutoAddPolicy())
            self._client.connect(
                hostname=self.node.host,
                port=self.node.port,
                username=self.node.user,
                password=self.node.password,
                timeout=SSH_TIMEOUT,
                banner_timeout=BANNER_TIMEOUT,
                auth_timeout=AUTH_TIMEOUT,
            )
        except AuthenticationException as e:
            raise SSHConnectionError(
                f"認證失敗：請確認 {self.node} 的使用者名稱與密碼是否正確"
            ) from e
        except NoValidConnectionsError as e:
            raise SSHConnectionError(
                f"無法連線：請確認 {self.node} 是否可達，SSH 服務是否啟動"
            ) from e
        except socket.timeout as e:
            raise SSHConnectionError(
                f"連線逾時：{self.node} 在 {SSH_TIMEOUT} 秒內無回應"
            ) from e
        except SSHException as e:
            raise SSHConnectionError(f"SSH 錯誤：{str(e)}") from e

    def disconnect(self) -> None:
        """關閉 SSH 連線"""
        if self._client:
            self._client.close()
            self._client = None

    def execute(self, command: str) -> Tuple[str, str, int]:
        """
        執行 SSH 命令
        
        Returns:
            Tuple[stdout, stderr, exit_code]
        """
        if not self._client:
            raise SSHConnectionError("尚未建立連線，請先呼叫 connect()")

        try:
            stdin, stdout, stderr = self._client.exec_command(
                command, 
                timeout=SSH_TIMEOUT
            )
            exit_code = stdout.channel.recv_exit_status()
            stdout_str = stdout.read().decode("utf-8")
            stderr_str = stderr.read().decode("utf-8")
            return stdout_str, stderr_str, exit_code
        except socket.timeout as e:
            raise SSHCommandError(
                f"命令執行逾時：{command[:50]}..."
            ) from e
        except SSHException as e:
            raise SSHCommandError(f"命令執行失敗：{str(e)}") from e

    def execute_script(self, script: str) -> Tuple[str, str, int]:
        """
        執行多行腳本
        
        將腳本內容透過 bash -c 執行
        """
        # 將腳本轉換為單行執行
        escaped_script = script.replace("'", "'\"'\"'")
        command = f"bash -c '{escaped_script}'"
        return self.execute(command)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


def test_connection(node: NodeConnection) -> Tuple[bool, str]:
    """
    測試 SSH 連線
    
    Returns:
        Tuple[success, message]
    """
    try:
        with K8SSSHClient(node) as client:
            stdout, stderr, exit_code = client.execute("echo 'Connection OK'")
            if exit_code == 0:
                return True, f"連線成功：{node}"
            else:
                return False, f"連線異常：{stderr}"
    except SSHConnectionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"未知錯誤：{str(e)}"
