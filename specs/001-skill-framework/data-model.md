# Data Model: K8S-Installer Skill

**Date**: 2026-01-04  
**Source**: [spec.md](spec.md), [research.md](research.md)

## Entities

### 1. SkillDefinition

Skill 的元資料定義，儲存於 `skill.yaml`。

| 屬性 | 型別 | 必填 | 說明 |
|------|------|------|------|
| name | string | ✅ | Skill 唯一識別名稱 |
| description | string | ✅ | Skill 功能描述 |
| version | string | ✅ | 語意化版本號 |
| parameters | SkillParameter[] | ✅ | 參數定義列表 |

**範例**:
```yaml
name: k8s-installer
description: K8S 安裝設定代理
version: 1.0.0
parameters:
  - name: control_plane
    type: node
    required: true
    description: Control Plane 節點連線資訊
  - name: workers
    type: node[]
    required: true
    description: Worker 節點連線資訊列表
```

---

### 2. SkillParameter

定義 Skill 所需的輸入參數。

| 屬性 | 型別 | 必填 | 說明 |
|------|------|------|------|
| name | string | ✅ | 參數名稱 |
| type | string | ✅ | 參數型別：string, int, bool, node, node[] |
| required | boolean | ✅ | 是否必填 |
| default | any | ❌ | 預設值 |
| description | string | ✅ | 參數說明 |

---

### 3. NodeConnection

K8S 節點的 SSH 連線資訊。

| 屬性 | 型別 | 必填 | 說明 |
|------|------|------|------|
| host | string | ✅ | 主機 IP 或域名 |
| port | int | ❌ | SSH 連接埠，預設 22 |
| user | string | ✅ | SSH 使用者名稱 |
| password | string | ✅ | SSH 密碼 |

**驗證規則**:
- host: 有效的 IP 地址或可解析的域名
- port: 1-65535 範圍內
- user: 非空字串
- password: 非空字串

---

### 4. ClusterConfig

K8S 叢集配置。

| 屬性 | 型別 | 必填 | 說明 |
|------|------|------|------|
| control_plane | NodeConnection | ✅ | Control Plane 節點 |
| workers | NodeConnection[] | ✅ | Worker 節點列表 |
| pod_network_cidr | string | ❌ | Pod 網路 CIDR，預設 10.244.0.0/16 |

---

### 5. ExecutionResult

Skill 執行結果。

| 屬性 | 型別 | 必填 | 說明 |
|------|------|------|------|
| success | boolean | ✅ | 執行是否成功 |
| message | string | ✅ | 結果訊息 |
| output | string | ❌ | 執行輸出內容 |
| error | string | ❌ | 錯誤訊息（失敗時） |
| join_command | string | ❌ | Worker 加入指令（成功時） |

---

### 6. InstallationStep

安裝步驟狀態追蹤。

| 屬性 | 型別 | 必填 | 說明 |
|------|------|------|------|
| name | string | ✅ | 步驟名稱 |
| status | enum | ✅ | pending, running, success, failed |
| node | string | ✅ | 執行節點 |
| output | string | ❌ | 執行輸出 |
| error | string | ❌ | 錯誤訊息 |

**Status 狀態機**:
```
pending → running → success
                 ↘ failed
```

---

## Entity Relationships

```
SkillDefinition
    └── parameters: SkillParameter[]

ClusterConfig
    ├── control_plane: NodeConnection
    └── workers: NodeConnection[]

ExecutionResult
    └── (獨立，為執行輸出)

InstallationStep
    └── (獨立，為狀態追蹤)
```

---

## Data Flow

```
使用者輸入
    ↓
ClusterConfig (驗證)
    ↓
InstallationStep[] (追蹤進度)
    ↓
ExecutionResult (回傳結果)
```
