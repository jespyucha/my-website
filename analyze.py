"""Turn cached prices into the analysis JSON the dashboard reads.

Computes, per ticker, percentage price changes over multiple windows:
  WTD  week-to-date   (since prior week's last close)
  1W   trailing 1 week
  MTD  month-to-date  (since prior month's last close)
  1M   trailing 1 month
  1Q   trailing 3 months
  YTD  year-to-date    (since last close of the prior calendar year)
  1Y   trailing 1 year

Plus context: latest close, 20-day avg volume ratio, and distance from the
52-week high/low. Then ranks biggest gainers/losers per window.
"""
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

import pandas as pd

from tickers import NASDAQ_100

DATA_DIR = Path(__file__).parent / "data"
PRICES_CSV = DATA_DIR / "prices.csv"
OUT_JSON = DATA_DIR / "nasdaq.json"

WINDOWS = ["WTD", "1W", "MTD", "1M", "1Q", "YTD", "1Y"]
# How many top gainers / losers to keep per window for the leaderboards.
TOP_N = 10


def asof(series: pd.Series, target: pd.Timestamp):
    """Last available close on or before `target` (handles weekends/holidays)."""
    s = series.loc[:target]
    return float(s.iloc[-1]) if len(s) else None


def pct(new, old):
    if new is None or old is None or old == 0:
        return None
    return round((new / old - 1) * 100, 2)


def reference_points(dates_index, latest: pd.Timestamp):
    """Return the target reference date for each window."""
    return {
        "WTD": latest - pd.Timedelta(days=latest.weekday() + 1),          # prior week's last day
        "1W": latest - pd.Timedelta(days=7),
        "MTD": latest.replace(day=1) - pd.Timedelta(days=1),              # prior month's last day
        "1M": latest - pd.DateOffset(months=1),
        "1Q": latest - pd.DateOffset(months=3),
        "YTD": latest.replace(month=1, day=1) - pd.Timedelta(days=1),     # last close of prior year
        "1Y": latest - pd.DateOffset(years=1),
    }


def analyze():
    df = pd.read_csv(PRICES_CSV, parse_dates=["date"])
    latest = df["date"].max()
    refs = reference_points(df["date"], latest)

    stocks = []
    for ticker, g in df.groupby("ticker"):
        g = g.sort_values("date")
        closes = pd.Series(g["close"].values, index=g["date"].values)
        vols = pd.Series(g["volume"].values, index=g["date"].values)
        last = float(closes.iloc[-1])

        changes = {w: pct(last, asof(closes, ref)) for w, ref in refs.items()}

        # Volume signal: latest vs trailing 20-day average.
        avg20 = vols.iloc[-21:-1].mean() if len(vols) > 21 else vols.mean()
        vol_ratio = round(float(vols.iloc[-1] / avg20), 2) if avg20 else None

        # 52-week positioning.
        yr = closes.loc[latest - pd.DateOffset(years=1):]
        hi, lo = float(yr.max()), float(yr.min())
        pct_from_high = round((last / hi - 1) * 100, 2) if hi else None
        pct_from_low = round((last / lo - 1) * 100, 2) if lo else None

        stocks.append({
            "ticker": ticker,
            "name": NASDAQ_100.get(ticker, ticker),
            "last": round(last, 2),
            "changes": changes,
            "vol_ratio": vol_ratio,
            "pct_from_high": pct_from_high,
            "pct_from_low": pct_from_low,
        })

    # Leaderboards: biggest gainers / losers per window.
    leaders = {}
    for w in WINDOWS:
        ranked = [s for s in stocks if s["changes"].get(w) is not None]
        ranked.sort(key=lambda s: s["changes"][w], reverse=True)
        leaders[w] = {
            "gainers": [_slim(s, w) for s in ranked[:TOP_N]],
            "losers": [_slim(s, w) for s in ranked[-TOP_N:][::-1]],
        }

    payload = {
        "index": "Nasdaq-100",
        "as_of": latest.date().isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "windows": WINDOWS,
        "constituents": len(stocks),
        "stocks": sorted(stocks, key=lambda s: s["ticker"]),
        "leaders": leaders,
        "movers_note": {},  # filled in by drivers.py
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUT_JSON} — {len(stocks)} stocks, as of {payload['as_of']}")
    return payload


def _slim(s, w):
    return {
        "ticker": s["ticker"],
        "name": s["name"],
        "last": s["last"],
        "change": s["changes"][w],
        "vol_ratio": s["vol_ratio"],
    }


if __name__ == "__main__":
    analyze()
