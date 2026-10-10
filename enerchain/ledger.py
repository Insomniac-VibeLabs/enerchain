"""Ledger state, transactions, blocks and the issuance rule.

Unit: the ledger counts watt-hours (Wh). One token is 1000 Wh, the
EC-MINT1 quantum. Meters mint whole tokens; accounts may transfer any whole
number of Wh, so a token is divisible to the watt-hour.

Issuance rule for a certified pair (GEN meter, GRID meter):

    minted_tokens(pair) = min(T_GEN, T_GRID + attested)

where T_X is the sum, over the meters that have held that side of the pair,
of (latest accepted token count - the count when it joined). Both fields
come out of the EC-MINT1 schedule, not from this code; the ledger only takes
the smaller of two hardware counts. Because the fields are cumulative,
records can arrive late, out of step between the two meters, or be lost, and
the pair still converges to the right total. A GRID meter counts net export
at the point of connection, so energy imported and pushed back out mints
nothing. ``attested`` is escrowed credit that k certifiers released (see
below); it is zero unless a GRID meter failed or energy went missing between
the meters, and the GEN count still caps it.

A token record (kind 0) is accepted only if
  - its signature verifies under the certified meter key (empty context),
  - meter id, role, version, class and calibration CRC match the certificate,
  - seq is strictly greater than the last accepted seq for that meter,
  - e_exp, e_imp and tokens do not decrease, and tokens * 1000 <= e_exp,
  - if the meter is revoked, seq is at or below the revocation's
    effective seq, and if it sent a tamper record, seq is below that one.
A tamper record (kind 1) verifies under the meter's tamper key, passes the
same order checks, mints nothing, and marks the meter wiped.

What a dishonest grid operator could do to under-credit a supplier, and the
rule here that answers it, is docs/grid-operator.md:
  - revocation takes effect at a stated seq, so energy already measured is
    still credited; it waits out a notice period the beneficiary can contest
    unless k_urgent certifiers sign it;
  - a revoked or wiped meter can be replaced in its pair (rebind);
  - while the GRID side is silent, revoked or wiped, GEN-only tokens are
    held in escrow, released only by a k-of-n attestation;
  - a pair request fixes the starting counts when it is filed, so a slow
    certifier cannot erase energy exported while it waits;
  - with a LOAD meter, GEN - GRID - LOAD beyond the pair's loss allowance
    raises a public balance flag, and the missing energy is claimable;
  - genesis refuses a certifier set in which one sector holds k keys.

Ordering in v0.0.1 is proof of authority: the genesis validator set takes
turns by height, and a block is valid only with the scheduled proposer's
ML-DSA-65 signature. There is no difficulty, no mining, and no supply cap.
"""

from __future__ import annotations

import copy
from dataclasses import asdict
from typing import Any

from . import crypto
from .record import (KIND_TAMPER, ROLE_GEN, ROLE_GRID, ROLE_LOAD, MeterRecord,
                     RecordError, parse_frame)
from .registry import (ATTEST_REASONS, EVIDENCE_LEN, REASONS, SECTORS,
                       Attestation, MeterCert, PairCert, PairRebind, Revocation,
                       check_meter_cert, check_sectors, count_approvals)

WH_PER_TOKEN = 1000
BLOCK_BYTES = 1 << 20
TRANSFER_CTX = b"enerchain/v0.0.1/transfer"
BLOCK_CTX = b"enerchain/v0.0.1/block"
ACCOUNT_CTX = b"enerchain/v0.0.1/account"   # pair requests and contests

NOTICE_S = 30 * 86400     # a contestable revocation waits this long
SILENT_S = 3 * 86400      # a GRID meter unheard for this long is in outage
MAX_LOSS_PPM = 200_000    # a pair's loss allowance may not exceed 20 %

ROLE_SIDE = {ROLE_GEN: "gen", ROLE_GRID: "grid", ROLE_LOAD: "load"}


