#!/usr/bin/env python3
"""
Visualize trading strategy results: price, EMAs, and signals.
Creates publication-ready charts for documentation/portfolio.
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_strategy():
    """Plot price, EMAs, and trading signals."""
    df = pd.read_csv("python_version/strategy_output.csv")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Top plot: Price and EMAs
    ax1.plot(df.index, df["price"], label="Price", alpha=0.7, linewidth=1)
    ax1.plot(df.index, df["fast_ema"], label="Fast EMA (1/2)", linewidth=1.5)
    ax1.plot(df.index, df["slow_ema"], label="Slow EMA (1/64)", linewidth=1.5)
    ax1.set_ylabel("Price")
    ax1.set_title("EMA Crossover Trading Strategy")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    # Bottom plot: Trading signals
    colors = ["red" if s == -1 else "green" if s == 1 else "gray" for s in df["signal"]]
    ax2.bar(df.index, df["signal"], color=colors, width=1.0)
    ax2.set_ylabel("Signal")
    ax2.set_xlabel("Tick")
    ax2.set_yticks([-1, 0, 1])
    ax2.set_yticklabels(["SELL", "HOLD", "BUY"])
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("docs/strategy_plot.png", dpi=150)
    print("Saved docs/strategy_plot.png")
    plt.show()

def plot_hw_results():
    """Plot hardware simulation results from hw_log.txt."""
    import re

    ticks = []
    fast = []
    slow = []
    signals = []

    try:
        with open("hw_log.txt") as f:
            for line in f:
                m = re.search(r"tick\s+(\d+).*signal=(\d+)\s+fast=(\d+)\s+slow=(\d+)", line)
                if m:
                    ticks.append(int(m.group(1)))
                    sig = int(m.group(2))
                    signals.append(1 if sig == 1 else (-1 if sig == 3 else 0))
                    fast.append(int(m.group(3)) / 65536.0)  # Q16.16 to float
                    slow.append(int(m.group(4)) / 65536.0)
    except FileNotFoundError:
        print("hw_log.txt not found. Run the Verilog simulation first:")
        print("  vvp verilog_version/sim | tee hw_log.txt")
        return

    if not ticks:
        print("No data found in hw_log.txt")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Top plot: Hardware EMAs
    ax1.plot(ticks, fast, label="Fast EMA (HW)", linewidth=1.5)
    ax1.plot(ticks, slow, label="Slow EMA (HW)", linewidth=1.5)
    ax1.set_ylabel("Price (Q16.16 → float)")
    ax1.set_title("Hardware Simulation Results")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    # Bottom plot: Hardware signals
    colors = ["red" if s == -1 else "green" if s == 1 else "gray" for s in signals]
    ax2.bar(ticks, signals, color=colors, width=1.0)
    ax2.set_ylabel("Signal")
    ax2.set_xlabel("Tick")
    ax2.set_yticks([-1, 0, 1])
    ax2.set_yticklabels(["SELL", "HOLD", "BUY"])
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("docs/hw_results_plot.png", dpi=150)
    print("Saved docs/hw_results_plot.png")
    plt.show()

if __name__ == "__main__":
    print("Plotting software strategy results...")
    plot_strategy()

    print("\nPlotting hardware simulation results...")
    plot_hw_results()
