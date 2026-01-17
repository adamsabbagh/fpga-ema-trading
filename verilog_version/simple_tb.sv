// verilog_version/simple_tb.sv
`timescale 1ns/1ps
import fixed_point_pkg::*;

module simple_tb;
  logic clk = 0, rst = 1;
  always #5 clk = ~clk;  // 100 MHz

  logic        in_valid;
  q16_t        in_price;
  logic        out_valid;
  logic signed [1:0] out_signal;

  tick_pipeline #(.FAST_WIN(16), .SLOW_WIN(64)) dut (
    .clk, .rst, .in_valid, .in_price, .out_valid, .out_signal
  );

  integer fd;
  string line;
  int    line_num = 0;

  initial begin
    $display("starting TB...");
    // reset
    repeat (5) @(posedge clk);
    rst = 0;

    // open CSV produced by Python
    fd = $fopen("python_version/ticks.csv", "r");
    if (fd == 0) begin
      $fatal(1, "failed to open python_version/ticks.csv");
    end

    // skip header
    void'($fgets(line, fd));

    // drive one sample per cycle
    while (!$feof(fd)) begin
      int price_q16;
      // parse "price,price_q16" but we only need the second column
      // read both to keep parser robust
      real price_unused;
      // read a line into variables (price as real, price_q16 as integer)
      if ($fscanf(fd, "%f,%d\n", price_unused, price_q16) == 2) begin
        in_valid <= 1;
        in_price <= q16_t'(price_q16);
      end else begin
        in_valid <= 0;
      end

      @(posedge clk);
      line_num++;

      // when output valid, print the signal
      if (out_valid) begin
        $display("tick %0d -> signal %0d", line_num, out_signal);
      end
    end

    // drain a few cycles
    in_valid <= 0;
    repeat (20) @(posedge clk);

    $display("TB done.");
    $finish;
  end
endmodule
