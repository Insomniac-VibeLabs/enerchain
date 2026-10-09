// 8N1 transmit-only UART. DIV clocks per bit: 139 at 16.000 MHz is
// about 115108 baud. Line idles high. `done` pulses after the stop bit.
module uart_tx #(
    parameter integer DIV = 139
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire [7:0] data,
    output reg        tx,
    output reg        busy,
    output reg        done
);
    reg [7:0] div;
    reg [3:0] bitn;
    reg [8:0] sh; // data then stop bit

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx <= 1'b1;
            busy <= 1'b0;
            done <= 1'b0;
            div <= 8'd0;
            bitn <= 4'd0;
            sh <= 9'h1FF;
        end else begin
            done <= 1'b0;
            if (!busy) begin
                if (start) begin
                    busy <= 1'b1;
                    tx <= 1'b0; // start bit
                    sh <= {1'b1, data};
                    div <= 8'd0;
                    bitn <= 4'd0;
                end
            end else if (div == DIV - 1) begin
                div <= 8'd0;
                if (bitn == 4'd9) begin
                    busy <= 1'b0;
                    done <= 1'b1;
                    tx <= 1'b1;
                end else begin
                    tx <= sh[0];
                    sh <= {1'b1, sh[8:1]};
                    bitn <= bitn + 4'd1;
                end
            end else
                div <= div + 8'd1;
        end
    end
endmodule
