// SPI mode 0 byte master. SCK idle low. MOSI changes only while SCK is low.
// MISO is sampled at the end of the SCK high phase. Eight bits, MSB first. One byte per `start`.
// `done` is a one-cycle pulse when `rx` holds the byte just clocked in.
// SCK is clk/2: 8 MHz at the 16.000 MHz XI clock.
module spi_byte (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire [7:0] tx,
    output reg  [7:0] rx,
    output reg        busy,
    output reg        done,
    output reg        sck,
    output reg        mosi,
    input  wire       miso
);
    reg [7:0] sh;
    reg [2:0] bitn;
    reg       phase; // 0 = drive, 1 = rising sample

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx <= 8'h00;
            busy <= 1'b0;
            done <= 1'b0;
            sck <= 1'b0;
            mosi <= 1'b0;
            sh <= 8'h00;
            bitn <= 3'd0;
            phase <= 1'b0;
        end else begin
            done <= 1'b0;
            if (!busy) begin
                sck <= 1'b0;
                if (start) begin
                    busy <= 1'b1;
                    sh <= tx;
                    mosi <= tx[7];
                    bitn <= 3'd0;
                    phase <= 1'b0;
                end
            end else if (!phase) begin
                sck <= 1'b1;
                phase <= 1'b1;
            end else begin
                // MISO is taken at the end of the high phase. MOSI moves to
                // the next bit as SCK falls, half a period before the next
                // rising edge. doc-1.1 moved MOSI on the rising edge itself.
                sh <= {sh[6:0], miso};
                mosi <= sh[6];
                sck <= 1'b0;
                phase <= 1'b0;
                if (bitn == 3'd7) begin
                    rx <= {sh[6:0], miso};
                    busy <= 1'b0;
                    done <= 1'b1;
                end else
                    bitn <= bitn + 3'd1;
            end
        end
    end
endmodule
