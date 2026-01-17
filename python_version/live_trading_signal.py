#!/usr/bin/env python3
"""
Live Trading Signal Generator

Fetches real stock prices and generates BUY/SELL/HOLD signals
using the EMA crossover strategy.

Usage:
    python live_trading_signal.py AAPL
    python live_trading_signal.py TSLA
    python live_trading_signal.py GOOGL
"""
import sys
import yfinance as yf
import numpy as np
from datetime import datetime

# EMA parameters (same as hardware implementation)
FAST_PERIOD = 12   # Fast EMA period
SLOW_PERIOD = 26   # Slow EMA period


def calculate_ema(prices, period):
    """
    Calculate Exponential Moving Average.

    Args:
        prices: Array of prices
        period: EMA period (e.g., 12 for fast, 26 for slow)

    Returns:
        Array of EMA values
    """
    multiplier = 2 / (period + 1)
    ema = [prices[0]]  # Start with first price

    for price in prices[1:]:
        new_ema = (price * multiplier) + (ema[-1] * (1 - multiplier))
        ema.append(new_ema)

    return np.array(ema)


def get_signal(fast_ema, slow_ema):
    """
    Determine trading signal based on EMA crossover.

    Returns:
        Tuple of (signal, description)
    """
    if fast_ema > slow_ema:
        return "BUY", "Fast EMA is ABOVE Slow EMA (upward momentum)"
    elif fast_ema < slow_ema:
        return "SELL", "Fast EMA is BELOW Slow EMA (downward momentum)"
    else:
        return "HOLD", "EMAs are equal (no clear trend)"


def analyze_stock(ticker):
    """
    Fetch stock data and generate trading signal.
    """
    print(f"\n{'='*60}")
    print(f"  LIVE TRADING SIGNAL: {ticker.upper()}")
    print(f"{'='*60}")

    # Fetch stock data
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")  # Last 3 months of data

        if hist.empty:
            print(f"\nError: No data found for ticker '{ticker}'")
            print("Make sure you entered a valid stock symbol.")
            return

    except Exception as e:
        print(f"\nError fetching data: {e}")
        return

    # Get company info
    try:
        info = stock.info
        company_name = info.get('longName', ticker.upper())
    except:
        company_name = ticker.upper()

    print(f"\n  Company: {company_name}")
    print(f"  Ticker:  {ticker.upper()}")
    print(f"  Date:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get closing prices
    prices = hist['Close'].values

    if len(prices) < SLOW_PERIOD:
        print(f"\nError: Not enough data points. Need at least {SLOW_PERIOD} days.")
        return

    # Calculate EMAs
    fast_ema = calculate_ema(prices, FAST_PERIOD)
    slow_ema = calculate_ema(prices, SLOW_PERIOD)

    # Current values
    current_price = prices[-1]
    current_fast = fast_ema[-1]
    current_slow = slow_ema[-1]

    # Previous values (for trend detection)
    prev_fast = fast_ema[-2]
    prev_slow = slow_ema[-2]

    # Get signal
    signal, reason = get_signal(current_fast, current_slow)

    # Detect crossover
    crossover = ""
    if prev_fast <= prev_slow and current_fast > current_slow:
        crossover = "BULLISH CROSSOVER DETECTED (Fast crossed above Slow)"
    elif prev_fast >= prev_slow and current_fast < current_slow:
        crossover = "BEARISH CROSSOVER DETECTED (Fast crossed below Slow)"

    # Print results
    print(f"\n  {'─'*56}")
    print(f"  PRICE DATA")
    print(f"  {'─'*56}")
    print(f"  Current Price:    ${current_price:.2f}")
    print(f"  52-Week High:     ${hist['Close'].max():.2f}")
    print(f"  52-Week Low:      ${hist['Close'].min():.2f}")

    print(f"\n  {'─'*56}")
    print(f"  EMA ANALYSIS")
    print(f"  {'─'*56}")
    print(f"  Fast EMA ({FAST_PERIOD}-day):  ${current_fast:.2f}")
    print(f"  Slow EMA ({SLOW_PERIOD}-day):  ${current_slow:.2f}")
    print(f"  Difference:       ${abs(current_fast - current_slow):.2f} ({'+' if current_fast > current_slow else '-'}{abs((current_fast - current_slow) / current_slow * 100):.2f}%)")

    print(f"\n  {'─'*56}")
    print(f"  SIGNAL")
    print(f"  {'─'*56}")

    # Color-coded signal (using ANSI codes for terminal)
    if signal == "BUY":
        signal_display = f"\033[92m  >>>  {signal}  <<<\033[0m"  # Green
    elif signal == "SELL":
        signal_display = f"\033[91m  >>>  {signal}  <<<\033[0m"  # Red
    else:
        signal_display = f"\033[93m  >>>  {signal}  <<<\033[0m"  # Yellow

    print(signal_display)
    print(f"\n  Reason: {reason}")

    if crossover:
        print(f"\n  ⚠️  {crossover}")

    # Recent trend
    print(f"\n  {'─'*56}")
    print(f"  RECENT PRICE HISTORY (last 5 days)")
    print(f"  {'─'*56}")

    recent_dates = hist.index[-5:]
    recent_prices = prices[-5:]

    for date, price in zip(recent_dates, recent_prices):
        print(f"  {date.strftime('%Y-%m-%d')}: ${price:.2f}")

    print(f"\n  {'─'*56}")
    print(f"  DISCLAIMER")
    print(f"  {'─'*56}")
    print(f"  This is not financial advice.")
    print(f"  Always do your own research before trading.")

    # Final clear answer
    print(f"\n{'='*60}")
    if signal == "BUY":
        print(f"\033[92m")  # Green
        print(f"  FINAL ANSWER:  BUY")
        print(f"")
        print(f"  {company_name} ({ticker.upper()}) at ${current_price:.2f}")
        print(f"  Upward momentum detected - consider buying")
        print(f"\033[0m", end="")
    elif signal == "SELL":
        print(f"\033[91m")  # Red
        print(f"  FINAL ANSWER:  SELL")
        print(f"")
        print(f"  {company_name} ({ticker.upper()}) at ${current_price:.2f}")
        print(f"  Downward momentum detected - consider selling")
        print(f"\033[0m", end="")
    else:
        print(f"\033[93m")  # Yellow
        print(f"  FINAL ANSWER:  HOLD")
        print(f"")
        print(f"  {company_name} ({ticker.upper()}) at ${current_price:.2f}")
        print(f"  No clear trend - consider holding")
        print(f"\033[0m", end="")
    print(f"{'='*60}\n")


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python live_trading_signal.py <TICKER>")
        print("\nExamples:")
        print("  python live_trading_signal.py AAPL    # Apple")
        print("  python live_trading_signal.py TSLA    # Tesla")
        print("  python live_trading_signal.py GOOGL   # Google")
        print("  python live_trading_signal.py MSFT    # Microsoft")
        print("  python live_trading_signal.py AMZN    # Amazon")
        print("  python live_trading_signal.py NVDA    # NVIDIA")
        print()

        # Interactive mode
        ticker = input("Enter a stock ticker: ").strip()
        if ticker:
            analyze_stock(ticker)
    else:
        ticker = sys.argv[1]
        analyze_stock(ticker)


if __name__ == "__main__":
    main()
