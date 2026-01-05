"""
使用者互動提示

使用 Click 實作互動式收集節點連線資訊。
"""
import click

from models import NodeConnection, ClusterConfig


def collect_node_info(node_name: str, default_port: int = 22) -> NodeConnection:
    """
    收集單一節點連線資訊
    
    Args:
        node_name: 節點名稱（顯示用）
        default_port: 預設 SSH 連接埠
        
    Returns:
        NodeConnection 物件
    """
    click.echo(f"\n📦 設定 {node_name}:")
    
    host = click.prompt("  HostAddr", type=str)
    port = click.prompt("  HostPort", type=int, default=default_port)
    user = click.prompt("  HostUser", type=str)
    password = click.prompt("  HostPass", type=str, hide_input=True)
    
    return NodeConnection(
        host=host.strip(),
        port=port,
        user=user.strip(),
        password=password,
    )


def collect_cluster_nodes(
    default_master_count: int = 3,
    default_worker_count: int = 2,
) -> ClusterConfig:
    """
    收集完整叢集節點資訊
    
    Args:
        default_worker_count: 預設 Worker 節點數量
        
    Returns:
        ClusterConfig 物件
    """
    click.echo("\n" + "=" * 50)
    click.echo("📦 K8S-Installer - Kubernetes 叢集安裝工具")
    click.echo("=" * 50)
    
    # Masters
    click.echo("\n=== Master 節點設定 ===")
    master_count = click.prompt(
        "Master 節點數量",
        type=int,
        default=default_master_count,
    )
    masters = []
    for i in range(master_count):
        click.echo(f"\n--- Master {i + 1} ---")
        masters.append(collect_node_info(f"Master {i + 1}"))

    # Workers
    click.echo("\n=== Worker 節點設定 ===")
    worker_count = click.prompt(
        "Worker 節點數量",
        type=int,
        default=default_worker_count,
    )
    workers = []
    for i in range(worker_count):
        click.echo(f"\n--- Worker {i + 1} ---")
        workers.append(collect_node_info(f"Worker {i + 1}"))

    # Load Balancer
    click.echo("\n=== Load Balancer（選填但建議）===")
    load_balancer_ip = click.prompt(
        "Load Balancer IP（指向 3 個 Master 的 6443 port）",
        type=str,
        default="",
        show_default=False,
    ).strip() or None

    # Pod Network CIDR
    click.echo("\n=== 網路設定 ===")
    pod_network_cidr = click.prompt(
        "Pod Network CIDR",
        type=str,
        default="192.168.0.0/16",
    )

    # MetalLB
    click.echo("\n=== MetalLB 設定（選填）===")
    metallb_ip_range = click.prompt(
        "MetalLB IP 位址範圍（例如 192.168.1.200-192.168.1.250）",
        type=str,
        default="",
        show_default=False,
    ).strip() or None

    return ClusterConfig(
        master_nodes=masters,
        worker_nodes=workers,
        load_balancer_ip=load_balancer_ip,
        pod_network_cidr=pod_network_cidr,
        metallb_ip_range=metallb_ip_range,
    )


def confirm_cluster_config(config: ClusterConfig) -> bool:
    """
    顯示叢集配置摘要並確認
    
    Args:
        config: ClusterConfig 物件
        
    Returns:
        使用者是否確認
    """
    click.echo("\n" + "=" * 50)
    click.echo("📋 叢集配置摘要")
    click.echo("=" * 50)
    
    click.echo(f"\n🧩 Masters ({len(config.master_nodes)} 個):")
    for i, master in enumerate(config.master_nodes):
        click.echo(f"   {i + 1}. {master}")

    click.echo(f"\n👷 Workers ({len(config.worker_nodes)} 個):")
    for i, worker in enumerate(config.worker_nodes):
        click.echo(f"   {i + 1}. {worker}")

    click.echo(f"\n🌐 Control Plane Endpoint: {config.control_plane_endpoint()}")
    click.echo(f"🌐 Pod Network CIDR: {config.pod_network_cidr}")
    if config.metallb_ip_range:
        click.echo(f"🧱 MetalLB IP Range: {config.metallb_ip_range}")
    
    click.echo("\n" + "-" * 50)
    return click.confirm("確認開始安裝？", default=False)


def show_progress(step_name: str, node: str, status: str = "running") -> None:
    """
    顯示安裝進度
    
    Args:
        step_name: 步驟名稱
        node: 執行節點
        status: 狀態（running, success, failed）
    """
    icons = {
        "running": "⏳",
        "success": "✅",
        "failed": "❌",
    }
    icon = icons.get(status, "⏳")
    click.echo(f"{icon} [{node}] {step_name}")


def show_error(message: str, suggestion: str = "") -> None:
    """
    顯示錯誤訊息
    
    Args:
        message: 錯誤訊息
        suggestion: 建議動作
    """
    click.echo(f"\n❌ 錯誤：{message}", err=True)
    if suggestion:
        click.echo(f"💡 建議：{suggestion}", err=True)


def show_success(message: str) -> None:
    """顯示成功訊息"""
    click.echo(f"\n✅ {message}")
