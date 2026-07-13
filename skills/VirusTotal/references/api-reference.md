# VirusTotal API v3 參考

本文件整理本 skill 使用到的 VirusTotal API v3 端點與行為，作為離線 fallback。官方完整文件：<https://docs.virustotal.com/reference/overview>。

## 基本資訊

| 項目 | 值 |
|------|-----|
| Base URL | `https://www.virustotal.com/api/v3` |
| 認證標頭 | `x-apikey: <VT_API_KEY>` |
| 內容型別（一般） | `application/json` |
| 內容型別（上傳檔案） | `multipart/form-data` |

所有請求都必須帶上 `x-apikey` 標頭；金鑰由 skill 從 `.env` 的 `VT_API_KEY` 讀入。

### 認證範例

```bash
curl --request GET \
  --url "https://www.virustotal.com/api/v3/domains/example.com" \
  --header "x-apikey: $VT_API_KEY"
```

## 端點總覽

| 目標 | 方法與路徑 | 用途 |
|------|-----------|------|
| 上傳檔案（< 32MB） | `POST /files` | 上傳檔案並取得分析 id |
| 取得大檔上傳網址 | `GET /files/upload_url` | 檔案 ≥ 32MB 時先取得專用上傳網址 |
| 檔案報告 | `GET /files/{sha256}` | 以雜湊查詢既有檔案報告 |
| 提交 URL | `POST /urls` | 送出網址並取得分析 id |
| URL 報告 | `GET /urls/{url_id}` | 以 `url_id` 查詢網址報告 |
| 分析輪詢 | `GET /analyses/{id}` | 查詢一次掃描分析的狀態與統計 |
| 網域報告 | `GET /domains/{domain}` | 查詢網域信譽 |
| IP 報告 | `GET /ip_addresses/{ip}` | 查詢 IP 信譽 |

## 端點細節

### 上傳檔案（< 32MB）：`POST /files`

- 內容型別：`multipart/form-data`，欄位名為 `file`。
- 回應：`data.type == "analysis"`、`data.id` 為分析 id（供後續輪詢）。

```bash
curl --request POST \
  --url "https://www.virustotal.com/api/v3/files" \
  --header "x-apikey: $VT_API_KEY" \
  --form "file=@./sample.bin"
```

回應（節錄）：
```json
{
  "data": {
    "type": "analysis",
    "id": "OTk...base64..."
  }
}
```

### 大檔上傳（≥ 32MB）：`GET /files/upload_url`

檔案大小達 32MB（`32 * 1024 * 1024` bytes）以上時，需先取得一次性上傳網址：

```bash
curl --request GET \
  --url "https://www.virustotal.com/api/v3/files/upload_url" \
  --header "x-apikey: $VT_API_KEY"
```

回應：
```json
{ "data": "https://www.virustotal.com/_ah/upload/..." }
```

再對 `data` 回傳的網址以 `multipart/form-data`（欄位 `file`）`POST` 上傳，回應同樣得到分析 id。

### 檔案報告：`GET /files/{sha256}`

- 路徑參數可用 SHA-256、SHA-1 或 MD5。
- 查無樣本時回傳 `404`。

主要回應欄位（位於 `data.attributes`）：

| 欄位 | 說明 |
|------|------|
| `last_analysis_stats` | 各判定數量（見下方統計欄位） |
| `last_analysis_results` | 各引擎明細（引擎名 → `{category, result, engine_name, ...}`） |
| `meaningful_name` | 具代表性的檔名 |
| `type_description` | 檔案型別描述 |
| `size` | 檔案大小（bytes） |
| `md5` / `sha1` / `sha256` | 雜湊值 |
| `reputation` | 社群信譽分數 |

Permalink 慣例：`https://www.virustotal.com/gui/file/{sha256}`。

### 提交 URL：`POST /urls`

- 內容型別：`application/x-www-form-urlencoded`，欄位 `url`。
- 回應：`data.id` 為分析 id。

```bash
curl --request POST \
  --url "https://www.virustotal.com/api/v3/urls" \
  --header "x-apikey: $VT_API_KEY" \
  --form "url=https://example.com"
```

### URL 報告：`GET /urls/{url_id}`

`url_id` 由目標網址以 base64url 編碼後去除結尾 `=` padding 產生（見下節）。回應欄位與檔案類似，重點為 `last_analysis_stats` 與 `last_analysis_results`。

Permalink 慣例：`https://www.virustotal.com/gui/url/{url_id}`。

