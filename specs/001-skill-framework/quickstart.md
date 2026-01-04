# Quickstart: K8S-Installer

快速開始使用 K8S-Installer 安裝 Kubernetes 叢集。

## 前置需求

### 執行環境（你的電腦）
- Python 3.11+
- pip

### 目標節點（要安裝 K8S 的伺服器）
- Ubuntu 22.04 LTS
- 每節點至少 2 CPU、2GB RAM
- 網路互通
- SSH 存取（root 或 sudo 權限）

## 安裝

```bash
# 進入 Skill 目錄
cd K8S-Installer

# 安裝依賴
pip install -r requirements.txt
```

## 使用方式

### 方式一：互動模式（推薦）

```bash
python main.py install
```

系統會引導你輸入每個節點的連線資訊：

```
📦 K8S-Installer - Kubernetes 叢集安裝工具

=== Control Plane 節點設定 ===
  HostAddr: 192.168.1.100
  HostPort [22]: ↵
  HostUser: root
  HostPass: ********

=== Worker 節點設定 ===
Worker 節點數量 [4]: 2

--- Worker 1 ---
  HostAddr: 192.168.1.101
  HostPort [22]: ↵
  HostUser: root
  HostPass: ********

--- Worker 2 ---
  HostAddr: 192.168.1.102
  HostPort [22]: ↵
  HostUser: root
  HostPass: ********

確認開始安裝？ [y/N]: y
```

### 方式二：設定檔模式

1. 建立 `cluster.yaml`：

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
```

2. 執行安裝：

```bash
python main.py install --config cluster.yaml
```

## 驗證安裝

安裝完成後，SSH 登入 Control Plane 節點：

```bash
ssh root@192.168.1.100

# 檢查節點狀態
kubectl get nodes

# 預期輸出
NAME      STATUS   ROLES           AGE   VERSION
master    Ready    control-plane   5m    v1.29.0
worker1   Ready    <none>          3m    v1.29.0
worker2   Ready    <none>          3m    v1.29.0
```

## 常見問題

### Q: SSH 連線失敗？
確認：
- 目標節點 SSH 服務已啟動
- 防火牆允許 22 port
- 使用者名稱密碼正確

### Q: kubeadm init 失敗？
確認：
- 節點有足夠的 CPU 與記憶體
- swap 已停用
- 無其他 K8S 安裝殘留

### Q: Worker 無法加入叢集？
確認：
- 網路可連通 Control Plane
- 6443 port 開放
- token 未過期（24 小時有效）

## 下一步

- 部署應用程式到叢集
- 設定 Ingress Controller
- 配置持久化儲存
