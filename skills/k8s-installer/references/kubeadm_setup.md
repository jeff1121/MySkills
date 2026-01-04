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
| Flannel | 簡單易用，適合入門 |
| Calico | 功能完整，支援 Network Policy |
| Cilium | eBPF 為基礎，效能佳 |

本 Skill 預設使用 Flannel（簡單穩定）。

## kubeadm init 選項

常用參數：
```bash
kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \  # Flannel 預設
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
