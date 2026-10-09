# Enerchain roadmap

Edition: doc-1.1 (2026-10-09). Phase numbers are not release tags.

## Phase 1: Foundational research

- State the electricity-currency hypothesis. See [docs/hypothesis.md](docs/hypothesis.md).
- Define the hardware lock: voltage, current, time, coin schedule.
- Define public-ledger transfer and non-repudiation.
- Define regional books, including planetary and system books.
- Specify the meter and the schedule die so a board house and a chip house are not asked to invent the architecture. See [SOLUTION.md](SOLUTION.md). This is written. It is not built.

## Phase 2: Simulation

- Generation intervals and the coin schedule. The schedule rule already has an executable check in [tools/check_schedule.py](tools/check_schedule.py).
- Transfer and double-submit of one interval.
- Regional prices for one unit.
- Gate simulation of one EC-MINT1 sign and one wipe. Not done. The sandbox that wrote the Verilog had no simulator.

## Phase 3: Prototype

- Build one EC-SEAL1 pair, provision the QS7001, and run the tests in [hardware/fab/ec-seal1/TEST.md](hardware/fab/ec-seal1/TEST.md).
- Node, wallet, meter emulation, test network, against signatures from that pair. One board must not mint.

## Phase 4: Grid trial

- Residential injection onto a cooperating feeder.
- Transfer of the resulting coins on the test ledger.

## Phase 5: Wider regions

- More than one terrestrial book.
- Delay-tolerant transfer between books [Burleigh et al. 2003].
- Planetary and system books as further regions, same unit.
