# Enerchain roadmap

Release: v0.0.1 (doc-1.2, 2026-10-09). Phase numbers are not release tags.

## Phase 1: Foundational research

- State the electricity-currency hypothesis. See [docs/hypothesis.md](docs/hypothesis.md).
- Define the hardware lock: voltage, current, time, coin schedule.
- Define public-ledger transfer and non-repudiation.
- Define regional books, including planetary and system books.
- Specify the meter and the schedule die so a board house and a chip house are not asked to invent the architecture. See [SOLUTION.md](SOLUTION.md). This is written. It is not built.

## Phase 2: Simulation

- Done in v0.0.1: the net-export schedule ([tools/check_schedule.py](tools/check_schedule.py)); RTL simulation of provisioning, signing, power cuts, refusal and wipe, matched byte for byte to the Python model ([tools/check_rtl.py](tools/check_rtl.py)); the signing image as a host test; a devnet with transfers, replay refusal and the pair rule ([docs/software.md](docs/software.md)); a battery-loop attack that mints nothing.
- Still to do: regional prices for one unit; gate-level simulation on a foundry library; a multi-node network with a BFT validator protocol (open item S-1).

## Phase 3: Prototype

- Close the datasheet items O-2 to O-6 in [docs/open-items.md](docs/open-items.md).
- Build one EC-SEAL1 revision B pair, provision the QS7001, and run the tests in [hardware/fab/ec-seal1/TEST.md](hardware/fab/ec-seal1/TEST.md).
- Feed that pair's UART frames to the v0.0.1 devnet. One board must not mint. (The node, wallet and meter emulator exist as of v0.0.1.)
- Design the battery-backed tamper domain (O-1) for revision C.

## Phase 4: Grid trial

- Residential injection onto a cooperating feeder.
- Transfer of the resulting coins on the test ledger.

## Phase 5: Wider regions

- More than one terrestrial book.
- Delay-tolerant transfer between books [Burleigh et al. 2003].
- Planetary and system books as further regions, same unit.
