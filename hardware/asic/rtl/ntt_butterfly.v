// One NTT butterfly. q = 8380417, the ML-DSA prime. doc-1.0.
module ntt_butterfly (
    input  wire [22:0] a,
    input  wire [22:0] b,
    input  wire [22:0] zeta,
    output wire [22:0] a_out,
    output wire [22:0] b_out
);
    localparam [23:0] Q = 24'd8380417;
    wire [45:0] prod = b * zeta;
    wire [23:0] zb = prod % Q;
    wire [23:0] sum = a + zb;
    wire [23:0] diff = a + Q - zb;
    assign a_out = (sum >= Q) ? (sum - Q) : sum[22:0];
    assign b_out = (diff >= Q) ? (diff - Q) : diff[22:0];
endmodule
