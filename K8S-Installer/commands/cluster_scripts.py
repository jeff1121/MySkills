"""
K8S 叢集設定腳本

包含 kubeadm init、安裝 Flannel CNI、kubeadm join 等步驟。
"""


def get_kubeadm_init_script(pod_network_cidr: str = "10.244.0.0/16") -> str:
    """
    取得初始化 Control Plane 的腳本
    
    Args:
        pod_network_cidr: Pod 網路 CIDR
    """
    return f"""
# 初始化 Kubernetes Control Plane
kubeadm init --pod-network-cidr={pod_network_cidr}

# 設定 kubectl 存取
mkdir -p $HOME/.kube
cp -f /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

echo "Control Plane initialized"
""".strip()


def get_install_flannel_script() -> str:
    """取得安裝 Flannel CNI 的腳本"""
    return """
# 安裝 Flannel CNI
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# 等待 Flannel 就緒
echo "Waiting for Flannel to be ready..."
sleep 10

echo "Flannel CNI installed"
""".strip()


def get_generate_join_command_script() -> str:
    """取得產生 join 命令的腳本"""
    return """
# 產生 Worker 加入命令
kubeadm token create --print-join-command
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


def get_check_cluster_status_script() -> str:
    """取得檢查叢集狀態的腳本"""
    return """
# 檢查叢集狀態
kubectl get nodes -o wide
kubectl get pods -A
""".strip()


def get_full_control_plane_setup_script(pod_network_cidr: str = "10.244.0.0/16") -> str:
    """取得完整的 Control Plane 設定腳本"""
    scripts = [
        "#!/bin/bash",
        "set -e",
        "",
        "echo '=== Control Plane Setup ==='",
        "",
        "# Step 1: Initialize Control Plane",
        get_kubeadm_init_script(pod_network_cidr),
        "",
        "# Step 2: Install Flannel CNI",
        get_install_flannel_script(),
        "",
        "echo '=== Control Plane setup completed ==='",
    ]
    return "\n".join(scripts)


# 預定義的步驟列表
CLUSTER_STEPS = [
    ("kubeadm_init", "初始化 Control Plane", get_kubeadm_init_script),
    ("install_flannel", "安裝 Flannel CNI", get_install_flannel_script),
]
