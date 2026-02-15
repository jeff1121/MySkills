# Tasks: Cisco Configer Skill

**Input**: 計畫文件（對話中的 Plan）
**版本號**: 0.1.0（SKILL.md、main.py、models.py 同步）

**Organization**: 任務按開發階段分組，每個階段可獨立驗證。

## 格式: `[ID] [P?] 說明`

- **[P]**: 可並行執行（不同檔案、無依賴）
- 包含完整檔案路徑（相對於 `skills/cisco-configer/`）

## 路徑慣例

- **Skill 根目錄**: `skills/cisco-configer/`
- **腳本目錄**: `skills/cisco-configer/scripts/`
- **參考文件**: `skills/cisco-configer/references/`

---

## Phase 1: Setup（專案初始化）

**Purpose**: 建立專案目錄結構與基礎設定

- [X] T001 建立 `skills/cisco-configer/` 資料夾結構（scripts/、scripts/commands/、references/）
- [X] T002 [P] 建立 `scripts/requirements.txt`（netmiko>=4.2.0、click>=8.0.0）
- [X] T003 [P] 建立 `SKILL.md`（frontmatter: name、description、version: 0.1.0；內容含概覽、適用情境、必要輸入、連線資訊提示、工作流程、指令判斷邏輯、輸出格式化、錯誤處理、腳本清單、參考文件）

---

## Phase 2: Foundational（基礎元件）

**Purpose**: 所有功能共用的核心模組

**⚠️ CRITICAL**: 此階段完成前，不可開始 Phase 3

- [X] T004 [P] 建立 `scripts/models.py` — 資料模型（dataclass），包含：
  - `ConnectionInfo`：host、username、password、device_type（Optional，預設 None 自動偵測）、enable_password（Optional）、port（預設 22）；含 `validate() -> list[str]`、`__str__()`
  - `CommandResult`：command、output、formatted_output、success、error（Optional）；含 `to_dict()`
  - `ExecutionResult`：success、device_info（Optional）、results: list[CommandResult]、error（Optional）；含 `to_dict()`
  - 檔案頂部加入 `__version__ = "0.1.0"`
- [X] T005 [P] 建立 `scripts/ssh_client.py` — netmiko SSH 封裝，包含：
  - `CiscoSSHClient` 類別，支援 context manager
  - `connect()`：根據 device_type 決定 netmiko 參數，若 None 則用 `SSHDetect` 自動偵測
  - `disconnect()`：斷開連線
  - `execute_show(command) -> CommandResult`：執行 show 指令
  - `execute_config(commands: list[str]) -> CommandResult`：進入 config mode 執行設定
  - `get_device_type() -> str`：回傳偵測到的平台類型
  - 自訂例外：`CiscoSSHConnectionError`、`CiscoSSHCommandError`
  - 逾時常數：SSH_TIMEOUT=30、BANNER_TIMEOUT=30、AUTH_TIMEOUT=30
- [X] T006 [P] 建立 `scripts/formatter.py` — 輸出排版美化，包含：
  - `format_output(raw, command) -> str`：主入口，根據指令類型路由
  - `format_table_output(raw) -> str`：空白分隔輸出轉 Markdown 表格
  - `format_config_output(raw) -> str`：設定輸出加入縮排與分段
  - `format_routing_output(raw) -> str`：路由表美化
  - `strip_ansi(raw) -> str`：移除 ANSI 控制字元
  - `strip_command_echo(raw, command) -> str`：移除指令回顯與提示符

**Checkpoint**: 基礎元件就緒，可開始實作指令模組與編排邏輯

---

## Phase 3: 平台指令模組

**Purpose**: 各 Cisco 平台的指令映射與建構

### IOS / IOS-XE

- [X] T007 [P] 建立 `scripts/commands/ios.py` — IOS/IOS-XE 指令模組：
  - `get_info_commands(intent: str) -> list[str]`：依意圖回傳 show 指令
  - `get_config_commands(intent: str, params: dict) -> list[str]`：依意圖回傳 config 指令
  - 常用意圖映射：interface、vlan、routing、acl、bgp、ospf、ntp、logging 等

### NX-OS

- [X] T008 [P] 建立 `scripts/commands/nxos.py` — NX-OS 指令模組：
  - 同 IOS 介面，額外處理 `feature` 啟用邏輯
  - NX-OS 特有指令差異（如 `show vlan brief`、`show port-channel summary`）

### ASA

- [X] T009 [P] 建立 `scripts/commands/asa.py` — ASA 指令模組：
  - 同統一介面，處理 ASA 特有語法（如 `show xlate`、`show conn`、`changeto context`）
  - 安全設定指令（ACL、NAT、VPN）

### IOS-XR

- [X] T010 [P] 建立 `scripts/commands/iosxr.py` — IOS-XR 指令模組：
  - 同統一介面，處理 IOS-XR 特有語法（如 `commit`、`show running-config`）
  - 電信級功能指令（MPLS、segment routing）

### 模組入口

- [X] T011 建立 `scripts/commands/__init__.py` — 平台工廠函式：
  - `get_platform_module(device_type: str)` 根據平台類型回傳對應模組

**Checkpoint**: 所有平台指令模組就緒

---

## Phase 4: 編排與 CLI

**Purpose**: 指令執行編排與使用者介面

- [X] T012 建立 `scripts/executor.py` — 執行編排邏輯：
  - `run_query(connection, intent) -> ExecutionResult`：查詢流程（連線 → 偵測平台 → 取得 show 指令 → 執行 → 格式化 → 回傳）
  - `run_config(connection, intent, params) -> ExecutionResult`：設定流程（連線 → 偵測平台 → 產生 config 指令 → 確認 → 執行 → 驗證 → 回傳）
  - 使用 `CiscoSSHClient` context manager 確保連線正確關閉
