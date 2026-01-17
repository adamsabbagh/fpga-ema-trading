`timescale 1ns/1ps
//-----------------------------------------------------------------------------
// Module: ma_core_ema
// Description: Exponential Moving Average (EMA) core in Verilog-2001
//
// EMA Formula: avg_next = avg + (x - avg) / 2^ALPHA_SH
//
// Features:
//   - Q16.16 fixed-point arithmetic (32-bit: 16 integer, 16 fractional)
//   - Parameterizable smoothing factor via ALPHA_SH
//   - Uses blocking assignments for intermediates to avoid X propagation
//   - Icarus Verilog compatible (pure Verilog-2001, no SystemVerilog)
//
// Parameters:
//   ALPHA_SH: Smoothing shift factor. EMA smoothing = 1/2^ALPHA_SH
//             ALPHA_SH=1 -> 1/2 (very fast)
//             ALPHA_SH=4 -> 1/16
//             ALPHA_SH=6 -> 1/64 (very slow)
//-----------------------------------------------------------------------------
module ma_core_ema(clk, rst, in_valid, in_price, out_valid, out_avg);
  parameter ALPHA_SH = 4;  // smoothing = 1/16 by default

  input clk;
  input rst;
  input in_valid;
  input  [31:0] in_price;   // Q16.16 fixed-point price
  output        out_valid;
  output [31:0] out_avg;    // Q16.16 fixed-point EMA output

  reg out_valid;
  reg [31:0] out_avg;
  reg seeded;

  // Intermediate registers (use blocking '=' to compute within same cycle)
  reg [47:0] avg48, x48, delta48, step48, next48;

  // Arithmetic right shift task (replicates sign bit)
  task arshift48;
    inout [47:0] v;
    input integer sh;
    integer k;
    begin
      for (k = 0; k < sh; k = k + 1)
        v = {v[47], v[47:1]};  // shift right, replicate MSB
    end
  endtask

  always @(posedge clk) begin
    if (rst) begin
      out_valid <= 1'b0;
      out_avg   <= 32'd0;
      seeded    <= 1'b0;
    end else begin
      out_valid <= 1'b0;

      if (in_valid) begin
        // Sign-extend 32-bit to 48-bit for intermediate math
        avg48   = {{16{out_avg[31]}}, out_avg};
        x48     = {{16{in_price[31]}}, in_price};

        // delta = x - avg (two's complement subtraction)
        delta48 = x48 + (~avg48 + 48'd1);

        // step = delta >> ALPHA_SH (arithmetic right shift)
        step48  = delta48;
        arshift48(step48, ALPHA_SH);

        if (!seeded) begin
          // Seed EMA with first sample
          out_avg <= in_price;
          seeded  <= 1'b1;
        end else begin
          // Update EMA: avg_next = avg + step
          next48  = avg48 + step48;
          out_avg <= next48[31:0];
        end

        out_valid <= 1'b1;
      end
    end
  end
endmodule
