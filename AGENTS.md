# AGENTS.md

Instructions for AI coding agents (and people) working in this repository. Read this before changing anything. [CONTRIBUTING.md](CONTRIBUTING.md) is the human process; this file is the operating manual.

## What this repository is

Enerchain is a proposal and reference implementation for an electricity currency. A sealed meter counts active energy in both directions and mints **one token per 1000 Wh (1 kWh) of net grid export**. It signs a cumulative record for every token with ML-DSA-44. A public ledger credits each GEN/GRID meter pair with `min(T_GEN, T_GRID)` less what it already credited. An optional LOAD meter mints nothing; it lets the ledger check GEN = GRID + LOAD.

The repository has four parts that must agree with each other:

| Part | Path | What it is |
| --- | --- | --- |
| Software | `enerchain/`, `tests/` | Python ledger, wallet, devnet, CLI, and a bit-exact model of the meter |
| Chip | `hardware/asic/` | EC-MINT1 RTL (Verilog), testbenches, spec, pinout, package |
| Board | `hardware/fab/ec-seal1/` | EC-SEAL1 revision B: BOM, netlist, centroid, Gerbers, circuit calculations, bench test |
| Signer firmware | `firmware/qs7001/` | QS7001 signing image (C) and its host test |
| Documents | `README.md`, `WHITEPAPER.md`, `SOLUTION.md`, `docs/` | The claim, the math, the threat model, open items |
| Generators and checks | `tools/` | Schedule spec, RTL-vs-model check, board and schematic generators |

Nothing has been built or taped out. Everything is simulation, so do not describe anything as tested on hardware.

## Set up

