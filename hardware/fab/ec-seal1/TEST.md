# EC-SEAL1 test

Edition: doc-1.1. Do this on a current-limited bench supply first, not on the mains.

## Dead board

1. No power. Continuity from H3 to U1 ground, and from H3 to U2 VIN1. No continuity from H1 to H3.
2. Shunt force path H2 to H1 is a short through 100 µΩ. Kelvin pads are not that short to each other through a trace; they meet only inside the shunt.
3. Cover spring held closed. MESH node is under 0.3 V when 3.3 V is applied through R16. Spring released, and no light on PT1, MESH rises and ZEROIZE latches high and stays high after the spring is closed again. Power cycle clears the latch only. It must not clear a key that was wiped.

## Powered from 12 V on VRECT, dropper disconnected

4. VDD is 3.3 V ± 3%. QS_VDD is within 50 mV of it while Q4 is off.
5. STPM32 VDDD is about 1.2 V, produced by the chip, not by the board.
6. A 16 MHz square wave is on EC-MINT1 XI. CAL_LOCKED stays low until the ROM is shifted in.

## Current and voltage

7. A 1.000 A source through the shunt, Kelvin measured at the STPM32 pins, is 100 µV ± 5% plus the 100 Ω resistors' drop, which is zero at DC into the CMOS input. The check is the 100 µV on the shunt sense pads.
8. 240 V rms on H1 to H3, with a series 10 kΩ safety resistor if the dropper is in circuit, produces 0.120 V rms ± 1% on VIP_S. If it is near 0.5 V, the divider is the old one. Stop.

## Tokens

9. After the ROM is locked, 1000 pulses on LED1 produce one UART frame whose n field is 1 and whose W field grew by 1000. The executable check of that rule is `tools/check_schedule.py`.
10. A second board fed the same current and voltage, within the class window, produces a W that the ledger will accept as the pair. One board alone must not be treated as an issuance. That rule is in the ledger, and the test is that each board's signature verifies under its own key and that the two watt-hour totals match.

## Tamper under power

11. Release the spring. Within one second the signer rail is pulled down by Q4, EC-MINT1 has sent `5C 5C` on the signer MOSI, and a further pulse on LED1 does not produce a UART frame.
