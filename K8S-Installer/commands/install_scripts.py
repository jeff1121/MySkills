"""
K8S 安裝前置作業腳本

包含停用 swap、載入核心模組、設定 sysctl 等步驟。
"""


def get_disable_swap_script() -> str:
    """取得停用 swap 的腳本"""
    return """
# 停用 swap
swapoff -a
sed -i '/swap/d' /etc/fstab
echo "Swap disabled"
""".strip()


def get_load_kernel_modules_script() -> str:
    """取得載入核心模組的腳本"""
    return """
# 載入核心模組
cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

modprobe overlay
modprobe br_netfilter
echo "Kernel modules loaded"
""".strip()


def get_configure_sysctl_script() -> str:
    """取得設定 sysctl 的腳本"""
    return """
# 設定 sysctl 參數
cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sysctl --system > /dev/null 2>&1
echo "Sysctl configured"
""".strip()


def get_update_system_script() -> str:
    """取得更新系統的腳本"""
    return """
# 更新系統套件
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
echo "System updated"
""".strip()


def get_full_prerequisites_script() -> str:
    """取得完整的前置作業腳本"""
    scripts = [
        "#!/bin/bash",
        "set -e",
        "",
        "echo '=== K8S Prerequisites Setup ==='",
        "",
        "# Step 1: Disable swap",
        get_disable_swap_script(),
        "",
        "# Step 2: Load kernel modules",
        get_load_kernel_modules_script(),
        "",
        "# Step 3: Configure sysctl",
        get_configure_sysctl_script(),
        "",
        "echo '=== Prerequisites setup completed ==='",
    ]
    return "\n".join(scripts)


# 預定義的步驟列表
PREREQUISITE_STEPS = [
    ("disable_swap", "停用 Swap", get_disable_swap_script),
    ("load_modules", "載入核心模組", get_load_kernel_modules_script),
    ("configure_sysctl", "設定 Sysctl", get_configure_sysctl_script),
]
