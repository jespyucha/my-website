"""Attach 'why it moved' context to the biggest movers.

For each unique ticker that appears in any window's top gainers/losers, pull the
most recent headlines from Yahoo Finance (via yfinance) and store a compact list
in nasdaq.json under movers_note[ticker]. Runs headless, so it works inside the
scheduled refresh with no manual searching.
"""
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import yfinance as yf

DATA_DIR = Path(__file__).parent / "data"
OUT_JSON = DATA_DIR / "nasdaq.json"

HEADLINES_PER_TICKER = 3


def _url(item):
    c = item.get("content", {}) or {}
    for key in ("canonicalUrl", "clickThroughUrl"):
        v = c.get(key)
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
    return None


def headlines(ticker: str):
    try:
        news = yf.Ticker(ticker).news or []
    except Exception:
        return []
    out = []
    for item in news:
        c = item.get("content", {}) or {}
        title = c.get("title")
        if not title:
            continue
        provider = (c.get("provider") or {}).get("displayName")
        out.append({
            "title": title,
            "publisher": provider,
            "published": c.get("pubDate") or c.get("displayTime"),
            "url": _url(item),
        })
        if len(out) >= HEADLINES_PER_TICKER:
            break
    return out


def collect_mover_tickers(payload):
    seen = []
    for w in payload["windows"]:
        for side in ("gainers", "losers"):
            for s in payload["leaders"][w][side]:
                if s["ticker"] not in seen:
                    seen.append(s["ticker"])
    return seen


def main():
    payload = json.loads(OUT_JSON.read_text())
    tickers = collect_mover_tickers(payload)
    print(f"Fetching headlines for {len(tickers)} movers ...", flush=True)

    notes = {}
    for t in tickers:
        hl = headlines(t)
        if hl:
            notes[t] = hl
    payload["movers_note"] = notes

    OUT_JSON.write_text(json.dumps(payload, indent=2))
    print(f"Attached headlines for {len(notes)}/{len(tickers)} movers -> {OUT_JSON}")


if __name__ == "__main__":
    main()
