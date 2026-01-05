"""
commands 模組初始化
"""
from .install_scripts import (
    get_disable_swap_script,
    get_load_kernel_modules_script,
    get_configure_sysctl_script,
    get_full_prerequisites_script,
    PREREQUISITE_STEPS,
)
from .package_scripts import (
    get_install_containerd_script,
    get_install_kubernetes_packages_script,
    get_full_package_install_script,
    PACKAGE_STEPS,
)
from .cluster_scripts import (
    get_kubeadm_init_script,
    get_install_calico_script,
    get_generate_join_command_script,
    get_master_join_script,
    get_worker_join_script,
    get_install_metallb_script,
    get_check_cluster_status_script,
    CLUSTER_STEPS,
)

__all__ = [
    # install_scripts
    "get_disable_swap_script",
    "get_load_kernel_modules_script",
    "get_configure_sysctl_script",
    "get_full_prerequisites_script",
    "PREREQUISITE_STEPS",
    # package_scripts
    "get_install_containerd_script",
    "get_install_kubernetes_packages_script",
    "get_full_package_install_script",
    "PACKAGE_STEPS",
    # cluster_scripts
    "get_kubeadm_init_script",
    "get_install_calico_script",
    "get_generate_join_command_script",
    "get_master_join_script",
    "get_worker_join_script",
    "get_install_metallb_script",
    "get_check_cluster_status_script",
    "CLUSTER_STEPS",
]
