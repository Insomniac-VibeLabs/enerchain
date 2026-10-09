# Software, v0.0.1

Edition: v0.0.1 (doc-1.2, 2026-10-09).

The `enerchain` Python package is the software half of the design: the ledger that turns signed meter records into tokens, the wallet that moves them, and a reference model of the meter that produces those records. It runs a development network on one machine. It is not a production ledger; [open-items.md](open-items.md) S-1 to S-8 says what is missing.

## Install and check

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[test]'
pytest                      # ledger, meter model, devnet, CLI; RTL check if iverilog is installed
python3 tools/check_rtl.py  # EC-MINT1 RTL against the Python model, byte for byte
enerchain demo              # three simulated days on a two-validator devnet
```

`dilithium-py` 1.4.0 provides ML-DSA (FIPS 204). It is pure Python, fine for a devnet, not constant-time.

## Pieces

| Module | What it is |
| --- | --- |
| `record` | The 32-byte record EC-MINT1 builds and the QS7001 signs, the UART frame, CRC-8 and CRC-16 |
| `meter` | EC-MINT1 (schedule, FRAM slots, calibration lock, sequence), the QS7001 oracle (one keygen, rollback guard, wipe), and `EnergyMeter`, which turns watts into pulses |
| `crypto` | ML-DSA-44/65/87, SHA-384, canonical JSON, addresses |
| `registry` | Meter, pair and revocation certificates, approved by k of n certifiers |
| `ledger` | State, the issuance rule, transfers, blocks, proof-of-authority ordering |
| `wallet` | ML-DSA-65 account keys and signed transfers |
| `node` | A devnet persisted as `genesis.json`, `blocks.jsonl`, `mempool.jsonl` |
| `sim` | A solar site with a household load and an optional battery loop, metered by a GEN/GRID pair |
| `cli` | The `enerchain` command |

## Rules the ledger enforces

Unit: the ledger counts watt-hours. One token is 1000 Wh. Meters mint whole tokens; transfers can move any whole number of watt-hours.

A meter exists on the ledger only through a `meter_cert` approved by k of the n certifier keys in genesis. The certificate binds the meter id, its role (GEN or GRID), its public key and algorithm, the CRC-16 of its calibration image, and the hash of the signer image. A `pair_cert`, also k-of-n, binds one GEN and one GRID meter to a beneficiary address.

An `issuance` carries a record and its signature. It is accepted only if the signature verifies under the certified key; id, role, version, class and calibration CRC match the certificate; `seq` is greater than the last accepted one; none of the three counters went backward; `tokens × 1000 ≤ e_exp`; and the meter is not revoked. Then

```
minted(pair) = min(tokens_GEN − base_GEN, tokens_GRID − base_GRID)
```

where `base` is each meter's count when the pair was certified. The difference from the last minted total is credited to the beneficiary. Because every record is cumulative, records may arrive late, out of step between the two meters, or not at all, and the pair converges on the right total. A replayed or older record fails the `seq` check.

A `transfer` names sender, recipient, amount and nonce, carries the sender's ML-DSA-65 public key and signature over those fields and the chain id, and must use the next nonce.

A block lists transactions, the SHA-384 roots of those transactions and of the resulting state, and the scheduled validator's signature. Validators take turns by height. Blocks are capped at 2²⁰ bytes of transactions. There is no difficulty and no supply cap. Two nodes that replay the same genesis and blocks reach the same state; the test suite checks that.

## What the tests cover

- Record packing, CRC check values, range checks.
- Meter model: nothing counted before provisioning; an empty transcript does not arm; one token per q; a record every N tokens; import cancels export; a power cut keeps counters, sequence and calibration; unpersisted pulses are lost and never double counted; a FRAM rolled back to blank cannot get lower counts signed; keygen happens once; zeroize ends signing for good.
- Ledger: one meter alone mints nothing; the pair mints the smaller count; out-of-step and lost records converge; replay and tampered records are refused; a record under another calibration image is refused; tokens above energy are refused; certification needs k distinct genesis certifiers; pairs need one GEN and one GRID and a meter joins one pair; revocation stops minting; transfers check nonce, balance, chain id and key; blocks check proposer, state root and height.
- System: a simulated site over two days with and without a 3 kW grid-battery-grid loop mints the same; minting never exceeds generation or export; the CLI; the RTL matches the model.

## CLI

```
enerchain --version
enerchain demo [--days N] [--battery-loop-w W]
enerchain devnet init DIR [--validators N] [--certifiers N] [--k K]
enerchain devnet produce DIR
enerchain devnet show DIR
enerchain wallet new FILE
enerchain wallet address FILE
enerchain balance DIR ADDRESS
enerchain transfer DIR WALLET TO AMOUNT_WH
enerchain frame verify --alg ML-DSA-44 --pk HEX FRAME_HEX
```

`frame verify` takes the hex of a UART frame from a real or simulated EC-SEAL1 and checks its signature against the meter's published key.
