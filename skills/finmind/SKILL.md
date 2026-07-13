---
name: finmind
description: FinMind 金融數據 AI 助手 — 透過 MCP Server 查詢台股、美股、期貨、選擇權等金融資料，並進行技術分析與基本面分析。當使用者需要查詢股票價格、分析股市趨勢、取得財報數據或全球經濟指標時使用。
version: 0.1.0
---

# FinMind 金融數據助手

## 概覽

透過 FinMind API 與 MCP Server 提供完整的金融數據查詢與分析能力。支援 77+ 個資料集，涵蓋：

- **台股技術面**：股價、PER/PBR、當沖、還原股價、分K、週K、月K
- **台股籌碼面**：三大法人、融資融劵、外資持股、分點資料
- **台股基本面**：綜合損益表、資產負債表、現金流量表、月營收、股利
- **衍生品**：期貨日成交、選擇權日成交、三大法人
- **國際股市**：美股、英股、歐股、日股
- **全球經濟**：匯率、央行利率、黃金、原油、國債殖利率、CNN 恐懼貪婪指數

## 適用情境

- 使用者想查詢某檔股票的價格、成交量
- 使用者想做技術分析（移動平均線、RSI、MACD）
- 使用者想了解基本面（PER/PBR、月營收、股利）
- 使用者想比較多檔股票或追蹤趨勢
- 使用者想查看國際市場數據或經濟指標

## 必要輸入

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| FINMIND_TOKEN | str | ✅ | FinMind API Token |

取得方式：到 [https://finmindtrade.com/](https://finmindtrade.com/) 註冊並登入。

## MCP Server 連線

### Docker 部署

```bash
# 部署
cd FinMind
cp .env.example .env
# 編輯 .env 填入 FINMIND_TOKEN
docker compose up -d
```

### MCP 設定（Claude CLI / Copilot CLI）

```json
{
  "mcpServers": {
    "finmind": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

或使用 stdio 模式：

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

## 可用工具

| 工具 | 說明 | 主要參數 |
|------|------|---------|
| `finmind_query_data` | 通用資料查詢 | dataset, data_id, start_date, end_date |
| `finmind_list_data_ids` | 列出資料集的 data_id | dataset |
| `finmind_translate_columns` | 欄位名稱中英對照 | dataset |
| `finmind_stock_search` | 搜尋股票代碼/名稱 | keyword |
| `finmind_analyze` | 資料分析 | stock_id, analysis_type |
| `finmind_check_usage` | API 使用量查詢 | — |

## Execution Workflow

### 查詢股價

1. 若使用者給出股票名稱，先用 `finmind_stock_search` 查詢代碼
2. 用 `finmind_query_data` 搭配 `TaiwanStockPrice` 資料集取得股價
3. 以表格格式呈現結果

### 技術分析

1. 確認股票代碼與日期範圍
2. 使用 `finmind_analyze` 搭配 `analysis_type: technical`
3. 回報 MA、RSI、MACD 指標與訊號判讀

### 基本面分析

1. 使用 `finmind_analyze` 搭配 `analysis_type: fundamental`
2. 取得 PER/PBR、月營收資料
3. 呈現估值與營收趨勢

## 常用股票代碼

| 代碼 | 名稱 |
|------|------|
| 2330 | 台積電 (TSMC) |
| 2317 | 鴻海 (Foxconn) |
| 2454 | 聯發科 (MediaTek) |
| 2882 | 國泰金 |
| 2881 | 富邦金 |
| 0050 | 元大台灣50 ETF |

## 參考文件

- [FinMind 官方文件](https://finmindtrade.com/)
- [API 參考文件](../../FinMind/references/finmind_api.md)
- [MCP Server 原始碼](../../FinMind/)

## Error Handling / 疑難排解

- **Token 無效或過期**: 重新至 [FinMind](https://finmindtrade.com/) 取得新的 API Token，更新環境變數 `FINMIND_TOKEN`。
- **API 回應 429 (Rate Limit)**: 降低請求頻率，等待數秒後重試。FinMind 免費方案有每日請求上限。
- **查無資料**: 確認股票代碼正確（台股用數字如 `2330`，美股用代號如 `AAPL`）。確認日期範圍內有交易日。
- **MCP Server 連線失敗**: 確認 Docker 容器正在運行（`docker ps`），檢查連接埠設定。
- **環境變數未設定**: 確認 `.env` 檔案包含 `FINMIND_TOKEN`，並已正確載入。
