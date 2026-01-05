"""
K8S 叢集設定腳本

包含 kubeadm init、安裝 Calico CNI、kubeadm join、MetalLB 等步驟。
"""


def get_kubeadm_init_script(
    pod_network_cidr: str,
    control_plane_endpoint: str,
) -> str:
    """
    取得初始化 Control Plane 的腳本
    
    Args:
        pod_network_cidr: Pod 網路 CIDR
        control_plane_endpoint: Control Plane Endpoint
    """
    return f"""
# 初始化 Kubernetes Control Plane
kubeadm init \\
  --control-plane-endpoint "{control_plane_endpoint}" \\
  --upload-certs \\
  --pod-network-cidr={pod_network_cidr}

# 設定 kubectl 存取
mkdir -p $HOME/.kube
cp -f /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

echo "Control Plane initialized"
""".strip()


def get_install_calico_script(pod_network_cidr: str) -> str:
    """取得安裝 Calico CNI 的腳本"""
    return f"""
# 安裝 Calico operator
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml

# 安裝 Calico 自訂資源
curl -fsSL https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/custom-resources.yaml | \\
  sed "s#192.168.0.0/16#{pod_network_cidr}#g" | \\
  kubectl apply -f -

# 等待 Calico 就緒
kubectl wait --for=condition=Ready pods -l k8s-app=calico-node -n calico-system --timeout=300s

echo "Calico CNI installed"
""".strip()


def get_generate_join_command_script() -> str:
    """取得產生 join 命令與 certificate key 的腳本"""
    return """
# 產生 Control Plane certificate key 與 join 命令
CERT_KEY=$(kubeadm init phase upload-certs --upload-certs | tail -n 1)
JOIN_CMD=$(kubeadm token create --print-join-command)

echo "CERT_KEY=${CERT_KEY}"
echo "JOIN_CMD=${JOIN_CMD}"
""".strip()


def get_master_join_script(join_command: str, certificate_key: str) -> str:
    """
    取得 Master 加入叢集的腳本
    
    Args:
        join_command: kubeadm join 基礎命令
        certificate_key: Control Plane certificate key
    """
    return f"""
# 加入 Kubernetes Control Plane
{join_command} --control-plane --certificate-key {certificate_key}

mkdir -p $HOME/.kube
cp -f /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

echo "Master joined the cluster"
""".strip()


def get_worker_join_script(join_command: str) -> str:
    """
    取得 Worker 加入叢集的腳本
    
    Args:
        join_command: kubeadm join 命令
    """
    return f"""
# 加入 Kubernetes 叢集
{join_command}

echo "Worker joined the cluster"
""".strip()


def get_install_metallb_script(metallb_ip_range: str) -> str:
    """取得安裝 MetalLB 的腳本"""
    return f"""
# 啟用 strictARP
kubectl get configmap kube-proxy -n kube-system -o yaml | \\
  sed -e 's/strictARP: false/strictARP: true/' | \\
  kubectl apply -f - -n kube-system

# 安裝 MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.3/config/manifests/metallb-native.yaml
kubectl wait --for=condition=Ready pods -l app=metallb -n metallb-system --timeout=120s

# 設定 IP Address Pool
cat <<EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - {metallb_ip_range}
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
spec:
  ipAddressPools:
  - default-pool
EOF

echo "MetalLB installed"
""".strip()


def get_check_cluster_status_script() -> str:
    """取得檢查叢集狀態的腳本"""
    return """
# 檢查叢集狀態
kubectl get nodes -o wide
kubectl get pods -A
""".strip()


# 預定義的步驟列表
CLUSTER_STEPS = [
    ("kubeadm_init", "初始化 Control Plane", get_kubeadm_init_script),
    ("install_calico", "安裝 Calico CNI", get_install_calico_script),
    ("install_metallb", "安裝 MetalLB", get_install_metallb_script),
]
