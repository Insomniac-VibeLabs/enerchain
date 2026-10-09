# Hardwired cryptography sheets

Edition: doc-0.8 (2026-10-08), text corrected in doc-1.3. These sheets open the secure element and the ledger node. Symbols: IEC register boxes, XOR as ⊕, AND as a labelled gate, flip-flops as DFF.

The novel hardwired path is the schedule counter tied to the sign datapath. In revision B the counter is EC-MINT1 and the sign engine is inside the QS7001; sheets 10 and 11 are a sketch of what such an engine does, not a tapeout. A host cannot write the token count \(T\). The signer signs only the record the schedule die built, one per token (1 kWh).

| Sheet | What is drawn |
| --- | --- |
| [09-sign-datapath.svg](09-sign-datapath.svg) | CF_EXP/CF_IMP synchronizers, export and import watt-hour counters, credit compared to \(q = 1000\), the 32-byte record register, then Keccak, NTT, reject bound and signature inside the QS7001. 3.3 V IO, 1.2 V core. |
| [10-keccak-round.svg](10-keccak-round.svg) | One Keccak-f1600 round (SHAKE128 expands \(A\), SHAKE256 hashes the message and the challenge). χ expanded to NOT, AND, XOR: \(a' = c \oplus (\lnot a \land b)\). Round constants in a ROM addressed by a 0..23 counter. |
| [11-ntt-butterfly.svg](11-ntt-butterfly.svg) | Butterfly \(a' = (a+\zeta b) \bmod 8380417\), \(b' = (a-\zeta b) \bmod 8380417\). Twiddle ROM. Barrett reduction wired. |
| [12-ledger-update.svg](12-ledger-update.svg) | Node verify; accept if seq increases and no counter decreases; credit \(\min(T_{GEN}, T_{GRID})\) less what was credited; SHA-384 chain (80 rounds, the SHA-512 core). No difficulty. Block cap is a length comparator. |

What these sheets are not: a complete transistor netlist. Keccak is 1600 bits by 24 rounds; the polynomial core repeats the butterfly. Drawing every instance would be a plotter job, not a different circuit. The operators and the only legal data path are here.

ML-DSA-44 and Keccak-f1600 are FIPS 204 and FIPS 202. The modulus 8380417 = 2²³ − 2¹³ + 1 is the ML-DSA prime. The round constants in `hardware/asic/rtl/keccak_round.v` match the FIPS 202 LFSR, and `ntt_butterfly.v` matches \((a \pm \zeta b) \bmod q\) on random vectors; both remain unsynthesized sketches.
