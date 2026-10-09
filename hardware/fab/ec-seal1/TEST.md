# EC-SEAL1 test

Edition: v0.0.1 (doc-1.2), board revision B.

Every low-voltage net on this board, ground included, is at Line potential. Bench it from a current-limited DC supply first. When the board sees the mains, feed it through an isolation transformer and a series current limiter, and use a differential or isolated probe. Never clip an earthed scope ground to GND.

## Dead board

1. No power. Continuity from H1 to U1 ground, to U2 VIN1, and to TV1. No continuity from H3 (Neutral) to H1. H3 reaches R4 pin 1 and F1 pin 1.
2. Shunt force path H2 to H1 is a short through 100 µΩ. Kelvin pads are not that short to each other through a trace; they meet only inside the shunt.
3. Cover spring held closed. MESH node is 0.30 V ± 0.05 V when 3.3 V is applied through R16. Spring released, and no light on PT1, MESH rises and ZEROIZE latches high and stays high after the spring is closed again. Spring closed, light on PT1 at bench lighting, ZEROIZE latches. Power cycle clears the latch only. It must not restore a key that was wiped.

## Supply, from DC

4. 300 V DC from a current-limited supply into VBULK (positive) and GND, dropper side disconnected at R1. VRECT is 12.1 V ± 0.5 V. VDD is 3.3 V ± 3 %. QS_VDD is within 20 mV of VDD while ZEROIZE is low.
5. Load VRECT with an extra 40 mA. VRECT stays above 11 V and the LM2936 does not drop out.
6. STPM32 VDDD is about 1.2 V, produced by the chip, not by the board.
7. A 16 MHz square wave is on EC-MINT1 XI. STP_EN is low, CAL_LOCKED is low, and no CF pulse is counted until the image is shifted in.

## Current and voltage

8. A 1.000 A DC source through the shunt, Kelvin measured at the STPM32 pins, is 100 µV ± 5 % on the shunt sense pads.
9. Through the isolation transformer, 240 V rms on H3 to H1 produces 0.120 V rms ± 1 % on VIP_S. If it is near 0.5 V, the divider is the doc-0.9 one. Stop.
10. Polarity: drive current from H2 to H1 (export) in phase with the voltage. LED1 pulses, LED2 does not. Reverse the current. LED2 pulses, LED1 does not.

## Provisioning and tokens

11. Shift the calibration image on J5. CAL_LOCKED rises. The image and its lock marker are in FRAM at 0x0100 and 0x0200. On the next boot STP_EN rises with STP_CS_N low, then the transcript is replayed.
12. 10 000 export pulses produce one UART frame: `EC 01`, a 32-byte record with seq 1, e_exp 10 000, tokens 10, then the signature. `tools/check_schedule.py` is the rule; `enerchain frame verify --pk <meter key> <frame hex>` checks the signature.
13. 5000 import pulses followed by 5000 export pulses produce no token.
14. Remove power between records and in the middle of a pulse burst. After power returns the counters and seq continue from FRAM; nothing is counted twice.
15. The other board of the pair, same current and voltage, its own key. One board's signature is not an issuance; the ledger mints min(GEN tokens, GRID tokens).

## Tamper under power

16. Release the spring. Within a millisecond the signer MOSI has carried `5C 5C`; within half a second QS_VDD has collapsed; a further pulse on LED1 produces no frame; VDD stays at 3.3 V.
