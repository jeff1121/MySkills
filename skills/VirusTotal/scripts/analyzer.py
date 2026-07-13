"""
VirusTotal 掃描編排與判定邏輯。

將 CLI 參數轉為 `ScanTarget`，透過 `VirusTotalClient` 送掃或查詢，解析
VirusTotal 回應中的統計與引擎明細，計算判定（verdict），並彙整為 `ReportData`。
所有 `VTError` 皆會被攔截並轉存為 `ScanResult.error`，避免單一目標失敗中斷整體流程。

採 scripts/ 扁平匯入慣例（from models import ...）。
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from datetime import datetime

from config import POLL_INTERVAL, POLL_TIMEOUT
from models import (
    VERDICT_HARMLESS,
    VERDICT_MALICIOUS,
    VERDICT_SUSPICIOUS,
    VERDICT_UNKNOWN,
    AnalysisStats,
    ReportData,
    ScanResult,
    ScanTarget,
)
from vt_client import VirusTotalClient, VTError

# VirusTotal GUI 基底位址（用於組出 permalink）
GUI_BASE_URL = "https://www.virustotal.com/gui"

# 判定嚴重度排序（數字越大越嚴重），用於彙整多筆結果的總體判定
_VERDICT_SEVERITY = {
    VERDICT_MALICIOUS: 3,
    VERDICT_SUSPICIOUS: 2,
    VERDICT_HARMLESS: 1,
    VERDICT_UNKNOWN: 0,
}


def compute_verdict(stats: AnalysisStats) -> str:
    """依統計計算判定：有 malicious→惡意；有 suspicious→可疑；有回報→安全；否則未知。"""
    if stats.malicious > 0:
        return VERDICT_MALICIOUS
    if stats.suspicious > 0:
        return VERDICT_SUSPICIOUS
    if stats.total > 0:
        return VERDICT_HARMLESS
    return VERDICT_UNKNOWN


def _extract_engines(results: dict | None) -> dict:
    """由 last_analysis_results / results 取出引擎明細：{引擎名: {category, result}}。"""
    engines: dict = {}
    for name, info in (results or {}).items():
        if not isinstance(info, dict):
            continue
        engines[name] = {
            "category": info.get("category"),
            "result": info.get("result"),
        }
    return engines


def _parse_object_attributes(attributes: dict) -> tuple[AnalysisStats, dict]:
    """由物件報告（file / domain / ip 物件）的 attributes 取 stats 與引擎明細。"""
    stats = AnalysisStats.from_dict(attributes.get("last_analysis_stats"))
    engines = _extract_engines(attributes.get("last_analysis_results"))
    return stats, engines


def _parse_analysis_attributes(attributes: dict) -> tuple[AnalysisStats, dict]:
    """由分析結果（/analyses/{id}）的 attributes 取 stats 與引擎明細。"""
    stats = AnalysisStats.from_dict(attributes.get("stats"))
    engines = _extract_engines(attributes.get("results"))
    return stats, engines


def _build_result(
    target: ScanTarget,
    stats: AnalysisStats,
    engines: dict,
    permalink: str | None,
    raw: dict,
) -> ScanResult:
    """組成成功的 ScanResult（自動計算 verdict）。"""
    return ScanResult(
        target=target,
        stats=stats,
        verdict=compute_verdict(stats),
        engines=engines,
        permalink=permalink,
        raw=raw,
    )


def analyze_domain(client: VirusTotalClient, domain: str) -> ScanResult:
    """查詢網域信譽並組成 ScanResult。"""
    target = ScanTarget(type="domain", value=domain)
    try:
        resp = client.get_domain(domain)
        attributes = resp.get("data", {}).get("attributes", {})
        stats, engines = _parse_object_attributes(attributes)
        permalink = f"{GUI_BASE_URL}/domain/{domain}"
        return _build_result(target, stats, engines, permalink, resp)
    except VTError as exc:
        return ScanResult(target=target, error=str(exc))


def analyze_ip(client: VirusTotalClient, ip: str) -> ScanResult:
    """查詢 IP 信譽並組成 ScanResult。"""
    target = ScanTarget(type="ip", value=ip)
    try:
        resp = client.get_ip(ip)
        attributes = resp.get("data", {}).get("attributes", {})
        stats, engines = _parse_object_attributes(attributes)
        permalink = f"{GUI_BASE_URL}/ip-address/{ip}"
        return _build_result(target, stats, engines, permalink, resp)
    except VTError as exc:
        return ScanResult(target=target, error=str(exc))


def analyze_hash(client: VirusTotalClient, file_hash: str) -> ScanResult:
    """以既有檔案雜湊查詢報告並組成 ScanResult。"""
    target = ScanTarget(type="hash", value=file_hash)
    try:
        resp = client.get_file(file_hash)
        attributes = resp.get("data", {}).get("attributes", {})
        stats, engines = _parse_object_attributes(attributes)
        permalink = f"{GUI_BASE_URL}/file/{file_hash}"
        return _build_result(target, stats, engines, permalink, resp)
    except VTError as exc:
        return ScanResult(target=target, error=str(exc))


def analyze_file(
    client: VirusTotalClient,
    path: str,
    interval: int = POLL_INTERVAL,
    timeout: int = POLL_TIMEOUT,
) -> ScanResult:
    """上傳本機檔案送掃、輪詢完成後解析結果並組成 ScanResult。"""
    size: int | None = None
    try:
        size = os.path.getsize(path)
    except OSError:
        size = None
    target = ScanTarget(type="file", value=path, size=size)
    try:
        analysis_id = client.scan_file(path)
        analysis = client.wait_for_analysis(analysis_id, interval=interval, timeout=timeout)
        attributes = analysis.get("data", {}).get("attributes", {})
        stats, engines = _parse_analysis_attributes(attributes)
        sha256 = analysis.get("meta", {}).get("file_info", {}).get("sha256")
        permalink = f"{GUI_BASE_URL}/file/{sha256}" if sha256 else None
        return _build_result(target, stats, engines, permalink, analysis)
    except VTError as exc:
        return ScanResult(target=target, error=str(exc))


def analyze_url(
    client: VirusTotalClient,
    url: str,
    interval: int = POLL_INTERVAL,
    timeout: int = POLL_TIMEOUT,
) -> ScanResult:
    """提交 URL 送掃、輪詢完成後解析結果並組成 ScanResult。"""
    target = ScanTarget(type="url", value=url)
    try:
        analysis_id = client.scan_url(url)
        analysis = client.wait_for_analysis(analysis_id, interval=interval, timeout=timeout)
        attributes = analysis.get("data", {}).get("attributes", {})
        stats, engines = _parse_analysis_attributes(attributes)
        permalink = f"{GUI_BASE_URL}/url/{client.url_to_id(url)}"
        return _build_result(target, stats, engines, permalink, analysis)
    except VTError as exc:
        return ScanResult(target=target, error=str(exc))


def analyze_target(
    client: VirusTotalClient,
    target_type: str,
    value: str,
    interval: int = POLL_INTERVAL,
    timeout: int = POLL_TIMEOUT,
) -> ScanResult:
    """依目標型別分派到對應的分析函式。"""
    if target_type == "file":
        return analyze_file(client, value, interval, timeout)
    if target_type == "url":
        return analyze_url(client, value, interval, timeout)
    if target_type == "domain":
        return analyze_domain(client, value)
    if target_type == "ip":
        return analyze_ip(client, value)
    if target_type == "hash":
        return analyze_hash(client, value)
    raise ValueError(f"未知的目標型別：{target_type}")


def summarize_verdict(results: Iterable[ScanResult]) -> str:
    """彙整多筆結果的總體判定：取最嚴重者。"""
    worst = VERDICT_UNKNOWN
    for result in results:
        if _VERDICT_SEVERITY.get(result.verdict, 0) > _VERDICT_SEVERITY.get(worst, 0):
            worst = result.verdict
    return worst


def build_report_data(
    results: Iterable[ScanResult],
    generated_at: str | None = None,
) -> ReportData:
    """由多筆 ScanResult 建立 ReportData（含產生時間與總體判定）。"""
    results_list = list(results)
    generated_at = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ReportData(
        results=results_list,
        generated_at=generated_at,
        summary_verdict=summarize_verdict(results_list),
    )
