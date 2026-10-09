# How to read and change Enerchain documents

Edition: doc-0.7 (2026-10-08). This is a documentation edition, not a software release.

## What this repository is

Enerchain is the working notes for an electricity-denominated public currency. Issuance is hardware-locked to measured generation delivered to a grid. Transfer uses a public ledger with non-repudiation.

## Reading order

1. [Hypothesis](hypothesis.md) — the claim, in ordinary language and then in technical language.
2. [Problem statement](problem-statement.md) — why an electricity unit, and why now.
3. [Whitepaper](../WHITEPAPER.md) — Proof of Generation, the hardware lock, and transfer.
4. [Energy verification](energy-verification.md) — voltages, current, time, and the coins that follow.
5. [Hardware binding](hardware-binding.md) — the sealed integral that signs the token.
6. [Ledger nonrepudiation](ledger-nonrepudiation.md) — posting that signature on a public, quantum-resistant ledger.
7. [Meter burden](meter-burden.md) — why minting and posting stay inside a present-day meter’s draw.
8. [Schematic](schematics/README.md) — block sketch, then one IEC-symbol sheet per block.
9. [Economics](economics.md) — individuals feeding grids, and regional price.
10. [Interplanetary economics](interplanetary-economics.md) — the token as proof of local generation, not an export of energy.
11. [Governance](governance.md) — who may change the rules.
12. [Roadmap](../ROADMAP.md) — research phases. Phase 1 is current.
13. [References](references.md) — sources used in doc-0.7.

## How a concept change is made

1. Open an issue that states the claim being changed and the evidence.
2. If the change is accepted, add a `doc-` row to `CHANGELOG.md`. Do not tag that edition as `vN`.
3. Update this file and `README.md` if the reading order changes.
4. Remove superseded wording in the same edition.
