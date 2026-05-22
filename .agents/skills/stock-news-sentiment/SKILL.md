---
name: stock-news-sentiment
description: Use when the user asks how news is affecting a stock's price trend, wants sentiment analysis of recent headlines, or wants to check if news sentiment aligns with price action.
---

# Stock News Sentiment

Fetches recent news headlines for a stock via Yahoo Finance, classifies sentiment (bullish/bearish/neutral) using VADER, and compares aggregate sentiment against the current technical trend to show alignment or divergence.

## Setup

```bash
pip install yfinance pandas numpy vaderSentiment
```

## Quick Commands

```bash
# Full sentiment + trend alignment
python scripts/news_sentiment.py AAPL

# Analyze multiple tickers
python scripts/news_sentiment.py AAPL MSFT GOOGL

# Custom lookback
python scripts/news_sentiment.py NVDA --days 14 --period 3mo
```

Or from the skill directory:

```bash
python scripts/news_sentiment.py AAPL
```

## Parameters

| Argument | Description | Default |
|----------|-------------|---------|
| `tickers` | One or more stock/ETF tickers (space-separated) | **Required** |
| `--days` | How far back to fetch news (days) | `7` |
| `--period` | Technical data period (5d, 1mo, 3mo, 6mo, 1y) | `1mo` |

## Output Sections

1. **[News Sentiment Summary]** — Total headlines analyzed, bullish/bearish/neutral counts with percentages, average VADER compound score
2. **[Recent Headlines]** — Table of individual headlines with date, title, sentiment label (Bullish/Bearish/Neutral), and compound score
3. **[Trend Context]** — Current price, SMA20/SMA50 trend direction, golden/death cross, RSI, recent returns
4. **[News-Trend Alignment]** — Compares aggregate news sentiment to price trend direction with alignment label (Aligned / Diverging / Mixed)

## Example Output

```text
═══════════════════════════════════════════════════════
  AAPL — News Sentiment (last 7 days)
═══════════════════════════════════════════════════════

[NEWS SENTIMENT SUMMARY]
  Headlines analyzed:    12
  BULL Bullish:               5  (41.7%)
  BEAR Bearish:               3  (25.0%)
  o Neutral:               4  (33.3%)
  Avg Sentiment:         BULL Bullish (+0.120)

[RECENT HEADLINES]
  Date         Title                                              Sentiment        Score
  -----------  -------------------------------------------------  ---------------  -------
  2026-05-21   Apple unveils new M4芯片 with AI capabilities...     BULL Bullish     +0.782
  2026-05-21   Apple faces antitrust probe in EU...                 BEAR Bearish     -0.624
  2026-05-20   Apple shares rise on analyst upgrade...              BULL Bullish     +0.851
  2026-05-19   Apple supply chain concerns mount...                 BEAR Bearish     -0.453
  2026-05-18   Apple services revenue hits new high...              BULL Bullish     +0.321

[TREND CONTEXT]
  Current Price:    $304.99
  SMA(20):          $287.32  ^
  SMA(50):          $269.29  ^
  SMA Cross:        Golden cross
  RSI(14):          57.3     Neutral
  5d Return:        +1.59%
  1mo Return:       +4.20%

[NEWS-TREND ALIGNMENT]
  News Sentiment:   BULL Bullish (+0.120)
  Price Trend:      Bullish
  Alignment:        BULL Aligned — Bullish news supporting uptrend
═══════════════════════════════════════════════════════
```

## Notes

- Sentiment uses VADER, a rule-based model optimized for social/media text — no heavy ML dependencies
- News comes from Yahoo Finance's feed (same as `yfinance.Ticker.news`)
- Trend direction is determined from a composite of SMA crossovers, RSI, and recent returns

## Script Location

```
scripts/news_sentiment.py
```

Run it from the skill directory:

```bash
python scripts/news_sentiment.py AAPL
```
