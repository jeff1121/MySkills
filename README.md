# MySkills - AI Agent Skills

這是一個 AI Agent Skills 集合，可安裝到 Claude CLI、Codex CLI、Copilot CLI 等 AI 工具中使用。

## 什麼是 Skill？

Skill 是一份 `SKILL.md` 文件，定義了 AI Agent 應如何執行特定任務。當使用者提出相關需求時，AI 會讀取 SKILL.md 並依照其中的指示完成工作。

## 專案結構

```
MySkills/
├── skills/                   # 各 Skill 獨立目錄
│   └── <skill-name>/
│       ├── SKILL.md          # Skill 定義（必要）
│       ├── references/       # 參考文件（選用）
│       └── scripts/          # 執行腳本（選用）
├── .github/
│   ├── agents/               # Copilot Agent 定義（speckit）
│   ├── prompts/              # Copilot Prompt 定義
│   ├── workflows/            # GitHub Actions CI
│   └── ISSUE_TEMPLATE/       # Issue 模板
├── .specify/                 # 專案治理（templates、scripts、constitution）
├── specs/                    # 功能規格文件
├── pyproject.toml            # 統一 lint/test 設定
└── Makefile                  # 開發命令
```

## 安裝到 AI CLI

### Claude CLI

```bash
# 加入到 Claude CLI 的 skills 目錄（以 k8s-installer 為例）
claude skill add https://github.com/jeff1121/MySkills/skills/k8s-installer
```

### Copilot CLI (GitHub Copilot)

在 `.github/agents/` 安裝 skill，或手動複製 skill 目錄。

### 手動安裝

將 `skills/<skill-name>/` 目錄複製到你的 AI 工具的 skills 目錄中。

## 使用方式

安裝後，直接對 AI 說：

> 「幫我安裝 K8S 叢集」

AI 會讀取 SKILL.md，然後：
1. 收集必要的節點連線資訊
2. 依照 Execution Workflow 逐步執行
3. 回報安裝進度與結果

## 可用的 Skills

| Skill | 版本 | 說明 |
|-------|------|------|
| [canvas-design](skills/canvas-design/SKILL.md) | — | 設計哲學驅動的視覺藝術創作（海報、資訊圖表、封面） |
| [cisco-configer](skills/cisco-configer/SKILL.md) | 0.1.0 | 透過 SSH 連線 Cisco 網路設備（IOS/NX-OS/ASA/IOS-XR）查詢與設定 |
| [elk-installer](skills/elk-installer/SKILL.md) | 1.1.0 | 自動化安裝 Elastic Stack（Elasticsearch、Logstash、Kibana、Fleet Server） |
| [finmind](skills/finmind/SKILL.md) | 0.1.0 | FinMind 金融數據 AI 助手 — 透過 MCP Server 查詢台股、美股等金融資料 |
| [k8s-installer](skills/k8s-installer/SKILL.md) | 1.1.2 | 自動化安裝 Kubernetes HA 叢集（Calico CNI + MetalLB LoadBalancer） |
| [pa-ngfw-manager](skills/pa-ngfw-manager/SKILL.md) | 0.1.0 | Palo Alto 新世代防火牆管理 — 異常偵測、安全策略 CRUD、組態備份還原 |
| [pdf](skills/pdf/SKILL.md) | — | PDF 處理工具集 — 表單填寫、文字提取、頁面操作、影像轉換 |
| [pptx](skills/pptx/SKILL.md) | — | PowerPoint 簡報建立、編輯與分析 |
| [video-downloader](skills/video-downloader/SKILL.md) | — | 下載線上影片（YouTube 等），支援格式選擇、字幕與播放清單處理 |
| [webapp-testing](skills/webapp-testing/SKILL.md) | — | Web 應用程式測試工具集（Playwright） |

## 建立新的 Skill

1. 建立 Skill 資料夾：`mkdir skills/my-new-skill`
2. 建立 `SKILL.md`，包含：
   - YAML frontmatter（name, description）
   - Overview（概述）
   - When to Use（使用時機）
   - Parameters（需收集的參數）
   - Execution Workflow（執行步驟）
   - Output（輸出格式）
   - Error Handling（錯誤處理）
3. 選擇性加入 `references/` 參考文件
4. 選擇性加入 `scripts/` 執行腳本

## SKILL.md 格式

```markdown
---
name: my-skill
description: 簡短描述，說明何時使用此 Skill
---

# Skill 名稱

## Overview
詳細說明此 Skill 的功能

## When to Use This Skill
列出觸發此 Skill 的使用者意圖

## Parameters
需要向使用者收集的資訊

## Execution Workflow
### Step 1: ...
### Step 2: ...

## Output
完成後應回報的資訊

## Error Handling
各種錯誤情境的處理方式
```

## 開發

```bash
# 安裝開發工具
pip install -e ".[dev]"

# 常用命令
make lint          # 執行 ruff lint
make format        # 自動格式化
make test          # 執行所有測試
make validate      # 驗證所有 SKILL.md 結構
make check         # 執行所有檢查（lint + format + validate）
```

## 授權

MIT License
