// Keccak-f1600 chi step for one lane bit: a' = c xor ((not a) and b).
// Full 24-round permutation is this gate, a rotate ROM, and a round-constant ROM.
// doc-1.0. Round constants are FIPS 202.
module keccak_chi_bit (
    input  wire a,
    input  wire b,
    input  wire c,
    output wire a_next
);
    assign a_next = c ^ ((~a) & b);
endmodule

module keccak_round_const (
    input  wire [4:0] round,
    output reg [63:0] rc
);
    always @* begin
        case (round)
            5'd0:  rc = 64'h0000000000000001;
            5'd1:  rc = 64'h0000000000008082;
            5'd2:  rc = 64'h800000000000808A;
            5'd3:  rc = 64'h8000000080008000;
            5'd4:  rc = 64'h000000000000808B;
            5'd5:  rc = 64'h0000000080000001;
            5'd6:  rc = 64'h8000000080008081;
            5'd7:  rc = 64'h8000000000008009;
            5'd8:  rc = 64'h000000000000008A;
            5'd9:  rc = 64'h0000000000000088;
            5'd10: rc = 64'h0000000080008009;
            5'd11: rc = 64'h000000008000000A;
            5'd12: rc = 64'h000000008000808B;
            5'd13: rc = 64'h800000000000008B;
            5'd14: rc = 64'h8000000000008089;
            5'd15: rc = 64'h8000000000008003;
            5'd16: rc = 64'h8000000000008002;
            5'd17: rc = 64'h8000000000000080;
            5'd18: rc = 64'h000000000000800A;
            5'd19: rc = 64'h800000008000000A;
            5'd20: rc = 64'h8000000080008081;
            5'd21: rc = 64'h8000000000008080;
            5'd22: rc = 64'h0000000080000001;
            default: rc = 64'h8000000080008008;
        endcase
    end
endmodule
