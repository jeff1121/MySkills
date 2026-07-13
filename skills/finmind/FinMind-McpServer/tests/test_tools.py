"""MCP 工具單元測試。"""

from __future__ import annotations

import pytest

from finmind_mcp.datasets import DATASET_MAP, find_datasets, ALL_DATASETS, CATEGORY_MAP
from finmind_mcp.errors import DatasetError


class TestDatasets:
    """資料集對照表測試。"""

    def test_dataset_count(self) -> None:
        """確認資料集總數。"""
        # 至少 77 個資料集
        assert len(ALL_DATASETS) >= 77

    def test_dataset_map_lookup(self) -> None:
        """測試資料集名稱查詢。"""
        ds = DATASET_MAP.get("TaiwanStockPrice")
        assert ds is not None
        assert ds.description == "股價日成交資訊"
        assert ds.tier == "Free(w/ data_id)"
        assert "data_id" in ds.params

    def test_dataset_map_not_found(self) -> None:
        """測試不存在的資料集。"""
        assert DATASET_MAP.get("NonExistentDataset") is None

    def test_find_datasets_by_name(self) -> None:
        """測試以名稱搜尋資料集。"""
        results = find_datasets("Stock")
        assert len(results) > 0
        assert any("Stock" in ds.name for ds in results)

    def test_find_datasets_by_description(self) -> None:
        """測試以中文描述搜尋資料集。"""
        results = find_datasets("融資")
        assert len(results) > 0

    def test_category_map(self) -> None:
        """測試分類查詢。"""
        assert "台股-技術面" in CATEGORY_MAP
        assert "台股-籌碼面" in CATEGORY_MAP
        assert "台股-基本面" in CATEGORY_MAP
        assert "國際股市" in CATEGORY_MAP
        assert "全球經濟" in CATEGORY_MAP

    def test_all_datasets_have_required_fields(self) -> None:
        """確認所有資料集都有必要欄位。"""
        for ds in ALL_DATASETS:
            assert ds.name, f"資料集缺少名稱"
            assert ds.description, f"{ds.name} 缺少描述"
            assert ds.tier, f"{ds.name} 缺少等級"
            assert ds.category, f"{ds.name} 缺少分類"


class TestModels:
    """資料模型測試。"""

    def test_stock_info_model(self) -> None:
        """測試 StockInfo 模型。"""
        from finmind_mcp.models import StockInfo

        info = StockInfo(
            stock_id="2330",
            stock_name="台積電",
            industry_category="半導體業",
            type="twse",
        )
        assert info.stock_id == "2330"
        assert info.stock_name == "台積電"

    def test_tool_result_model(self) -> None:
        """測試 ToolResult 模型。"""
        from finmind_mcp.models import ToolResult

        result = ToolResult(ok=True, result={"data": [1, 2, 3]}, row_count=3)
        assert result.ok is True
        assert result.row_count == 3

    def test_usage_info_model(self) -> None:
        """測試 UsageInfo 模型。"""
        from finmind_mcp.models import UsageInfo

        usage = UsageInfo(user_count=100, api_request_limit=600, remaining=500)
        assert usage.remaining == 500


class TestErrors:
    """錯誤類別測試。"""

    def test_finmind_error(self) -> None:
        """測試基礎錯誤類別。"""
        from finmind_mcp.errors import FinMindError

        err = FinMindError("測試錯誤", error_code="TEST", remediation="重試")
        assert err.message == "測試錯誤"
        assert err.error_code == "TEST"
        d = err.to_dict()
        assert d["error_code"] == "TEST"
        assert d["remediation"] == "重試"

    def test_dataset_error(self) -> None:
        """測試資料集錯誤。"""
        err = DatasetError("找不到資料集")
        assert err.error_code == "DATASET_ERROR"
        assert "finmind.list_data_ids" in err.remediation
