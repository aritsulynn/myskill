#!/usr/bin/env python3
"""
Stock News Sentiment Analysis — News sentiment vs trend alignment.

Usage:
    python news_sentiment.py AAPL
    python news_sentiment.py AAPL MSFT GOOGL
    python news_sentiment.py NVDA --days 14 --period 3mo

Dependencies: pip install yfinance pandas numpy vaderSentiment
"""

import argparse
import os
import sys
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

warnings.filterwarnings("ignore", category=FutureWarning)

# -- Terminal / Unicode detection -------------------------------------------

def _supports_unicode() -> bool:
    enc = (sys.stdout.encoding or "").upper()
    if enc in ("ASCII", "ANSI_X3.4-1968", "US-ASCII"):
        return False
    if os.name == "nt" and enc in ("CP1252", "CP850", "CP437", "IBM850", "IBM437"):
        return False
    return True

_UNICODE_OK = _supports_unicode()

def _u(uni: str, asc: str) -> str:
    return uni if _UNICODE_OK else asc

_SYM = {
    "BOX":   _u("\u2550", "="),
    "UP":    _u("\u2191", "^"),
    "DOWN":  _u("\u2193", "v"),
    "RIGHT": _u("\u2192", "->"),
    "WARN":  _u("\u26a0", "!"),
    "BULL":  _u("\U0001f4d7", "BULL"),
    "BEAR":  _u("\U0001f4d5", "BEAR"),
    "CHART": _u("\U0001f4ca", "CHART"),
    "NEWS":  _u("\U0001f4f0", "NEWS"),
    "CLIP":  _u("\U0001f4cb", "SUM"),
    "CIRC":  _u("\u26aa", "o"),
    "STAR":  _u("\u2605", "*"),
    "ERR":   _u("\u2717", "x"),
    "TARGET":_u("\U0001f3af", ">"),
}

def sym(name: str) -> str:
    return _SYM.get(name, name)

# -- Colour helpers ----------------------------------------------------------

def _c(code: str, text: str) -> str:
    if not sys.stdout.isatty():
        return text
    codes = {
        "reset":   "\033[0m",
        "bold":    "\033[1m",
        "red":     "\033[91m",
        "green":   "\033[92m",
        "yellow":  "\033[93m",
        "blue":    "\033[94m",
        "magenta": "\033[95m",
        "cyan":    "\033[96m",
        "dim":     "\033[2m",
    }
    cval = codes.get(code, "")
    return f"{cval}{text}{codes['reset']}"

def _arrow(up: bool) -> str:
    return _c("green", sym("UP")) if up else _c("red", sym("DOWN"))

# -- Helpers -----------------------------------------------------------------

def fmt_price(v) -> str:
    if pd.isna(v) or v is None:
        return "--"
    return f"{v:.2f}"

def hdr(label: str, symbol_key: str) -> str:
    return "  " + _c("bold", f"[{sym(symbol_key)} {label}]")

def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()

# -- Sentiment analysis -------------------------------------------------------

_SENTIMENT_ANALYZER = None

def get_sentiment_analyzer():
    global _SENTIMENT_ANALYZER
    if _SENTIMENT_ANALYZER is None:
        _SENTIMENT_ANALYZER = SentimentIntensityAnalyzer()
    return _SENTIMENT_ANALYZER

def classify_sentiment(compound: float) -> tuple:
    if compound >= 0.05:
        label = _c("green", sym("BULL") + " Bullish")
    elif compound <= -0.05:
        label = _c("red", sym("BEAR") + " Bearish")
    else:
        label = _c("dim", sym("CIRC") + " Neutral")
    return label, f"{compound:+.3f}"

