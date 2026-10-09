# Enerchain roadmap

Edition: doc-0.2 (2026-10-08). Phase 1 is the current phase. No software release exists. Phase numbers are not release tags.

## Phase 1: Foundational research (current)

Objectives:

- Define Proof of Generation as an acceptance predicate, not as a block-ordering algorithm.
- Separate the issuance function from local price. See [WHITEPAPER.md](WHITEPAPER.md).
- Write the threat model for fabricated generation, cloning, replay, double counting, and storage loops.
- State verification assumptions that do not smuggle in a single utility oracle.

Deliverables:

- Whitepaper and the documents under `docs/`.
- A cited references list.
- An economic note that treats oversupply of the unit as a first-class risk.

Exit criterion: an issue list of open questions that a simulation could falsify.

## Phase 2: Simulation

Objectives:

- Simulate generation events, including fraudulent ones.
- Simulate validator checks on signed records.
- Compare at least two issuance functions under growing generation.
- Test storage-loop and double-registry cases.

No mainnet and no token in this phase.

## Phase 3: Prototype

Objectives, only after Phase 2 reports:

- Enerchain node.
- Wallet.
- Meter emulation, not a claim of certified hardware.
- A test network with public parameters.

## Phase 4: Real-world testing

Objectives:

- Residential solar, with a published exclusivity rule against any certificate registry.
- Microgrid participation where regulation allows it. Regulation has blocked otherwise complete market designs [Mengelkamp et al. 2018].
- Utility integration only under a written oracle policy.

## Phase 5: Scale, including off-Earth accounting

Objectives:

- Multi-grid interoperability of records, not of electrons.
- Delay-tolerant settlement assumptions [Burleigh et al. 2003].
- Interplanetary economic research limited to local books and public conversion rates.

Phase 5 does not authorize a claim that physical energy is traded between planets.
