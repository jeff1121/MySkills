"""FinMind MCP Server — 使用 FastMCP 提供金融數據查詢與分析工具。

啟動方式：
  - stdio 模式：python -m finmind_mcp.server
  - HTTP 模式：python -m finmind_mcp.server --http [port]

MCP 工具清單：
  1. finmind_query_data      — 通用資料查詢
  2. finmind_list_data_ids   — 資料集 ID 列表
  3. finmind_translate_columns — 欄位名稱中英對照
  4. finmind_stock_search    — 股票搜尋
  5. finmind_analyze         — 資料分析
  6. finmind_check_usage     — API 使用量查詢
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from finmind_mcp.log import setup_logging
from finmind_mcp.tools import analysis, query, search, translate, usage

# 初始化日誌
setup_logging()

# 建立 FastMCP 伺服器
mcp = FastMCP(
    "FinMind 金融數據助手",
    instructions="透過 FinMind API 查詢台股、美股、期貨、選擇權等金融資料，並進行技術分析與基本面分析。",
)


# ---------------------------------------------------------------------------
# MCP 工具註冊
# ---------------------------------------------------------------------------


@mcp.tool()
async def finmind_query_data(
    dataset: str,
    data_id: str = "",
    start_date: str = "",
    end_date: str = "",
    row_limit: int = 100,
) -> str:
    """查詢 FinMind 資料集。

    支援 77+ 個資料集，涵蓋台股技術面、籌碼面、基本面、衍生品、國際股市、全球經濟指標。

    Args:
        dataset: 資料集名稱（必填），如 TaiwanStockPrice、USStockPrice
        data_id: 資料識別碼（如股票代碼 2330），部分資料集必填
        start_date: 開始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        row_limit: 回傳最大筆數（預設 100，設 0 不限制）
    """
    result = await query.query_data(
        dataset=dataset,
        data_id=data_id,
        start_date=start_date,
        end_date=end_date,
        row_limit=row_limit,
    )
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def finmind_list_data_ids(dataset: str) -> str:
    """列出某資料集可用的 data_id（如股票代碼清單）。

    Args:
        dataset: 資料集名稱，如 TaiwanStockPrice
    """
    result = await search.list_data_ids(dataset)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def finmind_translate_columns(dataset: str) -> str:
    """取得資料集欄位名稱的中英對照翻譯。

    Args:
        dataset: 資料集名稱，如 TaiwanStockPrice
    """
    result = await translate.translate_columns(dataset)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def finmind_stock_search(keyword: str) -> str:
    """以名稱或代碼搜尋股票。透過 TaiwanStockInfo 資料集查詢。

    Args:
        keyword: 搜尋關鍵字（股票代碼如 2330、名稱如 台積電、或產業分類如 半導體）
    """
    result = await search.stock_search(keyword)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def finmind_analyze(
    stock_id: str,
    analysis_type: str = "summary",
    start_date: str = "",
    end_date: str = "",
    dataset: str = "TaiwanStockPrice",
) -> str:
    """分析股票資料，提供技術分析與基本面分析。

    Args:
        stock_id: 股票代碼（必填），如 2330
        analysis_type: 分析類型
            - summary: 基本統計摘要（預設）
            - trend: 趨勢分析（移動平均線）
            - volatility: 波動度分析
            - volume: 成交量分析
            - technical: 技術指標（MA、RSI、MACD）
            - fundamental: 基本面（PER/PBR + 月營收）
        start_date: 開始日期 (YYYY-MM-DD)，預設 3 個月前
        end_date: 結束日期 (YYYY-MM-DD)，預設今天
        dataset: 資料集名稱（預設 TaiwanStockPrice）
    """
    result = await analysis.analyze(
        stock_id=stock_id,
        analysis_type=analysis_type,
        start_date=start_date,
        end_date=end_date,
        dataset=dataset,
    )
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def finmind_check_usage() -> str:
    """查詢 FinMind API 使用量與配額。需要已設定 FINMIND_TOKEN 環境變數。"""
    result = await usage.check_usage()
    return json.dumps(result, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# MCP 資源：資料集參考
# ---------------------------------------------------------------------------


@mcp.resource("finmind://datasets")
def get_datasets_catalog() -> str:
    """取得 FinMind 所有可用資料集的完整清單。"""
    result = search.list_all_datasets()
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.resource("finmind://datasets/{category}")
def get_datasets_by_category(category: str) -> str:
    """取得特定分類的資料集清單。"""
    result = search.list_all_datasets(category=category)
    return json.dumps(result, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# 進入點
# ---------------------------------------------------------------------------


def main() -> None:
    """MCP Server 進入點。"""
    import sys

    if "--http" in sys.argv:
        # HTTP/SSE 模式 — 透過設定 FastMCP 的 host/port 再以 SSE 啟動
        idx = sys.argv.index("--http")
        port = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit() else 8080
        mcp.settings.host = "0.0.0.0"  # type: ignore[assignment]
        mcp.settings.port = port  # type: ignore[assignment]
        mcp.run(transport="sse")
    else:
        # 預設 stdio 模式
        mcp.run()


if __name__ == "__main__":
    main()
