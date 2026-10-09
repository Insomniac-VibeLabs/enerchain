# Governance

Edition: v0.0.1 (doc-1.2, 2026-10-09).

## Plain language

No single company should be able to decide, alone, which meters are real or how many coins a reading creates. The hardware schedule is the mint. Governance changes the schedule and the list of accepted meters. It does not sign individual intervals.

## Subjects

A later community may govern:

- the coin schedule per accepted kilowatt-hour
- meter certification and revocation
- validator rules for the public ledger
- protocol upgrades
- how regional books convert

Principle: no single organization has unilateral control of verification or issuance. A manufacturer can build the meter. The manufacturer’s signature alone does not mint.

## What v0.0.1 implements

- **Certification is k of n.** Genesis names n certifier keys and a threshold k. A meter, a pair or a revocation is valid only with approvals from k distinct genesis certifiers. The devnet default is 2 of 3. A public network should use independent bodies (a metrology authority, a grid operator, a consumer body) and k of at least 2.
- **Revocation** stops a meter's records from being accepted. Coins already minted stay.
- **Validators** are a fixed proof-of-authority set in genesis, taking turns by height. Changing the set, the threshold or the parameters requires a new genesis in v0.0.1. On-chain governance and a BFT validator protocol are open item S-1.
- **The schedule** (q = 1000 Wh, a signed record for every token) is in the meter die, not on the ledger. Changing it is a new die and a new certificate, which is the point.
