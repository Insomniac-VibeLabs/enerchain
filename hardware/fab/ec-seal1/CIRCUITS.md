# EC-SEAL1 circuits

Edition: v0.0.1 (doc-1.3), board revision B. Voltages are the 240 V rms, 50/60 Hz service the divider is calculated for. 120 V service uses the same board; the supply is universal-input and the integral is smaller because the voltage is smaller, which is what the meter is supposed to report.

Why revision B exists, in one paragraph: in doc-1.1 logic ground was Neutral while the shunt sat in Line, so the STPM32 current inputs were at full mains voltage; the half-wave dropper had D1 reversed and could not charge its rail; even with D1 turned round, 330 nF could source about 11 mA at 240 V and 6.5 mA at 120 V, under the logic load; the signer was fed through 47 Ω; and export energy came out with a negative sign. The calculations are in [docs/electrical-review.md](../../../docs/electrical-review.md).

## Ground reference

Logic ground is the Line conductor on the grid side of the shunt. One net, named GND: the H1 stud, the shunt's grid-side force pad, the top-edge strip to via TV1, and the inner ground plane. Neutral (net N) is the other mains terminal, H3. Every low-voltage part on this board is therefore at Line potential. The cover is the insulation; see [TEST.md](TEST.md) before putting a probe on it.

Tying ground to the shunt is what lets a single shunt feed the STPM32 current inputs: both Kelvin leads sit within a few millivolts of ground.

## Supply

```
N --- F1 250 mA T --- N_F --- R1 10 ohm --- N_R --- D1 >|--- VB1 --- L1 1 mH --- VBULK
                       |                                     |                    |
                      RV1 275 VAC to GND (Line)            C1 4.7u 400V        C16 4.7u 400V
                                                             to GND              to GND
VBULK --- U5 LNK304 D;  U5 S = SW;  D3 ES1J from GND (anode) to SW (cathode)
SW --- L2 1 mH --- VRECT (12 V) --- C2 470u 25V, Z1 15 V clamp, R27 3.3 k preload, U1 LM2936 -> VDD 3.3 V
Feedback, riding on SW: D2 from VRECT to FBC, C18 10u FBC-SW, R2 13.0 k FBC-FB, R3 2.05 k FB-SW, C17 100 nF BP-SW
```

U5 is a Power Integrations LNK304DG high-side buck in its standard non-isolated configuration. When D3 conducts, SW sits a diode drop below ground, D2 charges C18 to about VRECT, and the R2/R3 divider presents that to FB. VRECT = 1.65 V × (1 + 13.0 k / 2.05 k) ≈ 12.1 V. The input is half-wave rectified from Neutral with respect to Line, filtered by the C1–L1–C16 π network.

- Capability: the LNK304 is specified for up to 120 mA in this topology, from 85 to 265 V ac. The board needs about 30 mA for logic plus whatever the radio draws on J4 (budget 40 mA average at 12 V).
- Burden: 12 V × 70 mA ÷ an assumed 0.6 light-load efficiency ≈ 1.4 W worst case with the radio transmitting, inside the 2 W cap. With the radio asleep it is well under 1 W. Input volt-amperes are a few VA, inside the 10 VA limit; the doc-1.1 dropper was a reactive load.
- R1 limits the inrush into C1 and C16 to about 34 A peak for under 0.1 ms (I²t ≈ 0.05 A²s). F1 is a 250 mA time-lag fuse so that inrush does not age it. The doc-1.1 100 mA fuse is too small for a capacitor-input supply.
- Z1 (15 V) clamps a start-up overshoot. C2 is rated 25 V. LM2936 accepts 40 V on its input.
- LM2936 dissipation is (12.1 − 3.3) V × 30 mA ≈ 0.26 W in SOT-223.

The LM2936 is limited to 50 mA. It feeds logic only. The radio header J4 pin 1 is VRECT, so the radio's transmit current does not pass through the 3.3 V regulator.

## Current

RS is 100 µΩ, four terminal. Force current is L_GEN to GND (the grid-side Line). At 40 A the sense voltage is 4.0 mV rms, 5.66 mV peak, and the burden is 0.16 W.

