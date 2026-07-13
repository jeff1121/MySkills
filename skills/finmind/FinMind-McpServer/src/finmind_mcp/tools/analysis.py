"""finmind.analyze — 股票資料分析工具。

提供基本統計分析、趨勢分析、技術指標計算等功能。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from finmind_mcp.client import FinMindClient
from finmind_mcp.config import get_settings


async def analyze(
    stock_id: str,
    analysis_type: str = "summary",
    start_date: str = "",
    end_date: str = "",
    dataset: str = "TaiwanStockPrice",
) -> dict[str, Any]:
    """分析股票資料。

    Args:
        stock_id: 股票代碼（必填），如 2330
        analysis_type: 分析類型
            - summary: 基本統計摘要（預設）
            - trend: 趨勢分析（移動平均線、漲跌趨勢）
            - volatility: 波動度分析
            - volume: 成交量分析
            - technical: 技術指標（MA、RSI、MACD）
            - fundamental: 基本面摘要（PER/PBR + 月營收）
        start_date: 開始日期 (YYYY-MM-DD)，預設為 3 個月前
        end_date: 結束日期 (YYYY-MM-DD)，預設為今天

    Returns:
        分析結果字典
    """
    # 預設日期範圍：最近 3 個月
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    settings = get_settings()

    # 根據分析類型決定查詢策略
    if analysis_type == "fundamental":
        return await _analyze_fundamental(settings, stock_id, start_date, end_date)

    # 技術面分析：取得股價資料
    async with FinMindClient(settings) as client:
        raw = await client.query_data(
            dataset=dataset,
            data_id=stock_id,
            start_date=start_date,
            end_date=end_date,
        )

    records = raw.get("data", [])
    if not records:
        return {
            "stock_id": stock_id,
            "analysis_type": analysis_type,
            "period": f"{start_date} ~ {end_date}",
            "error": "查無資料，請確認股票代碼與日期範圍。",
        }

    df = pd.DataFrame(records)

    # 確保數值欄位正確
    numeric_cols = ["open", "max", "min", "close", "spread", "Trading_Volume", "Trading_money", "Trading_turnover"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "date" in df.columns:
        df = df.sort_values("date")

    # 根據分析類型執行對應分析
    analyzers = {
        "summary": _analyze_summary,
        "trend": _analyze_trend,
        "volatility": _analyze_volatility,
        "volume": _analyze_volume,
        "technical": _analyze_technical,
    }

    analyzer = analyzers.get(analysis_type, _analyze_summary)
    result = analyzer(df, stock_id)

    result["period"] = f"{start_date} ~ {end_date}"
    result["total_trading_days"] = len(df)
    return result


def _analyze_summary(df: pd.DataFrame, stock_id: str) -> dict[str, Any]:
    """基本統計摘要。"""
    result: dict[str, Any] = {
        "stock_id": stock_id,
        "analysis_type": "summary",
    }

    if "close" in df.columns:
        close = df["close"]
        result["price"] = {
            "latest": float(close.iloc[-1]),
            "highest": float(close.max()),
            "lowest": float(close.min()),
            "mean": round(float(close.mean()), 2),
            "std": round(float(close.std()), 2),
            "change": round(float(close.iloc[-1] - close.iloc[0]), 2),
            "change_pct": round(float((close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100), 2),
        }

    if "Trading_Volume" in df.columns:
        vol = df["Trading_Volume"]
        result["volume"] = {
            "avg_daily": round(float(vol.mean()), 0),
            "max_daily": float(vol.max()),
            "min_daily": float(vol.min()),
        }

    if "spread" in df.columns:
        spread = df["spread"]
        result["spread"] = {
            "up_days": int((spread > 0).sum()),
            "down_days": int((spread < 0).sum()),
            "flat_days": int((spread == 0).sum()),
            "max_gain": float(spread.max()),
            "max_loss": float(spread.min()),
        }

    return result


def _analyze_trend(df: pd.DataFrame, stock_id: str) -> dict[str, Any]:
    """趨勢分析：移動平均線與趨勢判斷。"""
    result: dict[str, Any] = {
        "stock_id": stock_id,
        "analysis_type": "trend",
    }

    if "close" not in df.columns:
        result["error"] = "無收盤價資料"
        return result

    close = df["close"]

    # 計算移動平均線
    ma_periods = [5, 10, 20, 60]
    ma_data: dict[str, float | None] = {}
    for period in ma_periods:
        if len(close) >= period:
            ma_data[f"MA{period}"] = round(float(close.rolling(period).mean().iloc[-1]), 2)
        else:
            ma_data[f"MA{period}"] = None

    result["moving_averages"] = ma_data
    result["latest_close"] = float(close.iloc[-1])

    # 趨勢判斷
    trends: list[str] = []
    latest = close.iloc[-1]
    for key, val in ma_data.items():
        if val is not None:
            if latest > val:
                trends.append(f"股價在 {key} 之上（多頭）")
            else:
                trends.append(f"股價在 {key} 之下（空頭）")

    result["trend_signals"] = trends

    # 短期趨勢（近 5 日）
    if len(close) >= 5:
        recent = close.tail(5)
        if recent.iloc[-1] > recent.iloc[0]:
            result["short_term"] = "短期上升趨勢"
        elif recent.iloc[-1] < recent.iloc[0]:
            result["short_term"] = "短期下降趨勢"
        else:
            result["short_term"] = "短期持平"

    return result


def _analyze_volatility(df: pd.DataFrame, stock_id: str) -> dict[str, Any]:
    """波動度分析。"""
    result: dict[str, Any] = {
        "stock_id": stock_id,
        "analysis_type": "volatility",
    }

    if "close" not in df.columns:
        result["error"] = "無收盤價資料"
        return result

    close = df["close"]
    # 日報酬率
    returns = close.pct_change().dropna()

    result["daily_returns"] = {
        "mean_pct": round(float(returns.mean() * 100), 4),
        "std_pct": round(float(returns.std() * 100), 4),
        "max_gain_pct": round(float(returns.max() * 100), 2),
        "max_loss_pct": round(float(returns.min() * 100), 2),
    }

    # 年化波動度
    if len(returns) > 1:
        annualized_vol = float(returns.std() * (252 ** 0.5) * 100)
        result["annualized_volatility_pct"] = round(annualized_vol, 2)

    # 價格振幅
    if "max" in df.columns and "min" in df.columns:
        amplitude = ((df["max"] - df["min"]) / df["min"] * 100).dropna()
        result["daily_amplitude"] = {
            "mean_pct": round(float(amplitude.mean()), 2),
            "max_pct": round(float(amplitude.max()), 2),
        }

    return result


def _analyze_volume(df: pd.DataFrame, stock_id: str) -> dict[str, Any]:
    """成交量分析。"""
    result: dict[str, Any] = {
        "stock_id": stock_id,
        "analysis_type": "volume",
    }

    if "Trading_Volume" not in df.columns:
        result["error"] = "無成交量資料"
        return result

    vol = df["Trading_Volume"]
    avg_vol = vol.mean()

    result["volume_stats"] = {
        "avg_daily": round(float(avg_vol), 0),
        "latest": float(vol.iloc[-1]),
        "max": float(vol.max()),
        "min": float(vol.min()),
    }

    # 量能變化
    if len(vol) >= 5:
        recent_avg = vol.tail(5).mean()
        vol_ratio = recent_avg / avg_vol if avg_vol > 0 else 0
        result["volume_trend"] = {
            "recent_5day_avg": round(float(recent_avg), 0),
            "volume_ratio": round(float(vol_ratio), 2),
            "signal": "量增" if vol_ratio > 1.2 else ("量縮" if vol_ratio < 0.8 else "量穩"),
        }

    # 找出爆量日
    if avg_vol > 0:
        threshold = avg_vol * 2
        high_vol_days = df[vol > threshold]
        if not high_vol_days.empty and "date" in df.columns:
            result["high_volume_days"] = high_vol_days[["date", "Trading_Volume", "close"]].to_dict("records")[:10]

    return result


def _analyze_technical(df: pd.DataFrame, stock_id: str) -> dict[str, Any]:
    """技術指標分析：MA、RSI、MACD。"""
    result: dict[str, Any] = {
        "stock_id": stock_id,
        "analysis_type": "technical",
    }

    if "close" not in df.columns:
        result["error"] = "無收盤價資料"
        return result

    close = df["close"]

    # 移動平均線
    ma_data: dict[str, float | None] = {}
    for period in [5, 10, 20, 60]:
        if len(close) >= period:
            ma_data[f"MA{period}"] = round(float(close.rolling(period).mean().iloc[-1]), 2)
    result["moving_averages"] = ma_data

    # RSI (14 日)
    if len(close) >= 15:
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi = 100 - (100 / (1 + rs))
        rsi_value = float(rsi.iloc[-1])
        result["RSI_14"] = round(rsi_value, 2)
        if rsi_value > 70:
            result["RSI_signal"] = "超買區（>70），注意回檔風險"
        elif rsi_value < 30:
            result["RSI_signal"] = "超賣區（<30），可能有反彈機會"
        else:
            result["RSI_signal"] = "中性區間"

    # MACD (12, 26, 9)
    if len(close) >= 26:
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        result["MACD"] = {
            "MACD": round(float(macd_line.iloc[-1]), 4),
            "signal": round(float(signal_line.iloc[-1]), 4),
            "histogram": round(float(histogram.iloc[-1]), 4),
        }
        if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0:
            result["MACD_signal"] = "MACD 柱狀體由負轉正（黃金交叉），可能上漲訊號"
        elif histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0:
            result["MACD_signal"] = "MACD 柱狀體由正轉負（死亡交叉），可能下跌訊號"
        elif histogram.iloc[-1] > 0:
            result["MACD_signal"] = "MACD 柱狀體為正（多頭趨勢）"
        else:
            result["MACD_signal"] = "MACD 柱狀體為負（空頭趨勢）"

    result["latest_close"] = float(close.iloc[-1])
    return result


async def _analyze_fundamental(
    settings: Any, stock_id: str, start_date: str, end_date: str
) -> dict[str, Any]:
    """基本面分析：PER/PBR + 月營收。"""
    result: dict[str, Any] = {
        "stock_id": stock_id,
        "analysis_type": "fundamental",
        "period": f"{start_date} ~ {end_date}",
    }

    async with FinMindClient(settings) as client:
        # 取得 PER/PBR
        try:
            per_raw = await client.query_data(
                dataset="TaiwanStockPER",
                data_id=stock_id,
                start_date=start_date,
                end_date=end_date,
            )
            per_data = per_raw.get("data", [])
            if per_data:
                df_per = pd.DataFrame(per_data)
                for col in ["PER", "PBR", "dividend_yield"]:
                    if col in df_per.columns:
                        df_per[col] = pd.to_numeric(df_per[col], errors="coerce")

                latest = df_per.iloc[-1]
                result["valuation"] = {
                    "latest_PER": float(latest.get("PER", 0)),
                    "latest_PBR": float(latest.get("PBR", 0)),
                    "latest_dividend_yield": float(latest.get("dividend_yield", 0)),
                    "date": str(latest.get("date", "")),
                }
        except Exception:
            result["valuation_error"] = "無法取得 PER/PBR 資料"

        # 取得月營收
        try:
            rev_raw = await client.query_data(
                dataset="TaiwanStockMonthRevenue",
                data_id=stock_id,
                start_date=start_date,
                end_date=end_date,
            )
            rev_data = rev_raw.get("data", [])
            if rev_data:
                df_rev = pd.DataFrame(rev_data)
                df_rev["revenue"] = pd.to_numeric(df_rev["revenue"], errors="coerce")
                result["monthly_revenue"] = {
                    "latest": float(df_rev["revenue"].iloc[-1]),
                    "avg": round(float(df_rev["revenue"].mean()), 0),
                    "max": float(df_rev["revenue"].max()),
                    "min": float(df_rev["revenue"].min()),
                    "months": len(df_rev),
                    "trend": "成長" if df_rev["revenue"].iloc[-1] > df_rev["revenue"].mean() else "衰退",
                }
        except Exception:
            result["revenue_error"] = "無法取得月營收資料"

    return result
