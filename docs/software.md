# Software, v0.0.1

Edition: v0.0.1 (doc-1.4, 2026-10-10).

The `enerchain` Python package is the software half of the design: the ledger that turns signed meter records into tokens, the wallet that moves them, and a reference model of the meter that produces those records. It runs a development network on one machine. It is not a production ledger; [open-items.md](open-items.md) S-1 to S-10 says what is missing.

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
| `record` | The 32-byte record EC-MINT1 builds and the QS7001 signs (kind 0, token; kind 1, tamper), the UART frame, CRC-8 and CRC-16 |
| `meter` | EC-MINT1 (schedule, FRAM slots, calibration lock, sequence, daily re-send, tamper record), the QS7001 oracle (one keygen of two keys, rollback guard, wipe, one tamper signature), and `EnergyMeter`, which turns watts into pulses |
| `crypto` | ML-DSA-44/65/87, SHA-384, canonical JSON, addresses |
| `registry` | Meter, pair, revocation, rebind and attestation certificates, approved by k of n certifiers; certifier sectors |
| `ledger` | State, the issuance rule, revocation with notice and contest, rebind, escrow, the balance check, transfers, blocks, proof-of-authority ordering |
| `wallet` | ML-DSA-65 account keys, signed transfers, pair requests and contests |
| `node` | A devnet persisted as `genesis.json`, `blocks.jsonl`, `mempool.jsonl` |
| `sim` | A solar site with a household load, an optional battery loop and an optional tap before the GRID meter, metered by a GEN/GRID pair and an optional LOAD meter |
| `cli` | The `enerchain` command |

## Rules the ledger enforces

Unit: the ledger counts watt-hours. One token is 1000 Wh. Meters mint whole tokens; transfers can move any whole number of watt-hours.

A meter exists on the ledger only through a `meter_cert` approved by k of the n certifier keys in genesis. The certificate binds the meter id, its role (GEN, GRID or LOAD), its meter key and tamper key and their algorithm, the CRC-16 of its calibration image, and the hash of the signer image. A `pair_cert`, also k-of-n, binds one GEN and one GRID meter, and optionally one LOAD meter, to a beneficiary address, with a loss allowance (`loss_ppm`, default 2 %) and the hash of the approved single-line diagram (`site_hash`). Genesis labels each certifier with a sector and refuses a set in which one sector holds k keys.

An `issuance` carries a record and its signature. A token record (kind 0) is accepted only if the signature verifies under the certified meter key; id, role, version, class and calibration CRC match the certificate; `seq` is greater than the last accepted one; none of the three counters went backward; `tokens × 1000 ≤ e_exp`; if the meter is revoked, `seq` is at or below the revocation's effective seq; and if the meter sent a tamper record, `seq` is below that one. A tamper record (kind 1) passes the same checks under the tamper key, marks the meter wiped, and mints nothing. Then

```
T_side = Σ over the meters that have held the side (tokens_m − base_m)
minted(pair) = min(T_GEN, T_GRID + attested)
```

where `base` is each meter's count when it joined the pair: when the pair was requested, if a `pair_request` was filed, else when it was certified. The difference from the last minted total is credited to the beneficiary. Because every record is cumulative, records may arrive late, out of step between the two meters, or not at all, and the pair converges on the right total. A replayed or older record fails the `seq` check. `attested` is zero unless certifiers released escrow.

The rules that stop a dishonest grid operator from under-crediting a supplier are in [grid-operator.md](grid-operator.md):

| Transaction | Signed by | Effect |
| --- | --- | --- |
| `pair_request` | the beneficiary's account | fixes the pair's starting counts now |
| `revoke` | k certifiers (pending, 30-day notice) or `k_urgent` (at once) | reason from a list, evidence hash, effective seq |
| `contest` | the pair's beneficiary | stops a pending revocation |
| `rebind` | k certifiers | replaces a pair's revoked or wiped meter |
| `attest` | k certifiers | releases escrow (`outage` or `balance`), capped and numbered |

