"""finmind.list_data_ids & finmind.stock_search — 資料集 ID 列表與股票搜尋工具。"""

from __future__ import annotations

from typing import Any

from finmind_mcp.client import FinMindClient
from finmind_mcp.config import get_settings
from finmind_mcp.datasets import ALL_DATASETS, CATEGORY_MAP, DATASET_MAP, find_datasets


async def list_data_ids(dataset: str) -> dict[str, Any]:
    """列出某資料集可用的 data_id。

    Args:
        dataset: 資料集名稱，如 TaiwanStockPrice

    Returns:
        包含可用 data_id 清單的字典
    """
    ds_meta = DATASET_MAP.get(dataset)
    if not ds_meta:
        # 嘗試模糊搜尋
        matches = find_datasets(dataset)
        if matches:
            suggestions = [f"  - {m.name}: {m.description}" for m in matches[:5]]
            return {
                "dataset": dataset,
                "error": f"找不到資料集 '{dataset}'",
                "suggestions": suggestions,
                "data_ids": [],
            }
        return {
            "dataset": dataset,
            "error": f"找不到資料集 '{dataset}'，請確認名稱是否正確。",
            "data_ids": [],
        }

    settings = get_settings()
    async with FinMindClient(settings) as client:
        raw = await client.list_data_ids(dataset)

    data_ids = raw.get("data", [])

    return {
        "dataset": dataset,
        "description": ds_meta.description,
        "tier": ds_meta.tier,
        "category": ds_meta.category,
        "total_count": len(data_ids),
        "data_ids": data_ids,
    }


async def stock_search(keyword: str) -> dict[str, Any]:
    """以名稱或代碼搜尋股票。

    優先在本地資料集對照表中搜尋，再透過 TaiwanStockInfo API 查詢。

    Args:
        keyword: 搜尋關鍵字（股票代碼、名稱、產業分類）

    Returns:
        符合條件的股票清單
    """
    settings = get_settings()

    # 透過 TaiwanStockInfo API 搜尋
    async with FinMindClient(settings) as client:
        raw = await client.query_data(dataset="TaiwanStockInfo")

    records = raw.get("data", [])
    keyword_lower = keyword.lower()

    # 過濾符合條件的股票
    matches = [
        r for r in records
        if keyword_lower in str(r.get("stock_id", "")).lower()
        or keyword_lower in str(r.get("stock_name", "")).lower()
        or keyword_lower in str(r.get("industry_category", "")).lower()
    ]

    # 準備可用資料集清單
    available_datasets: list[str] = []
    for ds in ALL_DATASETS:
        if "data_id" in ds.params:
            available_datasets.append(f"{ds.name}: {ds.description} ({ds.tier})")

    return {
        "keyword": keyword,
        "total_matches": len(matches),
        "stocks": matches[:50],  # 最多回傳 50 筆
        "tip": "找到股票代碼後，可使用 finmind.query_data 查詢詳細資料",
        "common_datasets": [
            "TaiwanStockPrice: 股價日成交資訊",
            "TaiwanStockPER: PER/PBR",
            "TaiwanStockInstitutionalInvestorsBuySell: 三大法人買賣",
            "TaiwanStockFinancialStatements: 綜合損益表",
            "TaiwanStockMonthRevenue: 月營收",
            "TaiwanStockDividend: 股利政策",
        ],
    }


def list_all_datasets(category: str = "") -> dict[str, Any]:
    """列出所有可用的資料集（本地查詢，不需 API 呼叫）。

    Args:
        category: 篩選分類（留空列出全部）

    Returns:
        資料集清單
    """
    if category:
        datasets = CATEGORY_MAP.get(category, [])
        if not datasets:
            return {
                "category": category,
                "error": f"找不到分類 '{category}'",
                "available_categories": list(CATEGORY_MAP.keys()),
                "datasets": [],
            }
    else:
        datasets = ALL_DATASETS

    return {
        "category": category or "全部",
        "total_count": len(datasets),
        "categories": list(CATEGORY_MAP.keys()),
        "datasets": [
            {
                "name": ds.name,
                "description": ds.description,
                "tier": ds.tier,
                "category": ds.category,
                "params": ds.params,
            }
            for ds in datasets
        ],
    }
