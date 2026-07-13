"""finmind.query_data — 通用資料查詢工具。

支援查詢 FinMind API 所有資料集，回傳結構化表格資料。
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from finmind_mcp.client import FinMindClient
from finmind_mcp.config import get_settings
from finmind_mcp.datasets import DATASET_MAP
from finmind_mcp.errors import DatasetError


async def query_data(
    dataset: str,
    data_id: str = "",
    start_date: str = "",
    end_date: str = "",
    row_limit: int = 100,
) -> dict[str, Any]:
    """查詢 FinMind 資料集。

    Args:
        dataset: 資料集名稱（必填），如 TaiwanStockPrice
        data_id: 資料識別碼（如股票代碼 2330），部分資料集必填
        start_date: 開始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        row_limit: 回傳最大筆數（預設 100，設 0 不限制）

    Returns:
        包含資料表格、欄位資訊與統計摘要的字典
    """
    # 驗證資料集名稱
    ds_meta = DATASET_MAP.get(dataset)
    if not ds_meta:
        raise DatasetError(f"找不到資料集 '{dataset}'。請使用 finmind.list_data_ids 查詢可用的資料集。")

    settings = get_settings()
    async with FinMindClient(settings) as client:
        raw = await client.query_data(
            dataset=dataset,
            data_id=data_id,
            start_date=start_date,
            end_date=end_date,
        )

    records: list[dict[str, Any]] = raw.get("data", [])
    total_count = len(records)

    if not records:
        return {
            "dataset": dataset,
            "data_id": data_id,
            "period": f"{start_date} ~ {end_date}",
            "total_count": 0,
            "columns": ds_meta.key_columns,
            "data": [],
            "summary": "查無資料。請確認查詢參數是否正確。",
        }

    # 轉為 DataFrame 方便處理
    df = pd.DataFrame(records)

    # 基本統計摘要
    summary_parts: list[str] = [
        f"資料集: {ds_meta.description} ({dataset})",
        f"總筆數: {total_count}",
    ]

    if "date" in df.columns:
        summary_parts.append(f"日期範圍: {df['date'].min()} ~ {df['date'].max()}")
    if data_id:
        summary_parts.append(f"查詢標的: {data_id}")

    # 限制回傳筆數
    if row_limit > 0 and total_count > row_limit:
        records = records[:row_limit]
        summary_parts.append(f"⚠️ 僅顯示前 {row_limit} 筆（共 {total_count} 筆）")

    return {
        "dataset": dataset,
        "description": ds_meta.description,
        "tier": ds_meta.tier,
        "data_id": data_id,
        "period": f"{start_date} ~ {end_date}",
        "total_count": total_count,
        "displayed_count": len(records),
        "columns": list(df.columns),
        "data": records,
        "summary": " | ".join(summary_parts),
    }
