# Enerchain

**Power is the new gold.**

Edition: doc-0.5 (2026-10-08). Documentation edition, not a software release. See [CHANGELOG.md](CHANGELOG.md).

## In plain language

Enerchain is a proposal for an electricity currency. Coins are created when hardware measures power delivered to a grid. The count of coins is locked to the electrical reading — voltage, current, and time — and the reading is signed. Anyone can transfer the coins on a public ledger, and the signer cannot later deny the signature.

The reason to denominate money this way is the direction of the technical economy. Compute and the machines around it run on electricity, and more of that load is arriving. Generation is spreading outward: a home array can feed a feeder, not only a central station. Proof-of-work mining already spends electricity to make a coin. Enerchain spends the opposite direction: the coin records electricity contributed.

Grids already trade power between regions. The same unit is the proposed trade good when the region is a planet or a solar system.

## Technical statement

Issuance is Proof of Generation. A meter integrates active energy, \(E = \int v(t)\, i(t)\, dt\), signs the interval, and mints only the units that function allows for that integral. The ledger is public. Transfer is a signed transaction. Non-repudiation is the device signature over the generation record and the account signature over the spend.

Proof-of-work orders history by hashing and consumes large amounts of electricity to do it [de Vries 2018]. Enerchain does not use that expenditure as the mint. Injection into the grid is the mint, as NRGcoin proposed for renewable injection [Mihaylov et al. 2014]. Households and other small agents that both consume and produce are the prosumer case already described in the market-design literature [Parag and Sovacool 2016]. Price still varies by region, which wholesale markets already do [Schweppe et al. 1988; Hogan 1992].

## Design goals

- Hardware-locked issuance from voltage, current, and time.
- Coins only for energy the meter accepted as delivered to the grid.
- Public ledger, easy transfer, non-repudiation.
- Individuals and larger plants on the same evidence rule.
- One measurement language from a feeder to a planetary region.

## Worked example

A home array delivers 10 kWh in one hour. The meter records voltage, current, power factor, and the integral, then signs. The protocol mints the units that integral allows. The holder transfers them with an account signature. Validators check both signatures and that the interval was not already minted.

## Status

Concept and research. Phase 1 in [ROADMAP.md](ROADMAP.md). No implementation is in this repository yet.

## Documents

Start with [docs/how-to.md](docs/how-to.md). The claim itself is in [docs/hypothesis.md](docs/hypothesis.md). Sources are in [docs/references.md](docs/references.md).

| Document | Question it answers |
| --- | --- |
| [Hypothesis](docs/hypothesis.md) | What is being proposed? |
| [Problem statement](docs/problem-statement.md) | Why an electricity currency? |
| [Whitepaper](WHITEPAPER.md) | How issuance and transfer work? |
| [Energy verification](docs/energy-verification.md) | How is the hardware lock specified? |
| [Hardware binding](docs/hardware-binding.md) | How does the sealed integral sign the token? |
| [Ledger nonrepudiation](docs/ledger-nonrepudiation.md) | How does that signature become a public, quantum-resistant record? |
| [Economics](docs/economics.md) | Who generates, and how do regions trade? |
| [Interplanetary economics](docs/interplanetary-economics.md) | What does a planetary region prove? |
| [Governance](docs/governance.md) | Who may change the rules? |
| [Contributing](CONTRIBUTING.md) | How to propose a change? |

License: Apache-2.0. See [LICENSE](LICENSE).
