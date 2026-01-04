# 快速開始：K8S-Installer

本文件說明如何使用 K8S-Installer 自動化安裝 Kubernetes 叢集。

## 前置需求

### 執行環境（你的電腦）

- Python 3.11+
- pip 套件管理器

### 目標節點（要安裝 K8S 的伺服器）

- Oracle Linux 9+
- 每節點至少 2 CPU、2GB RAM
- 節點間網路互通
- SSH 存取權限（root 或具 sudo 權限的使用者）

## 安裝步驟

```bash
# 1. 進入專案根目錄
cd MySkills

# 2. 安裝框架依賴
pip install -r requirements.txt

# 3. 安裝 K8S-Installer 依賴
pip install -r K8S-Installer/requirements.txt
```

## 使用方式

### 方式一：透過 Skill Installer 框架（推薦）

```bash
# 列出可用的 Skills
python skill_installer.py list

# 執行 K8S-Installer
python skill_installer.py run K8S-Installer
```

系統會根據 `skill.yaml` 定義的參數，自動引導你輸入：

```
📦 k8s-installer - K8S 安裝設定代理 - 自動化 Kubernetes 叢集安裝

=== Control Plane (Master) 節點連線資訊 ===
  主機 IP 地址或域名: 192.168.1.100
  SSH 連接埠 [22]: ↵
  SSH 使用者名稱: root
  SSH 密碼: ********

=== Worker 節點連線資訊列表（建議 1-10 個） ===
  節點數量: 2

--- 節點 1 ---
  主機 IP 地址或域名: 192.168.1.101
  SSH 連接埠 [22]: ↵
  SSH 使用者名稱: root
  SSH 密碼: ********

--- 節點 2 ---
  主機 IP 地址或域名: 192.168.1.102
  SSH 連接埠 [22]: ↵
  SSH 使用者名稱: root
  SSH 密碼: ********

  Pod 網路 CIDR 範圍 [10.168.0.0/16]: ↵

==================================================
即將執行安裝，參數如下：
  control_plane:
    host: 192.168.1.100
    port: 22
    user: root
    password: ********
  workers:
    [1]
      host: 192.168.1.101
      ...

確認開始執行？ [y/N]: y

🚀 開始執行...
```

### 方式二：直接執行 K8S-Installer CLI

```bash
cd K8S-Installer
python main.py install
```

### 方式三：設定檔模式（適合自動化）

1. 建立 `cluster.yaml` 設定檔：

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

pod_network_cidr: 10.244.0.0/16
```

2. 使用設定檔執行安裝：

```bash
python main.py install -c cluster.yaml
```

3. 跳過確認提示（自動化場景）：

```bash
python main.py install -c cluster.yaml -y
```

4. JSON 格式輸出（供程式整合）：

```bash
python main.py install -c cluster.yaml --json-output
```

## 其他命令

### 列出可用的 Skills

```bash
python main.py list
```

### 查看 Skill 詳細資訊

```bash
python main.py info k8s-installer
```

### 驗證設定檔

```bash
python main.py validate -c cluster.yaml
```

## 驗證安裝結果

安裝完成後，SSH 登入 Control Plane 節點：

```bash
ssh root@192.168.1.100

# 檢查節點狀態
kubectl get nodes
```

預期輸出：

```
NAME      STATUS   ROLES           AGE   VERSION
master    Ready    control-plane   5m    v1.29.0
worker1   Ready    <none>          3m    v1.29.0
worker2   Ready    <none>          3m    v1.29.0
```

## 安裝流程說明

K8S-Installer 會依序執行以下步驟：

| 階段 | 步驟 | 說明 |
|------|------|------|
| 前置作業 | 停用 Swap | K8S 要求停用 swap |
| | 載入核心模組 | overlay, br_netfilter |
| | 設定 Sysctl | 網路轉發參數 |
| 套件安裝 | 安裝 Containerd | 容器執行時 |
| | 安裝 K8S 套件 | kubeadm, kubelet, kubectl |
| 叢集初始化 | kubeadm init | 初始化 Control Plane |
| | 安裝 Flannel | CNI 網路外掛 |
| | 取得 Join 命令 | 供 Worker 加入 |
| Worker 加入 | kubeadm join | 各 Worker 加入叢集 |

## 常見問題

### SSH 連線失敗

確認以下項目：
- 目標節點 SSH 服務已啟動（`systemctl status sshd`）
- 防火牆允許 22 port（`ufw allow 22`）
- 使用者名稱與密碼正確

### kubeadm init 失敗

確認以下項目：
- 節點有足夠的 CPU（≥2）與記憶體（≥2GB）
- swap 已停用（`free -h` 確認 swap 為 0）
- 無其他 K8S 安裝殘留（`kubeadm reset` 清除）

### Worker 無法加入叢集

確認以下項目：
- Worker 可連通 Control Plane 的 6443 port
- Join token 未過期（預設 24 小時有效）
- 防火牆規則正確

### 如何重置叢集？

在所有節點執行：

```bash
kubeadm reset -f
rm -rf /etc/cni/net.d
rm -rf $HOME/.kube
```

## 下一步

叢集安裝完成後，你可以：

- 部署第一個應用程式：`kubectl create deployment nginx --image=nginx`
- 設定 Ingress Controller 暴露服務
- 配置持久化儲存（PV/PVC）
- 設定監控（Prometheus + Grafana）
