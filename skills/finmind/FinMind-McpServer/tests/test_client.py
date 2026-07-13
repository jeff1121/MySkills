"""FinMind API 客戶端單元測試。"""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from finmind_mcp.client import FinMindClient
from finmind_mcp.config import Settings
from finmind_mcp.errors import AuthenticationError, RateLimitError, APIError


@pytest.fixture
def settings() -> Settings:
    """測試用設定。"""
    return Settings(
        FINMIND_TOKEN="test-token",
        FINMIND_API_BASE_URL="https://api.finmindtrade.com/api/v4",
        HTTP_TIMEOUT=10,
    )


class TestFinMindClient:
    """FinMindClient 測試。"""

    @respx.mock
    @pytest.mark.asyncio
    async def test_query_data_success(self, settings: Settings, sample_stock_price_response: dict) -> None:
        """測試成功查詢股價資料。"""
        respx.get("https://api.finmindtrade.com/api/v4/data").mock(
            return_value=Response(200, json=sample_stock_price_response)
        )

        async with FinMindClient(settings) as client:
            result = await client.query_data(
                dataset="TaiwanStockPrice",
                data_id="2330",
                start_date="2024-01-01",
                end_date="2024-01-31",
            )

        assert result["status"] == 200
        assert len(result["data"]) == 3
        assert result["data"][0]["stock_id"] == "2330"

    @respx.mock
    @pytest.mark.asyncio
    async def test_query_data_auth_error(self, settings: Settings) -> None:
        """測試認證失敗 (401)。"""
        respx.get("https://api.finmindtrade.com/api/v4/data").mock(
            return_value=Response(401, json={"msg": "Unauthorized"})
        )

        async with FinMindClient(settings) as client:
            with pytest.raises(AuthenticationError):
                await client.query_data(dataset="TaiwanStockPrice", data_id="2330")

    @respx.mock
    @pytest.mark.asyncio
    async def test_query_data_rate_limit(self, settings: Settings) -> None:
        """測試頻率超限 (402)。"""
        respx.get("https://api.finmindtrade.com/api/v4/data").mock(
            return_value=Response(402, json={"msg": "Rate limit exceeded"})
        )

        async with FinMindClient(settings) as client:
            with pytest.raises(RateLimitError):
                await client.query_data(dataset="TaiwanStockPrice", data_id="2330")

    @respx.mock
    @pytest.mark.asyncio
    async def test_query_data_api_error(self, settings: Settings) -> None:
        """測試 API 回傳錯誤狀態。"""
        respx.get("https://api.finmindtrade.com/api/v4/data").mock(
            return_value=Response(200, json={"status": 400, "msg": "參數錯誤", "data": []})
        )

        async with FinMindClient(settings) as client:
            with pytest.raises(APIError):
                await client.query_data(dataset="InvalidDataset")

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_data_ids(self, settings: Settings) -> None:
        """測試列出 data_id。"""
        mock_response = {
            "status": 200,
            "msg": "success",
            "data": ["2330", "2317", "2454"],
        }
        respx.get("https://api.finmindtrade.com/api/v4/datalist").mock(
            return_value=Response(200, json=mock_response)
        )

        async with FinMindClient(settings) as client:
            result = await client.list_data_ids("TaiwanStockPrice")

        assert result["status"] == 200
        assert "2330" in result["data"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_translate_columns(self, settings: Settings) -> None:
        """測試欄位翻譯。"""
        mock_response = {
            "status": 200,
            "msg": "success",
            "data": {"open": "開盤價", "close": "收盤價", "max": "最高價"},
        }
        respx.get("https://api.finmindtrade.com/api/v4/translation").mock(
            return_value=Response(200, json=mock_response)
        )

        async with FinMindClient(settings) as client:
            result = await client.translate_columns("TaiwanStockPrice")

        assert result["data"]["open"] == "開盤價"


class TestSettings:
    """設定模組測試。"""

    def test_validate_token_with_valid_token(self) -> None:
        """測試有效 Token 驗證。"""
        s = Settings(FINMIND_TOKEN="real-token-123")
        assert s.validate_token() is True

    def test_validate_token_with_empty_token(self) -> None:
        """測試空 Token 驗證。"""
        s = Settings(FINMIND_TOKEN="")
        assert s.validate_token() is False

    def test_validate_token_with_placeholder(self) -> None:
        """測試佔位符 Token 驗證。"""
        s = Settings(FINMIND_TOKEN="your_token_here")
        assert s.validate_token() is False
