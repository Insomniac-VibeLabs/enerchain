# EC-SEAL1 circuits

Edition: doc-1.1. Voltages are the 240 V rms, 50/60 Hz service the divider is calculated for. 120 V service uses the same board; the integral is smaller because the voltage is smaller, which is what the meter is supposed to report.

## Supply

Ground of the logic is Neutral. One net, named GND: the H3 stud, the MOV neutral pin, the rectifier return, the LDO ground, and the inner plane. The dropper is a half-wave capacitor supply so the meter current does not pass through the shunt.

```
L_GRID -- F1 100 mA -- L_FUSED -- C1 330 nF X2 -- R3 100 ohm -- RECT_AC
                              |                              |
                              RV1 275 VAC                    D1 anode, cathode to N
                                                             D2 anode, cathode to VRECT
N ---------------------------------------------------------------------
                              |
                             Z1 12 V from VRECT to N
                             C2 470 uF from VRECT to N
                             U1 LM2936, IN=VRECT, OUT=VDD 3.3 V, GND=GND
```

R1 and R2, 1 MΩ each, 700 V, sit across C1 so the X2 capacitor cannot stay charged. At 50 Hz the 330 nF dropper sources about 25 mA. The zener takes what the logic does not. LM2936 is used because its input can take the 12 V rail; a 6 V LDO cannot.

D1 returns the negative half-cycle into Neutral. D2 is the positive rectifier. Both are 1000 V SMA.

## Current

RS is 100 µΩ, four terminal. Force current is L_GEN to L_GRID. At 40 A the sense voltage is 4.0 mV and the burden is 0.16 W.

R10 and R11, 100 Ω 0.1%, stand in the Kelvin leads. C6, 10 nF C0G, is across the STPM32 current inputs. Gain 16 in the factory ROM puts 4 mV at about a fifth of the ±300 mV pin window.

## Voltage

Four TNPV1206 499 kΩ resistors in series from L_GRID to VIP_S, then R8 1.00 kΩ to Neutral. The ratio is 1000 / 1,997,000. At 240 V rms the STPM32 pin sees 0.120 V rms, 0.170 V peak, inside the ±0.3 V pin rating. The doc-0.9 divider at 0.50 V rms was not.

R9, 1 kΩ, isolates the pin. TVS1 is a 5 V bidirectional part so a surge has somewhere to go and the normal waveform is not clipped. C5, 10 nF, is across R8.

## Meter chip

U2 is the STPM32. Pin numbers are DocID025358 Figure 4:

| Pin | Name | Net |
| --- | --- | --- |
| 1 | CLKOUT | no connect |
| 2 | CLKIN/XTAL2 | crystal |
| 3 | XTAL1 | crystal |
| 4 | LED1 | watt-hour pulse, 1000 per kWh |
| 5 | LED2 | no connect |
| 6 | INT1 | no connect |
| 7 | EN | 10 kΩ to 3.3 V |
| 8 | VIP1 | voltage sense |
| 9 | VIN1 | Neutral |
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
| 21 | SCS | EC-MINT1, boot only |
| 22 | SCL | EC-MINT1 |
| 23 | MOSI | EC-MINT1 |
| 24 | MISO | EC-MINT1 |

The crystal is 16.000 MHz with two 27 pF C0G loads. SPI is replayed from EC-MINT1 at power-up because the STPM32 configuration is volatile. After the replay, the counter runs from LED1 only.

## Pulse buffer

LED1 is pulled to 3.3 V by 10 kΩ. R14, 100 Ω, and C13, 100 pF, feed the gate of Q1, a 2N7002. Source is ground. Drain is CF, pulled up by R15, 10 kΩ. EC-MINT1 pin 3 counts the rising edges. One token is 1000 edges, which is 1 kWh at this CF rate.

## Tamper latch

This is the part that is transistors on purpose. No firmware can clear it except by removing power, and removing power does not restore the key.

- R16, 100 kΩ, pulls MESH up to 3.3 V.
- R17, 2.2 kΩ, and the cover spring SW1 hold MESH down while the cover is on.
- PT1, a VEMT3700, collector on 3.3 V and emitter on MESH. Light sources current into MESH. With the spring still closed, that current in 2.2 kΩ lifts MESH through a transistor base.
- R18, 47 kΩ, from MESH to Q2 base. Q2 is an MMBT3904, emitter ground. R19, 100 kΩ, holds that base down so an open mesh is the only thing that turns it on.
- Q3 is an MMBT3906, emitter on 3.3 V. R20, 10 kΩ, from Q2 collector to Q3 base.
- R21, 10 kΩ, from Q3 collector back to Q2 base. That is the latch. Once it fires it stays, even if the spring is pushed closed again.
- Q3 collector is ZEROIZE, active high, into EC-MINT1 pin 4 and QS7001 GPIO3.
- R22, 220 kΩ, and C14, 1 µF, delay the gate of Q4, a second 2N7002, by about a fifth of a second. Q4 then shorts the signer rail to ground. R23, 47 Ω, 0.25 W, feeds that rail from 3.3 V, so the short is a current limit and not a weld. The delay is there so EC-MINT1 can issue the wipe command before the signer rail collapses.

## Signer and schedule

U3 is EC-MINT1. U4 is the QS7001. The SPI between them is not shared with the radio. Pin lists are [../../asic/PINOUT.md](../../asic/PINOUT.md) and the QS7001 summary 6658GS figure (pin 1 VCC, pin 17 reset, pin 19 clock, pin 20 chip select, pin 21 MOSI, pin 24 MISO).

Y2 is a 3.3 V CMOS oscillator, 16.000 MHz, into EC-MINT1 XI. The die does not grow a Pierce cell. R24, 100 kΩ, holds RST_N up. R25, 100 kΩ, holds the signer reset up until EC-MINT1 drives it down after a wipe.

## Radio

J4 is six pins. Pin 1 is 3.3 V, pins 2 and 3 are ground, pin 4 is the UART from EC-MINT1 through R26, 100 Ω. Pins 5 and 6 are empty. There is no receive path.
