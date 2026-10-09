// Schedule vector. 1000 watt-hour pulses, one mint, residual 0.
// The Python spec tools/check_schedule.py is the same rule and is the
// vector that was executed for doc-1.1. This file is the chip-house run.
`timescale 1ns/1ps
module tb_schedule;
    reg clk = 0;
    reg rst_n = 0;
    reg cf_rise = 0;
    reg zeroize = 0;
    reg count_en = 0;
    wire [31:0] watt_hours;
    wire [15:0] residual;
    wire [15:0] tokens;
    wire mint_pulse;
    integer i;
    integer mints;

    always #31.25 clk = ~clk;

    ec_mint1_schedule dut (
        .clk(clk), .rst_n(rst_n), .cf_rise(cf_rise), .zeroize(zeroize),
        .count_en(count_en), .watt_hours(watt_hours), .residual(residual),
        .tokens(tokens), .mint_pulse(mint_pulse)
    );

    initial begin
        mints = 0;
        repeat (4) @(posedge clk);
        rst_n = 1;
        count_en = 1;
        for (i = 0; i < 1000; i = i + 1) begin
            @(posedge clk);
            cf_rise = 1;
            @(posedge clk);
            cf_rise = 0;
            if (mint_pulse) mints = mints + 1;
        end
        @(posedge clk);
        if (mints != 1 || residual != 0 || watt_hours != 1000 || tokens != 1) begin
            $display("FAIL mints=%0d W=%0d r=%0d n=%0d", mints, watt_hours, residual, tokens);
            $finish(1);
        end
        $display("PASS one token per 1000 watt-hour pulses");
        $finish(0);
    end
endmodule
