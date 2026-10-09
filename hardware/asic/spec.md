# EC-MINT1 specification

Edition: v0.0.1 (doc-1.2). The pin table is [PINOUT.md](PINOUT.md). This file is the electrical and logical contract around that table. The private ML-DSA key is not in this die; it stays in the QS7001.

## Rails

- VDD_IO 3.3 V, from the meter LDO. Two pins, 1 and 23.
- VDD_CORE 1.2 V, on-die regulator from VDD_IO. The board does not supply it.
- VSS on pins 2, 24, 31, 32 and the exposed pad.

## Clock and reset

16.000 MHz CMOS on XI. There is no XO pin and no Pierce cell. Reset is asynchronous, active low. CF_EXP, CF_IMP, ZEROIZE and the PROV pins pass through two-flop synchronizers. UART is 8N1 at 139 clocks per bit, about 115108 baud. All three SPI masters run at 8 MHz, mode 0; MOSI changes only while SCK is low.

## Schedule

Two pulse inputs. One export pulse or one import pulse is one watt-hour (the STPM32 is set to 1000 impulses per kWh on each LED).

- `e_exp`, `e_imp`: 48-bit cumulative watt-hours, monotone.
- `tokens`: 48-bit cumulative tokens.
- `credit`: 48-bit signed, `credit = e_exp − e_imp − tokens·q`.

An export pulse adds one to `credit`; when it reaches `q = 1000` a token is minted and `credit` returns to zero. An import pulse subtracts one. So `tokens = ⌊max over time of (e_exp − e_imp) / q⌋`: energy that came in from the grid and went back out mints nothing, and splitting an interval cannot mint extra. Every 10 tokens (10 kWh) the die signs one record. Records carry cumulative counts, so a lost record loses nothing.

`q`, the record cadence and the registers have no host write port.

## Persistence

An FM25V02A FRAM (32 KiB, 10¹⁴ write cycles) on its own SPI holds:

| Address | Content |
| --- | --- |
| 0x0000, 0x0040 | Two 36-byte state slots: `EC 01`, gen (4), e_exp (6), e_imp (6), tokens (6), credit (6), seq (4), tokens since the last record (1), CRC-8 |
| 0x0100 | The 256-byte calibration image |
| 0x0200 | `'L' 'K'` and the CRC-16 of the image |

After every counted pulse and every new sequence number, the die writes the state to the slot chosen by the low bit of the next `gen`. At boot it takes the valid slot with the larger `gen`. A power cut in the middle of a write leaves the other slot intact and loses at most the pulses since that slot was written. At 9.6 kW that is under three writes a second, about 10⁸ a year.

## Record

The QS7001 signs 32 bytes. Fields are big-endian.

| Bytes | Field |
| --- | --- |
| 0–3 | meter id |
| 4 | `0x1R`: version 1, role R (1 GEN, 2 GRID) |
| 5 | class tag `0x22` |
| 6–9 | seq, +1 for every record the die starts |
| 10–15 | e_exp, Wh |
| 16–21 | e_imp, Wh |
| 22–27 | tokens, cumulative |
| 28–29 | CRC-16/CCITT-FALSE of the calibration image |
| 30–31 | zero |

There is no wall-clock time in the record. The ledger orders records by `seq` and timestamps them at inclusion. The calibration CRC lets the ledger refuse a record made under an image other than the certified one.

UART frame: `EC 01`, the 32-byte record, then the signature (2420 bytes for ML-DSA-44, 4627 for ML-DSA-87; parameter `SIG_BYTES`).

## Power

Sign is the QS7001's peak, not a lattice core on this die. Budget this die so the meter stays inside the 2 W cap in [docs/meter-burden.md](../../docs/meter-burden.md). Target for this die is under 20 mW average. The doc-1.2 netlist synthesizes in yosys to about 3.9k flip-flops and 42k generic cells; 2048 of the flops are the cached calibration image.
