# MySkills - AI Agent Skills

這是一個 AI Agent Skills 集合，可安裝到 Claude CLI、Codex CLI、Copilot CLI 等 AI 工具中使用。

## 什麼是 Skill？

Skill 是一份 `SKILL.md` 文件，定義了 AI Agent 應如何執行特定任務。當使用者提出相關需求時，AI 會讀取 SKILL.md 並依照其中的指示完成工作。

## 專案結構

```
MySkills/
└── skills/
    └── k8s-installer/
        ├── SKILL.md              # Skill 定義（必要）
        ├── references/           # 參考文件
        │   ├── kubeadm_setup.md
        │   ├── troubleshooting.md
        │   └── oracle_linux_notes.md
        └── scripts/              # 執行腳本（選用）
            ├── main.py
            ├── installer.py
            └── ...
```

## 安裝到 AI CLI

### Claude CLI

```bash
# 加入到 Claude CLI 的 skills 目錄
claude skill add https://github.com/jeff1121/MySkills/skills/k8s-installer
```

### 手動安裝

將 `skills/k8s-installer/` 目錄複製到你的 AI 工具的 skills 目錄中。

## 使用方式

安裝後，直接對 AI 說：

> 「幫我安裝 K8S 叢集」

AI 會讀取 SKILL.md，然後：
1. 收集必要的節點連線資訊
2. 依照 Execution Workflow 逐步執行
3. 回報安裝進度與結果

## 可用的 Skills

| Skill | 說明 |
|-------|------|
| [k8s-installer](skills/k8s-installer/SKILL.md) | 自動化安裝 Kubernetes HA 叢集（Calico CNI + MetalLB LoadBalancer） |

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

## 授權

MIT License
