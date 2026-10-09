# Solution decision

Edition: v0.0.1 (doc-1.2, 2026-10-09). The choice below is unchanged from doc-1.1. What v0.0.1 corrected is in the second table.

## Choice

Hardware. Not a software wallet, and not a from-scratch ML-DSA ASIC.

A program on the inverter, the radio, or a server can report any integral it wants. The whitepaper’s claim is that the signed total is the total the sealed terminals measured. That claim is false if software is allowed to choose `n`. It is also weaker, not stronger, if the signature comes from a new die whose lattice core, random source, and key injection have never been reviewed. A partial Keccak gate and an NTT butterfly that uses the Verilog `%` operator are not a mask set, and they are not side-channel resistant.

The manufacturable lock is three pieces, and none of them is left for the factory to invent:

1. **EC-SEAL1 board.** Shunt, divider, supply, tamper latch, meter ASIC and an F-RAM for the counters, with every resistor, capacitor, diode, and transistor called out. Two boards are required for an issuance: a GEN board at the generator terminals and a GRID board at the point of connection. The ledger mints the smaller of the two boards' token counts.
2. **EC-MINT1 die.** A small standard-cell chip. It counts export and import watt-hour pulses, mints on net export, keeps its counters through power cuts, and is the only SPI master the signer will ever see. The radio is not on that bus. The foundry synthesizes the Verilog in this repository on its own standard-cell library. It does not choose the schedule, the packet, or the pinout.
3. **QS7001 signer.** A catalog secure element that already runs ML-DSA in hardware, keeps the private key inside, and has a public QFN-32 pinout. The image is the signing oracle in [firmware/qs7001/sign_oracle.c](firmware/qs7001/sign_oracle.c). It has two commands: sign this 32-byte record, or erase the key. It generates its key once, at personalization, and refuses to sign a record that does not advance the last one it signed. The image hash is published next to the meter’s public key, so a substituted image does not verify.

Non-repudiation is the ML-DSA-44 signature over the record EC-MINT1 built from its own counters. A later party checks the signature, the certified key, the calibration CRC, and that the record's sequence number and cumulative counters advance the previous accepted record. The signer cannot deny the signature. The radio cannot produce one. Opening the cover fires a discrete transistor latch, which orders a key erase and then crowbars the signer rail.

## What was wrong in the doc-1.1 pack

Do not build the doc-1.1 board (revision A). The full review, with calculations, is [docs/electrical-review.md](docs/electrical-review.md).

| Item | doc-1.1 | Why it does not work | v0.0.1 |
| --- | --- | --- | --- |
| Ground reference | Logic ground on Neutral, shunt in Line | STPM32 current inputs at full mains voltage | Ground is Line at the shunt; divider from Neutral |
| Supply | Half-wave X2 dropper | D1 reversed, so the rail never charges; even corrected, about 11 mA at 240 V | LNK304 buck to 12 V, then the LM2936 |
| Signer rail | 47 Ω feed plus a crowbar | About 1 V drop while signing; the crowbar overloads the 50 mA regulator | P-FET switch, discharge only after the erase |
| Counters and boot ROM | Flip-flops | First power cut resets W and erases the calibration | F-RAM, two CRC-checked slots and a locked image |
| Signer key | Generated at every boot | A power cycle makes a new, uncertified key; a wiped part revives | Generated once; wipe recorded in non-volatile memory |
| Direction | Export pulses only, read as negative | Export never pulses; a grid-battery-grid loop mints | Export and import pulses; mint on net export |
| Pairing rule | Two meters "agree within the class tag" per interval | Meters drift; intervals never line up | Ledger mints min of two cumulative token counts |
| Counter width | 16-bit n, 32-bit W | Wraps in years (home) or hours (plant) | 48-bit cumulative |
| Signature read | 2420 bytes clocked immediately | No wait for signing time | Ready poll, then streamed to the UART |

## What was wrong in the doc-0.9 pack

Do not build the doc-0.9 BOM as drawn.

| Item | doc-0.9 | Why it does not ship | doc-1.1 |
| --- | --- | --- | --- |
| MOV | MOV-07D271K, 175 V class | Conducts on a 240 V crest and overheats | MOV-10D431K, 275 VAC |
| LDO | TPS7A2033, 6 V absolute max, fed from a 12 V zener | The zener destroys the regulator | LM2936MP-3.3, 40 V absolute max |
| Divider | 0.50 V rms into STPM32 | VIP1/VIN1 operating window is ±0.3 V. 0.50 V rms is 0.71 V peak | 0.120 V rms, four 499 kΩ high-side resistors |
| Signer key | 256-bit shift register called ML-DSA | An ML-DSA-44 private key is 2560 bytes and does not live in that register | Key stays in the QS7001 |
| X2 capacitor | No bleeder | The dropper can hold a charge | Two 1 MΩ, 700 V resistors across it |
| Zeroize polarity | Sheet 06 says active low, the ASIC pin says active high | The latch would do the opposite of the erase | Active high, transistor latch |

The last column is the doc-1.1 correction. Revision B keeps the MOV, the divider, the LDO and the latch polarity; it replaces the X2 dropper outright.

## What a factory is given

The board house gets the EC-SEAL1 revision B order in [hardware/fab/ec-seal1/](hardware/fab/ec-seal1/): BOM, centroid, netlist, stackup, the circuit, and Gerber. The Gerber already has the 40 A force pours, the ground strip into the inner plane, the Neutral pour and its gutter into the divider, and the fused-Neutral tap. The QFN fanout is not in that Gerber. It is executed from the netlist under written spacing rules, which `tools/gen_board.py` checks on the placed lands. The chip house gets the pinout, package, SDC, Verilog, and the testbenches under [hardware/asic/](hardware/asic/). Neither file asks them to pick an architecture.

## What this does not pretend

There is no GDSII. A foundry still runs place-and-route on its own process design kit. The ML-DSA signature stays in the QS7001. The RTL now runs end to end in Icarus Verilog against behavioral models of the signer, the F-RAM and the STPM32, synthesizes in yosys, and matches the Python reference model record for record; that is simulation, not silicon. The board has not been built. Opening the cover while the meter is unpowered is not detected, so revision B is a bench prototype. Facts about the STPM32, QS7001, LNK304 and LM2936 that could not be read from their datasheets here are listed in [docs/open-items.md](docs/open-items.md).
