#!/usr/bin/env python3
"""
K8S-Installer CLI

自動化安裝 Kubernetes 叢集的命令列工具。
"""
import json
import sys
from pathlib import Path
from typing import Optional

import click

from config_loader import load_cluster_config, ConfigLoadError, ConfigValidationError
from installer import run_installation
from prompts import (
    collect_cluster_nodes,
    confirm_cluster_config,
    show_error,
    show_success,
)
from models import ClusterConfig


@click.group()
@click.version_option(version="0.1.0", prog_name="k8s-installer")
def cli() -> None:
    """K8S-Installer - 自動化安裝 Kubernetes 叢集"""
    pass


@cli.command()
@click.option(
    "-c", "--config",
    type=click.Path(exists=True, path_type=Path),
    help="叢集配置檔路徑（YAML 格式）",
)
@click.option(
    "--json-output",
    is_flag=True,
    default=False,
    help="以 JSON 格式輸出結果",
)
@click.option(
    "-y", "--yes",
    is_flag=True,
    default=False,
    help="跳過確認提示",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    default=False,
    help="顯示詳細輸出",
)
def install(
    config: Optional[Path],
    json_output: bool,
    yes: bool,
    verbose: bool,
) -> None:
    """安裝 Kubernetes 叢集"""
    try:
        cluster_config = _get_cluster_config(config)
        
        if not yes and not json_output:
            if not confirm_cluster_config(cluster_config):
                click.echo("已取消安裝")
                sys.exit(0)
        
        result = run_installation(cluster_config, verbose)
        _output_result(result, json_output)
        sys.exit(0 if result.success else 1)
        
    except ConfigLoadError as e:
        _handle_error("配置載入失敗", str(e), json_output)
        sys.exit(1)
    except ConfigValidationError as e:
        _handle_error("配置驗證失敗", str(e), json_output)
        sys.exit(1)
    except KeyboardInterrupt:
        _handle_interrupt(json_output)
        sys.exit(130)
    except Exception as e:
        _handle_error("未預期的錯誤", str(e), json_output)
        sys.exit(1)


def _get_cluster_config(config_path: Optional[Path]) -> ClusterConfig:
    """取得叢集配置"""
    if config_path:
        return load_cluster_config(config_path)
    return collect_cluster_nodes()


def _output_result(result, json_output: bool) -> None:
    """輸出執行結果"""
    if json_output:
        output = {"success": result.success, "message": result.message}
        if result.join_command:
            output["join_command"] = result.join_command
        if result.error:
            output["error"] = result.error
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if result.success:
            show_success(result.message)
            if result.join_command:
                click.echo(f"\n📋 Join 命令：\n{result.join_command}")
        else:
            show_error(result.message, result.error)


def _handle_interrupt(json_output: bool) -> None:
    """處理使用者中斷"""
    if json_output:
        click.echo(json.dumps({"success": False, "error": "使用者中斷"}))
    else:
        click.echo("\n已中斷")


def _handle_error(message: str, error: Optional[str], json_output: bool) -> None:
    """處理錯誤輸出"""
    if json_output:
        output = {"success": False, "message": message}
        if error:
            output["error"] = error
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        show_error(message, error)


@cli.command("list")
@click.option(
    "--json-output",
    is_flag=True,
    default=False,
    help="以 JSON 格式輸出",
)
def list_skills(json_output: bool) -> None:
    """列出所有可用的 Skills"""
    from skill_loader import discover_skills, format_skill_list
    
    skills = discover_skills()
    
    if json_output:
        output = {
            "skills": [
                {
                    "name": s.name,
                    "version": s.version,
                    "description": s.description,
                }
                for s in skills
            ]
        }
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        click.echo(format_skill_list(skills))


