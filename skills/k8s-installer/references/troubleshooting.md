# K8S 安裝常見問題排除

## SSH 相關

### 連線被拒絕 (Connection refused)
```
原因：SSH 服務未啟動或防火牆阻擋
解決：
  systemctl start sshd
  firewall-cmd --add-port=22/tcp --permanent
  firewall-cmd --reload
```

### 認證失敗 (Authentication failed)
```
原因：密碼錯誤或 SSH 設定不允許密碼認證
解決：
  1. 確認密碼正確
  2. 檢查 /etc/ssh/sshd_config：
     PasswordAuthentication yes
  3. 重啟 sshd：systemctl restart sshd
```

### 連線逾時 (Connection timed out)
```
原因：網路不通或防火牆阻擋
解決：
  1. 確認網路連通：ping {host}
  2. 檢查防火牆規則
  3. 確認目標主機 IP 正確
```

## kubeadm init 相關

### [ERROR NumCPU]: the number of available CPUs 1 is less than the required 2
```
原因：CPU 核心數不足
解決：增加 VM 的 CPU 至少 2 cores
```

### [ERROR Mem]: the system RAM (1024 MB) is less than the minimum 1700 MB
```
原因：記憶體不足
解決：增加 VM 記憶體至少 2 GB
```

### [ERROR Swap]: running with swap on is not supported
```
原因：Swap 未停用
解決：
  swapoff -a
  sed -i '/swap/d' /etc/fstab
```

### [ERROR FileContent--proc-sys-net-bridge-bridge-nf-call-iptables]: /proc/sys/net/bridge/bridge-nf-call-iptables does not exist
```
原因：核心模組未載入
解決：
  modprobe br_netfilter
  echo 1 > /proc/sys/net/bridge/bridge-nf-call-iptables
```

### [ERROR Port-6443]: Port 6443 is in use
```
原因：已有 K8S 安裝殘留
解決：
  kubeadm reset -f
  rm -rf /etc/kubernetes/
  rm -rf /var/lib/kubelet/
  rm -rf /var/lib/etcd/
```

### [ERROR CRI]: container runtime is not running
```
原因：containerd 未啟動或設定錯誤
解決：
  systemctl restart containerd
  systemctl status containerd
  # 檢查日誌
  journalctl -xeu containerd
```

## kubeadm join 相關

### error execution phase preflight: couldn't validate the identity of the API Server
```
原因：Token 已過期或 hash 錯誤
解決：在 Control Plane 重新產生 join 命令
  kubeadm token create --print-join-command
```

### Unable to connect to the server: dial tcp {ip}:6443: connect: connection refused
```
原因：無法連線 Control Plane
解決：
  1. 確認 Control Plane 的 6443 port 開放
  2. 檢查防火牆：firewall-cmd --add-port=6443/tcp --permanent
  3. 確認 kube-apiserver 運作中
```

### The kubelet is not running
```
原因：kubelet 服務異常
解決：
  systemctl status kubelet
  journalctl -xeu kubelet
  # 常見原因：containerd 設定錯誤
```

## 網路相關

### Nodes NotReady
```
原因：CNI 網路外掛未安裝或異常
解決：
  1. 確認 Flannel 已安裝
  2. 檢查 Pod 狀態：kubectl get pods -n kube-flannel
  3. 查看日誌：kubectl logs -n kube-flannel -l app=flannel
```

### Pod 無法通訊
```
原因：網路設定問題
解決：
  1. 確認 Pod CIDR 與 Flannel 設定一致
  2. 檢查 iptables 規則
  3. 確認 kube-proxy 運作中
```

## 重置叢集

完整清除 K8S 安裝：

```bash
# 在所有節點執行
kubeadm reset -f
rm -rf /etc/kubernetes/
rm -rf /var/lib/kubelet/
rm -rf /var/lib/etcd/
rm -rf /etc/cni/net.d/
rm -rf $HOME/.kube/

# 清除 iptables 規則
iptables -F && iptables -t nat -F && iptables -t mangle -F && iptables -X
```

## 日誌位置

| 元件 | 日誌命令 |
|------|----------|
| kubelet | `journalctl -xeu kubelet` |
| containerd | `journalctl -xeu containerd` |
| kube-apiserver | `kubectl logs -n kube-system kube-apiserver-<node>` |
| etcd | `kubectl logs -n kube-system etcd-<node>` |
