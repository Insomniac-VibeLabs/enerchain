"""In-process development network, persisted to a directory.

    <dir>/genesis.json    the genesis document
    <dir>/blocks.jsonl    one block per line
    <dir>/mempool.jsonl   pending transactions
    <dir>/devkeys.json    validator and certifier secret keys (devnet only)

Every node that has the same genesis and blocks reaches the same state; the
state is never stored, only replayed.
"""

from __future__ import annotations

import copy
import json
import os
import time as _time

from . import crypto
from .ledger import Ledger, LedgerError, make_genesis
from .registry import CERT_CTX, Certifier


class Devnet:
    def __init__(self, path: str) -> None:
        self.path = path
        with open(self._p("genesis.json")) as f:
            self.ledger = Ledger(json.load(f))
        with open(self._p("devkeys.json")) as f:
            keys = json.load(f)
        self.validator_sks = [bytes.fromhex(k) for k in keys["validators"]]
        self.certifier_keys = [(bytes.fromhex(p), bytes.fromhex(s))
                               for p, s in keys["certifiers"]]
        if os.path.exists(self._p("blocks.jsonl")):
            with open(self._p("blocks.jsonl")) as f:
                self.ledger.replay([json.loads(line) for line in f if line.strip()])

    def _p(self, name: str) -> str:
        return os.path.join(self.path, name)

    @classmethod
    def init(cls, path: str, n_validators: int = 1, n_certifiers: int = 3, k: int = 2,
             chain_id: str = "enerchain-devnet") -> "Devnet":
        os.makedirs(path, exist_ok=True)
        if os.path.exists(os.path.join(path, "genesis.json")):
            raise FileExistsError(f"{path} already holds a devnet")
        vals = [crypto.keygen(crypto.ACCOUNT_ALG) for _ in range(n_validators)]
        certs = [Certifier() for _ in range(n_certifiers)]
        genesis = make_genesis(chain_id, [pk for pk, _ in vals], [c.pk for c in certs], k,
                               int(_time.time()))
        with open(os.path.join(path, "genesis.json"), "w") as f:
            json.dump(genesis, f, indent=1)
        fd = os.open(os.path.join(path, "devkeys.json"), os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump({"warning": "devnet keys; never use on a public network",
                       "validators": [sk.hex() for _, sk in vals],
                       "certifiers": [[c.pk.hex(), c._sk.hex()] for c in certs]}, f)
        return cls(path)

    # ------------------------------------------------------------ mempool
    def mempool(self) -> list[dict]:
        if not os.path.exists(self._p("mempool.jsonl")):
            return []
        with open(self._p("mempool.jsonl")) as f:
            return [json.loads(line) for line in f if line.strip()]

    def submit(self, tx: dict) -> None:
        with open(self._p("mempool.jsonl"), "a") as f:
            f.write(json.dumps(tx, sort_keys=True) + "\n")

    def produce(self, now: int | None = None) -> dict:
        """The scheduled validator builds, signs and appends one block."""
        h = self.ledger.height + 1
        pk = self.ledger.proposer_for(h)
        sk = self.validator_sks[self.ledger.validators.index(pk)]
        prev_t = (self.ledger.blocks[-1]["header"]["time"] if self.ledger.blocks
                  else self.ledger.genesis["time"])
        t = max(prev_t, int(_time.time()) if now is None else now)
        pool = self.mempool()
        block = self.ledger.build_block(pool, sk, t)
        self.ledger.add_block(block)
        with open(self._p("blocks.jsonl"), "a") as f:
            f.write(json.dumps(block, sort_keys=True) + "\n")
        included = {json.dumps(tx, sort_keys=True) for tx in block["txs"]}
        # Keep what did not fit; drop what can no longer apply (a replayed
        # record, a spent nonce). A transfer waiting on a later nonce stays.
        rest = []
        for tx in pool:
            if json.dumps(tx, sort_keys=True) in included:
                continue
            try:
                self.ledger.apply_tx(copy.deepcopy(self.ledger.state), tx)
                rest.append(tx)
            except LedgerError:
                if tx.get("type") == "transfer" and int(tx.get("nonce", 0)) > \
                        self.ledger.nonce(str(tx.get("from"))) + 1:
                    rest.append(tx)
        with open(self._p("mempool.jsonl"), "w") as f:
            for tx in rest:
                f.write(json.dumps(tx, sort_keys=True) + "\n")
        return block

    def approve(self, body: bytes, n: int | None = None) -> list[tuple[bytes, bytes]]:
        """Collect approvals from the first n dev certifiers (default k)."""
        n = self.ledger.k if n is None else n
        return [(pk, crypto.sign(crypto.ACCOUNT_ALG, sk, body, CERT_CTX))
                for pk, sk in self.certifier_keys[:n]]
