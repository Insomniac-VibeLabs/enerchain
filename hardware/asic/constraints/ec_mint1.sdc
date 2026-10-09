# EC-MINT1, v0.0.1 (doc-1.2). 16.000 MHz CMOS clock on XI. Period 62.5 ns.
create_clock -name xi -period 62.5 -waveform {0 31.25} [get_ports XI]
set_input_delay 8 -clock xi [get_ports {CF_EXP CF_IMP ZEROIZE QS_MISO STP_MISO FR_MISO PROV_CS PROV_SCK PROV_MOSI}]
set_output_delay 8 -clock xi [get_ports {MINT UART_TX QS_SCK QS_MOSI QS_CS_N QS_RST_N STP_SCK STP_MOSI STP_CS_N STP_EN FR_SCK FR_MOSI FR_CS_N PROV_MISO CAL_LOCKED}]
set_false_path -from [get_ports RST_N]
# CF_EXP, CF_IMP, ZEROIZE and the PROV pins are asynchronous and pass
# through two-flop synchronizers before any logic.
set_false_path -from [get_ports {CF_EXP CF_IMP ZEROIZE PROV_CS PROV_SCK PROV_MOSI}]
# The three SPI masters run SCK at XI/2 from registered outputs; MISO is
# captured one full XI period after the SCK edge that launched it.
set_multicycle_path 2 -setup -from [get_ports {QS_MISO STP_MISO FR_MISO}]
set_multicycle_path 1 -hold -from [get_ports {QS_MISO STP_MISO FR_MISO}]