def _parse_pubdate(pub_date_str: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(pub_date_str.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def analyze_news_sentiment(ticker: str, days: int = 7) -> tuple:
    stock = yf.Ticker(ticker)
    news_items = stock.news or []

    analyzer = get_sentiment_analyzer()
    now = datetime.now(timezone.utc)
    cutoff_ts = now.timestamp() - days * 86400

    headlines = []
    for item in news_items:
        content = item.get("content") or item
        pub_date_str = content.get("pubDate", "")
        pub_dt = _parse_pubdate(pub_date_str) if pub_date_str else now
        if pub_dt.timestamp() < cutoff_ts:
            continue

        title = (content.get("title") or "").strip()
        summary = (content.get("summary") or "").strip()
        text = f"{title}. {summary}" if summary else title

        vs = analyzer.polarity_scores(text)
        compound = vs["compound"]
        label, score_str = classify_sentiment(compound)

        headlines.append({
            "date": pub_dt.strftime("%Y-%m-%d"),
            "title": title,
            "label": label,
            "score": compound,
            "score_str": score_str,
        })

    headlines.sort(key=lambda h: h["date"], reverse=True)

    total = len(headlines)
    if total == 0:
        return headlines, {"total": 0, "bullish": 0, "bearish": 0, "neutral": 0,
                           "avg_score": 0.0, "avg_label": _c("dim", "No news found")}

    bullish = sum(1 for h in headlines if h["score"] >= 0.05)
    bearish = sum(1 for h in headlines if h["score"] <= -0.05)
    neutral = total - bullish - bearish
    avg_score = float(np.mean([h["score"] for h in headlines]))

    if avg_score >= 0.05:
        avg_label = _c("green", f"{sym('BULL')} Bullish ({avg_score:+.3f})")
    elif avg_score <= -0.05:
        avg_label = _c("red", f"{sym('BEAR')} Bearish ({avg_score:+.3f})")
    else:
        avg_label = _c("dim", f"{sym('CIRC')} Neutral ({avg_score:+.3f})")

    summary = {
        "total": total,
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "avg_score": avg_score,
        "avg_label": avg_label,
    }

    return headlines, summary

def get_trend_context(ticker: str, period: str = "1mo") -> dict:
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if df.empty or len(df) < 2:
        return {"error": "Insufficient price data"}

    close = df["Close"]
    close_flat = close.values.flatten()
    close_clean = pd.Series(close_flat, index=close.index)

    ctx = {"price": float(close_clean.iloc[-1])}

    if len(close_clean) >= 20:
        s20 = sma(close_clean, 20).iloc[-1]
        ctx["sma20"] = float(s20)
        ctx["sma20_above"] = bool(ctx["price"] > s20)
    if len(close_clean) >= 50:
        s50 = sma(close_clean, 50).iloc[-1]
        ctx["sma50"] = float(s50)
        ctx["sma50_above"] = bool(ctx["price"] > s50)
    if len(close_clean) >= 50:
        ctx["sma20_vs_50"] = bool(sma(close_clean, 20).iloc[-1] > sma(close_clean, 50).iloc[-1])

    if len(close_clean) >= 5:
        ctx["ret_5d"] = float((ctx["price"] / close_clean.iloc[-5] - 1) * 100)
    if len(close_clean) >= 21:
        ctx["ret_1mo"] = float((ctx["price"] / close_clean.iloc[-21] - 1) * 100)

    delta = close_clean.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    ctx["rsi"] = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else None

    return ctx

def determine_trend_direction(ctx: dict) -> str:
    signals = []
    if "sma20_vs_50" in ctx:
        signals.append(1 if ctx["sma20_vs_50"] else -1)
    if "ret_5d" in ctx:
        signals.append(1 if ctx["ret_5d"] > 0 else -1)
    if ctx.get("rsi") is not None:
        if ctx["rsi"] > 60:
            signals.append(1)
        elif ctx["rsi"] < 40:
            signals.append(-1)

    if not signals:
        return "Neutral"
    avg = float(np.mean(signals))
    if avg > 0.3:
        return "Bullish"
    elif avg < -0.3:
        return "Bearish"
    return "Neutral"

def alignment_text(sentiment_label: str, trend: str) -> str:
    sent_map = {"Bullish": 1, "Bearish": -1, "Neutral": 0}
    trend_map = {"Bullish": 1, "Bearish": -1, "Neutral": 0}

    s = 0
    for k, v in sent_map.items():
        if k in sentiment_label:
            s = v
            break

    t = trend_map.get(trend, 0)

    if s == 0 and t == 0:
        return _c("dim", f"{sym('CIRC')} Neutral")
    if s == t:
        if s == 1:
            return _c("green", f"{sym('BULL')} Aligned — Bullish news supporting uptrend")
        elif s == -1:
            return _c("red", f"{sym('BEAR')} Aligned — Bearish news reinforcing downtrend")
        return _c("dim", f"{sym('CIRC')} Neutral")
    if s == 1 and t == -1:
        return _c("yellow", f"{sym('WARN')} Diverging — Bullish news but price trending down")
    if s == -1 and t == 1:
        return _c("yellow", f"{sym('WARN')} Diverging — Bearish news but price trending up")
    if s == 0:
        return _c("yellow", f"{sym('WARN')} Neutral news, {trend.lower()} trend")
    if t == 0:
        return _c("yellow", f"{sym('WARN')} Mixed — {sentiment_label} news, neutral trend")

    return _c("dim", f"{sym('WARN')} Mixed signals")


def report_ticker(ticker: str, days: int = 7, period: str = "1mo"):
    sep = sym("BOX") * 56
    print()
    print("  " + _c("bold", sep))
    print("  " + _c("bold", f"{ticker.upper()} — News Sentiment (last {days} days)"))
    print("  " + _c("bold", sep))
    print()

    try:
        headlines, summary = analyze_news_sentiment(ticker, days)
    except Exception as e:
        print(f"  {_c('red', sym('ERR'))} Error fetching news: {e}")
        return

    try:
        ctx = get_trend_context(ticker, period)
    except Exception as e:
        ctx = {"error": str(e)}

    print(hdr("NEWS SENTIMENT SUMMARY", "NEWS"))
    if summary["total"] == 0:
        print(f"  {_c('dim', 'No news articles found for this period')}")
    else:
        bp = (summary["bullish"] / summary["total"]) * 100
        bap = (summary["bearish"] / summary["total"]) * 100
        npct = (summary["neutral"] / summary["total"]) * 100

        print(f"  Headlines analyzed:    {summary['total']}")
        print(f"  {_c('green', sym('BULL'))} Bullish:               {summary['bullish']:>3}  ({bp:5.1f}%)")
        print(f"  {_c('red', sym('BEAR'))} Bearish:                {summary['bearish']:>3}  ({bap:5.1f}%)")
        print(f"  {_c('dim', sym('CIRC'))} Neutral:                {summary['neutral']:>3}  ({npct:5.1f}%)")
        print(f"  Avg Sentiment:         {summary['avg_label']}")
    print()

    print(hdr("RECENT HEADLINES", "NEWS"))
    if headlines:
        print(f"  {'Date':<12} {'Title':<50} {'Sentiment':<16} {'Score':>8}")
        print(f"  {'-'*11}  {'-'*48}  {'-'*14}  {'-'*7}")
        for h in headlines[:15]:
            title = h["title"][:48] + ".." if len(h["title"]) > 50 else h["title"]
            print(f"  {h['date']:<12} {title:<50} {h['label']:<16} {h['score_str']:>8}")
        if len(headlines) > 15:
            print(f"  {_c('dim', f'... and {len(headlines) - 15} more headlines')}")
    else:
        print(f"  {_c('dim', 'No headlines to display')}")
    print()

    print(hdr("TREND CONTEXT", "CHART"))
    if "error" not in ctx:
        price = ctx.get("price", 0)
        print(f"  Current Price:    {_c('bold', f'${price:.2f}')}")

        if "sma20" in ctx:
            print(f"  SMA(20):          ${fmt_price(ctx['sma20'])}  {_arrow(ctx['sma20_above'])}")
        if "sma50" in ctx:
            print(f"  SMA(50):          ${fmt_price(ctx['sma50'])}  {_arrow(ctx['sma50_above'])}")
        if "sma20_vs_50" in ctx:
            cross = _c("green", "Golden cross") if ctx["sma20_vs_50"] else _c("red", "Death cross")
            print(f"  SMA Cross:        {cross}")
        if ctx.get("rsi") is not None:
            r = ctx["rsi"]
            if r > 70:
                rsi_label = _c("red", f"OVERBOUGHT ({r:.1f})")
            elif r < 30:
                rsi_label = _c("green", f"OVERSOLD ({r:.1f})")
            else:
                rsi_label = _c("dim", f"Neutral ({r:.1f})")
            print(f"  RSI(14):          {rsi_label}")
        if "ret_5d" in ctx:
            col = "green" if ctx["ret_5d"] >= 0 else "red"
            ret = ctx["ret_5d"]
            print(f"  5d Return:        {_c(col, f'{ret:+.2f}%')}")
        if "ret_1mo" in ctx:
            col = "green" if ctx["ret_1mo"] >= 0 else "red"
            ret = ctx["ret_1mo"]
            print(f"  1mo Return:       {_c(col, f'{ret:+.2f}%')}")
    else:
        print(f"  {_c('yellow', sym('WARN'))} {ctx['error']}")
    print()

    print(hdr("NEWS-TREND ALIGNMENT", "TARGET"))
    if summary["total"] > 0 and "error" not in ctx:
        trend = determine_trend_direction(ctx)
        trend_colored = (_c("green", trend) if trend == "Bullish"
                         else _c("red", trend) if trend == "Bearish"
                         else _c("dim", trend))

        if summary["avg_score"] >= 0.05:
            sent_label = "Bullish"
        elif summary["avg_score"] <= -0.05:
            sent_label = "Bearish"
        else:
            sent_label = "Neutral"

        align = alignment_text(sent_label, trend)
        print(f"  News Sentiment:   {summary['avg_label']}")
        print(f"  Price Trend:      {trend_colored}")
        print(f"  Alignment:        {align}")
    elif summary["total"] == 0:
        print(f"  {_c('dim', 'No news to compare with trend')}")
    else:
        print(f"  {_c('yellow', sym('WARN'))} Cannot determine trend")
    print()
    print("  " + _c("bold", sep))
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Stock news sentiment analysis with trend alignment.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python news_sentiment.py AAPL\n"
               "  python news_sentiment.py AAPL MSFT GOOGL\n"
               "  python news_sentiment.py NVDA --days 14 --period 3mo",
    )
    parser.add_argument("tickers", nargs="+", help="Stock ticker(s) to analyze")
    parser.add_argument("--days", type=int, default=7,
                        help="How far back to fetch news (days, default: 7)")
    parser.add_argument("--period", default="1mo",
                        choices=["5d", "1mo", "3mo", "6mo", "1y"],
                        help="Technical data lookback period (default: 1mo)")
    args = parser.parse_args()

    for ticker in args.tickers:
        report_ticker(ticker.upper(), args.days, args.period)


if __name__ == "__main__":
    main()
