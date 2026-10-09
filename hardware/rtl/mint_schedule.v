// Mint schedule. Synthesizable counter and comparator.
// Wraps a hard ML-DSA engine. Not a tapeout. doc-0.9.
module mint_schedule (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        cf_edge,
    input  wire        zeroize,
    output reg  [31:0] watt_hours,
    output reg  [15:0] residual,
    output reg         mint_pulse,
    output reg  [15:0] tokens_this
);
    localparam [15:0] Q = 16'd1000;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            watt_hours <= 32'd0;
            residual <= 16'd0;
            mint_pulse <= 1'b0;
            tokens_this <= 16'd0;
        end else if (zeroize) begin
            watt_hours <= 32'd0;
            residual <= 16'd0;
            mint_pulse <= 1'b0;
            tokens_this <= 16'd0;
        end else begin
            mint_pulse <= 1'b0;
            tokens_this <= 16'd0;
            if (cf_edge) begin
                watt_hours <= watt_hours + 32'd1;
                if (residual + 16'd1 >= Q) begin
                    residual <= residual + 16'd1 - Q;
                    tokens_this <= 16'd1;
                    mint_pulse <= 1'b1;
                end else begin
                    residual <= residual + 16'd1;
                end
            end
        end
    end
endmodule