class LedgerError(ValueError):
    pass


def tx_hash(tx: dict) -> bytes:
    return crypto.sha384(crypto.canonical(tx))


def transfer_body(chain_id: str, frm: str, to: str, amount: int, nonce: int) -> bytes:
    return crypto.canonical({"type": "transfer", "chain_id": chain_id, "from": frm,
                             "to": to, "amount": amount, "nonce": nonce})


def pair_request_body(chain_id: str, gen_id: int, grid_id: int, load_id: int,
                      beneficiary: str) -> bytes:
    return crypto.canonical({"type": "pair_request", "chain_id": chain_id,
                             "gen_id": gen_id, "grid_id": grid_id,
                             "load_id": load_id, "beneficiary": beneficiary})


def contest_body(chain_id: str, meter_id: int) -> bytes:
    return crypto.canonical({"type": "contest", "chain_id": chain_id,
                             "meter_id": meter_id})


def request_key(gen_id: int, grid_id: int, load_id: int, beneficiary: str) -> str:
    return f"{gen_id}/{grid_id}/{load_id}/{beneficiary}"


def make_genesis(chain_id: str, validators: list[bytes], certifiers: list[bytes],
                 k: int, time: int = 0, sectors: list[str] | None = None,
                 k_urgent: int | None = None, notice_s: int = NOTICE_S,
                 silent_s: int = SILENT_S) -> dict:
    """Genesis document. ``sectors`` labels each certifier (default: the
    SECTORS list in order); no sector may hold k keys. ``k_urgent``
    (default k + 1, at most n) is the threshold for a revocation that takes
    effect at once and cannot be contested."""
    n = len(certifiers)
    if not validators:
        raise LedgerError("at least one validator")
    if not 1 <= k <= n:
        raise LedgerError("k must be between 1 and the number of certifiers")
    if sectors is None:
        sectors = [SECTORS[i % len(SECTORS)] for i in range(n)]
    if len(sectors) != n:
        raise LedgerError("one sector per certifier")
    try:
        check_sectors(sectors, k)
    except ValueError as e:
        raise LedgerError(str(e)) from None
    if k_urgent is None:
        k_urgent = min(n, k + 1)
    if not k <= k_urgent <= n:
        raise LedgerError("k_urgent must be between k and the number of certifiers")
    if notice_s < 0 or silent_s <= 0:
        raise LedgerError("notice and silence periods must be positive")
    return {
        "chain_id": chain_id,
        "time": time,
        "validators": [v.hex() for v in validators],
        "certifiers": [c.hex() for c in certifiers],
        "certifier_sectors": list(sectors),
        "k": k,
        "k_urgent": k_urgent,
        "params": {"wh_per_token": WH_PER_TOKEN, "block_bytes": BLOCK_BYTES,
                   "hash": "SHA-384", "account_alg": crypto.ACCOUNT_ALG,
                   "notice_s": notice_s, "silent_s": silent_s},
    }


# ---------------------------------------------------------------- pair views
def side_tokens(state: dict, pair: dict, side: str) -> int:
    """Tokens counted on one side of a pair, across every meter that held it."""
    return sum(state["meters"][str(e["id"])]["last"][3] - e["base"]
               for e in pair["sides"][side])


def meter_retired(m: dict) -> bool:
    """Wiped (tamper record on chain) or under an active revocation."""
    rev = m["revocation"]
    return m["wiped"] is not None or (rev is not None and rev["status"] == "active")


def outage_open(state: dict, pair: dict, silent_s: int) -> bool:
    """The pair's current GRID meter is retired, or unheard for silent_s."""
    cur = pair["sides"]["grid"][-1]
    m = state["meters"][str(cur["id"])]
    if meter_retired(m):
        return True
    heard = m["last_time"] if m["last_time"] is not None else cur["since"]
    return state["time"] - heard > silent_s


