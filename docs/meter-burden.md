# Meter burden and ledger energy

Edition: v0.0.1 (doc-1.3, 2026-10-09). The supply and the signing cadence are updated to EC-SEAL1 revision B; the cap is unchanged.

Minting and posting use electricity. The mint path is a meter, so its draw is capped at a present-day meter. The ledger is not a proof-of-work puzzle, so posting is a signature check, not a mining load.

## Plain language

A house meter already uses a small, continuous trickle. Enerchain may use that trickle. It may not add a second load that looks like an appliance. Signing a kilowatt-hour costs far less than measuring it. Updating the ledger costs a check of that signature, not a hash contest.

## Meter budget

IEC 62052-11 limits the voltage-circuit consumption of a static meter. The published reading of that limit is 2 W and 10 VA per phase; the current circuit is a further 1 VA per phase at nominal current, which is the shunt burden \(I^2 R\) [IEC 62052-11; Günther 2021]. Field meters are often specified under 1.5 W. The Enerchain mint path, supply included, shall stay inside the voltage-circuit figure:

\[
P_{\text{mint}} \le 2\ \text{W}.
\]

At that cap, continuous draw over a year is

\[
E_{\text{year}} = 2\ \text{W} \times 24 \times 365 = 17.5\ \text{kWh}.
\]

A site that delivers 1 kW average, 8760 kWh in a year, spends 0.2% of that delivery on the mint path at the cap. The design target is under 1.5 W, in line with meters already on walls. The supply is taken on the grid side of the shunt, so this trickle is neither counted as export nor as import.

Revision B's budget: an LNK304 buck to 12 V carries about 30 mA of logic (through the 3.3 V regulator) and up to 40 mA average for the radio. At an assumed 60 % light-load efficiency that is about 1.4 W with the radio transmitting and well under 1 W with it asleep, and a few volt-amperes. The doc-1.1 capacitive dropper could not carry the logic: see [electrical-review.md](electrical-review.md) C-3.

## Signature cost

ML-DSA-44, the smaller NIST parameter, costs on the order of 19 mJ for a sign cycle on a small microcontroller, using a 79 mW active model [software measurement, RP2040 class]. A hardware engine in a secure element is the same order or lower, because it is not clocking a general core. The meter signs once per token, 1 kWh, so every kilowatt-hour is credited on its own. That is

\[
\frac{0.019\ \text{J}}{3.6 \times 10^{6}\ \text{J}} \approx 5 \times 10^{-9}
\]

of the energy being attested. The continuous meter supply dominates. The signature does not.

The ledger note had used ML-DSA-65. For this budget the meter key is ML-DSA-44. The signature is 2420 bytes rather than 3309 [NIST FIPS 204]. A fixed \(2^{20}\)-byte block then holds on the order of 400 issuances in a binary encoding (\(2^{20} / 2452 \approx 427\)) instead of the earlier note's \(\lfloor 2^{20}/3600 \rfloor = 291\) (about 210 in the v0.0.1 devnet's JSON encoding, 4.9 kB each). The cap \(B\) does not change. Airtime falls with the shorter signature, which is the radio part of the energy.

## Ledger cost

There is no difficulty and no hash contest, so a node does not burn power to win a block. Acceptance is \(\mathrm{Verify}(pk, m, \sigma)\) plus the hash-chain link. Verification is the cheaper half of an ML-DSA cycle. At the same 79 mW model, a few milliseconds of verify is well under 1 mJ per issuance. A full block of a few hundred issuances is under 1 J at the node. That is the ledger update. It is not comparable to proof-of-work ordering, whose electricity cost is the load de Vries measured [de Vries 2018].

Posting is duty-cycled. The core signs once per token, 1 kWh. A frame is 2454 bytes, about 0.21 s on the 115 kbaud UART. Even if the radio drew its whole 40 mA, 12 V budget (0.48 W) for a full second per frame, that is about 0.5 J per kilowatt-hour, \(1.3 \times 10^{-7}\) of the energy attested. The radio sleeps otherwise and has no receive path on the board.

## What this refuses

A host CPU left on to run a wallet, a proof-of-work share, or an always-on broadband modem is outside the 2 W cap. Those are not part of the mint path. The schematic in [schematics/mint-path.svg](schematics/mint-path.svg) is the path that is in budget: shunt, divider, fixed-function metrology core, secure element, tamper zeroize, and a slept radio.

## Sources

IEC 62052-11. Electricity metering equipment — General requirements, tests and test conditions. Voltage-circuit and current-circuit consumption limits.

Günther, R. (2021). Self-consumption in the current circuit. CLOU Global. Restates the IEC 62052-11 voltage-circuit figure of 2 W and 10 VA, and 1 VA per phase in the current circuit at nominal current.

NIST. (2024). *FIPS 204: Module-Lattice-Based Digital Signature Standard*. ML-DSA-44 signature length 2420 bytes. https://doi.org/10.6028/NIST.FIPS.204
