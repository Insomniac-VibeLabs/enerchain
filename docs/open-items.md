# Open items

Edition: v0.0.1 (doc-1.3, 2026-10-09).

What is not done, what was assumed, and what has to be true before a meter leaves the bench. "Verify" items are facts about a catalog part that the review could not read from the datasheet here; the design assumes them and says where.

## Hardware: blocks a field meter

**O-1. Tamper while unpowered.** The tamper latch, the erase command and the QS7001 all need power. An attacker who disconnects the meter, opens the cover, and closes it again before reconnecting leaves the key intact and the latch clear. While open they could inject pulses on CF_EXP, replace EC-MINT1, or rewrite the FRAM. The ledger's pair rule bounds the damage to min(GEN, GRID), so one opened meter cannot mint past its partner, but a pair under one owner's control can be opened together. The fix is a battery-backed tamper domain that holds a key-encryption key and clears it in hardware on a mesh break, powered or not (a secure supervisor of the Analog Devices DS3645 class, or a secure element with a battery tamper domain), with the QS7001's signing key stored wrapped by that key. Revision B does not have it. Until it does, EC-SEAL1 is a bench prototype.

**O-2. STPM32 configuration (verify).** The design assumes, from DocID025358: LED1 can be configured to pulse on positive active energy only and LED2 on negative active energy only, both at 1000 impulses/kWh; the SPI interface is selected by SCS low across the EN rising edge; SCS is active low in SPI mode. If the LED outputs cannot be split by sign, the fallback is to read the signed active-energy register over SPI instead of counting LED pulses, which is an RTL change, not a board change. The register addresses for the factory transcript are deliberately not in this tree.

**O-3. QS7001 (verify).** Public material confirms a RISC-V secure microcontroller with hardware ML-DSA (ML-DSA-87 is named) and ML-KEM. Still to confirm under the vendor's datasheet and SDK: that ML-DSA-44 is offered (if not, set `SIG_BYTES = 4627` and certify meters as ML-DSA-87; the ledger supports both); that a customer image like `firmware/qs7001/sign_oracle.c` can be loaded and locked; non-volatile storage for the rollback guard; the QFN-32 pin map used on the board (from the vendor summary 6658GS); its supply range and signing current.

**O-4. LNK304 design values (verify).** The buck uses the standard LinkSwitch-TN high-side buck values: 1 mH inductors, 4.7 µF 400 V input capacitors, feedback 13.0 kΩ / 2.05 kΩ for 12 V with a 1.65 V FB reference, ultrafast freewheel diode. Confirm against the LNK304 datasheet and run the PI design tool for the 12 V, 70 mA load. Confirm the RLB0914-102KL saturation current exceeds the LNK304 current limit.

**O-10. Signer-rail gate thresholds (verify).** Q5 (DMG2305UX) and Q4 (2N7002) share the delayed gate CROW_G. With the datasheet threshold spreads, Q4 can turn on before Q5 has opened; R23 = 1 kΩ limits that overlap to 3.3 mA. Confirm on the bench that VDD does not sag when ZEROIZE fires (TEST.md step 16).

**O-5. LM2936 output capacitor (verify).** C3 is a 10 µF ceramic. Confirm it falls inside the LM2936 output-capacitor ESR stability region; if not, fit a 10 µF tantalum or add series resistance.

**O-6. R1 surge rating (verify).** R1 (ERJ-P08J100V, anti-surge 1206) takes about 34 A for under 0.1 ms on every power-up. Confirm the single-pulse rating, or use a flameproof wirewound fusible resistor of the kind Power Integrations specifies.

**O-7. Metrology class.** Accuracy class is a calibration and type-test result (IEC 62053-21/-22). Nothing here has been calibrated. The 100 µΩ shunt gives 25 µV at 0.25 A, so the starting current and low-current accuracy must be measured on the bench.

**O-8. Safety and EMC.** Creepage, clearance, hipot, surge (IEC 61000-4-5), and the LNK304 conducted emissions are a type test. The layout rule in `tools/gen_board.py` is 2.5 mm mains-to-logic on placed lands; it is not a certificate.

**O-9. EC-MINT1 physical design.** Gate-level simulation on the foundry library, STA with real I/O cells, scan insertion, and a decision on whether the 256-byte image cache stays in flops or streams from FRAM at boot.

## Protocol and software

**S-1. Consensus.** v0.0.1 orders blocks by proof of authority: a fixed validator set from genesis, round-robin by height, one signature per block. There is no fork choice, no finality gadget, no validator rotation and no network layer. A public network needs a BFT protocol (for example Tendermint-style two-thirds precommits) with validator-set changes under governance.

**S-2. Key storage.** Wallets and devnet keys are unencrypted JSON files (mode 0600). The ML-DSA implementation is pure Python and not constant-time. Neither may hold value.

**S-3. Fees and spam.** Transfers carry no fee. A public network needs a fee or rate limit per account and per meter.

**S-4. Throughput.** An issuance is a 32-byte record and a 2420-byte signature. In the devnet's JSON encoding that is about 4.9 kB, so a 1 MiB block holds about 210 issuances; a binary encoding would roughly double that. At one record per meter per kWh, and two meters per site, one million home systems that each export 25 kWh a day produce about fifty million records a day, about 580 a second, or close to three full JSON blocks a second. That needs regional books (one chain per grid region, which is already the economic design), short block times, or both. Signature aggregation is not available for ML-DSA.

**S-5. Double counting with existing instruments.** The energy a token records has usually also been sold to a utility and may also earn a renewable energy certificate or guarantee of origin. Whether a token replaces, accompanies, or must be reconciled with those is a market-design and legal decision, not a protocol one. It is undecided.

**S-6. Value.** Supply grows with net generation and has no cap; nothing redeems a token for energy. What makes a token worth holding (acceptance for settlement in a regional book, utility participation, demand from compute loads) is the economic hypothesis this repository states, not something the code establishes.

**S-7. Meter lifecycle.** Certification exists; key rotation, meter replacement, and moving a pair to a new beneficiary are not specified.

**S-8. Time.** Records carry no wall-clock time; the ledger orders them by sequence number and dates them at inclusion. Time-of-use pricing per region would need a trusted time source in the meter.
