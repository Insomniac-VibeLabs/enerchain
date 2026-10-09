// Behavioral models for the EC-MINT1 testbench. Not for synthesis.
// They stand in for parts on EC-SEAL1 so the RTL can be run end to end.
`timescale 1ns/1ps

// QS7001 signing oracle, as specified in firmware/qs7001/sign_oracle.c.
// SPI mode 0 slave. A1 + 32 bytes + CRC-8 -> BUSY poll bytes of 00, then
// 5A and SIG_BYTES signature bytes, or EE if the record does not advance
// the last signed sequence number. 5C 5C erases the key for good.
// The "signature" is a deterministic stand-in: sig[i] = m[i%32] ^ i ^ A5.
module qs7001_model #(
    parameter integer SIG_BYTES = 40,
    parameter integer BUSY = 5
) (
    input  wire sck,
    input  wire mosi,
    output reg  miso,
    input  wire cs_n,
    input  wire rst_n
);
    reg [7:0] msg [0:31];
    reg [7:0] rx_sh, out_sh, crc;
    integer bitcnt, n, k, state;
    integer last_seq;
    integer signs, refusals, wipes;
    reg wiped, refuse;
    reg [31:0] rseq;
    localparam CMD = 0, MSG = 1, CRC = 2, RESP = 3, WIPE1 = 4, IGN = 5;

    function [7:0] crc8;
        input [7:0] c, d;
        integer j;
        reg [7:0] x;
        begin
            x = c ^ d;
            for (j = 0; j < 8; j = j + 1)
                x = x[7] ? ({x[6:0], 1'b0} ^ 8'h07) : {x[6:0], 1'b0};
            crc8 = x;
        end
    endfunction

    function [7:0] resp;
        input integer kk;
        begin
            if (kk < BUSY) resp = 8'h00;
            else if (kk == BUSY) resp = refuse ? 8'hEE : 8'h5A;
            else if (refuse) resp = 8'h00;
            else resp = msg[(kk - BUSY - 1) % 32] ^ ((kk - BUSY - 1) & 8'hFF) ^ 8'hA5;
        end
    endfunction

    initial begin
        miso = 1'b0; bitcnt = 0; state = CMD; out_sh = 8'h00; rx_sh = 8'h00;
        last_seq = 0; signs = 0; refusals = 0; wipes = 0; wiped = 1'b0; refuse = 1'b0;
        n = 0; k = 0; crc = 8'h00;
    end

    always @(negedge cs_n) begin
        bitcnt = 0;
        state = wiped ? IGN : CMD;
        out_sh = 8'h00;
        miso = 1'b0;
    end
    always @(posedge cs_n) begin
        state = CMD;
    end

    always @(posedge sck) if (!cs_n) begin
        rx_sh = {rx_sh[6:0], mosi};
        bitcnt = bitcnt + 1;
        if (bitcnt == 8) begin
            bitcnt = 0;
            case (state)
            CMD: begin
                if (rx_sh == 8'hA1) begin state = MSG; n = 0; crc = 8'h00; end
                else if (rx_sh == 8'h5C) state = WIPE1;
                out_sh = 8'h00;
            end
            MSG: begin
                msg[n] = rx_sh; crc = crc8(crc, rx_sh); n = n + 1;
                if (n == 32) state = CRC;
                out_sh = 8'h00;
            end
            CRC: begin
                if (rx_sh != crc) begin
                    state = IGN; out_sh = 8'h00;
                end else begin
                    rseq = {msg[6], msg[7], msg[8], msg[9]};
                    refuse = (rseq <= last_seq);
                    if (refuse) refusals = refusals + 1;
                    else begin last_seq = rseq; signs = signs + 1; end
                    state = RESP; k = 0;
                    out_sh = resp(k); k = k + 1;
                end
            end
            RESP: begin
                out_sh = resp(k); k = k + 1;
            end
            WIPE1: begin
                if (rx_sh == 8'h5C) begin wiped = 1'b1; wipes = wipes + 1; end
                state = IGN; out_sh = 8'h00;
            end
            default: out_sh = 8'h00;
            endcase
        end
    end

    always @(negedge sck) if (!cs_n) begin
        miso = (bitcnt == 0) ? out_sh[7] : out_sh[7 - bitcnt];
    end
endmodule

// FM25V02A-like SPI FRAM. 32 KiB. WREN 06, WRITE 02, READ 03, WRDI 04.
// Memory survives the testbench's power cycles (it is not reset).
module fram_model (
    input  wire sck,
    input  wire mosi,
    output reg  miso,
    input  wire cs_n
);
    reg [7:0] mem [0:32767];
    reg [7:0] rx_sh, out_sh;
    reg wel, wrote;
    integer bitcnt, state, i;
    reg [14:0] addr;
    integer writes;
    localparam OP = 0, AH_W = 1, AL_W = 2, DATA_W = 3, AH_R = 4, AL_R = 5, DATA_R = 6, IGN = 7;

    initial begin
        for (i = 0; i < 32768; i = i + 1) mem[i] = 8'hFF;
        wel = 1'b0; miso = 1'b0; bitcnt = 0; state = OP; writes = 0; wrote = 1'b0;
        out_sh = 8'h00; rx_sh = 8'h00;
    end

    always @(negedge cs_n) begin
        bitcnt = 0; state = OP; out_sh = 8'h00; wrote = 1'b0;
    end
    always @(posedge cs_n) begin
        if (wrote) begin wel = 1'b0; writes = writes + 1; end
        state = OP;
    end

    always @(posedge sck) if (!cs_n) begin
        rx_sh = {rx_sh[6:0], mosi};
        bitcnt = bitcnt + 1;
        if (bitcnt == 8) begin
            bitcnt = 0;
            case (state)
            OP: begin
                if (rx_sh == 8'h06) wel = 1'b1;
                else if (rx_sh == 8'h04) wel = 1'b0;
                else if (rx_sh == 8'h02) state = AH_W;
                else if (rx_sh == 8'h03) state = AH_R;
                else state = IGN;
            end
            AH_W: begin addr[14:8] = rx_sh[6:0]; state = AL_W; end
            AL_W: begin addr[7:0] = rx_sh; state = DATA_W; end
            DATA_W: begin
                if (wel) begin mem[addr] = rx_sh; wrote = 1'b1; end
                addr = addr + 1;
            end
            AH_R: begin addr[14:8] = rx_sh[6:0]; state = AL_R; end
            AL_R: begin addr[7:0] = rx_sh; out_sh = mem[addr]; addr = addr + 1; state = DATA_R; end
            DATA_R: begin out_sh = mem[addr]; addr = addr + 1; end
            default: ;
            endcase
        end
    end

    always @(negedge sck) if (!cs_n) begin
        miso = (bitcnt == 0) ? out_sh[7] : out_sh[7 - bitcnt];
    end
endmodule

// STPM32 configuration port, as far as this die drives it: records the
// level of SCS at the EN rising edge and every byte written while SCS is low.
module stpm32_model (
    input  wire sck,
    input  wire mosi,
    input  wire cs_n,
    input  wire en
);
    reg [7:0] rx_sh;
    reg [7:0] got [0:255];
    integer nbytes, frames, bitcnt;
    reg scs_at_en;
    initial begin nbytes = 0; frames = 0; bitcnt = 0; scs_at_en = 1'b1; end
    always @(posedge en) scs_at_en = cs_n;
    always @(negedge cs_n) begin bitcnt = 0; if (en) frames = frames + 1; end
    always @(posedge sck) if (!cs_n) begin
        rx_sh = {rx_sh[6:0], mosi};
        bitcnt = bitcnt + 1;
        if (bitcnt == 8) begin
            bitcnt = 0;
            got[nbytes] = rx_sh;
            nbytes = nbytes + 1;
        end
    end
endmodule
