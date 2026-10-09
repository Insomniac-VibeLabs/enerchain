// EC-MINT1 schedule, v0.0.1 (doc-1.2). Net-export watt-hour schedule.
//
// Export pulses (CF_EXP) and import pulses (CF_IMP) are counted in two
// monotone 48-bit registers. A signed credit register holds
//     credit = e_exp - e_imp - tokens * Q
// A token is minted only when credit reaches Q. Imported energy pulls
// credit down, so energy bought from the grid and pushed back out mints
// nothing: tokens = floor(max over time of (e_exp - e_imp) / Q).
// Splitting an interval cannot mint extra, because credit carries.
//
// Every SIGN_EVERY tokens, sign_req pulses once. The record carries the
// cumulative registers, so a lost or skipped record loses nothing.
//
// q, the registers and the credit have no host write port. `load` is
// driven only by the boot FSM from the FRAM image, before counting starts.
module ec_mint1_schedule #(
    parameter [15:0] Q          = 16'd1000,
    parameter [7:0]  SIGN_EVERY = 8'd10
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        count_en,
    input  wire        exp_rise,
    input  wire        imp_rise,
    input  wire        load,
    input  wire [47:0] ld_exp,
    input  wire [47:0] ld_imp,
    input  wire [47:0] ld_tok,
    input  wire [47:0] ld_credit,
    input  wire [7:0]  ld_since,
    output reg  [47:0] e_exp,
    output reg  [47:0] e_imp,
    output reg  [47:0] tokens,
    output reg  [47:0] credit,      // two's complement
    output reg  [7:0]  since_sign,
    output reg         mint_pulse,
    output reg         sign_req,
    output reg         changed
);
    localparam [47:0] QM1  = {32'd0, Q} - 48'd1;
    localparam [47:0] CMIN = 48'h8000_0000_0000;

    wire ex = count_en & exp_rise;
    wire im = count_en & imp_rise;
    wire up = ex & ~im;
    wire dn = im & ~ex;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            e_exp <= 48'd0;
            e_imp <= 48'd0;
            tokens <= 48'd0;
            credit <= 48'd0;
            since_sign <= 8'd0;
            mint_pulse <= 1'b0;
            sign_req <= 1'b0;
            changed <= 1'b0;
        end else if (load) begin
            e_exp <= ld_exp;
            e_imp <= ld_imp;
            tokens <= ld_tok;
            credit <= ld_credit;
            since_sign <= ld_since;
            mint_pulse <= 1'b0;
            sign_req <= 1'b0;
            changed <= 1'b0;
        end else begin
            mint_pulse <= 1'b0;
            sign_req <= 1'b0;
            changed <= ex | im;
            if (ex)
                e_exp <= e_exp + 48'd1;
            if (im)
                e_imp <= e_imp + 48'd1;
            if (up) begin
                if (credit == QM1) begin
                    credit <= 48'd0;
                    tokens <= tokens + 48'd1;
                    mint_pulse <= 1'b1;
                    if (since_sign >= SIGN_EVERY - 8'd1) begin
                        since_sign <= 8'd0;
                        sign_req <= 1'b1;
                    end else
                        since_sign <= since_sign + 8'd1;
                end else
                    credit <= credit + 48'd1;
            end else if (dn) begin
                if (credit != CMIN)
                    credit <= credit - 48'd1;
            end
        end
    end
endmodule
