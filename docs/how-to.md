# How to read and change Enerchain documents

Edition: doc-0.2 (2026-10-08). This is a documentation edition, not a software release.

## What this repository is

Enerchain is a research repository. It does not contain a node, a token, a meter, or a network. The documents state a hypothesis and the constraints any later design would have to meet.

## Reading order

Read in this order. Each document starts in ordinary language and then states the same idea in technical terms.

1. [Problem statement](problem-statement.md) — why the question is being asked.
2. [Whitepaper](../WHITEPAPER.md) — the proposal, what it measures, what it does not claim.
3. [Energy verification](energy-verification.md) — how a generation claim would have to be evidenced.
4. [Economics](economics.md) — issuance, local price, and known failure modes.
5. [Governance](governance.md) — who may change the rules.
6. [Interplanetary economics](interplanetary-economics.md) — accounting across light-time delay, not shipping electrons between planets.
7. [Roadmap](../ROADMAP.md) — research phases. Phase 1 is the current phase.
8. [References](references.md) — sources used in doc-0.2.

## How a concept change is made

1. Open an issue that states the claim being changed, the evidence, and whether the change is a clarification or a thesis change.
2. Do not edit the thesis in a pull request that only claims to be editorial.
3. If the change is accepted, add a row to `CHANGELOG.md` with the next `doc-` edition. Do not tag that edition as `vN`.
4. Update this file and `README.md` if the reading order or status changes.
5. Delete or rewrite superseded passages in the same edition. Do not leave a second, conflicting explanation in the tree.

## What not to cite as proof

Blog posts, token marketing pages, and unpublished whitepapers may be named as prior art. They are not evidence that a mechanism works. Prefer the peer-reviewed and standards sources in [references.md](references.md).
