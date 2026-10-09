# Contributing to Enerchain

Edition: doc-0.2 (2026-10-08).

Thank you for working on Enerchain. The repository is research: economic modeling, cryptographic design, and energy-verification mechanisms. It is not a network.

Useful backgrounds:

- Electrical engineering and power systems
- Cryptography and distributed systems
- Energy economics and energy policy
- Security analysis of metering

## Process

1. Read [docs/how-to.md](docs/how-to.md).
2. Fork and branch.
3. Open a pull request that says whether it clarifies a claim or changes one.
4. If the claim changes, add a `doc-` row to [CHANGELOG.md](CHANGELOG.md). Do not use a `v` tag for a document edition. Software releases, when they exist, increment on their own and must not be the citation for a document.
5. Update [README.md](README.md) and this file if the reading order or the research areas change.
6. Remove the superseded wording in the same change. Do not leave two explanations.

## Research areas

- Proof of Generation as evidence, not as consensus
- Meter security and fraud
- Distributed energy markets and exclusivity with certificate registries
- Issuance functions that do not assume a fixed price
- Delay-tolerant settlement for the interplanetary case

Design changes should prefer transparency, verifiability, and the absence of a unilateral issuer. A change that cannot name a source, a standard, or a stated assumption does not belong in the concept documents.

## Sources

Peer-reviewed work and formal standards outrank blog posts and token marketing. Add new sources to [docs/references.md](docs/references.md) with author, year, venue, and a stable identifier. Do not cite a source you have not opened.
