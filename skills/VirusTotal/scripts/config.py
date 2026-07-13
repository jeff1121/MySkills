"""
VirusTotal Skill 設定與環境變數載入。

集中管理 API base URL、輪詢與大檔門檻等常數，並負責從 `.env`（透過 python-dotenv）
讀取 `VT_API_KEY`。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

__version__ = "0.1.0"

# VirusTotal API v3 基底位址
API_BASE_URL = "https://www.virustotal.com/api/v3"

# 分析輪詢預設值（秒）
POLL_INTERVAL = 15
POLL_TIMEOUT = 300

# 檔案上傳門檻：≥ 32MB 需先向 VT 取得專用上傳網址
LARGE_FILE_THRESHOLD = 32 * 1024 * 1024

# 環境變數名稱
API_KEY_ENV = "VT_API_KEY"


class ConfigError(Exception):
    """設定相關錯誤（例如缺少 API 金鑰）。"""


def load_env(env_path: str | None = None) -> None:
    """載入環境變數。

    優先順序：
    1. 明確指定的 `env_path`。
    2. skill 根目錄下的 `.env`（skills/VirusTotal/.env）。
    3. python-dotenv 預設搜尋（目前工作目錄向上尋找）。
    """
    if env_path:
        load_dotenv(env_path, override=False)
        return

    skill_env = Path(__file__).resolve().parent.parent / ".env"
    if skill_env.exists():
        load_dotenv(skill_env, override=False)
    else:
        load_dotenv(override=False)


def get_api_key(env_path: str | None = None) -> str:
    """取得 VirusTotal API 金鑰，缺少時丟出 `ConfigError`。"""
    load_env(env_path)
    key = os.getenv(API_KEY_ENV, "").strip()
    if not key:
        raise ConfigError(
            "找不到 VirusTotal API 金鑰。請於 skills/VirusTotal/.env 設定 "
            f"{API_KEY_ENV}=<your_api_key>，或匯出同名環境變數。可參考 .env.example。"
        )
    return key
