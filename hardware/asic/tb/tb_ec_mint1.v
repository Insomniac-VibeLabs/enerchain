// EC-MINT1 end-to-end testbench, v0.0.1. Self-checking.
// Runs the top with small parameters so a sign fits in simulation time:
// Q = 10 pulses per token, a record every 2 tokens, 40-byte stand-in
// signature, 4 clocks per UART bit.
//
// Covers: blank FRAM -> provisioning -> lock; STPM32 SPI-mode select and
// transcript replay; net-export minting; import cancels export; a power
// cut between records (counters and sequence survive); a power cut in the
// middle of a FRAM write (the older slot is used); a signer refusal of a
// non-advancing sequence; zeroize (5C 5C, signer reset, counting stops).
//
// Each accepted record is printed as `REC <64 hex digits>` so that
// tools/check_rtl.py can compare it with the Python reference model.
`timescale 1ns/1ps
module tb_ec_mint1;
    localparam integer SIGB = 40;
    localparam integer DIV = 4;
    localparam integer FRAME = 2 + 32 + SIGB;

    reg clk = 0;
    reg rst_n = 0;
    reg cf_exp = 0, cf_imp = 0, zeroize = 0;
    reg prov_cs = 0, prov_sck = 0, prov_mosi = 0;
    wire mint, uart, qs_sck, qs_mosi, qs_miso, qs_cs_n, qs_rst_n;
    wire stp_sck, stp_mosi, stp_cs_n, stp_en, fr_sck, fr_mosi, fr_miso, fr_cs_n;
    wire prov_miso, cal_locked;

    always #31.25 clk = ~clk;

    ec_mint1 #(.Q(16'd10), .SIGN_EVERY(8'd2), .SIG_BYTES(SIGB), .UART_DIV(DIV),
               .T_WAIT(20), .POLL_MAX(2000)) dut (
        .XI(clk), .RST_N(rst_n), .CF_EXP(cf_exp), .CF_IMP(cf_imp), .ZEROIZE(zeroize),
        .MINT(mint), .UART_TX(uart),
        .QS_SCK(qs_sck), .QS_MOSI(qs_mosi), .QS_MISO(qs_miso), .QS_CS_N(qs_cs_n),
        .QS_RST_N(qs_rst_n),
        .STP_SCK(stp_sck), .STP_MOSI(stp_mosi), .STP_MISO(1'b0), .STP_CS_N(stp_cs_n),
        .STP_EN(stp_en),
        .FR_SCK(fr_sck), .FR_MOSI(fr_mosi), .FR_MISO(fr_miso), .FR_CS_N(fr_cs_n),
        .PROV_CS(prov_cs), .PROV_SCK(prov_sck), .PROV_MOSI(prov_mosi),
        .PROV_MISO(prov_miso), .CAL_LOCKED(cal_locked)
    );

    qs7001_model #(.SIG_BYTES(SIGB), .BUSY(5)) qs (
        .sck(qs_sck), .mosi(qs_mosi), .miso(qs_miso), .cs_n(qs_cs_n), .rst_n(qs_rst_n));
    fram_model fr (.sck(fr_sck), .mosi(fr_mosi), .miso(fr_miso), .cs_n(fr_cs_n));
    stpm32_model st (.sck(stp_sck), .mosi(stp_mosi), .cs_n(stp_cs_n), .en(stp_en));

    // ---------------- UART receiver ---------------------------------------
    reg [7:0] fb [0:FRAME-1];
    integer nb = 0;
    integer frames = 0;
    integer bad_sig = 0;
    reg [7:0] ub;
    integer j;
    always begin
        @(negedge uart);
        repeat (DIV + DIV / 2) @(posedge clk);
        for (j = 0; j < 8; j = j + 1) begin
            ub[j] = uart;
            repeat (DIV) @(posedge clk);
        end
        fb[nb] = ub;
        nb = nb + 1;
        if (nb == FRAME) begin
            nb = 0;
            frames = frames + 1;
            for (j = 0; j < SIGB; j = j + 1)
                if (fb[34 + j] !== (fb[2 + (j % 32)] ^ (j & 8'hFF) ^ 8'hA5))
                    bad_sig = bad_sig + 1;
            $write("REC ");
            for (j = 2; j < 34; j = j + 1) $write("%02x", fb[j]);
            $write("\n");
        end
        @(posedge clk);
    end

    function [47:0] f48;
        input integer off;
        f48 = {fb[2+off], fb[3+off], fb[4+off], fb[5+off], fb[6+off], fb[7+off]};
    endfunction
    function [31:0] f32;
        input integer off;
        f32 = {fb[2+off], fb[3+off], fb[4+off], fb[5+off]};
    endfunction

    // ---------------- helpers ---------------------------------------------
    integer fails = 0;
    task check;
        input cond;
        input [8*64-1:0] what;
        begin
            if (!cond) begin
                fails = fails + 1;
                $display("FAIL %0s", what);
            end
        end
    endtask

    task pulse_exp;
        input integer n;
        integer i;
        begin
            for (i = 0; i < n; i = i + 1) begin
                cf_exp = 1; repeat (3) @(posedge clk);
                cf_exp = 0; repeat (3) @(posedge clk);
            end
        end
    endtask
    task pulse_imp;
        input integer n;
        integer i;
        begin
            for (i = 0; i < n; i = i + 1) begin
                cf_imp = 1; repeat (3) @(posedge clk);
                cf_imp = 0; repeat (3) @(posedge clk);
            end
        end
    endtask

    task wait_frames;
        input integer want;
        integer t;
        begin
            t = 0;
            while (frames < want && t < 200000) begin
                @(posedge clk); t = t + 1;
            end
        end
    endtask

    task settle; // let the persist FSM finish
        begin
            repeat (2000) @(posedge clk);
        end
    endtask

    task power_cycle;
        begin
            rst_n = 0;
            repeat (10) @(posedge clk);
            rst_n = 1;
        end
    endtask

    task wait_armed;
        integer t;
        begin
            t = 0;
            while (dut.count_en !== 1'b1 && t < 100000) begin
                @(posedge clk); t = t + 1;
            end
        end
    endtask

    reg [7:0] image [0:255];
    task provision;
        integer b, k;
        begin
            prov_cs = 1;
            for (b = 0; b < 256; b = b + 1)
                for (k = 7; k >= 0; k = k - 1) begin
                    prov_mosi = image[b][k];
                    repeat (2) @(posedge clk);
                    prov_sck = 1;
                    repeat (3) @(posedge clk);
                    prov_sck = 0;
                    repeat (2) @(posedge clk);
                end
            prov_cs = 0;
        end
    endtask

    integer i, t, f0;
    reg [47:0] w0;
    initial begin
        for (i = 0; i < 256; i = i + 1) image[i] = 8'h00;
        image[0] = 8'hA5; image[1] = 8'h5A; image[2] = 8'h02;           // role GRID
        image[3] = 8'h00; image[4] = 8'h00; image[5] = 8'h00; image[6] = 8'h42;
        image[7] = 8'd3; image[8] = 8'h11; image[9] = 8'h22; image[10] = 8'h33;
        image[11] = 8'd2; image[12] = 8'h44; image[13] = 8'h55;
        image[14] = 8'd0;

        repeat (4) @(posedge clk);
        rst_n = 1;

        // 1. Blank FRAM: the die waits for provisioning and does not count.
        repeat (6000) @(posedge clk);
        check(cal_locked == 1'b0, "blank FRAM must not lock");
        check(dut.bst == 4'd1, "blank FRAM waits in B_PROV");
        pulse_exp(30);
        check(dut.e_exp == 48'd0, "no counting before provisioning");

        // 2. Provision, lock, replay.
        provision;
        wait_armed;
        check(cal_locked == 1'b1, "locked after provisioning");
        check(fr.mem[16'h0200] == 8'h4C && fr.mem[16'h0201] == 8'h4B, "lock marker in FRAM");
        check(st.scs_at_en == 1'b0, "STPM32 SCS low at EN rise (SPI select)");
        check(st.nbytes == 5, "transcript bytes replayed");
        check(st.got[0] == 8'h11 && st.got[4] == 8'h55, "transcript content");

        // 3. 20 export pulses = 2 tokens = one record.
        pulse_exp(20);
        wait_frames(1);
        check(frames == 1, "first record");
        check(f32(0) == 32'h00000042, "meter id");
        check(fb[2+4] == 8'h12, "version 1, role GRID");
        check(fb[2+5] == 8'h22, "class");
        check(f32(6) == 32'd1, "seq 1");
        check(f48(10) == 48'd20 && f48(16) == 48'd0 && f48(22) == 48'd2, "counters rec 1");

        // 4. Import cancels export. Net high-water 40 -> 4 tokens.
        pulse_imp(15);
        pulse_exp(14);
        repeat (200) @(posedge clk);
        check(dut.tokens == 48'd2, "import blocks minting");
        pulse_exp(21);
        wait_frames(2);
        check(frames == 2, "second record");
        check(f32(6) == 32'd2, "seq 2");
        check(f48(10) == 48'd55 && f48(16) == 48'd15 && f48(22) == 48'd4, "counters rec 2");

        // 5. Power cut between records.
        pulse_exp(5);
        settle;
        power_cycle;
        wait_armed;
        check(dut.e_exp == 48'd60 && dut.e_imp == 48'd15 && dut.tokens == 48'd4,
              "counters restored from FRAM");
        check(dut.seq == 32'd2, "sequence restored");
        check(st.nbytes == 10, "transcript replayed again after power cut");
        pulse_exp(15);
        wait_frames(3);
        check(frames == 3 && f32(6) == 32'd3, "seq 3 after power cut");
        check(f48(10) == 48'd75 && f48(22) == 48'd6, "counters rec 3");

        // 6. Power cut in the middle of a FRAM slot write.
        settle;
        cf_exp = 1; repeat (3) @(posedge clk); cf_exp = 0;
        t = 0;
        while (!(dut.pst == 2'd3 && dut.pi == 6'd20) && t < 10000) begin
            @(posedge clk); t = t + 1;
        end
        check(t < 10000, "reached the middle of a slot write");
        power_cycle;
        wait_armed;
        check(dut.e_exp == 48'd75, "torn write: older slot used, one pulse lost");
        check(dut.seq == 32'd3, "torn write: sequence intact");

        // 7. Signer refuses a sequence that does not advance.
        qs.last_seq = 4;
        f0 = frames;
        pulse_exp(20);              // tokens 6 -> 8, record seq 4: refused
        repeat (3000) @(posedge clk);
        check(frames == f0, "refused record is not sent");
        check(qs.refusals == 1, "refusal counted");
        pulse_exp(20);              // record seq 5: accepted
        wait_frames(f0 + 1);
        check(frames == f0 + 1 && f32(6) == 32'd5, "next sequence accepted");

        // 8. Zeroize.
        zeroize = 1;
        repeat (500) @(posedge clk);
        check(qs.wiped == 1'b1, "signer received 5C 5C");
        check(qs_rst_n == 1'b0, "signer held in reset");
        f0 = frames;
        w0 = dut.e_exp;
        pulse_exp(40);
        repeat (2000) @(posedge clk);
        check(frames == f0, "no record after zeroize");
        check(dut.e_exp == w0, "no counting after zeroize");

        check(bad_sig == 0, "signature bytes streamed intact");

        if (fails == 0)
            $display("PASS ec_mint1: provision, replay, net export, power cuts, refusal, zeroize");
        else
            $display("FAIL %0d checks", fails);
        $finish;
    end
endmodule
