---
name: virustotal
description: 使用 VirusTotal API v3 掃描本機檔案、URL、網域、IP 或檔案雜湊，彙整多引擎威脅情資為易讀摘要，並產生 HTML 或 PDF 報告。當使用者想查詢某個檔案/網址/網域/IP/雜湊是否惡意、或需要一份威脅情資報告時使用。
version: 0.1.0
---

# VirusTotal 掃描與報告

## 概覽
透過隨附的 Python CLI 呼叫 [VirusTotal](https://www.virustotal.com) API v3，掃描或查詢下列目標並彙整多家防毒引擎的判定結果：

- 本機檔案（上傳至 VirusTotal 分析）
- URL（網址）
- 網域（domain）
- IP 位址
- 檔案雜湊（MD5 / SHA-1 / SHA-256）

掃描完成後可輸出純文字摘要、機器可讀的 JSON，或產生 HTML / PDF 報告。所有指令都在代理端機器本地執行，只有「檔案」與「URL」掃描會將目標送往 VirusTotal。

## 必要輸入
在執行任何掃描前，先設定 VirusTotal API 金鑰。

1. 取得金鑰：登入 <https://www.virustotal.com> → 右上角帳號選單 → **API key**。
2. 於 skill 目錄複製範本並填入金鑰：
   ```bash
   cd skills/VirusTotal
   cp .env.example .env
   # 編輯 .env，將 VT_API_KEY 設為實際金鑰
   ```
3. `.env` 內容：
   ```
   VT_API_KEY=你的實際金鑰
   ```

> `.env` 已被 git 忽略，請勿提交金鑰。除 `.env` 檔外，也可直接匯出同名環境變數 `VT_API_KEY`。

## 前置需求
### 1. 安裝 Python 相依套件
```bash
python3 -m pip install -r scripts/requirements.txt
```
內含 `click`、`requests`、`python-dotenv`、`jinja2`、`weasyprint`。

### 2. 安裝 weasyprint 的系統原生相依（僅產生 PDF 時需要）
weasyprint 依賴 pango / cairo 等原生函式庫，需以系統套件管理員安裝：

| 平台 | 安裝指令 |
|------|----------|
| macOS（Homebrew） | `brew install pango` |
| Debian / Ubuntu | `sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0` |

> 若只需要文字摘要或 HTML 報告，可略過此步驟；缺少原生相依時，`--format pdf` 或 `--format both` 會失敗。

## 工作流程
CLI 進入點為 `scripts/main.py`，用法：`python3 scripts/main.py <子指令> [選項]`。

### 共用選項
| 選項 | 說明 |
|------|------|
| `--format [html\|pdf\|both]` | 產生報告的格式；省略時只在終端機列印文字摘要 |
| `--output PATH` | 報告輸出路徑（檔名基底或目錄），預設 `./output/` |
| `--json-output` | 以 JSON 輸出結果，可導向檔案供 `report --input` 合併 |
| `--timeout SECONDS` | 分析輪詢逾時秒數（預設 300） |
| `--yes`, `-y` | 略過確認提示；非互動環境會自動略過 |
| `--verbose` | 顯示除錯訊息 |

### 1. 設定金鑰與安裝相依
如上「必要輸入」與「前置需求」所述，完成 `.env` 設定並安裝套件。

### 2. 執行掃描子指令
每個子指令對應一種目標類型：

```bash
# 掃描本機檔案（會上傳到 VirusTotal，並輪詢分析結果）
python3 scripts/main.py scan-file ./samples/suspicious.exe

# 掃描網址（會提交 URL 並輪詢分析結果）
python3 scripts/main.py scan-url https://example.com

# 查詢網域信譽
python3 scripts/main.py scan-domain example.com

# 查詢 IP 信譽
python3 scripts/main.py scan-ip 8.8.8.8

# 以既有檔案雜湊查詢（不需上傳檔案）
python3 scripts/main.py scan-hash 44d88612fea8a8f36de82e1278abb02f
```

未帶 `--format` 時，會直接在終端機印出判定與統計摘要。

### 3. 產生 HTML / PDF 報告
加上 `--format` 即可輸出報告；`both` 會同時產出 HTML 與 PDF：

```bash
python3 scripts/main.py scan-domain example.com \
  --format both \
  --output ./output/example
# → 產生 ./output/example.report.html 與 ./output/example.report.pdf
```

### 4. 保存 JSON 結果供後續合併
以 `--json-output` 將單筆掃描結果存成 JSON：

```bash
python3 scripts/main.py scan-domain example.com  --json-output > ./output/domain.json
python3 scripts/main.py scan-ip 8.8.8.8          --json-output > ./output/ip.json
python3 scripts/main.py scan-hash 44d88612fea8a8f36de82e1278abb02f --json-output > ./output/hash.json
```

### 5. 用 `report` 合併多筆 JSON 成單一報告
`report` 子指令可讀取多個先前存下的 JSON（`--input` 可重複），合併為一份總報告：

```bash
python3 scripts/main.py report \
  --input ./output/domain.json \
  --input ./output/ip.json \
  --input ./output/hash.json \
  --format both \
  --output ./output/combined
# → 產生 ./output/combined.report.html 與 ./output/combined.report.pdf
```

## 判定說明
每個目標依 VirusTotal 回傳的 `last_analysis_stats` 計算單一判定（verdict）：

| 判定代碼 | 中文標籤 | 判定依據 |
|----------|----------|----------|
| `malicious` | 惡意 | `malicious > 0`（至少一家引擎判為惡意） |
| `suspicious` | 可疑 | `malicious == 0` 且 `suspicious > 0` |
| `harmless` | 安全 | 無引擎判為惡意或可疑 |
| `unknown` | 未知 | 查無分析結果或發生錯誤 |

統計欄位意義：`malicious`（惡意）、`suspicious`（可疑）、`harmless`（無害）、`undetected`（未偵測到）、`timeout`（逾時）。詳細對應請見 `references/report-format.md`。

## 疑難排解
| 症狀 | 原因與處理 |
|------|-----------|
| `401 Unauthorized` | API 金鑰錯誤或未設定。確認 `.env` 的 `VT_API_KEY` 正確、無多餘空白，且未使用已撤銷的金鑰。 |
| `429 Too Many Requests` | 超過免費額度（4 次/分、500 次/日、15.5K 次/月）。CLI 會尊重 `Retry-After` 退避重試；請放慢請求或稍後再試，避免短時間連續掃描。 |
| `404 Not Found` | 該雜湊 / URL 尚未被 VirusTotal 分析過。`scan-hash` 僅能查詢既有樣本；未知檔案請改用 `scan-file` 上傳分析。 |
| 分析一直未完成 / 逾時 | 大型或罕見樣本分析較久。以 `--timeout` 增加輪詢秒數（預設 300）後重試。 |
| weasyprint 匯入或執行失敗 | 缺少 pango / cairo 原生相依。依「前置需求」以系統套件管理員安裝；或改用 `--format html` 略過 PDF。 |
| 大檔（≥ 32MB）上傳 | CLI 會自動改走 `GET /files/upload_url` 取得專用上傳網址再上傳；若失敗，請確認網路穩定與檔案可讀。 |

> ⚠️ **隱私警告**：使用 `scan-file` 上傳檔案至 VirusTotal，等同於公開分享該檔案，其他訂閱者可能取得。切勿上傳含機敏、個資或機密內容的檔案。若只想查詢是否為已知惡意樣本，請改用 `scan-hash` 以雜湊查詢，不會上傳檔案內容。

## 腳本與參考
### 腳本（`scripts/`）
- `main.py` — Click CLI 進入點（`scan-file` / `scan-url` / `scan-domain` / `scan-ip` / `scan-hash` / `report`）
- `config.py` — 載入 `.env` 與 `VT_API_KEY`，集中管理 API base URL、輪詢與大檔門檻常數
- `models.py` — 資料模型（`ScanTarget`、`AnalysisStats`、`ScanResult`、`ReportData`）
- `vt_client.py` — VirusTotal API v3 客戶端封裝、自訂例外、輪詢與 429 退避
- `analyzer.py` — 掃描編排：送掃 → 輪詢 → 取報告 → 計算判定
- `reporter.py` — 產生文字摘要、HTML（jinja2）與 PDF（weasyprint）
- `templates/report.html.j2` — 報告 HTML 模板
- `requirements.txt` — Python 相依套件
- `tests/` — pytest 單元測試（以 mock 覆蓋，不需真實網路）

### 參考文件（`references/`）
- `references/api-reference.md` — VirusTotal API v3 端點、請求／回應欄位、`url_id` 演算法、額度與錯誤碼（離線 fallback）
- `references/report-format.md` — 判定代碼對應、統計欄位、報告版面與輸出檔名慣例
