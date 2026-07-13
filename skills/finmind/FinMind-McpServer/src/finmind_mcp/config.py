"""設定管理模組 — 透過環境變數與 .env 檔管理 FinMind API 設定。"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """FinMind MCP Server 設定。

    所有設定皆可透過環境變數或 .env 檔案提供。
    """

    # FinMind API 設定
    FINMIND_TOKEN: str = ""
    FINMIND_API_BASE_URL: str = "https://api.finmindtrade.com/api/v4"
    FINMIND_USER_INFO_URL: str = "https://api.web.finmindtrade.com/v2/user_info"

    # MCP Server 設定
    MCP_SERVER_PORT: int = 8080
    MCP_SERVER_HOST: str = "0.0.0.0"

    # 日誌設定
    LOG_LEVEL: str = "INFO"

    # HTTP 客戶端設定
    HTTP_TIMEOUT: int = 30
    HTTP_MAX_RETRIES: int = 3

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    def validate_token(self) -> bool:
        """檢查 API Token 是否已設定。"""
        return bool(self.FINMIND_TOKEN and self.FINMIND_TOKEN != "your_token_here")


@lru_cache
def get_settings() -> Settings:
    """取得全域設定（單例模式）。"""
    return Settings()