- [X] T013 建立 `scripts/main.py` — CLI 進入點（click.group）：
  - `query` 子指令：--host、--username、--password（hide_input）、--device-type、--enable-password、--port、--intent
  - `config` 子指令：同上加 --params
  - 共用選項：--json-output、--yes（跳過確認）、--verbose
  - 缺少必填資訊時以 prompt=True 主動詢問（HostAddr、HostUser、HostPass）
  - 連線前顯示摘要確認（除非 --yes）
  - `@click.version_option(version="0.1.0")`
  - `if __name__ == "__main__":` 進入點保護

**Checkpoint**: CLI 可執行查詢與設定指令

---

## Phase 5: 參考文件

**Purpose**: 建立各平台指令參考文件，供 AI Agent 使用技能時作為指令選擇依據

- [X] T014 [P] 建立 `references/ios-commands.md` — IOS/IOS-XE 常用指令參考（show 指令清單、config 範例、提示符格式）
- [X] T015 [P] 建立 `references/nxos-commands.md` — NX-OS 常用指令參考（含 feature 啟用、NX-OS 特有指令）
- [X] T016 [P] 建立 `references/asa-commands.md` — ASA 常用指令參考（安全指令、context 切換）
- [X] T017 [P] 建立 `references/iosxr-commands.md` — IOS-XR 常用指令參考（commit 機制、電信級功能）

**Checkpoint**: 參考文件完成

---

## Phase 6: Polish（收尾優化）

**Purpose**: 整合驗證與程式碼品質

- [X] T018 版本號一致性檢查：確認 SKILL.md frontmatter `version`、main.py `click.version_option`、models.py `__version__` 皆為 `0.1.0`
- [X] T019 程式碼清理：確保函式長度 < 50 行、命名清晰、移除冗餘
- [X] T020 SKILL.md 最終校對：確認所有腳本路徑、參考文件路徑正確

---

## 依賴關係與執行順序

### 階段依賴

- **Phase 1 (Setup)**: 無依賴，立即開始
- **Phase 2 (Foundational)**: 依賴 Phase 1，**阻擋後續所有階段**
- **Phase 3 (平台指令)**: 依賴 Phase 2 的 models.py
- **Phase 4 (編排與 CLI)**: 依賴 Phase 2 + Phase 3
- **Phase 5 (參考文件)**: 無程式碼依賴，可與 Phase 3/4 並行
- **Phase 6 (Polish)**: 依賴所有前置階段完成

### 並行機會

- T002, T003 可並行
- T004, T005, T006 可並行
- T007, T008, T009, T010 可並行（各平台獨立）
- T014, T015, T016, T017 可並行（參考文件獨立）
- Phase 5 可與 Phase 3/4 並行開發

---

## 驗證方式

| 階段 | 驗證方式 |
|------|----------|
| Phase 2 | `python -c "from models import ConnectionInfo; print('OK')"` |
| Phase 3 | `python -c "from commands import get_platform_module; print('OK')"` |
| Phase 4 - query | `python main.py query --host <IP> --username <user> --password <pass> --intent "show interfaces"` |
| Phase 4 - config | `python main.py config --host <IP> --username <user> --password <pass> --intent "set hostname"` |
| Phase 4 - version | `python main.py --version` → 輸出 `0.1.0` |
| Phase 6 | 確認三處版本號一致 |

---

## 摘要

| 項目 | 數值 |
|------|------|
| 總任務數 | 25 |
| Phase 1 (Setup) | 3 |
| Phase 2 (Foundational) | 3 |
| Phase 3 (平台指令) | 5 |
| Phase 4 (編排與 CLI) | 2 |
| Phase 5 (參考文件) | 4 |
| Phase 6 (Polish) | 3 |
| Phase 7 (Bugfix) | 5 |
| 可並行任務 | 13（標記 [P]）|

### MVP 範圍（建議）

先完成 Phase 1–4（T001–T013），共 13 個任務，即可執行 Cisco 設備的查詢與設定功能。Phase 5 參考文件可後續補充。

---

## Phase 7: Bugfix（實機測試修正）

**Purpose**: 修正實機測試與非互動環境部署發現的問題

- [X] T021 修正 `scripts/formatter.py`：分隔線正規式 `^[-=]+$` → `^[-=\s]+$` 以處理含空格的分隔線（如 `show vlan brief`）
- [X] T022 修正 `scripts/formatter.py`：最後一欄不額外填充，避免 Ports 欄過長
- [X] T023 新增 `scripts/formatter.py` `_find_split_gap()` 函式：在 ±3 字元範圍內自動修正欄位分割偏移（修復 `show interfaces status` Duplex/Speed 欄位錯位）
- [X] T024 修正 `scripts/main.py`：非互動式終端（`sys.stdin.isatty() == False`）自動跳過確認提示，避免在 agent / pipeline 環境中卡在 `確認執行？ [y/N]:` 造成逾時
- [X] T025 更新 `SKILL.md` 工作流程範例：所有指令加上 `--yes --verbose`，並加入非互動式環境注意事項

---

## 備註

- [P] 任務 = 不同檔案、無依賴，可並行執行
- 每完成一個任務或邏輯群組後 commit
- 在每個 Checkpoint 停下來驗證該階段的獨立性
- 所有 Python 模組統一使用 `__version__ = "0.1.0"` 常數
- 連線資訊提示格式：HostAddr: 0.0.0.0 / HostUser: username / HostPass: password