# How to read, set up, and build

Release: v0.0.1 (doc-1.2, 2026-10-09). Nothing in the tree has been stuffed or taped out. The software runs; the hardware simulates.

## What this repository is

Enerchain is an electricity currency. Coins are created when sealed meters measure energy delivered to a grid, net of energy taken from it, and sign that total. The count is not chosen by a program on the inverter, the radio, or a server.

The buildable form is four pieces, decided in [SOLUTION.md](../SOLUTION.md):

1. **EC-SEAL1**, the meter board, revision B. Order two per site. One sits at the generator terminals (GEN), one at the point of connection to the grid (GRID). The ledger mints the smaller of the two boards' token counts.
2. **EC-MINT1**, a small standard-cell die. It counts export and import watt-hour pulses, keeps its counters in F-RAM through power cuts, and is the only SPI master the signer will ever see. One token is 1000 net-export pulses, which is 1 kWh at the meter’s 1000 impulses/kWh setting.
3. **QS7001**, a catalog secure element. ML-DSA runs inside it. The private key is not in EC-MINT1 and not in any file in this repository.
4. **The `enerchain` package**: the ledger, the wallet, a development network, and a reference model of the meter.

Do not build from [hardware/fab/BOM.csv](../hardware/fab/BOM.csv) (doc-0.9) or from the doc-1.1 board files in git history. The buy list that ships is [hardware/fab/ec-seal1/BOM.csv](../hardware/fab/ec-seal1/BOM.csv).

## Reading order

1. [Hypothesis](hypothesis.md) — the claim.
2. [Problem statement](problem-statement.md) — why an electricity unit.
3. [Whitepaper](../WHITEPAPER.md) — Proof of Generation, the lock, transfer, and prior art.
4. [Solution](../SOLUTION.md) — why this is hardware, and what v0.0.1 corrected.
5. [Energy verification](energy-verification.md) — what the meter signs.
6. [Hardware binding](hardware-binding.md) — the net-export schedule and the pair rule.
7. [Ledger nonrepudiation](ledger-nonrepudiation.md) — that signature on a public ledger.
8. [Meter burden](meter-burden.md) — the mint path stays inside a present-day meter’s draw.
9. [Electrical review](electrical-review.md) — what was wrong with the doc-1.1 board, with calculations.
10. [Threat model](threat-model.md) and [open items](open-items.md) — what is stopped, what is not, and what is still assumed.
11. [Software](software.md) — the ledger, wallet and devnet.
12. [EC-SEAL1 manufacturer file](../hardware/fab/ec-seal1/MANUFACTURER.md) and [circuits](../hardware/fab/ec-seal1/CIRCUITS.md).
13. [EC-MINT1](../hardware/asic/README.md) — chip handoff. Verilog and a package drawing, not GDSII.
14. [Economics](economics.md), [interplanetary economics](interplanetary-economics.md), [governance](governance.md), [roadmap](../ROADMAP.md), [references](references.md).

The SVG sheets in `docs/schematics/` are doc-0.7 design drawings and are superseded. `hardware/asic/rtl/keccak_round.v` and `ntt_butterfly.v` are doc-0.8 sketches. Do not build or synthesize them.

## Set up

You need Git and Python 3.10 or later. Icarus Verilog runs the RTL; yosys is optional; a C compiler runs the firmware test; Pillow draws the board placement image.

```sh
git clone https://github.com/sbusch305/enerchain.git
cd enerchain
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[test]' pillow
```

## Check everything

```sh
python3 tools/check_schedule.py      # the coin rule, no dependencies
pytest                               # ledger, meter model, devnet, CLI, RTL == model
python3 tools/check_rtl.py           # EC-MINT1 RTL vs the Python model, byte for byte
cc -std=c99 -Wall -Wextra -o /tmp/oracle firmware/qs7001/test/test_sign_oracle.c && /tmp/oracle
python3 tools/gen_board.py           # regenerate the board files and check the layout rules
```

Passing lines:

```text
PASS schedule: 1000 net-export Wh -> 1 token, splits and loops mint nothing extra
PASS rtl == model: 4 signed records byte-exact
PASS sign_oracle: one keygen, persistent wipe, rollback guard
bodies clear 82 ... wrote .../gerber regions 7 pads 277
```

