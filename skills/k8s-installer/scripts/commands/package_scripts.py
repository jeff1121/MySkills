"""
K8S 套件安裝腳本

包含 containerd、kubeadm、kubelet、kubectl 的安裝。
"""


def get_install_containerd_script() -> str:
    """取得安裝 containerd 的腳本"""
    return """
# 安裝 containerd
dnf install -y dnf-plugins-core
dnf config-manager --enable ol9_addons || true
dnf install -y containerd

# 設定 containerd
mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml > /dev/null
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# 啟動 containerd
systemctl enable --now containerd

echo "Containerd installed and configured"
""".strip()


def get_install_kubernetes_packages_script() -> str:
    """取得安裝 Kubernetes 套件的腳本"""
    return """
# 新增 Kubernetes YUM repository
cat <<EOF | tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.29/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.29/rpm/repodata/repomd.xml.key
EOF

# 安裝 kubelet, kubeadm, kubectl
dnf install -y kubelet kubeadm kubectl
systemctl enable --now kubelet

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