A pair is in outage while its GRID meter is wiped, revoked or unheard for 3 days; GEN tokens counted since it was last heard are escrow. With a LOAD meter, each GRID record is paired with the next LOAD record (and the reverse) to bound GEN − GRID − LOAD from below; above the loss allowance the pair's balance flag is raised and the excess is escrow. `enerchain pair report` shows all of it.

A `transfer` names sender, recipient, amount and nonce, carries the sender's ML-DSA-65 public key and signature over those fields and the chain id, and must use the next nonce.

A block lists transactions, the SHA-384 roots of those transactions and of the resulting state, and the scheduled validator's signature. Validators take turns by height. Blocks are capped at 2²⁰ bytes of transactions. There is no difficulty and no supply cap. Two nodes that replay the same genesis and blocks reach the same state; the test suite checks that.

## What the tests cover

- Record packing, CRC check values, range checks.
- Meter model: nothing counted before provisioning; an empty transcript does not arm; one token per q; a record every N tokens; import cancels export; a power cut keeps counters, sequence and calibration; unpersisted pulses are lost and never double counted; a FRAM rolled back to blank cannot get lower counts signed; keygen happens once; zeroize ends signing for good after one tamper record under the tamper key; the tamper key does not survive a power cut and signs once; a quiet day re-sends the last record under a new seq; a LOAD meter counts consumption.
- Ledger: one meter alone mints nothing; the pair mints the smaller count; out-of-step and lost records converge; replay and tampered records are refused; a record under another calibration image is refused; tokens above energy are refused; certification needs k distinct genesis certifiers; pairs need one GEN and one GRID and a meter joins one pair; revocation stops minting; transfers check nonce, balance, chain id and key; blocks check proposer, state root and height. Against a dishonest grid operator: genesis refuses a sector holding k keys; a revocation honours records up to its effective seq, needs a listed reason and evidence, waits out its notice unless k_urgent signed it, and stops when the beneficiary contests; a tamper record marks a wipe and mints nothing while earlier records still count; a wiped GRID meter is rebound and its outage escrow released once, capped; a silent GRID meter opens an outage that its late records close; a pair request fixes the start while certifiers wait; a LOAD meter mints nothing and balances; a tap between GEN and GRID raises the flag; anyone may submit a raw frame.
- System: a simulated site over two days with and without a 3 kW grid-battery-grid loop mints the same; minting never exceeds generation or export; an honest site with a LOAD meter stays unflagged with and without the loop; a 300 W tap before the GRID meter is flagged and the claimable amount never exceeds what it took; the CLI, including `frame submit` and `pair report`; the RTL matches the model.

## CLI

```
enerchain --version
enerchain demo [--days N] [--battery-loop-w W] [--load] [--siphon-w W]
enerchain devnet init DIR [--validators N] [--certifiers N] [--k K]
enerchain devnet produce DIR
enerchain devnet show DIR
enerchain pair report DIR PAIR_ID
enerchain pair request DIR WALLET GEN_ID GRID_ID [--load LOAD_ID]
enerchain pair contest DIR WALLET METER_ID
enerchain wallet new FILE
enerchain wallet address FILE
enerchain balance DIR ADDRESS
enerchain transfer DIR WALLET TO AMOUNT_WH
enerchain frame verify --alg ML-DSA-44 --pk HEX FRAME_HEX
enerchain frame submit DIR [--alg ML-DSA-44] FRAME_HEX
```

`frame verify` takes the hex of a UART frame from a real or simulated EC-SEAL1 and checks its signature against the meter's published key (the tamper key, for a tamper record). `frame submit` queues a frame on a devnet: anyone who hears a frame may submit it. `pair request` files a pair request from the beneficiary's wallet; `pair contest` contests a pending revocation of a meter in the wallet's pair. `pair report` prints a pair's side counts, minted and attested tokens, outage, escrow, balance flag and member revocations. `demo --siphon-w 300` adds a LOAD meter and a 300 W tap before the GRID meter, and prints the balance flag each day.
