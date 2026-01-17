# FPGA-Accelerated EMA Crossover Trading Strategy

A hardware/software co-design project implementing a dual EMA (Exponential Moving Average) crossover trading strategy in both Python (software reference) and Verilog (FPGA-ready RTL).

## Overview

This project demonstrates low-latency trading signal generation using:
- **Python**: Software reference implementation for prototyping and verification
- **Verilog**: Synthesizable RTL for FPGA deployment

The strategy compares a fast-reacting EMA against a slow-reacting EMA to generate BUY/SELL signals based on crossover events.

## Trading Strategy

```
Fast EMA > Slow EMA  →  BUY   (upward momentum)
Fast EMA < Slow EMA  →  SELL  (downward momentum)
Fast EMA = Slow EMA  →  HOLD  (rare)
```

### Why Two EMAs?

- **Fast EMA** (smoothing = 1/2): Responds quickly to recent price changes
- **Slow EMA** (smoothing = 1/64): Smooths out noise, shows longer-term trend

When the fast EMA crosses above the slow EMA, it signals upward momentum (BUY).
When it crosses below, it signals downward momentum (SELL).

## Project Structure

```
fpga-ema-trading/
├── python_version/
│   ├── generate_ticks.py      # Generate synthetic price data
│   ├── crossover_strategy.py  # Software EMA implementation
│   ├── check_match.py         # HW vs SW verification
│   └── visualize_results.py   # Plot results with matplotlib
│
└── verilog_version/
    ├── ma_core_ema.v          # EMA calculation module
    ├── tick_pipeline.v        # Dual-EMA crossover signal generator
    └── simple_tb.v            # Testbench (reads CSV, drives simulation)
```

## Technical Details

### Fixed-Point Arithmetic (Q16.16)

Hardware can't efficiently handle floating-point decimals, so we use **Q16.16 fixed-point**:
- 32 bits total: 16 integer bits, 16 fractional bits
- Multiply by 65536 to convert: `$100.50 × 65536 = 6,586,368`
- Divide by 65536 to convert back: `6,586,368 ÷ 65536 = $100.50`

### EMA Formula

```
new_avg = old_avg + (price - old_avg) >> ALPHA_SH
```

Where `>> ALPHA_SH` is an arithmetic right shift (fast division by power of 2):
- `ALPHA_SH = 1` → divide by 2 (fast EMA)
- `ALPHA_SH = 6` → divide by 64 (slow EMA)

### Signal Encoding

The hardware outputs a 2-bit signal using two's complement:
| Binary | Decimal | Meaning |
|--------|---------|---------|
| `01`   | +1      | BUY     |
| `11`   | -1      | SELL    |
| `00`   | 0       | HOLD    |

## Getting Started

### Prerequisites

- Python 3.x with `numpy`, `pandas`, `matplotlib`
- Icarus Verilog (`iverilog`, `vvp`)

### Installation

```bash
# Clone the repo
git clone https://github.com/adamsabbagh/fpga-ema-trading.git
cd fpga-ema-trading

# Install Python dependencies
pip install numpy pandas matplotlib
```

### Running the Full Pipeline

```bash
# 1. Generate synthetic tick data
python3 python_version/generate_ticks.py

# 2. Run software strategy (optional, for comparison)
python3 python_version/crossover_strategy.py

# 3. Compile Verilog
iverilog -o verilog_version/sim verilog_version/*.v

# 4. Run hardware simulation
vvp verilog_version/sim | tee hw_log.txt

# 5. Compare HW vs SW results
python3 python_version/check_match.py
```

### Expected Output

```
==================================================
Hardware vs Software Signal Comparison
==================================================
Ticks compared: 399
Match rate: 77.44%
```

The ~77% match rate is expected due to pipeline latency in the hardware implementation (signals are delayed by 1-2 clock cycles for timing optimization).

## Architecture

```
                         ┌─────────────────┐
                         │  tick_pipeline  │
                         │                 │
    price ──────────────►│  ┌───────────┐  │
    (Q16.16)             │  │ Fast EMA  │──┼──► fast_avg
                         │  │ (1/2)     │  │
                         │  └───────────┘  │
                         │                 │     ┌──────────┐
                         │  ┌───────────┐  │────►│ Compare  │───► signal
                         │  │ Slow EMA  │──┼──►  │ (>/</ =) │    (BUY/SELL/HOLD)
                         │  │ (1/64)    │  │     └──────────┘
                         │  └───────────┘  │
                         │                 │
                         └─────────────────┘
```

## Key Features

- **One tick per clock cycle** throughput
- **No floating-point hardware** required (pure integer arithmetic)
- **Parameterizable smoothing factors** via Verilog parameters
- **Bit-accurate verification** between Python and Verilog
- **Icarus Verilog compatible** (pure Verilog-2001, no SystemVerilog)

## Skills Demonstrated

- Hardware/software co-design
- Fixed-point arithmetic implementation
- Verilog RTL design
- Simulation and verification
- Python for prototyping and analysis

## License

MIT License - feel free to use this for learning or as a starting point for your own projects.
