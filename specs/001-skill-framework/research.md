# Research: K8S-Installer Skill

**Date**: 2026-01-04  
**Purpose**: 解決 Technical Context 中的技術選型問題

## 1. SSH 連線方案

### Decision: Paramiko + SSHClient

**Rationale**: 
- Python 原生 SSH 套件，高階 API 易於使用
- 內建處理認證、傳輸層細節
- 廣泛使用，文件完整

**Alternatives Considered**:
| 方案 | 排除原因 |
|------|----------|
| Fabric | 額外依賴，功能過多 |
| subprocess + ssh | 難以處理密碼認證 |
| AsyncSSH | 異步複雜度增加，MVP 不需要 |

### 最佳實踐

```python
# 連線設定
client = SSHClient()
client.set_missing_host_key_policy(AutoAddPolicy())
client.connect(
    hostname=host,
    port=port,
    username=user,
    password=password,
    timeout=30,           # 連線逾時
    banner_timeout=30,    # SSH banner 逾時
    auth_timeout=30       # 認證逾時
)
```

### 錯誤處理

必須處理的例外：
- `AuthenticationException`: 認證失敗
- `NoValidConnectionsError`: 無法連線
- `socket.timeout`: 連線逾時

---

## 2. Kubernetes 安裝流程

### Decision: kubeadm + containerd + Flannel

**Rationale**:
- kubeadm 是官方工具，標準化流程
- containerd 是標準 CRI，無需額外元件
- Flannel 簡單穩定，跨環境相容

**Alternatives Considered**:
| 方案 | 排除原因 |
|------|----------|
| k3s | 輕量但非標準 K8S |
| Docker + cri-dockerd | 額外依賴，官方不再推薦 |
| Calico | 功能豐富但設定複雜 |

### 安裝順序

#### Step 1: 前置作業（所有節點）

```bash
# 停用 swap
swapoff -a
sed -i '/swap/d' /etc/fstab

# 載入核心模組
cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
modprobe overlay
modprobe br_netfilter

# 設定 sysctl
cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sysctl --system
```

#### Step 2: 安裝套件（所有節點）

```bash
# 安裝 containerd
apt-get update
apt-get install -y containerd

# 設定 containerd
mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
systemctl restart containerd

# 安裝 kubeadm, kubelet, kubectl
apt-get install -y apt-transport-https ca-certificates curl
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list
apt-get update
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl
```

#### Step 3: 初始化 Control Plane

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16

# 設定 kubectl
mkdir -p $HOME/.kube
cp /etc/kubernetes/admin.conf $HOME/.kube/config
```

#### Step 4: 安裝 CNI (Flannel)

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

#### Step 5: Worker 加入叢集

```bash
kubeadm join <control-plane-ip>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```

---

## 3. CLI 互動設計

### Decision: Click 套件

**Rationale**:
- 內建 prompt 功能，支援隱藏密碼輸入
- 裝飾器語法簡潔
- 型別驗證內建

**Alternatives Considered**:
| 方案 | 排除原因 |
|------|----------|
| argparse | 無內建 prompt 功能 |
| questionary | 額外依賴，功能相似 |
| Typer | 基於 Click，額外抽象層不必要 |

### 節點資訊收集流程

```python
import click

def collect_node_info(node_name: str, default_port: int = 22) -> dict:
    """收集單一節點連線資訊"""
    click.echo(f"\n📦 設定 {node_name}:")
    return {
        "host": click.prompt("  HostAddr", type=str),
        "port": click.prompt("  HostPort", type=int, default=default_port),
        "user": click.prompt("  HostUser", type=str),
        "password": click.prompt("  HostPass", type=str, hide_input=True),
    }

def collect_cluster_nodes() -> dict:
    """收集 5 個節點資訊"""
    nodes = {}
    
    # Control Plane
    nodes["control_plane"] = collect_node_info("Control Plane (Master)")
    
    # Workers
    worker_count = click.prompt("Worker 節點數量", type=int, default=4)
    nodes["workers"] = []
    for i in range(worker_count):
        nodes["workers"].append(collect_node_info(f"Worker {i+1}"))
    
    return nodes
```

---

## 4. MVP 依賴套件

```text
# requirements.txt
paramiko>=3.0.0
click>=8.0.0
pyyaml>=6.0
```

---

## 5. 決策總結

| 類別 | 選擇 | MVP 複雜度 |
|------|------|-----------|
| SSH | Paramiko SSHClient | 低 |
| K8S 安裝 | kubeadm | 中 |
| Container Runtime | containerd | 低 |
| CNI | Flannel | 低 |
| CLI | Click | 低 |
| 設定格式 | YAML | 低 |
