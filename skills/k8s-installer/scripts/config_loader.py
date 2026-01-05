"""
設定檔載入與驗證

支援從 YAML 檔案載入叢集配置。
"""
from pathlib import Path
from typing import Optional

import yaml

from models import NodeConnection, ClusterConfig


class ConfigLoadError(Exception):
    """設定檔載入錯誤"""
    pass


class ConfigValidationError(Exception):
    """設定檔驗證錯誤"""
    pass


def load_cluster_config(config_path: str) -> ClusterConfig:
    """
    從 YAML 檔案載入叢集配置
    
    Args:
        config_path: 設定檔路徑
        
    Returns:
        ClusterConfig 物件
        
    Raises:
        ConfigLoadError: 檔案讀取或解析失敗
        ConfigValidationError: 設定驗證失敗
    """
    path = Path(config_path)
    
    if not path.exists():
        raise ConfigLoadError(f"設定檔不存在：{config_path}")
    
    if not path.is_file():
        raise ConfigLoadError(f"路徑不是檔案：{config_path}")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigLoadError(f"YAML 解析錯誤：{str(e)}") from e
    except IOError as e:
        raise ConfigLoadError(f"檔案讀取錯誤：{str(e)}") from e
    
    return parse_cluster_config(data)


def parse_cluster_config(data: dict) -> ClusterConfig:
    """
    解析叢集配置字典
    
    Args:
        data: 從 YAML 載入的字典
        
    Returns:
        ClusterConfig 物件
        
    Raises:
        ConfigValidationError: 設定驗證失敗
    """
    if not isinstance(data, dict):
        raise ConfigValidationError("設定檔格式錯誤：根元素必須是物件")
    
    # 解析 Master 節點
    master_nodes = []
    if "master_nodes" in data:
        if not isinstance(data["master_nodes"], list):
            raise ConfigValidationError("master_nodes 必須是陣列")
        for i, master_data in enumerate(data["master_nodes"]):
            master_nodes.append(
                parse_node_connection(master_data, f"master_nodes[{i}]")
            )
    elif "control_plane" in data:
        master_nodes = [parse_node_connection(data["control_plane"], "control_plane")]
    else:
        raise ConfigValidationError("缺少必要欄位：master_nodes")

    # 解析 Workers
    workers = []
    worker_data_list = data.get("worker_nodes", data.get("workers", []))
    if worker_data_list:
        if not isinstance(worker_data_list, list):
            raise ConfigValidationError("worker_nodes 必須是陣列")
        for i, worker_data in enumerate(worker_data_list):
            workers.append(
                parse_node_connection(worker_data, f"worker_nodes[{i}]")
            )

    # 解析其他參數
    load_balancer_ip = data.get("load_balancer_ip")
    pod_network_cidr = data.get("pod_network_cidr", "192.168.0.0/16")
    metallb_ip_range = data.get("metallb_ip_range")

    config = ClusterConfig(
        master_nodes=master_nodes,
        worker_nodes=workers,
        load_balancer_ip=load_balancer_ip,
        pod_network_cidr=pod_network_cidr,
        metallb_ip_range=metallb_ip_range,
    )
    
    # 驗證配置
    errors = config.validate()
    if errors:
        raise ConfigValidationError(
            "設定驗證失敗：\n" + "\n".join(f"  - {e}" for e in errors)
        )
    
    return config


def parse_node_connection(data: dict, field_name: str) -> NodeConnection:
    """
    解析節點連線資訊
    
    Args:
        data: 節點資料字典
        field_name: 欄位名稱（用於錯誤訊息）
        
    Returns:
        NodeConnection 物件
        
    Raises:
        ConfigValidationError: 設定驗證失敗
    """
    if not isinstance(data, dict):
        raise ConfigValidationError(f"{field_name} 必須是物件")
    
    required_fields = ["host", "user", "password"]
    for field in required_fields:
        if field not in data:
            raise ConfigValidationError(f"{field_name} 缺少必要欄位：{field}")
    
    return NodeConnection(
        host=str(data["host"]),
        port=int(data.get("port", 22)),
        user=str(data["user"]),
        password=str(data["password"]),
    )


def save_cluster_config(config: ClusterConfig, config_path: str) -> None:
    """
    將叢集配置儲存為 YAML 檔案
    
    Args:
        config: ClusterConfig 物件
        config_path: 儲存路徑
    """
    data = {
        "master_nodes": [
            {
                "host": m.host,
                "port": m.port,
                "user": m.user,
                "password": m.password,
            }
            for m in config.master_nodes
        ],
        "worker_nodes": [
            {
                "host": w.host,
                "port": w.port,
                "user": w.user,
                "password": w.password,
            }
            for w in config.worker_nodes
        ],
        "load_balancer_ip": config.load_balancer_ip,
        "pod_network_cidr": config.pod_network_cidr,
        "metallb_ip_range": config.metallb_ip_range,
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
