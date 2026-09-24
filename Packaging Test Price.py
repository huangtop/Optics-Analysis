from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf


# =========================================================
# 1) 公司與分類
#    - 上櫃股票使用 .TWO
#    - 分類與 TGV 文章供應鏈表對齊
#    - "TGV" 為總分類，可直接供 [supply_chain_chart type="tgv" category="TGV"] 使用
# =========================================================

COMPANIES = {
    # ===== 台灣 =====
    "日月光投控": {
        "ticker": "3711.TW", "symbol": "3711", "market": "TW", "exchange": "TWSE",
        "categories": ["Semiconductor Packaging & Test", "Advanced Packaging / OSAT", "Final Test / Package Test", "System Level Test / SLT"],
    },
    "力成": {
        "ticker": "6239.TW", "symbol": "6239", "market": "TW", "exchange": "TWSE",
        "categories": ["Semiconductor Packaging & Test", "Advanced Packaging / OSAT", "HBM Test", "Final Test / Package Test"],
    },
    "致茂": {
        "ticker": "2360.TW", "symbol": "2360", "market": "TW", "exchange": "TWSE",
        "categories": ["Semiconductor Packaging & Test", "Automatic Test Equipment / ATE"],
    },
    "旺矽": {
        "ticker": "6223.TWO", "symbol": "6223", "market": "TW", "exchange": "TPEx",
        "categories": ["Semiconductor Packaging & Test", "Probe / Probe Card / Wafer Probe", "HBM Test"],
    },
    "穎崴": {
        "ticker": "6515.TW", "symbol": "6515", "market": "TW", "exchange": "TWSE",
        "categories": ["Semiconductor Packaging & Test", "Probe / Probe Card / Wafer Probe", "HBM Test", "Test Socket / Test Interface", "Burn-In / Reliability Test"],
    },
    "精測": {
        "ticker": "6510.TWO", "symbol": "6510", "market": "TW", "exchange": "TPEx",
        "categories": ["Semiconductor Packaging & Test", "Probe / Probe Card / Wafer Probe", "HBM Test", "Test Socket / Test Interface"],
    },
    "京元電子": {
        "ticker": "2449.TW", "symbol": "2449", "market": "TW", "exchange": "TWSE",
        "categories": ["Semiconductor Packaging & Test", "HBM Test", "Final Test / Package Test", "Burn-In / Reliability Test", "System Level Test / SLT"],
    },
    "矽格": {
        "ticker": "6257.TW", "symbol": "6257", "market": "TW", "exchange": "TWSE",
        "categories": ["Semiconductor Packaging & Test", "Final Test / Package Test", "Burn-In / Reliability Test", "System Level Test / SLT"],
    },
    "欣銓": {
        "ticker": "3264.TWO", "symbol": "3264", "market": "TW", "exchange": "TPEx",
        "categories": ["Semiconductor Packaging & Test", "Wafer Test / Circuit Probe", "Final Test / Package Test"],
    },
    "南茂": {
        "ticker": "8150.TW", "symbol": "8150", "market": "TW", "exchange": "TWSE",
        "categories": ["Semiconductor Packaging & Test", "Advanced Packaging / OSAT", "Wafer Test / Circuit Probe", "Final Test / Package Test", "Display Driver IC Packaging & Test"],
    },
    "頎邦": {
        "ticker": "6147.TWO", "symbol": "6147", "market": "TW", "exchange": "TPEx",
        "categories": ["Semiconductor Packaging & Test", "Advanced Packaging / OSAT", "Wafer Test / Circuit Probe", "Final Test / Package Test", "Display Driver IC Packaging & Test"],
    },
    "超豐": {
        "ticker": "2441.TW", "symbol": "2441", "market": "TW", "exchange": "TWSE",
        "categories": ["Semiconductor Packaging & Test", "Advanced Packaging / OSAT", "Wafer Test / Circuit Probe", "Final Test / Package Test"],
    },
    "華泰": {
        "ticker": "2329.TW", "symbol": "2329", "market": "TW", "exchange": "TWSE",
        "categories": ["Semiconductor Packaging & Test", "Advanced Packaging / OSAT", "Wafer Test / Circuit Probe", "Final Test / Package Test", "Burn-In / Reliability Test"],
    },

    # ===== 美國 =====
    "Amkor Technology": {
        "ticker": "AMKR", "symbol": "AMKR", "market": "US", "exchange": "NASDAQ",
        "categories": ["Semiconductor Packaging & Test", "Advanced Packaging / OSAT", "Final Test / Package Test", "Burn-In / Reliability Test", "System Level Test / SLT"],
    },
    "ASE Technology": {
        "ticker": "ASX", "symbol": "ASX", "market": "US", "exchange": "NYSE",
        "categories": ["Semiconductor Packaging & Test", "Advanced Packaging / OSAT", "Final Test / Package Test"],
    },
    "Teradyne": {
        "ticker": "TER", "symbol": "TER", "market": "US", "exchange": "NASDAQ",
        "categories": ["Semiconductor Packaging & Test", "Automatic Test Equipment / ATE", "CPO / Silicon Photonics Test"],
    },
    "Cohu": {
        "ticker": "COHU", "symbol": "COHU", "market": "US", "exchange": "NASDAQ",
        "categories": ["Semiconductor Packaging & Test", "Automatic Test Equipment / ATE", "Test Socket / Test Interface", "Burn-In / Reliability Test"],
    },
    "FormFactor": {
        "ticker": "FORM", "symbol": "FORM", "market": "US", "exchange": "NASDAQ",
        "categories": ["Semiconductor Packaging & Test", "Probe / Probe Card / Wafer Probe", "HBM Test"],
    },
    "ChipMOS Technologies ADR": {
        "ticker": "IMOS", "symbol": "IMOS", "market": "US", "exchange": "NASDAQ",
        "categories": ["Semiconductor Packaging & Test", "Advanced Packaging / OSAT", "Wafer Test / Circuit Probe", "Final Test / Package Test", "Display Driver IC Packaging & Test"],
    },
    "Aehr Test Systems": {
        "ticker": "AEHR", "symbol": "AEHR", "market": "US", "exchange": "NASDAQ",
        "categories": ["Semiconductor Packaging & Test", "Wafer Test / Circuit Probe", "Burn-In / Reliability Test", "System Level Test / SLT", "CPO / Silicon Photonics Test"],
    },
}


