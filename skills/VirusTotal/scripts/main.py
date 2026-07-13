#!/usr/bin/env python3
"""
VirusTotal 掃描與報告 CLI。

子指令：
- scan-file / scan-url / scan-domain / scan-ip / scan-hash：掃描或查詢單一目標。
- report：讀取先前 --json-output 存下的 JSON 結果，合併產生報告。

共用選項：--format、--output、--json-output、--timeout、--yes、--verbose。
採 scripts/ 扁平匯入慣例（from analyzer import ...）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from analyzer import (
    analyze_domain,
    analyze_file,
    analyze_hash,
    analyze_ip,
    analyze_url,
    build_report_data,
)
from config import POLL_TIMEOUT, ConfigError, get_api_key
from models import ReportData, ScanResult
from reporter import build_summary, write_report
from vt_client import VirusTotalClient

__version__ = "0.1.0"


# ---------------------------------------------------------------------------
# 共用工具
# ---------------------------------------------------------------------------
def _report_options(func):
    """為子指令附加共用選項（由下而上套用，故宣告順序與顯示相反）。"""
    func = click.option("--verbose", is_flag=True, default=False, help="顯示除錯訊息")(func)
    func = click.option("--yes", "-y", is_flag=True, default=False, help="略過確認（非互動環境自動略過）")(func)
    func = click.option("--timeout", type=int, default=POLL_TIMEOUT, show_default=True, help="分析輪詢逾時（秒）")(func)
    func = click.option("--json-output", is_flag=True, default=False, help="以 JSON 輸出結果")(func)
    func = click.option(
        "--output", "-o", default="./output/", show_default=True, help="報告輸出路徑（檔名基底或目錄）"
    )(func)
    func = click.option(
        "--format",
        "fmt",
        type=click.Choice(["html", "pdf", "both"], case_sensitive=False),
        default=None,
        help="產生報告格式（省略則只輸出摘要）",
    )(func)
    return func


def _error(message: str, json_output: bool) -> None:
    """輸出錯誤訊息至 stderr。"""
    if json_output:
        click.echo(json.dumps({"success": False, "error": message}, ensure_ascii=False), err=True)
    else:
        click.echo(f"❌ {message}", err=True)


def _make_client(json_output: bool) -> VirusTotalClient:
    """建立 VirusTotalClient；缺少金鑰時輸出錯誤並結束。"""
    try:
        api_key = get_api_key()
    except ConfigError as exc:
        _error(str(exc), json_output)
        sys.exit(1)
    return VirusTotalClient(api_key)


def _finish(results: list[ScanResult], fmt: str | None, output: str, json_output: bool) -> None:
    """輸出摘要或 JSON，並在指定 --format 時產生報告檔。"""
    report: ReportData = build_report_data(results)
    if json_output:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(build_summary(report))
    if fmt:
        try:
            written = write_report(report, fmt.lower(), output)
        except (OSError, ValueError, RuntimeError) as exc:
            _error(f"產生報告失敗：{exc}", json_output)
            sys.exit(1)
        for path in written:
            click.echo(f"✅ 已產生報告：{path}")


def _execute_single(result: ScanResult, fmt: str | None, output: str, json_output: bool) -> None:
    """收斂單一 ScanResult 的輸出流程。"""
    _finish([result], fmt, output, json_output)


# ---------------------------------------------------------------------------
# CLI 定義
# ---------------------------------------------------------------------------
@click.group()
@click.version_option(__version__, prog_name="virustotal")
def cli() -> None:
    """VirusTotal 掃描與報告工具。"""


@cli.command("scan-file")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@_report_options
def scan_file_cmd(path, fmt, output, json_output, timeout, yes, verbose):
    """掃描本機檔案（會上傳至 VirusTotal）。"""
    # 上傳等同公開分享，於互動環境先確認。
    if (
        not yes
        and not json_output
        and sys.stdin.isatty()
        and not click.confirm(f"將上傳檔案「{path}」至 VirusTotal（等同公開分享），是否繼續？")
    ):
        click.echo("已取消。")
        return
    client = _make_client(json_output)
    result = analyze_file(client, path, timeout=timeout)
    _execute_single(result, fmt, output, json_output)


@cli.command("scan-url")
@click.argument("url")
@_report_options
def scan_url_cmd(url, fmt, output, json_output, timeout, yes, verbose):
    """掃描網址。"""
    client = _make_client(json_output)
    result = analyze_url(client, url, timeout=timeout)
    _execute_single(result, fmt, output, json_output)


@cli.command("scan-domain")
@click.argument("domain")
@_report_options
def scan_domain_cmd(domain, fmt, output, json_output, timeout, yes, verbose):
    """查詢網域信譽。"""
    client = _make_client(json_output)
    result = analyze_domain(client, domain)
    _execute_single(result, fmt, output, json_output)


@cli.command("scan-ip")
@click.argument("ip")
@_report_options
def scan_ip_cmd(ip, fmt, output, json_output, timeout, yes, verbose):
    """查詢 IP 位址信譽。"""
    client = _make_client(json_output)
    result = analyze_ip(client, ip)
    _execute_single(result, fmt, output, json_output)


@cli.command("scan-hash")
@click.argument("file_hash")
@_report_options
def scan_hash_cmd(file_hash, fmt, output, json_output, timeout, yes, verbose):
    """以既有檔案雜湊（MD5/SHA-1/SHA-256）查詢報告。"""
    client = _make_client(json_output)
    result = analyze_hash(client, file_hash)
    _execute_single(result, fmt, output, json_output)


@cli.command("report")
@click.option(
    "--input",
    "-i",
    "inputs",
    multiple=True,
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="先前以 --json-output 存下的 JSON 結果檔（可多次指定）",
)
@_report_options
def report_cmd(inputs, fmt, output, json_output, timeout, yes, verbose):
    """讀取多個 JSON 結果檔，合併產生報告。"""
    results: list[ScanResult] = []
    for path in inputs:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            _error(f"無法讀取或解析 JSON：{path}（{exc}）", json_output)
            sys.exit(1)
        results.extend(_results_from_json(data))

    if not results:
        _error("找不到可用的掃描結果。", json_output)
        sys.exit(1)

    # report 子指令以產生報告為目的：未指定格式時預設 both。
    _finish(results, (fmt or "both").lower(), output, json_output)


def _results_from_json(data) -> list[ScanResult]:
    """由 JSON（單筆結果 / 結果清單 / ReportData 匯出）還原 ScanResult 清單。"""
    if isinstance(data, list):
        return [ScanResult.from_dict(item) for item in data]
    if isinstance(data, dict) and "results" in data:
        return [ScanResult.from_dict(item) for item in data["results"]]
    if isinstance(data, dict):
        return [ScanResult.from_dict(data)]
    return []


if __name__ == "__main__":
    cli()
