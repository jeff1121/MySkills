"""
Cisco 設備指令執行編排邏輯。
"""
from models import ConnectionInfo, CommandResult, ExecutionResult
from ssh_client import CiscoSSHClient, CiscoSSHConnectionError
from formatter import format_output
from commands import get_platform_module

__version__ = "0.1.0"


def run_query(connection: ConnectionInfo, intent: str) -> ExecutionResult:
    """查詢流程：連線 → 偵測平台 → 取得 show 指令 → 執行 → 格式化 → 回傳。"""
    errors = connection.validate()
    if errors:
        return ExecutionResult(
            success=False,
            error=f"連線資訊驗證失敗：{'; '.join(errors)}",
        )

    try:
        with CiscoSSHClient(connection) as client:
            device_type = client.get_device_type()
            platform = get_platform_module(device_type)
            commands = platform.get_info_commands(intent)

            results: list[CommandResult] = []
            for cmd in commands:
                result = client.execute_show(cmd)
                if result.success:
                    result.formatted_output = format_output(
                        result.output, cmd
                    )
                results.append(result)

            all_success = all(r.success for r in results)
            return ExecutionResult(
                success=all_success,
                device_info=device_type,
                results=results,
            )

    except CiscoSSHConnectionError as exc:
        return ExecutionResult(
            success=False,
            error=str(exc),
        )


def run_config(
    connection: ConnectionInfo, intent: str, params: dict
) -> ExecutionResult:
    """設定流程：連線 → 偵測平台 → 產生 config 指令 → 執行 → 驗證 → 回傳。"""
    errors = connection.validate()
    if errors:
        return ExecutionResult(
            success=False,
            error=f"連線資訊驗證失敗：{'; '.join(errors)}",
        )

    try:
        with CiscoSSHClient(connection) as client:
            device_type = client.get_device_type()
            platform = get_platform_module(device_type)
            commands = platform.get_config_commands(intent, params)

            config_result = client.execute_config(commands)
            if config_result.success:
                config_result.formatted_output = format_output(
                    config_result.output, "configure"
                )

            return ExecutionResult(
                success=config_result.success,
                device_info=device_type,
                results=[config_result],
                error=config_result.error,
            )

    except CiscoSSHConnectionError as exc:
        return ExecutionResult(
            success=False,
            error=str(exc),
        )
