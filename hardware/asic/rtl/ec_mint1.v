// EC-MINT1. Hardwired watt-hour schedule plus the only SPI master the
// signer ever sees. The ML-DSA private key is not in this die.
// 16.000 MHz CMOS clock on XI. No on-die Pierce oscillator.
// doc-1.1
module ec_mint1 #(
    parameter integer SIG_BYTES = 2420
) (
    input  wire XI,
    input  wire RST_N,
    input  wire CF_IN,
    input  wire ZEROIZE,
    output wire MINT,
    output wire UART_TX,
    output wire QS_SCK,
    output wire QS_MOSI,
    input  wire QS_MISO,
    output wire QS_CS_N,
    output wire QS_RST_N,
    output wire STP_SCK,
    output wire STP_MOSI,
    input  wire STP_MISO,
    output wire STP_CS,
    input  wire PROV_CS,
    input  wire PROV_SCK,
    input  wire PROV_MOSI,
    output wire PROV_MISO,
    output wire CAL_LOCKED
);
    localparam integer ROM_BYTES = 256;
    localparam integer MSG_BYTES = 32;

    reg [7:0] rom [0:ROM_BYTES-1];
    reg [7:0] msg [0:MSG_BYTES-1];
    reg [7:0] sigm [0:SIG_BYTES-1];
    reg       locked;
    integer   ini;
    initial begin
        locked = 1'b0;
        for (ini = 0; ini < ROM_BYTES; ini = ini + 1)
            rom[ini] = 8'h00;
        rom[0] = 8'hA5;
        rom[1] = 8'h5A;
        rom[2] = 8'h00; // empty frame list: do not arm
    end

    reg cf0, cf1, cf2;
    wire cf_rise = cf1 & ~cf2;
    reg count_en;
    wire [31:0] watt_hours;
    wire [15:0] residual;
    wire [15:0] tokens;
    wire        mint_pulse;

    ec_mint1_schedule sched (
        .clk(XI),
        .rst_n(RST_N),
        .cf_rise(cf_rise),
        .zeroize(ZEROIZE),
        .count_en(count_en),
        .watt_hours(watt_hours),
        .residual(residual),
        .tokens(tokens),
        .mint_pulse(mint_pulse)
    );
    assign MINT = mint_pulse;

    reg spi_start;
    reg [7:0] spi_tx;
    wire [7:0] spi_rx;
    wire spi_busy;
    wire spi_sck, spi_mosi;
    reg  which; // 0 STPM32, 1 QS7001
    reg  spi_cs;
    wire spi_miso = which ? QS_MISO : STP_MISO;

    spi_byte spi (
        .clk(XI), .rst_n(RST_N), .start(spi_start), .tx(spi_tx),
        .rx(spi_rx), .busy(spi_busy), .sck(spi_sck), .mosi(spi_mosi),
        .miso(spi_miso)
    );

    assign QS_SCK   = which ? spi_sck  : 1'b0;
    assign QS_MOSI  = which ? spi_mosi : 1'b0;
    assign QS_CS_N  = which ? ~spi_cs  : 1'b1;
    assign STP_SCK  = which ? 1'b0 : spi_sck;
    assign STP_MOSI = which ? 1'b0 : spi_mosi;
    assign STP_CS   = which ? 1'b0 : spi_cs;

    localparam S_BOOT = 3'd0;
    localparam S_IDLE = 3'd1;
    localparam S_SIGN = 3'd2;
    localparam S_UART = 3'd3;
    localparam S_WIPE = 3'd4;
    localparam S_DEAD = 3'd5;

    reg [2:0] state;
    reg [8:0] rom_i;
    reg [7:0] frame_left;
    reg       boot_send;
    reg [15:0] idx;
    reg [7:0] crc;
    reg       qs_rst;
    reg [8:0] prov_addr;
    reg       prov_phase;
    reg [7:0] meter_id0, meter_id1, meter_id2, meter_id3;
    reg       sign_pending;
    reg [31:0] snap_w;
    reg [15:0] snap_n;

    reg uart_tx_r;
    reg [15:0] uart_i, uart_n;
    reg [3:0] uart_bit;
    reg [7:0] uart_div, uart_sh;
    assign UART_TX = uart_tx_r;
    assign QS_RST_N = qs_rst;
    assign PROV_MISO = locked;
    assign CAL_LOCKED = locked;

    function [7:0] crc8;
        input [7:0] c, d;
        integer k;
        reg [7:0] x;
        begin
            x = c ^ d;
            for (k = 0; k < 8; k = k + 1)
                x = x[7] ? ({x[6:0], 1'b0} ^ 8'h07) : {x[6:0], 1'b0};
            crc8 = x;
        end
    endfunction

    always @(posedge XI or negedge RST_N) begin
        if (!RST_N) begin
            cf0 <= 0; cf1 <= 0; cf2 <= 0;
            count_en <= 0; state <= S_BOOT; which <= 0; spi_cs <= 0;
            spi_start <= 0; spi_tx <= 0; rom_i <= 0; frame_left <= 0;
            boot_send <= 0; idx <= 0; crc <= 0; qs_rst <= 1;
            prov_addr <= 0; prov_phase <= 0;
            meter_id0 <= 0; meter_id1 <= 0; meter_id2 <= 0; meter_id3 <= 1;
            sign_pending <= 0; snap_w <= 0; snap_n <= 0;
            uart_tx_r <= 1; uart_i <= 0; uart_n <= 0; uart_bit <= 0;
            uart_div <= 0; uart_sh <= 0;
        end else begin
            cf0 <= CF_IN; cf1 <= cf0; cf2 <= cf1;
            spi_start <= 1'b0;

            if (!locked && PROV_CS && PROV_SCK && !prov_phase) begin
                rom[prov_addr[7:0]] <= {rom[prov_addr[7:0]][6:0], PROV_MOSI};
                prov_phase <= 1'b1;
            end else if (!locked && PROV_CS && !PROV_SCK && prov_phase) begin
                prov_phase <= 1'b0;
                if (prov_addr == 9'd255) begin
                    locked <= 1'b1;
                    meter_id0 <= rom[3];
                    meter_id1 <= rom[4];
                    meter_id2 <= rom[5];
                    meter_id3 <= rom[6];
                end else
                    prov_addr <= prov_addr + 9'd1;
            end

            if (mint_pulse) begin
                sign_pending <= 1'b1;
                snap_w <= watt_hours + 32'd1;
                snap_n <= tokens + 16'd1;
            end

            case (state)
            S_BOOT: begin
                which <= 1'b0;
                if (!locked) begin
                    count_en <= 1'b0;
                end else if (rom_i == 0 && rom[2] == 8'h00) begin
                    count_en <= 1'b0; // factory image not loaded
                end else if (!boot_send && !spi_busy && !spi_cs && frame_left == 0) begin
                    // ROM layout after the 7-byte header (sync, sync, id x4, flags):
                    // frames start at byte 7. A 0x00 length ends the list.
                    if (rom_i == 0)
                        rom_i <= 9'd7;
                    else if (rom[rom_i] == 8'h00) begin
                        count_en <= 1'b1;
                        state <= S_IDLE;
                    end else begin
                        frame_left <= rom[rom_i];
                        rom_i <= rom_i + 9'd1;
                        spi_cs <= 1'b1;
                    end
                end else if (spi_cs && frame_left != 0 && !spi_busy && !spi_start) begin
                    spi_tx <= rom[rom_i];
                    spi_start <= 1'b1;
                    boot_send <= 1'b1;
                    rom_i <= rom_i + 9'd1;
                    frame_left <= frame_left - 8'd1;
                end else if (boot_send && !spi_busy && !spi_start) begin
                    boot_send <= 1'b0;
                    if (frame_left == 0)
                        spi_cs <= 1'b0;
                end
            end
            S_IDLE: begin
                if (sign_pending) begin
                    msg[0] <= meter_id0; msg[1] <= meter_id1;
                    msg[2] <= meter_id2; msg[3] <= meter_id3;
                    msg[4] <= 8'h00; msg[5] <= 8'h00; msg[6] <= 8'h00; msg[7] <= 8'h00;
                    msg[8] <= 8'h00; msg[9] <= 8'h00; msg[10] <= 8'h00; msg[11] <= 8'h00;
                    msg[12] <= 8'h00; msg[13] <= 8'h00; msg[14] <= 8'h03; msg[15] <= 8'hE8;
                    msg[16] <= snap_n[15:8]; msg[17] <= snap_n[7:0];
                    msg[18] <= snap_w[31:24]; msg[19] <= snap_w[23:16];
                    msg[20] <= snap_w[15:8]; msg[21] <= snap_w[7:0];
                    msg[22] <= residual[15:8]; msg[23] <= residual[7:0];
                    msg[24] <= 8'h22;
                    msg[25] <= 8'h00; msg[26] <= 8'h00; msg[27] <= 8'h00;
                    msg[28] <= 8'h00; msg[29] <= 8'h00; msg[30] <= 8'h00; msg[31] <= 8'h00;
                    sign_pending <= 1'b0;
                    which <= 1'b1;
                    spi_cs <= 1'b1;
                    idx <= 0;
                    crc <= 8'h00;
                    state <= S_SIGN;
                end
            end
            S_SIGN: begin
                if (!spi_busy && !spi_start) begin
                    if (idx == 0) begin
                        spi_tx <= 8'hA1; spi_start <= 1; idx <= 1;
                    end else if (idx <= MSG_BYTES) begin
                        spi_tx <= msg[idx - 1]; spi_start <= 1;
                        crc <= crc8(crc, msg[idx - 1]);
                        idx <= idx + 16'd1;
                    end else if (idx == MSG_BYTES + 1) begin
                        spi_tx <= crc; spi_start <= 1; idx <= idx + 16'd1;
                    end else if (idx < (MSG_BYTES + 2 + SIG_BYTES)) begin
                        spi_tx <= 8'h00; spi_start <= 1;
                        // previous dummy clocks the signature byte in on completion;
                        // capture below uses spi_rx one byte behind, so the first
                        // signature index stores on the following cycle. The byte
                        // captured here is the one whose transfer just finished.
                        if (idx > (MSG_BYTES + 2))
                            sigm[idx - (MSG_BYTES + 3)] <= spi_rx;
                        idx <= idx + 16'd1;
                    end else begin
                        sigm[SIG_BYTES-1] <= spi_rx;
                        spi_cs <= 1'b0;
                        uart_i <= 0;
                        uart_n <= MSG_BYTES + SIG_BYTES;
                        uart_bit <= 0;
                        uart_div <= 0;
                        uart_tx_r <= 1'b1;
                        state <= S_UART;
                    end
                end
            end
            S_UART: begin
                if (uart_div == 8'd138) begin
                    uart_div <= 0;
                    if (uart_bit == 0) begin
                        uart_tx_r <= 1'b0;
                        uart_sh <= (uart_i < MSG_BYTES) ? msg[uart_i] : sigm[uart_i - MSG_BYTES];
                        uart_bit <= 4'd1;
                    end else if (uart_bit <= 8) begin
                        uart_tx_r <= uart_sh[0];
                        uart_sh <= {1'b0, uart_sh[7:1]};
                        uart_bit <= uart_bit + 4'd1;
                    end else if (uart_bit == 9) begin
                        uart_tx_r <= 1'b1;
                        uart_bit <= 4'd10;
                    end else begin
                        uart_bit <= 0;
                        if (uart_i + 16'd1 == uart_n)
                            state <= S_IDLE;
                        else
                            uart_i <= uart_i + 16'd1;
                    end
                end else
                    uart_div <= uart_div + 8'd1;
            end
            S_WIPE: begin
                which <= 1'b1;
                count_en <= 1'b0;
                if (!spi_cs) begin
                    spi_cs <= 1'b1;
                    idx <= 0;
                end else if (!spi_busy && !spi_start) begin
                    if (idx < 2) begin
                        spi_tx <= 8'h5C; spi_start <= 1; idx <= idx + 16'd1;
                    end else begin
                        spi_cs <= 1'b0;
                        qs_rst <= 1'b0;
                        state <= S_DEAD;
                    end
                end
            end
            default: begin
                qs_rst <= 1'b0;
                spi_cs <= 1'b0;
                count_en <= 1'b0;
                uart_tx_r <= 1'b1;
            end
            endcase

            if (ZEROIZE && state != S_DEAD && state != S_WIPE)
                state <= S_WIPE;

            if (state == S_WIPE || state == S_DEAD || ZEROIZE)
                count_en <= 1'b0;
        end
    end
endmodule
