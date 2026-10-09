# EC-MINT1 chip handoff

Edition: doc-1.1 (2026-10-09). This is the package an ASIC design house accepts before physical design. It is not GDSII. A foundry will not mask it until place-and-route on that foundry's process design kit.

## Function

EC-MINT1 counts watt-hour pulses and is the only SPI master the signer ever sees. One token is 1000 pulses. The private key is not in this die. It is in a QS7001, which already runs ML-DSA-44. ZEROIZE tells that part to erase the key and then holds the signer in reset.

The doc-1.0 files `rtl/keccak_round.v` and `rtl/ntt_butterfly.v` are sketches from doc-0.8. They are not in this netlist. The butterfly uses a Verilog modulo operator. Do not synthesize them.

## What to send a chip house

- [PINOUT.md](PINOUT.md) and [PACKAGE.md](PACKAGE.md) — QFN-32, 5 mm, 0.50 mm, pin 1 at the top of the left side.
- [spec.md](spec.md) — rails, clock, packet.
- [rtl/ec_mint1.v](rtl/ec_mint1.v), [rtl/ec_mint1_schedule.v](rtl/ec_mint1_schedule.v), [rtl/spi_byte.v](rtl/spi_byte.v) — the netlist.
- [constraints/ec_mint1.sdc](constraints/ec_mint1.sdc) — 16.000 MHz.
- [tb/tb_schedule.v](tb/tb_schedule.v) and [../../tools/check_schedule.py](../../tools/check_schedule.py) — the schedule. The Python spec passes. The SPI and UART paths were not simulated in the sandbox that wrote them; there is no Verilog simulator here. Run the schedule testbench before place-and-route, and run a gate simulation of one sign and one wipe before tapeout.

## What not to send a foundry yet

No LEF, no Liberty, no GDSII. Those come back from the design house after synthesis and layout on the PDK they hold under contract. Do not add a CPU, a Pierce oscillator, or a second SPI master.
