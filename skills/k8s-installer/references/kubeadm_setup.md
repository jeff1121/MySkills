# kubeadm 安裝指南

本文件整理 kubeadm 官方安裝流程，供 AI Agent 執行時參考。

## 官方文件

- [Installing kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)

## 系統需求

| 項目 | 最低需求 |
|------|----------|
| CPU | 2 cores |
| RAM | 2 GB |
| 磁碟 | 10 GB |
| 網路 | 節點間互通 |

## 必要 Port

### Control Plane
| Port | 用途 |
|------|------|
| 6443 | Kubernetes API server |
| 2379-2380 | etcd server client API |
| 10250 | Kubelet API |
| 10259 | kube-scheduler |
| 10257 | kube-controller-manager |

### Worker
| Port | 用途 |
|------|------|
| 10250 | Kubelet API |
| 30000-32767 | NodePort Services |

## Container Runtime

Kubernetes 1.24+ 不再內建 Docker shim，建議使用：
- **containerd**（推薦）
- CRI-O

### containerd 設定重點

必須啟用 SystemdCgroup：
```toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  SystemdCgroup = true
```

## CNI 網路外掛選項

| 外掛 | 特點 |
|------|------|
| Calico | 功能完整，支援 Network Policy（**預設使用**） |
| Flannel | 簡單易用，適合入門 |
| Cilium | eBPF 為基礎，效能佳 |

本 Skill 預設使用 **Calico**（功能完整、支援 Network Policy）。

### Calico 安裝

```bash
# 安裝 Calico operator
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml

# 安裝 Calico 自訂資源
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/custom-resources.yaml
```

預設 Pod CIDR：`192.168.0.0/16`

## LoadBalancer（MetalLB）

在 Bare Metal 環境中，MetalLB 提供 LoadBalancer 類型 Service 的支援：

```bash
# 安裝 MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.3/config/manifests/metallb-native.yaml

# 設定 IP 位址池
cat <<EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.200-192.168.1.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
EOF
```

## kubeadm init 選項

常用參數：
```bash
kubeadm init \
  --pod-network-cidr=192.168.0.0/16 \  # Calico 預設
  --apiserver-advertise-address=<ip> \ # 多網卡時指定
  --control-plane-endpoint=<lb-ip>     # HA 架構時指定
```

## kubeadm join 選項

```bash
kubeadm join <control-plane-ip>:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

Token 預設有效期 24 小時，可用以下命令重新產生：
```bash
kubeadm token create --print-join-command
```

## 版本相容性

| Kubernetes | 支援的 OS |
|------------|-----------|
| 1.29 | Ubuntu 22.04, RHEL 8/9, Oracle Linux 8/9 |
| 1.28 | Ubuntu 20.04/22.04, RHEL 7/8/9 |

## 參考連結

- [kubeadm reference](https://kubernetes.io/docs/reference/setup-tools/kubeadm/)
- [Troubleshooting kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/)
