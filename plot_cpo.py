# -*- coding: utf-8 -*-
"""
用 cpo_stock_prices_1y.json 畫同分類股票的一年標準化股價。

範例:
    python3 plot_cpo.py "CW Laser"
    python3 plot_cpo.py "ELS"
    python3 plot_cpo.py "FAU"

輸出:
    public/charts/cpo_CW_Laser_1y.png
"""

import json
import re
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


DATA_PATH = Path("public/data/cpo_stock_prices_1y.json")
OUTPUT_DIR = Path("public/charts")


def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\-]+", "_", text.strip(), flags=re.UNICODE)
    return text.strip("_")


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"找不到 {DATA_PATH}\n"
            '請先執行: python3 "CPO Price.py"'
        )

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_category(category: str):
    data = load_data()

    if category not in data["categories"]:
        available = "\n".join(f"  - {x}" for x in sorted(data["categories"]))
        raise ValueError(
            f'找不到分類: "{category}"\n\n可用分類:\n{available}'
        )

    members = data["categories"][category]
    member_symbols = {m["symbol"] for m in members}

    selected = [
        item for item in data["series"]
        if item["symbol"] in member_symbols
    ]

    if not selected:
        raise ValueError(f"{category} 沒有可畫的股價資料")

    # 每張圖獨立一張 figure
    fig, ax = plt.subplots(figsize=(13, 7))

    for item in selected:
        prices = pd.DataFrame(item["prices"])
        prices["date"] = pd.to_datetime(prices["date"])

        label = f'{item["company"]} ({item["symbol"]})'

        ax.plot(
            prices["date"],
            prices["normalized"],
            linewidth=2,
            label=label,
        )

    ax.axhline(100, linewidth=1, linestyle="--")

    ax.set_title(
        f"CPO {category}｜1Y Normalized Stock Price",
        fontsize=16,
        pad=14,
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Price (Start = 100)")
    ax.grid(True, alpha=0.2)
    ax.legend(frameon=False)
    fig.autofmt_xdate()

    # 圖下注解
    fig.text(
        0.01,
        0.01,
        "Normalized price: each stock's first available trading day = 100. "
        "US and Taiwan stocks may have different trading holidays.",
        fontsize=9,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    out = OUTPUT_DIR / f"cpo_{safe_filename(category)}_1y.png"
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Category: {category}")
    print("[OK] Companies:")
    for item in selected:
        print(
            f'  - {item["company"]} ({item["symbol"]}) '
            f'1Y return: {item["one_year_return_pct"]:+.2f}%'
        )

    print(f"[OK] Saved: {out}")

    # 額外印出分類內 correlation
    corr = data.get("correlations", {}).get(category, [])

    if corr:
        print("\nDaily-return correlation:")
        for x in corr:
            print(
                f'  {x["company_1"]} ↔ {x["company_2"]}: '
                f'{x["correlation"]:.3f} '
                f'({x["common_trading_days"]} common days)'
            )
    else:
        print("\nNo pairwise correlation available.")


def main():
    if len(sys.argv) < 2:
        print(
            '請指定分類，例如:\n'
            '  python3 plot_cpo.py "CW Laser"\n'
            '  python3 plot_cpo.py "ELS"\n'
            '  python3 plot_cpo.py "FAU"'
        )
        sys.exit(1)

    category = sys.argv[1]
    plot_category(category)


if __name__ == "__main__":
    main()
