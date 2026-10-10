// EC-MINT1, v0.0.1 (doc-1.4).
// Hardwired net-export watt-hour schedule, the only SPI master the signer
// ever sees, and a power-fail-safe FRAM image of the counters and of the
// factory calibration transcript. The ML-DSA private key is not in this die.
// 16.000 MHz CMOS clock on XI. No on-die Pierce oscillator.
//
// What changed from doc-1.1, and why:
//  - Counters, sequence number and the calibration image live in an
//    external FRAM (FM25V02A). doc-1.1 kept W, r and the "locked" boot ROM
//    in flops, so the first power cut reset W to zero (the ledger chain then
//    rejected every later record) and erased the calibration (the meter
//    never armed again).
//  - Two pulse inputs, export and import. Tokens follow the net-export
//    high-water mark, so a grid-to-battery-to-grid loop mints nothing.
//  - 48-bit cumulative registers. doc-1.1 wrapped n at 65 535 tokens.
//  - The signature is streamed QS7001 -> UART one byte at a time instead of
//    being held in a 2420-byte flop array, and the signer is polled for a
//    ready byte (0x5A) before the signature is clocked. doc-1.1 clocked the
//    signature out with no wait for the signing time.
//  - One record per token (SIGN_EVERY = 1), so every kWh is signed and
//    credited on its own. A token minted while a record is still being
//    signed sets sign_pending again; the next record carries both, because
//    every field is cumulative. Nothing is lost when tokens come faster
//    than about one per 1.3 s (a site above roughly 2.7 MW).
//  - The STPM32 is put in SPI mode on its EN rising edge with SCS low, and
//    STP_CS_N is active low.
//
// What changed in doc-1.4, and why (docs/grid-operator.md):
//  - Re-send. After RESEND_S seconds with no record, the die signs the last
//    token record again under a new seq. A frame dropped on the way to the
//    ledger (by a relay that the grid operator runs, say) comes back without
//    a receive path, and a live meter is heard from at least once a day.
//  - Tamper record. On ZEROIZE the die still sends 5C 5C first, so the meter
//    key is gone within microseconds. Then it sends A7 and a record of kind 1
//    over the counters as they stand; the QS7001 signs it with a separate
//    tamper key and erases that key. The ledger can then tell a cover opened
//    under power from a meter that went quiet or was revoked.
//  - Role 3, LOAD: the same board, wired so that site consumption flows
//    generator stud to grid stud. Its tokens count consumed kWh. It mints
//    nothing; the ledger uses it for the GEN = GRID + LOAD energy balance.
//
// FRAM map (byte addresses):
//   0x0000 state slot A, 36 bytes   0x0040 state slot B, 36 bytes
//   0x0100 calibration image, 256 bytes
//   0x0200 'L' 'K' crc16_hi crc16_lo  (lock marker over the image)
// State slot: EC 01 gen[4] e_exp[6] e_imp[6] tokens[6] credit[6] seq[4]
//             since[1] crc8[1]. Slots alternate on gen; boot takes the
//             valid slot with the larger gen.
//
// Signed record, 32 bytes, big-endian fields:
//   0-3 meter id   4 {version=1, role}   5 class 0x22   6-9 seq
//   10-15 e_exp Wh   16-21 e_imp Wh   22-27 tokens (cumulative)
//   28-29 CRC-16 of the calibration image   30 kind (0 token, 1 tamper)
//   31 zero
// UART frame: EC 01, the 32-byte record, then SIG_BYTES signature bytes.
module ec_mint1 #(
    parameter [15:0] Q          = 16'd1000,  // pulses (Wh) per token
    parameter [7:0]  SIGN_EVERY = 8'd1,      // tokens per signed record: one per kWh
    parameter integer SIG_BYTES = 2420,      // ML-DSA-44; 4627 for ML-DSA-87
    parameter integer UART_DIV  = 139,
    parameter integer T_WAIT    = 16000,     // 1 ms STPM32 select timing
    parameter integer POLL_MAX  = 1000000,   // about 1.1 s of ready polls
    parameter integer TICK      = 16000000,  // clocks per second
    parameter integer RESEND_S  = 86400      // re-send after a day with no record
) (
    input  wire XI,
    input  wire RST_N,
    input  wire CF_EXP,
    input  wire CF_IMP,
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
    output wire STP_CS_N,
    output wire STP_EN,
    output wire FR_SCK,
    output wire FR_MOSI,
    input  wire FR_MISO,
    output wire FR_CS_N,
    input  wire PROV_CS,
    input  wire PROV_SCK,
    input  wire PROV_MOSI,
    output wire PROV_MISO,
    output wire CAL_LOCKED
);
    // ------------------------------------------------------------------
    // Input synchronizers
    reg [2:0] ce_s, ci_s, z_s, pcs_s, psck_s, pmosi_s;
    always @(posedge XI or negedge RST_N) begin
        if (!RST_N) begin
            ce_s <= 3'b000; ci_s <= 3'b000; z_s <= 3'b000;
            pcs_s <= 3'b000; psck_s <= 3'b000; pmosi_s <= 3'b000;
        end else begin
            ce_s <= {ce_s[1:0], CF_EXP};
            ci_s <= {ci_s[1:0], CF_IMP};
            z_s <= {z_s[1:0], ZEROIZE};
            pcs_s <= {pcs_s[1:0], PROV_CS};
            psck_s <= {psck_s[1:0], PROV_SCK};
            pmosi_s <= {pmosi_s[1:0], PROV_MOSI};
        end
    end
    wire exp_rise = ce_s[1] & ~ce_s[2];
    wire imp_rise = ci_s[1] & ~ci_s[2];
    wire zeroize  = z_s[1];
    wire prov_rise = pcs_s[1] & psck_s[1] & ~psck_s[2];

    // ------------------------------------------------------------------
    // CRC helpers
    function [7:0] crc8;            // poly 0x07, init 0
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

    function [15:0] crc16;          // CCITT-FALSE: poly 0x1021, init 0xFFFF
        input [15:0] c;
        input [7:0]  d;
        integer k;
        reg [15:0] x;
        begin
            x = c ^ {d, 8'h00};
            for (k = 0; k < 8; k = k + 1)
                x = x[15] ? ({x[14:0], 1'b0} ^ 16'h1021) : {x[14:0], 1'b0};
            crc16 = x;
        end
    endfunction

    // ------------------------------------------------------------------
    // Schedule
    reg         count_en;
    reg         ld;
    reg  [47:0] ld_exp, ld_imp, ld_tok, ld_cred;
    reg  [7:0]  ld_since;
    wire [47:0] e_exp, e_imp, tokens, credit;
    wire [7:0]  since_sign;
    wire        mint_pulse, sign_req, changed;

    ec_mint1_schedule #(.Q(Q), .SIGN_EVERY(SIGN_EVERY)) sched (
        .clk(XI), .rst_n(RST_N), .count_en(count_en),
        .exp_rise(exp_rise), .imp_rise(imp_rise),
        .load(ld), .ld_exp(ld_exp), .ld_imp(ld_imp), .ld_tok(ld_tok),
        .ld_credit(ld_cred), .ld_since(ld_since),
        .e_exp(e_exp), .e_imp(e_imp), .tokens(tokens), .credit(credit),
        .since_sign(since_sign), .mint_pulse(mint_pulse),
        .sign_req(sign_req), .changed(changed)
    );
    assign MINT = mint_pulse;

    // ------------------------------------------------------------------
    // Three SPI byte engines: FRAM, STPM32, QS7001. Separate pins, so the
    // signer bus is never shared.
    reg        fr_start, st_start, qs_start;
    reg  [7:0] fr_tx, st_tx, qs_tx;
    wire [7:0] fr_rx, st_rx, qs_rx;
    wire       fr_busy, st_busy, qs_busy, fr_done, st_done, qs_done;
    wire       fr_sck, st_sck, qs_sck, fr_mosi, st_mosi, qs_mosi;
    reg        fr_cs, st_cs, qs_cs, st_en, qs_rst_n;

    spi_byte u_fr (.clk(XI), .rst_n(RST_N), .start(fr_start), .tx(fr_tx), .rx(fr_rx),
                   .busy(fr_busy), .done(fr_done), .sck(fr_sck), .mosi(fr_mosi), .miso(FR_MISO));
    spi_byte u_st (.clk(XI), .rst_n(RST_N), .start(st_start), .tx(st_tx), .rx(st_rx),
                   .busy(st_busy), .done(st_done), .sck(st_sck), .mosi(st_mosi), .miso(STP_MISO));
    spi_byte u_qs (.clk(XI), .rst_n(RST_N), .start(qs_start), .tx(qs_tx), .rx(qs_rx),
                   .busy(qs_busy), .done(qs_done), .sck(qs_sck), .mosi(qs_mosi), .miso(QS_MISO));

    assign FR_SCK = fr_sck;   assign FR_MOSI = fr_mosi;   assign FR_CS_N = ~fr_cs;
    assign STP_SCK = st_sck;  assign STP_MOSI = st_mosi;  assign STP_CS_N = ~st_cs;
    assign STP_EN = st_en;
    assign QS_SCK = qs_sck;   assign QS_MOSI = qs_mosi;   assign QS_CS_N = ~qs_cs;
    assign QS_RST_N = qs_rst_n;

    // ------------------------------------------------------------------
    // UART
    reg        u_start;
    reg  [7:0] u_data;
    wire       u_busy, u_done;
    uart_tx #(.DIV(UART_DIV)) u_uart (.clk(XI), .rst_n(RST_N), .start(u_start),
        .data(u_data), .tx(UART_TX), .busy(u_busy), .done(u_done));

    // ------------------------------------------------------------------
    // Calibration image (cached from FRAM) and identity
    reg [7:0]  rom [0:255];
    reg        locked;
    reg [15:0] cal_crc;
    reg [7:0]  role;
    reg [31:0] meter_id;
    assign CAL_LOCKED = locked;
    assign PROV_MISO = locked;

    // Provisioning shift register: 256 bytes, MSB first, on PROV_SCK rise
    reg [10:0] prov_bit;
    reg [7:0]  prov_sh;
    reg        prov_done;

    // ------------------------------------------------------------------
    // Persistent state
    reg [31:0] seq, gen;
    reg        dirty;

    // ------------------------------------------------------------------
    // Boot FSM, FRAM persist FSM, sign FSM
    localparam B_RDROM = 4'd0,  B_PROV = 4'd1,  B_PCRC = 4'd2,  B_WREN1 = 4'd3,
               B_WRROM = 4'd4,  B_RDST = 4'd5,  B_LOAD = 4'd6,  B_HDR = 4'd7,
               B_SEL   = 4'd8,  B_REPLAY = 4'd9, B_DONE = 4'd10, B_HALT = 4'd11;
    reg [3:0]  bst;
    reg [9:0]  bi;           // byte index inside a FRAM transaction
    reg        fr_wait;      // a FRAM byte is in flight
    reg        gap;          // CS high between two FRAM commands
    reg [15:0] crc_acc;
    reg [7:0]  crc_s;
    reg [287:0] sh;          // one state slot as read
    reg        slot;         // 0 = A, 1 = B
    reg        have;
    reg [31:0] b_gen, b_seq;
    reg [47:0] b_exp, b_imp, b_tok, b_cred;
    reg [7:0]  b_since;
    reg [7:0]  mk0, mk1, mk2;
    reg [15:0] tw;           // STPM32 select timer
    reg [1:0]  selph;
    reg [8:0]  ri;           // replay index into rom
    reg [7:0]  fl;           // bytes left in this replay frame
    reg        st_wait;
    reg        booted;

    // Persist FSM
    localparam P_IDLE = 2'd0, P_WREN = 2'd1, P_GAP = 2'd2, P_WR = 2'd3;
    reg [1:0]  pst;
    reg [5:0]  pi;
    reg        p_wait;
    reg [31:0] s_gen, s_seq;
    reg [47:0] s_exp, s_imp, s_tok, s_cred;
    reg [7:0]  s_since, p_crc;

    // Sign FSM
    localparam S_IDLE = 4'd0, S_CMD = 4'd1, S_POLL = 4'd2, S_HDR = 4'd3,
               S_SIGQ = 4'd4, S_SIGU = 4'd5, S_END = 4'd6, S_W0 = 4'd7,
               S_W1 = 4'd8, S_DEAD = 4'd9, S_TG = 4'd10;
    reg [3:0]  sst;
    reg [5:0]  si;
    reg [12:0] sig_i;
    reg [19:0] polls;
    reg        q_wait, u_wait;
    reg        sign_pending;
    reg [7:0]  m_crc;
    reg [31:0] m_seq;
    reg [47:0] m_exp, m_imp, m_tok;
    reg [7:0]  m_kind;       // record byte 30: 0 token, 1 tamper
    reg [7:0]  m_cmd;        // A1 sign with the meter key, A7 tamper key
    reg        have_m;       // m_* hold a record the signer accepted
    reg        tomb;         // the record in flight is the tamper record
    reg        wipe_done;    // 5C 5C has been sent

    // Re-send timer: seconds since the last record was started.
    reg [31:0] tick_c, idle_s;

    // Byte i of the record being signed
    function [7:0] msg_byte;
        input [5:0] i;
        begin
            case (i)
            6'd0:  msg_byte = meter_id[31:24];
            6'd1:  msg_byte = meter_id[23:16];
            6'd2:  msg_byte = meter_id[15:8];
            6'd3:  msg_byte = meter_id[7:0];
            6'd4:  msg_byte = {4'h1, role[3:0]};
            6'd5:  msg_byte = 8'h22;
            6'd6:  msg_byte = m_seq[31:24];
            6'd7:  msg_byte = m_seq[23:16];
            6'd8:  msg_byte = m_seq[15:8];
            6'd9:  msg_byte = m_seq[7:0];
            6'd10: msg_byte = m_exp[47:40];
            6'd11: msg_byte = m_exp[39:32];
            6'd12: msg_byte = m_exp[31:24];
            6'd13: msg_byte = m_exp[23:16];
            6'd14: msg_byte = m_exp[15:8];
            6'd15: msg_byte = m_exp[7:0];
            6'd16: msg_byte = m_imp[47:40];
            6'd17: msg_byte = m_imp[39:32];
            6'd18: msg_byte = m_imp[31:24];
            6'd19: msg_byte = m_imp[23:16];
            6'd20: msg_byte = m_imp[15:8];
            6'd21: msg_byte = m_imp[7:0];
            6'd22: msg_byte = m_tok[47:40];
            6'd23: msg_byte = m_tok[39:32];
            6'd24: msg_byte = m_tok[31:24];
            6'd25: msg_byte = m_tok[23:16];
            6'd26: msg_byte = m_tok[15:8];
            6'd27: msg_byte = m_tok[7:0];
            6'd28: msg_byte = cal_crc[15:8];
            6'd29: msg_byte = cal_crc[7:0];
            6'd30: msg_byte = m_kind;
            default: msg_byte = 8'h00;
            endcase
        end
    endfunction

    // Byte i of the state slot being written (i < 35); byte 35 is the CRC
    function [7:0] slot_byte;
        input [5:0] i;
        begin
            case (i)
            6'd0:  slot_byte = 8'hEC;
            6'd1:  slot_byte = 8'h01;
            6'd2:  slot_byte = s_gen[31:24];
            6'd3:  slot_byte = s_gen[23:16];
            6'd4:  slot_byte = s_gen[15:8];
            6'd5:  slot_byte = s_gen[7:0];
            6'd6:  slot_byte = s_exp[47:40];
            6'd7:  slot_byte = s_exp[39:32];
            6'd8:  slot_byte = s_exp[31:24];
            6'd9:  slot_byte = s_exp[23:16];
            6'd10: slot_byte = s_exp[15:8];
            6'd11: slot_byte = s_exp[7:0];
            6'd12: slot_byte = s_imp[47:40];
            6'd13: slot_byte = s_imp[39:32];
            6'd14: slot_byte = s_imp[31:24];
            6'd15: slot_byte = s_imp[23:16];
            6'd16: slot_byte = s_imp[15:8];
            6'd17: slot_byte = s_imp[7:0];
            6'd18: slot_byte = s_tok[47:40];
            6'd19: slot_byte = s_tok[39:32];
            6'd20: slot_byte = s_tok[31:24];
            6'd21: slot_byte = s_tok[23:16];
            6'd22: slot_byte = s_tok[15:8];
            6'd23: slot_byte = s_tok[7:0];
            6'd24: slot_byte = s_cred[47:40];
            6'd25: slot_byte = s_cred[39:32];
            6'd26: slot_byte = s_cred[31:24];
            6'd27: slot_byte = s_cred[23:16];
            6'd28: slot_byte = s_cred[15:8];
            6'd29: slot_byte = s_cred[7:0];
            6'd30: slot_byte = s_seq[31:24];
            6'd31: slot_byte = s_seq[23:16];
            6'd32: slot_byte = s_seq[15:8];
            6'd33: slot_byte = s_seq[7:0];
            6'd34: slot_byte = s_since;
            default: slot_byte = 8'h00;
            endcase
        end
    endfunction

    // Decoded view of the slot shift register (byte 0 is the oldest)
    wire        sl_ok_hdr = (sh[287:280] == 8'hEC) && (sh[279:272] == 8'h01);
    wire [31:0] sl_gen  = sh[271:240];
    wire [47:0] sl_exp  = sh[239:192];
    wire [47:0] sl_imp  = sh[191:144];
    wire [47:0] sl_tok  = sh[143:96];
    wire [47:0] sl_cred = sh[95:48];
    wire [31:0] sl_seq  = sh[47:16];
    wire [7:0]  sl_since = sh[15:8];
    wire [7:0]  sl_crc  = sh[7:0];

    always @(posedge XI or negedge RST_N) begin
        if (!RST_N) begin
            count_en <= 1'b0; ld <= 1'b0;
            ld_exp <= 48'd0; ld_imp <= 48'd0; ld_tok <= 48'd0; ld_cred <= 48'd0; ld_since <= 8'd0;
            fr_start <= 1'b0; st_start <= 1'b0; qs_start <= 1'b0;
            fr_tx <= 8'd0; st_tx <= 8'd0; qs_tx <= 8'd0;
            fr_cs <= 1'b0; st_cs <= 1'b0; qs_cs <= 1'b0; st_en <= 1'b0; qs_rst_n <= 1'b1;
            u_start <= 1'b0; u_data <= 8'd0;
            locked <= 1'b0; cal_crc <= 16'd0; role <= 8'd0; meter_id <= 32'd0;
            prov_bit <= 11'd0; prov_sh <= 8'd0; prov_done <= 1'b0;
            seq <= 32'd0; gen <= 32'd0; dirty <= 1'b0;
            bst <= B_RDROM; bi <= 10'd0; fr_wait <= 1'b0; gap <= 1'b0;
            crc_acc <= 16'hFFFF; crc_s <= 8'd0; sh <= 288'd0; slot <= 1'b0; have <= 1'b0;
            b_gen <= 32'd0; b_seq <= 32'd0; b_exp <= 48'd0; b_imp <= 48'd0; b_tok <= 48'd0;
            b_cred <= 48'd0; b_since <= 8'd0; mk0 <= 8'd0; mk1 <= 8'd0; mk2 <= 8'd0;
            tw <= 16'd0; selph <= 2'd0; ri <= 9'd0; fl <= 8'd0; st_wait <= 1'b0; booted <= 1'b0;
            pst <= P_IDLE; pi <= 6'd0; p_wait <= 1'b0;
            s_gen <= 32'd0; s_seq <= 32'd0; s_exp <= 48'd0; s_imp <= 48'd0; s_tok <= 48'd0;
            s_cred <= 48'd0; s_since <= 8'd0; p_crc <= 8'd0;
            sst <= S_IDLE; si <= 6'd0; sig_i <= 13'd0; polls <= 20'd0;
            q_wait <= 1'b0; u_wait <= 1'b0; sign_pending <= 1'b0; m_crc <= 8'd0;
            m_seq <= 32'd0; m_exp <= 48'd0; m_imp <= 48'd0; m_tok <= 48'd0;
            m_kind <= 8'd0; m_cmd <= 8'hA1; have_m <= 1'b0; tomb <= 1'b0; wipe_done <= 1'b0;
            tick_c <= 32'd0; idle_s <= 32'd0;
        end else begin
            fr_start <= 1'b0;
            st_start <= 1'b0;
            qs_start <= 1'b0;
            u_start <= 1'b0;
            ld <= 1'b0;

            if (changed)
                dirty <= 1'b1;
            if (sign_req)
                sign_pending <= 1'b1;

            // ---------------- provisioning shift (before lock only) -------
            if (!locked && bst == B_PROV && !prov_done && prov_rise) begin
                prov_sh <= {prov_sh[6:0], pmosi_s[1]};
                prov_bit <= prov_bit + 11'd1;
                if (prov_bit[2:0] == 3'd7) begin
                    rom[prov_bit[10:3]] <= {prov_sh[6:0], pmosi_s[1]};
                    if (prov_bit[10:3] == 8'd255)
                        prov_done <= 1'b1;
                end
            end

            // ---------------- boot FSM ------------------------------------
            case (bst)
            // Read the calibration image and lock marker from FRAM 0x0100.
            B_RDROM: begin
                if (!fr_cs) begin
                    fr_cs <= 1'b1; bi <= 10'd0; crc_acc <= 16'hFFFF;
                end else if (!fr_wait && !fr_busy) begin
                    fr_tx <= (bi == 10'd0) ? 8'h03 : (bi == 10'd1) ? 8'h01 : 8'h00;
                    fr_start <= 1'b1; fr_wait <= 1'b1;
                end else if (fr_done) begin
                    fr_wait <= 1'b0;
                    if (bi >= 10'd3 && bi < 10'd259) begin
                        rom[bi - 10'd3] <= fr_rx;
                        crc_acc <= crc16(crc_acc, fr_rx);
                    end
                    if (bi == 10'd259) mk0 <= fr_rx;
                    if (bi == 10'd260) mk1 <= fr_rx;
                    if (bi == 10'd261) mk2 <= fr_rx;
                    if (bi == 10'd262) begin
                        fr_cs <= 1'b0;
                        if (mk0 == 8'h4C && mk1 == 8'h4B && {mk2, fr_rx} == crc_acc) begin
                            locked <= 1'b1;
                            cal_crc <= crc_acc;
                            bst <= B_RDST;
                        end else
                            bst <= B_PROV;
                        bi <= 10'd0;
                    end else
                        bi <= bi + 10'd1;
                end
            end
            // Wait for the factory transcript on J5.
            B_PROV: begin
                if (prov_done) begin
                    bst <= B_PCRC; bi <= 10'd0; crc_acc <= 16'hFFFF;
                end
            end
            B_PCRC: begin
                crc_acc <= crc16(crc_acc, rom[bi[7:0]]);
                if (bi == 10'd255) begin
                    bst <= B_WREN1; bi <= 10'd0;
                end else
                    bi <= bi + 10'd1;
            end
            B_WREN1: begin
                if (!fr_cs && !gap) begin
                    fr_cs <= 1'b1;
                end else if (fr_cs && !fr_wait && !fr_busy) begin
                    fr_tx <= 8'h06; fr_start <= 1'b1; fr_wait <= 1'b1;
                end else if (fr_done) begin
                    fr_wait <= 1'b0; fr_cs <= 1'b0; gap <= 1'b1;
                end else if (gap) begin
                    gap <= 1'b0; bst <= B_WRROM; bi <= 10'd0;
                end
            end
            B_WRROM: begin
                if (!fr_cs) begin
                    fr_cs <= 1'b1;
                end else if (!fr_wait && !fr_busy) begin
                    if (bi == 10'd0)       fr_tx <= 8'h02;
                    else if (bi == 10'd1)  fr_tx <= 8'h01;
                    else if (bi == 10'd2)  fr_tx <= 8'h00;
                    else if (bi < 10'd259) fr_tx <= rom[bi - 10'd3];
                    else if (bi == 10'd259) fr_tx <= 8'h4C;
                    else if (bi == 10'd260) fr_tx <= 8'h4B;
                    else if (bi == 10'd261) fr_tx <= crc_acc[15:8];
                    else                    fr_tx <= crc_acc[7:0];
                    fr_start <= 1'b1; fr_wait <= 1'b1;
                end else if (fr_done) begin
                    fr_wait <= 1'b0;
                    if (bi == 10'd262) begin
                        fr_cs <= 1'b0;
                        locked <= 1'b1;
                        cal_crc <= crc_acc;
                        bst <= B_RDST; bi <= 10'd0; slot <= 1'b0; have <= 1'b0;
                    end else
                        bi <= bi + 10'd1;
                end
            end
            // Read slot A (0x0000) then slot B (0x0040).
            B_RDST: begin
                if (!fr_cs && !gap) begin
                    fr_cs <= 1'b1; bi <= 10'd0; crc_s <= 8'd0;
                end else if (gap) begin
                    gap <= 1'b0;
                end else if (!fr_wait && !fr_busy) begin
                    fr_tx <= (bi == 10'd0) ? 8'h03 : (bi == 10'd2) ? {1'b0, slot, 6'd0} : 8'h00;
                    fr_start <= 1'b1; fr_wait <= 1'b1;
                end else if (fr_done) begin
                    fr_wait <= 1'b0;
                    if (bi >= 10'd3) begin
                        sh <= {sh[279:0], fr_rx};
                        if (bi < 10'd38)
                            crc_s <= crc8(crc_s, fr_rx);
                    end
                    if (bi == 10'd38) begin
                        fr_cs <= 1'b0;
                        gap <= 1'b1;
                        bst <= B_LOAD;
                    end else
                        bi <= bi + 10'd1;
                end
            end
            B_LOAD: begin
                // sh now holds one slot. crc_s covers bytes 0..34.
                if (sl_ok_hdr && sl_crc == crc_s && (!have || sl_gen > b_gen)) begin
                    have <= 1'b1;
                    b_gen <= sl_gen; b_exp <= sl_exp; b_imp <= sl_imp; b_tok <= sl_tok;
                    b_cred <= sl_cred; b_seq <= sl_seq; b_since <= sl_since;
                end
                if (!slot) begin
                    slot <= 1'b1;
                    bst <= B_RDST;
                end else
                    bst <= B_HDR;
            end
            B_HDR: begin
                gap <= 1'b0;
                if (have) begin
                    ld <= 1'b1;
                    ld_exp <= b_exp; ld_imp <= b_imp; ld_tok <= b_tok;
                    ld_cred <= b_cred; ld_since <= b_since;
                    seq <= b_seq; gen <= b_gen;
                end
                role <= rom[2];
                meter_id <= {rom[3], rom[4], rom[5], rom[6]};
                if (rom[0] == 8'hA5 && rom[1] == 8'h5A &&
                    (rom[2] == 8'h01 || rom[2] == 8'h02 || rom[2] == 8'h03) &&
                    rom[7] != 8'h00) begin
                    bst <= B_SEL; selph <= 2'd0; tw <= 16'd0;
                end else
                    bst <= B_HALT; // empty or malformed transcript: do not arm
            end
            // STPM32 interface select: SCS low across the EN rising edge.
            B_SEL: begin
                if (tw != T_WAIT[15:0]) begin
                    tw <= tw + 16'd1;
                end else begin
                    tw <= 16'd0;
                    case (selph)
                    2'd0: begin st_cs <= 1'b1; selph <= 2'd1; end
                    2'd1: begin st_en <= 1'b1; selph <= 2'd2; end
                    2'd2: begin st_cs <= 1'b0; selph <= 2'd3; end
                    default: begin bst <= B_REPLAY; ri <= 9'd7; fl <= 8'd0; end
                    endcase
                end
            end
            // Replay the transcript: length byte, then that many bytes with CS low.
            B_REPLAY: begin
                if (fl == 8'd0 && !st_cs) begin
                    if (ri > 9'd255 || rom[ri[7:0]] == 8'h00) begin
                        bst <= B_DONE;
                    end else begin
                        fl <= rom[ri[7:0]];
                        ri <= ri + 9'd1;
                        st_cs <= 1'b1;
                    end
                end else if (st_cs && fl != 8'd0 && !st_wait && !st_busy) begin
                    if (ri > 9'd255) begin
                        st_cs <= 1'b0; bst <= B_HALT;
                    end else begin
                        st_tx <= rom[ri[7:0]]; st_start <= 1'b1; st_wait <= 1'b1;
                        ri <= ri + 9'd1; fl <= fl - 8'd1;
                    end
                end else if (st_done) begin
                    st_wait <= 1'b0;
                    if (fl == 8'd0)
                        st_cs <= 1'b0;
                end
            end
            B_DONE: begin
                booted <= 1'b1;
                if (!zeroize && sst != S_DEAD)
                    count_en <= 1'b1;
            end
            default: begin // B_HALT
                count_en <= 1'b0;
            end
            endcase

            // ---------------- FRAM persist FSM (after boot) ---------------
            if (booted) begin
                case (pst)
                P_IDLE: begin
                    if (dirty && !changed) begin
                        dirty <= 1'b0;
                        s_gen <= gen + 32'd1; gen <= gen + 32'd1;
                        s_exp <= e_exp; s_imp <= e_imp; s_tok <= tokens;
                        s_cred <= credit; s_seq <= seq; s_since <= since_sign;
                        p_crc <= 8'd0; pi <= 6'd0;
                        fr_cs <= 1'b1;
                        pst <= P_WREN;
                    end
                end
                P_WREN: begin
                    if (!p_wait && !fr_busy) begin
                        fr_tx <= 8'h06; fr_start <= 1'b1; p_wait <= 1'b1;
                    end else if (fr_done) begin
                        p_wait <= 1'b0; fr_cs <= 1'b0; pst <= P_GAP;
                    end
                end
                P_GAP: begin
                    fr_cs <= 1'b1; pst <= P_WR; pi <= 6'd0;
                end
                default: begin // P_WR: 02, addr, 36 bytes
                    if (!p_wait && !fr_busy) begin
                        if (pi == 6'd0)       fr_tx <= 8'h02;
                        else if (pi == 6'd1)  fr_tx <= 8'h00;
                        else if (pi == 6'd2)  fr_tx <= {1'b0, s_gen[0], 6'd0};
                        else if (pi < 6'd38)  fr_tx <= slot_byte(pi - 6'd3);
                        else                  fr_tx <= p_crc;
                        if (pi >= 6'd3 && pi < 6'd38)
                            p_crc <= crc8(p_crc, slot_byte(pi - 6'd3));
                        fr_start <= 1'b1; p_wait <= 1'b1;
                    end else if (fr_done) begin
                        p_wait <= 1'b0;
                        if (pi == 6'd38) begin
                            fr_cs <= 1'b0; pst <= P_IDLE;
                        end else
                            pi <= pi + 6'd1;
                    end
                end
                endcase
            end

            // ---------------- re-send timer -------------------------------
            if (booted) begin
                if (tick_c == TICK - 1) begin
                    tick_c <= 32'd0;
                    if (idle_s != RESEND_S)
                        idle_s <= idle_s + 32'd1;
                end else
                    tick_c <= tick_c + 32'd1;
            end

            // ---------------- sign FSM ------------------------------------
            case (sst)
            S_IDLE: begin
                if (booted && count_en && sign_pending && !zeroize) begin
                    sign_pending <= 1'b0;
                    m_seq <= seq + 32'd1;
                    seq <= seq + 32'd1;
                    dirty <= 1'b1;
                    m_exp <= e_exp; m_imp <= e_imp; m_tok <= tokens;
                    m_kind <= 8'd0; m_cmd <= 8'hA1;
                    m_crc <= 8'd0; si <= 6'd0;
                    tick_c <= 32'd0; idle_s <= 32'd0;
                    qs_cs <= 1'b1;
                    sst <= S_CMD;
                end else if (booted && count_en && have_m && idle_s == RESEND_S &&
                             !zeroize) begin
                    // Re-send: the last accepted record's counters, new seq.
                    m_seq <= seq + 32'd1;
                    seq <= seq + 32'd1;
                    dirty <= 1'b1;
                    m_kind <= 8'd0; m_cmd <= 8'hA1;
                    m_crc <= 8'd0; si <= 6'd0;
                    tick_c <= 32'd0; idle_s <= 32'd0;
                    qs_cs <= 1'b1;
                    sst <= S_CMD;
                end
            end
            // A1 (or A7), 32 record bytes, CRC-8
            S_CMD: begin
                if (!q_wait && !qs_busy) begin
                    if (si == 6'd0)
                        qs_tx <= m_cmd;
                    else if (si <= 6'd32) begin
                        qs_tx <= msg_byte(si - 6'd1);
                        m_crc <= crc8(m_crc, msg_byte(si - 6'd1));
                    end else
                        qs_tx <= m_crc;
                    qs_start <= 1'b1; q_wait <= 1'b1;
                end else if (qs_done) begin
                    q_wait <= 1'b0;
                    if (si == 6'd33) begin
                        sst <= S_POLL; polls <= 20'd0;
                    end else
                        si <= si + 6'd1;
                end
            end
            // Clock 00 until the signer answers 5A (signature follows) or EE (refused).
            S_POLL: begin
                if (!q_wait && !qs_busy) begin
                    qs_tx <= 8'h00; qs_start <= 1'b1; q_wait <= 1'b1;
                end else if (qs_done) begin
                    q_wait <= 1'b0;
                    if (qs_rx == 8'h5A) begin
                        sst <= S_HDR; si <= 6'd0;
                        have_m <= !tomb;
                    end else if (qs_rx == 8'hEE || polls == POLL_MAX[19:0]) begin
                        sst <= S_END;
                        have_m <= 1'b0;
                    end else
                        polls <= polls + 20'd1;
                end
            end
            // UART EC 01 and the 32-byte record
            S_HDR: begin
                if (!u_wait && !u_busy) begin
                    u_data <= (si == 6'd0) ? 8'hEC : (si == 6'd1) ? 8'h01 : msg_byte(si - 6'd2);
                    u_start <= 1'b1; u_wait <= 1'b1;
                end else if (u_done) begin
                    u_wait <= 1'b0;
                    if (si == 6'd33) begin
                        sst <= S_SIGQ; sig_i <= 13'd0;
                    end else
                        si <= si + 6'd1;
                end
            end
            // One signature byte from the signer...
            S_SIGQ: begin
                if (!q_wait && !qs_busy) begin
                    qs_tx <= 8'h00; qs_start <= 1'b1; q_wait <= 1'b1;
                end else if (qs_done) begin
                    q_wait <= 1'b0;
                    u_data <= qs_rx; u_start <= 1'b1; u_wait <= 1'b1;
                    sst <= S_SIGU;
                end
            end
            // ...then out of the UART, before the next one is clocked.
            S_SIGU: begin
                if (u_done) begin
                    u_wait <= 1'b0;
                    if (sig_i == SIG_BYTES - 1)
                        sst <= S_END;
                    else begin
                        sig_i <= sig_i + 13'd1;
                        sst <= S_SIGQ;
                    end
                end
            end
            S_END: begin
                qs_cs <= 1'b0;
                sst <= tomb ? S_DEAD : S_IDLE;
            end
            // Wipe: release CS so the signer resets its parser, then 5C 5C.
            S_W0: begin
                qs_cs <= 1'b0;
                if (!qs_busy && !q_wait) begin
                    sst <= S_W1; si <= 6'd0;
                end else if (qs_done)
                    q_wait <= 1'b0;
            end
            S_W1: begin
                if (!qs_cs) begin
                    qs_cs <= 1'b1;
                end else if (!q_wait && !qs_busy) begin
                    if (si < 6'd2) begin
                        qs_tx <= 8'h5C; qs_start <= 1'b1; q_wait <= 1'b1;
                    end else begin
                        qs_cs <= 1'b0;
                        wipe_done <= 1'b1;
                        if (booted) begin
                            // The meter key is gone. Ask for one tamper
                            // record over the counters as they stand.
                            m_seq <= seq + 32'd1;
                            seq <= seq + 32'd1;
                            dirty <= 1'b1;
                            m_exp <= e_exp; m_imp <= e_imp; m_tok <= tokens;
                            m_kind <= 8'd1; m_cmd <= 8'hA7;
                            m_crc <= 8'd0; si <= 6'd0;
                            tomb <= 1'b1;
                            sst <= S_TG;
                        end else begin
                            qs_rst_n <= 1'b0;
                            sst <= S_DEAD;
                        end
                    end
                end else if (qs_done) begin
                    q_wait <= 1'b0;
                    si <= si + 6'd1;
                end
            end
            // CS high for 16 clocks between 5C 5C and A7.
            S_TG: begin
                if (si == 6'd15) begin
                    si <= 6'd0;
                    qs_cs <= 1'b1;
                    sst <= S_CMD;
                end else
                    si <= si + 6'd1;
            end
            default: begin // S_DEAD
                qs_cs <= 1'b0;
                qs_rst_n <= 1'b0;
                count_en <= 1'b0;
            end
            endcase

            if (zeroize) begin
                count_en <= 1'b0;
                sign_pending <= 1'b0;
                if (!wipe_done && sst != S_W0 && sst != S_W1 && sst != S_DEAD)
                    sst <= S_W0;
            end
        end
    end
endmodule
