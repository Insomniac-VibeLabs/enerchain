# Hardwired cryptography sheets

Edition: doc-0.8 (2026-10-08). These sheets open the secure element and the ledger node. Symbols: IEC register boxes, XOR as ⊕, AND as a labelled gate, flip-flops as DFF.

The novel hardwired path is the schedule counter tied to the sign datapath. A host cannot write \(n\). The element signs only the \(n\) the comparator produced.

| Sheet | What is drawn |
| --- | --- |
| [09-sign-datapath.svg](09-sign-datapath.svg) | CF synchronizer, watt-hour counter, compare to \(q = 1000\), residual subtract, message register, Keccak, NTT, reject bound, signature register. 3.3 V IO, 1.2 V core. |
| [10-keccak-round.svg](10-keccak-round.svg) | One Keccak-f1600 round. χ expanded to NOT, AND, XOR: \(a' = c \oplus (\lnot a \land b)\). Round constants in a ROM addressed by a 0..23 counter. |
| [11-ntt-butterfly.svg](11-ntt-butterfly.svg) | Butterfly \(a' = (a+\zeta b) \bmod 8380417\), \(b' = (a-\zeta b) \bmod 8380417\). Twiddle ROM. Barrett reduction wired. |
| [12-ledger-update.svg](12-ledger-update.svg) | Node verify, cumulative-register compare, SHA-384 chain. No difficulty. Block cap is a length comparator. |

What these sheets are not: a complete transistor netlist. Keccak is 1600 bits by 24 rounds; the polynomial core repeats the butterfly. Drawing every instance would be a plotter job, not a different circuit. The operators and the only legal data path are here.

ML-DSA-44 and Keccak-f1600 are FIPS 204 and FIPS 202. The modulus 8380417 is the ML-DSA prime.
