#!/usr/bin/env python3
"""
Skill Installer - AI Agent Skills 執行框架

統一入口，可執行任意 Skill。
用法：skill-installer <skill-name>
"""
import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional

import click
import yaml


class SkillRunner:
    """Skill 執行器"""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path(__file__).parent

    def list_skills(self) -> list[dict]:
        """列出所有可用的 Skills"""
        skills = []
        for item in self.base_path.iterdir():
            if item.is_dir() and not item.name.startswith((".", "_")):
                skill_file = item / "skill.yaml"
                if skill_file.exists():
                    try:
                        with open(skill_file, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                        skills.append({
                            "name": data.get("name", item.name),
                            "description": data.get("description", ""),
                            "version": data.get("version", "0.1.0"),
                            "path": str(item),
                        })
                    except Exception:
                        pass
        return skills

    def load_skill(self, skill_name: str) -> Optional[dict]:
        """載入指定 Skill 的定義"""
        skill_dir = self.base_path / skill_name
        skill_file = skill_dir / "skill.yaml"
        
        if not skill_file.exists():
            return None
        
        with open(skill_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        data["_path"] = skill_dir
        return data

    def collect_parameters(self, skill_def: dict) -> dict:
        """根據 skill.yaml 定義收集參數"""
        params = {}
        parameters = skill_def.get("parameters", [])
        node_schema = skill_def.get("node_schema", [])
        
        click.echo(f"\n📦 {skill_def['name']} - {skill_def.get('description', '')}\n")
        
        for param in parameters:
            name = param["name"]
            param_type = param.get("type", "string")
            required = param.get("required", False)
            default = param.get("default")
            description = param.get("description", "")
            
            if param_type == "node":
                # 單一節點
                click.echo(f"=== {description} ===")
                params[name] = self._collect_node(node_schema)
            elif param_type == "node[]":
                # 節點陣列
                click.echo(f"=== {description} ===")
                params[name] = self._collect_node_list(node_schema)
            else:
                # 一般參數
                value = click.prompt(
                    f"  {description}",
                    default=default,
                    show_default=True if default else False,
                )
                params[name] = value
        
        return params

    def _collect_node(self, schema: list) -> dict:
        """收集單一節點資訊"""
        node = {}
        for field in schema:
            name = field["name"]
            field_type = field.get("type", "string")
            required = field.get("required", False)
            default = field.get("default")
            description = field.get("description", name)
            sensitive = field.get("sensitive", False)
            
            if sensitive:
                value = click.prompt(f"  {description}", hide_input=True)
            elif default is not None:
                value = click.prompt(f"  {description}", default=default, show_default=True)
            else:
                value = click.prompt(f"  {description}")
            
            # 型別轉換
            if field_type == "int":
                value = int(value)
            
            node[name] = value
        
        return node

    def _collect_node_list(self, schema: list) -> list:
        """收集多個節點資訊"""
        count = click.prompt("  節點數量", type=int, default=1)
        nodes = []
        
        for i in range(count):
            click.echo(f"\n--- 節點 {i + 1} ---")
            nodes.append(self._collect_node(schema))
        
        return nodes

    def run_skill(self, skill_name: str, params: dict) -> None:
        """執行 Skill"""
        skill_def = self.load_skill(skill_name)
        if not skill_def:
            raise click.ClickException(f"找不到 Skill：{skill_name}")
        
        skill_path = skill_def["_path"]
        entrypoint = skill_def.get("entrypoint", "main.py")
        entrypoint_path = skill_path / entrypoint
        
        if not entrypoint_path.exists():
            raise click.ClickException(f"找不到進入點：{entrypoint_path}")
        
        # 動態載入並執行
        sys.path.insert(0, str(skill_path))
        
        spec = importlib.util.spec_from_file_location("skill_main", entrypoint_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 呼叫 run 函式（如果存在）
        if hasattr(module, "run"):
            module.run(params)
        else:
            click.echo("⚠️  Skill 沒有定義 run() 函式")


@click.group()
@click.version_option(version="0.1.0", prog_name="skill-installer")
def cli():
    """Skill Installer - AI Agent Skills 執行框架"""
    pass


@cli.command("list")
def list_skills():
    """列出所有可用的 Skills"""
    runner = SkillRunner()
    skills = runner.list_skills()
    
    if not skills:
        click.echo("目前沒有可用的 Skills")
        return
    
    click.echo("\n可用的 Skills：\n")
    for skill in skills:
        click.echo(f"  📦 {skill['name']} (v{skill['version']})")
        click.echo(f"     {skill['description']}\n")


@cli.command("run")
@click.argument("skill_name")
@click.option("-y", "--yes", is_flag=True, help="跳過確認提示")
def run_skill(skill_name: str, yes: bool):
    """執行指定的 Skill"""
    runner = SkillRunner()
    
    # 載入 Skill 定義
    skill_def = runner.load_skill(skill_name)
    if not skill_def:
        raise click.ClickException(f"找不到 Skill：{skill_name}")
    
    # 收集參數
    params = runner.collect_parameters(skill_def)
    
    # 確認執行
    if not yes:
        click.echo("\n" + "=" * 50)
        click.echo("即將執行安裝，參數如下：")
        _print_params(params)
        if not click.confirm("\n確認開始執行？"):
            click.echo("已取消")
            return
    
    # 執行
    click.echo("\n🚀 開始執行...\n")
    runner.run_skill(skill_name, params)


@cli.command("info")
@click.argument("skill_name")
def skill_info(skill_name: str):
    """查看 Skill 詳細資訊"""
    runner = SkillRunner()
    skill_def = runner.load_skill(skill_name)
    
    if not skill_def:
        raise click.ClickException(f"找不到 Skill：{skill_name}")
    
    click.echo(f"\n📦 {skill_def['name']} v{skill_def.get('version', '0.1.0')}")
    click.echo(f"\n  {skill_def.get('description', '')}")
    click.echo(f"\n  進入點：{skill_def.get('entrypoint', 'main.py')}")
    
    params = skill_def.get("parameters", [])
    if params:
        click.echo("\n  參數：")
        for p in params:
            req = "必填" if p.get("required") else "選填"
            default = f"，預設：{p['default']}" if p.get("default") else ""
            click.echo(f"    - {p['name']} ({p.get('type', 'string')}，{req}{default})")
            if p.get("description"):
                click.echo(f"      {p['description']}")


def _print_params(params: dict, indent: int = 2):
    """格式化列印參數"""
    prefix = " " * indent
    for key, value in params.items():
        if isinstance(value, dict):
            click.echo(f"{prefix}{key}:")
            _print_params(value, indent + 2)
        elif isinstance(value, list):
            click.echo(f"{prefix}{key}:")
            for i, item in enumerate(value):
                click.echo(f"{prefix}  [{i + 1}]")
                if isinstance(item, dict):
                    _print_params(item, indent + 4)
                else:
                    click.echo(f"{prefix}    {item}")
        elif key == "password":
            click.echo(f"{prefix}{key}: ********")
        else:
            click.echo(f"{prefix}{key}: {value}")


if __name__ == "__main__":
    cli()