Python 3.10+, Icarus Verilog, yosys, a C compiler, Pillow.

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[test]' pillow
sudo apt-get install -y iverilog yosys     # Debian/Ubuntu
```

Use `python3 -m pytest` rather than a bare `pytest` if several Python installs exist; a stray `pytest` on PATH fails with `No module named 'dilithium_py'`.

## Run the demo

```sh
enerchain demo                          # 3 simulated days: 2 validators, 1 GEN/GRID pair, a transfer, a refused replay
enerchain demo --days 1
enerchain demo --battery-loop-w 3000    # adds a grid->battery->grid loop; mints the same amount
```

The demo is `cmd_demo` in `enerchain/cli.py`; the site simulation is `enerchain/sim.py`. Every command is in [docs/software.md](docs/software.md).

## Checks (CI runs all of these; run them before every commit)

```sh
python3 tools/check_schedule.py                       # the coin rule, executable spec
python3 -m pytest -q                                  # ledger, meter model, devnet, CLI, RTL == model
iverilog -g2012 -o /tmp/sched hardware/asic/rtl/ec_mint1_schedule.v hardware/asic/tb/tb_schedule.v && vvp /tmp/sched
python3 tools/check_rtl.py                            # RTL testbench vs Python model, byte for byte
(cd hardware/asic/rtl && yosys -q -p "read_verilog ec_mint1.v ec_mint1_schedule.v spi_byte.v uart_tx.v; synth -top ec_mint1 -flatten; check -assert")
cc -std=c99 -Wall -Wextra -Werror -o /tmp/oracle firmware/qs7001/test/test_sign_oracle.c && /tmp/oracle
python3 tools/gen_board.py && git diff --exit-code -- hardware/fab/ec-seal1
python3 tools/gen_schematics.py && git diff --exit-code -- docs/schematics
```

Each prints a `PASS` line or exits non-zero. The full pytest run takes about a minute because ML-DSA is pure Python. The workflow is [.github/workflows/ci.yml](.github/workflows/ci.yml); if you add a check, add it there and to [docs/how-to.md](docs/how-to.md#check-everything).

## Invariants: do not break these

- **The schedule.** `q = 1000` Wh per token, `SIGN_EVERY = 1` (a signed record per token). `credit = e_exp − e_imp − q·tokens`; tokens follow the high-water mark of net export, so `tokens = ⌊max(e_exp − e_imp) / q⌋`. A record is built when its token mints, so in every token record `e_exp − e_imp = 1000 · tokens` exactly; the daily re-send repeats the last token record's counters under a new seq, so it holds there too. Any example token record in a document must satisfy that. The one tamper record a meter signs (kind 1) carries the live counters and mints nothing.
- **Four implementations of one rule.** The schedule lives in `hardware/asic/rtl/ec_mint1_schedule.v`, `enerchain/meter.py`, `tools/check_schedule.py` and `firmware/qs7001/sign_oracle.c` (the rollback and `tokens·q ≤ e_exp` guard). Change one and you change all, then run `tools/check_rtl.py`.
- **The record.** 32 bytes, big-endian, layout in [hardware/asic/spec.md](hardware/asic/spec.md) and `enerchain/record.py`. Byte 30 is the kind (0 token, signed by the meter key; 1 tamper, signed by the tamper key), byte 31 is zero. Roles are 1 GEN, 2 GRID, 3 LOAD. Frame = `EC 01` + record + 2420-byte ML-DSA-44 signature = 2454 bytes.
- **The issuance rule.** The ledger accepts a record only if the signature verifies under the certified key, the calibration CRC matches, `seq` increases, no counter decreases, and the meter is not revoked past the revocation's effective seq or past its own tamper record. It credits `min(T_GEN, T_GRID + attested)` minus what it already credited, where each side sums `tokens − base` over the meters that have held it. `attested` moves only by a k-of-n attestation, capped by the escrow. Balances are in watt-hours; 1 token = 1000 Wh.
- **The supplier's protections** ([docs/grid-operator.md](docs/grid-operator.md)). Do not weaken these without a CHANGELOG row: revocation has a listed reason, an evidence hash, an effective seq, and a contestable notice period below `k_urgent`; genesis refuses a sector holding k certifier keys; a pair request fixes starting counts; GEN tokens counted during a GRID outage are escrowed, not dropped; the balance flag never moves credit by itself.
- **No host write port.** Nothing outside EC-MINT1 may set a counter or choose what the QS7001 signs. The radio is transmit-only. Do not add a path from the radio, or a second SPI master, to the signer or the F-RAM.
- **Ground is Line.** On EC-SEAL1 logic ground is the grid side of the shunt; the divider runs from Neutral. Read [CIRCUITS.md](hardware/fab/ec-seal1/CIRCUITS.md) before touching the analog front end or the supply.

## Generated files: never edit by hand

| Files | Generator |
| --- | --- |
| `hardware/fab/ec-seal1/{BOM.csv,centroid.csv,netlist.txt,placement.svg}`, `gerber/*` | `tools/gen_board.py` |
| `docs/schematics/01-*.svg` … `08-*.svg`, `docs/schematics/mint-path.svg` | `tools/gen_schematics.py` |

To change a part, edit `tools/gen_board.py` and regenerate. If a value changes, update the calculation in `CIRCUITS.md` and the assertion in `tools/gen_schematics.py`, then regenerate the sheets. `gen_schematics.py` stops if a printed value disagrees with the circuit math, or if a drawn connection is not in `netlist.txt`. Sheets 09–12 are hand-drawn SVG; edit them directly.

## Documents and math

- When you change a number, recompute it, then search the repo for every other place it appears (`grep -rn`). The same figure often appears in `README.md`, `WHITEPAPER.md`, `docs/*.md`, `hardware/**/*.md` and the SVG sheets.
- Show the arithmetic where a reader would check it. State the assumption (240 V rms, 50 Hz, 60 % efficiency, and so on).
- A fact about a catalog part that you cannot read from its datasheet goes in [docs/open-items.md](docs/open-items.md) as a "verify" item. Do not state it as fact.
- Style: plain, short declarative sentences; a "Plain language" section before the technical one; no marketing words. Cite peer-reviewed work and standards as `[Author Year]`, and add the source to [docs/references.md](docs/references.md).
- Superseded designs (the doc-0.9 BOM, the doc-1.1 revision A board, `hardware/rtl/mint_schedule.v`, `keccak_round.v`, `ntt_butterfly.v`) stay as history. Do not build or synthesize them, and do not delete them without being asked.

## Versions and changelog

- Software releases are `vX.Y.Z` (currently v0.0.1, set in `pyproject.toml` and `enerchain/__init__.py`). Documentation editions are `doc-N.M` (currently doc-1.4) and are never git tags.
- A change to the claim, the math, the schedule or the hardware adds a row to [CHANGELOG.md](CHANGELOG.md). Update the `Edition:` line at the top of each document you change.
- Electrical findings go in [docs/electrical-review.md](docs/electrical-review.md) with the calculation, in the C-/M-/Minor numbering.

## Licensing

`hardware/` is CERN-OHL-S-2.0 ([LICENSE-HARDWARE](LICENSE-HARDWARE)). Everything else is Apache-2.0 ([LICENSE](LICENSE)). Keep new files on the right side of that split.

## Git

- Commit messages: a short summary line, then what changed and why. Never commit generated files that differ from what the generator writes.
- Do not commit `__pycache__/`, `*.egg-info/`, `.venv/` or `hardware/fab/ec-seal1/placement.png` (all in `.gitignore`).