@cli.command()
@click.argument("skill_name")
@click.option(
    "--json-output",
    is_flag=True,
    default=False,
    help="以 JSON 格式輸出",
)
def info(skill_name: str, json_output: bool) -> None:
    """顯示指定 Skill 的詳細資訊"""
    from skill_loader import get_skill_by_name, format_skill_info
    
    skill = get_skill_by_name(skill_name)
    
    if skill is None:
        if json_output:
            click.echo(json.dumps({
                "success": False,
                "error": f"找不到 Skill：{skill_name}",
            }, ensure_ascii=False, indent=2))
        else:
            show_error(f"找不到 Skill：{skill_name}")
        sys.exit(1)
    
    if json_output:
        output = {
            "name": skill.name,
            "version": skill.version,
            "description": skill.description,
            "author": skill.author,
            "entrypoint": skill.entrypoint,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                }
                for p in skill.parameters
            ],
        }
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        click.echo(format_skill_info(skill))


@cli.command()
@click.option(
    "-c", "--config",
    type=click.Path(exists=True, path_type=Path),
    help="叢集配置檔路徑（YAML 格式）",
)
def validate(config: Optional[Path]) -> None:
    """驗證叢集配置檔"""
    if not config:
        show_error("請指定配置檔路徑", "使用 -c 或 --config 選項")
        sys.exit(1)
    
    try:
        cluster_config = load_cluster_config(config)
        show_success(f"配置檔驗證通過：{config}")
        
        click.echo(f"\n叢集配置：")
        click.echo(f"  Masters: {len(cluster_config.master_nodes)} 個節點")
        for i, master in enumerate(cluster_config.master_nodes, 1):
            click.echo(f"    {i}. {master}")
        click.echo(f"  Workers: {len(cluster_config.worker_nodes)} 個節點")
        for i, worker in enumerate(cluster_config.worker_nodes, 1):
            click.echo(f"    {i}. {worker}")
        click.echo(f"  Control Plane Endpoint: {cluster_config.control_plane_endpoint()}")
        click.echo(f"  Pod Network CIDR: {cluster_config.pod_network_cidr}")
        if cluster_config.metallb_ip_range:
            click.echo(f"  MetalLB IP Range: {cluster_config.metallb_ip_range}")
        
    except ConfigLoadError as e:
        show_error("配置載入失敗", str(e))
        sys.exit(1)
    except ConfigValidationError as e:
        show_error("配置驗證失敗", str(e))
        sys.exit(1)


# === Skill Installer 框架介面 ===
# 當被 skill-installer 呼叫時，會執行此函式

def run(params: dict) -> None:
    """
    Skill 執行入口（供 skill-installer 框架呼叫）
    
    Args:
        params: 從對話式介面收集的參數，結構對應 skill.yaml 定義
            - master_nodes: list[dict] (host, port, user, password)
            - worker_nodes: list[dict]
            - load_balancer_ip: str (optional)
            - pod_network_cidr: str (optional)
            - metallb_ip_range: str (optional)
    """
    from models import NodeConnection, ClusterConfig
    from installer import run_installation
    from prompts import show_success, show_error
    import click
    
    # 轉換參數為內部資料結構
    master_data_list = params.get("master_nodes")
    if not master_data_list and "control_plane" in params:
        master_data_list = [params["control_plane"]]
    if not master_data_list:
        raise ValueError("缺少 master_nodes 參數")

    masters = []
    for m_data in master_data_list:
        masters.append(NodeConnection(
            host=m_data["host"],
            port=m_data.get("port", 22),
            user=m_data["user"],
            password=m_data.get("password"),
        ))

    workers = []
    for w_data in params.get("worker_nodes", params.get("workers", [])):
        workers.append(NodeConnection(
            host=w_data["host"],
            port=w_data.get("port", 22),
            user=w_data["user"],
            password=w_data.get("password"),
        ))
    
    cluster_config = ClusterConfig(
        master_nodes=masters,
        worker_nodes=workers,
        load_balancer_ip=params.get("load_balancer_ip"),
        pod_network_cidr=params.get("pod_network_cidr", "192.168.0.0/16"),
        metallb_ip_range=params.get("metallb_ip_range"),
    )
    
    # 執行安裝
    result = run_installation(cluster_config, verbose=True)
    
    # 輸出結果
    if result.success:
        show_success(result.message)
        if result.join_command:
            click.echo(f"\n📋 Join 命令：\n{result.join_command}")
    else:
        show_error(result.message, result.error)


if __name__ == "__main__":
    cli()
