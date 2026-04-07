# FinMind MCP Server — 快速入門指南

5 分鐘內完成 FinMind MCP Server 的安裝與設定。

## 步驟 1：取得 FinMind API Token

1. 到 [https://finmindtrade.com/](https://finmindtrade.com/) 註冊帳號
2. 登入後在個人資料頁面取得 API Token
3. 免費帳號即可使用，每小時 600 次請求

## 步驟 2：選擇部署方式

### 方式 A：Docker 部署（推薦）

```bash
# 1. 進入專案目錄
cd FinMind

# 2. 建立環境變數檔
cp .env.example .env

# 3. 編輯 .env，填入你的 Token
#    FINMIND_TOKEN=your_actual_token

# 4. 建置並啟動
docker compose -f docker-compose.build.yml build
docker compose up -d

# 5. 確認服務運行中
curl http://localhost:8080/sse
```

### 方式 B：本地安裝

```bash
# 1. 進入專案目錄
cd FinMind

# 2. 安裝 Python 套件
pip install -e .

# 3. 設定環境變數
export FINMIND_TOKEN="your_actual_token"

# 4. 啟動 MCP Server（stdio 模式）
python -m finmind_mcp.server

# 或 HTTP/SSE 模式
python -m finmind_mcp.server --http 8080
```

## 步驟 3：設定 AI Agent

### Claude Desktop

編輯 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "finmind": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### Claude CLI

```bash
claude mcp add finmind --url http://localhost:8080/sse
```

### Copilot CLI（stdio 模式）

在你的 MCP 設定檔中加入：

```json
{
  "mcpServers": {
    "finmind": {
      "command": "python",
      "args": ["-m", "finmind_mcp.server"],
      "env": {
        "FINMIND_TOKEN": "your_actual_token"
      }
    }
  }
}
```

## 步驟 4：開始使用

連線成功後，你可以直接對 AI 說：

### 查詢股價
> 「查詢台積電最近一個月的股價」

### 技術分析
> 「分析 2330 的技術指標，包括 RSI 和 MACD」

### 基本面
> 「查看鴻海的 PER/PBR 和月營收趨勢」

### 搜尋股票
> 「搜尋半導體相關的股票」

### 國際市場
> 「查詢 AAPL 最近的美股股價」

### 經濟指標
> 「查詢美元對台幣匯率」

## 常見問題

### Q: 出現 "API Token 認證失敗" 怎麼辦？
確認 `FINMIND_TOKEN` 環境變數已正確設定。到 [FinMind](https://finmindtrade.com/) 登入確認 Token。

### Q: 出現 "API 請求頻率超限" 怎麼辦？
免費帳號每小時限 600 次。等待一小時後重試，或升級到 Backer/Sponsor 方案。

### Q: Docker 容器啟動失敗？
```bash
# 查看日誌
docker compose logs finmind-mcp-server

# 確認 .env 檔案存在且 Token 已填入
cat .env
```

### Q: 如何查看 API 使用量？
直接詢問 AI：「查詢我的 FinMind API 使用量」

## 下一步

- 📖 閱讀 [README.md](README.md) 了解完整功能
- 📚 參考 [references/finmind_api.md](references/finmind_api.md) 查看所有資料集
- 🔧 查看 [Tasks.md](Tasks.md) 了解開發計畫
