# EC-MINT1 pinout

Edition: v0.0.1 (doc-1.4). Package is QFN-32, 5.00 mm × 5.00 mm, 0.50 mm pitch, exposed pad. Pin 1 is the top-left corner of the top view, then counterclockwise.

The bond diagram is the pin list. Do not swap pins to make the place-and-route easier.

doc-1.2 changes: pin 3 is now `CF_EXP` (export pulses), pin 16 is `STP_CS_N` (active low), and pins 25–30 carry the import pulse input, the FRAM bus and the STPM32 enable. Those pins were spare VSS in doc-1.1. Pins 31, 32 and the exposed pad remain ground.

| Pin | Name | Dir | Net on EC-SEAL1 | Note |
| --- | --- | --- | --- | --- |
| 1 | VDD_IO | power | VDD | 3.3 V |
| 2 | VSS | power | GND | |
| 3 | CF_EXP | in | CF_EXP | Export watt-hour pulse from the LED1 buffer, active high |
| 4 | ZEROIZE | in | ZEROIZE | Active high, from the transistor latch |
| 5 | RST_N | in | RST_N | Active low, 100 kΩ to VDD on the board |
| 6 | MINT | out | MINT | One-cycle pulse per token. Test point, no load required |
| 7 | UART_TX | out | UART_TX | 8N1, 139 clocks/bit at 16 MHz |
| 8 | QS_SCK | out | QS_SCK | SPI mode 0 master to the signer, 8 MHz |
| 9 | QS_MOSI | out | QS_MOSI | |
| 10 | QS_MISO | in | QS_MISO | |
| 11 | QS_CS_N | out | QS_CS_N | Active low |
| 12 | QS_RST_N | out | QS_RST | Driven high. Driven low after a wipe |
| 13 | STP_SCK | out | STP_SCK | SPI to the STPM32, boot only |
| 14 | STP_MOSI | out | STP_MOSI | |
| 15 | STP_MISO | in | STP_MISO | |
| 16 | STP_CS_N | out | STP_CS_N | Active low. Low across the EN rising edge selects SPI |
| 17 | XI | in | XI | 16.000 MHz CMOS. No crystal pins on this die |
| 18 | PROV_CS | in | PROV_CS | Factory pogo only |
| 19 | PROV_SCK | in | PROV_SCK | |
| 20 | PROV_MOSI | in | PROV_MOSI | Calibration image bits, never read back |
| 21 | PROV_MISO | out | PROV_MISO | Locked flag only |
| 22 | CAL_LOCKED | out | CAL_LOCKED | High once a valid image is locked in FRAM |
| 23 | VDD_IO | power | VDD | |
| 24 | VSS | power | GND | |
| 25 | CF_IMP | in | CF_IMP | Import watt-hour pulse from the LED2 buffer, active high |
| 26 | FR_CS_N | out | FR_CS_N | FRAM chip select, active low |
| 27 | FR_SCK | out | FR_SCK | FRAM SPI mode 0, 8 MHz |
| 28 | FR_MOSI | out | FR_MOSI | |
| 29 | FR_MISO | in | FR_MISO | |
| 30 | STP_EN | out | STP_EN | STPM32 EN. Low out of reset; 10 kΩ pull-down on the board |
| 31 | VSS | power | GND | |
| 32 | VSS | power | GND | |
| EP | VSS | power | GND | Soldered pad, vias to the ground plane |

Core voltage is an on-die 1.2 V regulator from VDD_IO. The board does not supply 1.2 V to this package. Standard-cell library choice is the foundry’s. Schedule behavior is not.

## Calibration image

256 bytes, shifted in on PROV once, MSB first, before the seal. EC-MINT1 then writes the image to FRAM at 0x0100 with a lock marker (`'L' 'K'` and a CRC-16) at 0x0200, and reads it back on every boot. Once a valid marker exists, PROV is ignored for the life of the board. doc-1.1 held this image in flops, so it vanished at the first power cut and the meter never armed again.

| Bytes | Content |
| --- | --- |
| 0–1 | `A5 5A` |
| 2 | Role: `01` GEN (generator terminals), `02` GRID (point of connection) |
| 3–6 | Meter id, big-endian |
| 7… | STPM32 frames: a length byte, that many SPI bytes with CS low, repeated, then a `00` length |

An image with a bad header, another role, or an empty frame list does not arm the counter. The factory captures the golden STPM32 transcript — 1000 impulses per kWh on LED1 for export and on LED2 for import, current gain 16, voltage channel inside ±0.3 V, calibration words — and stores that transcript. This die replays it. It does not contain a second copy of the metrology DSP. Register addresses are not invented in this tree; see [docs/open-items.md](../../docs/open-items.md) O-2.

## Sign transaction

To the QS7001, and to nobody else:

1. CS low, command `A1`, the 32-byte record, CRC-8 (poly `0x07`, init `0`) over the 32 bytes.
2. Clock `00` until the signer answers `5A` (signature follows) or `EE` (refused). Give up after about 1.1 s.
3. On `5A`: UART `EC 01` and the 32-byte record, then clock one signature byte at a time and UART each one before clocking the next.
4. CS high.

The record layout is in [spec.md](spec.md). Wipe is command `5C 5C`, then `A7` and one tamper record signed by the tamper key, then QS_RST_N is held low and the counter stops. No pin changed in doc-1.4.
