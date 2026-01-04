# Implementation Plan: K8S-Installer Skill

**Branch**: `001-skill-framework` | **Date**: 2026-01-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-skill-framework/spec.md`

## Summary

建立第一個 AI Agent Skill「K8S-Installer」，透過 Python 實作 SSH 連線，自動化完成 Kubernetes 叢集的安裝設定。使用者提供 5 個節點的連線資訊（HostAddr、HostPort、HostUser、HostPass），系統將自動執行作業系統更新、K8S 套件安裝、Cluster 設定。

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: paramiko (SSH)、PyYAML (設定檔)、click (CLI)  
**Storage**: YAML 檔案（Skill 定義與節點設定）  
**Testing**: pytest  
**Target Platform**: Linux/macOS（執行端）→ Ubuntu/Debian（目標節點）  
**Project Type**: Single project（每個 Skill 獨立資料夾）  
**Performance Goals**: 單一 SSH 命令執行 < 30 秒回應  
**Constraints**: SSH 連線逾時 30 秒、支援 5 節點並行連線  
**Scale/Scope**: 單一 K8S Cluster（1 master + 4 workers 或類似配置）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 狀態 | 說明 |
|------|------|------|
| I. 程式碼品質 | ✅ PASS | 函式保持單一職責，SSH 操作與業務邏輯分離 |
| II. 測試標準 | ✅ PASS | 核心邏輯（參數驗證、設定解析）有單元測試 |
| III. 使用者體驗一致性 | ✅ PASS | 錯誤訊息友善，提示缺少參數或連線失敗原因 |
| IV. 效能要求 | ✅ PASS | SSH 連線有逾時設定，避免無限等待 |
| MVP 開發原則 | ✅ PASS | 從單一 Skill 開始，不預先建立複雜框架 |

## Project Structure

### Documentation (this feature)

```text
specs/001-skill-framework/
├── plan.md              # 本檔案
├── research.md          # Phase 0 研究結果
├── data-model.md        # Phase 1 資料模型
├── quickstart.md        # Phase 1 快速開始指南
└── contracts/           # Phase 1 介面契約
```

### Source Code (repository root)

```text
K8S-Installer/
├── skill.yaml           # Skill 定義檔（名稱、描述、參數）
├── main.py              # 進入點
├── ssh_client.py        # SSH 連線封裝
├── installer.py         # K8S 安裝邏輯
├── prompts.py           # 使用者互動提示
├── requirements.txt     # Python 依賴
└── tests/
    ├── test_ssh_client.py
    └── test_installer.py
```

**Structure Decision**: 選擇獨立資料夾結構，每個 Skill 自包含所有程式碼與設定，符合 FR-002 需求「每個 Skill MUST 獨立存放於自己的資料夾內」。

## Complexity Tracking

> 無違反憲章原則，無需記錄複雜度理由。
