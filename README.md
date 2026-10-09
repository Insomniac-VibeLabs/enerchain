# Enerchain

**Power is the new gold.**

Edition: doc-0.2 (2026-10-08). Documentation edition, not a software release. See [CHANGELOG.md](CHANGELOG.md).

## In plain language

Enerchain asks whether a public ledger can reward people for producing useful electricity, instead of rewarding them for burning electricity on puzzles.

A meter would measure energy that was actually delivered. It would sign that measurement. A network would check the signature and the claim. If the claim passed the rules, the protocol would mint a transferable unit. The unit would not be a promise that every kilowatt-hour is worth the same money. Markets would price it. The project is research. There is no network and no token.

## Technical statement

Enerchain is a proposed settlement protocol whose issuance event is verified electrical energy delivered across a defined boundary, called Proof of Generation (PoG). PoG is an evidence rule, not a consensus algorithm. Ordering of claims may still use an ordinary replicated ledger. The physical quantity is active energy, in watt-hours, measured under a stated accuracy class. The economic quantity is a protocol unit minted only after that evidence is accepted. Price is out of protocol: locational marginal pricing already shows that one megawatt-hour does not have one price across a network [Schweppe et al. 1988; Hogan 1992].

The contrast with proof of work is specific. Bitcoin orders transactions by competitive hashing, and that work consumes large amounts of electricity [de Vries 2018]. Enerchain does not claim to replace proof of work inside Bitcoin. It asks whether the issuance event itself can be a verified injection or delivery of electrical energy, an idea already sketched for smart-grid trade by NRGcoin [Mihaylov et al. 2014].

## What this repository is not

- Not a production chain, wallet, meter, or exchange.
- Not a claim that a token is redeemable for a kilowatt-hour. Redeemability would be a later market rule, not a consequence of minting.
- Not a claim that electrons can be shipped between planets. Interplanetary scope is about signed records and delay-tolerant settlement. See [docs/interplanetary-economics.md](docs/interplanetary-economics.md).
- Not a substitute for a grid operator, a renewable energy certificate registry, or a utility bill.

## Design goals

These are requirements on a future specification, not properties of a running system.

- Public verification of a generation claim without a single issuer of the unit.
- Non-repudiation of the meter signature, and a published path for revocation when a meter is compromised.
- Hardware identity that is expensive to clone. Identity alone is not proof of energy.
- One accepted claim per delivered watt-hour, so the same energy cannot mint twice or also retire as an exclusive certificate.
- Local price. The protocol measures; markets value.
- A path that still works when confirmation takes minutes, because Earth–Mars light time does [Burleigh et al. 2003].

## Worked example

A rooftop array delivers 10 kWh across the meter in one hour. The meter records identity, time, voltage, current, power factor, and integrated active energy, then signs the record. Validators check the key, the freshness of the timestamp, and that this interval was not already settled. They do not, at this stage of the research, have a completed rule for proving the energy was not a looped battery. That gap is open. See [docs/energy-verification.md](docs/energy-verification.md).

## Status

Concept and research. Phase 1 in [ROADMAP.md](ROADMAP.md). No implementation exists in this repository.

## Documents

Start with [docs/how-to.md](docs/how-to.md). Sources are in [docs/references.md](docs/references.md).

| Document | Question it answers |
| --- | --- |
| [Problem statement](docs/problem-statement.md) | Why tie a ledger unit to generation at all? |
| [Whitepaper](WHITEPAPER.md) | What is proposed, and what is refused? |
| [Energy verification](docs/energy-verification.md) | What evidence must a claim carry? |
| [Economics](docs/economics.md) | Who is paid, and what can go wrong? |
| [Governance](docs/governance.md) | Who may change issuance and meter rules? |
| [Interplanetary economics](docs/interplanetary-economics.md) | What survives light-time delay? |
| [Contributing](CONTRIBUTING.md) | How to propose a change of claim |

License: Apache-2.0. See [LICENSE](LICENSE).
