// EC-MINT1 top. Schedule counter plus a sign start pulse.
// Key register has no runtime read port. doc-1.0.
module ec_mint1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        cf_in,
    input  wire        zeroize,
    input  wire        prov_cs,
    input  wire        prov_sck,
    input  wire        prov_mosi,
    output wire        prov_miso,
    output wire        tx,
    output wire        mint
);
    wire cf_sync;
    reg cf_d0, cf_d1, cf_d2;
    reg [31:0] watt_hours;
    reg [15:0] residual;
    reg [15:0] tokens;
    reg mint_r;
    reg [255:0] key_reg;
    reg key_locked;
    reg [8:0] prov_count;
    localparam [15:0] Q = 16'd1000;

    assign cf_sync = cf_d1 & ~cf_d2;
    assign mint = mint_r;
    assign prov_miso = key_locked;
    assign tx = 1'b1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cf_d0 <= 1'b0;
            cf_d1 <= 1'b0;
            cf_d2 <= 1'b0;
            watt_hours <= 32'd0;
            residual <= 16'd0;
            tokens <= 16'd0;
            mint_r <= 1'b0;
            key_reg <= 256'd0;
            key_locked <= 1'b0;
            prov_count <= 9'd0;
        end else if (zeroize) begin
            key_reg <= 256'd0;
            key_locked <= 1'b0;
            residual <= 16'd0;
            mint_r <= 1'b0;
        end else begin
            cf_d0 <= cf_in;
            cf_d1 <= cf_d0;
            cf_d2 <= cf_d1;
            mint_r <= 1'b0;
            if (!key_locked && prov_cs && prov_sck) begin
                key_reg <= {key_reg[254:0], prov_mosi};
                if (prov_count == 9'd255)
                    key_locked <= 1'b1;
                else
                    prov_count <= prov_count + 9'd1;
            end
            if (cf_sync) begin
                watt_hours <= watt_hours + 32'd1;
                if (residual + 16'd1 >= Q) begin
                    residual <= residual + 16'd1 - Q;
                    tokens <= tokens + 16'd1;
                    mint_r <= 1'b1;
                end else begin
                    residual <= residual + 16'd1;
                end
            end
        end
    end
endmodule
