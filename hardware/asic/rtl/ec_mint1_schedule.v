// EC-MINT1 schedule. One token per 1000 accepted watt-hour pulses.
// q, W and r are registers. No host write port exists.
// Synthesizable. No modulo operator.
module ec_mint1_schedule (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        cf_rise,
    input  wire        zeroize,
    input  wire        count_en,
    output reg  [31:0] watt_hours,
    output reg  [15:0] residual,
    output reg  [15:0] tokens,
    output reg         mint_pulse
);
    localparam [15:0] Q = 16'd1000;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            watt_hours <= 32'd0;
            residual   <= 16'd0;
            tokens     <= 16'd0;
            mint_pulse <= 1'b0;
        end else if (zeroize) begin
            mint_pulse <= 1'b0;
        end else begin
            mint_pulse <= 1'b0;
            if (count_en && cf_rise) begin
                watt_hours <= watt_hours + 32'd1;
                if (residual >= (Q - 16'd1)) begin
                    residual   <= 16'd0;
                    tokens     <= tokens + 16'd1;
                    mint_pulse <= 1'b1;
                end else begin
                    residual <= residual + 16'd1;
                end
            end
        end
    end
endmodule
