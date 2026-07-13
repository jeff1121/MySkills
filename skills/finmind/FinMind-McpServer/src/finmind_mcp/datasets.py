"""資料集參考對照表 — FinMind API 支援的所有資料集定義。

包含資料集名稱、描述、會員等級需求、必要參數與欄位說明。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DatasetMeta:
    """資料集後設資料。"""

    name: str
    description: str
    tier: str  # Free / Free(w/ data_id) / Backer / Sponsor
    category: str  # 分類
    params: list[str] = field(default_factory=list)  # 可用參數
    key_columns: list[str] = field(default_factory=list)  # 關鍵欄位
    note: str = ""  # 備註


# ---------------------------------------------------------------------------
# 台股技術面（20 個資料集）
# ---------------------------------------------------------------------------

TAIWAN_TECHNICAL: list[DatasetMeta] = [
    DatasetMeta("TaiwanStockInfo", "台股總覽", "Free", "台股-技術面",
                ["dataset"], ["industry_category", "stock_id", "stock_name", "type", "date"]),
    DatasetMeta("TaiwanStockInfoWithWarrant", "台股總覽含權證", "Free", "台股-技術面",
                ["dataset"], ["industry_category", "stock_id", "stock_name", "type", "date"]),
    DatasetMeta("TaiwanStockInfoWithWarrantSummary", "台股權證標的對照表", "Sponsor", "台股-技術面",
                ["data_id", "start_date"],
                ["stock_id", "date", "close", "target_stock_id", "target_close", "type", "exercise_ratio"]),
    DatasetMeta("TaiwanStockTradingDate", "台股交易日", "Free", "台股-技術面",
                ["dataset"], ["date"]),
    DatasetMeta("TaiwanStockPrice", "股價日成交資訊", "Free(w/ data_id)", "台股-技術面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "Trading_Volume", "Trading_money", "open", "max", "min", "close", "spread", "Trading_turnover"]),
    DatasetMeta("TaiwanStockPriceAdj", "還原股價", "Free(w/ data_id)", "台股-技術面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "Trading_Volume", "Trading_money", "open", "max", "min", "close", "spread", "Trading_turnover"]),
    DatasetMeta("TaiwanStockPriceTick", "歷史逐筆交易", "Backer", "台股-技術面",
                ["data_id", "start_date"],
                ["date", "stock_id", "deal_price", "volume", "Time", "TickType"],
                note="單日查詢"),
    DatasetMeta("TaiwanStockPER", "PER/PBR", "Free", "台股-技術面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "dividend_yield", "PER", "PBR"]),
    DatasetMeta("TaiwanStockStatisticsOfOrderBookAndTrade", "每5秒委託成交統計", "Free", "台股-技術面",
                ["start_date"],
                ["Time", "TotalBuyOrder", "TotalBuyVolume", "TotalSellOrder", "TotalSellVolume", "TotalDealVolume", "TotalDealMoney", "date"],
                note="單日查詢"),
    DatasetMeta("TaiwanVariousIndicators5Seconds", "台股加權指數", "Free", "台股-技術面",
                ["start_date"], ["date", "TAIEX"], note="單日查詢"),
    DatasetMeta("TaiwanStockDayTrading", "當沖交易", "Free(w/ data_id)", "台股-技術面",
                ["data_id", "start_date", "end_date"],
                ["stock_id", "date", "BuyAfterSale", "Volume", "BuyAmount", "SellAmount"]),
    DatasetMeta("TaiwanStockTotalReturnIndex", "報酬指數", "Free", "台股-技術面",
                ["data_id", "start_date", "end_date"],
                ["price", "stock_id", "date"],
                note="data_id: TAIEX 或 TPEx"),
    DatasetMeta("TaiwanStock10Year", "十年線", "Backer", "台股-技術面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "close"]),
    DatasetMeta("TaiwanStockKBar", "分K資料", "Sponsor", "台股-技術面",
                ["data_id", "start_date"],
                ["date", "minute", "stock_id", "open", "high", "low", "close", "volume"],
                note="單日查詢"),
    DatasetMeta("TaiwanStockWeekPrice", "週K", "Backer", "台股-技術面",
                ["data_id", "start_date", "end_date"],
                ["stock_id", "yweek", "max", "min", "trading_volume", "trading_money", "date", "close", "open", "spread"]),
    DatasetMeta("TaiwanStockMonthPrice", "月K", "Backer", "台股-技術面",
                ["data_id", "start_date", "end_date"],
                ["stock_id", "ymonth", "max", "min", "trading_volume", "trading_money", "date", "close", "open", "spread"]),
    DatasetMeta("TaiwanStockEvery5SecondsIndex", "每5秒指數統計", "Backer", "台股-技術面",
                ["start_date"], ["date", "time", "stock_id", "price", "kind"], note="單日查詢"),
    DatasetMeta("TaiwanStockSuspended", "暫停交易公告", "Backer", "台股-技術面",
                ["start_date", "end_date"],
                ["stock_id", "date", "suspension_time", "resumption_date"]),
    DatasetMeta("TaiwanStockDayTradingSuspension", "暫停先賣後買當沖", "Backer", "台股-技術面",
                ["start_date", "end_date"],
                ["stock_id", "date", "end_date", "reason"]),
    DatasetMeta("TaiwanStockPriceLimit", "每日漲跌停價", "Free(w/ data_id)", "台股-技術面",
                ["data_id", "start_date"],
                ["date", "stock_id", "reference_price", "limit_up", "limit_down"]),
]

# ---------------------------------------------------------------------------
# 台股籌碼面（18 個資料集）
# ---------------------------------------------------------------------------

TAIWAN_CHIP: list[DatasetMeta] = [
    DatasetMeta("TaiwanStockMarginPurchaseShortSale", "融資融劵", "Free(w/ data_id)", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "MarginPurchaseBuy", "MarginPurchaseSell", "MarginPurchaseTodayBalance",
                 "ShortSaleBuy", "ShortSaleSell", "ShortSaleTodayBalance"]),
    DatasetMeta("TaiwanStockTotalMarginPurchaseShortSale", "整體市場融資融劵", "Free", "台股-籌碼面",
                ["start_date", "end_date"],
                ["TodayBalance", "YesBalance", "buy", "date", "name", "Return", "sell"]),
    DatasetMeta("TaiwanStockInstitutionalInvestorsBuySell", "三大法人買賣", "Free(w/ data_id)", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "buy", "name", "sell"]),
    DatasetMeta("TaiwanStockTotalInstitutionalInvestors", "整體三大法人", "Free", "台股-籌碼面",
                ["start_date", "end_date"],
                ["buy", "date", "name", "sell"]),
    DatasetMeta("TaiwanStockShareholding", "外資持股", "Free(w/ data_id)", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "ForeignInvestmentShares", "ForeignInvestmentSharesRatio"]),
    DatasetMeta("TaiwanStockHoldingSharesPer", "股權持股分級", "Backer", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "HoldingSharesLevel", "people", "percent", "unit"]),
    DatasetMeta("TaiwanStockSecuritiesLending", "借券成交", "Free(w/ data_id)", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "transaction_type", "volume", "fee_rate", "close"]),
    DatasetMeta("TaiwanStockMarginShortSaleSuspension", "暫停融券賣出", "Free(w/ data_id)", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["stock_id", "date", "end_date", "reason"]),
    DatasetMeta("TaiwanDailyShortSaleBalances", "信用額度總量管制餘額", "Free(w/ data_id)", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["stock_id", "date", "MarginShortSalesBalance", "SBLShortSalesBalance"]),
    DatasetMeta("TaiwanSecuritiesTraderInfo", "證券商資訊", "Free", "台股-籌碼面",
                ["dataset"],
                ["securities_trader_id", "securities_trader", "date", "address", "phone"]),
    DatasetMeta("TaiwanStockTradingDailyReport", "分點資料", "Sponsor", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["securities_trader", "price", "buy", "sell", "securities_trader_id", "stock_id", "date"]),
    DatasetMeta("TaiwanStockWarrantTradingDailyReport", "權證分點資料", "Sponsor", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["securities_trader", "price", "buy", "sell", "securities_trader_id", "stock_id", "date"]),
    DatasetMeta("TaiwanstockGovernmentBankBuySell", "八大行庫買賣", "Sponsor", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "buy_amount", "sell_amount", "buy", "sell", "bank_name"]),
    DatasetMeta("TaiwanTotalExchangeMarginMaintenance", "大盤融資維持率", "Backer", "台股-籌碼面",
                ["start_date", "end_date"],
                ["date", "TotalExchangeMarginMaintenance"]),
    DatasetMeta("TaiwanStockTradingDailyReportSecIdAgg", "卷商分點統計", "Sponsor", "台股-籌碼面",
                ["data_id", "start_date", "end_date"],
                ["securities_trader", "securities_trader_id", "stock_id", "date", "buy_volume", "sell_volume"]),
    DatasetMeta("TaiwanStockDispositionSecuritiesPeriod", "處置有價證券", "Backer", "台股-籌碼面",
                ["start_date", "end_date"],
                ["date", "stock_id", "stock_name", "disposition_cnt", "condition", "measure", "period_start", "period_end"]),
]

# ---------------------------------------------------------------------------
# 台股基本面（12 個資料集）
# ---------------------------------------------------------------------------

TAIWAN_FUNDAMENTAL: list[DatasetMeta] = [
    DatasetMeta("TaiwanStockFinancialStatements", "綜合損益表", "Free(w/ data_id)", "台股-基本面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "type", "value", "origin_name"]),
    DatasetMeta("TaiwanStockBalanceSheet", "資產負債表", "Free(w/ data_id)", "台股-基本面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "type", "value", "origin_name"]),
    DatasetMeta("TaiwanStockCashFlowsStatement", "現金流量表", "Free(w/ data_id)", "台股-基本面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "type", "value", "origin_name"]),
    DatasetMeta("TaiwanStockDividend", "股利政策", "Free(w/ data_id)", "台股-基本面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "CashEarningsDistribution", "StockEarningsDistribution", "CashExDividendTradingDate"]),
    DatasetMeta("TaiwanStockDividendResult", "除權除息結果", "Free(w/ data_id)", "台股-基本面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "before_price", "after_price", "stock_and_cache_dividend"]),
    DatasetMeta("TaiwanStockMonthRevenue", "月營收", "Free(w/ data_id)", "台股-基本面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "revenue", "revenue_month", "revenue_year"]),
    DatasetMeta("TaiwanStockCapitalReductionReferencePrice", "減資恢復買賣參考價", "Free", "台股-基本面",
                ["start_date", "end_date"],
                ["date", "stock_id", "PostReductionReferencePrice", "ReasonforCapitalReduction"]),
    DatasetMeta("TaiwanStockMarketValue", "股價市值", "Backer", "台股-基本面",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "market_value"]),
    DatasetMeta("TaiwanStockDelisting", "下市櫃", "Free", "台股-基本面",
                ["start_date", "end_date"],
                ["date", "stock_id", "stock_name"]),
    DatasetMeta("TaiwanStockMarketValueWeight", "市值比重", "Backer", "台股-基本面",
                ["start_date", "end_date"],
                ["rank", "stock_id", "stock_name", "weight_per", "date", "type"]),
    DatasetMeta("TaiwanStockSplitPrice", "分割後參考價", "Free", "台股-基本面",
                ["start_date", "end_date"],
                ["date", "stock_id", "type", "before_price", "after_price"]),
    DatasetMeta("TaiwanStockParValueChange", "變更面額恢復買賣參考價", "Free", "台股-基本面",
                ["start_date", "end_date"],
                ["date", "stock_id", "stock_name", "before_close", "after_ref_close"]),
]

# ---------------------------------------------------------------------------
# 台股衍生品（16 個資料集）
# ---------------------------------------------------------------------------

TAIWAN_DERIVATIVE: list[DatasetMeta] = [
    DatasetMeta("TaiwanFutOptDailyInfo", "期貨選擇權總覽", "Free", "台股-衍生品",
                ["dataset"], ["code", "type", "name"]),
    DatasetMeta("TaiwanFuturesDaily", "期貨日成交", "Free(w/ data_id)", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["date", "futures_id", "contract_date", "open", "max", "min", "close", "volume", "settlement_price", "open_interest"]),
    DatasetMeta("TaiwanOptionDaily", "選擇權日成交", "Free(w/ data_id)", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["date", "option_id", "contract_date", "strike_price", "call_put", "open", "max", "min", "close", "volume"]),
    DatasetMeta("TaiwanFuturesTick", "期貨交易明細", "Backer", "台股-衍生品",
                ["data_id", "start_date"],
                ["contract_date", "date", "futures_id", "price", "volume"]),
    DatasetMeta("TaiwanOptionTIck", "選擇權交易明細", "Backer", "台股-衍生品",
                ["data_id", "start_date"],
                ["ExercisePrice", "PutCall", "contract_date", "date", "option_id", "price", "volume"]),
    DatasetMeta("TaiwanFuturesInstitutionalInvestors", "期貨三大法人", "Free(w/ data_id)", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["name", "date", "institutional_investors", "long_deal_volume", "short_deal_volume"]),
    DatasetMeta("TaiwanOptionInstitutionalInvestors", "選擇權三大法人", "Free(w/ data_id)", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["name", "date", "call_put", "institutional_investors", "long_deal_volume", "short_deal_volume"]),
    DatasetMeta("TaiwanFuturesInstitutionalInvestorsAfterHours", "期貨夜盤三大法人", "Backer", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["futures_id", "date", "institutional_investors", "long_deal_volume", "short_deal_volume"]),
    DatasetMeta("TaiwanOptionInstitutionalInvestorsAfterHours", "選擇權夜盤三大法人", "Backer", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["option_id", "date", "call_put", "institutional_investors", "long_deal_volume", "short_deal_volume"]),
    DatasetMeta("TaiwanFuturesDealerTradingVolumeDaily", "期貨各卷商每日交易", "Free", "台股-衍生品",
                ["start_date", "end_date"],
                ["date", "dealer_code", "dealer_name", "futures_id", "volume"]),
    DatasetMeta("TaiwanOptionDealerTradingVolumeDaily", "選擇權各卷商每日交易", "Free", "台股-衍生品",
                ["start_date", "end_date"],
                ["date", "dealer_code", "dealer_name", "option_id", "volume"]),
    DatasetMeta("TaiwanFuturesOpenInterestLargeTraders", "期貨大額交易人未沖銷", "Backer", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["name", "futures_id", "buy_top5_trader_open_interest", "sell_top5_trader_open_interest", "date"]),
    DatasetMeta("TaiwanOptionOpenInterestLargeTraders", "選擇權大額交易人未沖銷", "Backer", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["name", "option_id", "put_call", "buy_top5_trader_open_interest", "sell_top5_trader_open_interest", "date"]),
    DatasetMeta("TaiwanFuturesSpreadTrading", "期貨價差行情", "Backer", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["date", "futures_id", "contract_date", "open", "max", "min", "close"]),
    DatasetMeta("TaiwanFuturesFinalSettlementPrice", "期貨最後結算價", "Backer", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["date", "contract_month", "futures_id", "settlement_price"]),
    DatasetMeta("TaiwanOptionFinalSettlementPrice", "選擇權最後結算價", "Backer", "台股-衍生品",
                ["data_id", "start_date", "end_date"],
                ["date", "contract_month", "option_id", "settlement_price"]),
]

# ---------------------------------------------------------------------------
# 台股即時（4 個資料集，Sponsor）
# ---------------------------------------------------------------------------

TAIWAN_REALTIME: list[DatasetMeta] = [
    DatasetMeta("taiwan_stock_tick_snapshot", "台股即時資訊", "Sponsor", "台股-即時",
                ["data_id"],
                ["close", "high", "low", "open", "volume", "total_volume", "change_price", "change_rate", "date", "stock_id"]),
    DatasetMeta("TaiwanFutOptTickInfo", "期貨選擇權即時總覽", "Sponsor", "台股-即時",
                ["dataset"], ["code", "callput", "date", "name"]),
    DatasetMeta("taiwan_futures_snapshot", "期貨即時資訊", "Sponsor", "台股-即時",
                ["data_id"],
                ["open", "high", "low", "close", "volume", "total_volume", "change_price", "change_rate", "date", "futures_id"]),
    DatasetMeta("taiwan_options_snapshot", "選擇權即時資訊", "Sponsor", "台股-即時",
                ["data_id"],
                ["open", "high", "low", "close", "volume", "total_volume", "change_price", "change_rate", "date", "options_id"]),
]

# ---------------------------------------------------------------------------
# 台股可轉債（4 個資料集）
# ---------------------------------------------------------------------------

TAIWAN_CONVERTIBLE_BOND: list[DatasetMeta] = [
    DatasetMeta("TaiwanStockConvertibleBondInfo", "可轉債總覽", "Backer", "台股-可轉債",
                ["dataset"],
                ["cb_id", "cb_name", "InitialDateOfConversion", "DueDateOfConversion"]),
    DatasetMeta("TaiwanStockConvertibleBondDaily", "可轉債日成交", "Backer", "台股-可轉債",
                ["data_id", "start_date", "end_date"],
                ["cb_id", "cb_name", "close", "open", "max", "min", "volume", "date"]),
    DatasetMeta("TaiwanStockConvertibleBondInstitutionalInvestors", "可轉債三大法人", "Backer", "台股-可轉債",
                ["data_id", "start_date", "end_date"],
                ["ForeignBuy", "ForeignSell", "Investment_TrustBuy", "Investment_TrustSell", "cb_id", "date"]),
    DatasetMeta("TaiwanStockConvertibleBondDailyOverview", "可轉債每日總覽", "Backer", "台股-可轉債",
                ["data_id", "start_date", "end_date"],
                ["cb_id", "ConversionPrice", "IssuanceAmount", "OutstandingAmount", "date"]),
]

# ---------------------------------------------------------------------------
# 台股其他（3 個資料集）
# ---------------------------------------------------------------------------

TAIWAN_OTHERS: list[DatasetMeta] = [
    DatasetMeta("TaiwanStockNews", "相關新聞", "Free", "台股-其他",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "description", "link", "source", "title"]),
    DatasetMeta("TaiwanBusinessIndicator", "景氣對策信號", "Backer", "台股-其他",
                ["start_date", "end_date"],
                ["date", "leading", "coincident", "lagging", "monitoring", "monitoring_color"]),
    DatasetMeta("TaiwanStockIndustryChain", "產業鏈", "Backer", "台股-其他",
                ["data_id", "start_date", "end_date"],
                ["stock_id", "industry", "sub_industry", "date"]),
]

# ---------------------------------------------------------------------------
# 國際股市（9 個資料集）
# ---------------------------------------------------------------------------

INTERNATIONAL: list[DatasetMeta] = [
    DatasetMeta("USStockInfo", "美股總覽", "Free", "國際股市",
                ["dataset"], ["date", "stock_id", "Country", "MarketCap", "stock_name"]),
    DatasetMeta("USStockPrice", "美股股價 daily", "Free", "國際股市",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "Open", "High", "Low", "Close", "Adj_Close", "Volume"]),
    DatasetMeta("USStockPriceMinute", "美股股價 minute", "Backer", "國際股市",
                ["data_id", "start_date"],
                ["date", "stock_id", "open", "high", "low", "close", "volume"]),
    DatasetMeta("UKStockInfo", "英股總覽", "Free", "國際股市",
                ["dataset"], ["date", "stock_id", "Country", "stock_name"]),
    DatasetMeta("UKStockPrice", "英股股價", "Free", "國際股市",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "Open", "High", "Low", "Close", "Adj_Close", "Volume"]),
    DatasetMeta("EuropeStockInfo", "歐股總覽", "Free", "國際股市",
                ["dataset"], ["date", "stock_id", "Market", "stock_name"]),
    DatasetMeta("EuropeStockPrice", "歐股股價", "Free", "國際股市",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "Open", "High", "Low", "Close", "Adj_Close", "Volume"]),
    DatasetMeta("JapanStockInfo", "日股總覽", "Free", "國際股市",
                ["dataset"], ["date", "stock_id", "Exchange", "Sector", "stock_name"]),
    DatasetMeta("JapanStockPrice", "日股股價", "Free", "國際股市",
                ["data_id", "start_date", "end_date"],
                ["date", "stock_id", "Open", "High", "Low", "Close", "Adj_Close", "Volume"]),
]

# ---------------------------------------------------------------------------
# 全球經濟指標（6 個資料集）
# ---------------------------------------------------------------------------

GLOBAL_ECONOMIC: list[DatasetMeta] = [
    DatasetMeta("TaiwanExchangeRate", "外幣匯率", "Free", "全球經濟",
                ["data_id", "start_date", "end_date"],
                ["date", "currency", "cash_buy", "cash_sell", "spot_buy", "spot_sell"],
                note="data_id: USD, EUR, JPY, GBP, CNY, HKD, AUD, CAD, CHF, IDR, KRW, MYR, NZD, PHP, SEK, SGD, THB, VND, ZAR"),
    DatasetMeta("InterestRate", "央行利率", "Free", "全球經濟",
                ["data_id", "start_date", "end_date"],
                ["country", "date", "interest_rate"],
                note="data_id: FED, BOE, RBA, PBOC, BOC, ECB, RBNZ, RBI, CBR, BCB, BOJ, SNB"),
    DatasetMeta("GoldPrice", "黃金價格", "Free", "全球經濟",
                ["start_date", "end_date"],
                ["Price", "date"]),
    DatasetMeta("CrudeOilPrices", "原油價格", "Free", "全球經濟",
                ["data_id", "start_date", "end_date"],
                ["date", "name", "price"],
                note="data_id: WTI, Brent"),
    DatasetMeta("GovernmentBondsYield", "美國國債殖利率", "Free", "全球經濟",
                ["data_id", "start_date", "end_date"],
                ["date", "name", "value"],
                note='data_id: "United States 1-Month" ~ "United States 30-Year"'),
    DatasetMeta("CnnFearGreedIndex", "CNN 恐懼貪婪指數", "Backer", "全球經濟",
                ["start_date", "end_date"],
                ["date", "fear_greed", "fear_greed_emotion"]),
]

# ---------------------------------------------------------------------------
# 彙總：所有資料集
# ---------------------------------------------------------------------------

ALL_DATASETS: list[DatasetMeta] = (
    TAIWAN_TECHNICAL
    + TAIWAN_CHIP
    + TAIWAN_FUNDAMENTAL
    + TAIWAN_DERIVATIVE
    + TAIWAN_REALTIME
    + TAIWAN_CONVERTIBLE_BOND
    + TAIWAN_OTHERS
    + INTERNATIONAL
    + GLOBAL_ECONOMIC
)

# 快速查找字典：dataset name → DatasetMeta
DATASET_MAP: dict[str, DatasetMeta] = {ds.name: ds for ds in ALL_DATASETS}

# 分類查找字典：category → list[DatasetMeta]
CATEGORY_MAP: dict[str, list[DatasetMeta]] = {}
for _ds in ALL_DATASETS:
    CATEGORY_MAP.setdefault(_ds.category, []).append(_ds)


def find_datasets(keyword: str) -> list[DatasetMeta]:
    """以關鍵字搜尋資料集（名稱或描述）。

    Args:
        keyword: 搜尋關鍵字，支援中英文

    Returns:
        符合條件的資料集清單
    """
    keyword_lower = keyword.lower()
    return [
        ds for ds in ALL_DATASETS
        if keyword_lower in ds.name.lower() or keyword_lower in ds.description
    ]
