# K8S-Installer

自動化安裝 Kubernetes 叢集的 AI Agent Skill。

## 功能

- 🚀 自動化 K8S 叢集部署（使用 kubeadm）
- 🔐 透過 SSH 連線執行遠端安裝
- 📦 安裝 containerd 容器執行時
- 🌐 自動配置 Flannel CNI 網路
- 🤖 支援互動式與配置檔兩種模式

## 需求

- Python 3.11+
- 目標節點需為 Ubuntu/Debian 系統
- 目標節點需有 SSH 存取權限
- 目標節點需有 sudo 權限

## 安裝

```bash
cd K8S-Installer
pip install -r requirements.txt
```

## 使用方式

### 互動式安裝

```bash
python main.py install
```

系統將引導您輸入：
- Control Plane 節點資訊（IP、SSH 使用者、密碼/金鑰）
- Worker 節點資訊

### 使用配置檔

```bash
python main.py install -c cluster.yaml
```

配置檔範例：

```yaml
control_plane:
  host: 192.168.1.100
  user: ubuntu
  password: your-password
  # 或使用 SSH 金鑰
  # private_key_path: ~/.ssh/id_rsa

workers:
  - host: 192.168.1.101
    user: ubuntu
    password: your-password
  - host: 192.168.1.102
    user: ubuntu
    password: your-password

pod_network_cidr: 10.244.0.0/16
```

### JSON 輸出

```bash
python main.py install -c cluster.yaml --json-output
```

輸出範例：
```json
{
  "success": true,
  "message": "K8S 叢集安裝完成",
  "join_command": "kubeadm join 192.168.1.100:6443 --token xxx --discovery-token-ca-cert-hash sha256:xxx"
}
```

### 其他命令

```bash
# 列出所有 Skills
python main.py list

# 顯示 Skill 詳細資訊
python main.py info k8s-installer

# 驗證配置檔
python main.py validate -c cluster.yaml
```

## 安裝流程

1. **前置作業**
   - 停用 Swap
   - 載入必要核心模組
   - 設定 Sysctl 參數

2. **安裝套件**
   - 安裝 containerd
   - 安裝 kubeadm、kubelet、kubectl

3. **初始化叢集**
   - 在 Control Plane 執行 `kubeadm init`
   - 安裝 Flannel CNI
   - 產生 Worker 加入命令

4. **加入 Worker**
   - 在各 Worker 節點執行 join 命令

## 錯誤處理

- SSH 連線失敗會顯示詳細錯誤訊息
- 任一步驟失敗會中止安裝並報告失敗原因
- 支援 JSON 格式的錯誤輸出供自動化整合

## 授權

MIT License
