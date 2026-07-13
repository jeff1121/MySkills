"""models.py 的單元測試：驗證、序列化與往返還原。"""

from __future__ import annotations

from models import (
    VERDICT_HARMLESS,
    VERDICT_MALICIOUS,
    VERDICT_UNKNOWN,
    AnalysisStats,
    ReportData,
    ScanResult,
    ScanTarget,
    verdict_label,
)


class TestScanTarget:
    def test_validate_ok(self):
        assert ScanTarget(type="domain", value="example.com").validate() == []

    def test_validate_invalid_type(self):
        errors = ScanTarget(type="bogus", value="x").validate()
        assert any("type must be one of" in e for e in errors)

    def test_validate_empty_value(self):
        errors = ScanTarget(type="url", value="   ").validate()
        assert any("value is required" in e for e in errors)

    def test_validate_negative_size(self):
        errors = ScanTarget(type="file", value="a", size=-1).validate()
        assert any("size must be >= 0" in e for e in errors)

    def test_to_from_dict_roundtrip(self):
        target = ScanTarget(type="file", value="/tmp/a.bin", size=123)
        assert ScanTarget.from_dict(target.to_dict()) == target

    def test_to_dict_omits_none_size(self):
        assert "size" not in ScanTarget(type="ip", value="1.1.1.1").to_dict()


class TestAnalysisStats:
    def test_from_dict_and_total(self):
        stats = AnalysisStats.from_dict(
            {"malicious": 2, "suspicious": 1, "harmless": 10, "undetected": 5, "timeout": 0}
        )
        assert stats.total == 18
        assert stats.malicious == 2

    def test_from_dict_handles_none(self):
        stats = AnalysisStats.from_dict(None)
        assert stats.total == 0

    def test_to_dict_includes_total(self):
        data = AnalysisStats(malicious=1).to_dict()
        assert data["total"] == 1
        assert data["malicious"] == 1


class TestScanResult:
    def test_success_property(self):
        assert ScanResult(target=ScanTarget(type="domain", value="a")).success is True
        assert ScanResult(target=ScanTarget(type="domain", value="a"), error="boom").success is False

    def test_verdict_label(self):
        result = ScanResult(target=ScanTarget(type="domain", value="a"), verdict=VERDICT_MALICIOUS)
        assert result.verdict_label == "惡意"

    def test_to_dict_contains_fields(self):
        result = ScanResult(
            target=ScanTarget(type="domain", value="a"),
            stats=AnalysisStats(malicious=1),
            verdict=VERDICT_MALICIOUS,
            engines={"ClamAV": {"category": "malicious", "result": "Win.Test"}},
            permalink="https://vt/x",
        )
        data = result.to_dict()
        assert data["verdict"] == VERDICT_MALICIOUS
        assert data["verdict_label"] == "惡意"
        assert data["success"] is True
        assert data["permalink"] == "https://vt/x"
        assert "engines" in data

    def test_from_dict_roundtrip(self):
        result = ScanResult(
            target=ScanTarget(type="hash", value="abc"),
            stats=AnalysisStats(harmless=70),
            verdict=VERDICT_HARMLESS,
            permalink="https://vt/y",
        )
        restored = ScanResult.from_dict(result.to_dict())
        assert restored.target == result.target
        assert restored.verdict == VERDICT_HARMLESS
        assert restored.stats is not None
        assert restored.stats.harmless == 70


class TestReportData:
    def test_counts_and_labels(self):
        report = ReportData(
            results=[
                ScanResult(target=ScanTarget(type="domain", value="a"), verdict=VERDICT_MALICIOUS),
                ScanResult(target=ScanTarget(type="domain", value="b"), verdict=VERDICT_HARMLESS),
                ScanResult(target=ScanTarget(type="domain", value="c"), verdict=VERDICT_HARMLESS),
            ],
            generated_at="2026-01-01 00:00:00",
            summary_verdict=VERDICT_MALICIOUS,
        )
        assert report.counts[VERDICT_HARMLESS] == 2
        assert report.counts[VERDICT_MALICIOUS] == 1
        assert report.summary_verdict_label == "惡意"

    def test_to_dict(self):
        report = ReportData(generated_at="t", summary_verdict=VERDICT_UNKNOWN)
        data = report.to_dict()
        assert data["generated_at"] == "t"
        assert data["summary_verdict_label"] == "未知"
        assert data["results"] == []


def test_verdict_label_fallback():
    assert verdict_label("nonsense") == "未知"
