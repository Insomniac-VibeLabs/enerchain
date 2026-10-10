# EC-MINT1 chip handoff

Edition: v0.0.1 (doc-1.4). This is the package an ASIC design house accepts before physical design. It is not GDSII. A foundry will not mask it until place-and-route on that foundry's process design kit.

## Function

EC-MINT1 counts export and import watt-hour pulses, mints on net export, keeps its counters and the calibration image in an external FRAM so a power cut loses nothing, and is the only SPI master the signer ever sees. One token is 1000 net-export pulses, 1 kWh; one signed record goes out for every token. The private key is not in this die. It is in a QS7001. ZEROIZE tells that part to erase the key and then holds the signer in reset.

The doc-0.8 files `rtl/keccak_round.v` and `rtl/ntt_butterfly.v` are not in this netlist. The butterfly uses a Verilog modulo operator. Do not synthesize them.

## What to send a chip house

- [PINOUT.md](PINOUT.md) and [PACKAGE.md](PACKAGE.md) — QFN-32, 5 mm, 0.50 mm, pin 1 at the top of the left side.
- [spec.md](spec.md) — rails, clock, schedule, FRAM map, record.
- [rtl/ec_mint1.v](rtl/ec_mint1.v), [rtl/ec_mint1_schedule.v](rtl/ec_mint1_schedule.v), [rtl/spi_byte.v](rtl/spi_byte.v), [rtl/uart_tx.v](rtl/uart_tx.v) — the netlist.
- [constraints/ec_mint1.sdc](constraints/ec_mint1.sdc) — 16.000 MHz.
- [tb/tb_schedule.v](tb/tb_schedule.v), [tb/tb_ec_mint1.v](tb/tb_ec_mint1.v) and [tb/models.v](tb/models.v) — the schedule vector and the end-to-end vector.

## What was run

- `tb_schedule.v`: 999 pulses mint nothing, 1000 mint one, 400 + 600 mint one, 500 import then 1500 export mint one, every token raises exactly one record request.
- `tb_ec_mint1.v`, against behavioral models of the QS7001 oracle, the FRAM and the STPM32 configuration port: blank FRAM waits for provisioning and does not count; provisioning locks the image into FRAM; the STPM32 is put in SPI mode and the transcript is replayed; export mints, import cancels; a power cut between records keeps counters and sequence; a power cut in the middle of a FRAM write falls back to the older slot; a refused sequence produces no frame and the next one is accepted; after an idle spell the last record is re-sent under the next seq with the same counters; ZEROIZE sends `5C 5C`, then `A7` and one tamper record (kind 1, the live counters) signed with the tamper key, holds the signer in reset, and stops counting.
- `tools/check_rtl.py` replays the same events through the Python reference model (`enerchain/meter.py`) and requires every signed record to match byte for byte.
- `yosys synth -top ec_mint1` with `check -assert`: no problems.

Still to run before tapeout: gate-level simulation on the foundry library, STA with the real I/O cells, and a scan-insertion pass if the house requires one.

## What not to send a foundry yet

No LEF, no Liberty, no GDSII. Those come back from the design house after synthesis and layout on the PDK they hold under contract. Do not add a CPU, a Pierce oscillator, or a second master on the signer SPI.
