"""FinMind API HTTP 客戶端 — 負責與 FinMind API 通訊。

支援的端點：
  - GET /data      — 查詢資料集
  - GET /datalist  — 列出資料集可用的 data_id
  - GET /translation — 欄位名稱中英對照

Rate Limit：
  - 有 Token：600 次/小時
  - 無 Token：300 次/小時
  - 超限回傳 HTTP 402
"""

from __future__ import annotations

from typing import Any

import httpx

from finmind_mcp.config import Settings, get_settings
from finmind_mcp.errors import APIError, AuthenticationError, RateLimitError
from finmind_mcp.log import get_logger

logger = get_logger(__name__)


class FinMindClient:
    """FinMind API 非同步 HTTP 客戶端。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "FinMindClient":
        """建立 HTTP 連線。"""
        headers: dict[str, str] = {}
        if self._settings.validate_token():
            headers["Authorization"] = f"Bearer {self._settings.FINMIND_TOKEN}"

        self._client = httpx.AsyncClient(
            base_url=self._settings.FINMIND_API_BASE_URL,
            headers=headers,
            timeout=httpx.Timeout(self._settings.HTTP_TIMEOUT),
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """關閉 HTTP 連線。"""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """取得 HTTP 客戶端實例。"""
        if self._client is None:
            raise RuntimeError("請使用 async with FinMindClient() 建立連線")
        return self._client

    # -----------------------------------------------------------------
    # 核心 API 方法
    # -----------------------------------------------------------------

    async def query_data(
        self,
        dataset: str,
        data_id: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> dict[str, Any]:
        """查詢資料集。

        Args:
            dataset: 資料集名稱（必填），如 TaiwanStockPrice
            data_id: 資料識別碼，如股票代碼 2330
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            API 回應的 JSON 資料

        Raises:
            AuthenticationError: Token 認證失敗
            RateLimitError: 請求頻率超限
            APIError: 其他 API 錯誤
        """
        params: dict[str, str] = {"dataset": dataset}
        if data_id:
            params["data_id"] = data_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return await self._get("/data", params)

    async def list_data_ids(self, dataset: str) -> dict[str, Any]:
        """列出資料集可用的 data_id。

        Args:
            dataset: 資料集名稱

        Returns:
            包含可用 data_id 清單的 JSON 資料
        """
        return await self._get("/datalist", {"dataset": dataset})

    async def translate_columns(self, dataset: str) -> dict[str, Any]:
        """取得資料集欄位名稱的中英對照。

        Args:
            dataset: 資料集名稱

        Returns:
            欄位名稱對照表的 JSON 資料
        """
        return await self._get("/translation", {"dataset": dataset})

    async def check_usage(self) -> dict[str, Any]:
        """查詢 API 使用量。

        透過 user_info API 查詢目前的請求次數與上限。

        Returns:
            包含 user_count 與 api_request_limit 的 JSON 資料
        """
        # user_info 使用不同的 base URL
        headers: dict[str, str] = {}
        if self._settings.validate_token():
            headers["Authorization"] = f"Bearer {self._settings.FINMIND_TOKEN}"

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.HTTP_TIMEOUT),
        ) as client:
            resp = await client.get(
                self._settings.FINMIND_USER_INFO_URL,
                headers=headers,
            )
            self._check_response(resp)
            return resp.json()

    # -----------------------------------------------------------------
    # 內部方法
    # -----------------------------------------------------------------

    async def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        """發送 GET 請求並處理回應。"""
        logger.debug("api_request", path=path, params=params)

        resp = await self.client.get(path, params=params)
        self._check_response(resp)

        data = resp.json()

        # 檢查 FinMind 自訂狀態碼
        status = data.get("status")
        if status and status != 200:
            msg = data.get("msg", "未知錯誤")
            logger.warning("api_error", path=path, status=status, msg=msg)
            raise APIError(message=msg, status_code=status)

        logger.debug(
            "api_response",
            path=path,
            row_count=len(data.get("data", [])),
        )
        return data

    @staticmethod
    def _check_response(resp: httpx.Response) -> None:
        """檢查 HTTP 回應狀態碼。"""
        if resp.status_code == 401 or resp.status_code == 403:
            raise AuthenticationError()
        if resp.status_code == 402:
            raise RateLimitError()
        if resp.status_code >= 400:
            raise APIError(
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
            )
