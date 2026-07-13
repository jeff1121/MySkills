# Plan：VirusTotal 掃描與報告 Agent Skill

## 一、目標

在 `./skills/VirusTotal` 新建一個 Agent Skill，透過 **VirusTotal API v3** 掃描：

- 本機檔案（local-file）
- URL
- 網域（domain）
- IP 位址（ip）
- 檔案雜湊（hash）

並將 VirusTotal 回傳的資料**彙整為易讀摘要**，最後**產生報告（HTML 或 PDF）**。

整體遵循 repo 既有 skill 慣例（`cisco-configer`、`elk-installer`、`finmind`）：Click CLI、
dataclass models、自訂例外、`.validate()`/`.to_dict()`、zh-TW 註解與文件、通過 `make validate`
的 SKILL.md 結構、line-length 120。

## 二、使用者決策（已確認）

| 項目 | 決策 |
| --- | --- |
| 報告格式 | `--format html\|pdf\|both`（每次由使用者選擇） |
| PDF 產生 | **weasyprint**（HTML/CSS → PDF） |
| CLI 結構 | 子指令 `scan-file` / `scan-url` / `scan-domain` / `scan-ip` / `scan-hash` / `report` |
| 掃描範圍 | file / url / domain / IP / hash |
| 語言 | 文件、程式註解、chat、commit message 全部 zh-TW |
| commit message | 需詳細，分階段提交 |
| 金鑰管理 | `.env` + `python-dotenv`；dev 測試 key 僅寫入本機 `.env`（不進 git） |
| 平行處理 | 實作階段可用多 agent 平行 |

## 三、預設技術決策（採建議值）

1. **大檔支援**：檔案 > 32MB 時，先 `GET /files/upload_url` 取得專用上傳網址再上傳。
2. **HTTP 客戶端**：以 `requests` 自寫封裝（貼近 repo 現況、易於 mock 測試），不引入官方 `vt-py` SDK。
3. **輪詢**：分析輪詢預設間隔 15 秒、最長等候約 5 分鐘（300 秒），可用 `--timeout` 覆寫。

## 四、VirusTotal API v3 重點

- Base URL：`https://www.virustotal.com/api/v3`
- 認證標頭：`x-apikey: <VT_API_KEY>`
- 檔案（< 32MB）：`POST /files`（multipart，欄位名 `file`）→ 回傳 analysis id
- 檔案（≥ 32MB）：`GET /files/upload_url` → 對回傳網址 `POST` 上傳 → analysis id
- URL：`POST /urls`（form 欄位 `url`）→ analysis id；`url_id = base64url(url).rstrip("=")` → `GET /urls/{url_id}`
- 分析輪詢：`GET /analyses/{id}`，`data.attributes.status == "completed"` 後讀取 `stats`
- 檔案報告：`GET /files/{sha256}`
- 網域：`GET /domains/{domain}`
- IP：`GET /ip_addresses/{ip}`
- 常見統計欄位：`last_analysis_stats`（malicious / suspicious / harmless / undetected / timeout）
- 免費額度：4 requests/min、500/day、15.5K/month → 需節流與友善的 429 錯誤處理

## 五、檔案結構

```
skills/VirusTotal/
  SKILL.md                    # zh-TW；含 名稱/描述/version + 概覽/工作流程/疑難排解（通過 make validate）
  plan.md                     # 本檔
  Tasks.md                    # 交接用任務清單
  .env.example                # VT_API_KEY 佔位符
  references/
    api-reference.md          # VT v3 端點、請求/回應欄位整理
    report-format.md          # verdict 判定對應、報告欄位與版面說明
  scripts/
    main.py                   # Click group：scan-file/url/domain/ip/hash/report
    config.py                 # python-dotenv 載入 .env，取得並驗證 VT_API_KEY
    models.py                 # dataclass：ScanTarget, AnalysisStats, ScanResult, ReportData
    vt_client.py              # requests 封裝 VT API v3 + 自訂例外 + 輪詢 + 節流
    analyzer.py               # 編排：送掃 → 輪詢 → 取報告 → 產生判定摘要
    reporter.py               # 產生摘要文字 + HTML(jinja2) + PDF(weasyprint)
    templates/
      report.html.j2          # 報告 HTML 模板
    requirements.txt          # click, requests, python-dotenv, jinja2, weasyprint
    tests/
      __init__.py
      test_models.py          # 資料模型驗證/序列化
      test_vt_client.py       # mock requests 的 API 行為
      test_analyzer.py        # mock client 的編排流程
      test_reporter.py        # 報告產生（HTML 內容 / PDF 產出）
```

