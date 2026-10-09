# Ledger nonrepudiation and quantum-resistant issuance

Edition: v0.0.1 (doc-1.2, 2026-10-09). The payload, the acceptance rule and the block arithmetic are updated to the v0.0.1 record; the argument is unchanged.

The token is proof that a sealed core measured an integral. This note is how that proof is posted on a public ledger, why the signature scheme is quantum-resistant rather than quantum-proof, and why the protocol has no difficulty and no supply cap.

## Plain language

The meter signs the watt-hours with a key that never leaves the seal. The ledger stores that signature. Anyone can check it. The scheme is chosen from the signatures standardized against a large quantum computer. Checking does not get harder as more coins exist. Blocks do not grow. Coins have no maximum count, because the count is the measured energy.

## Nonrepudiation onto the ledger

The sealed core from [hardware-binding.md](hardware-binding.md) holds a signing key \(sk\) and a certified public key \(pk\). For an interval it produces the issuance payload

\[
m = (\text{meter id},\; \text{role},\; \text{class},\; \text{seq},\; E_x,\; E_m,\; T,\; \text{cal CRC})
\]

(32 bytes; [hardware/asic/spec.md](../hardware/asic/spec.md))

and a signature \(\sigma = \mathrm{Sign}(sk, m)\). The host can broadcast \((m, \sigma)\). It cannot produce a valid \(\sigma\) for a different \(m\).

A ledger node accepts the record into a block if and only if \(\mathrm{Verify}(pk, m, \sigma) = 1\), \(pk\) is the certified key for that meter, the calibration CRC matches the certificate, \(\text{seq}\) is greater than the last accepted sequence number for that meter, and none of \(E_x, E_m, T\) is lower than the last accepted value. The pair's owner is then credited with \(\min(T_{GEN}, T_{GRID})\) less what the pair has already been credited. The block commits to the record by a hash chain

\[
H_k = \mathrm{Hash}(H_{k-1} \,\|\, \text{block body}_k).
\]

A third party who later sees \(H_k\), the body, and \(\sigma\) repeats the verify. Acceptance does not depend on a private message to the signer. That is nonrepudiation of the amount: the core cannot deny \(\sigma\) on \(m\), and the public chain fixes the \(m\) that was accepted. Tamper zeroization of \(sk\), specified in the hardware note, is what stops a broken meter from signing a new \(m\).

Account transfers use a second key pair, also post-quantum, so a spend is the same public check. The generation signature and the spend signature are different keys. Stealing a wallet does not let the thief sign a generation record.

## Why the signature is quantum-resistant

Shor’s algorithm factors and computes discrete logarithms in polynomial time on a large quantum computer [Shor 1997]. RSA and elliptic-curve signatures, including the ECDSA used by current public chains, fall under that result. A ledger that still used those schemes would not keep the nonrepudiation property after such a machine exists.

NIST has standardized two signature families against that adversary. ML-DSA (FIPS 204) is a module-lattice signature, derived from CRYSTALS-Dilithium. SLH-DSA (FIPS 205) is a stateless hash-based signature, derived from SPHINCS+. NIST’s statement for ML-DSA is that it is believed secure against an adversary with a large-scale quantum computer [NIST FIPS 204]. Enerchain uses ML-DSA-44 for the meter key so the signature stays short and the sign energy stays on the order of 20 mJ. SLH-DSA remains the fallback if a lattice assumption fails. Account keys may use ML-DSA-65. The draw of the mint path is capped in [meter-burden.md](meter-burden.md). The hardware path is [schematics/mint-path.svg](schematics/mint-path.svg).

The hash in the chain is SHA-384. Grover’s algorithm gives a quadratic speedup for preimage search, not the exponential break Shor gives against discrete log [Grover 1996]. A 384-bit hash keeps a collision and preimage margin after that quadratic loss. The hash does not make the signature quantum-proof. It keeps the chain at the same class of assumption as the hash-based fallback.

## What is not claimed

Quantum-proof would mean security even if the computational assumption is false. Public-key signatures do not have that property. ML-DSA is a belief about lattices, published as a standard, not a proof from information theory. SLH-DSA is the conservative choice, and it is still an assumption on the hash. This protocol is quantum-resistant under those standards. It is not quantum-proof.

## No difficulty, fixed block size

There is no difficulty parameter. Issuance is the token count \(T\) from the sealed registers, not a puzzle. Nothing in the protocol retargets \(q\) or a hash threshold as more meters appear. Block time is a clock constant. A block is valid when its hash chain links and its signatures verify, not when a hash is below a moving target.

The block byte cap \(B\) is a protocol constant. It does not grow with height, with meter count, or with supply. An ML-DSA-44 signature is 2420 bytes [NIST FIPS 204] and the record is 32 bytes. In a binary encoding one issuance is about 2.5 kB and a cap of \(B = 2^{20}\) bytes holds about 400 issuances; the v0.0.1 devnet encodes transactions as JSON with hex fields, about 5 kB each, so about 200. A meter signs once per 10 kWh, not once per kWh, because its records are cumulative. Excess records wait for the next block; since they are cumulative, waiting costs nothing. The cap stays \(B\). If the signer part offers only ML-DSA-87 the signature is 4627 bytes and the counts roughly halve. Throughput at national scale is open item S-4 in [open-items.md](open-items.md).

## Unlimited supply

There is no maximum \(S\). After all accepted issuances,

\[
S = \sum_{\text{pairs } p} \min\bigl(T_{GEN}(p),\, T_{GRID}(p)\bigr),
\]

with no terminal term. \(S\) tracks accepted net-export watt-hours. It is not a monetary cap, and it is not limited by a halving schedule. A transfer moves an existing balance. It does not mint, and it does not require a difficulty increase to stay valid.

## Sources

Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum computer. *SIAM Journal on Computing*, 26(5), 1484–1509. https://doi.org/10.1137/S0097539795293172

Grover, L. K. (1996). A fast quantum mechanical algorithm for database search. In *Proceedings of the 28th Annual ACM Symposium on Theory of Computing*, 212–219. https://doi.org/10.1145/237814.237866

NIST. (2024). *FIPS 204: Module-Lattice-Based Digital Signature Standard*. https://doi.org/10.6028/NIST.FIPS.204

NIST. (2024). *FIPS 205: Stateless Hash-Based Digital Signature Standard*. https://doi.org/10.6028/NIST.FIPS.205
