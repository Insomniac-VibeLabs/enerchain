# EC-MINT1 specification

Edition: v0.0.1 (doc-1.4). The pin table is [PINOUT.md](PINOUT.md). This file is the electrical and logical contract around that table. The private ML-DSA key is not in this die; it stays in the QS7001.

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

An export pulse adds one to `credit`; when it reaches `q = 1000` a token is minted and `credit` returns to zero. An import pulse subtracts one. So `tokens = ⌊max over time of (e_exp − e_imp) / q⌋`: energy that came in from the grid and went back out mints nothing, and splitting an interval cannot mint extra. Every token (1 kWh) the die signs one record, so each kilowatt-hour is credited on its own; at that moment `credit` is zero and `e_exp − e_imp = 1000 · tokens` exactly. Records carry cumulative counts, so a lost record loses nothing. A token minted while the previous record is still being signed (ready poll up to 1.1 s, then 2454 bytes at 115 kbaud, about 0.21 s) is carried by the next record; that only happens above roughly 2.7 MW.

`q`, the record cadence and the registers have no host write port.

## Re-send

A 16 MHz prescaler (`TICK` = 16 000 000 clocks) counts seconds since the last record was started. After `RESEND_S` = 86 400 seconds with none, if the signer accepted the last record, the die signs that record again: the same e_exp, e_imp and tokens, and the next seq. The rule `e_exp − e_imp = 1000 · tokens` still holds. A frame lost on the way to the ledger therefore comes back within a day without a receive path, and a live meter is heard from at least daily. The ledger treats three days of silence from a GRID meter as an outage ([docs/grid-operator.md](../../docs/grid-operator.md)). The last-sent record is not kept in FRAM, so after a power cut the re-send starts again with the next token.

## Tamper record

On ZEROIZE the die stops counting and sends `5C 5C`; the QS7001 erases its meter key. If the die had booted, it then raises CS for 16 clocks and sends `A7`, a 32-byte record of kind 1 (byte 30 = 01) carrying the counters as they stand and the next seq, and its CRC-8. The QS7001 signs it once with its tamper key, erases that key, and answers `5A` and the signature, which the die frames on the UART like any record. Then the die holds QS_RST_N low and stops. A tamper record mints nothing; it tells the ledger the cover was opened under power. The board holds the signer rail up for about 2 s after ZEROIZE so that the record can be signed (R22·C14, [CIRCUITS.md](../fab/ec-seal1/CIRCUITS.md)).

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
| 4 | `0x1R`: version 1, role R (1 GEN, 2 GRID, 3 LOAD) |
| 5 | class tag `0x22` |
| 6–9 | seq, +1 for every record the die starts |
| 10–15 | e_exp, Wh |
| 16–21 | e_imp, Wh |
| 22–27 | tokens, cumulative |
| 28–29 | CRC-16/CCITT-FALSE of the calibration image |
| 30 | kind: 00 token record (meter key), 01 tamper record (tamper key) |
| 31 | zero |

There is no wall-clock time in the record. The ledger orders records by `seq` and timestamps them at inclusion. The calibration CRC lets the ledger refuse a record made under an image other than the certified one.

A LOAD meter is the same die with role 3 in its image. It is wired so that the site's consumption flows from the generator stud to the grid stud, so its tokens count consumed kilowatt-hours. The ledger uses it only for the GEN = GRID + LOAD check.

UART frame: `EC 01`, the 32-byte record, then the signature (2420 bytes for ML-DSA-44, 4627 for ML-DSA-87; parameter `SIG_BYTES`). With ML-DSA-44 a frame is 2454 bytes, about 0.21 s at 10 bits per byte.

## Power

Sign is the QS7001's peak, not a lattice core on this die. Budget this die so the meter stays inside the 2 W cap in [docs/meter-burden.md](../../docs/meter-burden.md). Target for this die is under 20 mW average. The doc-1.4 netlist synthesizes in yosys to about 3 980 flip-flops and 43.7k generic cells; 2048 of the flops are the cached calibration image. The re-send timer and the tamper-record path add about 70 flip-flops and 1.3k cells to doc-1.3.
