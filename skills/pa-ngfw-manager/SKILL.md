---
name: pa-ngfw-manager
description: 透過 PAN-OS XML API 連線 Palo Alto 新世代防火牆，提供異常偵測、安全策略管理（CRUD）、組態備份還原、系統效能監控等自動化能力。當使用者需要管理 Palo Alto 防火牆的安全策略、備份設定、偵測異常流量或查看系統狀態時使用。
version: 0.1.0
---

# Palo Alto NGFW Manager

## 概覽

透過隨附的 Python 工具，以 PAN-OS XML API 連線 Palo Alto 新世代防火牆（NGFW），自動執行防火牆管理任務。核心能力：

1. **異常網路活動偵測（Anomaly Detection）**：從 Traffic/Threat 日誌分析異常行為，包含 Top Talker 突增、Port Scan、DDoS、可疑外連、威脅事件激增、Deny Rate 異常等 6 項偵測規則
2. **安全策略管理（Policy CRUD）**：列表、新增、更新、刪除安全規則，所有寫入操作皆有安全護欄（dry-run / confirm / commit control）
3. **組態備份與還原（Backup & Restore）**：匯出 running config 至本地或 S3/MinIO，並可從備份還原
4. **系統效能監控（System Usage）**：取得 CPU、記憶體、Session 使用量、Dataplane 負載

## 適用情境

- 使用者需要查看或管理 Palo Alto 防火牆的安全策略
- 使用者需要備份防火牆設定或從備份還原
- 使用者想偵測網路異常活動（可疑流量、攻擊跡象）
- 使用者需要查看防火牆系統資源使用狀態
- 使用者需要批次管理多台防火牆（透過不同 PANOS_HOST）

## 支援功能

| 功能 | 指令 | 說明 |
|------|------|------|
| 異常偵測 | `pa-agent anomaly detect` | 6 項規則的異常分析 |
| 策略列表 | `pa-agent policy list` | 列出安全規則（支援篩選） |
| 策略新增 | `pa-agent policy add` | 新增安全規則（dry-run 預設） |
| 策略更新 | `pa-agent policy update` | 更新規則欄位（patch 模式） |
| 策略刪除 | `pa-agent policy delete` | 刪除規則（需 confirm） |
| 備份 | `pa-agent config backup` | 備份到本地或 S3 |
| 還原 | `pa-agent config restore` | 從備份還原（需 confirm） |
| 系統狀態 | `pa-agent system usage` | CPU / 記憶體 / Session |

## 必要輸入

在執行任何操作前，需設定以下環境變數：

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| PANOS_HOST | str | ✅ | 防火牆位址（如 https://10.0.0.1） |
| PANOS_API_KEY | str | ⚠️ | XML API Key（或使用帳密） |
| PANOS_USERNAME | str | ⚠️ | 登入帳號（搭配 PANOS_PASSWORD） |
| PANOS_PASSWORD | str | ⚠️ | 登入密碼（搭配 PANOS_USERNAME） |
| PANOS_VSYS | str | ❌ | 虛擬系統（預設 vsys1） |
| PANOS_VERIFY_TLS | bool | ❌ | 驗證 TLS 憑證（預設 true） |

⚠️ PANOS_API_KEY 或 (PANOS_USERNAME + PANOS_PASSWORD) 擇一必填。

## 連線資訊提示

若使用者未提供連線資訊，**主動向使用者詢問**以下項目：
1. 防火牆 IP 或主機名稱（PANOS_HOST）
2. 認證方式：API Key 或帳號密碼
3. 要操作的虛擬系統（預設 vsys1）

## Execution Workflow

### 環境準備
1. 確認 Python 3.11+ 已安裝
2. 進入專案目錄：`cd skills/pa-ngfw-manager/scripts/paloalto-ngfw-agent-skills`
3. 安裝依賴：`pip install -e ".[dev]"` 或 `bash scripts/dev.sh`
4. 設定環境變數（.env 檔或 export）

### 執行流程

#### 策略管理
1. 先用 `pa-agent policy list` 了解目前規則
2. 新增/更新/刪除規則時，先用 `--dry-run` 預覽變更
3. 確認無誤後加上 `--no-dry-run --confirm` 執行
4. 若需要套用到 running config，加上 `--commit --commit-comment "說明"`

#### 備份還原
1. 備份：`pa-agent config backup --backend local`（或 `--backend s3`）
2. 列出備份：`pa-agent config list --backend local`
3. 還原：先 `--dry-run` 查看備份資訊，再 `--no-dry-run --confirm` 執行

#### 異常偵測
1. 執行偵測：`pa-agent anomaly detect --window 1h --baseline 24h`
2. 查看結果：findings 包含 rule_id、severity、summary、evidence
3. 注意 data_gaps 欄位，表示哪些資料無法取得

## Output

### 策略列表
以表格或 JSON 輸出，包含：name, from, to, source, destination, service, application, action, disabled

### 異常偵測報告
```json
{
  "findings": [
    {
      "rule_id": "top_talker_surge",
      "severity": "medium",
      "summary": "IP 10.1.1.1 connection count 450 exceeds baseline avg 100 * 3.0",
      "evidence": {"src_ip": "10.1.1.1", "connections": 450, "baseline_avg": 100},
      "first_seen": "2024-01-15T10:00:00Z",
      "last_seen": "2024-01-15T10:30:00Z"
    }
  ],
  "data_gaps": [],
  "window": "1h",
  "baseline": "24h"
}
```

### 系統狀態
```json
{
  "cpu_percent": 25.3,
  "memory_percent": 45.8,
  "sessions_active": 12345,
  "sessions_max": 65536,
  "dp_load": 18.5
}
```

## Error Handling

### 認證失敗（401）
- 確認 PANOS_API_KEY 有效且未過期
- 或確認 PANOS_USERNAME / PANOS_PASSWORD 正確

### 連線逾時
- 確認 PANOS_HOST 可連線
- 調高 PANOS_TIMEOUT
- 檢查網路路由是否通暢

### Commit 失敗
- 檢查 candidate config 是否有衝突
- 在 PAN-OS Web UI 查看 commit 錯誤訊息
- 考慮從備份還原：`pa-agent config restore`

### XPath 錯誤
- 確認 PANOS_VSYS 設定正確
- 檢查規則名稱是否包含特殊字元
- 先用 `--dry-run` 檢查 xpath

## 安全護欄

⚠️ **所有寫入操作皆有安全機制：**
- `--dry-run`（預設開啟）：僅顯示計畫，不實際變更
- `--confirm`：明確確認後才執行
- `--commit`：預設不 commit；需明確開啟
- 日誌不會記錄 API Key 或密碼
- 內建 Rate Limit 避免過載防火牆
