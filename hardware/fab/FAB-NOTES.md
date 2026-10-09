# Fabrication pack

Edition: doc-0.9 (2026-10-08).

## What a PCB house can be sent

A board house builds from Gerber or ODB++, a drill file, a centroid file, and this BOM. Those plot files do not exist yet. This directory is the schematic-level order pack: part numbers, nets, and the rule that layout must follow.

Do not send the SVG sheets in `docs/schematics/` as fabrication artwork. They are design drawings.

Orderable parts are in [BOM.csv](BOM.csv). Nets are in [netlist.txt](netlist.txt). The metrology device is STPM32TR, QFN-24, active at ST. The shunt is Vishay WSBS5216L1000JT, 100 µΩ. The signer is a SEALSQ VaultIC 409, QFN32, a quote part, not a distributor reel confirmed in this pack.

Layout rules before Gerbers:

- Supply tap on the feeder side of Rs, so mint-path current is not in the integral.
- Kelvin sense from Rs to U2.IP and U2.IN. No shared force copper.
- R1a and R1b each rated at least 200 V, series.
- U3 ZEROIZE to the mesh, no firmware override.
- U4 holds no key. Antenna match from the module datasheet.
- Continuous draw under 2 W. See [docs/meter-burden.md](../../docs/meter-burden.md).

After layout, export Gerber X2, Excellon drill, and IPC-7351 centroid, then a board house can quote assembly.

## What a chip house cannot be sent yet

A foundry tapeout needs a process design kit, a synthesized netlist, timing constraints, and GDSII. None of that is in this repository. ML-DSA is not a small gate schematic a fab will mask from a drawing.

The mass-order path for the cryptography is the VaultIC 409, which already integrates an ML-DSA engine in a QFN32. A custom die is a later program, and it needs a foundry contract. [rtl/mint_schedule.v](../rtl/mint_schedule.v) is the schedule counter a chip team would wrap around that engine. It is not a tapeout.
