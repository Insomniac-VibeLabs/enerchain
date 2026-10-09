// Schedule vector, v0.0.1. Q = 1000 and a record every 10 tokens, as built.
// The Python spec is tools/check_schedule.py; this is the chip-house run.
//  - 1000 export pulses mint one token; 999 do not.
//  - 400 then 600 mint one token, not two.
//  - 500 import pulses then 1500 export pulses mint one token (net 1000).
//  - The tenth token raises sign_req once.
`timescale 1ns/1ps
module tb_schedule;
    reg clk = 0;
    reg rst_n = 0;
    reg ex = 0, im = 0;
    reg count_en = 0;
    wire [47:0] e_exp, e_imp, tokens, credit;
    wire [7:0] since;
    wire mint_pulse, sign_req, changed;
    integer mints, signs, fails;

    always #31.25 clk = ~clk;

    ec_mint1_schedule #(.Q(16'd1000), .SIGN_EVERY(8'd10)) dut (
        .clk(clk), .rst_n(rst_n), .count_en(count_en),
        .exp_rise(ex), .imp_rise(im), .load(1'b0),
        .ld_exp(48'd0), .ld_imp(48'd0), .ld_tok(48'd0), .ld_credit(48'd0), .ld_since(8'd0),
        .e_exp(e_exp), .e_imp(e_imp), .tokens(tokens), .credit(credit),
        .since_sign(since), .mint_pulse(mint_pulse), .sign_req(sign_req), .changed(changed)
    );

    always @(posedge clk) begin
        if (mint_pulse) mints = mints + 1;
        if (sign_req) signs = signs + 1;
    end

    task pe; input integer n; integer i;
        for (i = 0; i < n; i = i + 1) begin
            @(posedge clk) ex <= 1; @(posedge clk) ex <= 0;
        end
    endtask
    task pi; input integer n; integer i;
        for (i = 0; i < n; i = i + 1) begin
            @(posedge clk) im <= 1; @(posedge clk) im <= 0;
        end
    endtask

    initial begin
        mints = 0; signs = 0; fails = 0;
        repeat (4) @(posedge clk);
        rst_n = 1;
        count_en = 1;
        pe(999);
        repeat (2) @(posedge clk);
        if (mints != 0) begin fails = fails + 1; $display("FAIL 999 minted"); end
        pe(1);
        repeat (2) @(posedge clk);
        if (mints != 1 || tokens != 1 || credit != 0) begin fails = fails + 1; $display("FAIL 1000"); end
        pe(400); pe(600);
        repeat (2) @(posedge clk);
        if (tokens != 2) begin fails = fails + 1; $display("FAIL split"); end
        pi(500); pe(1500);
        repeat (2) @(posedge clk);
        if (tokens != 3 || e_exp != 3500 || e_imp != 500) begin
            fails = fails + 1; $display("FAIL net tokens=%0d", tokens);
        end
        pe(7000);
        repeat (2) @(posedge clk);
        if (tokens != 10 || signs != 1) begin
            fails = fails + 1; $display("FAIL sign_req tokens=%0d signs=%0d", tokens, signs);
        end
        if (fails == 0)
            $display("PASS schedule: one token per 1000 net-export Wh, record every 10 tokens");
        $finish;
    end
endmodule
