"""Account keys, addresses and signed transfers.

v0.0.1 stores the secret key unencrypted in a JSON file with mode 0600.
That is acceptable for a development network and nothing else. Encrypted
key storage and hardware-wallet signing are open item S-2 in
docs/open-items.md.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from . import crypto
from .ledger import (ACCOUNT_CTX, TRANSFER_CTX, contest_body, pair_request_body,
                     transfer_body)


@dataclass
class Wallet:
    pk: bytes
    sk: bytes

    @classmethod
    def create(cls, seed: bytes | None = None) -> "Wallet":
        pk, sk = crypto.keygen(crypto.ACCOUNT_ALG, seed)
        return cls(pk, sk)

    @property
    def address(self) -> str:
        return crypto.address(self.pk)

    def transfer(self, chain_id: str, to: str, amount_wh: int, nonce: int) -> dict:
        body = transfer_body(chain_id, self.address, to, amount_wh, nonce)
        sig = crypto.sign(crypto.ACCOUNT_ALG, self.sk, body, TRANSFER_CTX)
        return {"type": "transfer", "from": self.address, "to": to,
                "amount": amount_wh, "nonce": nonce, "pk": self.pk.hex(),
                "sig": sig.hex()}

    def pair_request(self, chain_id: str, gen_id: int, grid_id: int,
                     load_id: int = 0) -> dict:
        """File a pair request naming this wallet as beneficiary. It fixes
        the pair's starting counts now, whenever the certificate lands."""
        body = pair_request_body(chain_id, gen_id, grid_id, load_id, self.address)
        sig = crypto.sign(crypto.ACCOUNT_ALG, self.sk, body, ACCOUNT_CTX)
        return {"type": "pair_request", "gen_id": gen_id, "grid_id": grid_id,
                "load_id": load_id, "beneficiary": self.address,
                "pk": self.pk.hex(), "sig": sig.hex()}

    def contest(self, chain_id: str, meter_id: int) -> dict:
        """Contest a pending revocation of a meter in this wallet's pair."""
        body = contest_body(chain_id, meter_id)
        sig = crypto.sign(crypto.ACCOUNT_ALG, self.sk, body, ACCOUNT_CTX)
        return {"type": "contest", "meter_id": meter_id, "pk": self.pk.hex(),
                "sig": sig.hex()}

    def save(self, path: str) -> None:
        data = {"alg": crypto.ACCOUNT_ALG, "address": self.address,
                "pk": self.pk.hex(), "sk": self.sk.hex(),
                "warning": "unencrypted development key; do not hold value"}
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=1)

    @classmethod
    def load(cls, path: str) -> "Wallet":
        with open(path) as f:
            data = json.load(f)
        if data.get("alg") != crypto.ACCOUNT_ALG:
            raise ValueError("unsupported wallet algorithm")
        w = cls(bytes.fromhex(data["pk"]), bytes.fromhex(data["sk"]))
        if w.address != data["address"]:
            raise ValueError("wallet file is inconsistent")
        return w
