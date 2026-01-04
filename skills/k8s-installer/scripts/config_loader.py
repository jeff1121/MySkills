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
    
    # 解析 Control Plane
    if "control_plane" not in data:
        raise ConfigValidationError("缺少必要欄位：control_plane")
    
    control_plane = parse_node_connection(data["control_plane"], "control_plane")
    
    # 解析 Workers
    workers = []
    if "workers" in data:
        if not isinstance(data["workers"], list):
            raise ConfigValidationError("workers 必須是陣列")
        for i, worker_data in enumerate(data["workers"]):
            workers.append(parse_node_connection(worker_data, f"workers[{i}]"))
    
    # 解析 Pod Network CIDR
    pod_network_cidr = data.get("pod_network_cidr", "10.244.0.0/16")
    
    config = ClusterConfig(
        control_plane=control_plane,
        workers=workers,
        pod_network_cidr=pod_network_cidr,
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
        "control_plane": {
            "host": config.control_plane.host,
            "port": config.control_plane.port,
            "user": config.control_plane.user,
            "password": config.control_plane.password,
        },
        "workers": [
            {
                "host": w.host,
                "port": w.port,
                "user": w.user,
                "password": w.password,
            }
            for w in config.workers
        ],
        "pod_network_cidr": config.pod_network_cidr,
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
