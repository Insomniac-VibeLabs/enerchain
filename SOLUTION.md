# Solution decision

Edition: doc-1.1 (2026-10-09).

## Choice

Hardware. Not a software wallet, and not a from-scratch ML-DSA ASIC.

A program on the inverter, the radio, or a server can report any integral it wants. The whitepaper's claim is that the signed total is the total the sealed terminals measured. That claim is false if software is allowed to choose `n`. It is also weaker, not stronger, if the signature comes from a new die whose lattice core, random source, and key injection have never been reviewed. A partial Keccak gate and an NTT butterfly that uses the Verilog `%` operator are not a mask set, and they are not side-channel resistant.

The manufacturable lock is three pieces, and none of them is left for the factory to invent:

1. **EC-SEAL1 board.** Shunt, divider, supply, tamper latch, and meter ASIC, with every resistor, capacitor, diode, and transistor called out. Two boards are required for an issuance: one on the generator side of the terminals, one on the grid side. The ledger mints only when both signatures agree within the class tag.
2. **EC-MINT1 die.** A small standard-cell chip. It counts watt-hour pulses, and it is the only SPI master the signer will ever see. The radio is not on that bus. The foundry synthesizes the Verilog in this repository on its own standard-cell library. It does not choose the schedule, the packet, or the pinout.
3. **QS7001 signer.** A catalog secure element that already runs ML-DSA in hardware, keeps the private key inside, and has a public QFN-32 pinout. The OTP image is the signing oracle in [firmware/qs7001/sign_oracle.c](firmware/qs7001/sign_oracle.c). It has two commands: sign this 32-byte record, or erase the key. The image hash is published next to the meter's public key, so a substituted image does not verify.

Non-repudiation is the ML-DSA-44 signature over the record EC-MINT1 built from its own counters. A later party checks the signature, the certified key, and that cumulative watt-hours extend the previous accepted record. The signer cannot deny the signature. The radio cannot produce one. Opening the cover fires a discrete transistor latch, which orders a key erase and then crowbars the signer rail.

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

## What a factory is given

The board house gets the EC-SEAL1 order in [hardware/fab/ec-seal1/](hardware/fab/ec-seal1/): BOM, centroid, netlist, stackup, the discrete circuit, and Gerber. The Gerber already has the 40 A force pours, the line tap into the divider, the fused tap into the X2 capacitor, and the neutral tie into the ground plane. The QFN fanout is not in that Gerber. It is executed from the netlist under written spacing rules, because a via pad does not fit between 0.50 mm lands without a short, and a short is not a file worth sending. The chip house gets the pinout, package, SDC, Verilog, and the schedule test under [hardware/asic/](hardware/asic/). Neither file asks them to pick an architecture.

## What this does not pretend

There is no GDSII. A foundry still runs place-and-route on its own process design kit, because that database is not public and a hand-drawn transistor netlist of an ML-DSA core would be the wrong artifact. The schedule itself is fully specified and is small enough to synthesize without an architectural choice. The ML-DSA signature stays in the QS7001. The SPI byte path on EC-MINT1 was not simulated here; the sandbox has no Verilog simulator. The schedule was. `tools/check_schedule.py` passes: 1000 watt-hour pulses mint one token, and splitting the interval does not mint a second.
