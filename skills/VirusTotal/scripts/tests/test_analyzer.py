"""analyzer.py 的單元測試：以 MagicMock 注入 client，不連網。"""

from __future__ import annotations

from unittest.mock import MagicMock

from analyzer import (
    analyze_domain,
    analyze_file,
    analyze_hash,
    analyze_ip,
    analyze_url,
    build_report_data,
    compute_verdict,
    summarize_verdict,
)
from models import (
    VERDICT_HARMLESS,
    VERDICT_MALICIOUS,
    VERDICT_SUSPICIOUS,
    VERDICT_UNKNOWN,
    AnalysisStats,
    ScanResult,
    ScanTarget,
)
from vt_client import VTNotFoundError

# ---------------------------------------------------------------------------
# 共用測試資料
# ---------------------------------------------------------------------------
_OBJECT_ATTRS = {
    "last_analysis_stats": {"malicious": 3, "suspicious": 0, "harmless": 60, "undetected": 5, "timeout": 0},
    "last_analysis_results": {
        "ClamAV": {"category": "malicious", "result": "Win.Trojan"},
        "Kaspersky": {"category": "harmless", "result": None},
    },
}
_ANALYSIS = {
    "data": {
        "attributes": {
            "status": "completed",
            "stats": {"malicious": 1, "suspicious": 0, "harmless": 70, "undetected": 2, "timeout": 0},
            "results": {"ESET": {"category": "malicious", "result": "Eicar"}},
        }
    },
    "meta": {"file_info": {"sha256": "deadbeef"}},
}


# ---------------------------------------------------------------------------
# compute_verdict / summarize_verdict
# ---------------------------------------------------------------------------
class TestComputeVerdict:
    def test_malicious(self):
        assert compute_verdict(AnalysisStats(malicious=1)) == VERDICT_MALICIOUS

    def test_suspicious(self):
        assert compute_verdict(AnalysisStats(suspicious=2)) == VERDICT_SUSPICIOUS

    def test_harmless(self):
        assert compute_verdict(AnalysisStats(harmless=50)) == VERDICT_HARMLESS

    def test_unknown(self):
        assert compute_verdict(AnalysisStats()) == VERDICT_UNKNOWN


def test_summarize_verdict_picks_worst():
    results = [
        ScanResult(target=ScanTarget(type="domain", value="a"), verdict=VERDICT_HARMLESS),
        ScanResult(target=ScanTarget(type="domain", value="b"), verdict=VERDICT_MALICIOUS),
        ScanResult(target=ScanTarget(type="domain", value="c"), verdict=VERDICT_SUSPICIOUS),
    ]
    assert summarize_verdict(results) == VERDICT_MALICIOUS


def test_build_report_data():
    results = [ScanResult(target=ScanTarget(type="ip", value="1.1.1.1"), verdict=VERDICT_HARMLESS)]
    report = build_report_data(results, generated_at="2026-01-01 00:00:00")
    assert report.generated_at == "2026-01-01 00:00:00"
    assert report.summary_verdict == VERDICT_HARMLESS


# ---------------------------------------------------------------------------
# 物件型查詢（domain / ip / hash）
# ---------------------------------------------------------------------------
class TestAnalyzeObject:
    def test_analyze_domain(self):
        client = MagicMock()
        client.get_domain.return_value = {"data": {"attributes": _OBJECT_ATTRS}}
        result = analyze_domain(client, "example.com")
        assert result.success is True
        assert result.verdict == VERDICT_MALICIOUS
        assert result.stats.malicious == 3
        assert result.engines["ClamAV"]["result"] == "Win.Trojan"
        assert result.permalink.endswith("/domain/example.com")

    def test_analyze_ip(self):
        client = MagicMock()
        client.get_ip.return_value = {"data": {"attributes": _OBJECT_ATTRS}}
        result = analyze_ip(client, "8.8.8.8")
        assert result.permalink.endswith("/ip-address/8.8.8.8")
        assert result.verdict == VERDICT_MALICIOUS

    def test_analyze_hash(self):
        client = MagicMock()
        client.get_file.return_value = {"data": {"attributes": _OBJECT_ATTRS}}
        result = analyze_hash(client, "abc123")
        assert result.permalink.endswith("/file/abc123")
        assert result.stats.total == 68

    def test_error_becomes_result_error(self):
        client = MagicMock()
        client.get_file.side_effect = VTNotFoundError("找不到")
        result = analyze_hash(client, "unknownhash")
        assert result.success is False
        assert "找不到" in result.error
        assert result.verdict == VERDICT_UNKNOWN


# ---------------------------------------------------------------------------
# 送掃型（file / url）
# ---------------------------------------------------------------------------
class TestAnalyzeScan:
    def test_analyze_file(self, tmp_path):
        sample = tmp_path / "sample.bin"
        sample.write_bytes(b"hello")
        client = MagicMock()
        client.scan_file.return_value = "analysis-1"
        client.wait_for_analysis.return_value = _ANALYSIS
        result = analyze_file(client, str(sample))
        assert result.success is True
        assert result.verdict == VERDICT_MALICIOUS
        assert result.target.size == 5
        assert result.permalink.endswith("/file/deadbeef")
        assert result.engines["ESET"]["result"] == "Eicar"
        client.scan_file.assert_called_once_with(str(sample))

    def test_analyze_url(self):
        client = MagicMock()
        client.scan_url.return_value = "analysis-2"
        client.wait_for_analysis.return_value = _ANALYSIS
        client.url_to_id.return_value = "urlid123"
        result = analyze_url(client, "https://example.com")
        assert result.verdict == VERDICT_MALICIOUS
        assert result.permalink.endswith("/url/urlid123")
