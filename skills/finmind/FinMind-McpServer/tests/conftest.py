"""測試共用 fixtures。"""

from __future__ import annotations

import pytest

from finmind_mcp.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """測試用設定（不連接真實 API）。"""
    return Settings(
        FINMIND_TOKEN="test-token-12345",
        FINMIND_API_BASE_URL="https://api.finmindtrade.com/api/v4",
        LOG_LEVEL="DEBUG",
        HTTP_TIMEOUT=10,
    )


@pytest.fixture
def sample_stock_price_response() -> dict:
    """模擬 TaiwanStockPrice API 回應。"""
    return {
        "status": 200,
        "msg": "success",
        "data": [
            {
                "date": "2024-01-02",
                "stock_id": "2330",
                "Trading_Volume": 25_000_000,
                "Trading_money": 14_500_000_000,
                "open": 578.0,
                "max": 582.0,
                "min": 576.0,
                "close": 580.0,
                "spread": 3.0,
                "Trading_turnover": 15000,
            },
            {
                "date": "2024-01-03",
                "stock_id": "2330",
                "Trading_Volume": 30_000_000,
                "Trading_money": 17_400_000_000,
                "open": 580.0,
                "max": 585.0,
                "min": 578.0,
                "close": 583.0,
                "spread": 3.0,
                "Trading_turnover": 18000,
            },
            {
                "date": "2024-01-04",
                "stock_id": "2330",
                "Trading_Volume": 22_000_000,
                "Trading_money": 12_900_000_000,
                "open": 583.0,
                "max": 586.0,
                "min": 580.0,
                "close": 585.0,
                "spread": 2.0,
                "Trading_turnover": 13000,
            },
        ],
    }


@pytest.fixture
def sample_stock_info_response() -> dict:
    """模擬 TaiwanStockInfo API 回應。"""
    return {
        "status": 200,
        "msg": "success",
        "data": [
            {
                "stock_id": "2330",
                "stock_name": "台積電",
                "industry_category": "半導體業",
                "type": "twse",
                "date": "2024-01-02",
            },
            {
                "stock_id": "2317",
                "stock_name": "鴻海",
                "industry_category": "其他電子業",
                "type": "twse",
                "date": "2024-01-02",
            },
            {
                "stock_id": "2454",
                "stock_name": "聯發科",
                "industry_category": "半導體業",
                "type": "twse",
                "date": "2024-01-02",
            },
        ],
    }
