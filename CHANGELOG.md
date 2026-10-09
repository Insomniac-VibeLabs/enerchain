# Documentation revision log

Enerchain has no software release. Documentation editions use the `doc-` prefix so they cannot be confused with future software release tags (`v1`, `v2`, …), which only increment and would otherwise collide with document references.

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

Software release tags, when they exist, must not be used as documentation edition numbers. Cite a document as `path@doc-0.9` until a later edition supersedes it.
