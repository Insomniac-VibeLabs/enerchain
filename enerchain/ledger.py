"""Ledger state, transactions, blocks and the issuance rule.

Unit: the ledger counts watt-hours (Wh). One token is 1000 Wh, the
EC-MINT1 quantum. Meters mint whole tokens; accounts may transfer any whole
number of Wh, so a token is divisible to the watt-hour.

Issuance rule for a certified pair (GEN meter, GRID meter):

    minted_tokens(pair) = min(tokens_GEN, tokens_GRID)

where tokens_X is the cumulative token field of the latest accepted record
from meter X. Both fields come out of the EC-MINT1 schedule, not from this
code; the ledger only takes the smaller of two hardware counts. Because the
fields are cumulative, records can arrive late, out of step between the two
meters, or be lost, and the pair still converges to the right total. A GRID
meter counts net export at the point of connection, so energy imported and
pushed back out mints nothing.

A record is accepted only if
  - its signature verifies under the certified meter key (empty context),
  - meter id, role, version, class and calibration CRC match the certificate,
  - seq is strictly greater than the last accepted seq for that meter,
  - e_exp, e_imp and tokens do not decrease, and tokens * 1000 <= e_exp,
  - the meter is not revoked.

Ordering in v0.0.1 is proof of authority: the genesis validator set takes
turns by height, and a block is valid only with the scheduled proposer's
ML-DSA-65 signature. There is no difficulty, no mining, and no supply cap.
"""

from __future__ import annotations

import copy
from dataclasses import asdict
from typing import Any

from . import crypto
from .record import ROLE_GEN, ROLE_GRID, MeterRecord, RecordError
from .registry import (MeterCert, PairCert, Revocation, approvals_ok,
                       check_meter_cert)

WH_PER_TOKEN = 1000
BLOCK_BYTES = 1 << 20
TRANSFER_CTX = b"enerchain/v0.0.1/transfer"
BLOCK_CTX = b"enerchain/v0.0.1/block"


class LedgerError(ValueError):
    pass


def tx_hash(tx: dict) -> bytes:
    return crypto.sha384(crypto.canonical(tx))


def transfer_body(chain_id: str, frm: str, to: str, amount: int, nonce: int) -> bytes:
    return crypto.canonical({"type": "transfer", "chain_id": chain_id, "from": frm,
                             "to": to, "amount": amount, "nonce": nonce})


def make_genesis(chain_id: str, validators: list[bytes], certifiers: list[bytes],
                 k: int, time: int = 0) -> dict:
    if not validators:
        raise LedgerError("at least one validator")
    if not 1 <= k <= len(certifiers):
        raise LedgerError("k must be between 1 and the number of certifiers")
    return {
        "chain_id": chain_id,
        "time": time,
        "validators": [v.hex() for v in validators],
        "certifiers": [c.hex() for c in certifiers],
        "k": k,
        "params": {"wh_per_token": WH_PER_TOKEN, "block_bytes": BLOCK_BYTES,
                   "hash": "SHA-384", "account_alg": crypto.ACCOUNT_ALG},
    }


