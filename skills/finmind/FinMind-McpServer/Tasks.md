# FinMind MCP Server — 實作任務清單

## 概覽

建立 FinMind 金融數據 MCP Server，提供 6 個工具讓 AI Agent 查詢與分析台股、美股、期貨等金融資料。

**專案根目錄**: `FinMind/`
**分支**: `feat/finmind-mcp-server`

---

## Phase 1: 專案基礎建設

### Task 1 — 建立分支與專案骨架
- [x] 建立 `feat/finmind-mcp-server` 分支
- [x] 建立 `FinMind/` 目錄結構：`src/finmind_mcp/`、`tools/`、`references/`、`tests/`
- [x] 建立 `pyproject.toml`（依賴：mcp[cli], httpx, pandas, pydantic-settings, structlog）
- [x] 建立 `.env.example`

### Task 2 — 設定模組 (config.py)
- [x] Pydantic `BaseSettings` 讀取 `FINMIND_TOKEN`、`FINMIND_API_BASE_URL` 等環境變數
- [x] 支援 `.env` 檔案
- [x] Token 驗證方法

### Task 3 — 錯誤處理與日誌模組
- [x] 自定義錯誤類別：`FinMindError`、`AuthenticationError`、`RateLimitError`、`DatasetError`、`APIError`、`ConfigError`
- [x] structlog 日誌設定，含敏感資訊遮蔽

### Task 4 — FinMind API 客戶端 (client.py)
- [x] `FinMindClient` 非同步 HTTP 客戶端（httpx）
- [x] `query_data()` — GET /data
- [x] `list_data_ids()` — GET /datalist
- [x] `translate_columns()` — GET /translation
- [x] `check_usage()` — GET /v2/user_info
- [x] HTTP 狀態碼處理（401/402/403）

### Task 5 — 資料模型與資料集對照表
- [x] Pydantic 模型：`FinMindAPIResponse`、`StockInfo`、`StockPrice`、`AnalysisResult`、`ToolResult`、`UsageInfo`
- [x] 完整資料集對照表（77+ 個資料集，9 個分類）
- [x] 搜尋函式 `find_datasets()`

---

## Phase 2: MCP 工具實作

### Task 6 — finmind.query_data（通用資料查詢）
- [x] 支援所有 77+ 資料集
- [x] 參數驗證（dataset 必填，驗證名稱是否存在）
- [x] 回傳結構化表格、統計摘要
- [x] 可設定 row_limit 控制回傳筆數

### Task 7 — finmind.list_data_ids（資料集 ID 列表）
- [x] 列出某資料集的所有 data_id
- [x] 模糊搜尋建議（找不到時推薦相近資料集）

### Task 8 — finmind.translate_columns（欄位翻譯）
- [x] 取得資料集欄位的中英對照

### Task 9 — finmind.stock_search（股票搜尋）
- [x] 支援股票代碼、名稱、產業分類搜尋
- [x] 透過 TaiwanStockInfo 資料集查詢
- [x] 回傳常用資料集提示

### Task 10 — finmind.analyze（資料分析）
- [x] 分析類型：summary / trend / volatility / volume / technical / fundamental
- [x] 技術指標：MA (5/10/20/60)、RSI (14)、MACD (12/26/9)
- [x] 基本面：PER/PBR + 月營收
- [x] 自動計算日期範圍（預設 3 個月）

### Task 11 — finmind.check_usage（使用量查詢）
- [x] 查詢 API 使用次數與配額
- [x] 計算剩餘次數與使用百分比
- [x] 估算會員等級

---

## Phase 3: MCP Server 整合

### Task 12 — FastMCP Server 進入點
- [x] 使用 `mcp[cli]` SDK 建立 FastMCP 伺服器
- [x] 註冊 6 個工具 + 2 個資源
- [x] 支援 stdio 模式與 HTTP/SSE 模式

### Task 13 — 整合所有工具
- [x] 所有工具在 server.py 中正確註冊
- [x] JSON 序列化回傳

---

## Phase 4: Docker 與部署

### Task 14 — Dockerfile
- [x] python:3.11-slim 基礎映像
- [x] 安裝依賴、複製原始碼
- [x] EXPOSE 8080、HEALTHCHECK
- [x] CMD 以 HTTP/SSE 模式啟動

### Task 15 — docker-compose.build.yml
- [x] 建置映像設定（image: jeffhou/finmind-mcp-server）
- [x] 支援 linux/amd64 平台

### Task 16 — docker-compose.yml
- [x] 部署設定：port mapping、env_file、healthcheck
- [x] 環境變數注入（FINMIND_TOKEN 等）
- [x] restart: unless-stopped

### Task 17 — publish.sh
- [x] 建置 + 標記 + 推送到 DockerHub (jeffhou)
- [x] 支援指定版本標籤

---

## Phase 5: 文件與 Skill

### Task 18 — skills/finmind/SKILL.md
- [x] 遵循 repo 的 SKILL.md 格式（YAML frontmatter）
- [x] 概覽、適用情境、必要輸入、MCP 連線設定
- [x] 可用工具清單、Execution Workflow

### Task 19 — README.md
- [x] 功能特色、支援資料範圍
- [x] 快速開始（Docker + 本地）
- [x] MCP 設定方式
- [x] 6 個工具詳細參數說明
- [x] Docker 指令、專案結構

### Task 20 — Quickstart.md
- [x] 4 步驟快速入門
- [x] Docker 與本地兩種部署方式
- [x] Claude / Copilot CLI 設定
- [x] 使用範例與常見問題

### Task 21 — references/finmind_api.md
- [x] API 端點、認證、Rate Limit
- [x] 完整資料集總覽（按分類）
- [x] 常用股票代碼、注意事項

---

## Phase 6: 測試與驗證

### Task 22 — 單元測試
- [ ] test_client.py — API 客戶端測試（mock HTTP）
- [ ] test_tools.py — 工具功能測試

### Task 23 — Docker 建置測試
- [ ] docker compose build 成功
- [ ] 容器可正常啟動

### Task 24 — MCP Server 啟動驗證
- [ ] stdio 模式啟動正常
- [ ] HTTP/SSE 模式啟動正常
- [ ] tools/list 回傳正確的工具清單
