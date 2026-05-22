#!/usr/bin/env python3
"""
Fundamental Analysis — Revenue, Earnings, Valuation, Financial Health

Usage:
    python fundamental_analysis.py AAPL
    python fundamental_analysis.py AAPL MSFT GOOGL
    python fundamental_analysis.py NVDA --ttm
    python fundamental_analysis.py AAPL --quarterly

Dependencies: pip install yfinance pandas numpy
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
    "STAR":  _u("\u2605", "*"),
    "REV":   _u("\U0001f4b0", "$"),
    "PROF":  _u("\U0001f4c8", "+"),
    "SCALE": _u("\u2696", "#"),
    "HEART": _u("\U0001f4ca", "~"),
    "CHART": _u("\U0001f4ca", "#"),
    "CLIP":  _u("\U0001f4cb", "*"),
    "CIRC":  _u("\u26aa", "o"),
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
    return "{0}{1}{2}".format(cval, text, codes["reset"])

def _pct_col(val: float) -> str:
    """Green for positive, red for negative."""
    if val is None or np.isnan(val):
        return _c("dim", "N/A")
    col = "green" if val >= 0 else "red"
    return _c(col, "{0:+.1f}%".format(val))

def _fmt_b(v: float) -> str:
    """Format value as billions."""
    if v is None or np.isnan(v):
        return "N/A"
    return "${0:,.2f}B".format(v / 1e9)

def _fmt_bn(v: float) -> str:
    """Format as billions without $."""
    if v is None or np.isnan(v):
        return "N/A"
    return "{0:,.2f}B".format(v / 1e9)

def _fmt(v, decimals=2, prefix="$") -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    if isinstance(v, (int, float)):
        return "{0}{1:.{2}f}".format(prefix, v, decimals)
    return str(v)

def _hdr(label: str, symbol_key: str) -> str:
    return _c("bold", "[{0} {1}]".format(sym(symbol_key), label))

# -- Safe extraction helpers ------------------------------------------------

def _safe_loc(df: pd.DataFrame, label: str) -> float | None:
    """Get a value from a DataFrame by row label, return None if missing."""
    try:
        val = df.loc[label]
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        return float(val)
    except (KeyError, IndexError, TypeError, ValueError):
        return None

def _safe_val(series: pd.Series | list, idx: int = 0) -> float | None:
    try:
        val = series.iloc[idx] if hasattr(series, "iloc") else series[idx]
        return None if pd.isna(val) else float(val)
    except (IndexError, TypeError, ValueError):
        return None

# -- CAGR calculation -------------------------------------------------------

def _cagr(values: list[float]) -> float | None:
    """Calculate CAGR over a list of yearly values (oldest first)."""
    vals = [v for v in values if v is not None and v > 0]
    if len(vals) < 2:
        return None
    start = vals[0]
    end = vals[-1]
    n = len(vals) - 1
    if start <= 0 or n == 0:
        return None
    return (end / start) ** (1.0 / n) - 1.0

# -- Main analysis ----------------------------------------------------------

def analyze_fundamentals(ticker: str, ttm: bool = False, quarterly: bool = False):
    """Fetch fundamental data and print report."""

    freq = "quarterly" if quarterly else "yearly"
    label = "Quarterly" if quarterly else "Annual"

    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
    except Exception as e:
        print("  " + _c("red", "Error fetching {0}: {1}".format(ticker, e)))
        return

    # Fetch financial statements
    try:
        if ttm:
            financials = stock.get_financials(freq="trailing")
        elif quarterly:
            financials = stock.quarterly_financials
        else:
            financials = stock.financials
    except Exception:
        financials = None

    try:
        if ttm:
            bs = stock.get_balance_sheet(freq="trailing")
        elif quarterly:
            bs = stock.quarterly_balance_sheet
        else:
            bs = stock.balance_sheet
    except Exception:
        bs = None

    try:
        if ttm:
            cf = stock.get_cashflow(freq="trailing")
        elif quarterly:
            cf = stock.quarterly_cashflow
        else:
            cf = stock.cashflow
    except Exception:
        cf = None

    # Info fields
    name = info.get("longName", info.get("shortName", ticker))
    currency = info.get("financialCurrency", "USD")
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    market_cap = info.get("marketCap", 0)

    # Printable currency
    cs = "$" if currency == "USD" else currency + " "

    # ---- Extract metrics ----
    rev = _safe_loc(financials, "Total Revenue") if financials is not None else None
    net_income = _safe_loc(financials, "Net Income") if financials is not None else None
    gross_profit = _safe_loc(financials, "Gross Profit") if financials is not None else None
    operating_income = _safe_loc(financials, "Operating Income") if financials is not None else None
    ebitda = _safe_loc(financials, "EBITDA") if financials is not None else None

    # Get data series for growth calculations
    rev_series = None
    ni_series = None
    op_series = None
    if financials is not None and not ttm:
        try:
            if "Total Revenue" in financials.index:
                rev_series = financials.loc["Total Revenue"]
        except (KeyError, AttributeError):
            pass
        try:
            if "Net Income" in financials.index:
                ni_series = financials.loc["Net Income"]
        except (KeyError, AttributeError):
            pass
        try:
            if "Operating Income" in financials.index:
                op_series = financials.loc["Operating Income"]
        except (KeyError, AttributeError):
            pass

    # Growth rates (Year-over-Year)
    rev_growth = info.get("revenueGrowth")
    earnings_growth = info.get("earningsGrowth")
    eps_growth = info.get("earningsQuarterlyGrowth")

    # Per share
    rev_per_share = info.get("revenuePerShare")
    book_value = info.get("bookValue")
    eps_ttm = info.get("trailingEps")
    eps_forward = info.get("forwardEps")

    # Margins
    gross_margin = info.get("grossMargins")
    operating_margin = info.get("operatingMargins")
    profit_margin = info.get("profitMargins")
    ebitda_margin = info.get("ebitdaMargins")
    roe = info.get("returnOnEquity")
    roa = info.get("returnOnAssets")

    # Valuation
    pe_trailing = info.get("trailingPE")
    pe_forward = info.get("forwardPE")
    ps_ttm = info.get("priceToSalesTrailing12Months")
    pb = info.get("priceToBook")
    ev_ebitda = info.get("enterpriseToEbitda")
    ev_revenue = info.get("enterpriseToRevenue")
    peg = info.get("pegRatio")
    dividend_yield = info.get("trailingAnnualDividendYield") or info.get("dividendYield")
    payout_ratio = info.get("payoutRatio")

    # Financial health
    five_year_div_yield = info.get("fiveYearAvgDividendYield")
    current_ratio = info.get("currentRatio")
    debt_to_equity = info.get("debtToEquity")
    total_debt = info.get("totalDebt")
    free_cash_flow = info.get("freeCashflow")
    operating_cf = info.get("operatingCashFlow")
    capex = info.get("capitalExpenditures")

    # Deferred / missing items
    if ebitda is None and operating_income is not None:
        d_a = _safe_loc(financials, "Depreciation And Amortization") if financials is not None else None
        ebitda = (operating_income + d_a) if d_a is not None else None

    # Shares outstanding
    shares_out = info.get("sharesOutstanding")
    if shares_out and rev_per_share is None and rev is not None:
        rev_per_share = rev / shares_out
    if shares_out and free_cash_flow is not None:
        fcf_share = free_cash_flow / shares_out
    else:
        fcf_share = None

    # ---- Print report ----

    sep = sym("BOX") * 56
    print()
    print("  " + _c("bold", sep))
    print("  " + _c("bold", ticker.upper()) + " -- {0} ({1})".format(name, label))
    print("  " + _c("bold", "Price:") + " {0}{1:.2f}   {2}Cap: {3}".format(
        cs, price, cs, _fmt_bn(market_cap)))
    print("  " + _c("bold", sep))
    print()

    # 1. Revenue
    print(_hdr("REVENUE", "REV"))
    if rev:
        print("  Latest {0}:    {1}{2}".format(label, cs, _fmt_bn(rev)))
        if rev_per_share:
            print("  Revenue / Share: {0}{1:.2f}".format(cs, rev_per_share))
        if rev_growth is not None:
            print("  YoY Growth:      {0}".format(_pct_col(rev_growth * 100)))
    else:
        print("  " + _c("dim", "N/A"))
    print()

    # 2. Earnings
    print(_hdr("EARNINGS", "PROF"))
    if net_income:
        print("  Net Income:      {0}{1}".format(cs, _fmt_bn(net_income)))
        if eps_ttm:
            print("  Diluted EPS:     {0}{1:.2f}".format(cs, eps_ttm))
        if eps_growth is not None:
            print("  EPS Growth (QoQ): {0}".format(_pct_col(eps_growth * 100)))
        if profit_margin is not None:
            print("  Net Profit Margin: {0:.1f}%".format(profit_margin * 100))
    else:
        print("  " + _c("dim", "N/A"))
    print()

    # 3. Profitability
    print(_hdr("PROFITABILITY", "SCALE"))
    if gross_margin is not None:
        print("  Gross Margin:      {0:.1f}%".format(gross_margin * 100))
    if operating_margin is not None:
        print("  Operating Margin:  {0:.1f}%".format(operating_margin * 100))
    if ebitda_margin is not None:
        print("  EBITDA Margin:     {0:.1f}%".format(ebitda_margin * 100))
    else:
        if ebitda and rev:
            print("  EBITDA Margin:     {0:.1f}%".format((ebitda / rev) * 100))
    if roe is not None:
        print("  ROE:               {0:.1f}%".format(roe * 100))
    if roa is not None:
        print("  ROA:               {0:.1f}%".format(roa * 100))
    print()

    # 4. Valuation
    print(_hdr("VALUATION", "SCALE"))
    if pe_trailing:
        print("  Trailing P/E:     {0:.1f}".format(pe_trailing))
    if pe_forward:
        print("  Forward P/E:      {0:.1f}".format(pe_forward))
    if ps_ttm:
        print("  P/S (TTM):        {0:.1f}".format(ps_ttm))
    if pb:
        print("  P/B:              {0:.1f}".format(pb))
    if ev_ebitda:
        print("  EV/EBITDA:        {0:.1f}".format(ev_ebitda))
    if peg:
        print("  PEG Ratio:        {0:.2f}".format(peg))
    if dividend_yield:
        yield_pct = dividend_yield * 100
        print("  Dividend Yield:   {0:.2f}%".format(yield_pct))
        if payout_ratio:
            print("  Payout Ratio:     {0:.1f}%".format(payout_ratio * 100))
    elif five_year_div_yield:
        print("  Dividend Yield (5y avg): {0:.2f}%".format(five_year_div_yield))
        if payout_ratio:
            print("  Payout Ratio:           {0:.1f}%".format(payout_ratio * 100))
    print()

    # 5. Revenue Growth (series)
    if rev_series is not None and len(rev_series) >= 2:
        rev_list = [float(v) for v in rev_series if pd.notna(v)]  # newest first from yfinance
        rev_list_asc = list(reversed(rev_list))  # oldest first for CAGR
        print(_hdr("REVENUE GROWTH", "CHART"))
        for i in range(min(5, len(rev_list))):
            yr_lbl = rev_series.index[i].strftime("%Y") if hasattr(rev_series.index[i], "strftime") else str(rev_series.index[i])[:4]
            print("  {0}: {1}{2}".format(yr_lbl, cs, _fmt_bn(rev_list[i])))
        if len(rev_list_asc) >= 2:
            cagr_val = _cagr(rev_list_asc)
            if cagr_val is not None:
                n_yrs = len(rev_list_asc) - 1
                print("  {0}y CAGR: {1}".format(n_yrs, _pct_col(cagr_val * 100)))
        print()

    # 6. Earnings Growth (series)
    if ni_series is not None and len(ni_series) >= 2:
        ni_list = [float(v) for v in ni_series if pd.notna(v)]
        ni_list_asc = list(reversed(ni_list))
        print(_hdr("EARNINGS GROWTH", "CHART"))
        for i in range(min(5, len(ni_list))):
            yr_lbl = ni_series.index[i].strftime("%Y") if hasattr(ni_series.index[i], "strftime") else str(ni_series.index[i])[:4]
            sign = "-" if ni_list[i] < 0 else ""
            print("  {0}: {1}{2}{3}".format(yr_lbl, sign, cs, _fmt_bn(abs(ni_list[i]))))
        if len(ni_list_asc) >= 2:
            cagr_val = _cagr(ni_list_asc)
            if cagr_val is not None:
                n_yrs = len(ni_list_asc) - 1
                print("  {0}y CAGR: {1}".format(n_yrs, _pct_col(cagr_val * 100)))
        print()

    # 7. Growth Estimates
    print(_hdr("GROWTH ESTIMATES", "CHART"))
    rev_est = info.get("revenueEstimate")
    eps_est = info.get("epsCurrentYear")
    next_q_rev = info.get("revenueEstimateNextQuarter")
    next_q_eps = info.get("epsNextQuarter")
    growth_est = info.get("growthEstimates")

    found_est = False
    if rev_est:
        print("  Current Year Rev:  {0}{1}".format(cs, _fmt_bn(rev_est)))
        found_est = True
    if next_q_rev:
        print("  Next Quarter Rev:  {0}{1}".format(cs, _fmt_bn(next_q_rev)))
        found_est = True
    if eps_est:
        print("  Current Year EPS:  {0}{1:.2f}".format(cs, eps_est))
        found_est = True
    if next_q_eps:
        print("  Next Quarter EPS:  {0}{1:.2f}".format(cs, next_q_eps))
        found_est = True
    if growth_est:
        print("  Long-term Growth:  {0}".format(_pct_col(growth_est * 100)))
        found_est = True
    if not found_est:
        print("  " + _c("dim", "N/A"))
    print()

    # 8. Financial Health
    print(_hdr("FINANCIAL HEALTH", "HEART"))
    if current_ratio:
        col = "green" if current_ratio >= 1.0 else "red"
        print("  Current Ratio:     {0}".format(_c(col, "{0:.2f}".format(current_ratio))))
    if debt_to_equity is not None:
        col = "green" if debt_to_equity <= 100 else "yellow" if debt_to_equity <= 200 else "red"
        print("  Debt / Equity:     {0}".format(_c(col, "{0:.1f}%".format(debt_to_equity))))
    if total_debt and rev:
        dpr = (total_debt / rev) * 100
        col = "green" if dpr <= 50 else "yellow" if dpr <= 100 else "red"
        print("  Debt / Revenue:    {0}".format(_c(col, "{0:.1f}%".format(dpr))))
    if free_cash_flow:
        print("  Free Cash Flow:    {0}{1}".format(cs, _fmt_bn(free_cash_flow)))
        if market_cap:
            fcf_yield = (free_cash_flow / market_cap) * 100
            col = "green" if fcf_yield >= 3 else "yellow" if fcf_yield >= 1 else "red"
            print("  FCF Yield:         {0}".format(_c(col, "{0:.1f}%".format(fcf_yield))))
    if fcf_share:
        print("  FCF / Share:       {0}{1:.2f}".format(cs, fcf_share))
    print()

    # 9. Composite Score
    print(_hdr("COMPOSITE", "CLIP"))

    score = 0
    details = []

    # Revenue growth (0-10)
    if rev_growth is not None:
        if rev_growth * 100 >= 10:
            score += 10
            details.append("Revenue growth: +10 (strong +{0:.0f}%)".format(rev_growth * 100))
        elif rev_growth * 100 >= 5:
            score += 7
            details.append("Revenue growth: +7  (decent +{0:.0f}%)".format(rev_growth * 100))
        elif rev_growth >= 0:
            score += 4
            details.append("Revenue growth: +4  (flat {0:+.0f}%)".format(rev_growth * 100))
        else:
            score += 0
            details.append("Revenue growth: +0  (shrinking {0:.0f}%)".format(rev_growth * 100))
    else:
        details.append("Revenue growth: --  (N/A)")

    # Profit margin (0-10)
    if profit_margin is not None:
        pm = profit_margin * 100
        if pm >= 20:
            score += 10
            details.append("Profit margin: +10 ({0:.0f}%)".format(pm))
        elif pm >= 10:
            score += 7
            details.append("Profit margin: +7  ({0:.0f}%)".format(pm))
        elif pm >= 5:
            score += 4
            details.append("Profit margin: +4  ({0:.0f}%)".format(pm))
        elif pm > 0:
            score += 1
            details.append("Profit margin: +1  ({0:.0f}%)".format(pm))
        else:
            score += 0
            details.append("Profit margin: +0  (negative)")
    else:
        details.append("Profit margin: --  (N/A)")

    # P/E (0-10)
    if pe_trailing and pe_trailing > 0:
        if pe_trailing <= 15:
            score += 10
            details.append("P/E: +10 ({0:.0f})".format(pe_trailing))
        elif pe_trailing <= 25:
            score += 7
            details.append("P/E: +7  ({0:.0f})".format(pe_trailing))
        elif pe_trailing <= 40:
            score += 4
            details.append("P/E: +4  ({0:.0f})".format(pe_trailing))
        else:
            score += 1
            details.append("P/E: +1  ({0:.0f})".format(pe_trailing))
    else:
        details.append("P/E: --  (N/A)")

    # ROE (0-10)
    if roe is not None:
        if roe * 100 >= 20:
            score += 10
            details.append("ROE: +10 ({0:.0f}%)".format(roe * 100))
        elif roe * 100 >= 10:
            score += 7
            details.append("ROE: +7 ({0:.0f}%)".format(roe * 100))
        elif roe * 100 >= 5:
            score += 4
            details.append("ROE: +4 ({0:.0f}%)".format(roe * 100))
        else:
            score += 1
            details.append("ROE: +1 ({0:.0f}%)".format(roe * 100))
    else:
        details.append("ROE: --  (N/A)")

    # Debt/Equity (0-10)
    if debt_to_equity is not None:
        if debt_to_equity <= 50:
            score += 10
            details.append("D/E: +10 ({0:.0f}%)".format(debt_to_equity))
        elif debt_to_equity <= 100:
            score += 7
            details.append("D/E: +7 ({0:.0f}%)".format(debt_to_equity))
        elif debt_to_equity <= 200:
            score += 4
            details.append("D/E: +4 ({0:.0f}%)".format(debt_to_equity))
        else:
            score += 1
            details.append("D/E: +1 ({0:.0f}%)".format(debt_to_equity))
    else:
        details.append("D/E: --  (N/A)")

    # FCF Yield (0-10) — bonus
    fcf_yield_val = None
    if free_cash_flow and market_cap:
        fcf_yield_val = (free_cash_flow / market_cap) * 100
        if fcf_yield_val >= 5:
            score += 10
            details.append("FCF yield: +10 ({0:.1f}%)".format(fcf_yield_val))
        elif fcf_yield_val >= 3:
            score += 7
            details.append("FCF yield: +7 ({0:.1f}%)".format(fcf_yield_val))
        elif fcf_yield_val >= 1:
            score += 4
            details.append("FCF yield: +4 ({0:.1f}%)".format(fcf_yield_val))
        else:
            score += 1
            details.append("FCF yield: +1 ({0:.1f}%)".format(fcf_yield_val))

    # Composite label
    max_possible = 60  # 6 categories x 10
    pct = (score / max_possible) * 100

    if pct >= 80:
        label_composite = _c("green", "EXCELLENT ({0}/100)".format(round(pct)))
    elif pct >= 60:
        label_composite = _c("green", "Good ({0}/100)".format(round(pct)))
    elif pct >= 40:
        label_composite = _c("yellow", "Fair ({0}/100)".format(round(pct)))
    elif pct >= 20:
        label_composite = _c("red", "Weak ({0}/100)".format(round(pct)))
    else:
        label_composite = _c("red", "POOR ({0}/100)".format(round(pct)))

    print("  SCORE: {0}/{1}  {2}".format(score, max_possible, label_composite))
    print()
    for d in details:
        print("    " + _c("dim", d))
    print()
    print("  " + _c("bold", sep))


# -- CLI --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fundamental analysis of stocks using Yahoo Finance data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("tickers", nargs="+", help="Stock ticker(s) to analyze")
    parser.add_argument("--ttm", action="store_true", help="Use trailing-twelve-months")
    parser.add_argument("--quarterly", action="store_true", help="Use quarterly data")
    args = parser.parse_args()

    for ticker in args.tickers:
        analyze_fundamentals(ticker.upper(), ttm=args.ttm, quarterly=args.quarterly)


if __name__ == "__main__":
    main()
