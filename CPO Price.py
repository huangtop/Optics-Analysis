
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf


# =========================================================
# 1) 公司與分類
#    - 排除 MACOM
#    - 排除 Sumitomo Electric
#    - 上櫃股票使用 .TWO
#    - 分類與文章 BOM 表對齊：
#      父層分類會包含其子項中的上市公司
#      例如 Optical Engine 會帶入 MLA / PIC / PD / Packaging，
#      ELS 會帶入 CW Laser / DFB Laser。
# =========================================================

COMPANIES = {
    # ===== 海外 =====
    "Broadcom": {
        "ticker": "AVGO",
        "symbol": "AVGO",
        "market": "US",
        "exchange": "NASDAQ",
        "categories": ["Switch ASIC", "Optical Engine", "PIC / SiPh Chip"],
    },
    "NVIDIA": {
        "ticker": "NVDA",
        "symbol": "NVDA",
        "market": "US",
        "exchange": "NASDAQ",
        "categories": ["Switch ASIC"],
    },
    "Marvell Technology": {
        "ticker": "MRVL",
        "symbol": "MRVL",
        "market": "US",
        "exchange": "NASDAQ",
        "categories": ["Switch ASIC", "Optical Engine", "PIC / SiPh Chip"],
    },
    "Coherent": {
        "ticker": "COHR",
        "symbol": "COHR",
        "market": "US",
        "exchange": "NYSE",
        "categories": [
            "Optical Engine",
            "MLA / Micro Optics",
            "PIC / SiPh Chip",
            "Optical Packaging",
            "ELS",
            "CW Laser",
            "DFB Laser",
        ],
    },
    "Lumentum Holdings": {
        "ticker": "LITE",
        "symbol": "LITE",
        "market": "US",
        "exchange": "NASDAQ",
        "categories": [
            "Optical Engine",
            "200G/lane Photodetector / PD",
            "ELS",
            "CW Laser",
            "DFB Laser",
        ],
    },
    "Corning": {
        "ticker": "GLW",
        "symbol": "GLW",
        "market": "US",
        "exchange": "NYSE",
        "categories": ["FAU", "Fiber Array / V-Groove", "Single Mode Fiber"],
    },
    "Amphenol": {
        "ticker": "APH",
        "symbol": "APH",
        "market": "US",
        "exchange": "NYSE",
        "categories": ["MPO Connectors / Cables"],
    },

    # ===== 台灣 =====
    "台積電": {
        "ticker": "2330.TW",
        "symbol": "2330",
        "market": "TW",
        "exchange": "TWSE",
        "categories": ["Optical Engine", "PIC / SiPh Chip", "Optical Packaging"],
    },
    "日月光投控": {
        "ticker": "3711.TW",
        "symbol": "3711",
        "market": "TW",
        "exchange": "TWSE",
        "categories": ["Optical Engine", "Optical Packaging"],
    },
    "大立光": {
        "ticker": "3008.TW",
        "symbol": "3008",
        "market": "TW",
        "exchange": "TWSE",
        "categories": ["Optical Engine", "MLA / Micro Optics", "Metalens", "Prism"],
    },
    "玉晶光": {
        "ticker": "3406.TW",
        "symbol": "3406",
        "market": "TW",
        "exchange": "TWSE",
        "categories": ["Optical Engine", "MLA / Micro Optics", "Prism"],
    },
    "采鈺": {
        "ticker": "6789.TW",
        "symbol": "6789",
        "market": "TW",
        "exchange": "TWSE",
        "categories": ["Optical Engine", "Metalens"],
    },
    "亞光": {
        "ticker": "3019.TW",
        "symbol": "3019",
        "market": "TW",
        "exchange": "TWSE",
        "categories": ["Optical Engine", "Metalens", "Prism"],
    },
    "中揚光": {
        "ticker": "6668.TW",
        "symbol": "6668",
        "market": "TW",
        "exchange": "TWSE",
        "categories": ["Optical Engine", "Metalens"],
    },
    "揚明光": {
        "ticker": "3504.TW",
        "symbol": "3504",
        "market": "TW",
        "exchange": "TWSE",
        "categories": ["Optical Engine", "Prism"],
    },
    "先進光": {
        "ticker": "3362.TWO",
        "symbol": "3362",
        "market": "TW",
        "exchange": "TPEx",
        "categories": ["Optical Engine", "Prism"],
    },
    "上詮": {
        "ticker": "3363.TWO",
        "symbol": "3363",
        "market": "TW",
        "exchange": "TPEx",
        "categories": ["FAU", "Fiber Array / V-Groove", "MPO Connectors / Cables"],
    },
    "波若威": {
        "ticker": "3163.TWO",
        "symbol": "3163",
        "market": "TW",
        "exchange": "TPEx",
        "categories": [
            "FAU",
            "Fiber Array / V-Groove",
            "Shuffle Box",
            "MPO Connectors / Cables",
            "Single Mode Fiber",
        ],
    },
    "貿聯-KY": {
        "ticker": "3665.TW",
        "symbol": "3665",
        "market": "TW",
        "exchange": "TWSE",
        "categories": [
            "FAU",
            "Fiber Array / V-Groove",
            "Shuffle Box",
            "MPO Connectors / Cables",
        ],
    },
    "華星光": {
        "ticker": "4979.TWO",
        "symbol": "4979",
        "market": "TW",
        "exchange": "TPEx",
        "categories": ["ELS", "CW Laser", "DFB Laser"],
    },
    "光聖": {
        "ticker": "6442.TW",
        "symbol": "6442",
        "market": "TW",
        "exchange": "TWSE",
        "categories": ["Single Mode Fiber"],
    },
}


# =========================================================
# 2) 抓最近一年
# =========================================================

END = date.today() + timedelta(days=1)
START = END - timedelta(days=365)

OUTPUT_DIR = Path("public/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "cpo_stock_prices_1y.json"


def download_one(ticker: str) -> pd.Series:
    """下載單一 ticker 的 auto-adjusted Close。"""
    df = yf.download(
        ticker,
        start=START.isoformat(),
        end=END.isoformat(),
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if df.empty:
        return pd.Series(dtype=float)

    if isinstance(df.columns, pd.MultiIndex):
        # yfinance 某些版本即使單 ticker 也可能回 MultiIndex
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

print(f"Downloading {len(COMPANIES)} tickers...")

for company, info in COMPANIES.items():
    ticker = info["ticker"]

    try:
        s = download_one(ticker)
    except Exception as exc:
        print(f"[ERROR] {company} / {ticker}: {exc}")
        failed.append({"company": company, "ticker": ticker, "error": str(exc)})
        continue

    if s.empty:
        print(f"[WARN] No price data: {company} / {ticker}")
        failed.append({"company": company, "ticker": ticker, "error": "no price data"})
        continue

    price_by_company[company] = s
    print(
        f"[OK] {company:18s} {ticker:10s} "
        f"{s.index[0].date()} -> {s.index[-1].date()} "
        f"({len(s)} trading days)"
    )


# =========================================================
# 4) 建立 categories 索引
#    前端選 "CW Laser" 就先查這裡
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