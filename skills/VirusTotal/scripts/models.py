"""
VirusTotal Skill 資料模型。

以純 dataclass 描述掃描目標、統計、單筆結果與整體報告資料；
每個模型皆提供 `validate()`（回傳錯誤字串清單）與 `to_dict()`（JSON 友善序列化）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

__version__ = "0.1.0"

# 合法的掃描目標類型
VALID_TARGET_TYPES = {"file", "url", "domain", "ip", "hash"}

# 判定代碼
VERDICT_MALICIOUS = "malicious"
VERDICT_SUSPICIOUS = "suspicious"
VERDICT_HARMLESS = "harmless"
VERDICT_UNKNOWN = "unknown"

# 判定代碼對應的繁體中文標籤（供報告與 CLI 顯示）
VERDICT_LABELS = {
    VERDICT_MALICIOUS: "惡意",
    VERDICT_SUSPICIOUS: "可疑",
    VERDICT_HARMLESS: "安全",
    VERDICT_UNKNOWN: "未知",
}


def verdict_label(verdict: str) -> str:
    """回傳判定代碼對應的繁體中文標籤。"""
    return VERDICT_LABELS.get(verdict, VERDICT_LABELS[VERDICT_UNKNOWN])


@dataclass
class ScanTarget:
    """掃描目標。"""

    type: str  # file / url / domain / ip / hash
    value: str
    size: int | None = None  # 檔案大小（bytes），僅 file 類型使用

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.type not in VALID_TARGET_TYPES:
            errors.append(f"type must be one of {sorted(VALID_TARGET_TYPES)}, got '{self.type}'")
        if not self.value or not self.value.strip():
            errors.append("target value is required")
        if self.size is not None and self.size < 0:
            errors.append("size must be >= 0")
        return errors

    def to_dict(self) -> dict:
        data: dict = {"type": self.type, "value": self.value}
        if self.size is not None:
            data["size"] = self.size
        return data

    @classmethod
    def from_dict(cls, data: dict) -> ScanTarget:
        """由 `to_dict()` 產生的 dict 還原實例。"""
        return cls(
            type=data.get("type", ""),
            value=data.get("value", ""),
            size=data.get("size"),
        )


@dataclass
class AnalysisStats:
    """各防毒引擎的判定統計。"""

    malicious: int = 0
    suspicious: int = 0
    harmless: int = 0
    undetected: int = 0
    timeout: int = 0

    @property
    def total(self) -> int:
        """有回報的引擎總數。"""
        return self.malicious + self.suspicious + self.harmless + self.undetected + self.timeout

    @classmethod
    def from_dict(cls, stats: dict | None) -> AnalysisStats:
        """由 VirusTotal 回傳的 stats 物件建立實例（缺欄位以 0 計）。"""
        stats = stats or {}
        return cls(
            malicious=int(stats.get("malicious", 0) or 0),
            suspicious=int(stats.get("suspicious", 0) or 0),
            harmless=int(stats.get("harmless", 0) or 0),
            undetected=int(stats.get("undetected", 0) or 0),
            timeout=int(stats.get("timeout", 0) or 0),
        )

    def to_dict(self) -> dict:
        return {
            "malicious": self.malicious,
            "suspicious": self.suspicious,
            "harmless": self.harmless,
            "undetected": self.undetected,
            "timeout": self.timeout,
            "total": self.total,
        }


@dataclass
class ScanResult:
    """單一目標的掃描結果。"""

    target: ScanTarget
    stats: AnalysisStats | None = None
    verdict: str = VERDICT_UNKNOWN
    engines: dict = field(default_factory=dict)
    permalink: str | None = None
    raw: dict = field(default_factory=dict)
    error: str | None = None

    @property
    def success(self) -> bool:
        """是否成功取得結果（無錯誤）。"""
        return self.error is None

    @property
    def verdict_label(self) -> str:
        return verdict_label(self.verdict)

    def to_dict(self) -> dict:
        data: dict = {
            "target": self.target.to_dict(),
            "verdict": self.verdict,
            "verdict_label": self.verdict_label,
            "success": self.success,
        }
        if self.stats is not None:
            data["stats"] = self.stats.to_dict()
        if self.engines:
            data["engines"] = self.engines
        if self.permalink:
            data["permalink"] = self.permalink
        if self.error:
            data["error"] = self.error
        return data

    @classmethod
    def from_dict(cls, data: dict) -> ScanResult:
        """由 `to_dict()` 產生的 dict 還原實例（供 report 子指令合併使用）。"""
        stats_data = data.get("stats")
        return cls(
            target=ScanTarget.from_dict(data.get("target", {})),
            stats=AnalysisStats.from_dict(stats_data) if stats_data is not None else None,
            verdict=data.get("verdict", VERDICT_UNKNOWN),
            engines=data.get("engines", {}) or {},
            permalink=data.get("permalink"),
            raw=data.get("raw", {}) or {},
            error=data.get("error"),
        )


@dataclass
class ReportData:
    """報告資料（彙整多筆掃描結果）。"""

    results: list[ScanResult] = field(default_factory=list)
    generated_at: str = ""
    summary_verdict: str = VERDICT_UNKNOWN

    @property
    def summary_verdict_label(self) -> str:
        return verdict_label(self.summary_verdict)

    @property
    def counts(self) -> dict:
        """各判定的目標數量統計。"""
        counts = {
            VERDICT_MALICIOUS: 0,
            VERDICT_SUSPICIOUS: 0,
            VERDICT_HARMLESS: 0,
            VERDICT_UNKNOWN: 0,
        }
        for result in self.results:
            counts[result.verdict] = counts.get(result.verdict, 0) + 1
        return counts

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "summary_verdict": self.summary_verdict,
            "summary_verdict_label": self.summary_verdict_label,
            "counts": self.counts,
            "results": [r.to_dict() for r in self.results],
        }
