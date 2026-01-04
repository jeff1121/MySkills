# Tasks: K8S-Installer Skill

**Input**: Design documents from `/specs/001-skill-framework/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: 規格中未明確要求 TDD，測試任務為 OPTIONAL（本版本不包含）。

**Organization**: 任務按 User Story 分組，每個故事可獨立實作與測試。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可並行執行（不同檔案、無依賴）
- **[Story]**: 所屬 User Story（US1, US2, US3）
- 包含完整檔案路徑

## Path Conventions

本專案採用獨立 Skill 資料夾結構：
- **Skill 根目錄**: `K8S-Installer/`
- **測試目錄**: `K8S-Installer/tests/`

---

## Phase 1: Setup（專案初始化）

**Purpose**: 建立專案結構與基礎設定

- [X] T001 建立 K8S-Installer 專案資料夾結構
- [X] T002 建立 K8S-Installer/requirements.txt（paramiko>=3.0.0, click>=8.0.0, pyyaml>=6.0）
- [X] T003 [P] 建立 K8S-Installer/skill.yaml（Skill 定義檔，依據 contracts/skill-definition.yaml）

---

## Phase 2: Foundational（基礎元件）

**Purpose**: 所有 User Story 共用的核心模組

**⚠️ CRITICAL**: 此階段完成前，不可開始任何 User Story

- [X] T004 [P] 建立 K8S-Installer/models.py（NodeConnection, ClusterConfig, ExecutionResult 資料類別）
- [X] T005 [P] 建立 K8S-Installer/ssh_client.py（SSHClient 封裝，含連線、執行命令、錯誤處理）
- [X] T006 [P] 建立 K8S-Installer/config_loader.py（YAML 設定檔載入與驗證）
- [X] T007 建立 K8S-Installer/prompts.py（Click 互動式提示：collect_node_info, collect_cluster_nodes）

**Checkpoint**: 基礎元件就緒，可開始實作 User Stories

---

## Phase 3: User Story 1 - 執行單一 Skill (Priority: P1) 🎯 MVP

**Goal**: 使用者可透過 CLI 執行 K8S 安裝，提供節點連線資訊後自動完成叢集安裝

**Independent Test**: 執行 `python main.py install` 互動模式或 `--config cluster.yaml` 設定檔模式，驗證安裝流程

### Implementation for User Story 1

- [X] T008 [P] [US1] 建立 K8S-Installer/commands/install_scripts.py（前置作業腳本：disable swap, load modules, sysctl）
- [X] T009 [P] [US1] 建立 K8S-Installer/commands/package_scripts.py（套件安裝腳本：containerd, kubeadm, kubelet, kubectl）
- [X] T010 [P] [US1] 建立 K8S-Installer/commands/cluster_scripts.py（叢集腳本：kubeadm init, flannel, kubeadm join）
- [X] T011 [US1] 建立 K8S-Installer/installer.py（K8SInstaller 類別：orchestrate 安裝流程，呼叫 ssh_client 執行腳本）
- [X] T012 [US1] 建立 K8S-Installer/main.py（CLI 進入點：install 命令，支援互動模式與 --config 模式）
- [X] T013 [US1] 實作 install 命令的錯誤處理與友善訊息（連線失敗、安裝失敗等情境）
- [X] T014 [US1] 實作 install 命令的執行結果輸出（JSON 格式，含 join_command）

**Checkpoint**: User Story 1 完成，可獨立執行 K8S 安裝

---

## Phase 4: User Story 2 - 查看可用 Skills 清單 (Priority: P2)

**Goal**: 使用者可列出所有已安裝的 Skills，包含名稱與簡短描述

**Independent Test**: 執行 `python main.py list` 驗證輸出格式

### Implementation for User Story 2

- [X] T015 [US2] 建立 K8S-Installer/skill_loader.py（載入 skill.yaml、解析 SkillDefinition）
- [X] T016 [US2] 在 K8S-Installer/main.py 新增 list 命令（顯示 Skill 名稱、描述、版本）
- [X] T017 [US2] 實作空 Skills 情境的友善提示訊息

**Checkpoint**: User Story 2 完成，可獨立執行 list 命令

---

## Phase 5: User Story 3 - 查看 Skill 詳細資訊 (Priority: P3)

**Goal**: 使用者可查看特定 Skill 的完整說明、參數定義、使用範例

**Independent Test**: 執行 `python main.py info k8s-installer` 驗證輸出內容

### Implementation for User Story 3

- [X] T018 [US3] 在 K8S-Installer/main.py 新增 info 命令（顯示完整 Skill 資訊）
- [X] T019 [US3] 實作參數定義格式化輸出（名稱、型別、必填、預設值、描述）
- [X] T020 [US3] 實作 Skill 不存在時的錯誤訊息

**Checkpoint**: User Story 3 完成，可獨立執行 info 命令

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 改善與跨功能優化

- [X] T021 [P] 更新 K8S-Installer/README.md（使用說明，引用 quickstart.md 內容）
- [X] T022 [P] 新增 K8S-Installer/validate 命令（驗證節點連線，依據 cli-interface.md）
- [X] T023 執行 quickstart.md 驗證流程（確認文件與實作一致）
- [X] T024 程式碼清理：確保函式長度 < 50 行、命名清晰

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 無依賴，可立即開始
- **Phase 2 (Foundational)**: 依賴 Phase 1 完成，**阻擋所有 User Stories**
- **Phase 3-5 (User Stories)**: 依賴 Phase 2 完成
  - 可按優先級順序執行 (P1 → P2 → P3)
  - 或並行開發（如有多人）
- **Phase 6 (Polish)**: 依賴所有 User Stories 完成

### User Story Dependencies

- **User Story 1 (P1)**: 依賴 Phase 2，無其他故事依賴
- **User Story 2 (P2)**: 依賴 Phase 2，使用 skill_loader.py（與 US1 獨立）
- **User Story 3 (P3)**: 依賴 Phase 2 + US2 的 skill_loader.py

### Within Each User Story

- 腳本檔案 (T008-T010) 可並行
- installer.py 依賴腳本檔案
- main.py 命令依賴 installer.py

### Parallel Opportunities

- T003 與 T001-T002 可並行
- T004, T005, T006 可並行
- T008, T009, T010 可並行
- T021, T022 可並行

---

## Parallel Example: User Story 1

```bash
# 並行啟動腳本建立任務：
Task T008: "建立 install_scripts.py"
Task T009: "建立 package_scripts.py"
Task T010: "建立 cluster_scripts.py"

