# EC-MINT1 specification

Edition: doc-1.1. The pin table is [PINOUT.md](PINOUT.md). This file is the electrical contract around that table. The doc-1.0 text that put an ML-DSA key in a 256-bit register is withdrawn. An ML-DSA-44 private key is 2560 bytes and it stays in the QS7001.

## Rails

- VDD_IO 3.3 V, from the meter LDO. Two pins, 1 and 23.
- VDD_CORE 1.2 V, on-die regulator from VDD_IO. The board does not supply it.
- VSS on pins 2, 24, 25–32, and the exposed pad.

## Clock

16.000 MHz CMOS on XI. There is no XO pin and no Pierce cell. Reset is asynchronous, active low, synchronized inside. UART is 8N1 at 139 clocks per bit, about 115108 baud.

## Packet

The signer sees a command byte `A1`, then 32 bytes, then a CRC-8 (poly `0x07`, init `0`) over those 32 bytes, then 2420 clocks of signature. The 32 bytes are:

| Field | Bytes |
| --- | --- |
| meter id | 4 |
| t0 | 4, zero. Anti-replay is W |
| t1 | 4, zero |
| w | 4, the value 1000 |
| n | 2 |
| W | 4, cumulative watt-hours |
| r | 2, residual pulses |
| class | 1, `0x22` |
| pad | 7, zero |

The UART then sends those 32 bytes and the 2420 signature bytes. Wipe is command `5C 5C`, then QS_RST_N stays low and the counter stops.

## Power

Sign is the peak, and it is the QS7001's peak, not a lattice core on this die. Budget this die so the meter stays inside the 2 W cap in [docs/meter-burden.md](../../docs/meter-burden.md) with the radio asleep. Target for this die is under 20 mW average.