R10 and R11, 100 Ω 0.1%, stand in the Kelvin leads. C6, 10 nF C0G, is across the STPM32 current inputs. IIP1 is the grid-side Kelvin pad (SI), IIN1 the generator-side pad (SG). Gain 16 in the factory transcript puts 5.66 mV peak at about 90 mV at the modulator, under a third of the ±300 mV window: a peak current of roughly 130 A rms before clipping.

## Voltage

Four TNPV1206 499 kΩ resistors in series from N to VIP_S, then R8 1.00 kΩ to ground (Line). The ratio is 1000 / 1,997,000. At 240 V rms the STPM32 pin sees 0.120 V rms, 0.170 V peak; at 264 V (+10 %) 0.187 V peak, inside the ±0.3 V pin rating. Each 499 kΩ part drops 60 V rms and 177.5 V at the MOV clamp (710 V across the string), against a 700 V rating. The string dissipates 29 mW.

R9, 1 kΩ, isolates the pin. TVS1 is a 5 V bidirectional part so a surge has somewhere to go and the normal waveform is not clipped. C5, 10 nF, is across R8.

## Polarity

The divider measures V(N) − V(L) = −v_LN. Export current runs from the generator stud to the grid stud through the shunt, so V(SG) − V(SI) = +i·R. With IIP1 on SI and IIN1 on SG the current channel reads −i·R. The product is (−v)(−i) = +p: export is positive active power. In doc-1.1 the same Kelvin wiring with a Line-referenced divider read export as negative.

## Meter chip

U2 is the STPM32. Pin numbers are DocID025358 Figure 4:

| Pin | Name | Net |
| --- | --- | --- |
| 1 | CLKOUT | no connect |
| 2 | CLKIN/XTAL2 | crystal |
| 3 | XTAL1 | crystal |
| 4 | LED1 | export watt-hour pulse, 1000 per kWh |
| 5 | LED2 | import watt-hour pulse, 1000 per kWh |
| 6 | INT1 | no connect |
| 7 | EN | STP_EN from EC-MINT1, 10 kΩ pull-down (R12) |
| 8 | VIP1 | voltage sense |
| 9 | VIN1 | ground (Line) |
| 10 | IIP1 | Kelvin grid side |
| 11 | IIN1 | Kelvin generator side |
| 12 | VREF1 | 1 µF to ground |
| 13 | GND_REF | ground |
| 14 | GNDA | ground |
| 15 | VDDA | 100 nF, do not power this pin |
| 16 | GND_REG | ground |
| 17 | VCC | 3.3 V |
| 18 | GNDD | ground |
| 19 | SYN | ground |
| 20 | VDDD | 100 nF, the 1.2 V regulator output |
| 21 | SCS | STP_CS_N from EC-MINT1, active low |
| 22 | SCL | EC-MINT1 |
| 23 | MOSI | EC-MINT1 |
| 24 | MISO | EC-MINT1 |

The crystal is 16.000 MHz with two 27 pF C0G loads. EC-MINT1 holds EN low out of reset, takes SCS low, raises EN so the part latches the SPI interface, then replays the configuration transcript because the STPM32 configuration is volatile. After the replay the counter runs from the LED pins only. That LED1 can be restricted to positive and LED2 to negative active energy, and the exact EN/SCS selection timing, are open item O-2 in [docs/open-items.md](../../../docs/open-items.md).

## Pulse buffers

LED1 is pulled to 3.3 V by R13, 10 kΩ. R14, 100 Ω, and C13, 100 pF, feed the gate of Q1, a 2N7002. Source is ground. Drain is CF_EXP, pulled up by R15, 10 kΩ, into EC-MINT1 pin 3.

LED2 is the same circuit: R28 pull-up, R29 and C19 into Q6, drain CF_IMP pulled up by R30 into EC-MINT1 pin 25.

## FRAM

U6 is an FM25V02A-G, 256 Kbit SPI F-RAM, 2.0–3.6 V, 10¹⁴ write cycles. /WP and /HOLD are tied high. C20 decouples it. EC-MINT1 is its only master. It holds the counters, the sequence number and the calibration image; the layout is in [../../asic/spec.md](../../asic/spec.md).

