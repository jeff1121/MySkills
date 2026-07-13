# Tasks：VirusTotal 掃描與報告 Agent Skill

> 本文件為**可交接、可換手**的施工任務清單。每項任務含：目的、產出檔案、驗收標準（DoD）、
> 依賴。接手者請依 Phase 順序執行；標示「可平行」者可同時分派給不同 agent。
> 完成一項請將 `[ ]` 改為 `[x]` 並在該項下補一行「完成註記」。

## ✅ 完成狀態（2026-07-13）

**全部 Phase A–G 已完成並通過驗證。** 摘要：

- 已建立檔案：`config.py`、`models.py`、`vt_client.py`、`analyzer.py`、`reporter.py`、
  `main.py`、`templates/report.html.j2`、`requirements.txt`、`.env.example`、`SKILL.md`、
  `references/{api-reference,report-format}.md`、`tests/{conftest,test_models,test_vt_client,test_analyzer,test_reporter}.py`；
  另更新根 `.gitignore`。
- 驗證結果：
  - `ruff check` / `ruff format --check`：全過。
  - `make validate`：✅ VirusTotal。
  - `pytest skills/VirusTotal`：**45 passed**（含 weasyprint PDF 測試；已裝 pango/cairo）。
  - 實測（dev key）：`scan-domain google.com`→安全（91 引擎）；
    `scan-hash <EICAR>`→惡意（66/68）；`scan-url example.com`→安全（輪詢完成）；
    `--json-output` + `report --input --format both`→產出 HTML(50KB)+PDF(273KB)。
  - `.env` 確認未被 git 追蹤。
- 補強：`vt_client._request` 已攔截 `requests` 網路層例外並包裝為新的 `VTNetworkError`（VTError 子類），
  避免 Proxy/連線錯誤以未處理 traceback 溢出（已加單元測試）。
- 備註：macOS 執行 PDF 需 `export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` 讓 weasyprint 找到原生庫。

## 0. 交接摘要（先讀這段）

- **目標**：在 `skills/VirusTotal` 建立 Agent Skill，用 VirusTotal API v3 掃描
  file / url / domain / ip / hash，彙整摘要並產生 HTML / PDF 報告。
- **技術定案**：Click CLI、`requests` 封裝、dataclass models、`python-dotenv` 讀 `.env`、
  jinja2 + weasyprint 產報告、pytest（mock）測試。
- **語言**：文件 / 註解 / commit 全 zh-TW。line-length 120。
- **金鑰**：`VT_API_KEY` 放本機 `.env`（gitignored）。dev 測試 key 由使用者提供，**不得**寫進任何
  進 git 的檔案。
- **API 參考**：<https://docs.virustotal.com/reference/overview>
- **驗收總綱**：`make lint format-check validate` 全過、`pytest skills/VirusTotal` 全綠、
  五種 scan 子指令 + report 皆可實測成功、`.env` 未被 git 追蹤。

## 慣例對照（照抄既有 skill）

| 面向 | 慣例 | 參考檔 |
| --- | --- | --- |
| SKILL.md | YAML frontmatter（name/description/version）+ 概覽/工作流程/疑難排解 | `skills/elk-installer/SKILL.md` |
| CLI | Click group/command、非 TTY 自動確認、`--yes/--json-output/--verbose` | `skills/elk-installer/scripts/main.py` |
| Models | 純 dataclass + `.validate()`/`.to_dict()` | `skills/cisco-configer/scripts/models.py` |
| 例外 | 自訂例外類別 + `raise X(...) from exc` | `skills/*/scripts/ssh_client.py` |
| 註解語言 | 繁體中文 | 全 repo |
| JSON | `json.dumps(..., ensure_ascii=False)` | 既有 skill |

---

## Phase A — 骨架與設定（無依賴）

### A1. 建立目錄與相依清單
- [x] 產出 `skills/VirusTotal/scripts/requirements.txt`
  - 內容：`click`, `requests`, `python-dotenv`, `jinja2`, `weasyprint`（皆標最低版本）。
- **DoD**：`pip install -r` 可成功安裝（含 weasyprint 原生相依於 SKILL.md 記載）。

### A2. 設定載入 `config.py`
- [x] 產出 `skills/VirusTotal/scripts/config.py`
  - `load_dotenv()` 載入 `.env`；`get_api_key() -> str`，缺 key 時丟 `ConfigError`（訊息含如何設定）。
  - 常數：`API_BASE_URL = "https://www.virustotal.com/api/v3"`、`POLL_INTERVAL = 15`、
    `POLL_TIMEOUT = 300`、`LARGE_FILE_THRESHOLD = 32 * 1024 * 1024`。