def claimable(state: dict, pair: dict, silent_s: int) -> dict:
    """Escrowed tokens an attestation may release, by reason.

    outage:  tokens the GEN side counted while the GRID side could not
             (silent, revoked or wiped), plus what earlier GRID outages left
             when their meter was replaced.
    balance: with a LOAD meter, GEN - GRID - LOAD - attested beyond the loss
             allowance at the last record.
    """
    live = 0
    if outage_open(state, pair, silent_s):
        live = max(0, side_tokens(state, pair, "gen") - pair["grid_seen_gen"]
                   - pair["outage_attested"])
    bal = pair["balance"]
    over = max(0, bal["residual"] - bal["allowance"]) if pair["sides"]["load"] else 0
    return {"outage": pair["escrow"] + live, "outage_live": live, "balance": over}


class Ledger:
    def __init__(self, genesis: dict) -> None:
        self.genesis = genesis
        self.chain_id: str = genesis["chain_id"]
        self.validators = [bytes.fromhex(v) for v in genesis["validators"]]
        self.certifiers = [bytes.fromhex(c) for c in genesis["certifiers"]]
        self.sectors: list[str] = genesis["certifier_sectors"]
        self.k: int = genesis["k"]
        self.k_urgent: int = genesis["k_urgent"]
        self.notice_s: int = genesis["params"]["notice_s"]
        self.silent_s: int = genesis["params"]["silent_s"]
        self.state: dict[str, Any] = {"accounts": {}, "meters": {}, "pairs": {},
                                      "requests": {}, "supply_wh": 0,
                                      "height": 0, "time": genesis["time"]}
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

    def pair_report(self, pair_id: int) -> dict:
        """Everything a supplier needs to see whether its pair is being
        under-credited: side counts, escrow, balance flag, revocations."""
        st = self.state
        p = st["pairs"].get(str(pair_id))
        if p is None:
            raise LedgerError("unknown pair")
        meters = {}
        for side, entries in p["sides"].items():
            for e in entries:
                m = st["meters"][str(e["id"])]
                meters[str(e["id"])] = {"side": side, "base": e["base"],
                                        "last": m["last"], "last_time": m["last_time"],
                                        "revocation": m["revocation"], "wiped": m["wiped"]}
        return {
            "pair_id": pair_id, "beneficiary": p["beneficiary"],
            "tokens": {s: side_tokens(st, p, s) for s in ("gen", "grid", "load")},
            "minted_tokens": p["minted_tokens"], "attested_tokens": p["attested_tokens"],
            "outage_open": outage_open(st, p, self.silent_s),
            "claimable": claimable(st, p, self.silent_s),
            "balance": p["balance"], "loss_ppm": p["loss_ppm"],
            "requested": p["requested"], "certified": p["certified"],
            "meters": meters,
        }

    # ------------------------------------------------------- transactions
    def begin_block(self, state: dict, height: int, time: int) -> None:
        """Block-level bookkeeping before any transaction: the clock, and
        revocations whose notice period has run out without a contest."""
        state["height"] = height
        state["time"] = time
        for mid in sorted(state["meters"], key=int):
            rev = state["meters"][mid]["revocation"]
            if rev and rev["status"] == "pending" and time >= rev["activates"]:
                rev["status"] = "active"

    def apply_tx(self, state: dict, tx: dict) -> None:
        """Apply tx to state in place, or raise LedgerError and leave the
        caller to discard the state copy."""
        kind = tx.get("type")
        handlers = {
            "meter_cert": self._apply_meter_cert,
            "pair_request": self._apply_pair_request,
            "pair_cert": self._apply_pair_cert,
            "revoke": self._apply_revoke,
            "contest": self._apply_contest,
            "rebind": self._apply_rebind,
            "attest": self._apply_attest,
            "issuance": self._apply_issuance,
            "transfer": self._apply_transfer,
        }
        if kind not in handlers:
            raise LedgerError(f"unknown transaction type {kind!r}")
        handlers[kind](state, tx)

    def _approvals(self, tx: dict) -> list[tuple[bytes, bytes]]:
        return [(bytes.fromhex(p), bytes.fromhex(s)) for p, s in tx.get("approvals", [])]

    def _need(self, body: bytes, tx: dict, what: str) -> int:
        n = count_approvals(body, self._approvals(tx), self.certifiers)
        if n < self.k:
            raise LedgerError(f"{what} lacks k certifier approvals")
        return n

    def _account(self, tx: dict, body: bytes, addr: str) -> None:
        pk = bytes.fromhex(tx["pk"])
        if crypto.address(pk) != addr:
            raise LedgerError("public key does not match the account")
        if not crypto.verify(crypto.ACCOUNT_ALG, pk, body, bytes.fromhex(tx["sig"]),
                             ACCOUNT_CTX):
            raise LedgerError("account signature does not verify")

    @staticmethod
    def _evidence(h: str) -> bytes:
        b = bytes.fromhex(h)
        if len(b) != EVIDENCE_LEN:
            raise LedgerError("evidence must be a SHA-384 hash")
        return b

    def _apply_meter_cert(self, state: dict, tx: dict) -> None:
        c = tx["cert"]
        cert = MeterCert(int(c["meter_id"]), int(c["role"]), c["alg"],
                         bytes.fromhex(c["pk"]), bytes.fromhex(c["tamper_pk"]),
                         int(c["cal_crc"]), bytes.fromhex(c["image_hash"]))
        try:
            check_meter_cert(cert)
        except ValueError as e:
            raise LedgerError(str(e)) from None
        self._need(cert.body(), tx, "meter certificate")
        key = str(cert.meter_id)
        if key in state["meters"]:
            raise LedgerError("meter id already certified")
        state["meters"][key] = {
            "role": cert.role, "alg": cert.alg, "pk": cert.pk.hex(),
            "tamper_pk": cert.tamper_pk.hex(),
            "cal_crc": cert.cal_crc, "image_hash": cert.image_hash.hex(),
            "pair": None, "last": [0, 0, 0, 0], "last_time": None,
            "revocation": None, "wiped": None,
        }

    def _free_meter(self, state: dict, mid: int, role: int) -> dict:
        m = state["meters"].get(str(mid))
        if not m:
            raise LedgerError("meters must be certified first")
        if m["role"] != role:
            raise LedgerError("pair needs one GEN and one GRID meter, and LOAD in the load slot")
        if m["pair"] is not None:
            raise LedgerError("a meter belongs to at most one pair")
        if m["revocation"] is not None or m["wiped"] is not None:
            raise LedgerError("revoked or wiped meter")
        return m

    def _apply_pair_request(self, state: dict, tx: dict) -> None:
        gen_id, grid_id = int(tx["gen_id"]), int(tx["grid_id"])
        load_id, who = int(tx.get("load_id", 0)), str(tx["beneficiary"])
        self._account(tx, pair_request_body(self.chain_id, gen_id, grid_id, load_id, who), who)
        gen = self._free_meter(state, gen_id, ROLE_GEN)
        grid = self._free_meter(state, grid_id, ROLE_GRID)
        load = self._free_meter(state, load_id, ROLE_LOAD) if load_id else None
        key = request_key(gen_id, grid_id, load_id, who)
        if key in state["requests"]:
            raise LedgerError("pair already requested")
        state["requests"][key] = {
            "bases": [gen["last"][3], grid["last"][3], load["last"][3] if load else 0],
            "height": state["height"], "time": state["time"],
        }

    def _apply_pair_cert(self, state: dict, tx: dict) -> None:
        c = tx["cert"]
        cert = PairCert(int(c["pair_id"]), int(c["gen_id"]), int(c["grid_id"]),
                        str(c["beneficiary"]), int(c.get("load_id", 0)),
                        int(c.get("loss_ppm", PairCert.loss_ppm)),
                        bytes.fromhex(c.get("site_hash", PairCert.site_hash.hex())))
        if not 0 <= cert.loss_ppm <= MAX_LOSS_PPM:
            raise LedgerError("loss allowance out of range")
        if len(cert.site_hash) != EVIDENCE_LEN:
            raise LedgerError("site hash must be a SHA-384 hash")
        self._need(cert.body(), tx, "pair certificate")
        if str(cert.pair_id) in state["pairs"]:
            raise LedgerError("pair id already used")
        gen = self._free_meter(state, cert.gen_id, ROLE_GEN)
        grid = self._free_meter(state, cert.grid_id, ROLE_GRID)
        load = self._free_meter(state, cert.load_id, ROLE_LOAD) if cert.load_id else None
        if not (cert.beneficiary.startswith("ec") and len(cert.beneficiary) == 42):
            raise LedgerError("bad beneficiary address")
        # Tokens counted before the pair was requested are not minted
        # retroactively. A request on chain fixes the starting counts when it
        # is filed, so the time certifiers take to approve costs nothing.
        req = state["requests"].pop(
            request_key(cert.gen_id, cert.grid_id, cert.load_id, cert.beneficiary), None)
        if req:
            bases = req["bases"]
            requested = {"height": req["height"], "time": req["time"]}
        else:
            bases = [gen["last"][3], grid["last"][3], load["last"][3] if load else 0]
            requested = None
        now = state["time"]
        sides = {"gen": [{"id": cert.gen_id, "base": bases[0], "since": now}],
                 "grid": [{"id": cert.grid_id, "base": bases[1], "since": now}],
                 "load": ([{"id": cert.load_id, "base": bases[2], "since": now}]
                          if load else [])}
        state["pairs"][str(cert.pair_id)] = {
            "beneficiary": cert.beneficiary, "loss_ppm": cert.loss_ppm,
            "site_hash": cert.site_hash.hex(), "sides": sides,
            "minted_tokens": 0, "attested_tokens": 0, "attest_nonce": 0,
            "requested": requested,
            "certified": {"height": state["height"], "time": now},
            "grid_seen_gen": 0, "outage_attested": 0, "escrow": 0,
            "grid_mark": None, "load_mark": None,
            "balance": {"gross": 0, "gen": 0, "residual": 0, "allowance": 0,
                        "flag": False, "since": None, "max_residual": 0},
        }
        for m in (gen, grid, load):
            if m is not None:
                m["pair"] = cert.pair_id
        # Energy counted since the request is credited now, not at the next
        # record.
        self._mint(state, state["pairs"][str(cert.pair_id)])

    def _apply_revoke(self, state: dict, tx: dict) -> None:
        r = tx["revocation"]
        rev = Revocation(int(r["meter_id"]), str(r["reason"]), int(r["effective_seq"]),
                         self._evidence(r["evidence"]))
        if rev.reason not in REASONS:
            raise LedgerError(f"revocation reason must be one of {', '.join(REASONS)}")
        if rev.effective_seq < 0:
            raise LedgerError("effective seq out of range")
        n = self._need(rev.body(), tx, "revocation")
        m = state["meters"].get(str(rev.meter_id))
        if not m:
            raise LedgerError("unknown meter")
        old = m["revocation"]
        if old and old["status"] == "active":
            raise LedgerError("meter already revoked")
        urgent = n >= self.k_urgent
        if old and not urgent:
            raise LedgerError("a revocation is already filed; replacing it needs "
                              "k_urgent approvals")
        now = state["time"]
        m["revocation"] = {
            "reason": rev.reason, "effective_seq": rev.effective_seq,
            "evidence": rev.evidence.hex(), "approvals": n,
            "filed": {"height": state["height"], "time": now},
            "status": "active" if urgent else "pending",
            "activates": now if urgent else now + self.notice_s,
        }

    def _apply_contest(self, state: dict, tx: dict) -> None:
        mid = int(tx["meter_id"])
        m = state["meters"].get(str(mid))
        if not m or m["pair"] is None:
            raise LedgerError("only a paired meter's revocation can be contested")
        who = state["pairs"][str(m["pair"])]["beneficiary"]
        self._account(tx, contest_body(self.chain_id, mid), who)
        rev = m["revocation"]
        if not rev or rev["status"] != "pending":
            raise LedgerError("no pending revocation to contest")
        rev["status"] = "contested"
        rev["contested"] = {"height": state["height"], "time": state["time"]}

    def _apply_rebind(self, state: dict, tx: dict) -> None:
        c = tx["cert"]
        rb = PairRebind(int(c["pair_id"]), int(c["old_id"]), int(c["new_id"]))
        self._need(rb.body(), tx, "rebind")
        p = state["pairs"].get(str(rb.pair_id))
        if not p:
            raise LedgerError("unknown pair")
        old = state["meters"].get(str(rb.old_id))
        if not old:
            raise LedgerError("unknown meter")
        side = ROLE_SIDE[old["role"]]
        if not p["sides"][side] or p["sides"][side][-1]["id"] != rb.old_id:
            raise LedgerError("old meter is not the pair's current meter on that side")
        if not meter_retired(old):
            raise LedgerError("only a revoked or wiped meter can be replaced")
        new = self._free_meter(state, rb.new_id, old["role"])
        if side == "grid":
            # The new meter counts from now on. What the GEN side counted
            # while no GRID meter could stays claimable.
            p["escrow"] += claimable(state, p, self.silent_s)["outage_live"]
            p["grid_seen_gen"] = side_tokens(state, p, "gen")
            p["outage_attested"] = 0
        p["sides"][side].append({"id": rb.new_id, "base": new["last"][3],
                                 "since": state["time"]})
        new["pair"] = rb.pair_id

    def _apply_attest(self, state: dict, tx: dict) -> None:
        c = tx["cert"]
        a = Attestation(int(c["pair_id"]), int(c["tokens"]), str(c["reason"]),
                        self._evidence(c["evidence"]), int(c["nonce"]))
        if a.reason not in ATTEST_REASONS:
            raise LedgerError(f"attestation reason must be one of {', '.join(ATTEST_REASONS)}")
        self._need(a.body(), tx, "attestation")
        p = state["pairs"].get(str(a.pair_id))
        if not p:
            raise LedgerError("unknown pair")
        if a.nonce != p["attest_nonce"] + 1:
            raise LedgerError("attestation nonce must be the pair's next")
        cap = claimable(state, p, self.silent_s)
        if not 0 < a.tokens <= cap[a.reason]:
            raise LedgerError(f"attestation exceeds the {a.reason} escrow ({cap[a.reason]})")
        if a.reason == "outage":
            from_live = min(a.tokens, cap["outage_live"])
            p["outage_attested"] += from_live
            p["escrow"] -= a.tokens - from_live
        p["attest_nonce"] = a.nonce
        p["attested_tokens"] += a.tokens
        self._mint(state, p)
        self._flag(state, p)

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
        tamper = rec.kind == KIND_TAMPER
        key = m["tamper_pk"] if tamper else m["pk"]
        if not crypto.verify(m["alg"], bytes.fromhex(key), raw, sig):
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
        if m["wiped"] is not None and (tamper or rec.seq >= m["wiped"]["seq"]):
            raise LedgerError("record after the meter's tamper record")
        rev = m["revocation"]
        if rev and rev["status"] == "active" and rec.seq > rev["effective_seq"]:
            raise LedgerError("record from a revoked meter (seq above the "
                              "revocation's effective seq)")
        if tamper:
            # Proof the cover was opened under power. It mints nothing and
            # does not move the counters; token records built before it
            # (lower seq) are still accepted when they arrive.
            m["wiped"] = {"seq": rec.seq, "e_exp": rec.e_exp, "e_imp": rec.e_imp,
                          "tokens": rec.tokens, "height": state["height"],
                          "time": state["time"]}
            return
        m["last"] = [rec.seq, rec.e_exp, rec.e_imp, rec.tokens]
        m["last_time"] = state["time"]
        if m["pair"] is None:
            return
        p = state["pairs"][str(m["pair"])]
        side = ROLE_SIDE[m["role"]]
        if p["sides"][side][-1]["id"] == rec.meter_id:
            gen = side_tokens(state, p, "gen")
            if side == "grid":
                # The pair's GRID meter is heard from: any silence outage
                # ends. Its cumulative count already covers the silence.
                p["grid_seen_gen"] = gen
                p["outage_attested"] = 0
            if side in ("grid", "load") and p["sides"]["load"]:
                self._balance_mark(state, p, side, gen)
        self._mint(state, p)

    def _mint(self, state: dict, p: dict) -> None:
        target = min(side_tokens(state, p, "gen"),
                     side_tokens(state, p, "grid") + p["attested_tokens"])
        delta = target - p["minted_tokens"]
        if delta > 0:
            p["minted_tokens"] = target
            acct = state["accounts"].setdefault(p["beneficiary"], {"balance": 0, "nonce": 0})
            acct["balance"] += delta * WH_PER_TOKEN
            state["supply_wh"] += delta * WH_PER_TOKEN

    def _balance_mark(self, state: dict, p: dict, side: str, gen: int) -> None:
        """GEN = GRID + LOAD + losses, checked as a lower bound that record
        timing cannot inflate.

        When a GRID record is accepted at time T, the GEN count on chain was
        built no later than T, so it is at most the energy generated by T.
        The GRID count is the high-water of net export at T, at least the
        net export by T. The first LOAD record accepted after T is at least
        the consumption by T. So GEN(at T) - GRID(at T) - LOAD(first after T)
        is at most the energy that went missing between the meters by T,
        give or take the one token each of GRID and LOAD truncates. The same
        holds with GRID and LOAD swapped. Records must reach the ledger in
        the order they were built, which a transmit-only radio does; a
        record held back and delivered late can only lower this bound until
        the next pairing, or raise it by what it held back."""
        tok = side_tokens(state, p, side)
        other = "load" if side == "grid" else "grid"
        mark = p[f"{other}_mark"]
        if mark is not None:
            if side == "grid":
                gross = mark["gen"] - tok - mark["tokens"]
            else:
                gross = mark["gen"] - mark["tokens"] - tok
            p["balance"]["gross"] = gross
            p["balance"]["gen"] = mark["gen"]
            p[f"{other}_mark"] = None
            self._flag(state, p)
        p[f"{side}_mark"] = {"gen": gen, "tokens": tok}

    def _flag(self, state: dict, p: dict) -> None:
        if not p["sides"]["load"]:
            return
        b = p["balance"]
        residual = b["gross"] - p["attested_tokens"]
        # Each of GRID and LOAD truncates up to one token below its energy.
        allowance = -(-b["gen"] * p["loss_ppm"] // 1_000_000) + 2
        flag = residual > allowance
        if flag and not b["flag"]:
            b["since"] = {"height": state["height"], "time": state["time"]}
        elif not flag:
            b["since"] = None
        b.update(residual=residual, allowance=allowance, flag=flag,
                 max_residual=max(b["max_residual"], residual))

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
        self.begin_block(state, self.height + 1, time)
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
        self.begin_block(state, h["height"], h["time"])
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


def frame_tx(frame: bytes, alg: str) -> dict:
    """An issuance from a raw EC-MINT1 UART frame. Anyone who hears the
    frame may submit it: the ledger checks the meter's signature, not the
    sender, so no relay, the grid operator's included, is needed."""
    raw, sig = parse_frame(frame, crypto.SIG_LEN[alg])
    return issuance_tx(raw, sig)
