# Revision log

Software releases are tagged `vX.Y.Z`. Documentation editions keep the `doc-` prefix so a document can be cited apart from the code. Each software release names the documentation edition it ships with.

## Software releases

| Release | Date | Docs | Scope |
| --- | --- | --- | --- |
| unreleased | 2026-10-09 | doc-1.3 | One signed record and one ledger credit per token, 1 kWh (`SIGN_EVERY` 10 → 1 in the RTL and the model), with tests. R23 1 kΩ on the signer rail. `tools/gen_schematics.py` and a CI check for the circuit sheets. |
| v0.0.1 | 2026-10-09 | doc-1.2 | First runnable release. `enerchain` Python package: 32-byte meter record, bit-exact EC-MINT1 and QS7001 model, ML-DSA keys, k-of-n meter and pair certification, issuance rule min(GEN, GRID) on cumulative records, transfers, proof-of-authority blocks with SHA-384 roots, wallet, devnet CLI, pytest suite. EC-MINT1 RTL rewritten (net-export schedule, 48-bit counters, F-RAM persistence, signer ready-poll, streamed signature) with an end-to-end testbench and an RTL-vs-model check. QS7001 image: one keygen, persistent wipe, rollback guard, host test. EC-SEAL1 revision B after an electrical review. CI. |

## Documentation editions

| Edition | Date | Scope |
| --- | --- | --- |
| doc-0.1 | 2026-10-08 | Initial concept notes. |
| doc-0.2 | 2026-10-08 | Layered rewrite with citations. |
| doc-0.3 | 2026-10-08 | Removed the doc-0.2 non-claims. Concept set restated around the electricity-currency hypothesis, hardware-locked issuance, and regional-to-planetary trade. |
| doc-0.4 | 2026-10-08 | Added hardware binding of the energy integral to token issuance. Confirmed the token is proof of generation, not a physical export. |
| doc-0.5 | 2026-10-08 | Added public-ledger nonrepudiation, NIST post-quantum signatures, a fixed block cap, no difficulty parameter, and uncapped supply. |
| doc-0.6 | 2026-10-08 | Capped mint-path draw at a present-day meter. Switched the meter key to ML-DSA-44. Added the hardware-only schematic. |
| doc-0.7 | 2026-10-08 | Split the mint path into IEC-symbol circuit sheets and a burden chart. |
| doc-0.8 | 2026-10-08 | Opened the sign datapath and the ledger update to registers, Keccak gates, and an NTT butterfly. |
| doc-0.9 | 2026-10-08 | Added a PCB order pack: BOM, netlist, fab notes. No Gerber and no GDSII. |
| doc-1.0 | 2026-10-08 | Added the EC-MINT1 ASIC handoff: spec, RTL, constraints. Not a tapeout. |
| doc-1.1 | 2026-10-09 | Chose hardware over a software wallet and over an on-die ML-DSA core. EC-SEAL1 board order, EC-MINT1 schedule die, QS7001 signing oracle. Corrected the doc-0.9 MOV, LDO, and divider. The how-to is the reading order and the build. |
| doc-1.2 | 2026-10-09 | Ships with v0.0.1. Electrical review of doc-1.1 ([docs/electrical-review.md](docs/electrical-review.md)): logic ground moved to Line at the shunt, LNK304 supply replaces the reversed X2 dropper, P-FET signer rail, F-RAM for counters and calibration, import pulses. Net-export schedule and the pair rule replace per-interval agreement. New: threat model, open items, software guide, prior art in the whitepaper. |

| doc-1.3 | 2026-10-09 | Math and drawing audit. Every token (1 kWh) is now signed and credited on its own instead of every tenth. The energy-verification example record was impossible (export − import must equal 1000 × tokens in a record); replaced with one produced by the model. Corrected: tamper photocurrent (≈ 70 µA, not 60), MOV-clamp voltage per divider part (177.5 V), sign-energy ratio per kWh (5 × 10⁻⁹), block-capacity and throughput figures, SHA-384 rounds (80) and SHAKE128 for ExpandA on the crypto sheets. New finding M-8: Q4 and Q5 could conduct together and brown out the 3.3 V rail; R23 raised from 47 Ω to 1 kΩ. Circuit sheets 01–08 and the mint path redrawn for revision B, generated and checked against the netlist. |

Software release tags must not be used as documentation edition numbers. Cite a document as `path@doc-1.2` until a later edition supersedes it.