## Tamper latch

This is the part that is transistors on purpose. No firmware can clear it except by removing power.

- R16, 100 kΩ, pulls MESH up to 3.3 V.
- R17, 10 kΩ, and the cover spring SW1 hold MESH down while the cover is on: 3.3 V × 10 k / 110 k = 0.30 V.
- PT1, a VEMT3700, collector on 3.3 V and emitter on MESH. With the spring still closed, about 70 µA of photocurrent lifts MESH past the Q2 threshold: at 0.88 V, R17 sinks 88 µA and R18 + R19 6 µA, while R16 sources 24 µA. (doc-1.1 used 2.2 kΩ, which needed about 0.4 mA.)
- R18, 47 kΩ, from MESH to Q2 base. Q2 is an MMBT3904, emitter ground. R19, 100 kΩ, holds that base down. Q2 turns on at MESH ≈ 0.6 V × (1 + 47/100) ≈ 0.9 V.
- Q3 is an MMBT3906, emitter on 3.3 V. R20, 10 kΩ, from Q2 collector to Q3 base.
- R21, 10 kΩ, from Q3 collector back to Q2 base: (3.3 − 0.6) V / 10 kΩ ≈ 270 µA, about 265 µA of base drive after R19. That is the latch. Closing the cover again sinks at most about 13 µA through R18 (MESH at 0 V), so the latch holds.
- Q3 collector is ZEROIZE, active high, into EC-MINT1 pin 4 and QS7001 GPIO3.

## Signer rail

Q5, a DMG2305UX P-channel MOSFET, switches VDD onto QS_VDD. Its gate is CROW_G: ZEROIZE delayed by R22, 220 kΩ, and C14, 1 µF. While CROW_G is low Q5 is fully on; the rail drop is millivolts. About 0.3 s after ZEROIZE rises, CROW_G passes VDD − |V_th| and Q5 opens; Q4, a 2N7002 on the same gate, discharges QS_VDD through R23, 1 kΩ. The two thresholds (Q4 1.0–2.5 V, Q5 −0.4 to −0.9 V) overlap, so for up to about 0.2 s both can conduct; R23 holds that to 3.3 V / 1 kΩ = 3.3 mA, which the regulator does not notice. EC-MINT1 sends `5C 5C` within microseconds of ZEROIZE, long before the rail opens.

doc-1.1 fed the signer through a 47 Ω R23 directly and shorted the rail with Q4. Revision B as first drawn kept 47 Ω for the discharge path, which in the overlap above would again have drawn 70 mA; doc-1.3 makes it 1 kΩ. The QS7001's signing current through 47 Ω would have dropped about 1 V, and firing the crowbar drew 70 mA from a 50 mA regulator, browning out the whole board.

The latch and the erase need power. Opening the cover while the meter is unpowered is not detected. That is open item O-1, and it is why revision B is a bench prototype, not a field meter.

## Signer and schedule

U3 is EC-MINT1. U4 is the QS7001. The SPI between them is not shared with the radio or the FRAM. Pin lists are [../../asic/PINOUT.md](../../asic/PINOUT.md) and the QS7001 summary 6658GS figure (pin 1 VCC, pin 17 reset, pin 19 clock, pin 20 chip select, pin 21 MOSI, pin 24 MISO); the QS7001 pin map must be confirmed against the vendor datasheet, open item O-3.

Y2 is a 3.3 V CMOS oscillator, 16.000 MHz, into EC-MINT1 XI. R24, 100 kΩ, holds RST_N up. R25, 100 kΩ, holds the signer reset up until EC-MINT1 drives it down after a wipe.

## Radio

J4 is six pins. Pin 1 is VRECT, 12 V, pins 2 and 3 are ground, pin 4 is the UART from EC-MINT1 through R26, 100 Ω. Pins 5 and 6 are empty. There is no receive path. The radio module regulates its own supply, must average under 40 mA at 12 V, and must carry a 2454-byte frame (a record and its signature) for every token, every kWh.
