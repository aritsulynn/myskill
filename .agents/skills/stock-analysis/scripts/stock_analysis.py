#!/usr/bin/env python3
"""
Stock Analysis -- Technical Indicators, Support & Resistance, Patterns

Usage:
    python stock_analysis.py AAPL
    python stock_analysis.py AAPL MSFT GOOGL
    python stock_analysis.py NVDA --period 6mo --interval 1d

Dependencies: pip install yfinance pandas numpy tabulate
"""

import argparse
import os
import sys
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)

# -- Terminal / Unicode detection -------------------------------------------

def _supports_unicode() -> bool:
    """Check if the terminal stdout supports Unicode display."""
    enc = (sys.stdout.encoding or "").upper()
    if enc in ("ASCII", "ANSI_X3.4-1968", "US-ASCII"):
        return False
    if os.name == "nt" and enc in ("CP1252", "CP850", "CP437", "IBM850", "IBM437"):
        return False
    return True


_UNICODE_OK = _supports_unicode()


def _u(uni: str, asc: str) -> str:
    """Return unicode or ASCII fallback based on terminal support."""
    return uni if _UNICODE_OK else asc


# Unicode symbols with ASCII fallbacks
_SYM = {
    "BOX":    _u("\u2550", "="),
    "STAR":   _u("\u2605", "*"),
    "UP":     _u("\u2191", "^"),
    "DOWN":   _u("\u2193", "v"),
    "RIGHT":  _u("\u2192", "->"),
    "WARN":   _u("\u26a0", "!"),
    "BULL":   _u("\U0001f4d7", "BULL"),
    "BEAR":   _u("\U0001f4d5", "BEAR"),
    "BULL2":  _u("\U0001f4d8", "BULL"),
    "CHART":  _u("\U0001f4ca", "CHART"),
    "UP2":    _u("\U0001f4c8", "UP"),
    "DOWN2":  _u("\U0001f4c9", "DOWN"),
    "UP3":    _u("\u2b06", "^"),
    "DOWN3":  _u("\u2b07", "v"),
    "CIRC":   _u("\u26aa", "o"),
    "ERR":    _u("\u2717", "x"),
    "KEY":    _u("\U0001f511", "KEY"),
    "CLIP":   _u("\U0001f4cb", "SUMMARY"),
    "GEQ":    _u("\u2265", ">="),
}


def sym(name: str) -> str:
    """Get terminal-safe symbol by key."""
    return _SYM.get(name, name)


# -- Colour helpers ----------------------------------------------------------

def _c(code: str, text: str) -> str:
    """Wrap text in ANSI colour code if stdout is a TTY."""
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


def _signal_colour(signal: str) -> str:
    """Apply colour to signal symbol."""
    m = {
        sym("BULL"): "green", sym("BEAR"): "red", sym("WARN"): "yellow",
        sym("BULL2"): "cyan", sym("UP3"): "green", sym("DOWN3"): "red",
        sym("CHART"): "blue", sym("UP2"): "green", sym("DOWN2"): "red",
    }
    for symchar, col in m.items():
        if symchar in signal:
            return _c(col, signal)
    return signal


def _arrow(up: bool) -> str:
    return _c("green", sym("UP")) if up else _c("red", sym("DOWN"))


# -- Indicator helpers ------------------------------------------------------