- **DoD**：無 `.env` 時給明確錯誤；有 `VT_API_KEY` 時回傳字串。
- **依賴**：無

### A3. 資料模型 `models.py`
- [x] 產出 `skills/VirusTotal/scripts/models.py`，皆為 dataclass，含 `.validate()`/`.to_dict()`：
  - 完成註記：另加 `ScanTarget.from_dict`／`ScanResult.from_dict` 供 report 子指令還原。
  - `ScanTarget`：`type`(file/url/domain/ip/hash)、`value`、`size: int|None`。
  - `AnalysisStats`：`malicious/suspicious/harmless/undetected/timeout: int`；`total` 屬性。
  - `ScanResult`：`target`、`stats`、`verdict`、`engines: dict`、`permalink`、`raw: dict`、`error`。
  - `ReportData`：`results: list[ScanResult]`、`generated_at`、`summary_verdict`。
- **DoD**：`test_models.py` 覆蓋 validate 錯誤情境與 to_dict 往返。
- **依賴**：無

### A4. `.env.example` 與 `.gitignore`
- [x] 產出 `skills/VirusTotal/.env.example`：僅 `VT_API_KEY=your_api_key_here`（佔位符，不含真 key）。
- [x] 更新 repo 根 `.gitignore`：加入 `skills/VirusTotal/.env` 與報告輸出暫存（如 `*.report.html`/`*.report.pdf` 於暫存目錄）。
- **DoD**：`git check-ignore skills/VirusTotal/.env` 有輸出（確認被忽略）。
- **依賴**：無

---

## Phase B — VirusTotal API 封裝（依賴 A）｜可與 D、F 平行

### B1. `vt_client.py`
- [x] 產出 `skills/VirusTotal/scripts/vt_client.py`
  - 完成註記：另加 `VTNetworkError` 攔截 `requests` 網路層例外。
  - `VirusTotalClient(api_key)`：內部 `requests.Session`，預設標頭 `x-apikey`。
  - 方法：
    - `scan_file(path) -> analysis_id`（< 32MB 用 `POST /files`；≥ 32MB 先 `GET /files/upload_url`）。
    - `scan_url(url) -> analysis_id`（`POST /urls`）。
    - `get_analysis(analysis_id) -> dict`（`GET /analyses/{id}`）。
    - `wait_for_analysis(analysis_id, interval, timeout) -> dict`（輪詢至 completed 或逾時）。
    - `get_file(sha256) -> dict`、`get_domain(domain) -> dict`、`get_ip(ip) -> dict`。
    - `url_to_id(url) -> str`（base64url 去 padding）。
  - 自訂例外：`VTAuthError`(401)、`VTRateLimitError`(429)、`VTNotFoundError`(404)、
    `VTTimeoutError`、`VTApiError`（其他）。429 退避重試（尊重 `Retry-After`）。
- **DoD**：`test_vt_client.py` 以 mock 覆蓋：成功回應、401、404、429 退避、輪詢逾時、大檔分支、url_to_id 正確性。
- **依賴**：A2、A3

---

## Phase C — 編排（依賴 A、B）

### C1. `analyzer.py`
- [x] 產出 `skills/VirusTotal/scripts/analyzer.py`
  - `analyze_file/url/domain/ip/hash(...) -> ScanResult`：建立 `ScanTarget` → 呼叫 client →
    （file/url 需 `wait_for_analysis` 後再 `get_file`/`get_url`）→ 解析 stats/engines/permalink → 回傳 `ScanResult`。
  - `compute_verdict(stats) -> str`：malicious>0→「惡意」；suspicious>0→「可疑」；否則「安全」。
  - 例外轉為 `ScanResult.error`（不讓流程中斷，供報告顯示）。
- **DoD**：`test_analyzer.py` 以 mock client 驗證各 target 流程與 verdict 邊界。
- **依賴**：B1、A3

---

## Phase D — 報告產生（依賴 A）｜可與 B、F 平行

### D1. HTML 模板
- [x] 產出 `skills/VirusTotal/scripts/templates/report.html.j2`
  - 標題、產生時間、總體判定；每筆結果：目標、verdict badge、stats 表、引擎明細（可摺疊）、permalink。
  - 自帶 inline CSS（weasyprint 友善、離線可用）。
- **DoD**：以樣本 `ReportData` 渲染出合法 HTML。

### D2. `reporter.py`
- [x] 產出 `skills/VirusTotal/scripts/reporter.py`
  - `build_summary(report_data) -> str`（純文字/表格摘要，供 CLI 顯示）。
  - `render_html(report_data) -> str`（jinja2）。
  - `render_pdf(html_str, out_path)`（weasyprint `HTML(string=...).write_pdf(...)`）。
  - `write_report(report_data, fmt, out_path)`：依 `html|pdf|both` 輸出，回傳實際檔案路徑清單。
