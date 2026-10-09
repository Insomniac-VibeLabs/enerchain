# Governance

Edition: doc-0.2 (2026-10-08).

## Plain language

No single company should be able to decide, alone, which meters are real and how many units a reading creates. Some decisions still need a high bar, because a bad meter rule counterfeits the currency.

## Technical statement

Enerchain governance is the set of rules for changing issuance, meter certification, validator admission, and protocol upgrades. Decentralization is a constraint, not a slogan: a certification authority that can whitelist every meter can also halt issuance. A system with no certification admits cloned meters.

The design has to hold four properties at once, and they trade off:

- Security of the measurement.
- Scalability of verification.
- Integrity of the watt-hour claim.
- Absence of a unilateral controller.

Subjects a future community may govern:

- The issuance function, including any change to units per accepted kilowatt-hour.
- Meter certification and revocation.
- Validator requirements.
- Upgrade procedure.
- The exclusivity rule against certificate registries [Gillenwater 2008].

Principle, unchanged from the initial notes: no single organization should possess unilateral control over energy verification or currency issuance.

Practical reading of that principle: certification and revocation must be multi-party and publicly logged. A manufacturer can build a meter. A manufacturer cannot be the only party whose signature makes a reading mint. Regulatory reality may force a utility or a state into the set of parties [Mengelkamp et al. 2018]. That is a constraint to design for, not a reason to pretend the state is absent.
