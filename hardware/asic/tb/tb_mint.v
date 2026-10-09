`timescale 1ns/1ps
module tb_mint;
    reg clk = 0;
    reg rst_n = 0;
    reg cf_in = 0;
    reg zeroize = 0;
    wire mint;
    always #30.5 clk = ~clk;
    ec_mint1 dut (
        .clk(clk), .rst_n(rst_n), .cf_in(cf_in), .zeroize(zeroize),
        .prov_cs(1'b0), .prov_sck(1'b0), .prov_mosi(1'b0),
        .prov_miso(), .tx(), .mint(mint)
    );
    integer i;
    integer pulses;
    initial begin
        pulses = 0;
        repeat (4) @(posedge clk);
        rst_n = 1;
        for (i = 0; i < 1000; i = i + 1) begin
            @(posedge clk); cf_in = 1;
            @(posedge clk); cf_in = 0;
            @(posedge clk);
            if (mint) pulses = pulses + 1;
        end
        if (pulses != 1) begin
            $display("FAIL mint count %0d", pulses);
            $finish(1);
        end
        $display("PASS one token per 1000 watt-hour pulses");
        $finish(0);
    end
endmodule
