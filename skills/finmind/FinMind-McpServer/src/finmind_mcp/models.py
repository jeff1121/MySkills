"""Pydantic 資料模型 — FinMind API 回應與 MCP 工具的資料結構。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# FinMind API 回應模型
# ---------------------------------------------------------------------------


class FinMindAPIResponse(BaseModel):
    """FinMind API 標準回應格式。"""

    status: int = Field(description="HTTP 狀態碼，200 表示成功")
    msg: str = Field(default="success", description="回應訊息")
    data: list[dict[str, Any]] = Field(default_factory=list, description="資料陣列")


# ---------------------------------------------------------------------------
# 股票相關模型
# ---------------------------------------------------------------------------


class StockInfo(BaseModel):
    """台股股票基本資訊。"""

    stock_id: str = Field(description="股票代碼，如 2330")
    stock_name: str = Field(default="", description="股票名稱，如 台積電")
    industry_category: str = Field(default="", description="產業分類")
    type: str = Field(default="", description="股票類型（twse/tpex）")
    date: str = Field(default="", description="資料日期")


class StockPrice(BaseModel):
    """股價日成交資訊。"""

    date: str
    stock_id: str
    Trading_Volume: float = Field(default=0, description="成交股數")
    Trading_money: float = Field(default=0, description="成交金額")
    open: float = Field(default=0, description="開盤價")
    max: float = Field(default=0, description="最高價")
    min: float = Field(default=0, description="最低價")
    close: float = Field(default=0, description="收盤價")
    spread: float = Field(default=0, description="漲跌價差")
    Trading_turnover: float = Field(default=0, description="成交筆數")


# ---------------------------------------------------------------------------
# 分析結果模型
# ---------------------------------------------------------------------------


class AnalysisResult(BaseModel):
    """資料分析結果。"""

    stock_id: str = Field(description="股票代碼")
    analysis_type: str = Field(description="分析類型")
    period: str = Field(default="", description="分析期間")
    summary: str = Field(default="", description="分析摘要")
    metrics: dict[str, Any] = Field(default_factory=dict, description="分析指標")
    data: list[dict[str, Any]] = Field(default_factory=list, description="明細資料")


# ---------------------------------------------------------------------------
# MCP 工具回應模型
# ---------------------------------------------------------------------------


class ToolResult(BaseModel):
    """MCP 工具統一回應格式。"""

    ok: bool = Field(description="是否成功")
    result: Any | None = Field(default=None, description="回傳結果")
    error: dict[str, str] | None = Field(default=None, description="錯誤資訊")
    row_count: int = Field(default=0, description="資料筆數")


class UsageInfo(BaseModel):
    """API 使用量資訊。"""

    user_count: int = Field(default=0, description="目前已使用次數")
    api_request_limit: int = Field(default=0, description="每小時請求上限")
    remaining: int = Field(default=0, description="剩餘可用次數")
