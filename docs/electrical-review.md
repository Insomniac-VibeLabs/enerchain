# Electrical review, doc-1.1 to v0.0.1

Edition: v0.0.1 (doc-1.2, 2026-10-09; amended in doc-1.3, see M-8).

This is the record of checking the EC-SEAL1 board and the EC-MINT1 die against what they are supposed to do: measure energy at the generator or the grid connection, survive a power cut, and sign only what was measured. Each finding says what was wrong, how it was found, and what revision B does instead. Calculations use 240 V rms, 50 Hz unless noted.

What could be run here was run: the RTL in Icarus Verilog against behavioral models, the RTL through yosys, the signing-oracle firmware as a host program, the board generator's layout rules, and the Python reference model. Part facts that need a datasheet this environment could not fetch are listed as open items in [open-items.md](open-items.md) rather than assumed.

## Critical: the board could not have worked

### C-1. Current inputs at mains voltage

doc-1.1 tied logic ground to Neutral (STPM32 VIN1, the LDO ground and the plane were all net `GND` = H3). The shunt sat in the Line conductor between the generator and grid studs, and its Kelvin leads ran through 100 Ω to IIP1 and IIN1. Those pins were therefore at the full line voltage relative to the chip's ground: about 340 V peak on a pin rated for a few hundred millivolts.

Revision B ties logic ground to Line at the grid-side force pad of the shunt. Both Kelvin leads sit within millivolts of ground. The divider now runs from Neutral. [CIRCUITS.md](../hardware/fab/ec-seal1/CIRCUITS.md), "Ground reference".

### C-2. Supply rectifier reversed

The netlist had D1 anode on `RECT_AC`, cathode on ground, and D2 anode on `RECT_AC`, cathode on `VRECT`. Both diodes conduct on the same half-cycle, D1 clamps `RECT_AC` to +0.7 V, and on the other half-cycle nothing conducts, so the X2 capacitor never discharges. `VRECT` would never charge.

### C-3. The dropper could not carry the load anyway

With D1 turned round, a half-wave capacitor supply delivers an average current of f·C·(2V_pk − V_rail − 2V_d):

| Service | 330 nF delivers |
| --- | --- |
| 240 V, 50 Hz | 50 × 330 n × (679 − 13.4) ≈ 11.0 mA |
| 207 V, 50 Hz (−10 %) | ≈ 9.4 mA |
| 120 V, 60 Hz | 60 × 330 n × (339 − 13.4) ≈ 6.5 mA |

The board's logic (STPM32, EC-MINT1 at its 20 mW target, the QS7001 while signing, pull-ups, the radio) needs tens of milliamps. A larger capacitor raises the reactive burden: 1.5 µF at 240 V is 27 VA, over the 10 VA voltage-circuit limit in [meter-burden.md](meter-burden.md).

Revision B uses an LNK304 high-side buck to a 12 V rail (universal input, up to 120 mA in this topology), then the existing LM2936 for 3.3 V. The radio takes its power from 12 V so its transmit current does not pass through the 50 mA LDO. Budget: about 1.4 W worst case with the radio transmitting, under 1 W asleep, a few VA.

### C-4. Signer starved by its own supply resistor

QS_VDD was fed from 3.3 V through R23, 47 Ω, so that the tamper crowbar Q4 could short it. A secure element signing at a few tens of milliamps would see a 1 V drop. When Q4 fired it drew 70 mA through 47 Ω from a 50 mA regulator, pulling the whole 3.3 V rail down with it, including the EC-MINT1 that was supposed to be sending the erase command.

Revision B switches QS_VDD with a P-channel MOSFET (Q5) whose gate is the delayed ZEROIZE. Q4 now only discharges the isolated signer rail through R23, which doc-1.3 raises to 1 kΩ (M-8).

### C-5. A power cut erased the meter

EC-MINT1 held W (cumulative watt-hours), the residual and the "locked" boot ROM in flip-flops. After the first power cut W restarted at zero, so every later record failed the ledger's "W extends the previous W" check, and the boot ROM was blank, so the die never armed again. J5 is under the mesh by then.

Revision B adds an FM25V02A F-RAM. The die keeps two CRC-checked state slots and the calibration image there and reloads them at boot. The testbench cuts power both between records and in the middle of a slot write.

### C-6. A power cut changed the meter's key

The QS7001 image called key generation from its boot routine, and the wipe flag lived in RAM. Every power cycle produced a new, uncertified key; a wiped part came back to life with a fresh one. Revision B generates the key once at personalization, stores "personalized" and "wiped" in non-volatile memory, and checks ZEROIZE on GPIO3 at boot and on every poll. The firmware host test covers each case.

## Major

### M-1. Export would have read as negative energy

With the divider from Line (v = V_L − V_N) and IIP1 on the grid-side Kelvin pad, export current (generator to grid in the Line conductor) gave a negative current reading, so the product was negative for export. A meter configured to pulse on positive active energy would never have pulsed for the energy it exists to count. Revision B's divider from Neutral reads −v; with the same Kelvin wiring the product is positive for export. [CIRCUITS.md](../hardware/fab/ec-seal1/CIRCUITS.md), "Polarity".

