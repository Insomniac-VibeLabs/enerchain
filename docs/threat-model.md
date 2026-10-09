# Threat model

Edition: v0.0.1 (doc-1.2, 2026-10-09).

The asset is the token count: no one should be able to mint more than the net energy a certified pair of meters measured leaving a site, and no one should be able to spend someone else's tokens. Each row names an attacker, what they try, what stops it, and where the stop lives.

| Attacker and goal | What stops it | Where |
| --- | --- | --- |
| Site owner edits software on the inverter, the radio, or a server to report more energy | The token count is computed in EC-MINT1 from STPM32 pulses and signed in the QS7001. Nothing outside the seal can write a counter or ask for a signature over a different record. The radio has no receive path. | EC-MINT1, QS7001, board |
| Site owner buys grid power into a battery and pushes it back out | The GRID meter counts import and export and mints on the net-export high-water mark. The loop nets to zero. | EC-MINT1 schedule; `test_battery_loop_mints_nothing` |
| Site owner forces current through the generator terminals from the grid side | The GRID meter at the point of connection sees the same energy come in and go out. The pair mints min(GEN, GRID). | Ledger pair rule |
| Site owner splits intervals to round up | There is no rounding: credit carries pulse by pulse. | EC-MINT1 schedule |
| Replay an old record, or submit records out of order | `seq` must increase; counters must not go backward. Old records are refused; the newest cumulative record wins. | Ledger; QS7001 rollback guard |
| Cut power to reset counters | Counters, sequence and calibration live in FRAM with two CRC-checked slots. A blank or rolled-back FRAM makes the QS7001 refuse to sign until counts pass the last signed values, and the ledger refuses lower counts. | EC-MINT1, QS7001, ledger |
| Recalibrate the meter (more pulses per kWh) | The calibration image is locked into FRAM once, and its CRC is in every record and in the certificate. A different image produces records the ledger refuses. | EC-MINT1, ledger |
| Open the cover while powered | The mesh opens, the latch fires, EC-MINT1 sends `5C 5C`, the QS7001 erases its key and records the wipe, the signer rail is switched off. | Board, firmware |
| Open the cover while unpowered | **Not stopped in revision B.** See open item O-1. Damage per opened meter is bounded by its partner meter; a pair under one owner is not bounded. | Open |
| Clone a meter | The private key never leaves the QS7001; the certificate binds the public key. A clone without the key produces signatures that do not verify. | QS7001, registry |
| A manufacturer certifies fake meters | Certification needs k of n independent certifiers named in genesis. | Registry, governance |
| Steal a wallet key | Spends with that key are valid; the thief cannot sign generation records, which use meter keys. Wallet keys in v0.0.1 are unencrypted files. | Wallet (S-2) |
| A validator censors or reorders | v0.0.1 has a fixed proof-of-authority set and no fork choice. A dishonest validator can stall its own turns and delay transactions; it cannot forge a meter or account signature or mint. | Consensus (S-1) |
| A large quantum computer | Signatures are ML-DSA (FIPS 204); hashes are SHA-384. This is quantum-resistant under those standards, not quantum-proof. SLH-DSA is the fallback if lattice assumptions fail. | [ledger-nonrepudiation.md](ledger-nonrepudiation.md) |
| Side channels on the signer | The QS7001 vendor claims side-channel and fault-injection protection for ML-DSA. The devnet's Python ML-DSA has none. | O-3, S-2 |

What a token does not prove: that the energy was renewable, that it displaced anything, that the grid needed it at that moment, or that it was not also sold to a utility or certified elsewhere (S-5).
