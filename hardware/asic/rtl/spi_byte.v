// SPI mode 0 byte master. SCK idle low. MOSI changes while SCK is low.
// MISO is sampled as SCK rises. Eight bits, MSB first. One byte per `start`.
module spi_byte (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire [7:0] tx,
    output reg  [7:0] rx,
    output reg        busy,
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
            sck <= 1'b0;
            mosi <= 1'b0;
            sh <= 8'h00;
            bitn <= 3'd0;
            phase <= 1'b0;
        end else if (!busy) begin
            sck <= 1'b0;
            if (start) begin
                busy <= 1'b1;
                sh <= tx;
                mosi <= tx[7];
                bitn <= 3'd0;
                phase <= 1'b0;
            end
        end else if (!phase) begin
            mosi <= sh[7];
            sck <= 1'b1;
            phase <= 1'b1;
        end else begin
            sh <= {sh[6:0], miso};
            sck <= 1'b0;
            phase <= 1'b0;
            if (bitn == 3'd7) begin
                rx <= {sh[6:0], miso};
                busy <= 1'b0;
            end else
                bitn <= bitn + 3'd1;
        end
    end
endmodule
