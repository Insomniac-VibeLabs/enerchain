# Contributing to Enerchain

Edition: v0.0.1 (doc-1.2, 2026-10-09).

The repository is the research set and reference implementation for an electricity currency: hardware-locked issuance, public-ledger transfer, regional trade.

Useful backgrounds: power systems, cryptography, distributed systems, energy economics, security of metering.

## Process

1. Read [docs/how-to.md](docs/how-to.md) and [docs/hypothesis.md](docs/hypothesis.md).
2. Fork and branch.
3. Open a pull request that says whether it clarifies the hypothesis or changes it.
4. If the claim changes, add a `doc-` row to [CHANGELOG.md](CHANGELOG.md). Software releases are tagged `vX.Y.Z`; document editions keep the `doc-` prefix and are never tagged.
5. Before opening the pull request, run the checks in [docs/how-to.md](docs/how-to.md#check-everything). CI runs the same ones.
6. Update [README.md](README.md) if the reading order changes.
7. Remove superseded wording in the same change.
8. If the RTL changes, change `enerchain/meter.py` to match; if a part moves, regenerate with `tools/gen_board.py`.

Peer-reviewed work and formal standards outrank marketing pages. Add sources to [docs/references.md](docs/references.md) with author, year, venue, and a stable identifier.