def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = sma(series, window)
    std = series.rolling(window=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    bandwidth = (upper - lower) / mid
    return upper, mid, lower, bandwidth


def macd(series: pd.Series):
    e12 = ema(series, 12)
    e26 = ema(series, 26)
    line = e12 - e26
    signal = ema(line, 9)
    hist = line - signal
    return line, signal, hist


# -- Candlestick pattern detection ------------------------------------------

def detect_candlestick_patterns(df: pd.DataFrame) -> list:
    """Return list of {pattern, date, signal} for recent patterns."""
    o, h, l, c = df["Open"], df["High"], df["Low"], df["Close"]
    body = (c - o).abs()
    upper_wick = h - o.where(c > o, c)
    lower_wick = c.where(c > o, o) - l
    total_range = h - l

    warn = sym("WARN")
    bull = sym("BULL")
    bear = sym("BEAR")

    patterns = []

    for i in range(1, len(df)):
        idx = df.index[i]
        if total_range.iloc[i] == 0:
            continue

        # Doji
        if body.iloc[i] <= 0.03 * total_range.iloc[i] and total_range.iloc[i] > 0:
            patterns.append({"pattern": "Doji", "date": idx, "signal": warn})
            continue

        # Hammer / Hanging Man
        if (lower_wick.iloc[i] >= 2 * body.iloc[i]
                and upper_wick.iloc[i] <= body.iloc[i]
                and body.iloc[i] > 0):
            if c.iloc[i] > o.iloc[i] if body.iloc[i] > 0 else True:
                patterns.append({"pattern": "Hammer", "date": idx, "signal": bull})
            else:
                patterns.append({"pattern": "Hanging Man", "date": idx, "signal": bear})
            continue

        # Shooting Star
        if (upper_wick.iloc[i] >= 2 * body.iloc[i]
                and lower_wick.iloc[i] <= body.iloc[i]
                and body.iloc[i] > 0):
            patterns.append({"pattern": "Shooting Star", "date": idx, "signal": bear})
            continue

        # Bullish / Bearish Engulfing
        if i > 0:
            prev_body = c.iloc[i - 1] - o.iloc[i - 1]
            if prev_body != 0:
                if (c.iloc[i] > o.iloc[i] and prev_body < 0
                        and o.iloc[i] <= c.iloc[i - 1] and c.iloc[i] >= o.iloc[i - 1]):
                    patterns.append({"pattern": "Bullish Engulfing", "date": idx, "signal": bull})
                elif (c.iloc[i] < o.iloc[i] and prev_body > 0
                      and o.iloc[i] >= c.iloc[i - 1] and c.iloc[i] <= o.iloc[i - 1]):
                    patterns.append({"pattern": "Bearish Engulfing", "date": idx, "signal": bear})

        # Morning / Evening Star (3-candle)
        if i >= 2:
            c1, c2, c3 = (c.iloc[i - 2], c.iloc[i - 1], c.iloc[i])
            o1, o2, o3 = (o.iloc[i - 2], o.iloc[i - 1], o.iloc[i])
            body1, body2, body3 = (c1 - o1, c2 - o2, c3 - o3)
            if body1 < 0 and body2 != 0 and body3 > 0:
                if abs(body2) <= abs(body1) * 0.4 and abs(body2) <= abs(body3) * 0.4:
                    if c2 < o1 and c3 > (o1 + c1) / 2:
                        patterns.append({"pattern": "Morning Star", "date": df.index[i], "signal": bull})
            elif body1 > 0 and body2 != 0 and body3 < 0:
                if abs(body2) <= abs(body1) * 0.4 and abs(body2) <= abs(body3) * 0.4:
                    if c2 > o1 and c3 < (o1 + c1) / 2:
                        patterns.append({"pattern": "Evening Star", "date": df.index[i], "signal": bear})

    return patterns[-5:]


# -- Support & Resistance ---------------------------------------------------

def find_support_resistance(df: pd.DataFrame, window: int = 20) -> dict:
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    pivots_high = []
    pivots_low = []

    for i in range(window, len(df) - window):
        if high.iloc[i] == high.iloc[i - window:i + window + 1].max():
            pivots_high.append((df.index[i], high.iloc[i]))
        if low.iloc[i] == low.iloc[i - window:i + window + 1].min():
            pivots_low.append((df.index[i], low.iloc[i]))

    current_price = close.iloc[-1]

    def cluster(levels):
        if not levels:
            return []
        vals = sorted(set(round(v, 2) for _, v in levels))
        groups, cur = [], [vals[0]]
        threshold = current_price * 0.02
        for v in vals[1:]:
            if abs(v - cur[-1]) <= threshold:
                cur.append(v)
            else:
                groups.append(round(np.mean(cur), 2))
                cur = [v]
        groups.append(round(np.mean(cur), 2))
        return groups

    resistance = cluster(pivots_high)
    support = cluster(pivots_low)

    lo = current_price * 0.85
    hi = current_price * 1.15
    resistance = sorted([r for r in resistance if lo <= r <= hi])
    support = sorted([s for s in support if lo <= s <= hi], reverse=True)

    return {"support": support[:3], "resistance": resistance[:3]}


# -- Volume analysis --------------------------------------------------------

def volume_analysis(df: pd.DataFrame, period: int = 20):
    vol = df["Volume"]
    avg = vol.rolling(period).mean()
    last_vol = vol.iloc[-1]
    last_avg = avg.iloc[-1]

    if pd.isna(last_avg) or last_avg == 0:
        return "Insufficient data", 0.0

    ratio = (last_vol / last_avg - 1) * 100

    recent = vol.iloc[-10:]
    up_arrow = sym("UP")
    down_arrow = sym("DOWN")
    right_arrow = sym("RIGHT")

    if recent.is_monotonic_increasing:
        trend_char = up_arrow
    elif recent.is_monotonic_decreasing:
        trend_char = down_arrow
    else:
        trend_char = right_arrow

    trend_col = _c("green", up_arrow) if trend_char == up_arrow else (
        _c("red", down_arrow) if trend_char == down_arrow else _c("dim", right_arrow)
    )

    vol_std = vol.rolling(period).std().iloc[-1]
    anomalous = ""
    if not pd.isna(vol_std) and vol_std > 0:
        z = (last_vol - last_avg) / vol_std
        if abs(z) > 2:
            anomalous = _c("yellow", " " + sym("WARN") + " {0:.1f}sigma {1}".format(abs(z), "surge" if z > 0 else "drop"))

    desc = "{0} {1:+.0f}% vs {2}d avg{3}".format(trend_col, ratio, period, anomalous)
    return desc, ratio


# -- Composite signal -------------------------------------------------------

def composite_signal(df: pd.DataFrame) -> tuple:
    """Score: +1 per bullish, -1 per bearish. Returns (score, label)."""
    score = 0
    close = df["Close"]
    last = close.iloc[-1]

    avg20 = sma(close, 20).iloc[-1]
    if not pd.isna(avg20):
        score += 1 if last > avg20 else -1

    if len(close) >= 50:
        avg50 = sma(close, 50).iloc[-1]
        if not pd.isna(avg50):
            score += 1 if last > avg50 else -1

    if len(close) >= 200:
        avg200 = sma(close, 200).iloc[-1]
        if not pd.isna(avg200):
            score += 1 if last > avg200 else -1

    rsi_val = rsi(close, 14).iloc[-1]
    if not pd.isna(rsi_val):
        if rsi_val > 70:
            score -= 1
        elif rsi_val < 30:
            score += 1

    macd_line, macd_sig, macd_hist = macd(close)
    if not pd.isna(macd_hist.iloc[-1]):
        if macd_hist.iloc[-1] > macd_hist.iloc[-2] and macd_line.iloc[-1] > macd_sig.iloc[-1]:
            score += 1
        elif macd_hist.iloc[-1] < macd_hist.iloc[-2] and macd_line.iloc[-1] < macd_sig.iloc[-1]:
            score -= 1

    recent_high = close.iloc[-20:].max()
    recent_low = close.iloc[-20:].min()
    rng = recent_high - recent_low
    range_pos = (last - recent_low) / rng if rng > 0 else 0.5
    if range_pos > 0.8:
        score += 1
    elif range_pos < 0.2:
        score -= 1

    _, _, _, bw = bollinger(close, 20)
    bw_avg = bw.iloc[-20:].mean()
    if not pd.isna(bw.iloc[-1]) and not pd.isna(bw_avg) and bw_avg > 0:
        if bw.iloc[-1] < bw_avg * 0.5:
            score += 1
        elif bw.iloc[-1] > bw_avg * 1.5:
            score -= 1

    if score >= 3:
        return score, _c("green", sym("BULL") + " BULLISH ({0:+d})".format(score))
    elif score <= -3:
        return score, _c("red", sym("BEAR") + " BEARISH ({0:+d})".format(score))
    elif score >= 1:
        return score, _c("cyan", sym("BULL2") + " SLIGHTLY_BULLISH ({0:+d})".format(score))
    elif score <= -1:
        return score, _c("yellow", sym("WARN") + " SLIGHTLY_BEARISH ({0:+d})".format(score))
    else:
        return score, _c("dim", sym("CIRC") + " NEUTRAL ({0:+d})".format(score))


# -- Price action summary ---------------------------------------------------

def price_action_summary(df: pd.DataFrame) -> list:
    lines = []
    close = df["Close"]

    if len(close) >= 5:
        ret5 = (close.iloc[-1] / close.iloc[-5] - 1) * 100
        col = "green" if ret5 >= 0 else "red"
        lines.append("  5d return: {0}".format(_c(col, "{0:+.2f}%".format(ret5))))

    avg20 = sma(close, 20)
    avg50 = sma(close, 50)
    if not pd.isna(avg20.iloc[-1]) and not pd.isna(avg50.iloc[-1]):
        if avg20.iloc[-1] > avg50.iloc[-1]:
            lines.append("  Short-term {0} (SMA20 > SMA50)".format(_c("green", "BULLISH")))
        else:
            lines.append("  Short-term {0} (SMA20 < SMA50)".format(_c("red", "BEARISH")))

    range10 = (close.iloc[-10:].max() - close.iloc[-10:].min()) / close.iloc[-10:].min()
    if range10 < 0.03:
        lines.append("  {0} Consolidating tight 10d range ({1:.1f}%)".format(
            _c("yellow", sym("WARN")), range10 * 100))
    elif range10 < 0.06:
        lines.append("  {0} Mild range ({1:.1f}%)".format(
            _c("dim", sym("RIGHT")), range10 * 100))

    if close.iloc[-1] >= close.iloc[-20:].max():
        lines.append("  {0} 20-day high!".format(_c("green", sym("STAR"))))
    elif close.iloc[-1] <= close.iloc[-20:].min():
        lines.append("  {0} 20-day low!".format(_c("red", sym("STAR"))))

    return lines


# -- Pretty-print helpers ---------------------------------------------------

def fmt_price(v) -> str:
    if pd.isna(v) or v is None:
        return "--"
    return "{0:.2f}".format(v)


def hdr(label: str, symbol_key: str) -> str:
    """Format section header with symbol."""
    return "  " + _c("bold", "[{0} {1}]".format(sym(symbol_key), label))


# -- Main analysis per ticker -----------------------------------------------

def analyze_ticker(ticker: str, period: str = "1y", interval: str = "1d"):
    """Download data, run all indicators, print report."""

    # Fetch
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
    except Exception as e:
        esym = sym("ERR")
        msg = "{0} Error fetching {1}: {2}".format(esym, ticker, e)
        print("  " + _c("red", msg))
        return

    if df.empty or len(df) < 20:
        wsym = sym("WARN")
        geq = sym("GEQ")
        msg = "{0} Insufficient data for {1} (need {2}20 bars, got {3})".format(wsym, ticker, geq, len(df))
        print("  " + _c("yellow", msg))
        return

    info = {}
    try:
        info = stock.info or {}
    except Exception:
        pass

    name = info.get("longName", info.get("shortName", ticker))
    close = df["Close"]

    # Header
    sep = sym("BOX") * 56
    print()
    print("  " + _c("bold", sep))
    print("  " + _c("bold", ticker.upper()) + " -- {0} ({1} / {2})".format(name, period, interval))
    last_close = close.iloc[-1]
    change = close.iloc[-1] - close.iloc[-2]
    chg_pct = (change / close.iloc[-2]) * 100
    chg_col = _c("green", "+{0:.2f}".format(change)) if change >= 0 else _c("red", "{0:.2f}".format(change))
    print("  " + _c("bold", "Close:") + " ${0:.2f}  ({1}, {2:+.2f}%)".format(last_close, chg_col, chg_pct))
    print("  " + _c("bold", sep))
    print()

    # 1. Candlestick Patterns
    patterns = detect_candlestick_patterns(df)
    print(hdr("CANDLESTICK PATTERNS", "CHART"))
    if patterns:
        print("    {0:<22} {1:<14} Signal".format("Pattern", "Date"))
        print("    {0} {1} {2}".format("-" * 22, "-" * 14, "-" * 8))
        for p in patterns:
            d = p["date"]
            ds = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
            print("    {0:<22} {1:<14} {2}".format(p["pattern"], ds, _signal_colour(p["signal"])))
    else:
        print("    " + _c("dim", "No significant patterns detected"))
    print()

    # 2. Moving Averages
    print(hdr("MOVING AVERAGES", "UP2"))
    for w, label in [(20, "SMA(20)"), (50, "SMA(50)"), (200, "SMA(200)")]:
        if len(close) >= w:
            val = sma(close, w).iloc[-1]
            above = val < last_close
            col = "green" if above else "red"
            di = _c(col, "Price {0} {1}".format("above" if above else "below", label))
            print("    {0}: {1}  {2}  {3}".format(label, _c("bold", fmt_price(val)), _arrow(above), di))
        else:
            print("    {0}: {1}".format(label, _c("dim", "-- insufficient data")))
    if len(close) >= 26:
        e12 = ema(close, 12).iloc[-1]
        e26 = ema(close, 26).iloc[-1]
        golden = e12 > e26
        cross = _c("green", "Golden cross") if golden else _c("red", "Death cross")
        print("    EMA12: {0}  EMA26: {1}  ({2})".format(fmt_price(e12), fmt_price(e26), cross))
    print()

    # 3. Support & Resistance
    sr = find_support_resistance(df)
    print(hdr("SUPPORT & RESISTANCE", "KEY"))
    if sr["resistance"]:
        r_str = ", ".join("${0}".format(r) for r in sr["resistance"])
        print("    {0}  {1}".format(_c("red", "Resistance:"), r_str))
    else:
        print("    {0}  {1}".format(_c("red", "Resistance:"), _c("dim", "none found")))
    if sr["support"]:
        s_str = ", ".join("${0}".format(s) for s in sr["support"])
        print("    {0}     {1}".format(_c("green", "Support:"), s_str))
    else:
        print("    {0}     {1}".format(_c("green", "Support:"), _c("dim", "none found")))

    above = [r for r in sr["resistance"] if r > last_close]
    below = [s for s in sr["support"] if s < last_close]
    near_r = min(above) if above else None
    near_s = max(below) if below else None
    parts = ["Current: ${0:.2f}".format(last_close)]
    if near_r:
        dist = ((near_r - last_close) / last_close) * 100
        parts.append("R${0:.2f} ({1:+.1f}%)".format(near_r, dist))
    if near_s:
        dist = ((near_s - last_close) / last_close) * 100
        parts.append("S${0:.2f} ({1:+.1f}%)".format(near_s, dist))
    print("    " + _c("dim", " | ".join(parts)))
    print()

    # 4. RSI
    rsi_val = rsi(close, 14).iloc[-1]
    print(hdr("RSI(14)", "DOWN2") + " ", end="")
    if not pd.isna(rsi_val):
        if rsi_val > 70:
            status = _c("red", "OVERBOUGHT")
        elif rsi_val < 30:
            status = _c("green", "OVERSOLD")
        else:
            status = _c("dim", "Neutral")
        print(" {0:.1f}  -- {1}".format(rsi_val, status))
    else:
        print(_c("dim", "insufficient data"))

    # 5. Bollinger Bands
    bb_u, bb_m, bb_l, bb_bw = bollinger(close, 20)
    print(hdr("BOLLINGER BANDS", "CHART") + " ", end="")
    if not pd.isna(bb_u.iloc[-1]):
        rng = bb_u.iloc[-1] - bb_l.iloc[-1]
        pos = (last_close - bb_l.iloc[-1]) / rng if rng > 0 else 0.5
        if pos < 0.05:
            pos_desc = _c("green", "Near lower band (oversold)")
        elif pos > 0.95:
            pos_desc = _c("red", "Near upper band (overbought)")
        else:
            pos_desc = _c("dim", "Within bands")
        bbw_val = bb_bw.iloc[-1]
        bbw_avg = bb_bw.iloc[-20:].mean()
        squeeze = ""
        if not pd.isna(bbw_val) and not pd.isna(bbw_avg) and bbw_val < bbw_avg * 0.5:
            squeeze = _c("yellow", " " + sym("WARN") + " Squeeze")
        print("{0} . Bandwidth: {1:.4f}{2}".format(pos_desc, bbw_val, squeeze))
        print("    Upper: ${0}  Mid: ${1}  Lower: ${2}".format(
            fmt_price(bb_u.iloc[-1]), fmt_price(bb_m.iloc[-1]), fmt_price(bb_l.iloc[-1])))
    else:
        print(_c("dim", "insufficient data"))

    # 6. MACD
    macd_line, macd_sig, macd_hist = macd(close)
    print(hdr("MACD", "DOWN2") + " ", end="")
    if not pd.isna(macd_line.iloc[-1]):
        cross = _c("green", "Above signal line") if macd_line.iloc[-1] > macd_sig.iloc[-1] else _c("red", "Below signal line")
        hist_trend = ""
        if not pd.isna(macd_hist.iloc[-2]):
            if macd_hist.iloc[-1] > macd_hist.iloc[-2]:
                hist_trend = " . Histogram {0}".format(_c("green", "rising"))
            else:
                hist_trend = " . Histogram {0}".format(_c("red", "falling"))
        print("{0}{1}".format(cross, hist_trend))
        print("    Line: {0:.4f}  Signal: {1:.4f}  Hist: {2:.4f}".format(
            macd_line.iloc[-1], macd_sig.iloc[-1], macd_hist.iloc[-1]))
    else:
        print(_c("dim", "insufficient data"))

    # 7. Volume
    vol_desc, vol_ratio = volume_analysis(df)
    print(hdr("VOLUME", "CHART") + "  " + vol_desc)

    # 8. Price Action Summary
    print(hdr("PRICE ACTION", "CLIP"))
    for line in price_action_summary(df):
        print(line)

    # 9. Composite Signal
    sc, label = composite_signal(df)
    print()
    print(hdr("COMPOSITE SIGNAL", "CLIP") + "  " + label)
    print("  " + _c("bold", sep))
    print()


# -- CLI --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Stock analysis with technical indicators.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python stock_analysis.py AAPL\n"
               "  python stock_analysis.py AAPL MSFT GOOGL --period 6mo\n"
               "  python stock_analysis.py NVDA --period 1mo --interval 1d",
    )
    parser.add_argument("tickers", nargs="+", help="Stock ticker(s) to analyze")
    parser.add_argument("--period", default="1y",
                        choices=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                        help="Data period (default: 1y)")
    parser.add_argument("--interval", default="1d",
                        choices=["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"],
                        help="Data interval (default: 1d)")
    args = parser.parse_args()

    for ticker in args.tickers:
        analyze_ticker(ticker.upper(), args.period, args.interval)


if __name__ == "__main__":
    main()
