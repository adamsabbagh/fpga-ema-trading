#!/usr/bin/env python3
"""
Software reference implementation of EMA crossover strategy.
This mirrors the hardware implementation for verification.
"""
import pandas as pd
import numpy as np

# EMA parameters - MUST match tick_pipeline.v settings
FAST_ALPHA_SH = 1  # Fast EMA: smoothing = 1/2
SLOW_ALPHA_SH = 6  # Slow EMA: smoothing = 1/64
SCALE = 1 << 16    # Q16.16 scale factor

def ema_q16(q16_prices, alpha_sh):
    """
    Compute EMA on Q16.16 fixed-point prices.
    Uses same arithmetic as hardware: avg += (x - avg) >> alpha_sh
    """
    avg = None
    out = []
    for x in q16_prices:
        if avg is None:
            avg = x
        else:
            # Arithmetic right shift (preserves sign)
            avg = avg + ((x - avg) >> alpha_sh)
        out.append(avg)
    return np.array(out, dtype=np.int64)

def ema_float(prices, alpha_sh):
    """
    Compute EMA on floating-point prices for visualization.
    """
    alpha = 1.0 / (1 << alpha_sh)
    out = []
    avg = None
    for x in prices:
        if avg is None:
            avg = x
        else:
            avg = avg + alpha * (x - avg)
        out.append(avg)
    return np.array(out)

def main():
    df = pd.read_csv("python_version/ticks.csv")

    # Compute EMAs (floating point for visualization)
    df["fast_ema"] = ema_float(df["price"].values, FAST_ALPHA_SH)
    df["slow_ema"] = ema_float(df["price"].values, SLOW_ALPHA_SH)

    # Compute signal: +1 = BUY (fast > slow), -1 = SELL (fast < slow), 0 = HOLD
    df["signal"] = 0
    df.loc[df["fast_ema"] > df["slow_ema"], "signal"] = 1
    df.loc[df["fast_ema"] < df["slow_ema"], "signal"] = -1

    df.to_csv("python_version/strategy_output.csv", index=False)
    print("Wrote python_version/strategy_output.csv")

    # Summary
    buys = (df["signal"] == 1).sum()
    sells = (df["signal"] == -1).sum()
    holds = (df["signal"] == 0).sum()
    print(f"Signals: BUY={buys}, SELL={sells}, HOLD={holds}")

if __name__ == "__main__":
    main()
