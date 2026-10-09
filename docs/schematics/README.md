# Circuit sheets

Edition: doc-0.7 (2026-10-08). Symbols follow IEC 60617: a resistor is a rectangle, a capacitor is two plates, a diode is a triangle and bar, ground is the stacked earth mark. These are proposed circuits, not a built board.

The block sketch remains [mint-path.svg](mint-path.svg). Each block now has its own sheet.

| Sheet | Circuit | Design point |
| --- | --- | --- |
| [01-supply.svg](01-supply.svg) | Fuse, MOV, X2 dropper, bridge, 12 V clamp, 3.3 V LDO | 220 nF at 240 V, 50 Hz draws about 16 mA. Zener heat about 0.19 W. Tap is before the shunt. |
| [02-shunt.svg](02-shunt.svg) | 100 µΩ four-terminal shunt into the current ADC | 4.0 mV and 0.16 W at 40 A. Sense nodes are Kelvin. |
| [03-divider.svg](03-divider.svg) | 2 × 499 kΩ over 2.08 kΩ, 1 nF across the lower arm | 240 V rms maps to 0.50 V rms. Divider heat 0.058 W. |
| [04-metrology.svg](04-metrology.svg) | Fixed-function energy ASIC, crystal, decouple, CF out | 1000 impulses per kWh. SPI unbonded. |
| [05-secure-element.svg](05-secure-element.svg) | Element woken by CF, ML-DSA-44, sleep | 1000 pulses mint one token. Key stays on die. |
| [06-tamper.svg](06-tamper.svg) | 100 kΩ pull-up, normally closed mesh to ground | Open mesh pulls ZEROIZE low and erases the key. |
| [07-radio.svg](07-radio.svg) | Slept 2.4 GHz radio, pi match, antenna | 1 mJ per posting. Radio holds no key. |
| [08-burden-chart.svg](08-burden-chart.svg) | Average draw against the 2 W cap | Continuous sum about 0.5 W. |

Equations for the supply current and the divider ratio are on those sheets and in [meter-burden.md](../meter-burden.md).