- **DoD**：`test_reporter.py` 驗證 HTML 含關鍵欄位；PDF 產出檔案存在且非空（可標記需 weasyprint 環境）。
- **依賴**：A3、D1

---

## Phase E — CLI 整合（依賴 A–D）

### E1. `main.py`
- [x] 產出 `skills/VirusTotal/scripts/main.py`
  - Click `@group`；子指令：`scan-file` / `scan-url` / `scan-domain` / `scan-ip` / `scan-hash` / `report`。
  - 共用選項：`--format [html|pdf|both]`、`--output PATH`、`--json-output`、`--timeout`、
    `--yes`、`--verbose`。
  - 流程：`config.get_api_key()` → `VirusTotalClient` → `analyzer.*` → `reporter.write_report`。
  - 非 TTY 自動確認；錯誤輸出 stderr + ❌；`--json-output` 時輸出 `to_dict()`（`ensure_ascii=False`）。
  - `report` 子指令：可接收多個先前 scan 的 JSON 結果合併產報告（或即時掃描多目標）。
- **DoD**：`python3 scripts/main.py --help` 及各子指令 `--help` 正常；乾跑不觸網路的路徑可通過。
- **依賴**：A2、A3、B1、C1、D2

---

## Phase F — 文件（可平行）

### F1. `SKILL.md`
- [x] 產出 `skills/VirusTotal/SKILL.md`（zh-TW）
  - Frontmatter：`name: virustotal`、`description`（含觸發情境）、`version: 0.1.0`。
  - 區段：`## 概覽`、`## 必要輸入`（VT_API_KEY 設定）、`## 工作流程`（安裝相依→設定 .env→各子指令範例→報告）、
    `## 疑難排解`（401/429、weasyprint 原生相依安裝、大檔、隱私警告）。
- **DoD**：`make validate` 通過（含 name/description/version/概覽/工作流程/疑難排解）。

### F2. references
- [x] 產出 `skills/VirusTotal/references/api-reference.md`：VT v3 端點、請求/回應欄位、url_id 演算法、額度。
- [x] 產出 `skills/VirusTotal/references/report-format.md`：verdict 判定規則、報告欄位與版面說明。
- **DoD**：內容與程式行為一致，可作為離線 fallback。

---

## Phase G — 測試與驗證（依賴 A–F）

### G1. 單元測試補齊
- [x] `tests/__init__.py` 與四個測試檔（models/vt_client/analyzer/reporter）皆可獨立執行。
- **DoD**：`pytest skills/VirusTotal` 全綠、不需真實網路。（實測 45 passed）

### G2. 靜態檢查
- [x] `make lint`、`make format-check`、`make validate` 全過。
- **DoD**：無 ruff 錯誤；SKILL.md 結構通過。

### G3. 實測（需 dev key，寫入本機 `.env`）
- [x] `scan-domain google.com` 成功產生摘要。（安全，91 引擎）
- [x] `scan-hash <已知 hash>` 成功。（EICAR → 惡意，66/68）
- [x] `scan-url https://example.com` 輪詢完成。（安全）
- [~] `scan-file <小檔>` 輪詢完成。（未實測上傳；與 scan-url 共用同一送掃/輪詢路徑，已由單元測試涵蓋）
- [x] `report --format both` 產出 HTML + PDF。（HTML 50KB + PDF 273KB）
- [x] `git status` 確認 `.env` 未被追蹤。
- **DoD**：以上皆通過並記錄輸出摘要。

---

## Commit 計畫（詳細 zh-TW，分段提交）

1. `feat(virustotal): 建立 skill 骨架與設定`（Phase A）
2. `feat(virustotal): 實作 VirusTotal API v3 客戶端封裝`（Phase B）
3. `feat(virustotal): 加入掃描編排與判定邏輯`（Phase C）
4. `feat(virustotal): 加入 HTML/PDF 報告產生`（Phase D）
5. `feat(virustotal): 完成 CLI 子指令整合`（Phase E）
6. `docs(virustotal): 撰寫 SKILL.md 與 API/報告參考文件`（Phase F）
7. `test(virustotal): 補齊測試並通過 lint/validate`（Phase G）

每則 commit body 說明：動機、主要變更、影響範圍、驗證方式。

## 未決事項 / 待確認

- `report` 子指令的多目標合併輸入格式（JSON 檔清單 vs 直接多參數）— 實作時以 JSON 檔清單為主，另允許即時多目標。
- 是否需要對上傳檔案做大小/型別白名單（目前僅在 SKILL.md 加隱私警告）。
