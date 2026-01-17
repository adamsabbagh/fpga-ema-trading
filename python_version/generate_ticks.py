#!/usr/bin/env python3
"""
Generate synthetic market tick data for FPGA simulation.
Outputs both floating-point prices and Q16.16 fixed-point integers.
"""
import numpy as np
import pandas as pd

SCALE = 1 << 16  # Q16.16 scale factor (65536)

def generate_ticks(num_points=400, seed=0):
    """
    Generate synthetic price data with sine wave oscillations.
    This creates regular crossovers between fast and slow EMAs.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(num_points)

    # Base price with sine wave (creates regular oscillations for crossovers)
    prices = 100 + 3.0 * np.sin(2 * np.pi * t / 18) + rng.normal(0, 0.6, size=num_points)

    df = pd.DataFrame({"price": prices})

    # Convert to Q16.16 fixed-point (multiply by 2^16, round to integer)
    df["price_q16"] = (df["price"] * SCALE).round().astype("int64")

    df.to_csv("python_version/ticks.csv", index=False)
    print(f"Wrote python_version/ticks.csv with {num_points} ticks")
    print(f"Price range: {prices.min():.2f} to {prices.max():.2f}")
    return df

if __name__ == "__main__":
    generate_ticks()
