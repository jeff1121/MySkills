"""
Cisco Configer CLI 進入點。
"""
import json
import sys

import click

from models import ConnectionInfo, __version__
from executor import run_query, run_config


@click.group()
@click.version_option(version=__version__)
def cli():
    """Cisco Configer — Cisco 網路設備查詢與設定工具。"""
    pass


@cli.command()
@click.option(
    "--host", prompt="HostAddr", help="設備 IP 位址或主機名稱。"
)
@click.option(
    "--username", prompt="HostUser", help="SSH 登入帳號。"
)
@click.option(
    "--password",
    prompt="HostPass",
    hide_input=True,
    help="SSH 登入密碼。",
)
@click.option(
    "--device-type",
    default=None,
    type=click.Choice(
        ["cisco_ios", "cisco_nxos", "cisco_asa", "cisco_xr"],
        case_sensitive=False,
    ),
    help="設備類型（預設自動偵測）。",
)
@click.option(
    "--enable-password",
    default=None,
    hide_input=True,
    help="Enable 模式密碼。",
)
@click.option("--port", default=22, type=int, help="SSH 連接埠。")
@click.option(
    "--intent", prompt="查詢意圖", help="查詢意圖（如 interface、vlan、routing）。"
)
@click.option(
    "--json-output", is_flag=True, default=False, help="以 JSON 格式輸出。"
)
@click.option(
    "-y", "--yes", is_flag=True, default=False, help="跳過確認。"
)
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="顯示詳細資訊。"
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="預覽模式：顯示將執行的指令但不連線設備。"
)
def query(
    host, username, password, device_type, enable_password, port,
    intent, json_output, yes, verbose, dry_run,
):
    """查詢 Cisco 設備資訊。"""
    connection = ConnectionInfo(
        host=host,
        username=username,
        password=password,
        device_type=device_type,
        enable_password=enable_password,
        port=port,
    )

    if dry_run:
        _show_dry_run("query", connection, device_type, intent, json_output)
        sys.exit(0)

    # 非互動式終端（agent / pipeline）自動跳過確認
    if not yes and not sys.stdin.isatty():
        yes = True

    if not yes:
        click.echo(f"\n{'='*50}")
        click.echo("連線摘要")
        click.echo(f"{'='*50}")
        click.echo(f"  目標設備：{connection}")
        click.echo(f"  設備類型：{device_type or '自動偵測'}")
        click.echo(f"  查詢意圖：{intent}")
        click.echo(f"{'='*50}\n")
        if not click.confirm("確認執行？"):
            click.echo("已取消。")
            sys.exit(0)

    if verbose:
        click.echo(f"正在連線至 {connection} ...")

    result = run_query(connection, intent)

    if json_output:
        click.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        if result.success:
            click.echo(f"\n✅ 查詢成功（設備類型：{result.device_info}）\n")
            for cmd_result in result.results:
                click.echo(f"--- {cmd_result.command} ---")
                click.echo(cmd_result.formatted_output)
                click.echo()
        else:
            click.echo(f"\n❌ 查詢失敗：{result.error}\n", err=True)

    sys.exit(0 if result.success else 1)


@cli.command()
@click.option(
    "--host", prompt="HostAddr", help="設備 IP 位址或主機名稱。"
)
@click.option(
    "--username", prompt="HostUser", help="SSH 登入帳號。"
)
@click.option(
    "--password",
    prompt="HostPass",
    hide_input=True,
    help="SSH 登入密碼。",
)
@click.option(
    "--device-type",
    default=None,
    type=click.Choice(
        ["cisco_ios", "cisco_nxos", "cisco_asa", "cisco_xr"],
        case_sensitive=False,
    ),
    help="設備類型（預設自動偵測）。",
)
@click.option(
    "--enable-password",
    default=None,
    hide_input=True,
    help="Enable 模式密碼。",
)
@click.option("--port", default=22, type=int, help="SSH 連接埠。")
@click.option(
    "--intent", prompt="設定意圖", help="設定意圖（如 vlan、interface、hostname）。"
)
@click.option(
    "--params",
    default="{}",
    help="設定參數（JSON 格式）。",
)
@click.option(
    "--json-output", is_flag=True, default=False, help="以 JSON 格式輸出。"
)
@click.option(
    "-y", "--yes", is_flag=True, default=False, help="跳過確認。"
)
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="顯示詳細資訊。"
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="預覽模式：顯示將執行的指令但不連線設備。"
)
def config(
    host, username, password, device_type, enable_password, port,
    intent, params, json_output, yes, verbose, dry_run,
):
    """設定 Cisco 設備組態。"""
    connection = ConnectionInfo(
        host=host,
        username=username,
        password=password,
        device_type=device_type,
        enable_password=enable_password,
        port=port,
    )

    try:
        config_params = json.loads(params)
    except json.JSONDecodeError:
        click.echo("❌ --params 格式錯誤，必須為有效的 JSON 字串。", err=True)
        sys.exit(1)

    if dry_run:
        _show_dry_run("config", connection, device_type, intent, json_output, config_params)
        sys.exit(0)

    # 非互動式終端（agent / pipeline）自動跳過確認
    if not yes and not sys.stdin.isatty():
        yes = True

    if not yes:
        click.echo(f"\n{'='*50}")
        click.echo("設定摘要")
        click.echo(f"{'='*50}")
        click.echo(f"  目標設備：{connection}")
        click.echo(f"  設備類型：{device_type or '自動偵測'}")
        click.echo(f"  設定意圖：{intent}")
        click.echo(f"  設定參數：{json.dumps(config_params, ensure_ascii=False)}")
        click.echo(f"{'='*50}\n")
        if not click.confirm("確認執行？（此操作將變更設備組態）"):
            click.echo("已取消。")
            sys.exit(0)

    if verbose:
        click.echo(f"正在連線至 {connection} ...")

    result = run_config(connection, intent, config_params)

    if json_output:
        click.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        if result.success:
            click.echo(f"\n✅ 設定成功（設備類型：{result.device_info}）\n")
            for cmd_result in result.results:
                click.echo(f"--- 執行的指令 ---")
                click.echo(cmd_result.formatted_output)
                click.echo()
        else:
            click.echo(f"\n❌ 設定失敗：{result.error}\n", err=True)

    sys.exit(0 if result.success else 1)


def _show_dry_run(mode, connection, device_type, intent, json_output, config_params=None):
    """顯示 dry-run 預覽。"""
    info = {
        "dry_run": True,
        "mode": mode,
        "target": str(connection),
        "device_type": device_type or "auto-detect",
        "intent": intent,
    }
    if config_params:
        info["config_params"] = config_params

    if json_output:
        click.echo(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        click.echo(f"\n🔍 Dry-run 模式 — 以下為將執行的操作：\n")
        click.echo(f"  模式：{'查詢' if mode == 'query' else '設定'}")
        click.echo(f"  目標設備：{connection}")
        click.echo(f"  設備類型：{device_type or '自動偵測'}")
        click.echo(f"  意圖：{intent}")
        if config_params:
            click.echo(f"  設定參數：{json.dumps(config_params, ensure_ascii=False)}")
        click.echo(f"\n  ⚠️  不會實際連線設備。移除 --dry-run 以執行。")


if __name__ == "__main__":
    cli()
