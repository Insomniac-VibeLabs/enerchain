# EC-MINT1 specification

Edition: doc-1.0.

## Rails

- VDD_IO 3.3 V, meter LDO.
- VDD_CORE 1.2 V, on-die regulator from VDD_IO.
- VSS common.
- Decouple 100 nF on each rail at the package.

## Clock

16.384 MHz on XI/XO, or a CMOS clock on XI with XO open. Reset is asynchronous, active low, synchronized inside.

## Pins

| Pin | Dir | Function |
| --- | --- | --- |
| VDD_IO, VDD_CORE, VSS | power | rails |
| XI, XO | in/out | 16.384 MHz |
| RST_N | in | async reset, active low |
| CF_IN | in | watt-hour pulse, 3.3 V |
| ZEROIZE | in | active high, clears key |
| TX | out | signed record, 115200 8N1 |
| PROV_CS, PROV_SCK, PROV_MOSI | in | one-time key load |
| PROV_MISO | out | status only, never the key |
| MINT | out | one-cycle token pulse |

## Packet on TX

id[31:0], t0[31:0], t1[31:0], w[31:0], n[15:0], W[31:0], r[15:0], class[7:0], then sig bytes. n is 1 when 1000 watt-hour pulses have accumulated.

## Power

Sign is the peak. Budget the core so average draw of this die stays inside the meter’s 2 W cap with the radio asleep. Target core average under 20 mW.
