# EC-MINT1 chip handoff

Edition: doc-1.0 (2026-10-08). This is the package an ASIC design house accepts before physical design. It is not GDSII. A foundry will not mask it until place-and-route on that foundry’s process design kit.

## Function

EC-MINT1 counts watt-hour pulses, mints one token per 1000 pulses, and signs the record with an on-die ML-DSA-44 datapath. The private key is written once through the provision port and has no runtime read. ZEROIZE clears the key register.

## What to send a chip house

- [spec.md](spec.md) — pins, rails, clock, packet.
- [rtl/](rtl/) — synthesizable Verilog.
- [constraints/ec_mint1.sdc](constraints/ec_mint1.sdc) — 16.384 MHz period.
The butterfly uses a modulo operator so the arithmetic is obvious. Replace it with the Barrett reduction from sheet 11 before synthesis. TX is held idle in this drop; the mint pulse and the key lock are the blocks under test. FIPS 204 known-answer vectors are required before a netlist freeze.

## What not to send a foundry yet

No LEF, no Liberty, no GDSII. Those come back from the design house after synthesis and layout on the PDK they hold under contract.