class Ledger:
    def __init__(self, genesis: dict) -> None:
        self.genesis = genesis
        self.chain_id: str = genesis["chain_id"]
        self.validators = [bytes.fromhex(v) for v in genesis["validators"]]
        self.certifiers = [bytes.fromhex(c) for c in genesis["certifiers"]]
        self.k: int = genesis["k"]
        self.state: dict[str, Any] = {"accounts": {}, "meters": {}, "pairs": {},
                                      "supply_wh": 0}
        self.blocks: list[dict] = []
        self.genesis_hash = crypto.sha384(crypto.canonical(genesis))

    # ------------------------------------------------------------------ util
    @property
    def height(self) -> int:
        return len(self.blocks)

    @property
    def tip_hash(self) -> bytes:
        if not self.blocks:
            return self.genesis_hash
        return block_hash(self.blocks[-1])

    def balance(self, addr: str) -> int:
        return self.state["accounts"].get(addr, {}).get("balance", 0)

    def nonce(self, addr: str) -> int:
        return self.state["accounts"].get(addr, {}).get("nonce", 0)

    def proposer_for(self, height: int) -> bytes:
        return self.validators[height % len(self.validators)]

    # ------------------------------------------------------- transactions
    def apply_tx(self, state: dict, tx: dict) -> None:
        """Apply tx to state in place, or raise LedgerError and leave the
        caller to discard the state copy."""
        kind = tx.get("type")
        if kind == "meter_cert":
            self._apply_meter_cert(state, tx)
        elif kind == "pair_cert":
            self._apply_pair_cert(state, tx)
        elif kind == "revoke":
            self._apply_revoke(state, tx)
        elif kind == "issuance":
            self._apply_issuance(state, tx)
        elif kind == "transfer":
            self._apply_transfer(state, tx)
        else:
            raise LedgerError(f"unknown transaction type {kind!r}")

    def _approvals(self, tx: dict) -> list[tuple[bytes, bytes]]:
        return [(bytes.fromhex(p), bytes.fromhex(s)) for p, s in tx.get("approvals", [])]

    def _apply_meter_cert(self, state: dict, tx: dict) -> None:
        c = tx["cert"]
        cert = MeterCert(int(c["meter_id"]), int(c["role"]), c["alg"],
                         bytes.fromhex(c["pk"]), int(c["cal_crc"]),
                         bytes.fromhex(c["image_hash"]))
        try:
            check_meter_cert(cert)
        except ValueError as e:
            raise LedgerError(str(e)) from None
        if not approvals_ok(cert.body(), self._approvals(tx), self.certifiers, self.k):
            raise LedgerError("meter certificate lacks k certifier approvals")
        key = str(cert.meter_id)
        if key in state["meters"]:
            raise LedgerError("meter id already certified")
        state["meters"][key] = {
            "role": cert.role, "alg": cert.alg, "pk": cert.pk.hex(),
            "cal_crc": cert.cal_crc, "image_hash": cert.image_hash.hex(),
            "revoked": False, "pair": None, "last": [0, 0, 0, 0],
        }

    def _apply_pair_cert(self, state: dict, tx: dict) -> None:
        c = tx["cert"]
        cert = PairCert(int(c["pair_id"]), int(c["gen_id"]), int(c["grid_id"]),
                        str(c["beneficiary"]))
        if not approvals_ok(cert.body(), self._approvals(tx), self.certifiers, self.k):
            raise LedgerError("pair certificate lacks k certifier approvals")
        if str(cert.pair_id) in state["pairs"]:
            raise LedgerError("pair id already used")
        gen = state["meters"].get(str(cert.gen_id))
        grid = state["meters"].get(str(cert.grid_id))
        if not gen or not grid:
            raise LedgerError("both meters must be certified first")
        if gen["role"] != ROLE_GEN or grid["role"] != ROLE_GRID:
            raise LedgerError("pair needs one GEN and one GRID meter")
        if gen["pair"] is not None or grid["pair"] is not None:
            raise LedgerError("a meter belongs to at most one pair")
        if gen["revoked"] or grid["revoked"]:
            raise LedgerError("revoked meter")
        if not (cert.beneficiary.startswith("ec") and len(cert.beneficiary) == 42):
            raise LedgerError("bad beneficiary address")
        state["pairs"][str(cert.pair_id)] = {
            "gen": cert.gen_id, "grid": cert.grid_id,
            "beneficiary": cert.beneficiary, "minted_tokens": 0,
            # Tokens counted before the pair existed are not minted
            # retroactively: the pair starts from the current counts.
            "base": [gen["last"][3], grid["last"][3]],
        }
        gen["pair"] = cert.pair_id
        grid["pair"] = cert.pair_id

    def _apply_revoke(self, state: dict, tx: dict) -> None:
        r = tx["revocation"]
        rev = Revocation(int(r["meter_id"]), str(r["reason"]))
        if not approvals_ok(rev.body(), self._approvals(tx), self.certifiers, self.k):
            raise LedgerError("revocation lacks k certifier approvals")
        m = state["meters"].get(str(rev.meter_id))
        if not m:
            raise LedgerError("unknown meter")
        m["revoked"] = True

    def _apply_issuance(self, state: dict, tx: dict) -> None:
        raw = bytes.fromhex(tx["record"])
        sig = bytes.fromhex(tx["sig"])
        try:
            rec = MeterRecord.unpack(raw)
        except RecordError as e:
            raise LedgerError(str(e)) from None
        m = state["meters"].get(str(rec.meter_id))
        if not m:
            raise LedgerError("record from an uncertified meter")
        if m["revoked"]:
            raise LedgerError("record from a revoked meter")
        if not crypto.verify(m["alg"], bytes.fromhex(m["pk"]), raw, sig):
            raise LedgerError("meter signature does not verify")
        if rec.version != 1 or rec.role != m["role"] or rec.class_tag != 0x22:
            raise LedgerError("version, role or class does not match the certificate")
        if rec.cal_crc != m["cal_crc"]:
            raise LedgerError("calibration image differs from the certified one")
        seq0, exp0, imp0, tok0 = m["last"]
        if rec.seq <= seq0:
            raise LedgerError("replayed or stale record (seq)")
        if rec.e_exp < exp0 or rec.e_imp < imp0 or rec.tokens < tok0:
            raise LedgerError("cumulative counter went backward")
        if rec.tokens * WH_PER_TOKEN > rec.e_exp:
            raise LedgerError("tokens exceed export energy")
        m["last"] = [rec.seq, rec.e_exp, rec.e_imp, rec.tokens]
        if m["pair"] is None:
            return
        p = state["pairs"][str(m["pair"])]
        gen = state["meters"][str(p["gen"])]
        grid = state["meters"][str(p["grid"])]
        target = min(gen["last"][3] - p["base"][0], grid["last"][3] - p["base"][1])
        delta = target - p["minted_tokens"]
        if delta > 0:
            p["minted_tokens"] = target
            acct = state["accounts"].setdefault(p["beneficiary"], {"balance": 0, "nonce": 0})
            acct["balance"] += delta * WH_PER_TOKEN
            state["supply_wh"] += delta * WH_PER_TOKEN

    def _apply_transfer(self, state: dict, tx: dict) -> None:
        frm, to = str(tx["from"]), str(tx["to"])
        amount, nonce = int(tx["amount"]), int(tx["nonce"])
        pk = bytes.fromhex(tx["pk"])
        if crypto.address(pk) != frm:
            raise LedgerError("public key does not match the sender address")
        if not (to.startswith("ec") and len(to) == 42):
            raise LedgerError("bad destination address")
        if amount <= 0:
            raise LedgerError("amount must be positive")
        body = transfer_body(self.chain_id, frm, to, amount, nonce)
        if not crypto.verify(crypto.ACCOUNT_ALG, pk, body, bytes.fromhex(tx["sig"]),
                             TRANSFER_CTX):
            raise LedgerError("transfer signature does not verify")
        acct = state["accounts"].get(frm)
        if not acct or acct["nonce"] + 1 != nonce:
            raise LedgerError("bad nonce")
        if acct["balance"] < amount:
            raise LedgerError("insufficient balance")
        acct["balance"] -= amount
        acct["nonce"] = nonce
        dst = state["accounts"].setdefault(to, {"balance": 0, "nonce": 0})
        dst["balance"] += amount

    # ------------------------------------------------------------- blocks
    def state_root(self, state: dict) -> bytes:
        return crypto.sha384(crypto.canonical(state))

    def build_block(self, txs: list[dict], proposer_sk: bytes, time: int) -> dict:
        """Apply as many txs as are valid and fit; return a signed block."""
        state = copy.deepcopy(self.state)
        accepted: list[dict] = []
        size = 2
        for tx in txs:
            tx_size = len(crypto.canonical(tx)) + 1
            if size + tx_size > BLOCK_BYTES:
                break
            trial = copy.deepcopy(state)
            try:
                self.apply_tx(trial, tx)
            except LedgerError:
                continue
            state = trial
            accepted.append(tx)
            size += tx_size
        header = {
            "chain_id": self.chain_id,
            "height": self.height + 1,
            "prev": self.tip_hash.hex(),
            "time": time,
            "tx_root": crypto.sha384(crypto.canonical([tx_hash(t) for t in accepted])).hex(),
            "state_root": self.state_root(state).hex(),
        }
        sig = crypto.sign(crypto.ACCOUNT_ALG, proposer_sk, crypto.canonical(header), BLOCK_CTX)
        return {"header": header, "txs": accepted, "sig": sig.hex()}

    def add_block(self, block: dict) -> None:
        """Validate a block against the tip and apply it, or raise."""
        h = block["header"]
        if h["chain_id"] != self.chain_id:
            raise LedgerError("wrong chain")
        if h["height"] != self.height + 1:
            raise LedgerError("wrong height")
        if h["prev"] != self.tip_hash.hex():
            raise LedgerError("does not extend the tip")
        prev_time = self.blocks[-1]["header"]["time"] if self.blocks else self.genesis["time"]
        if h["time"] < prev_time:
            raise LedgerError("time went backward")
        if len(crypto.canonical(block["txs"])) > BLOCK_BYTES:
            raise LedgerError("block over the byte cap")
        proposer = self.proposer_for(h["height"])
        if not crypto.verify(crypto.ACCOUNT_ALG, proposer, crypto.canonical(h),
                             bytes.fromhex(block["sig"]), BLOCK_CTX):
            raise LedgerError("not signed by the scheduled proposer")
        if h["tx_root"] != crypto.sha384(
                crypto.canonical([tx_hash(t) for t in block["txs"]])).hex():
            raise LedgerError("tx root mismatch")
        state = copy.deepcopy(self.state)
        for tx in block["txs"]:
            self.apply_tx(state, tx)
        if self.state_root(state).hex() != h["state_root"]:
            raise LedgerError("state root mismatch")
        self.state = state
        self.blocks.append(block)

    def replay(self, blocks: list[dict]) -> None:
        for b in blocks:
            self.add_block(b)


def block_hash(block: dict) -> bytes:
    return crypto.sha384(crypto.canonical(block["header"]))


def cert_tx(kind: str, cert: Any, approvals: list[tuple[bytes, bytes]]) -> dict:
    field = "revocation" if kind == "revoke" else "cert"
    body = {k: (v.hex() if isinstance(v, bytes) else v) for k, v in asdict(cert).items()}
    return {"type": kind, field: body,
            "approvals": [[p.hex(), s.hex()] for p, s in approvals]}


def issuance_tx(record: bytes, sig: bytes) -> dict:
    return {"type": "issuance", "record": record.hex(), "sig": sig.hex()}
