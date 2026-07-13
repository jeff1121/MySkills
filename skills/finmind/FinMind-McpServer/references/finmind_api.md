# FinMind API 參考文件

## 概覽

FinMind 是一個金融數據 API 平台，提供台灣股市、國際股市、期貨選擇權、全球經濟指標等資料。

## 認證

使用環境變數 `FINMIND_TOKEN` 作為 API Token。

取得方式：到 [https://finmindtrade.com/](https://finmindtrade.com/) 註冊並登入。

## API 基礎網址

`https://api.finmindtrade.com/api/v4`

## 端點

### GET /data — 查詢資料集

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| dataset | str | ✅ | 資料集名稱 |
| data_id | str | ❌ | 資料識別碼（如股票代碼） |
| start_date | str | ❌ | 開始日期 (YYYY-MM-DD) |
| end_date | str | ❌ | 結束日期 (YYYY-MM-DD) |

Header: `Authorization: Bearer {token}`

### GET /datalist — 列出可用 data_id

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| dataset | str | ✅ | 資料集名稱 |

### GET /translation — 欄位名稱中英對照

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| dataset | str | ✅ | 資料集名稱 |

## Rate Limits

- 有 Token：600 次/小時
- 無 Token：300 次/小時
- 超限回傳 HTTP 402
- 查詢使用量：`GET https://api.web.finmindtrade.com/v2/user_info`（Bearer token），回傳 `user_count` 與 `api_request_limit`

## 會員等級

| 等級 | 說明 |
|------|------|
| **Free** | 基本資料集，600 req/hour |
| **Backer** | 更多資料集，更高上限 |
| **Sponsor** | 全部資料集，含即時、分K、分點資料 |

## 資料集總覽

### 台股技術面（20 個）

| 資料集 | 說明 | 等級 | 參數 | 關鍵欄位 |
|--------|------|------|------|---------|
| TaiwanStockInfo | 台股總覽 | Free | dataset | industry_category, stock_id, stock_name, type, date |
| TaiwanStockInfoWithWarrant | 台股總覽含權證 | Free | dataset | industry_category, stock_id, stock_name, type, date |
| TaiwanStockTradingDate | 台股交易日 | Free | dataset | date |
| TaiwanStockPrice | 股價日成交資訊 | Free(w/ data_id) | data_id, start_date, end_date | date, stock_id, Trading_Volume, Trading_money, open, max, min, close, spread, Trading_turnover |
| TaiwanStockPriceAdj | 還原股價 | Free(w/ data_id) | data_id, start_date, end_date | 同 TaiwanStockPrice |
| TaiwanStockPriceTick | 歷史逐筆交易 | Backer | data_id, start_date（單日） | date, stock_id, deal_price, volume, Time, TickType |
| TaiwanStockPER | PER/PBR | Free | data_id, start_date, end_date | date, stock_id, dividend_yield, PER, PBR |
| TaiwanStockStatisticsOfOrderBookAndTrade | 每5秒委託成交統計 | Free | start_date（單日） | Time, TotalBuyOrder, TotalBuyVolume, TotalSellOrder, TotalSellVolume |
| TaiwanVariousIndicators5Seconds | 台股加權指數 | Free | start_date（單日） | date, TAIEX |
| TaiwanStockDayTrading | 當沖交易 | Free(w/ data_id) | data_id, start_date, end_date | stock_id, date, BuyAfterSale, Volume, BuyAmount, SellAmount |
| TaiwanStockTotalReturnIndex | 報酬指數 | Free | data_id(TAIEX/TPEx), start_date, end_date | price, stock_id, date |
| TaiwanStock10Year | 十年線 | Backer | data_id, start_date, end_date | date, stock_id, close |
| TaiwanStockKBar | 分K資料 | Sponsor | data_id, start_date（單日） | date, minute, stock_id, open, high, low, close, volume |
| TaiwanStockWeekPrice | 週K | Backer | data_id, start_date, end_date | stock_id, yweek, max, min, trading_volume, close |
| TaiwanStockMonthPrice | 月K | Backer | data_id, start_date, end_date | stock_id, ymonth, max, min, trading_volume, close |
| TaiwanStockEvery5SecondsIndex | 每5秒指數統計 | Backer | start_date（單日） | date, time, stock_id, price, kind |
| TaiwanStockSuspended | 暫停交易公告 | Backer | start_date, end_date | stock_id, date, suspension_time |
| TaiwanStockDayTradingSuspension | 暫停先賣後買當沖 | Backer | start_date, end_date | stock_id, date, reason |
| TaiwanStockPriceLimit | 每日漲跌停價 | Free(w/ data_id) | data_id, start_date | date, stock_id, reference_price, limit_up, limit_down |

### 台股籌碼面（16 個）

| 資料集 | 說明 | 等級 |
|--------|------|------|
| TaiwanStockMarginPurchaseShortSale | 融資融劵 | Free(w/ data_id) |
| TaiwanStockTotalMarginPurchaseShortSale | 整體市場融資融劵 | Free |
| TaiwanStockInstitutionalInvestorsBuySell | 三大法人買賣 | Free(w/ data_id) |
| TaiwanStockTotalInstitutionalInvestors | 整體三大法人 | Free |
| TaiwanStockShareholding | 外資持股 | Free(w/ data_id) |
| TaiwanStockHoldingSharesPer | 股權持股分級 | Backer |
| TaiwanStockSecuritiesLending | 借券成交 | Free(w/ data_id) |
| TaiwanStockMarginShortSaleSuspension | 暫停融券賣出 | Free(w/ data_id) |
| TaiwanDailyShortSaleBalances | 信用額度總量管制餘額 | Free(w/ data_id) |
| TaiwanSecuritiesTraderInfo | 證券商資訊 | Free |
| TaiwanStockTradingDailyReport | 分點資料 | Sponsor |
| TaiwanStockWarrantTradingDailyReport | 權證分點資料 | Sponsor |
| TaiwanstockGovernmentBankBuySell | 八大行庫買賣 | Sponsor |
| TaiwanTotalExchangeMarginMaintenance | 大盤融資維持率 | Backer |
| TaiwanStockTradingDailyReportSecIdAgg | 卷商分點統計 | Sponsor |
| TaiwanStockDispositionSecuritiesPeriod | 處置有價證券 | Backer |

### 台股基本面（12 個）

| 資料集 | 說明 | 等級 |
|--------|------|------|
| TaiwanStockFinancialStatements | 綜合損益表 | Free(w/ data_id) |
| TaiwanStockBalanceSheet | 資產負債表 | Free(w/ data_id) |
| TaiwanStockCashFlowsStatement | 現金流量表 | Free(w/ data_id) |
| TaiwanStockDividend | 股利政策 | Free(w/ data_id) |
| TaiwanStockDividendResult | 除權除息結果 | Free(w/ data_id) |
| TaiwanStockMonthRevenue | 月營收 | Free(w/ data_id) |
| TaiwanStockCapitalReductionReferencePrice | 減資恢復買賣參考價 | Free |
| TaiwanStockMarketValue | 股價市值 | Backer |
| TaiwanStockDelisting | 下市櫃 | Free |
| TaiwanStockMarketValueWeight | 市值比重 | Backer |
| TaiwanStockSplitPrice | 分割後參考價 | Free |
| TaiwanStockParValueChange | 變更面額恢復買賣參考價 | Free |

### 衍生品（16 個）

| 資料集 | 說明 | 等級 |
|--------|------|------|
| TaiwanFutOptDailyInfo | 期貨選擇權總覽 | Free |
| TaiwanFuturesDaily | 期貨日成交 | Free(w/ data_id) |
| TaiwanOptionDaily | 選擇權日成交 | Free(w/ data_id) |
| TaiwanFuturesTick | 期貨交易明細 | Backer |
| TaiwanOptionTIck | 選擇權交易明細 | Backer |
| TaiwanFuturesInstitutionalInvestors | 期貨三大法人 | Free(w/ data_id) |
| TaiwanOptionInstitutionalInvestors | 選擇權三大法人 | Free(w/ data_id) |
| TaiwanFuturesInstitutionalInvestorsAfterHours | 期貨夜盤三大法人 | Backer |
| TaiwanOptionInstitutionalInvestorsAfterHours | 選擇權夜盤三大法人 | Backer |
| TaiwanFuturesDealerTradingVolumeDaily | 期貨各卷商每日交易 | Free |
| TaiwanOptionDealerTradingVolumeDaily | 選擇權各卷商每日交易 | Free |
| TaiwanFuturesOpenInterestLargeTraders | 期貨大額交易人未沖銷 | Backer |
| TaiwanOptionOpenInterestLargeTraders | 選擇權大額交易人未沖銷 | Backer |
| TaiwanFuturesSpreadTrading | 期貨價差行情 | Backer |
| TaiwanFuturesFinalSettlementPrice | 期貨最後結算價 | Backer |
| TaiwanOptionFinalSettlementPrice | 選擇權最後結算價 | Backer |

### 即時資訊（4 個，Sponsor 專用）

| 資料集 | 說明 |
|--------|------|
| taiwan_stock_tick_snapshot | 台股即時資訊 |
| TaiwanFutOptTickInfo | 期貨選擇權即時總覽 |
| taiwan_futures_snapshot | 期貨即時資訊 |
| taiwan_options_snapshot | 選擇權即時資訊 |

### 國際股市（9 個）

| 資料集 | 說明 | 等級 |
|--------|------|------|
| USStockInfo | 美股總覽 | Free |
| USStockPrice | 美股股價 daily | Free |
| USStockPriceMinute | 美股股價 minute | Backer |
| UKStockInfo | 英股總覽 | Free |
| UKStockPrice | 英股股價 | Free |
| EuropeStockInfo | 歐股總覽 | Free |
| EuropeStockPrice | 歐股股價 | Free |
| JapanStockInfo | 日股總覽 | Free |
| JapanStockPrice | 日股股價 | Free |

### 全球經濟指標（6 個）

| 資料集 | 說明 | 等級 | data_id |
|--------|------|------|---------|
| TaiwanExchangeRate | 外幣匯率 | Free | USD, EUR, JPY, GBP, CNY... |
| InterestRate | 央行利率 | Free | FED, BOE, RBA, PBOC... |
| GoldPrice | 黃金價格 | Free | — |
| CrudeOilPrices | 原油價格 | Free | WTI, Brent |
| GovernmentBondsYield | 美國國債殖利率 | Free | "United States 1-Month" ~ "30-Year" |
| CnnFearGreedIndex | CNN 恐懼貪婪指數 | Backer | — |

## 常用股票代碼

| 代碼 | 名稱 | 說明 |
|------|------|------|
| 2330 | 台積電 | TSMC |
| 2317 | 鴻海 | Foxconn |
| 2454 | 聯發科 | MediaTek |
| 2882 | 國泰金 | Cathay Financial |
| 2881 | 富邦金 | Fubon Financial |
| 0050 | 元大台灣50 ETF | Taiwan Top 50 ETF |

## 注意事項

- 標記「單日查詢」的資料集只接受 start_date（不接受 end_date 範圍）
- 標記 `Free(w/ data_id)` 的資料集在指定 data_id 時免費，省略 data_id 查全部則需要 Backer/Sponsor
- 日期格式統一為 `YYYY-MM-DD`
