#!/usr/bin/env python3
"""
Compare hardware (Verilog) signals vs software (Python) signals.
Computes match rate to verify HW/SW parity.
"""
import pandas as pd
import numpy as np
import re
import sys

# EMA parameters - MUST match tick_pipeline.v settings
FAST_SH = 1   # Fast EMA: smoothing = 1/2
SLOW_SH = 6   # Slow EMA: smoothing = 1/64

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
            avg = avg + ((x - avg) >> alpha_sh)
        out.append(avg)
    return np.array(out, dtype=np.int64)

def read_hw_log(path="hw_log.txt"):
    """Parse hardware simulation log file."""
    rows = []
    try:
        with open(path, "r") as f:
            for line in f:
                # Match: "tick 87 -> signal=1  fast=... slow=..."
                m = re.search(r"tick\s+(\d+)\s*->\s*signal=(\d+)", line)
                if m:
                    t = int(m.group(1))
                    s = int(m.group(2))
                    # Map 2'b11 (3) to -1 for SELL
                    if s == 3:
                        s = -1
                    elif s == 1:
                        s = 1
                    else:
                        s = 0
                    rows.append((t, s))
    except FileNotFoundError:
        print(f"Error: {path} not found.")
        print("Run the simulation first:")
        print("  vvp verilog_version/sim | tee hw_log.txt")
        sys.exit(1)

    return pd.DataFrame(rows, columns=["tick", "hw_sig"]).drop_duplicates("tick")

def main():
    # Read tick data (Q16.16 fixed-point)
    df = pd.read_csv("python_version/ticks.csv")
    q16_prices = df["price_q16"].to_numpy(dtype=np.int64)

    # Compute software EMA signals (using Q16.16 arithmetic to match HW)
    fast = ema_q16(q16_prices, FAST_SH)
    slow = ema_q16(q16_prices, SLOW_SH)

    sw_sig = []
    for f, s in zip(fast, slow):
        if f > s:
            sw_sig.append(1)   # BUY
        elif f < s:
            sw_sig.append(-1)  # SELL
        else:
            sw_sig.append(0)   # HOLD

    sw = pd.DataFrame({
        "tick": range(1, len(sw_sig) + 1),
        "sw_sig": sw_sig
    })

    # Read hardware simulation log
    hw = read_hw_log("hw_log.txt")

    # Merge and compare
    merged = pd.merge(hw, sw, on="tick", how="inner")

    if len(merged) == 0:
        print("No overlapping ticks found between HW and SW.")
        print("Check that hw_log.txt contains 'tick N -> signal=X' lines.")
        return

    merged["match"] = (merged["hw_sig"] == merged["sw_sig"]).astype(int)
    acc = merged["match"].mean() * 100

    print("=" * 50)
    print("Hardware vs Software Signal Comparison")
    print("=" * 50)
    print(f"Ticks compared: {len(merged)}")
    print(f"Match rate: {acc:.2f}%")
    print()

    # Show first few mismatches if any
    mismatches = merged[merged["match"] == 0]
    if len(mismatches) > 0:
        print(f"Mismatches: {len(mismatches)}")
        print("\nFirst 10 mismatches:")
        print(mismatches.head(10).to_string(index=False))
    else:
        print("All signals match!")

    print()
    print("Sample of first 12 ticks:")
    print(merged.head(12).to_string(index=False))

if __name__ == "__main__":
    main()
