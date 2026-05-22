---
name: fundamental-analysis
description: Analyze stocks using fundamental data — revenue, earnings, valuation ratios, profitability, balance sheet health, cash flow, and growth estimates. Use for any stock or ETF fundamental analysis request.
---

# Fundamental Analysis

Performs comprehensive fundamental analysis on any stock/ETF using Yahoo Finance data — revenue trends, earnings quality, valuation multiples, profitability, and financial health.

## Setup

```bash
pip install yfinance pandas numpy
```

## Quick Commands

```bash
# Full fundamental analysis
python scripts/fundamental_analysis.py AAPL

# Analyze multiple tickers
python scripts/fundamental_analysis.py AAPL MSFT GOOGL

# Trailing Twelve Months (default is annual)
python scripts/fundamental_analysis.py NVDA --ttm

# Quarterly view
python scripts/fundamental_analysis.py AAPL --quarterly
```

Or from the skill directory:

```bash
python scripts/fundamental_analysis.py AAPL
```

## Parameters

| Argument | Description | Default |
|----------|-------------|---------|
| `tickers` | One or more stock tickers (space-separated) | **Required** |
| `--ttm` | Use trailing-twelve-months financials | `False` |
| `--quarterly` | Use quarterly instead of annual financials | `False` |

## Output Sections

1. **Revenue** — Annual revenue in billions, YoY growth rate, revenue per share
2. **Earnings** — Net income, diluted EPS, EPS growth, net profit margin
3. **Profitability** — Gross margin, operating margin, EBITDA margin, return on equity (ROE)
4. **Valuation** — P/E (trailing & forward), P/S, P/B, EV/EBITDA, PEG ratio, dividend yield
5. **Revenue Growth** — 5-year revenue CAGR (if enough data)
6. **Earnings Growth** — 5-year earnings CAGR (if enough data)
7. **Growth Estimates** — Analyst estimates for next quarter and next year
8. **Financial Health** — Current ratio, debt/equity, debt/revenue, free cash flow, FCF yield
9. **Composite Score** — Weighted fundamental rating from all metrics

## Example Output

```text
═══════════════════════════════════════════════════════
  AAPL — Apple Inc.
═══════════════════════════════════════════════════════

[REVENUE]
  Latest Annual:   $391.04B
  Revenue / Share: $25.84
  YoY Growth:      +0.2%

[EARNINGS]
  Net Income:      $93.74B
  Diluted EPS:     $6.16
  EPS Growth:      -2.4%
  Net Profit Margin: 23.9%

[PROFITABILITY]
  Gross Margin:    46.2%
  Operating Margin: 31.4%
  EBITDA Margin:   34.7%
  ROE:             173.5%

[VALUATION]
  Trailing P/E:    33.9
  Forward P/E:     27.4
  P/S (TTM):       8.1
  P/B:             57.9
  EV/EBITDA:       25.5
  PEG Ratio:       2.23

[REVENUE GROWTH]
  5y CAGR: +9.3%  (2021 → 2025)

[EARNINGS GROWTH]
  5y CAGR: +13.2%  (2021 → 2025)

[GROWTH ESTIMATES]
  Next Quarter Revenue: $94.8B  (+6.2%)
  Current Year Revenue: $402.3B (+10.1%)
  Next Quarter EPS:     $1.53   (+9.5%)

[FINANCIAL HEALTH]
  Current Ratio:     0.97
  Debt / Equity:     156.7%
  Debt / Revenue:    33.9%
  Free Cash Flow:    $108.6B
  FCF Yield:         3.7%

[COMPOSITE]  SCORE: 75/100 — Good fundamentals
═══════════════════════════════════════════════════════
```

## Script Location

The script lives at:

```
scripts/fundamental_analysis.py
```

Run it from the skill directory:

```bash
python scripts/fundamental_analysis.py AAPL
```
