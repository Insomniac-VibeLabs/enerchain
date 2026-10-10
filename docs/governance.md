# Governance

Edition: v0.0.1 (doc-1.4, 2026-10-10).

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

- **Certification is k of n.** Genesis names n certifier keys and a threshold k. A meter, a pair, a rebind, an attestation or a revocation is valid only with approvals from k distinct genesis certifiers. The devnet default is 2 of 3. A public network should use independent bodies (a metrology authority, a grid operator, a consumer body) and k of at least 2.
- **Sectors.** Genesis labels each certifier with a sector (`metrology`, `grid_operator`, `consumer`, `manufacturer`, `other`) and refuses a set in which one sector holds k keys. A grid operator may be a certifier. It can never approve alone, and neither can any other industry.
- **Revocation** names a reason from a fixed list (`seal_broken`, `metrology_fault`, `key_compromise`, `decommissioned`, `misinstalled`), the SHA-384 of its evidence, and an effective seq. Records at or below that seq are still accepted, so energy measured before the decision is still credited. Coins already minted stay. With k approvals a revocation waits a notice period (30 days on the devnet), during which records keep minting and the pair's beneficiary may contest it with its account key; a contested revocation never takes effect. With `k_urgent` approvals (default k + 1) it takes effect at once and cannot be contested. A meter that sent a tamper record is already marked wiped and needs no revocation.
- **Rebind.** k approvals replace a pair's revoked or wiped meter with a newly certified one of the same role.
- **Attestation.** k approvals release escrowed tokens to a pair: GEN tokens counted while its GRID meter was silent, revoked or wiped, or energy a balance flag shows went missing between the meters. The ledger caps each release and numbers them, so none can be replayed. This is the only way certifiers add credit, and the GEN meter's count bounds it.
- **Pair requests.** A supplier files a pair request with its own account key. It fixes the pair's starting counts when it is filed, so the time certifiers take to approve costs the supplier nothing. Both heights are public.

Why these rules exist is [grid-operator.md](grid-operator.md).
- **Validators** are a fixed proof-of-authority set in genesis, taking turns by height. Changing the set, the threshold or the parameters requires a new genesis in v0.0.1. On-chain governance and a BFT validator protocol are open item S-1.
- **The schedule** (q = 1000 Wh, a signed record for every token) is in the meter die, not on the ledger. Changing it is a new die and a new certificate, which is the point.
