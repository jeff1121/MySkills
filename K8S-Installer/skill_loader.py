"""
Skill 載入器

掃描並載入專案中的所有 Skill 定義。
"""
from pathlib import Path
from typing import Optional

import yaml

from models import SkillDefinition, SkillParameter


class SkillLoadError(Exception):
    """Skill 載入錯誤"""
    pass


def load_skill_definition(skill_path: Path) -> SkillDefinition:
    """
    載入單一 Skill 定義
    
    Args:
        skill_path: skill.yaml 檔案路徑
        
    Returns:
        SkillDefinition 物件
        
    Raises:
        SkillLoadError: 載入失敗時
    """
    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise SkillLoadError(f"空的 skill 定義：{skill_path}")
        
        # 解析參數
        parameters = []
        for param_data in data.get("parameters", []):
            param = SkillParameter(
                name=param_data["name"],
                type=param_data.get("type", "string"),
                description=param_data.get("description", ""),
                required=param_data.get("required", False),
                default=param_data.get("default"),
            )
            parameters.append(param)
        
        return SkillDefinition(
            name=data["name"],
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            parameters=parameters,
            entrypoint=data.get("entrypoint", "main.py"),
        )
    except yaml.YAMLError as e:
        raise SkillLoadError(f"YAML 解析錯誤：{e}")
    except KeyError as e:
        raise SkillLoadError(f"缺少必要欄位：{e}")
    except FileNotFoundError:
        raise SkillLoadError(f"找不到檔案：{skill_path}")


def discover_skills(base_path: Optional[Path] = None) -> list[SkillDefinition]:
    """
    掃描並發現所有 Skills
    
    Args:
        base_path: 基底路徑，預設為當前目錄的上層
        
    Returns:
        SkillDefinition 列表
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent
    
    skills = []
    
    # 掃描所有子目錄尋找 skill.yaml
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            skill_file = item / "skill.yaml"
            if skill_file.exists():
                try:
                    skill = load_skill_definition(skill_file)
                    skills.append(skill)
                except SkillLoadError:
                    # 忽略載入失敗的 skill，繼續處理其他
                    pass
    
    return skills


def get_skill_by_name(
    name: str,
    base_path: Optional[Path] = None,
) -> Optional[SkillDefinition]:
    """
    根據名稱取得 Skill
    
    Args:
        name: Skill 名稱
        base_path: 基底路徑
        
    Returns:
        SkillDefinition 或 None
    """
    skills = discover_skills(base_path)
    for skill in skills:
        if skill.name == name:
            return skill
    return None


def format_skill_list(skills: list[SkillDefinition]) -> str:
    """
    格式化 Skill 列表為表格
    
    Args:
        skills: SkillDefinition 列表
        
    Returns:
        格式化的字串
    """
    if not skills:
        return "目前沒有可用的 Skills"
    
    lines = ["可用的 Skills：", ""]
    
    # 計算欄寬
    name_width = max(len(s.name) for s in skills)
    name_width = max(name_width, 4)  # 至少 4 字元
    
    # 表頭
    lines.append(f"  {'名稱':<{name_width}}  {'版本':<8}  說明")
    lines.append(f"  {'-' * name_width}  {'-' * 8}  {'-' * 30}")
    
    # 內容
    for skill in skills:
        desc = skill.description[:30] + "..." if len(skill.description) > 30 else skill.description
        lines.append(f"  {skill.name:<{name_width}}  {skill.version:<8}  {desc}")
    
    return "\n".join(lines)


def format_skill_info(skill: SkillDefinition) -> str:
    """
    格式化單一 Skill 的詳細資訊
    
    Args:
        skill: SkillDefinition
        
    Returns:
        格式化的字串
    """
    lines = [
        f"📦 {skill.name} v{skill.version}",
        "",
        f"  說明：{skill.description}",
        f"  作者：{skill.author}",
        f"  進入點：{skill.entrypoint}",
    ]
    
    if skill.parameters:
        lines.append("")
        lines.append("  參數：")
        for param in skill.parameters:
            required = "必填" if param.required else "選填"
            default = f"，預設：{param.default}" if param.default else ""
            lines.append(f"    - {param.name} ({param.type}，{required}{default})")
            if param.description:
                lines.append(f"      {param.description}")
    
    return "\n".join(lines)