# 等待上述完成後，依序執行：
Task T011: "建立 installer.py"
Task T012: "建立 main.py install 命令"
```

---

## Implementation Strategy

### MVP First (僅 User Story 1)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational（**關鍵阻擋點**）
3. 完成 Phase 3: User Story 1
4. **停止並驗證**: 測試 K8S 安裝流程
5. 可交付 Demo（MVP 完成！）

### Incremental Delivery

1. Setup + Foundational → 基礎就緒
2. + User Story 1 → 可執行安裝（**MVP!**）
3. + User Story 2 → 可列出 Skills
4. + User Story 3 → 可查看詳細資訊
5. + Polish → 完整版本

---

## Summary

| 項目 | 數值 |
|------|------|
| 總任務數 | 24 |
| Phase 1 (Setup) | 3 |
| Phase 2 (Foundational) | 4 |
| User Story 1 (P1) | 7 |
| User Story 2 (P2) | 3 |
| User Story 3 (P3) | 3 |
| Phase 6 (Polish) | 4 |
| 可並行任務 | 11 (標記 [P]) |

### MVP Scope (建議)

僅實作至 **User Story 1 (T001-T014)**，共 14 個任務，可獨立交付 K8S 安裝功能。

### 每個 User Story 的獨立測試標準

| Story | 測試方式 |
|-------|----------|
| US1 | `python main.py install --config cluster.yaml` 完成安裝 |
| US2 | `python main.py list` 顯示 Skill 清單 |
| US3 | `python main.py info k8s-installer` 顯示詳細資訊 |

---

## Notes

- [P] 任務 = 不同檔案、無依賴，可並行
- [Story] 標籤 = 追蹤任務所屬 User Story
- 每個 User Story 應可獨立完成與測試
- 每完成一個任務或邏輯群組後 commit
- 在任何 checkpoint 停下來驗證故事獨立性
- 避免：模糊任務、同檔案衝突、跨故事依賴
