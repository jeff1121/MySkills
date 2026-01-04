# MySkills - AI Agent Skills 框架

這是一個用於建立 AI Agent Skills 的專案，讓使用者可以透過自然語言對話與給定所需的屬性即可開始完成目標。

## 概念

每個 **Skill** 是一個獨立的自動化任務，例如：
- K8S-Installer：自動化安裝 Kubernetes 叢集
- （未來可擴充更多 Skills）

## 快速開始

```bash
# 安裝依賴
pip install -r requirements.txt

# 列出可用的 Skills
python skill_installer.py list

# 執行指定的 Skill
python skill_installer.py run K8S-Installer

# 查看 Skill 詳細資訊
python skill_installer.py info K8S-Installer
```

## 專案結構

```
MySkills/
├── skill_installer.py      # 統一入口 CLI
├── requirements.txt        # 框架依賴
├── K8S-Installer/          # K8S 安裝 Skill
│   ├── skill.yaml          # Skill 定義（參數、進入點）
│   ├── main.py             # 執行入口
│   ├── requirements.txt    # Skill 依賴
│   └── ...
└── <其他 Skills>/
```

## Skill 定義格式

每個 Skill 需要一個 `skill.yaml` 定義檔：

```yaml
name: my-skill
description: Skill 描述
version: 1.0.0

parameters:
  - name: param1
    type: string
    required: true
    description: 參數說明
  - name: param2
    type: int
    required: false
    default: 10

entrypoint: main.py
```

## 建立新的 Skill

1. 建立 Skill 資料夾：`mkdir MyNewSkill`
2. 建立 `skill.yaml` 定義參數
3. 建立 `main.py` 並實作 `run(params: dict)` 函式
4. 完成！使用 `python skill_installer.py run MyNewSkill` 執行

## 可用的 Skills

| Skill | 說明 |
|-------|------|
| K8S-Installer | 自動化安裝 Kubernetes 叢集 |

## 授權

MIT License