### M-2. One direction only, so a loop minted

doc-1.1 counted one pulse train. Energy bought from the grid into a battery and pushed back out through the same terminals produced real pulses and real tokens. Revision B counts export (LED1) and import (LED2) separately and mints on the net-export high-water mark. The test `test_battery_loop_mints_nothing` runs a 3 kW nightly loop through a simulated site and mints exactly what the site without the loop mints.

### M-3. SPI MOSI changed on the rising clock edge

`spi_byte.v` set MOSI and raised SCK on the same clock edge for bits 1 to 7, so a mode-0 slave sampling on the rising edge would race. It now moves MOSI when SCK falls.

### M-4. No wait for the signature

The sign transaction clocked 2420 signature bytes immediately after the record. ML-DSA signing takes milliseconds; the first bytes would have been whatever the secure element's SPI idle fill was. Revision B polls for a ready byte (`5A`) or a refusal (`EE`), with a 1.1 s timeout, then streams one byte from the signer to the UART at a time. That also removes the 2420-byte signature buffer from the die.

### M-5. STPM32 interface selection and chip-select polarity

EN was tied high by a pull-up and the die drove SCS active high, idling low. A standard SPI chip select is active low, and the STPM3x family picks its serial interface from the SCS level when EN rises; with EN tied high that level was whatever EC-MINT1's reset state happened to be. Revision B gives EC-MINT1 an `STP_EN` pin and an active-low `STP_CS_N`, and sequences SCS low across the EN rising edge. Both the polarity and the timing are to be confirmed against DocID025358 (O-2); the RTL makes them one-line changes.

### M-6. Fuse sized for a resistive load

A 100 mA time-lag fuse in front of a capacitor-input supply sees an inrush of about 34 A for under 0.1 ms through the 10 Ω surge resistor, I²t ≈ 0.05 A²s, on every power-up. Revision B uses 250 mA T. The surge rating of R1 for that pulse is O-6.

### M-7. Counter widths

`n` was 16 bits (65 535 tokens, a few years of a home array) and W 32 bits (4.3 GWh, a few hours of a 1 GW plant). Revision B uses 48 bits for every cumulative register.

### M-8. Signer-rail switch and discharge overlap (doc-1.3)

Q5 and Q4 share CROW_G, a 220 kΩ / 1 µF delay (τ = 0.22 s). Q5 opens once CROW_G passes VDD − |V_th| (2.4–2.9 V for the DMG2305UX); Q4 closes once CROW_G passes its own V_th (1.0–2.5 V for the 2N7002). In the typical case Q4 turns on first, at about 0.22·ln(3.3/1.2) ≈ 0.22 s, and Q5 only opens at about 0.29 s, so with R23 at 47 Ω the overlap would again draw 70 mA from the 50 mA regulator, the C-4 brownout. doc-1.3 makes R23 1 kΩ (same 1206 land): the overlap draws at most 3.3 mA, and the isolated rail (C15, 100 nF) still discharges with a 0.1 ms time constant. Open item O-10 is the bench check.

## Minor

- R17, 2.2 kΩ, needed about 0.4 mA of photocurrent before the light sensor could trip the latch with the cover spring still closed. 10 kΩ needs about 70 µA and still holds MESH at 0.30 V, under the 0.9 V threshold. The real photocurrent at bench lighting is test step 3.
- The BOM and centroid writers did not quote `"provision, seal over"`, which split the J5 row into an extra column.
- `tb_mint.v` did not compile against the doc-1.1 top: every port name was wrong. It is replaced by `tb_ec_mint1.v`.
- `tools/gen_board.py` printed clearance failures but still wrote the Gerbers and exited 0. It now exits non-zero.
- The top 40 A pour ran to 2 mm from the board edge against the 3 mm rule. It now stops at 3 mm.

## Rechecked and kept

| Item | Check | Result |
| --- | --- | --- |
| Shunt | 100 µΩ, 40 A: 4.0 mV rms, 0.16 W | Kept |
| Current channel | 5.66 mV pk × 16 = 90 mV against ±300 mV; clips near 130 A rms | Kept |
| Divider | 240 V → 0.120 V rms; 264 V → 0.187 V pk < 0.3 V; 177.5 V per part at the 710 V MOV clamp, 700 V rating | Kept, moved to Neutral |
| MOV | 275 V ac continuous, above 240 V + 10 % | Kept, now Neutral to Line after the fuse |
| LM2936 | 40 V input, 50 mA output; 0.26 W at 30 mA from 12.1 V | Kept, logic only |
| Tamper latch | Q2 on at MESH ≈ 0.9 V; R21 gives ~265 µA of hold current against at most ~13 µA through R18 | Kept |
| Crystal loads | 27 pF C0G for an 18 pF crystal with a few pF of stray | Kept |
| FRAM endurance | 10¹⁴ cycles; at 9.6 kW about 10⁸ writes a year | New part, adequate |

## Not closed by this review

See [open-items.md](open-items.md). The ones that keep revision B on the bench are O-1 (tamper while unpowered) and O-2 (STPM32 LED direction and interface selection).
