"""Fetch ~13 months of daily OHLCV for the Nasdaq-100 and cache to disk.

Free, end-of-day data via yfinance. We pull a little over a year so that
1-year and YTD windows are always fully covered. Output is a single parquet
(fast) plus we keep it simple with a CSV fallback.
"""
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import pandas as pd
import yfinance as yf

from tickers import TICKERS

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
PRICES_CSV = DATA_DIR / "prices.csv"


def fetch_prices(period: str = "400d") -> pd.DataFrame:
    """Download daily Close + Volume for all tickers. Returns a tidy DataFrame:
    columns = [date, ticker, close, volume].
    """
    print(f"Downloading {len(TICKERS)} tickers ({period}) ...", flush=True)
    raw = yf.download(
        TICKERS,
        period=period,
        interval="1d",
        auto_adjust=True,     # adjust for splits/dividends -> clean % changes
        group_by="ticker",
        threads=True,
        progress=False,
    )

    def extract(source, ticker):
        try:
            sub = source[ticker]
        except (KeyError, TypeError):
            return None
        sub = sub.dropna(subset=["Close"])
        if sub.empty:
            return None
        return pd.DataFrame({
            "date": sub.index,
            "ticker": ticker,
            "close": sub["Close"].values,
            "volume": sub["Volume"].values,
        })

    rows = []
    missing = []
    for t in TICKERS:
        df = extract(raw, t)
        (rows if df is not None else missing).append(df if df is not None else t)

    # Retry pass: transient failures (e.g. yfinance cache "database is locked")
    # often clear on a second, single-ticker attempt.
    if missing:
        print(f"  retrying {len(missing)}: {', '.join(missing)}", flush=True)
        still_missing = []
        for t in missing:
            retry = yf.download(t, period=period, interval="1d",
                                auto_adjust=True, threads=False, progress=False)
            df = extract({t: retry}, t) if not retry.empty else None
            if df is not None:
                rows.append(df)
            else:
                still_missing.append(t)
        missing = still_missing

    if missing:
        print(f"  warning: no data for {len(missing)}: {', '.join(missing)}", flush=True)

    out = pd.concat(rows, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None).dt.normalize()
    out = out.sort_values(["ticker", "date"]).reset_index(drop=True)
    return out


def main():
    df = fetch_prices()
    df.to_csv(PRICES_CSV, index=False)
    n_tickers = df["ticker"].nunique()
    print(f"Saved {len(df):,} rows for {n_tickers} tickers -> {PRICES_CSV}")
    last = df["date"].max().date()
    print(f"Latest trading day in data: {last}")


if __name__ == "__main__":
    main()
