# EC-MINT1 pinout

Edition: doc-1.1. Package is QFN-32, 5.00 mm × 5.00 mm, 0.50 mm pitch, exposed pad. Pin 1 is the top-left corner of the top view, then counterclockwise.

The bond diagram is the pin list. Do not swap pins to make the place-and-route easier.

| Pin | Name | Dir | Net on EC-SEAL1 | Note |
| --- | --- | --- | --- | --- |
| 1 | VDD_IO | power | VDD | 3.3 V |
| 2 | VSS | power | GND | |
| 3 | CF_IN | in | CF | From the 2N7002 buffer, active high pulse |
| 4 | ZEROIZE | in | ZEROIZE | Active high, from the transistor latch |
| 5 | RST_N | in | RST_N | Active low, 100 kΩ to VDD on the board |
| 6 | MINT | out | MINT | One-cycle test point, no load required |
| 7 | UART_TX | out | UART_TX | 8N1, 139 clocks/bit at 16 MHz |
| 8 | QS_SCK | out | QS_SCK | SPI mode 0 master to the signer |
| 9 | QS_MOSI | out | QS_MOSI | |
| 10 | QS_MISO | in | QS_MISO | |
| 11 | QS_CS_N | out | QS_CS_N | Active low |
| 12 | QS_RST_N | out | QS_RST | Open, driven high. Driven low after a wipe |
| 13 | STP_SCK | out | STP_SCK | SPI to the STPM32, boot only |
| 14 | STP_MOSI | out | STP_MOSI | |
| 15 | STP_MISO | in | STP_MISO | |
| 16 | STP_CS | out | STP_CS | Active high while a boot frame is in flight |
| 17 | XI | in | XI | 16.000 MHz CMOS. No crystal pins on this die |
| 18 | PROV_CS | in | PROV_CS | Factory pogo only |
| 19 | PROV_SCK | in | PROV_SCK | |
| 20 | PROV_MOSI | in | PROV_MOSI | ROM bits, never read back |
| 21 | PROV_MISO | out | PROV_MISO | Locked flag only |
| 22 | CAL_LOCKED | out | CAL_LOCKED | High after the ROM lock |
| 23 | VDD_IO | power | VDD | |
| 24 | VSS | power | GND | |
| 25–31 | VSS | power | GND | Bond to the pad ring ground |
| 32 | VSS | power | GND | |
| EP | VSS | power | GND | Soldered pad, vias to the ground plane |

Core voltage is an on-die 1.2 V regulator from VDD_IO. The board does not supply 1.2 V to this package. Standard-cell library choice is the foundry’s. Schedule behavior is not.

## Boot ROM

256 bytes, shifted in on PROV before the seal, then locked. Bytes 0–1 are `A5 5A`. Bytes 3–6 are the meter id. Frames start at byte 7: a length byte, that many SPI bytes with CS asserted, repeated, then a `00` length. An image whose frame list is empty does not arm the counter. The factory captures the golden STPM32 transcript (1000 impulses per kWh, current gain 16, voltage channel inside ±0.3 V, calibration words) and stores that transcript. This die replays it. It does not contain a second copy of the metrology DSP.

## Sign transaction

To the QS7001, and to nobody else:

1. CS low, command `A1`, 32-byte record, CRC-8 (poly `0x07`, init `0`) over the 32 bytes.
2. Clock in 2420 signature bytes.
3. CS high.
4. UART the 32-byte record, then the 2420 signature bytes, 8N1.

The record is meter id (4), t0 (4, zero in this RTL; anti-replay is W), t1 (4, zero), w = 1000 (`00 00 03 E8`), n (2), W (4, cumulative watt-hours), r (2), class `0x22`, then 7 zero pad bytes.

Wipe is command `5C 5C`, then QS_RST_N is held low and the counter stops.
