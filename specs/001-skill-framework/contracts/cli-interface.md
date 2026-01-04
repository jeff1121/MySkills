# CLI Interface Contract

**Purpose**: 定義 K8S-Installer 的命令列介面

## Commands

### 1. Install Command

啟動 K8S 叢集安裝流程。

```bash
# 互動模式（提示輸入節點資訊）
python main.py install

# 使用設定檔
python main.py install --config cluster.yaml
```

**Options**:
| 選項 | 型別 | 必填 | 說明 |
|------|------|------|------|
| --config, -c | string | ❌ | 叢集設定檔路徑 |
| --dry-run | flag | ❌ | 只驗證不執行 |
| --verbose, -v | flag | ❌ | 顯示詳細輸出 |

**互動式提示流程**:
```
📦 K8S-Installer - Kubernetes 叢集安裝工具

=== Control Plane 節點設定 ===
  HostAddr: 192.168.1.100
  HostPort [22]: 
  HostUser: root
  HostPass: ********

=== Worker 節點設定 ===
Worker 節點數量 [4]: 3

--- Worker 1 ---
  HostAddr: 192.168.1.101
  HostPort [22]: 
  HostUser: root
  HostPass: ********

[繼續 Worker 2, 3...]

確認開始安裝？ [y/N]: y
```

**Output (Success)**:
```json
{
  "success": true,
  "message": "K8S 叢集安裝完成",
  "cluster": {
    "control_plane": "192.168.1.100",
    "workers": ["192.168.1.101", "192.168.1.102", "192.168.1.103"],
    "join_command": "kubeadm join 192.168.1.100:6443 --token xxx --discovery-token-ca-cert-hash sha256:xxx"
  }
}
```

**Output (Failure)**:
```json
{
  "success": false,
  "message": "安裝失敗於步驟：初始化 Control Plane",
  "error": "SSH 連線失敗：Connection refused",
  "failed_node": "192.168.1.100"
}
```

---

### 2. Validate Command

驗證節點連線與前置條件。

```bash
python main.py validate --config cluster.yaml
```

**Output**:
```json
{
  "success": true,
  "nodes": [
    {"host": "192.168.1.100", "ssh": "ok", "os": "Ubuntu 22.04"},
    {"host": "192.168.1.101", "ssh": "ok", "os": "Ubuntu 22.04"},
    {"host": "192.168.1.102", "ssh": "failed", "error": "Auth failed"}
  ]
}
```

---

### 3. Status Command

檢查已安裝叢集的狀態。

```bash
python main.py status --control-plane 192.168.1.100
```

**Output**:
```json
{
  "success": true,
  "cluster_status": "healthy",
  "nodes": [
    {"name": "master", "status": "Ready", "role": "control-plane"},
    {"name": "worker-1", "status": "Ready", "role": "worker"},
    {"name": "worker-2", "status": "Ready", "role": "worker"}
  ]
}
```

---

## Exit Codes

| Code | 說明 |
|------|------|
| 0 | 成功 |
| 1 | 一般錯誤 |
| 2 | 參數錯誤 |
| 3 | SSH 連線失敗 |
| 4 | 安裝步驟失敗 |

---

## Configuration File Format

`cluster.yaml`:
```yaml
control_plane:
  host: 192.168.1.100
  port: 22
  user: root
  password: your_password

workers:
  - host: 192.168.1.101
    port: 22
    user: root
    password: your_password
  - host: 192.168.1.102
    port: 22
    user: root
    password: your_password
  - host: 192.168.1.103
    port: 22
    user: root
    password: your_password
  - host: 192.168.1.104
    port: 22
    user: root
    password: your_password

pod_network_cidr: 10.244.0.0/16
```
