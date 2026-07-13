"""finmind.translate_columns — 欄位名稱中英對照工具。"""

from __future__ import annotations

from typing import Any

from finmind_mcp.client import FinMindClient
from finmind_mcp.config import get_settings
from finmind_mcp.datasets import DATASET_MAP


async def translate_columns(dataset: str) -> dict[str, Any]:
    """取得資料集欄位名稱的中英對照。

    Args:
        dataset: 資料集名稱，如 TaiwanStockPrice

    Returns:
        欄位名稱對照表
    """
    ds_meta = DATASET_MAP.get(dataset)
    if not ds_meta:
        return {
            "dataset": dataset,
            "error": f"找不到資料集 '{dataset}'，請確認名稱是否正確。",
            "translations": {},
        }

    settings = get_settings()
    async with FinMindClient(settings) as client:
        raw = await client.translate_columns(dataset)

    translations = raw.get("data", {})

    return {
        "dataset": dataset,
        "description": ds_meta.description,
        "translations": translations,
        "column_count": len(translations) if isinstance(translations, dict) else 0,
    }