# =========================================================
# 2) 抓最近一年
# =========================================================

END = date.today() + timedelta(days=1)
START = END - timedelta(days=365)

OUTPUT_DIR = Path("public/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "semiconductor_test_stock_prices_1y.json"


def load_existing_json() -> dict:
    """讀取既有 JSON；若不存在或損壞就回傳空 dict。"""
    if not OUTPUT_PATH.exists():
        return {}

    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"[WARN] Existing JSON unreadable, rebuild full year: {exc}")
        return {}


def existing_series_map(payload: dict) -> dict:
    """把既有 JSON 的 series 轉成 company -> pandas Series。"""
    result = {}

    for item in payload.get("series", []):
        company = item.get("company")
        prices = item.get("prices", [])

        if not company or not prices:
            continue

        values = {}
        for row in prices:
            dt = row.get("date")
            px = row.get("close")
            if dt is None or px is None:
                continue
            values[pd.Timestamp(dt)] = float(px)

        if values:
            s = pd.Series(values, dtype=float).sort_index()
            result[company] = s

    return result


def download_range(ticker: str, start_date: date, end_date: date) -> pd.Series:
    """下載指定日期區間的 auto-adjusted Close；yfinance 的 end 為 exclusive。"""
    if start_date >= end_date:
        return pd.Series(dtype=float)

    df = yf.download(
        ticker,
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if df.empty:
        return pd.Series(dtype=float)

    if isinstance(df.columns, pd.MultiIndex):
        close = df["Close"].iloc[:, 0]
    else:
        close = df["Close"]

    close = close.dropna().sort_index()
    close.name = ticker
    return close


# =========================================================
# 3) 下載
# =========================================================

price_by_company = {}
failed = []

existing_payload = load_existing_json()
existing_by_company = existing_series_map(existing_payload)

print(f"Updating {len(COMPANIES)} tickers...")

for company, info in COMPANIES.items():
    ticker = info["ticker"]
    existing = existing_by_company.get(company, pd.Series(dtype=float))

    if not existing.empty:
        # 先裁成滾動一年，避免舊 JSON 無限變大
        existing = existing[
            (existing.index.date >= START) &
            (existing.index.date < END)
        ]

    # 有既有資料：只從最後一天的下一天開始抓
    # 沒有既有資料：第一次才抓完整一年
    if not existing.empty:
        last_existing = existing.index.max().date()
        fetch_start = max(last_existing + timedelta(days=1), START)
    else:
        fetch_start = START

    try:
        new_data = download_range(ticker, fetch_start, END)
    except Exception as exc:
        print(f"[ERROR] {company} / {ticker}: {exc}")
        # 若更新失敗但舊資料還在，保留舊資料，不整家公司消失
        if not existing.empty:
            price_by_company[company] = existing
            print(
                f"[KEEP] {company:18s} {ticker:10s} "
                f"use existing through {existing.index[-1].date()}"
            )
        failed.append({"company": company, "ticker": ticker, "error": str(exc)})
        continue

    if existing.empty and new_data.empty:
        print(f"[WARN] No price data: {company} / {ticker}")
        failed.append({"company": company, "ticker": ticker, "error": "no price data"})
        continue

    if new_data.empty:
        merged = existing.copy()
        print(
            f"[SKIP] {company:18s} {ticker:10s} "
            f"already up to date through {merged.index[-1].date()}"
        )
    else:
        merged = pd.concat([existing, new_data])
        merged = merged[~merged.index.duplicated(keep="last")].sort_index()
        merged = merged[
            (merged.index.date >= START) &
            (merged.index.date < END)
        ]

        if existing.empty:
            print(
                f"[INIT] {company:18s} {ticker:10s} "
                f"{merged.index[0].date()} -> {merged.index[-1].date()} "
                f"({len(merged)} trading days)"
            )
        else:
            print(
                f"[ADD]  {company:18s} {ticker:10s} "
                f"{new_data.index[0].date()} -> {new_data.index[-1].date()} "
                f"(+{len(new_data)} rows, total {len(merged)})"
            )

    price_by_company[company] = merged


# =========================================================
# 4) 建立 categories 索引
#    前端可用 "Semiconductor Packaging & Test" 顯示全部概念股，或選各測試／封裝分類
# =========================================================

category_map = {}

for company, info in COMPANIES.items():
    if company not in price_by_company:
        continue

    member = {
        "company": company,
        "symbol": info["symbol"],
        "ticker": info["ticker"],
        "market": info["market"],
        "exchange": info["exchange"],
    }

    for category in info["categories"]:
        category_map.setdefault(category, []).append(member)


# =========================================================
# 5) 建立每家公司完整時間序列
# =========================================================

series = []
company_meta = []

for company, info in COMPANIES.items():
    if company not in price_by_company:
        continue

    s = price_by_company[company]
    normalized = s / s.iloc[0] * 100
    daily_return = s.pct_change(fill_method=None) * 100

    prices = []

    for dt, px in s.items():
        dr = daily_return.loc[dt]

        prices.append({
            "date": dt.strftime("%Y-%m-%d"),
            "close": round(float(px), 4),
            "normalized": round(float(normalized.loc[dt]), 4),
            "daily_return_pct": None if pd.isna(dr) else round(float(dr), 4),
        })

    first = float(s.iloc[0])
    last = float(s.iloc[-1])

    company_meta.append({
        "company": company,
        "symbol": info["symbol"],
        "ticker": info["ticker"],
        "market": info["market"],
        "exchange": info["exchange"],
        "categories": info["categories"],
    })

    series.append({
        "company": company,
        "symbol": info["symbol"],
        "ticker": info["ticker"],
        "market": info["market"],
        "exchange": info["exchange"],
        "categories": info["categories"],
        "start_date": prices[0]["date"],
        "end_date": prices[-1]["date"],
        "start_price": round(first, 4),
        "latest_price": round(last, 4),
        "one_year_return_pct": round((last / first - 1) * 100, 2),
        "prices": prices,
    })


# =========================================================
# 6) 分類內 pairwise correlation
#    使用兩家公司「共同有交易」的日期
# =========================================================

correlations = {}

for category, members in category_map.items():
    companies = [m["company"] for m in members]

    if len(companies) < 2:
        correlations[category] = []
        continue

    # 各市場休市日不同，不 forward fill
    tmp = pd.concat(
        {company: price_by_company[company] for company in companies},
        axis=1,
    )

    ret = tmp.pct_change(fill_method=None)

    pairs = []

    for i in range(len(companies)):
        for j in range(i + 1, len(companies)):
            c1 = companies[i]
            c2 = companies[j]

            pair = ret[[c1, c2]].dropna()

            if len(pair) < 20:
                continue

            corr = pair[c1].corr(pair[c2])

            if pd.isna(corr):
                continue

            pairs.append({
                "company_1": c1,
                "symbol_1": COMPANIES[c1]["symbol"],
                "market_1": COMPANIES[c1]["market"],
                "company_2": c2,
                "symbol_2": COMPANIES[c2]["symbol"],
                "market_2": COMPANIES[c2]["market"],
                "correlation": round(float(corr), 4),
                "common_trading_days": int(len(pair)),
            })

    correlations[category] = pairs


# =========================================================
# 7) 最終 JSON
# =========================================================

payload = {
    "generated_at": pd.Timestamp.now(tz="Asia/Taipei").isoformat(),

    "period": {
        "start": START.isoformat(),
        "end": (END - timedelta(days=1)).isoformat(),
    },

    "normalization": {
        "method": "first available trading day = 100",
        "price_type": "auto-adjusted close",
    },

    # 公司基本資料
    "companies": company_meta,

    # category -> 公司清單
    "categories": category_map,

    # 公司 -> 每日價格序列
    "series": series,

    # category -> 公司兩兩每日報酬相關係數
    "correlations": correlations,

    # 若抓取失敗，可在前端或 log 顯示
    "failed": failed,
}


with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

print()
print("=" * 60)
print(f"Saved: {OUTPUT_PATH}")
print(f"Companies: {len(series)}")
print(f"Categories: {len(category_map)}")
print(f"Failed: {len(failed)}")
print("=" * 60)

if failed:
    for item in failed:
        print(f"  - {item['company']} / {item['ticker']}: {item['error']}")