`gen_board.py` exits non-zero if two nets share copper, two bodies overlap, a pour misses its pad, a mains net comes within 2.5 mm of a logic net, mains copper crosses toward the plane cut, or anything reaches within 3 mm of the edge. Continuous integration runs all of the above on every push ([.github/workflows/ci.yml](../.github/workflows/ci.yml)).

## Run the software

```sh
enerchain demo                       # a two-validator devnet, a GEN/GRID pair, three simulated days
enerchain demo --battery-loop-w 3000 # the same, with a nightly grid->battery->grid loop: same mint
enerchain devnet init ./dn           # a persistent devnet
enerchain wallet new ./me.json
enerchain devnet show ./dn
```

[software.md](software.md) describes the rules and every command.

## Regenerate the board plots

The Gerbers, drill, centroid, BOM, netlist and placement drawing under `hardware/fab/ec-seal1/` are generated by one script. If you move a part, change `tools/gen_board.py` and run it again. Do not patch a Gerber by hand. What the script writes, and what it refuses to write, is in [hardware/fab/ec-seal1/gerber/README.md](../hardware/fab/ec-seal1/gerber/README.md).

## Build the board

Read [MANUFACTURER.md](../hardware/fab/ec-seal1/MANUFACTURER.md) once, then send the board house that directory. The house fans out every net that is not already copper, under the rules in the manufacturer file. Order one panel of two circuits, stuffed the same way. Mark one `GEN` and one `GRID` after the pair is serialized.

The whole board, logic included, is at Line potential. Bench it from a current-limited DC supply, then through an isolation transformer, with an isolated probe, in the order in [TEST.md](../hardware/fab/ec-seal1/TEST.md). Revision B is a bench prototype until open item O-1 is closed.

## Build the chip

Send the chip house [hardware/asic/](../hardware/asic/), not a request to “add ML-DSA”. They synthesize the Verilog on their own standard-cell library and run place-and-route on their process kit. Changing the schedule, adding a CPU, or putting the radio on the signer SPI is a different part.

## Personalize the signer

[firmware/qs7001/sign_oracle.c](../firmware/qs7001/sign_oracle.c) is the reference image, not a host program. At the factory, before the cover is sealed, the vendor provisioning flow loads the image and calls `sign_oracle_personalize(meter_id, role)` once. That generates the key on the part. Read out the public key, publish it with the image hash, and submit a meter certificate for k-of-n approval. The image's only SPI commands are `A1` (sign a record) and `5C 5C` (erase). Mapping the `qs_*` calls to the vendor SDK is open item O-3.

## Bring up one pair

Do these in order. The pass conditions are the numbered steps in [TEST.md](../hardware/fab/ec-seal1/TEST.md).

1. Dead board: ground is H1 (Line), Neutral is H3, and the two are not connected.
2. Tamper, unpowered then powered.
3. 300 V DC into the buck: 12 V, then 3.3 V; the signer rail follows.
4. Shift the calibration image. `CAL_LOCKED` rises and stays risen across power cycles.
5. Divider, shunt, and the LED1/LED2 direction check through the isolation transformer.
6. 10 000 export pulses, one UART frame with tokens 10; import cancels export; a power cut loses nothing.
7. The other board of the pair, its own key. Submit both records to a devnet with `enerchain`; the pair mints the smaller count.
8. Spring released under power: `5C 5C` on the signer MOSI, the signer rail off, no further frames.

## Versions

Software releases are tagged `vX.Y.Z`; v0.0.1 is the first. Documents still carry a `doc-` edition so a document can be cited apart from the code. v0.0.1 ships with doc-1.2.

## How a change is made

1. Open an issue that states the claim being changed and the evidence.
2. If the change is accepted, add a row to `CHANGELOG.md`.
3. Update this file and `README.md` if the reading order or the build steps change.
4. Remove superseded wording in the same change.
5. If a part moves, change `tools/gen_board.py`, regenerate, and commit the plots with the script.
6. If the RTL changes, change `enerchain/meter.py` to match and keep `tools/check_rtl.py` passing.
