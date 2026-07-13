"""自定義錯誤類別 — FinMind MCP Server 的錯誤處理。"""

from __future__ import annotations


class FinMindError(Exception):
    """FinMind MCP Server 基礎錯誤。"""

    def __init__(
        self,
        message: str,
        error_code: str = "FINMIND_ERROR",
        remediation: str = "",
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.remediation = remediation
        super().__init__(message)

    def to_dict(self) -> dict[str, str]:
        """轉換為字典格式，方便 JSON 序列化。"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "remediation": self.remediation,
        }


class AuthenticationError(FinMindError):
    """API Token 認證失敗。"""

    def __init__(self, message: str = "API Token 認證失敗") -> None:
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            remediation="請確認 FINMIND_TOKEN 環境變數已設定正確。到 https://finmindtrade.com/ 註冊並登入取得 Token。",
        )


class RateLimitError(FinMindError):
    """API 請求頻率超限。"""

    def __init__(self, message: str = "API 請求頻率超限 (HTTP 402)") -> None:
        super().__init__(
            message=message,
            error_code="RATE_LIMIT",
            remediation="已超過每小時請求上限（免費 600 次/小時）。請稍後再試，或升級帳號方案。",
        )


class DatasetError(FinMindError):
    """資料集查詢錯誤。"""

    def __init__(self, message: str = "資料集查詢失敗") -> None:
        super().__init__(
            message=message,
            error_code="DATASET_ERROR",
            remediation="請確認 dataset 名稱正確，可使用 finmind.list_data_ids 工具查詢可用的資料集。",
        )


class APIError(FinMindError):
    """FinMind API 回傳錯誤。"""

    def __init__(self, message: str = "FinMind API 回傳錯誤", status_code: int = 0) -> None:
        self.status_code = status_code
        super().__init__(
            message=f"{message} (status={status_code})" if status_code else message,
            error_code="API_ERROR",
            remediation="請檢查查詢參數是否正確，或稍後再試。",
        )


class ConfigError(FinMindError):
    """設定錯誤。"""

    def __init__(self, message: str = "設定錯誤") -> None:
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            remediation="請確認 .env 檔案或環境變數已正確設定。參考 .env.example 範例。",
        )