同時更新 repo 根目錄 `.gitignore`，排除 `skills/VirusTotal/.env` 與報告輸出暫存檔。

## 六、模組職責

- **config.py**：`load_dotenv()` 載入 `.env`；`get_api_key()` 回傳金鑰，缺少時丟出明確錯誤；集中管理 base URL、輪詢預設值。
- **models.py**：純 dataclass，每個都提供 `.validate() -> list[str]` 與 `.to_dict() -> dict`。
  - `ScanTarget`：type（file/url/domain/ip/hash）、value、size（檔案用）。
  - `AnalysisStats`：malicious / suspicious / harmless / undetected / timeout。
  - `ScanResult`：target、stats、verdict、engine 明細、permalink、raw、error。
  - `ReportData`：彙整多筆 `ScanResult` + 產生時間、摘要判定。
- **vt_client.py**：`VirusTotalClient`（`requests.Session` + `x-apikey`），方法涵蓋
  `scan_file` / `scan_url` / `get_domain` / `get_ip` / `get_file` / `wait_for_analysis`；
  自訂例外 `VTAuthError`、`VTRateLimitError`、`VTApiError`、`VTTimeoutError`；429 退避重試。
- **analyzer.py**：把 CLI 參數轉成 `ScanTarget`，呼叫 client，輪詢完成後組成 `ScanResult`，
  依 stats 計算 verdict（malicious>0 → 惡意；suspicious>0 → 可疑；否則安全）。
- **reporter.py**：`build_summary()`（純文字/JSON 摘要）、`render_html()`（jinja2）、
  `render_pdf()`（weasyprint 由 HTML 轉 PDF）、`write_report(format)`。
- **main.py**：Click group；各 scan 子指令共用 `--format`、`--output`、`--json-output`、
  `--yes`、`--timeout`、`--verbose`；非 TTY 自動確認；錯誤以 stderr + ❌ 呈現。

## 七、實作階段（可平行）

| Phase | 內容 | 依賴 |
| --- | --- | --- |
| A 骨架與設定 | config.py、models.py、requirements.txt、.env.example、.gitignore | — |
| B API 封裝 | vt_client.py + test_vt_client.py | A |
| C 編排 | analyzer.py + test_analyzer.py | A、B |
| D 報告產生 | reporter.py、templates/report.html.j2 + test_reporter.py | A |
| E CLI | main.py | A–D |
| F 文件 | SKILL.md、references/api-reference.md、references/report-format.md | 可平行 |
| G 測試與驗證 | 補齊測試、lint/format/validate、實測 | A–F |

平行建議：A 完成後，B / D / F 可同時進行（分派不同 subagent）；C 依 B；E 最後整合。

## 八、驗證

1. `python3 -m pip install -r skills/VirusTotal/scripts/requirements.txt`
2. `make lint format-check validate`（SKILL.md 結構檢查）
3. `pytest skills/VirusTotal`（mock 單元測試）
4. 實測（dev key 寫入本機 `.env`）：
   - `scan-domain google.com`
   - `scan-hash <已知樣本 hash>`
   - `scan-url https://example.com`
   - `scan-file <小檔>`（驗證輪詢完成）
   - `report --format both`（產出 HTML + PDF）
5. `git status` 確認 `.env` 未被追蹤。

## 九、Commit 策略

- 每個 Phase 一次（或數次）詳細 zh-TW commit，內容說明「動機、變更、影響、驗證方式」。
- 範例分段：骨架與設定 → API 封裝 → 編排 → 報告 → CLI → 文件 → 測試與驗證。

## 十、範圍與排除

- **包含**：file/url/domain/IP/hash 掃描與報告、HTML/PDF 輸出、大檔上傳、輪詢與節流。
- **排除**：VT 進階功能（retrohunt、graph、私有掃描、Livehunt）、批次排程、資料庫儲存。

## 十一、風險與注意

- **金鑰外洩**：dev key 僅存本機 `.env`；`.env.example` 只放佔位符；務必 gitignore。
- **速率限制**：免費額度低，實測時控制請求數；429 需退避重試並提示使用者。
- **weasyprint 系統相依**：需 `pango`、`cairo` 等原生函式庫；SKILL.md 疑難排解需說明安裝方式。
- **大檔上傳**：> 32MB 走 upload_url 流程，需額外測試。
- **隱私**：上傳檔案至 VT 等同公開分享，SKILL.md 需明確警告不要上傳機敏檔案。
