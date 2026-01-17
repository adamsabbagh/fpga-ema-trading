`timescale 1ns/1ps
//-----------------------------------------------------------------------------
// Module: simple_tb
// Description: Testbench for tick_pipeline EMA crossover trading strategy
//
// Features:
//   - Reads tick data from CSV file (python_version/ticks.csv)
//   - Feeds Q16.16 fixed-point prices to the DUT
//   - Outputs trading signals for HW/SW comparison
//   - Generates VCD waveform file for debugging
//
// Usage:
//   1. Generate tick data:  python python_version/generate_ticks.py
//   2. Compile:            iverilog -o verilog_version/sim verilog_version/*.v
//   3. Run simulation:     vvp verilog_version/sim | tee hw_log.txt
//   4. Compare results:    python python_version/check_match.py
//
// Output Format:
//   tick N -> signal=X  fast=Y  slow=Z
//   Where: signal: 0=HOLD, 1=BUY, 3=SELL (2'b11 = -1 in two's complement)
//          fast/slow: Q16.16 EMA values (divide by 65536 for float)
//-----------------------------------------------------------------------------
module simple_tb;

  //-------------------------------------------------------------------------
  // Clock and Reset
  //-------------------------------------------------------------------------
  reg clk = 0;
  reg rst = 1;

  always #5 clk = ~clk;  // 100 MHz clock (10ns period)

  //-------------------------------------------------------------------------
  // DUT Interface Signals
  //-------------------------------------------------------------------------
  reg         in_valid;
  reg  [31:0] in_price;      // Q16.16 fixed-point price from CSV
  wire        out_valid;
  wire [1:0]  out_signal;    // Trading signal output
  wire [31:0] fast_dbg;      // Fast EMA debug output
  wire [31:0] slow_dbg;      // Slow EMA debug output

  //-------------------------------------------------------------------------
  // Device Under Test
  //-------------------------------------------------------------------------
  tick_pipeline dut (
    .clk       (clk),
    .rst       (rst),
    .in_valid  (in_valid),
    .in_price  (in_price),
    .out_valid (out_valid),
    .out_signal(out_signal),
    .fast_dbg  (fast_dbg),
    .slow_dbg  (slow_dbg)
  );

  //-------------------------------------------------------------------------
  // File I/O Variables
  //-------------------------------------------------------------------------
  integer      fd;           // File descriptor
  reg [1023:0] line;         // Line buffer for CSV parsing
  real         price_r;      // Floating-point price (CSV column 1, unused)
  integer      price_q16;    // Q16.16 price (CSV column 2, used)
  integer      tick;         // Tick counter
  integer      n;            // Return value for $fgets

  //-------------------------------------------------------------------------
  // VCD Waveform Dump (for GTKWave or other viewers)
  //-------------------------------------------------------------------------
  initial begin
    $dumpfile("verilog_version/waves.vcd");
    $dumpvars(0, simple_tb);
  end

  //-------------------------------------------------------------------------
  // Main Test Sequence
  //-------------------------------------------------------------------------
  initial begin
    $display("===========================================");
    $display("  EMA Crossover Trading Strategy Testbench");
    $display("===========================================");

    // Initialize inputs
    in_valid = 0;
    in_price = 0;
    tick     = 0;

    // Hold reset for 5 clock cycles
    repeat (5) @(posedge clk);
    rst = 0;
    $display("Reset released at time %0t", $time);

    // Open tick data file
    fd = $fopen("python_version/ticks.csv", "r");
    if (fd == 0) begin
      $fatal(1, "ERROR: Cannot open python_version/ticks.csv");
    end

    // Skip CSV header line
    n = $fgets(line, fd);

    // Process each tick (one sample per clock cycle)
    while (!$feof(fd)) begin
      if ($fgets(line, fd)) begin
        // Parse CSV: price_float,price_q16
        if ($sscanf(line, "%f,%d", price_r, price_q16) == 2) begin
          in_valid <= 1;
          in_price <= price_q16[31:0];
        end else begin
          in_valid <= 0;
        end
      end
      @(posedge clk);
      tick = tick + 1;
    end

    $fclose(fd);

    // Drain pipeline (allow final outputs to propagate)
    in_valid <= 0;
    repeat (20) @(posedge clk);

    $display("===========================================");
    $display("  Simulation Complete: %0d ticks processed", tick);
    $display("===========================================");
    $finish;
  end

  //-------------------------------------------------------------------------
  // Output Monitor
  // Sample on negative edge to avoid race conditions with posedge updates
  //-------------------------------------------------------------------------
  always @(negedge clk) begin
    if (out_valid) begin
      $display("tick %0d -> signal=%0d  fast=%0d  slow=%0d",
               tick, out_signal, fast_dbg, slow_dbg);
    end
  end

endmodule
