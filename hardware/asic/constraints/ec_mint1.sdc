# EC-MINT1. 16.000 MHz CMOS clock on XI. Period 62.5 ns.
create_clock -name xi -period 62.5 -waveform {0 31.25} [get_ports XI]
set_input_delay 8 -clock xi [get_ports {CF_IN ZEROIZE QS_MISO STP_MISO PROV_CS PROV_SCK PROV_MOSI}]
set_output_delay 8 -clock xi [get_ports {MINT UART_TX QS_SCK QS_MOSI QS_CS_N QS_RST_N STP_SCK STP_MOSI STP_CS PROV_MISO CAL_LOCKED}]
set_false_path -from [get_ports RST_N]
set_false_path -from [get_ports ZEROIZE]
# SPI is launched by this die. Do not time QS_MISO as a same-edge internal path
# tighter than the 1 MHz byte engine. The byte engine is multi-cycle by construction.
set_multicycle_path 16 -setup -to [get_ports QS_SCK]
set_multicycle_path 15 -hold -to [get_ports QS_SCK]
