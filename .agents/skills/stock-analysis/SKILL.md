---
name: stock-analysis
description: Analyze stocks with technical indicators including support/resistance levels, RSI, MACD, Bollinger Bands, moving averages, volume analysis, and candlestick patterns. Use for any stock or ETF analysis request.
---

# Stock Analysis

Performs comprehensive technical analysis on any stock/ETF using Yahoo Finance data.

## Setup

Run once before first use:

```bash
cd scripts && pip install yfinance pandas numpy
```

> **Note:** If you don't have Python 3.8+, install it from [python.org](https://python.org) or run `winget install Python.Python.3.12`.

## Quick Commands

```bash
# Full analysis (candlestick patterns, support/resistance, indicators, volume)
python scripts/stock_analysis.py AAPL

# Analyze multiple tickers
python scripts/stock_analysis.py AAPL MSFT GOOGL

# Custom period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
python scripts/stock_analysis.py AAPL --period 6mo

# Custom interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
python scripts/stock_analysis.py NVDA --period 1mo --interval 1d
```

Or from the skill directory:

```bash
python scripts/stock_analysis.py AAPL
```

## Parameters

| Argument | Description | Default |
|----------|-------------|---------|
| `tickers` | One or more stock/ETF tickers (space-separated) | **Required** |
| `--period` | Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max) | `1y` |
| `--interval` | Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo) | `1d` |

## Output Sections

For each ticker the script prints:

1. **[Candlestick Patterns]** — Doji, Engulfing, Hammer, Shooting Star, Morning/Evening Star
2. **[Moving Averages]** — SMA20, SMA50, SMA200, EMA12, EMA26 with trend direction and golden/death cross
3. **[Support & Resistance]** — Key pivot-based price levels with distance from current price
4. **[RSI(14)]** — Overbought, oversold, or neutral with numeric value
5. **[Bollinger Bands]** — Position within bands, bandwidth, squeeze detection
6. **[MACD]** — Line, signal, histogram, crossovers, and histogram trend
7. **[Volume]** — Trend direction, % difference from average, anomalous volume alerts
8. **[Price Action]** — Short-term return, SMA crossover trend, consolidation/range detection
9. **[Composite Signal]** — Weighted bullish/bearish/neutral score from all indicators

## Example Output (Unicode Terminal)

```text
═══════════════════════════════════════════════════════
  AAPL -- Apple Inc. (1y / 1d)
═══════════════════════════════════════════════════════

[\U0001f4ca CANDLESTICK PATTERNS]
    Pattern                Date           Signal
    ---------------------- -------------- --------
    Bullish Engulfing      2026-04-15     \U0001f4d7
    Doji                   2026-05-01     ⚠

[\U0001f4c8 MOVING AVERAGES]
    SMA(20): 287.32  ↑  Price above SMA(20)
    SMA(50): 269.29  ↑  Price above SMA(50)
    SMA(200): -- insufficient data
    EMA12: 295.48  EMA26: 285.80  (Golden cross)

[\U0001f511 SUPPORT & RESISTANCE]
    Resistance:  312.54
    Support:     262.10
    Current: $304.99 | R$312.54 (+2.5%)

[\U0001f4c9 RSI(14)]  57.3  -- Neutral
[\U0001f4ca BOLLINGER BANDS] Within bands . Bandwidth: 0.1755
[\U0001f4c9 MACD] Above signal line . Histogram rising
[\U0001f4ca VOLUME]  ↑ +15% vs 20d avg  ! 2.1sigma surge
[\U0001f4cb PRICE ACTION]
  5d return: +1.59%
  Short-term BULLISH (SMA20 > SMA50)
  ★ 20-day high!

[\U0001f4cb COMPOSITE SIGNAL]  \U0001f4d7 BULLISH (+3)
═══════════════════════════════════════════════════════
```

On Windows consoles (cp1252/cp850), emoji and unicode box-drawing characters
are automatically replaced with ASCII equivalents.

## Script Location

The analysis script lives at:

```
scripts/stock_analysis.py
```

Run it from the skill directory:

```bash
python scripts/stock_analysis.py AAPL
```
