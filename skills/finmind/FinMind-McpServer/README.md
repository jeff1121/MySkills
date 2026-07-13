# FinMind MCP Server

[![GitHub Release](https://img.shields.io/github/v/release/jeff1121/MySkills?filter=finmind-*&label=version&color=blue)](https://github.com/jeff1121/MySkills/releases?q=finmind)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

FinMind 金融數據 MCP (Model Context Protocol) Server，讓 AI Agent 能查詢台股、美股、期貨、選擇權等金融資料，並進行技術分析與基本面分析。

## 功能特色

- 🔍 **通用資料查詢** — 支援 77+ 個 FinMind 資料集
- 📊 **技術分析** — 移動平均線 (MA)、RSI、MACD 指標
- 📈 **基本面分析** — PER/PBR、月營收、股利政策
- 🔎 **股票搜尋** — 以名稱、代碼或產業分類搜尋
- 🌍 **國際市場** — 美股、英股、歐股、日股、匯率、原油、黃金
- 🐳 **Docker 部署** — 一鍵啟動 MCP Server

## 支援的資料範圍

| 分類 | 資料集數量 | 範例 |
|------|-----------|------|
| 台股技術面 | 20 | 股價、PER/PBR、當沖、分K |
| 台股籌碼面 | 16 | 三大法人、融資融劵、外資持股 |
| 台股基本面 | 12 | 損益表、負債表、月營收、股利 |
| 衍生品 | 16 | 期貨、選擇權、三大法人 |
| 即時資訊 | 4 | 台股即時、期貨即時 (Sponsor) |
| 可轉債 | 4 | 可轉債日成交、三大法人 |
| 台股其他 | 3 | 新聞、景氣信號、產業鏈 |
| 國際股市 | 9 | 美股、英股、歐股、日股 |
| 全球經濟 | 6 | 匯率、利率、黃金、原油 |

## 快速開始

👉 詳細步驟請參閱 [Quickstart.md](Quickstart.md)

### 前置需求

1. 到 [FinMind](https://finmindtrade.com/) 註冊帳號並取得 API Token
2. Docker 與 Docker Compose（或 Python 3.11+）

### Docker 部署

```bash
cd FinMind
cp .env.example .env
# 編輯 .env，填入 FINMIND_TOKEN
docker compose up -d
```

### 本地開發

```bash
cd FinMind
pip install -e ".[dev]"
export FINMIND_TOKEN="your_token_here"
python -m finmind_mcp.server
```

## MCP 設定

### SSE 模式（Docker 部署後）

```json
{
  "mcpServers": {
    "finmind": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### Stdio 模式（本地安裝後）

```json
{
  "mcpServers": {
    "finmind": {
      "command": "python",
      "args": ["-m", "finmind_mcp.server"],
      "env": {
        "FINMIND_TOKEN": "your_token_here"
      }
    }
  }
}
```

## MCP 工具清單

### 1. `finmind_query_data` — 通用資料查詢

查詢任意 FinMind 資料集。

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| dataset | str | ✅ | 資料集名稱，如 `TaiwanStockPrice` |
| data_id | str | ⚠️ | 資料識別碼（如股票代碼 `2330`） |
| start_date | str | ❌ | 開始日期 (YYYY-MM-DD) |
| end_date | str | ❌ | 結束日期 (YYYY-MM-DD) |
| row_limit | int | ❌ | 回傳最大筆數（預設 100） |

### 2. `finmind_list_data_ids` — 資料集 ID 列表

列出某資料集所有可用的 data_id。

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| dataset | str | ✅ | 資料集名稱 |

### 3. `finmind_translate_columns` — 欄位名稱中英對照

取得資料集欄位的中文翻譯。

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| dataset | str | ✅ | 資料集名稱 |

### 4. `finmind_stock_search` — 股票搜尋

以名稱、代碼或產業分類搜尋股票。

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| keyword | str | ✅ | 搜尋關鍵字（如 `2330`、`台積電`、`半導體`） |

### 5. `finmind_analyze` — 資料分析

對股票進行技術分析或基本面分析。

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| stock_id | str | ✅ | 股票代碼 |
| analysis_type | str | ❌ | 分析類型：`summary` / `trend` / `volatility` / `volume` / `technical` / `fundamental` |
| start_date | str | ❌ | 開始日期（預設 3 個月前） |
| end_date | str | ❌ | 結束日期（預設今天） |

### 6. `finmind_check_usage` — API 使用量查詢

查詢目前 API 使用次數與配額。無需參數。

## 環境變數

| 變數 | 必填 | 預設值 | 說明 |
|------|------|--------|------|
| `FINMIND_TOKEN` | ✅ | — | FinMind API Token |
| `FINMIND_API_BASE_URL` | ❌ | `https://api.finmindtrade.com/api/v4` | API 基礎網址 |
| `MCP_SERVER_PORT` | ❌ | `8080` | MCP Server 連接埠 |
| `LOG_LEVEL` | ❌ | `INFO` | 日誌等級 |

## Docker 指令

```bash
# 建置映像
docker compose -f infra/docker-compose.build.yml build

# 啟動服務
docker compose -f infra/docker-compose.yml up -d

# 查看日誌
docker compose -f infra/docker-compose.yml logs -f

# 停止服務
docker compose -f infra/docker-compose.yml down

# 推送到 DockerHub
./infra/publish.sh           # 推送 latest
./infra/publish.sh v0.1.0    # 推送指定版本
```

## 專案結構

```
FinMind/
├── README.md                       # 本文件
├── Quickstart.md                   # 快速入門指南
├── Tasks.md                        # 實作任務清單
├── pyproject.toml                  # Python 專案設定
├── .env.example                    # 環境變數範例
├── infra/                          # 基礎設施與部署
│   ├── Dockerfile                  # Docker 映像定義
│   ├── docker-compose.build.yml    # 建置映像
│   ├── docker-compose.yml          # 部署設定
│   └── publish.sh                  # 推送 DockerHub
├── src/finmind_mcp/
│   ├── __init__.py                 # 版本號定義
│   ├── server.py                   # MCP Server 進入點 (FastMCP)
│   ├── client.py                   # FinMind API HTTP 客戶端
│   ├── config.py                   # 設定管理
│   ├── models.py                   # Pydantic 資料模型
│   ├── datasets.py                 # 資料集參考對照表
│   ├── errors.py                   # 錯誤定義
│   ├── log.py                      # 日誌模組
│   └── tools/                      # MCP 工具
│       ├── query.py                # 通用查詢
│       ├── search.py               # 搜尋與列表
│       ├── translate.py            # 欄位翻譯
│       ├── analysis.py             # 資料分析
│       └── usage.py                # 使用量查詢
├── references/
│   └── finmind_api.md              # FinMind API 參考文件
└── tests/                          # 單元測試
```

## 會員等級說明

| 等級 | 每小時請求 | 可用資料集 |
|------|-----------|-----------|
| Free | 600 | 基本資料集（含 data_id 時免費） |
| Backer | 更高 | 進階資料集（股權分級、週K月K 等） |
| Sponsor | 最高 | 全部資料集（含即時、分K、分點） |

## 授權

MIT License
