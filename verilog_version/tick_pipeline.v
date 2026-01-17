`timescale 1ns/1ps
//-----------------------------------------------------------------------------
// Module: tick_pipeline
// Description: Trading signal generator using dual EMA crossover strategy
//
// Architecture:
//   1. Two EMA cores (fast and slow) process incoming tick data
//   2. Registered comparison stage generates trading signals
//   3. Outputs: BUY (+1), SELL (-1), HOLD (0)
//
// Signal Encoding (2-bit two's complement):
//   2'b01 = +1 = BUY  (fast EMA > slow EMA)
//   2'b11 = -1 = SELL (fast EMA < slow EMA)
//   2'b00 =  0 = HOLD (fast EMA == slow EMA)
//
// Parameters:
//   FAST_ALPHA_SH: Fast EMA smoothing (smaller = faster response)
//   SLOW_ALPHA_SH: Slow EMA smoothing (larger = slower response)
//-----------------------------------------------------------------------------
module tick_pipeline(
  clk, rst, in_valid, in_price, out_valid, out_signal, fast_dbg, slow_dbg
);
  parameter FAST_ALPHA_SH = 1; // Fast EMA: 1/2 smoothing
  parameter SLOW_ALPHA_SH = 6; // Slow EMA: 1/64 smoothing

  input clk;
  input rst;
  input in_valid;
  input  [31:0] in_price;   // Q16.16 fixed-point price
  output        out_valid;
  output [1:0]  out_signal; // Trading signal
  output [31:0] fast_dbg;   // Fast EMA debug output
  output [31:0] slow_dbg;   // Slow EMA debug output

  //-------------------------------------------------------------------------
  // EMA Instances
  //-------------------------------------------------------------------------
  wire v_fast, v_slow;
  wire [31:0] fast_avg, slow_avg;

  ma_core_ema #(.ALPHA_SH(FAST_ALPHA_SH)) u_fast (
    .clk(clk),
    .rst(rst),
    .in_valid(in_valid),
    .in_price(in_price),
    .out_valid(v_fast),
    .out_avg(fast_avg)
  );

  ma_core_ema #(.ALPHA_SH(SLOW_ALPHA_SH)) u_slow (
    .clk(clk),
    .rst(rst),
    .in_valid(in_valid),
    .in_price(in_price),
    .out_valid(v_slow),
    .out_avg(slow_avg)
  );

  //-------------------------------------------------------------------------
  // Crossover Detection with Registered Comparison
  //-------------------------------------------------------------------------
  wire v_both = v_fast & v_slow;  // Both EMAs valid this cycle

  reg        out_valid_r;
  reg [1:0]  signal_r;
  reg [31:0] fast_q, slow_q;  // Registered EMA values

  always @(posedge clk) begin
    if (rst) begin
      fast_q      <= 32'd0;
      slow_q      <= 32'd0;
      out_valid_r <= 1'b0;
      signal_r    <= 2'b00;
    end else begin
      // Stage 1: Latch EMA outputs when both valid
      if (v_both) begin
        fast_q <= fast_avg;
        slow_q <= slow_avg;
      end

      // Stage 2: Generate signal based on registered values
      if (v_both) begin
        if (fast_q > slow_q)
          signal_r <= 2'b01;      // BUY (+1)
        else if (fast_q < slow_q)
          signal_r <= 2'b11;      // SELL (-1 in two's complement)
        else
          signal_r <= 2'b00;      // HOLD
        out_valid_r <= 1'b1;
      end else begin
        out_valid_r <= 1'b0;
      end
    end
  end

  //-------------------------------------------------------------------------
  // Output Assignments
  //-------------------------------------------------------------------------
  assign out_valid  = out_valid_r;
  assign out_signal = signal_r;
  assign fast_dbg   = fast_q;
  assign slow_dbg   = slow_q;

endmodule
