"""
VirusTotal 報告產生器。

提供三種輸出型式並以 write_report() 統一處理輸出路徑與檔案寫出：
- render_html()：以 Jinja2 模板渲染 HTML 字串。
- render_pdf()：以 weasyprint 由 HTML 轉出 PDF（延遲匯入）。
- build_summary()：產生純文字（zh-TW）摘要，適合印在終端機。

採 scripts/ 扁平匯入慣例（from models import ...）。
"""

from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from models import ReportData, verdict_label

# 模板所在目錄
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# 當 out_path 指向目錄時採用的預設檔名基底
DEFAULT_REPORT_BASENAME = "vt-report"


def render_html(report: ReportData) -> str:
    """以 Jinja2 模板 report.html.j2 渲染報告 HTML，回傳 HTML 字串。"""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")
    return template.render(report=report)


def render_pdf(html_str: str, out_path: str) -> str:
    """
    將 HTML 字串轉為 PDF 並寫至 out_path，回傳實際輸出路徑。

    weasyprint 於函式內部延遲匯入：僅在真正需要產生 PDF 時才載入，
    避免未安裝該套件（及其原生相依）時影響 HTML 或摘要輸出。
    """
    try:
        from weasyprint import HTML
    except ImportError as exc:  # pragma: no cover - 視執行環境是否已安裝而定
        raise RuntimeError(
            "產生 PDF 需要 weasyprint 套件。請先執行 `pip install weasyprint`，"
            "並安裝其原生相依 pango / cairo："
            "macOS 可用 `brew install pango`；"
            "Debian/Ubuntu 可用 "
            "`apt install libpango-1.0-0 libpangocairo-1.0-0 libcairo2`。"
        ) from exc

    HTML(string=html_str).write_pdf(out_path)
    return out_path


def build_summary(report: ReportData) -> str:
    """
    產生純文字（zh-TW）摘要。

    內容包含產生時間、總體判定、各判定數量，以及逐筆目標的
    型別/值、判定標籤、（若有）引擎統計的 malicious/total 與（若有）錯誤訊息。
    """
    lines: list[str] = []
    lines.append("=== VirusTotal 掃描報告 ===")
    lines.append(f"產生時間：{report.generated_at}")
    lines.append(f"總體判定：{report.summary_verdict_label}")

    # 各判定數量（依判定代碼轉為中文標籤）
    count_str = "、".join(f"{verdict_label(code)} {num}" for code, num in report.counts.items())
    lines.append(f"各判定數量：{count_str}")
    lines.append(f"目標總數：{len(report.results)}")
    lines.append("")
    lines.append("逐筆結果：")

    for idx, r in enumerate(report.results, start=1):
        lines.append(f"  {idx}. [{r.target.type}] {r.target.value} → {r.verdict_label}")
        if r.stats is not None:
            lines.append(f"      引擎判定：惡意 {r.stats.malicious} / 總計 {r.stats.total}")
        if r.error:
            lines.append(f"      錯誤：{r.error}")

    return "\n".join(lines)


def _resolve_base_path(out_path: str) -> Path:
    """
    依 out_path 推導報告檔名基底（不含副檔名）。

    - 若 out_path 以路徑分隔符結尾或指向既有目錄：於該目錄內採用預設檔名基底。
    - 否則：以 out_path 去除副檔名後作為基底。
    """
    is_dir_like = out_path.endswith(("/", os.sep)) or Path(out_path).is_dir()
    if is_dir_like:
        return Path(out_path) / DEFAULT_REPORT_BASENAME
    # 去除單一副檔名作為基底（例：/tmp/foo.pdf → /tmp/foo）
    return Path(out_path).with_suffix("")


def write_report(report: ReportData, fmt: str, out_path: str) -> list[str]:
    """
    依 fmt 產生報告檔並回傳實際寫出的檔案路徑清單。

    參數：
    - fmt：輸出格式，須為 "html"、"pdf" 或 "both"，其餘值丟出 ValueError。
    - out_path：可為目錄（於其中使用預設檔名 vt-report）或檔名基底。

    產出檔名為 `<base>.report.html` 與/或 `<base>.report.pdf`；
    不存在的父目錄會自動建立。
    """
    valid_formats = {"html", "pdf", "both"}
    if fmt not in valid_formats:
        raise ValueError(f"fmt 必須為 {sorted(valid_formats)} 之一，收到 '{fmt}'")

    base = _resolve_base_path(out_path)
    # 確保輸出目錄存在
    base.parent.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    html_str: str | None = None

    if fmt in ("html", "both"):
        html_str = render_html(report)
        html_path = base.with_name(f"{base.name}.report.html")
        html_path.write_text(html_str, encoding="utf-8")
        written.append(str(html_path))

    if fmt in ("pdf", "both"):
        # 重用已渲染的 HTML；若尚未渲染（fmt="pdf"）則現在渲染
        if html_str is None:
            html_str = render_html(report)
        pdf_path = base.with_name(f"{base.name}.report.pdf")
        render_pdf(html_str, str(pdf_path))
        written.append(str(pdf_path))

    return written