### 分析輪詢：`GET /analyses/{id}`

送掃檔案或 URL 後，以回傳的分析 id 輪詢，直到完成：

| 欄位 | 說明 |
|------|------|
| `data.attributes.status` | `queued` / `in-progress` / `completed` |
| `data.attributes.stats` | 完成後的判定統計 |
| `data.attributes.results` | 完成後的各引擎明細 |

流程：每隔 `POLL_INTERVAL`（預設 15 秒）查詢一次，直到 `status == "completed"` 或超過 `POLL_TIMEOUT`（預設 300 秒，可用 `--timeout` 覆寫）。

### 網域報告：`GET /domains/{domain}`

主要回應欄位（`data.attributes`）：

| 欄位 | 說明 |
|------|------|
| `last_analysis_stats` | 各判定數量 |
| `last_analysis_results` | 各引擎／服務判定明細 |
| `reputation` | 社群信譽分數 |
| `categories` | 各家分類服務的網域分類 |
| `last_dns_records` | DNS 記錄 |

Permalink 慣例：`https://www.virustotal.com/gui/domain/{domain}`。

### IP 報告：`GET /ip_addresses/{ip}`

主要回應欄位（`data.attributes`）：

| 欄位 | 說明 |
|------|------|
| `last_analysis_stats` | 各判定數量 |
| `last_analysis_results` | 各引擎／服務判定明細 |
| `reputation` | 社群信譽分數 |
| `as_owner` | 自治系統擁有者 |
| `country` | 國別代碼 |
| `network` | 所屬網段 |

Permalink 慣例：`https://www.virustotal.com/gui/ip-address/{ip}`。

## 統計欄位：`last_analysis_stats` / `analyses.stats`

| 欄位 | 中文 | 說明 |
|------|------|------|
| `malicious` | 惡意 | 判為惡意的引擎數 |
| `suspicious` | 可疑 | 判為可疑的引擎數 |
| `harmless` | 無害 | 判為無害的引擎數 |
| `undetected` | 未偵測 | 未偵測到威脅的引擎數 |
| `timeout` | 逾時 | 分析逾時的引擎數 |

## `url_id` 演算法（base64url 去 padding）

VirusTotal 以「網址的 base64url 編碼、去除結尾 `=`」作為 URL 資源識別碼。

```python
import base64

def url_to_id(url: str) -> str:
    """將網址轉為 VirusTotal url_id：base64url 編碼後去除 padding。"""
    return base64.urlsafe_b64encode(url.encode()).decode().strip("=")
```

範例（VirusTotal 官方示例）：

| 輸入網址 | `url_id` |
|----------|----------|
| `http://www.virustotal.com` | `aHR0cDovL3d3dy52aXJ1c3RvdGFsLmNvbQ` |
| `https://example.com` | `aHR0cHM6Ly9leGFtcGxlLmNvbQ` |

取得 `url_id` 後即可：`GET /urls/{url_id}` 查詢報告。

## 輪詢流程（檔案 / URL）

```
1. POST /files 或 POST /urls        → 取得 analysis id
2. loop:
     GET /analyses/{id}
     if status == "completed": break
     if 已等待 > timeout: 丟出逾時
     sleep(POLL_INTERVAL)
3. 依需要再 GET /files/{sha256} 或 GET /urls/{url_id} 取得完整報告
4. 讀取 last_analysis_stats 計算判定
```

網域與 IP 無需送掃與輪詢，直接 `GET` 即可取得 `last_analysis_stats`。

## 額度限制（免費公開 API）

| 範圍 | 上限 |
|------|------|
| 每分鐘 | 4 次請求 |
| 每日 | 500 次請求 |
| 每月 | 15,500 次請求 |

超過額度會回 `429`；請控制請求頻率，並在批次掃描時預留間隔。

## 常見錯誤碼

| HTTP 狀態 | 意義 | 處理建議 |
|-----------|------|----------|
| `401` | 認證失敗（金鑰錯誤或未帶 `x-apikey`） | 檢查 `VT_API_KEY` 是否正確且未被撤銷 |
| `404` | 資源不存在（雜湊 / URL 未曾被分析） | 改用上傳（`scan-file`）或提交（`scan-url`）流程 |
| `429` | 超過速率或每日／每月額度 | 尊重 `Retry-After` 退避重試，放慢請求 |

錯誤回應主體格式：
```json
{
  "error": {
    "code": "NotFoundError",
    "message": "..."
  }
}
```
