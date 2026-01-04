---
name: k8s-installer
description: 自動化安裝 Kubernetes 叢集。當使用者要求安裝 K8S、建立 Kubernetes cluster、或詢問如何自動化部署 K8S 時使用此 Skill。透過 SSH 連線到目標節點，自動完成前置作業、套件安裝、叢集初始化與 Worker 加入。
---

# K8S-Installer

## Overview

自動化安裝 Kubernetes 叢集的 AI Agent Skill。透過 SSH 連線到目標 Linux 節點，依序執行前置作業、安裝 containerd 與 kubeadm 套件、初始化 Control Plane、安裝 Flannel CNI 網路外掛，並將 Worker 節點加入叢集。

## When to Use This Skill

使用此 Skill 當使用者：
- 要求「幫我安裝 K8S」或「建立 Kubernetes 叢集」
- 提供節點 IP 位址並詢問如何部署 K8S
- 詢問「如何自動化安裝 Kubernetes」
- 需要在多台 Linux 伺服器上建立 K8S 叢集
- 有 SSH 存取權限的伺服器並想要部署容器平台

## Prerequisites

### 執行環境（AI Agent 端）
- 可執行 Python 3.11+ 腳本
- 需要 `paramiko`（SSH）、`click`（CLI）、`pyyaml`（設定檔）套件

### 目標節點（要安裝 K8S 的伺服器）
- Oracle Linux 9+ 或其他 RHEL 相容系統
- 每節點至少 2 CPU、2GB RAM
- 節點間網路互通（Control Plane 需開放 6443 port）
- SSH 存取權限（root 或具 sudo 權限的使用者）
- 需要 internet 連線以下載套件

## Parameters

向使用者收集以下資訊：

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| control_plane_host | string | ✓ | Control Plane 節點的 IP 位址或域名 |
| control_plane_user | string | ✓ | SSH 使用者名稱 |
| control_plane_password | string | ✓ | SSH 密碼（敏感資訊，不要顯示） |
| control_plane_port | int | | SSH 連接埠，預設 22 |
| worker_nodes | list | ✓ | Worker 節點列表，每個包含 host、user、password |
| pod_network_cidr | string | | Pod 網路 CIDR，預設 10.244.0.0/16 |

### 參數收集對話範例

```
我需要以下資訊來安裝 K8S 叢集：

=== Control Plane 節點 ===
1. Control Plane 的 IP 位址是什麼？
2. SSH 使用者名稱？（例如：root）
3. SSH 密碼？

=== Worker 節點 ===
4. 有幾個 Worker 節點要加入？
5. 請提供每個 Worker 的 IP、使用者名稱、密碼

=== 網路設定（選填）===
6. Pod 網路 CIDR？（預設 10.244.0.0/16）
```

## Execution Workflow

### Step 1: 驗證連線

在開始安裝前，先測試所有節點的 SSH 連線：

```python
# 對每個節點執行連線測試
ssh {user}@{host} -p {port} "echo 'Connection OK'"
```

如果連線失敗，報告錯誤並請使用者確認：
- SSH 服務是否啟動
- 防火牆是否允許 22 port
- 使用者名稱密碼是否正確

### Step 2: 前置作業（所有節點）

在每個節點執行：

**2.1 停用 Swap**
```bash
swapoff -a
sed -i '/swap/d' /etc/fstab
```

**2.2 載入核心模組**
```bash
cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

modprobe overlay
modprobe br_netfilter
```

**2.3 設定 Sysctl 參數**
```bash
cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sysctl --system
```

### Step 3: 安裝套件（所有節點）

**3.1 安裝 Containerd**
```bash
dnf install -y containerd
mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
systemctl enable --now containerd
```

**3.2 安裝 Kubernetes 套件**
```bash
cat <<EOF | tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.29/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.29/rpm/repodata/repomd.xml.key
EOF

dnf install -y kubelet kubeadm kubectl
systemctl enable --now kubelet
```

### Step 4: 初始化 Control Plane

僅在 Control Plane 節點執行：

**4.1 執行 kubeadm init**
```bash
kubeadm init --pod-network-cidr={pod_network_cidr}
```

**4.2 設定 kubectl**
```bash
mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config
```

**4.3 安裝 Flannel CNI**
```bash
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
```

### Step 5: Worker 加入叢集

**5.1 從 Control Plane 取得 Join 命令**
```bash
kubeadm token create --print-join-command
```

**5.2 在每個 Worker 執行 Join 命令**
```bash
kubeadm join {control_plane_ip}:6443 --token {token} --discovery-token-ca-cert-hash sha256:{hash}
```

### Step 6: 驗證安裝

在 Control Plane 執行：
```bash
kubectl get nodes
```

預期輸出：
```
NAME      STATUS   ROLES           AGE   VERSION
master    Ready    control-plane   5m    v1.29.0
worker1   Ready    <none>          3m    v1.29.0
worker2   Ready    <none>          3m    v1.29.0
```

## Output

安裝完成後，回報以下資訊給使用者：

```
✅ K8S 叢集安裝完成！

叢集資訊：
- Control Plane: {control_plane_ip}
- Worker 節點: {worker_count} 個
- Pod 網路: {pod_network_cidr}
- Kubernetes 版本: v1.29.0

📋 Join 命令（供未來新增 Worker 使用）：
kubeadm join {control_plane_ip}:6443 --token {token} --discovery-token-ca-cert-hash sha256:{hash}

下一步：
1. SSH 登入 Control Plane: ssh {user}@{control_plane_ip}
2. 檢查節點狀態: kubectl get nodes
3. 部署第一個應用: kubectl create deployment nginx --image=nginx
```

## Error Handling

### SSH 連線失敗
```
❌ 無法連線到 {host}
可能原因：
- SSH 服務未啟動：systemctl status sshd
- 防火牆阻擋：firewall-cmd --add-port=22/tcp --permanent
- 密碼錯誤
請確認後重試。
```

### kubeadm init 失敗
```
❌ Control Plane 初始化失敗
可能原因：
- CPU 或記憶體不足（需至少 2 CPU、2GB RAM）
- swap 未停用：free -h 確認 swap 為 0
- 已有 K8S 殘留：kubeadm reset -f
錯誤訊息：{error_message}
```

### Worker 加入失敗
```
❌ Worker {host} 無法加入叢集
可能原因：
- 無法連線 Control Plane 6443 port
- Token 已過期（24 小時有效）
- 網路不通
請確認後重試，或重新產生 token：kubeadm token create --print-join-command
```

## Scripts Location

此 Skill 的執行腳本位於 `scripts/` 目錄：
- `install.py` - 主要安裝腳本
- `ssh_client.py` - SSH 連線封裝
- `config.py` - 設定檔處理

## References

參考文件位於 `references/` 目錄：
- `kubeadm_setup.md` - kubeadm 官方安裝指南
- `troubleshooting.md` - 常見問題排除
- `oracle_linux_notes.md` - Oracle Linux 特定注意事項

## Key Principles

**收集完整資訊再執行**：
- 在開始安裝前，確保已收集所有必要的節點連線資訊
- 先驗證 SSH 連線，避免安裝到一半失敗

**逐步回報進度**：
- 每完成一個步驟，告知使用者進度
- 如果某步驟耗時較長，提供預估時間

**清楚的錯誤訊息**：
- 發生錯誤時，提供具體的原因與解決建議
- 不要只說「安裝失敗」，要說明是哪個步驟、什麼錯誤

**安全考量**：
- 密碼等敏感資訊不要顯示或記錄
- 完成後提醒使用者變更預設密碼
