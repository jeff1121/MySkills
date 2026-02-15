---
name: cisco-configer
description: 透過 SSH 連線 Cisco 網路設備（IOS/IOS-XE、NX-OS、ASA、IOS-XR），自動判斷所需 CLI 指令來查詢設備資訊或進行組態設定，並將設備回傳的文字資料重新排版為易讀格式。當使用者提供 Cisco 設備的 SSH 連線資訊，並希望查詢設備狀態、介面資訊、路由表等，或進行 VLAN、ACL、路由協定等組態設定時使用。
version: 0.1.0
---

# Cisco Configer

## 概覽

透過隨附的 Python 腳本，以 SSH 連線遠端 Cisco 網路設備，自動執行 CLI 指令。核心能力：

1. **查詢設備資訊**：自動判斷並執行對應的 show 指令，取得介面狀態、路由表、VLAN、ACL 等資訊
2. **設定設備組態**：自動產生 config 指令序列，完成 VLAN 建立、介面設定、路由協定配置等目標
3. **平台自動偵測**：支援 IOS/IOS-XE、NX-OS、ASA、IOS-XR，連線後自動識別設備類型
4. **輸出排版美化**：將設備回傳的原始文字轉為對齊的表格、分段的設定檔等易讀格式

## 適用情境

- 使用者需要查詢 Cisco 設備的運行狀態或組態資訊
- 使用者需要對 Cisco 設備進行組態變更
- 使用者不確定應使用哪些 CLI 指令 — 本技能會自動判斷
- 需要將設備輸出轉為結構化、易讀的格式

## 支援平台

| 平台 | netmiko device_type | 說明 |
|------|-------------------|------|
| IOS / IOS-XE | `cisco_ios` | Catalyst 交換機、ISR 路由器等 |
| NX-OS | `cisco_nxos` | Nexus 資料中心交換機 |
| ASA | `cisco_asa` | ASA 防火牆 |
| IOS-XR | `cisco_xr` | 電信級路由器（ASR、NCS） |

## 必要輸入

在進行任何操作前先收集 SSH 連線資訊：

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| HostAddr | str | ✅ | 設備 IP 位址或主機名稱 |
| HostUser | str | ✅ | SSH 登入帳號 |
| HostPass | str | ✅ | SSH 登入密碼 |
| device_type | str | ❌ | 設備類型（預設自動偵測）：`cisco_ios`、`cisco_nxos`、`cisco_asa`、`cisco_xr` |
| enable_password | str | ❌ | enable 模式密碼（若與登入密碼不同） |
| port | int | ❌ | SSH 連接埠（預設 22） |

## 連線資訊提示

若使用者未提供連線資訊，**主動向使用者詢問**以下項目：

```
請提供 Cisco 設備的 SSH 連線資訊：
HostAddr: 0.0.0.0
HostUser: username
HostPass: password
```

提示：enable_password、device_type、port 為選填，未提供時使用預設值。

## 工作流程

### 1. 安裝前置需求
```bash
python3 -m pip install -r scripts/requirements.txt
```

### 2. 查詢設備資訊
```bash
python3 scripts/main.py query \
  --host 10.0.0.1 \
  --username admin \
  --password <password> \
  --intent "show interfaces" \
  --yes --verbose
```

### 3. 設定設備組態
```bash
python3 scripts/main.py config \
  --host 10.0.0.1 \
  --username admin \
  --password <password> \
  --intent "set vlan 100 name DATA" \
  --yes --verbose
```

> **重要**：在非互動式環境（如 agent、CI/CD pipeline）中執行時，**務必加上 `--yes`** 跳過確認提示，
> 否則腳本會卡在 `確認執行？ [y/N]:` 等待輸入而逾時。
> 若 stdin 不是 TTY，腳本也會自動跳過確認。

### 4. 回報結果
- 查詢結果以美化格式呈現（Markdown 表格、對齊文字）
- 設定結果回報執行的指令與驗證結果
- 錯誤時提供明確的問題描述與建議

## 指令判斷邏輯

根據使用者的意圖自動選擇對應的 CLI 指令：

**查詢類**（自動選擇 show 指令）：
- 介面狀態 → `show ip interface brief`、`show interfaces status`
- 路由表 → `show ip route`
- VLAN → `show vlan brief`
- ACL → `show access-lists`
- 鄰居 → `show cdp neighbors`、`show lldp neighbors`
- BGP → `show ip bgp summary`
- OSPF → `show ip ospf neighbor`
- 系統資訊 → `show version`
- 運行組態 → `show running-config`

**設定類**（自動產生 config 指令序列）：
- 建立 VLAN → `vlan <id>` / `name <name>`
- 設定介面 → `interface <name>` / `ip address ...` / `no shutdown`
- 配置路由 → 對應路由協定指令
- 設定 ACL → `access-list ...` 或 `ip access-list ...`
- NTP / Logging / Hostname 等管理設定

## 輸出格式化

將設備回傳的原始文字資料重新排版，提升可讀性：

- **表格化**：將 `show ip interface brief` 等空白分隔輸出轉為對齊的 Markdown 表格
- **分段整理**：設定輸出依區塊分段，加入適當空行
- **路由表美化**：路由條目結構化呈現
- **清理雜訊**：移除 ANSI 控制字元、指令回顯、設備提示符
- **一致對齊**：確保所有欄位寬度一致，資料對齊

## 錯誤處理

| 錯誤情境 | 處理方式 |
|----------|---------|
| ❌ 連線逾時 | 確認設備 IP 與連接埠是否正確，以及網路可達性 |
| ❌ 認證失敗 | 確認帳號密碼是否正確 |
| ❌ Enable 密碼錯誤 | 確認 enable 密碼 |
| ❌ 指令執行失敗 | 顯示設備回傳的錯誤訊息，建議替代指令 |
| ❌ 設備類型無法偵測 | 手動指定 device_type 參數 |
| ❌ 連線中斷 | 自動重試一次，仍失敗則回報 |

## 腳本

- `scripts/main.py` — CLI 進入點（click group：query / config）
- `scripts/executor.py` — 指令執行編排邏輯
- `scripts/ssh_client.py` — netmiko SSH 封裝（支援平台自動偵測）
- `scripts/models.py` — 資料模型（ConnectionInfo、CommandResult、ExecutionResult）
- `scripts/formatter.py` — 設備輸出排版美化
- `scripts/commands/__init__.py` — 平台模組工廠函式
- `scripts/commands/ios.py` — IOS/IOS-XE 指令模組
- `scripts/commands/nxos.py` — NX-OS 指令模組
- `scripts/commands/asa.py` — ASA 指令模組
- `scripts/commands/iosxr.py` — IOS-XR 指令模組
- `scripts/requirements.txt` — Python 相依套件

## 參考文件

- `references/ios-commands.md` — IOS/IOS-XE 常用指令參考
- `references/nxos-commands.md` — NX-OS 常用指令參考
- `references/asa-commands.md` — ASA 常用指令參考
- `references/iosxr-commands.md` — IOS-XR 常用指令參考
