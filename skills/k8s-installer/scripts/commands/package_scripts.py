"""
K8S 套件安裝腳本

包含 containerd、kubeadm、kubelet、kubectl 的安裝。
"""


def get_install_containerd_script() -> str:
    """取得安裝 containerd 的腳本"""
    return """
# 安裝 containerd
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq containerd

# 設定 containerd
mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml > /dev/null
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# 重啟 containerd
systemctl restart containerd
systemctl enable containerd

echo "Containerd installed and configured"
""".strip()


def get_install_kubernetes_packages_script() -> str:
    """取得安裝 Kubernetes 套件的腳本"""
    return """
# 安裝必要的套件
export DEBIAN_FRONTEND=noninteractive
apt-get install -y -qq apt-transport-https ca-certificates curl gpg

# 新增 Kubernetes APT repository
mkdir -p /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg 2>/dev/null

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list > /dev/null

# 安裝 kubelet, kubeadm, kubectl
apt-get update -qq
apt-get install -y -qq kubelet kubeadm kubectl

# 固定版本，避免自動更新
apt-mark hold kubelet kubeadm kubectl

echo "Kubernetes packages installed"
""".strip()


def get_full_package_install_script() -> str:
    """取得完整的套件安裝腳本"""
    scripts = [
        "#!/bin/bash",
        "set -e",
        "",
        "echo '=== K8S Packages Installation ==='",
        "",
        "# Step 1: Install containerd",
        get_install_containerd_script(),
        "",
        "# Step 2: Install Kubernetes packages",
        get_install_kubernetes_packages_script(),
        "",
        "echo '=== Packages installation completed ==='",
    ]
    return "\n".join(scripts)


# 預定義的步驟列表
PACKAGE_STEPS = [
    ("install_containerd", "安裝 Containerd", get_install_containerd_script),
    ("install_k8s_packages", "安裝 K8S 套件", get_install_kubernetes_packages_script),
]
