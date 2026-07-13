"""
reporter 模組單元測試。

以 tests/conftest.py 設定的 sys.path 進行扁平匯入（from reporter / from models）。
PDF 相關測試以 pytest.importorskip 保護，未安裝 weasyprint 時自動略過。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from models import (
    VERDICT_HARMLESS,
    VERDICT_MALICIOUS,
    AnalysisStats,
    ReportData,
    ScanResult,
    ScanTarget,
)
from reporter import build_summary, render_html, write_report

# 樣本中惡意目標的永久連結，供斷言重複使用
MALICIOUS_PERMALINK = "https://www.virustotal.com/gui/file/abc123deadbeef"


def _sample_report() -> ReportData:
    """建立含 2 筆結果的樣本報告：一筆惡意（完整資料）、一筆安全。"""
    malicious = ScanResult(
        target=ScanTarget(type="hash", value="abc123deadbeef"),
        stats=AnalysisStats(malicious=42, suspicious=3, harmless=10, undetected=5, timeout=1),
        verdict=VERDICT_MALICIOUS,
        engines={
            "EngineA": {"category": "malicious", "result": "Trojan.Generic"},
            "EngineB": {"category": "harmless", "result": None},
        },
        permalink=MALICIOUS_PERMALINK,
    )
    harmless = ScanResult(
        target=ScanTarget(type="domain", value="example.com"),
        stats=AnalysisStats(malicious=0, suspicious=0, harmless=70, undetected=18, timeout=0),
        verdict=VERDICT_HARMLESS,
        engines={"EngineC": {"category": "harmless", "result": "clean"}},
    )
    return ReportData(
        results=[malicious, harmless],
        generated_at="2026-07-13 10:30:00",
        summary_verdict=VERDICT_MALICIOUS,
    )


def test_render_html_contains_key_fields() -> None:
    """HTML 輸出應包含標題、目標值、判定標籤與永久連結。"""
    html = render_html(_sample_report())
    assert "VirusTotal 掃描報告" in html  # 報告標題
    assert "abc123deadbeef" in html  # 惡意目標值
    assert "example.com" in html  # 安全目標值
    assert "惡意" in html  # 惡意判定標籤
    assert "安全" in html  # 安全判定標籤
    assert MALICIOUS_PERMALINK in html  # 永久連結網址


def test_render_html_error_block() -> None:
    """含錯誤的結果應在 HTML 中呈現錯誤訊息。"""
    report = ReportData(
        results=[
            ScanResult(
                target=ScanTarget(type="ip", value="203.0.113.9"),
                error="超過 API 額度限制（429）",
            )
        ],
        generated_at="2026-07-13 11:00:00",
        summary_verdict=VERDICT_MALICIOUS,
    )
    html = render_html(report)
    assert "203.0.113.9" in html
    assert "超過 API 額度限制（429）" in html


def test_build_summary() -> None:
    """純文字摘要應包含總體判定與各目標資訊。"""
    summary = build_summary(_sample_report())
    assert "總體判定：惡意" in summary
    assert "abc123deadbeef" in summary
    assert "example.com" in summary
    # 惡意目標的引擎統計（malicious/total）
    assert "惡意 42 / 總計 61" in summary


def test_write_report_html(tmp_path: Path) -> None:
    """fmt=html 應寫出單一 .report.html 檔且非空。"""
    written = write_report(_sample_report(), "html", str(tmp_path))
    assert len(written) == 1

    html_path = Path(written[0])
    assert html_path.name.endswith(".report.html")
    assert html_path.exists()
    assert html_path.stat().st_size > 0


def test_write_report_pdf(tmp_path: Path) -> None:
    """fmt=pdf 應寫出 .report.pdf 檔且非空（未安裝 weasyprint 時略過）。"""
    pytest.importorskip("weasyprint")
    written = write_report(_sample_report(), "pdf", str(tmp_path))
    assert len(written) == 1

    pdf_path = Path(written[0])
    assert pdf_path.name.endswith(".report.pdf")
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_write_report_invalid_format() -> None:
    """不支援的格式（如 xml）應丟出 ValueError。"""
    with pytest.raises(ValueError):
        write_report(_sample_report(), "xml", "out")
