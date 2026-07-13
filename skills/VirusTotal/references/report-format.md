# 報告格式與判定說明

本文件說明 VirusTotal skill 產生之報告的內容結構、判定對應與輸出慣例，作為離線 fallback 與版面參考。報告資料由 `models.ReportData` 彙整，經 `reporter.py` 渲染為文字摘要、HTML 與 PDF。

## 判定（verdict）代碼與中文標籤

每個掃描目標會依統計計算出一個判定代碼，對應固定的繁體中文標籤：

| 判定代碼 | 中文標籤 | 判定依據 |
|----------|----------|----------|
| `malicious` | 惡意 | `malicious > 0` |
| `suspicious` | 可疑 | `malicious == 0` 且 `suspicious > 0` |
| `harmless` | 安全 | 無引擎判為惡意或可疑 |
| `unknown` | 未知 | 查無分析結果、目標不存在或發生錯誤 |

判定優先序：**惡意 > 可疑 > 安全 > 未知**。整份報告的總體判定（`summary_verdict`）取所有目標中最嚴重者。

## 統計欄位（AnalysisStats）

對應 VirusTotal 的 `last_analysis_stats`，每個欄位為回報該類別的引擎數量：

| 欄位 | 中文 | 意義 |
|------|------|------|
| `malicious` | 惡意 | 判定為惡意的引擎數 |
| `suspicious` | 可疑 | 判定為可疑的引擎數 |
| `harmless` | 無害 | 判定為無害的引擎數 |
| `undetected` | 未偵測 | 未偵測到威脅的引擎數 |
| `timeout` | 逾時 | 分析逾時的引擎數 |
| `total` | 合計 | 上述欄位加總（衍生屬性） |

## 報告資料結構

| 模型 | 主要欄位 | 說明 |
|------|----------|------|
| `ReportData` | `generated_at`、`summary_verdict`、`counts`、`results` | 整份報告；`counts` 為各判定的目標數量統計 |
| `ScanResult` | `target`、`stats`、`verdict`、`engines`、`permalink`、`error` | 單一目標結果 |
| `ScanTarget` | `type`、`value`、`size` | 掃描目標（type：file/url/domain/ip/hash） |
| `AnalysisStats` | 見上節 | 引擎判定統計 |

## 報告版面區塊

報告（HTML / PDF）由上而下包含下列區塊：

1. **表頭（Header）**
   - 報告標題、產生時間（`generated_at`）。
   - 總體判定 badge（依 `summary_verdict` 上色：惡意=紅、可疑=橘、安全=綠、未知=灰）。

2. **概況統計（Summary）**
   - 各判定的目標數量（`counts`：惡意 / 可疑 / 安全 / 未知）。
   - 掃描目標總數。

3. **逐筆卡片（Per-target Cards）**
   - 每個目標一張卡片，顯示：目標類型與值、判定 badge。
   - 統計表：malicious / suspicious / harmless / undetected / timeout。
   - 若有 `error`，改以錯誤訊息呈現該卡片。

4. **引擎明細（Engine Details）**
   - 各防毒引擎的判定明細（引擎名稱、分類、偵測結果）。
   - 於 HTML 中可摺疊，避免版面過長。

5. **Permalink**
   - 指向 VirusTotal GUI 的連結，供人工複查：
     - 檔案：`https://www.virustotal.com/gui/file/{sha256}`
     - URL：`https://www.virustotal.com/gui/url/{url_id}`
     - 網域：`https://www.virustotal.com/gui/domain/{domain}`
     - IP：`https://www.virustotal.com/gui/ip-address/{ip}`

## HTML 與 PDF 的差異與產生方式

| 格式 | 產生方式 | 特性 |
|------|----------|------|
| HTML | jinja2 渲染 `templates/report.html.j2`，自帶 inline CSS | 互動式（引擎明細可摺疊）、離線可開、無額外系統相依 |
| PDF | 先渲染 HTML，再由 weasyprint（`HTML(string=...).write_pdf(...)`）轉檔 | 靜態、適合封存與分發；需 pango / cairo 原生相依 |

- `--format html`：只產生 HTML。
- `--format pdf`：只產生 PDF（內部仍先渲染 HTML 再轉檔）。
- `--format both`：同時產生 HTML 與 PDF。
- 省略 `--format`：不產生報告檔，只在終端機列印文字摘要。

> PDF 需要 weasyprint 的系統原生相依（macOS：`brew install pango`；Debian/Ubuntu：`apt-get install libpango-1.0-0 libpangoft2-1.0-0`）。缺少時請改用 `--format html`。

## 輸出檔名慣例

輸出路徑由 `--output` 決定，預設為 `./output/`。實際檔名以基底（base）加上固定後綴：

| 格式 | 檔名 |
|------|------|
| HTML | `<base>.report.html` |
| PDF | `<base>.report.pdf` |

- 若 `--output` 指向**目錄**（結尾為 `/` 或為既有目錄），base 取預設名稱（例如目標值或 `report`），輸出至該目錄。
- 若 `--output` 指向**檔名基底**（例如 `./output/example`），則輸出 `./output/example.report.html` 與 `./output/example.report.pdf`。

範例：

```bash
python3 scripts/main.py scan-domain example.com --format both --output ./output/example
# → ./output/example.report.html
# → ./output/example.report.pdf
```

## 文字摘要與 JSON

- **文字摘要**：未帶 `--format` 時於終端機列印，包含每個目標的判定標籤與統計數字，供快速判讀。
- **JSON 輸出**：`--json-output` 以 `ReportData.to_dict()` 序列化（`ensure_ascii=False`，保留中文），可導向檔案後透過 `report --input` 合併多筆結果成單一報告。
